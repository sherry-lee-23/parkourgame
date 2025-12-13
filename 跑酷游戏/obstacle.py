# obstacle.py
import pygame
import random
import os


class Obstacle:
    def __init__(self, x, y, width=30, height=30, speed=8, image_path='image/障碍物1.jpg'):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = speed
        self.color = (255, 0, 0)
        self.is_active = True

        # 加载障碍物图片
        self.image = None
        if image_path and os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (width, height))
            except:
                self.image = None

        # 如果没有图片，创建简单的图片
        if not self.image:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (200, 50, 50), (0, 0, width, height))
            pygame.draw.rect(self.image, (150, 0, 0), (0, 0, width, height), 2)

    def move(self, scroll_speed=None):
        """移动障碍物"""
        # ============ 修改：支持外部传入滚动速度 ============
        if scroll_speed is not None:
            # 使用传入的滚动速度
            self.rect.x -= scroll_speed
        else:
            # 使用自身的速度（默认）
            self.rect.x -= self.speed

        # 如果移出屏幕，标记为不活动
        if self.rect.right < 0:
            self.is_active = False

    def draw(self, screen):
        """绘制障碍物"""
        if self.is_active:
            screen.blit(self.image, self.rect)

    def check_collision(self, player_rect):
        """检测与玩家的碰撞"""
        return self.rect.colliderect(player_rect)


class ObstacleManager:
    def __init__(self):
        self.obstacles = []
        self.spawn_timer = 0
        self.spawn_interval = 120
        self.min_spacing = 200

        # ============ 新增：滚动速度 ============
        self.scroll_speed = scroll_speed
        self.base_spawn_interval = 120  # 基础生成间隔

        # ============ 新增：难度相关属性 ============
        self.difficulty_level = 1
        self.min_obstacle_height = 40
        self.max_obstacle_height = 90

        self.obstacles_images = [
            'image/ob1.png',
            'image/ob2.png',
            'image/ob3.png'
        ]

    def set_scroll_speed(self, speed):
        """设置滚动速度"""
        self.scroll_speed = speed
        
    def set_difficulty(self, level):
        """设置难度级别（1-5）"""
        self.difficulty_level = level
        # 难度越高，生成间隔越短，障碍物越大
        self.base_spawn_interval = max(60, 120 - (level * 10))
        
        # 调整障碍物大小范围
        self.min_obstacle_height = 30 + (level * 5)
        self.max_obstacle_height = 70 + (level * 10)

    def spawn_obstacle(self):
        """生成一个新的障碍物"""
        # ============ 修改：根据难度调整障碍物大小 ============
        obstacle_height = random.randint(self.min_obstacle_height, self.max_obstacle_height)
        obstacle_width = random.randint(int(obstacle_height * 0.7), int(obstacle_height * 1.3))
        
        # ============ 修改：障碍物Y坐标 ============
        # 假设地面高度是450，需要与Game类中的ground_y保持一致
        ground_y = 450  # 注意：这个值需要与main.py中的ground_y一致
        obstacle_y = ground_y - obstacle_height  # 让障碍物底部接触地面
        
        # ============ 修改：根据滚动速度调整障碍物大小 ============
        # 速度越快，障碍物越小（更有挑战性）
        size_factor = max(0.5, 1.0 - (self.scroll_speed - 5) * 0.1)
        obstacle_width = int(obstacle_width * size_factor)
        obstacle_height = int(obstacle_height * size_factor)

        # 检查与上一个障碍物的间隔
        if self.obstacles:
            last_obstacle = self.obstacles[-1]
            # ============ 修改：根据速度调整最小间距 ============
            dynamic_min_spacing = self.min_spacing * (1.0 + self.scroll_speed / 10)
            if last_obstacle.rect.x > 800 - dynamic_min_spacing:
                return None

        # ============ 修改：根据速度调整生成间隔 ============
        self.spawn_interval = int(self.base_spawn_interval * (1.0 - self.scroll_speed / 20))
        self.spawn_interval = max(30, self.spawn_interval)  # 最小间隔30帧
        
        image_path = random.choice(self.obstacles_images)
        obstacle = Obstacle(
            800,  # 从屏幕右侧生成
            obstacle_y, 
            obstacle_width, 
            obstacle_height, 
            self.scroll_speed,  # 使用当前的滚动速度作为基础速度
            image_path
        )
        return obstacle

    def update(self):
        """更新障碍物状态"""

        # ============ 修改：支持传入滚动速度 ============
        if scroll_speed is not None:
            self.scroll_speed = scroll_speed

        # 计时生成新障碍物
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            new_obstacle = self.spawn_obstacle()
            if new_obstacle:
                self.obstacles.append(new_obstacle)
                # ============ 修改：使用动态生成间隔 ============
                variation = random.randint(-20, 20)
                self.spawn_interval = random.randint(80, 150)
                self.spawn_timer = 0

        # 更新所有障碍物位置
        for obstacle in self.obstacles[:]:
            # ============ 修改：传递滚动速度给障碍物 ============
            obstacle.move(self.scroll_speed)


            # 移除不活动的障碍物
            if not obstacle.is_active:
                self.obstacles.remove(obstacle)

    def draw(self, screen):
        """绘制所有障碍物"""
        for obstacle in self.obstacles:
            obstacle.draw(screen)

    def check_collisions(self, player_rect):
        """检测玩家与所有障碍物的碰撞"""
        for obstacle in self.obstacles:
            if obstacle.check_collision(player_rect):
                return True
        return False

    def clear(self):
        """清除所有障碍物"""

        self.obstacles.clear()
        self.spawn_timer = 0  # 重置计时器
