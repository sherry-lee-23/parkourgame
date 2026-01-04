# player.py
import pygame
import os
import glob


class Player:
        def __init__(self, x, y, can_double_jump=False, player_id=1, image_folder=None, shoot_image_path=None):
        # 基本属性
        self.rect = pygame.Rect(x, y, 50, 50)

        # 动画相关属性
        self.animation_frames = []  # 存储所有动画帧
        self.current_frame = 0  # 当前帧索引
        self.animation_speed = 10  # 动画速度（帧数越高越慢）
        self.animation_counter = 0  # 动画计数器
        self.shoot_image = pygame.image.load(
            shoot_image_path).convert_alpha() if shoot_image_path else None
        self.shoot_timer = 0

        # 加载动画帧
        self.load_animation_frames(image_folder)

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

        # 动画状态
        self.is_moving = False
        self.is_jumping = False
        self.last_update_time = pygame.time.get_ticks()

        print(f"角色{player_id}加载完成，动画帧数: {len(self.animation_frames) if self.animation_frames else 0}")
    def load_animation_frames(self, folder_path):
        """加载动画帧"""

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
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(img, (50, 50))
            self.animation_frames.append(img)
            print(f"加载动画帧: {os.path.basename(img_path)}")

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

    def draw(self, screen):
        """绘制玩家"""
        # 绘制当前动画帧
        if self.shoot_timer > 0 and self.shoot_image:
            screen.blit(self.shoot_image, self.rect)
        else:
            current_image = self.animation_frames[self.current_frame]
            screen.blit(current_image, self.rect)

    def trigger_shooting_pose(self, duration=10):
        """在指定时间内切换到射击动作"""
        self.shoot_timer = max(self.shoot_timer, duration)
