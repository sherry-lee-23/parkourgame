# coin.py
import pygame
import random
import math
import os


class Coin:
    def __init__(self, x, y, size=25, is_ground_coin=False):
        """初始化金币"""
        self.rect = pygame.Rect(x, y, size, size)
        self.size = size
        self.is_active = True
        self.is_collected = False
        self.collect_animation = 0
        self.max_collect_animation = 10

        self.is_ground_coin = is_ground_coin
        self.original_y = y  # 记录原始Y坐标

        # 只有空中金币有浮动效果
        if not is_ground_coin:
            self.float_timer = random.uniform(0, math.pi * 2)
            self.float_speed = random.uniform(0.02, 0.06)
            self.float_amplitude = random.randint(2, 5)

    def move(self, scroll_speed=0):
        """移动金币"""
        if not self.is_collected:
            # 金币与背景同步滚动
            self.rect.x -= scroll_speed

            # 只有空中金币有浮动效果
            if not self.is_ground_coin:
                self.float_timer += self.float_speed
                self.rect.y = self.original_y + math.sin(self.float_timer) * self.float_amplitude

            # 如果移出屏幕，标记为不活动
            if self.rect.right < 0:
                self.is_active = False
        else:
            # 收集动画：金币向上飘并逐渐消失
            self.collect_animation += 1
            self.rect.y -= 2  # 向上飘
            self.rect.x += random.randint(-1, 1)  # 轻微左右晃动

            # 动画结束后标记为不活动
            if self.collect_animation >= self.max_collect_animation:
                self.is_active = False

    def collect(self):
        """收集金币"""
        if not self.is_collected:
            self.is_collected = True
            return True
        return False

    def draw(self, screen):
        """绘制金币"""
        if self.is_active:
            # 如果是收集动画，添加透明度效果
            if self.is_collected:
                alpha = 255 - (self.collect_animation * 255 // self.max_collect_animation)
                temp_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
                self.draw_coin(temp_surface, (0, 0), alpha)
                screen.blit(temp_surface, self.rect)
            else:
                # 正常金币
                self.draw_coin(screen, (self.rect.x, self.rect.y))

    def draw_coin(self, surface, pos, alpha=255):
        """绘制单个金币图形"""
        x, y = pos
        center = self.size // 2
        radius = self.size // 2 - 2

        # 绘制金币
        coin_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        # 绘制金币主体
        for i in range(radius, 0, -1):
            color_value = 200 + (radius - i) * 55 // radius
            color = (color_value, color_value, 50, alpha)
            pygame.draw.circle(coin_surface, color, (center, center), i)

        # 绘制金币边框
        pygame.draw.circle(coin_surface, (220, 220, 0, alpha), (center, center), radius, 2)

        # 绘制金币符号
        font = pygame.font.Font(None, self.size // 2)
        coin_text = font.render("$", True, (255, 255, 200, alpha))
        text_rect = coin_text.get_rect(center=(center, center))
        coin_surface.blit(coin_text, text_rect)

        surface.blit(coin_surface, (x, y))

        # 添加金币发光效果
        if random.random() < (0.05 if self.is_ground_coin else 0.1):
            glow_size = self.size + 4
            glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_color = (255, 255, 180, 100) if self.is_ground_coin else (255, 255, 200, 80)
            pygame.draw.circle(glow_surface, glow_color,
                               (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow_surface, (x - 2, y - 2))

    def check_collision(self, player_rect):
        """检测与玩家的碰撞"""
        return self.rect.colliderect(player_rect)


class CoinManager:
    def __init__(self, obstacle_manager=None):
        self.coins = []
        self.spawn_timer = 0
        self.spawn_interval = 35
        self.min_spacing = 80

        # 地面金币生成配置
        self.ground_coin_count_range = (2, 5)
        self.ground_coin_spacing = 30

        self.waiting_after_obstacle = False
        self.obstacle_manager = obstacle_manager

        # 加载音效
        self.collect_sound = None
        self.load_sound()

    def load_sound(self):
        """加载金币收集音效"""
        try:
            # 检查是否有音效文件
            sound_paths = [
                'image/Super Mario Bros 3 - Coin Sound Effect.mp3',
                'image/coin_sound.mp3',
                'image/coin.wav'
            ]

            for path in sound_paths:
                if os.path.exists(path):
                    self.collect_sound = pygame.mixer.Sound(path)
                    self.collect_sound.set_volume(0.3)  # 设置音量
                    print(f"成功加载音效: {path}")
                    break

            if not self.collect_sound:
                print("警告: 未找到音效文件，金币收集将没有声音")
        except Exception as e:
            print(f"加载音效失败: {e}")
            self.collect_sound = None

    def obstacle_too_close(self, min_gap):
        if not self.obstacle_manager:
            return False

        if not self.obstacle_manager.obstacles:
            return False

        last_ob = self.obstacle_manager.obstacles[-1]
        return last_ob.rect.x > 800 - min_gap

    def spawn_coins_group(self, x, is_ground_group=False):
        coins = []

        if is_ground_group:
            count = random.randint(*self.ground_coin_count_range)
            base_y = 350

            for i in range(count):
                coin_x = x + i * self.ground_coin_spacing
                coin = Coin(coin_x, base_y, is_ground_coin=True)
                coins.append(coin)
        else:
            spawn_y = random.randint(220, 260)

            # 如果地面被障碍物挡住，把金币放到障碍物上方
            if self.obstacle_manager:
                for ob in self.obstacle_manager.obstacles:
                    if abs(ob.rect.x - x) < 120:
                        spawn_y = ob.rect.top - 40
                        break

            coin = Coin(x, spawn_y, is_ground_coin=False)
            coins.append(coin)

        return coins

    def has_upcoming_obstacle(self, spawn_x):
        if not self.obstacle_manager:
            return False

        for ob in self.obstacle_manager.obstacles:
            if spawn_x <= ob.rect.x <= spawn_x + 260:
                return True
        return False

    def spawn_coin(self):
        if self.waiting_after_obstacle and self.spawn_timer < 60:
            return None

        spawn_x = 800
        OBSTACLE_COIN_GAP = 140

        # 只在"刚生成障碍物后"阻止一次地面金币
        if self.waiting_after_obstacle:
            if self.obstacle_too_close(OBSTACLE_COIN_GAP):
                return None
            else:
                self.waiting_after_obstacle = False

        spawn_ground_group = random.random() < 0.7

        if spawn_ground_group and self.has_upcoming_obstacle(spawn_x):
            spawn_ground_group = False

        if self.coins:
            last_coin = self.coins[-1]
            if last_coin.rect.x > spawn_x - self.min_spacing:
                return None

        coins = self.spawn_coins_group(spawn_x, is_ground_group=spawn_ground_group)
        return coins if coins else None

    def update(self, scroll_speed=0):
        """更新金币状态"""
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            new_coins = self.spawn_coin()
            if new_coins:
                self.coins.extend(new_coins)

                last_is_ground = hasattr(new_coins[0], 'is_ground_coin') and new_coins[0].is_ground_coin
                if last_is_ground:
                    self.spawn_interval = random.randint(50, 100)
                else:
                    self.spawn_interval = random.randint(30, 60)
                self.spawn_timer = 0

        # 更新所有金币位置
        for coin in self.coins[:]:
            coin.move(scroll_speed)

            if not coin.is_active:
                self.coins.remove(coin)

    def check_collections(self, player_rect, coin_multiplier=1):
        """检测玩家与所有金币的碰撞，支持金币翻倍效果"""
        collected_count = 0

        for coin in self.coins:
            if not coin.is_collected and coin.check_collision(player_rect):
                if coin.collect():
                    collected_count += 1
                    # 播放收集音效
                    if self.collect_sound:
                        self.collect_sound.play()

        # 应用金币翻倍效果
        return collected_count * coin_multiplier

    def draw(self, screen):
        """绘制所有金币"""
        for coin in self.coins:
            coin.draw(screen)

    def clear(self):
        """清除所有金币"""
        self.coins.clear()
