# coin.py
import pygame
import random
import os
import math

COIN_FONT = None


class Coin:
    def __init__(self, x, y, size=25, speed=2, image_path='image/coin.png', is_ground_coin=False):
        """
        初始化金币
        :param x: 初始x坐标
        :param y: 初始y坐标
        :param size: 金币大小
        :param speed: 移动速度
        :param image_path: 金币图片路径
        :param is_ground_coin: 是否是地面金币
        """
        # 金币位置和大小
        self.rect = pygame.Rect(x, y, size, size)
        self.size = size
        self.speed = speed
        self.is_active = True
        self.is_collected = False
        self.collect_animation = 0
        self.max_collect_animation = 10  # 收集动画帧数

        # 新增属性
        self.is_ground_coin = is_ground_coin
        self.original_y = y  # 记录原始Y坐标

        # 只有空中金币有浮动效果
        if not is_ground_coin:
            self.float_timer = random.uniform(0, math.pi * 2)  # 浮动计时器，随机起始位置
            self.float_speed = random.uniform(0.02, 0.06)  # 浮动速度（减小）
            self.float_amplitude = random.randint(2, 5)  # 浮动幅度（减小）

        # 金币图片
        self.image = None
        self.load_coin_image(image_path)

    def load_coin_image(self, image_path):
        """加载金币图片"""
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.size, self.size))
            except:
                self.image = None

        # 如果没有金币图片，创建一个简单的金币
        if not self.image:
            self.create_simple_coin()

    def create_simple_coin(self):
        global COIN_FONT

        if COIN_FONT is None:
            COIN_FONT = pygame.font.Font(None, self.size // 2)

        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        center = self.size // 2
        radius = self.size // 2 - 2

        for i in range(radius, 0, -1):
            color_value = 200 + (radius - i) * 55 // radius
            color = (color_value, color_value, 50)
            pygame.draw.circle(self.image, color, (center, center), i)

        pygame.draw.circle(self.image, (220, 220, 0), (center, center), radius, 2)

        coin_text = COIN_FONT.render("$", True, (255, 255, 200))
        text_rect = coin_text.get_rect(center=(center, center))
        self.image.blit(coin_text, text_rect)

    def move(self, scroll_speed=0):
        """移动金币
        :param scroll_speed: 背景滚动速度，金币将与背景同步移动
        """
        if not self.is_collected:
            # 金币与背景同步滚动
            self.rect.x -= scroll_speed

            # 只有空中金币有浮动效果
            if not self.is_ground_coin:
                # 使用正弦波实现平滑的上下浮动（幅度更小）
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
                # 计算透明度（从255到0）
                alpha = 255 - (self.collect_animation * 255 // self.max_collect_animation)
                temp_image = self.image.copy()
                temp_image.set_alpha(alpha)
                screen.blit(temp_image, self.rect)
            else:
                # 正常金币
                screen.blit(self.image, self.rect)

                # 添加金币发光效果（根据类型调整频率）
                if random.random() < (0.05 if self.is_ground_coin else 0.1):
                    glow_size = self.size + 4
                    glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                    glow_color = (255, 255, 180, 100) if self.is_ground_coin else (255, 255, 200, 80)
                    pygame.draw.circle(glow_surface, glow_color,
                                       (glow_size // 2, glow_size // 2), glow_size // 2)
                    screen.blit(glow_surface, (self.rect.x - 2, self.rect.y - 2))

    def check_collision(self, player_rect):
        """检测与玩家的碰撞"""
        return self.rect.colliderect(player_rect)


class CoinManager:

    def ground_blocked(self, spawn_x):
        if not self.obstacle_manager:
            return False

        for ob in self.obstacle_manager.obstacles:
            # 如果障碍物在金币生成区间内
            if abs(ob.rect.x - spawn_x) < 120:
                return True
        return False

    def __init__(self, obstacle_manager=None):
        self.coins = []
        self.spawn_timer = 0
        self.spawn_interval = 35  # 金币生成间隔（帧数，减小以使金币更多）
        self.min_spacing = 80  # 金币之间的最小间隔（减小以使金币更密集）
        self.coin_speed = 0  # 金币自身移动速度设为0，将与背景同步

        # 地面金币生成配置
        self.ground_coin_count_range = (2, 5)  # 每次生成地面金币的数量范围
        self.ground_coin_spacing = 30  # 地面金币之间的水平间距

        self.waiting_after_obstacle = False

        # 障碍物管理器引用（用于检测金币与障碍物的碰撞）
        self.obstacle_manager = obstacle_manager

        # 金币收集音效（可选）
        self.collect_sound = None
        self.load_sound()

        print("金币管理器初始化完成")

    def load_sound(self):
        """加载音效（如果可用）"""
        try:
            pygame.mixer.init()
            # 尝试加载音效文件
            if os.path.exists('image/Super Mario Bros 3 - Coin Sound Effect.mp3'):
                self.collect_sound = pygame.mixer.Sound('image/Super Mario Bros 3 - Coin Sound Effect.mp3')
                self.collect_sound.set_volume(0.3)
            elif os.path.exists('image/Super Mario Bros 3 - Coin Sound Effect.mp3'):
                self.collect_sound = pygame.mixer.Sound('image/Super Mario Bros 3 - Coin Sound Effect.mp3')
                self.collect_sound.set_volume(0.3)
        except:
            print("无法加载音效，将静音运行")
            self.collect_sound = None

    def obstacle_too_close(self, min_gap):
        if not self.obstacle_manager:
            return False

        if not self.obstacle_manager.obstacles:
            return False

        last_ob = self.obstacle_manager.obstacles[-1]

        # 障碍物还没离开生成区 enough distance
        if last_ob.rect.x > 800 - min_gap:
            return True

        return False

    def spawn_coins_group(self, x, is_ground_group=False):
        coins = []

        if is_ground_group:
            count = random.randint(*self.ground_coin_count_range)
            base_y = 350

            for i in range(count):
                coin_x = x + i * self.ground_coin_spacing
                coin = Coin(
                    coin_x,
                    base_y,
                    is_ground_coin=True
                )
                coins.append(coin)


        else:
            # ===== 空中金币（关键在这里）=====
            spawn_y = random.randint(220, 260)

            # ⭐ 如果地面被障碍物挡住，把金币放到障碍物上方
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
            # 只要右侧 200px 内有障碍物，就认为“地面被占用”
            if spawn_x <= ob.rect.x <= spawn_x + 200:
                return True
        return False

    def spawn_coin(self):
        if self.waiting_after_obstacle and self.spawn_timer < 60:
            return None

        spawn_x = 800
        OBSTACLE_COIN_GAP = 140 # 可以比之前小一点

        # ⭐ 只在“刚生成障碍物后”阻止一次地面金币
        if self.waiting_after_obstacle:
            if self.obstacle_too_close(OBSTACLE_COIN_GAP):
                return None
            else:
                # 已经空出距离，可以生成地面金币串了
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
        """更新金币状态
        :param scroll_speed: 背景滚动速度，金币将与背景同步移动
        """
        # 计时生成新金币
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            new_coins = self.spawn_coin()
            if new_coins:
                self.coins.extend(new_coins)

                # 随机化下次生成间隔
                last_is_ground = hasattr(new_coins[0], 'is_ground_coin') and new_coins[0].is_ground_coin
                if last_is_ground:
                    self.spawn_interval = random.randint(50, 100)
                else:
                    self.spawn_interval = random.randint(30, 60)
                self.spawn_timer = 0

        # 更新所有金币位置（传入背景滚动速度）
        for coin in self.coins[:]:  # 使用切片复制避免迭代问题
            coin.move(scroll_speed)

            # 移除不活动的金币
            if not coin.is_active:
                self.coins.remove(coin)

    def check_collections(self, player_rect):
        """检测玩家与所有金币的碰撞"""
        collected_count = 0

        for coin in self.coins:
            if not coin.is_collected and coin.check_collision(player_rect):
                if coin.collect():
                    collected_count += 1
                    # 播放收集音效
                    if self.collect_sound:
                        self.collect_sound.play()

        return collected_count

    def draw(self, screen):
        """绘制所有金币"""
        for coin in self.coins:
            coin.draw(screen)

    def clear(self):
        """清除所有金币"""
        self.coins.clear()