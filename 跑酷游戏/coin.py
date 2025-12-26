# coin.py
import pygame
import random
import os
import math


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
        """创建简单的金币图片"""
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        # 绘制金币形状
        center = self.size // 2
        radius = self.size // 2 - 2

        # 金币颜色渐变
        for i in range(radius, 0, -1):
            color_value = 200 + (radius - i) * 55 // radius
            color = (color_value, color_value, 50)
            pygame.draw.circle(self.image, color, (center, center), i)

        # 金币边框
        pygame.draw.circle(self.image, (220, 220, 0), (center, center), radius, 2)

        # 金币中间的符号
        font = pygame.font.Font(None, self.size // 2)
        coin_text = font.render("$", True, (255, 255, 200))
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
    def __init__(self, obstacle_manager=None):
        self.coins = []
        self.spawn_timer = 0
        self.spawn_interval = 35  # 金币生成间隔（帧数，减小以使金币更多）
        self.min_spacing = 80  # 金币之间的最小间隔（减小以使金币更密集）
        self.coin_speed = 0  # 金币自身移动速度设为0，将与背景同步

        # 地面金币生成配置
        self.ground_coin_count_range = (2, 5)  # 每次生成地面金币的数量范围
        self.ground_coin_spacing = 30  # 地面金币之间的水平间距

        # 障碍物管理器引用（用于检测金币与障碍物的碰撞）
        self.obstacle_manager = obstacle_manager
        self.safe_distance = 50  # 金币与障碍物的安全距离

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

    def check_collision_with_obstacles(self, coin_rect):
        """检查金币是否与障碍物重合或太近"""
        if not self.obstacle_manager:
            return False

        # 获取所有障碍物的矩形
        obstacle_rects = self.obstacle_manager.get_all_obstacle_rects()

        for obstacle_rect in obstacle_rects:
            # 计算两个矩形之间的最小距离
            dx = min(coin_rect.right, obstacle_rect.right) - max(coin_rect.left, obstacle_rect.left)
            dy = min(coin_rect.bottom, obstacle_rect.bottom) - max(coin_rect.top, obstacle_rect.top)

            # 如果有重叠或距离太近
            if dx > -self.safe_distance and dy > -self.safe_distance:
                return True

        return False

    def spawn_coins_group(self, x, is_ground_group=False):
        """生成一组金币，检查是否与障碍物重合"""
        coins = []

        if is_ground_group:
            # 地面金币组：整齐排列
            count = random.randint(*self.ground_coin_count_range)
            base_y = 350  # 地面高度

            for i in range(count):
                coin_x = x + i * self.ground_coin_spacing
                coin_size = 25  # 地面金币大小固定
                coin_rect = pygame.Rect(coin_x, base_y, coin_size, coin_size)

                # 检查这个金币是否与障碍物重合
                if not self.check_collision_with_obstacles(coin_rect):
                    coin = Coin(coin_x, base_y, coin_size, self.coin_speed, is_ground_coin=True)
                    coins.append(coin)
                else:
                    # 如果有一个金币与障碍物重合，整组都不生成
                    return []
        else:
            # 空中金币：单个生成，有轻微浮动
            # 尝试最多3次生成位置
            for _ in range(3):
                coin_y = random.randint(220, 280)
                coin_size = random.randint(22, 28)
                coin_rect = pygame.Rect(x, coin_y, coin_size, coin_size)

                # 检查这个金币是否与障碍物重合
                if not self.check_collision_with_obstacles(coin_rect):
                    coin = Coin(x, coin_y, coin_size, self.coin_speed, is_ground_coin=False)
                    coins.append(coin)
                    break

        return coins

    def spawn_coin(self):
        """生成新的金币（地面组或空中单个）"""
        # 70%概率生成地面金币组，30%概率生成空中金币
        spawn_ground_group = random.random() < 0.7

        # 检查与上一个金币组的间隔
        if self.coins:
            last_coin = self.coins[-1]
            # 如果最后一个金币太近，跳过这次生成
            if last_coin.rect.x > 800 - self.min_spacing * (2 if spawn_ground_group else 1):
                return None

        # 生成金币组或单个金币
        coins = self.spawn_coins_group(800, is_ground_group=spawn_ground_group)

        # 如果因为障碍物而没有生成金币，尝试在空中生成金币作为替代
        if not coins and spawn_ground_group:
            # 如果地面金币组生成失败，尝试生成空中金币
            coins = self.spawn_coins_group(800, is_ground_group=False)

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