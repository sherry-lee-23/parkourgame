import pygame
import os
import glob


class Player:
    def __init__(self, x, y, can_double_jump=False, player_id=1, image_folder=None, shoot_image_path=None):
        # 基本属性
        self.rect = pygame.Rect(x, y, 50, 50)

        # 动画相关属性
        self.animation_frames = []  # 动画帧列表
        self.current_frame = 0  # 当前帧索引
        self.animation_speed = 10  # 动画速度
        self.animation_counter = 0  # 动画计数器

        # 战斗相关属性
        self.shoot_frame = None  # 射击动作帧
        self.shoot_timer = 0  # 射击计时器
        self.force_shoot_pose = False

        # 加载动画帧
        self.load_animation_frames(image_folder)

        # 加载射击图片（可选）
        self.load_shoot_image(player_id, shoot_image_path)

        # 物理属性
        self.velocity_y = 0
        self.on_ground = True
        self.jump_count = 0
        self.max_jump_count = 2 if can_double_jump else 1

        # 战斗属性
        self.attack_power = 25
        self.health = 3
        self.is_invincible = False
        self.buff_timer = 0
        self.speed_multiplier = 1.0

        # 玩家类型
        self.can_double_jump = can_double_jump
        self.player_id = player_id

        # 跳跃参数
        self.jump_power = -12

        # 状态
        self.is_jumping = False
        self.last_update_time = pygame.time.get_ticks()

        print(
            f"角色{player_id}加载完成，动画帧数: {len(self.animation_frames) if self.animation_frames else 0}")  # 修改这里的打印信息

    
    def load_shoot_image(self, player_id, shoot_image_path):
        """加载射击图片（可选）"""
        if shoot_image_path and os.path.exists(shoot_image_path):
            try:
                self.shoot_frame = pygame.image.load(shoot_image_path).convert_alpha()
                self.shoot_frame = pygame.transform.scale(self.shoot_frame, (50, 50))
                print(f"成功加载射击图片: {shoot_image_path}")
                return
            except Exception as e:
                print(f"加载射击图片失败: {e}")

        # 如果射击图片未能加载，改为使用静态图片以保持一致外观
        if self.static_frame is not None:
            self.shoot_frame = self.static_frame
            print("使用静态图片作为射击图片")
        else:
            # 如果静态图片也不存在，创建默认射击图片
            print("未提供射击图片，且静态图片不存在，创建默认射击图片")
            self.shoot_frame = self.create_default_shoot_image(player_id)
    
    def create_default_shoot_image(self, player_id):
        """创建默认射击图片"""
        image = pygame.Surface((50, 50), pygame.SRCALPHA)
        
        if player_id == 1:
            # 尼克射击姿势（蓝色）
            pygame.draw.ellipse(image, (100, 150, 255), (10, 20, 30, 20))
            pygame.draw.circle(image, (100, 150, 255), (25, 15), 12)
            pygame.draw.circle(image, (255, 255, 255), (20, 12), 4)
            pygame.draw.circle(image, (255, 255, 255), (30, 12), 4)
            # 添加射击动作：举起的"枪"（简单线条表示）
            pygame.draw.line(image, (100, 100, 100), (40, 20), (50, 10), 3)
        else:
            # 朱迪射击姿势（粉色）
            pygame.draw.ellipse(image, (255, 150, 200), (10, 20, 30, 20))
            pygame.draw.circle(image, (255, 150, 200), (25, 15), 12)
            pygame.draw.circle(image, (255, 255, 255), (20, 12), 4)
            pygame.draw.circle(image, (255, 255, 255), (30, 12), 4)
            # 添加射击动作：举起的"枪"（简单线条表示）
            pygame.draw.line(image, (100, 100, 100), (40, 20), (50, 10), 3)
        
        return image

    def load_animation_frames(self, folder_path):
        """加载动画帧"""
        self.animation_frames = []  # 确保清空列表
        self.current_frame = 0
        self.animation_speed = 10
        self.animation_counter = 0

        # 支持的图片格式
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']

        # 收集所有图片文件
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(folder_path, ext)))

        # 按文件名排序（确保帧顺序正确）
        image_files.sort()

        # 加载所有图片
        for img_path in image_files:
            try:
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (50, 50))
                self.animation_frames.append(img)
                print(f"加载动画帧: {os.path.basename(img_path)}")
            except Exception as e:
                print(f"加载动画帧失败: {img_path}, 错误: {e}")

        print(f"成功加载 {len(self.animation_frames)} 个动画帧")

    def update_animation(self):
        """更新动画"""
        if not self.animation_frames or len(self.animation_frames) <= 1:
            return

        # 更新动画计数器
        self.animation_counter += 1

        # 根据速度更新动画帧
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)

    def jump(self):
        """执行跳跃"""
        if self.jump_count < self.max_jump_count:
            self.velocity_y = self.jump_power
            self.on_ground = False
            self.is_jumping = True
            self.jump_count += 1

            # 如果是二段跳，给一个较小的速度
            if self.jump_count == 2 and self.can_double_jump:
                self.velocity_y = self.jump_power * 0.8  # 二段跳高度稍低

            return True
        return False

    def update(self):
        """更新玩家状态"""
        # 更新射击计时器
        if self.shoot_timer > 0:
            self.shoot_timer -= 1

        # 应用重力
        self.velocity_y += 0.5  # 重力加速度

        # 更新位置
        self.rect.y += self.velocity_y

        # 检测是否到达地面 (y=400)
        if self.rect.bottom >= 400:
            self.rect.bottom = 400
            self.velocity_y = 0
            self.on_ground = True
            self.is_jumping = False
            self.jump_count = 0  # 重置跳跃次数

        if self.buff_timer > 0:
            self.buff_timer -= 1
            if self.buff_timer <= 0:
                self.is_invincible = False
                self.speed_multiplier = 1.0

        # 更新动画
        self.update_animation()

    def reset_position(self, x, y):
        """重置玩家位置"""
        self.rect.x = x
        self.rect.y = y
        self.velocity_y = 0
        self.on_ground = True
        self.is_jumping = False
        self.jump_count = 0
        self.current_frame = 0  # 重置动画帧
        self.animation_counter = 0  # 重置动画计数器

    def draw(self, screen):
        """绘制玩家"""
        # 如果无敌状态，添加闪烁效果
        if self.is_invincible and self.buff_timer % 10 < 5:
            return  # 闪烁时不绘制

        # 如果正在射击，绘制射击图片
        if (self.force_shoot_pose or self.shoot_timer > 0) and self.shoot_frame:
            screen.blit(self.shoot_frame, self.rect)
        # 否则绘制当前动画帧
        elif self.animation_frames:
            current_image = self.animation_frames[self.current_frame]
            screen.blit(current_image, self.rect)
        else:
            # 如果动画帧不存在，绘制一个简单的矩形作为备份
            pygame.draw.rect(screen, (255, 0, 0) if self.player_id == 1 else (0, 255, 0), self.rect)
    def trigger_shooting_pose(self, duration=10):
        """在指定时间内切换到射击动作"""
        self.shoot_timer = max(self.shoot_timer, duration)

    def set_force_shoot_pose(self, enabled=True):
        """强制保持射击姿势"""
        self.force_shoot_pose = enabled


