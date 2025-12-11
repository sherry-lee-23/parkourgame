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

    def move(self):
        """移动障碍物"""
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

        self.obstacles_images = [
            'image/ob1.png',
            'image/ob2.png',
            'image/ob3.png'
        ]

    def spawn_obstacle(self):
        """生成一个新的障碍物"""
        # 随机高度和宽度
        obstacle_height = random.randint(40, 90)
        obstacle_width = random.randint(40, 90)#更改了高度和宽度
        obstacle_y = 400 - obstacle_height  # 底部在地面上，地面为400

        # 障碍物速度
        obstacle_speed = 8
        # 检查与上一个障碍物的间隔
        if self.obstacles:
            last_obstacle = self.obstacles[-1]
            if last_obstacle.rect.x > 800 - self.min_spacing:
                return None

        image_path = random.choice(self.obstacles_images)
        obstacle = Obstacle(800, obstacle_y, obstacle_width, obstacle_height, obstacle_speed, image_path)
        return obstacle

    def update(self):
        """更新障碍物状态"""
        # 计时生成新障碍物
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            new_obstacle = self.spawn_obstacle()
            if new_obstacle:
                self.obstacles.append(new_obstacle)
                self.spawn_interval = random.randint(80, 150)
                self.spawn_timer = 0

        # 更新所有障碍物位置
        for obstacle in self.obstacles[:]:
            obstacle.move()

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