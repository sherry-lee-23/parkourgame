import pygame
import os
import glob


class Player:
    def __init__(self, x, y, can_double_jump=False, player_id=1, image_folder=None, shoot_image_path=None):
        # 基本属性
        self.rect = pygame.Rect(x, y, 50, 50)

        # 图像相关属性 - 使用静态图片
        self.static_frame = None    # 静态帧（动物封面）
        self.shoot_frame = None     # 射击动作帧
        self.shoot_timer = 0        # 射击计时器
        self.force_shoot_pose = False
        
        # 加载静态图片
        self.load_static_image(player_id, image_folder)
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

        print(f"角色{player_id}加载完成，使用静态图片")
        
    def load_static_image(self, player_id, folder_path):
        """加载静态图片，确保一定能加载到"""
        print(f"开始加载角色{player_id}的图片，文件夹: {folder_path}")
        
        # 根据角色ID确定图片文件名
        if player_id == 1:
            target_files = ['nick.png', 'fox.png', 'animal1.png', 'player1.png', 'frame1.png']
        else:
            target_files = ['judy.png', 'rabbit.png', 'animal2.png', 'player2.png', 'frame1.png']
        
        # 先尝试从指定文件夹加载
        if folder_path and os.path.exists(folder_path):
            print(f"检查文件夹: {folder_path}")
            # 检查文件夹内的所有文件
            all_files = os.listdir(folder_path)
            print(f"文件夹内容: {all_files}")
            
            for filename in target_files:
                file_path = os.path.join(folder_path, filename)
                if os.path.exists(file_path):
                    try:
                        print(f"尝试加载: {file_path}")
                        img = pygame.image.load(file_path).convert_alpha()
                        img = pygame.transform.scale(img, (50, 50))
                        self.static_frame = img
                        print(f"成功加载角色{player_id}图片: {filename}")
                        return
                    except Exception as e:
                        print(f"加载失败 {filename}: {e}")
                        continue
        
        # 如果指定文件夹失败，尝试从gif文件夹加载
        print("尝试从gif文件夹加载...")
        gif_folder = 'gif'
        if os.path.exists(gif_folder):
            for filename in target_files:
                file_path = os.path.join(gif_folder, filename)
                if os.path.exists(file_path):
                    try:
                        print(f"尝试从gif加载: {file_path}")
                        img = pygame.image.load(file_path).convert_alpha()
                        img = pygame.transform.scale(img, (50, 50))
                        self.static_frame = img
                        print(f"成功从gif加载角色{player_id}图片: {filename}")
                        return
                    except Exception as e:
                        print(f"从gif加载失败 {filename}: {e}")
                        continue
        
        # 如果都没有，尝试加载文件夹中的第一个图片
        if folder_path and os.path.exists(folder_path):
            print(f"尝试加载文件夹中的第一个图片: {folder_path}")
            # 支持的图片格式
            image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']
            image_files = []
            
            for ext in image_extensions:
                pattern = os.path.join(folder_path, ext)
                found_files = glob.glob(pattern)
                image_files.extend(found_files)
            
            if image_files:
                image_files.sort()
                try:
                    print(f"尝试加载第一个文件: {image_files[0]}")
                    img = pygame.image.load(image_files[0]).convert_alpha()
                    img = pygame.transform.scale(img, (50, 50))
                    self.static_frame = img
                    print(f"成功加载第一个图片: {os.path.basename(image_files[0])}")
                    return
                except Exception as e:
                    print(f"加载第一个图片失败: {e}")
        
        # 最后，创建自定义动物图片
        print("所有加载方法失败，创建自定义动物图片")
        self.static_frame = self.create_custom_animal_image(player_id)
    
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
        
    def create_custom_animal_image(self, player_id):
        """创建自定义动物图片"""
        print(f"为角色{player_id}创建自定义动物图片")
        image = pygame.Surface((50, 50), pygame.SRCALPHA)
        
        if player_id == 1:
            # 尼克（蓝色狐狸） - 更详细的绘制
            # 身体
            pygame.draw.ellipse(image, (100, 150, 255), (10, 20, 30, 20))
            # 头部
            pygame.draw.circle(image, (100, 150, 255), (25, 15), 12)
            # 眼睛
            pygame.draw.circle(image, (255, 255, 255), (20, 12), 4)
            pygame.draw.circle(image, (255, 255, 255), (30, 12), 4)
            pygame.draw.circle(image, (0, 0, 0), (20, 12), 2)
            pygame.draw.circle(image, (0, 0, 0), (30, 12), 2)
            # 鼻子
            pygame.draw.circle(image, (255, 100, 100), (25, 18), 3)
            # 嘴巴
            pygame.draw.arc(image, (255, 100, 100), (22, 18, 6, 6), 0, 3.14, 2)
            # 耳朵
            pygame.draw.polygon(image, (100, 150, 255), [(20, 5), (25, 0), (30, 5)])
            pygame.draw.polygon(image, (150, 200, 255), [(22, 7), (25, 2), (28, 7)])
            # 尾巴
            pygame.draw.ellipse(image, (100, 150, 255), (35, 25, 10, 8))
        else:
            # 朱迪（粉色兔子） - 更详细的绘制
            # 身体
            pygame.draw.ellipse(image, (255, 150, 200), (10, 20, 30, 20))
            # 头部
            pygame.draw.circle(image, (255, 150, 200), (25, 15), 12)
            # 眼睛
            pygame.draw.circle(image, (255, 255, 255), (20, 12), 4)
            pygame.draw.circle(image, (255, 255, 255), (30, 12), 4)
            pygame.draw.circle(image, (0, 0, 0), (20, 12), 2)
            pygame.draw.circle(image, (0, 0, 0), (30, 12), 2)
            # 鼻子
            pygame.draw.circle(image, (255, 100, 100), (25, 18), 3)
            # 嘴巴
            pygame.draw.arc(image, (255, 100, 100), (22, 18, 6, 6), 0, 3.14, 2)
            # 长耳朵
            pygame.draw.ellipse(image, (255, 150, 200), (18, 0, 10, 20))
            pygame.draw.ellipse(image, (255, 150, 200), (27, 0, 10, 20))
            pygame.draw.ellipse(image, (255, 200, 220), (20, 2, 6, 16))
            pygame.draw.ellipse(image, (255, 200, 220), (29, 2, 6, 16))
            # 尾巴
            pygame.draw.circle(image, (255, 200, 220), (40, 30), 5)
        
        print("自定义动物图片创建完成")
        return image

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

    def reset_position(self, x, y):
        """重置玩家位置"""
        self.rect.x = x
        self.rect.y = y
        self.velocity_y = 0
        self.on_ground = True
        self.is_jumping = False
        self.jump_count = 0

    def draw(self, screen):
        """绘制玩家"""
        # 如果无敌状态，添加闪烁效果
        if self.is_invincible and self.buff_timer % 10 < 5:
            return  # 闪烁时不绘制
            
        # 如果正在射击，绘制射击图片
        if (self.force_shoot_pose or self.shoot_timer > 0) and self.shoot_frame:
            screen.blit(self.shoot_frame, self.rect)
        # 否则绘制静态动物图片
        elif self.static_frame:
            screen.blit(self.static_frame, self.rect)
        else:
            # 如果静态图片不存在，绘制一个简单的矩形作为备份
            pygame.draw.rect(screen, (255, 0, 0) if self.player_id == 1 else (0, 255, 0), self.rect)

    def trigger_shooting_pose(self, duration=10):
        """在指定时间内切换到射击动作"""
        self.shoot_timer = max(self.shoot_timer, duration)

    def set_force_shoot_pose(self, enabled=True):
        """强制保持射击姿势"""
        self.force_shoot_pose = enabled


