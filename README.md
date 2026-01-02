import pygame
import random
import math
import sys
from enum import Enum

# 初始化pygame
pygame.init()
pygame.font.init()

# 屏幕适配
class ScreenAdapter:
    def __init__(self):
        # 获取当前屏幕信息
        screen_info = pygame.display.Info()
        self.base_width = 1200
        self.base_height = 800
        
        # 根据屏幕大小自适应
        self.screen_width = min(screen_info.current_w - 100, self.base_width)
        self.screen_height = min(screen_info.current_h - 100, self.base_height)
        
        # 计算缩放比例
        self.scale_x = self.screen_width / self.base_width
        self.scale_y = self.screen_height / self.base_height
        
        # 创建窗口
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("跑酷游戏加速模块")
        
    def scale_pos(self, x, y):
        """缩放位置坐标"""
        return int(x * self.scale_x), int(y * self.scale_y)
    
    def scale_rect(self, rect):
        """缩放矩形区域"""
        x, y, w, h = rect
        return pygame.Rect(
            int(x * self.scale_x),
            int(y * self.scale_y),
            int(w * self.scale_x),
            int(h * self.scale_y)
        )

# 游戏状态枚举
class GameState(Enum):
    RUNNING = 1
    PAUSED = 2
    GAME_OVER = 3

# 加速状态枚举
class BoostState(Enum):
    NORMAL = 1
    ACCELERATING = 2
    SUPER_SPEED = 3
    SLOW_DOWN = 4
    COOLDOWN = 5

# 障碍物类型枚举
class ObstacleType(Enum):
    SIMPLE = 1
    SPEED_REDUCER = 2
    BOOST_BLOCK = 3
    WALL = 4

# 玩家类
class Player:
    def __init__(self, screen_adapter):
        self.screen_adapter = screen_adapter
        self.width = int(40 * screen_adapter.scale_x)
        self.height = int(60 * screen_adapter.scale_y)
        
        # 初始位置
        self.x = int(100 * screen_adapter.scale_x)
        self.y = screen_adapter.screen_height // 2
        
        # 速度相关
        self.base_speed = 5.0
        self.current_speed = self.base_speed
        self.max_speed = 20.0
        self.min_speed = 2.0
        
        # 加速相关
        self.boost_state = BoostState.NORMAL
        self.boost_multiplier = 1.0
        self.boost_duration = 0
        self.boost_cooldown = 0
        self.super_speed_charge = 0
        
        # 能量系统
        self.energy = 100.0
        self.max_energy = 100.0
        self.energy_regen_rate = 0.5  # 能量恢复速度
        self.boost_energy_cost = 15.0  # 加速消耗能量
        self.super_speed_energy_cost = 40.0  # 超级速度消耗能量
        
        # 物理效果
        self.velocity_y = 0
        self.gravity = 0.5
        self.jump_power = -12
        self.on_ground = False
        
        # 颜色
        self.color = (70, 130, 180)  # 钢蓝色
        
        # 动画效果
        self.boost_particles = []
        self.trail_positions = []
        self.max_trail_length = 15
        
    def update(self, obstacles):
        # 更新位置
        self.x += self.current_speed
        
        # 应用重力
        self.velocity_y += self.gravity
        self.y += self.velocity_y
        
        # 地面碰撞检测
        ground_level = self.screen_adapter.screen_height - 100
        if self.y >= ground_level - self.height:
            self.y = ground_level - self.height
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
            
        # 更新加速状态
        self._update_boost_state()
        
        # 更新能量
        self._update_energy()
        
        # 更新粒子效果
        self._update_particles()
        
        # 更新轨迹
        self._update_trail()
        
        # 检查障碍物碰撞
        self._check_obstacle_collision(obstacles)
        
    def _update_boost_state(self):
        # 减少加速持续时间
        if self.boost_duration > 0:
            self.boost_duration -= 1
            
        # 减少冷却时间
        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1
            
        # 更新速度乘数
        if self.boost_state == BoostState.ACCELERATING:
            self.boost_multiplier = min(2.5, self.boost_multiplier + 0.05)
            if self.boost_duration <= 0:
                self.boost_state = BoostState.COOLDOWN
                self.boost_cooldown = 60  # 60帧冷却时间
                
        elif self.boost_state == BoostState.SUPER_SPEED:
            self.boost_multiplier = 3.5
            if self.boost_duration <= 0:
                self.boost_state = BoostState.COOLDOWN
                self.boost_cooldown = 120  # 更长的冷却时间
                
        elif self.boost_state == BoostState.SLOW_DOWN:
            self.boost_multiplier = max(0.4, self.boost_multiplier - 0.1)
            if self.boost_duration <= 0:
                self.boost_state = BoostState.NORMAL
                
        elif self.boost_state == BoostState.COOLDOWN:
            self.boost_multiplier = max(1.0, self.boost_multiplier - 0.02)
            if self.boost_cooldown <= 0:
                self.boost_state = BoostState.NORMAL
        else:  # NORMAL状态
            self.boost_multiplier = max(1.0, self.boost_multiplier - 0.01)
            
        # 计算最终速度
        self.current_speed = min(self.max_speed, self.base_speed * self.boost_multiplier)
        
        # 超级速度充能
        if self.boost_state != BoostState.SUPER_SPEED and self.energy >= self.super_speed_energy_cost:
            self.super_speed_charge = min(100, self.super_speed_charge + 0.5)
        else:
            self.super_speed_charge = max(0, self.super_speed_charge - 0.5)
            
    def _update_energy(self):
        # 恢复能量
        if self.boost_state != BoostState.ACCELERATING and self.boost_state != BoostState.SUPER_SPEED:
            self.energy = min(self.max_energy, self.energy + self.energy_regen_rate)
            
        # 加速消耗能量
        if self.boost_state == BoostState.ACCELERATING:
            self.energy = max(0, self.energy - 0.8)
            
        if self.boost_state == BoostState.SUPER_SPEED:
            self.energy = max(0, self.energy - 1.5)
            
    def _update_particles(self):
        # 更新粒子效果
        for particle in self.boost_particles[:]:
            particle[0] += particle[2]  # 更新x位置
            particle[1] += particle[3]  # 更新y位置
            particle[4] -= 2  # 减少生命周期
            
            if particle[4] <= 0:
                self.boost_particles.remove(particle)
                
        # 添加新的粒子（加速时）
        if self.boost_state == BoostState.ACCELERATING or self.boost_state == BoostState.SUPER_SPEED:
            for _ in range(3):
                particle_x = self.x - random.randint(5, 20)
                particle_y = self.y + random.randint(0, self.height)
                particle_vx = -random.uniform(1.0, 3.0)
                particle_vy = random.uniform(-1.0, 1.0)
                lifetime = random.randint(10, 20)
                color = (255, 215, 0) if self.boost_state == BoostState.SUPER_SPEED else (70, 130, 255)
                self.boost_particles.append([particle_x, particle_y, particle_vx, particle_vy, lifetime, color])
                
    def _update_trail(self):
        # 更新轨迹
        trail_pos = (self.x + self.width // 2, self.y + self.height // 2)
        self.trail_positions.append(trail_pos)
        
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)
            
    def _check_obstacle_collision(self, obstacles):
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for obstacle in obstacles[:]:
            if player_rect.colliderect(obstacle.rect):
                # 根据障碍物类型处理碰撞
                if obstacle.obstacle_type == ObstacleType.SPEED_REDUCER:
                    self.slow_down(1.5)  # 减速1.5秒
                    obstacle.active = False
                elif obstacle.obstacle_type == ObstacleType.BOOST_BLOCK:
                    self.gain_energy(30)  # 获得能量
                    obstacle.active = False
                elif obstacle.obstacle_type == ObstacleType.WALL:
                    # 撞墙，大幅减速
                    self.slow_down(3.0)
                    self.energy = max(0, self.energy - 20)
                    
    def jump(self):
        if self.on_ground:
            self.velocity_y = self.jump_power
            
    def boost(self):
        if self.energy >= self.boost_energy_cost and self.boost_state not in [BoostState.ACCELERATING, BoostState.SUPER_SPEED, BoostState.COOLDOWN]:
            self.boost_state = BoostState.ACCELERATING
            self.boost_duration = 45  # 45帧加速时间
            self.energy -= self.boost_energy_cost
            
    def super_boost(self):
        if (self.energy >= self.super_speed_energy_cost and 
            self.super_speed_charge >= 100 and 
            self.boost_state not in [BoostState.SUPER_SPEED, BoostState.COOLDOWN]):
            self.boost_state = BoostState.SUPER_SPEED
            self.boost_duration = 90  # 90帧超级加速时间
            self.energy -= self.super_speed_energy_cost
            self.super_speed_charge = 0
            
    def slow_down(self, duration_seconds):
        self.boost_state = BoostState.SLOW_DOWN
        self.boost_duration = int(duration_seconds * 60)  # 转换为帧数
        
    def gain_energy(self, amount):
        self.energy = min(self.max_energy, self.energy + amount)
        
    def draw(self, screen):
        # 绘制轨迹
        if len(self.trail_positions) > 1:
            for i in range(1, len(self.trail_positions)):
                alpha = int(255 * (i / len(self.trail_positions)))
                color = (self.color[0], self.color[1], self.color[2], alpha)
                start_pos = self.trail_positions[i-1]
                end_pos = self.trail_positions[i]
                pygame.draw.line(screen, color, start_pos, end_pos, 3)
                
        # 绘制粒子效果
        for particle in self.boost_particles:
            particle_x, particle_y, _, _, lifetime, color = particle
            alpha = int(255 * (lifetime / 20))
            if len(color) == 3:
                color_with_alpha = (*color, alpha)
            else:
                color_with_alpha = color
                
            radius = max(1, lifetime // 5)
            pygame.draw.circle(screen, color_with_alpha, (int(particle_x), int(particle_y)), radius)
            
        # 绘制玩家
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # 根据状态改变颜色
        if self.boost_state == BoostState.SUPER_SPEED:
            color = (255, 215, 0)  # 金色
        elif self.boost_state == BoostState.ACCELERATING:
            color = (70, 130, 255)  # 亮蓝色
        elif self.boost_state == BoostState.SLOW_DOWN:
            color = (220, 20, 60)  # 深红色
        elif self.boost_state == BoostState.COOLDOWN:
            color = (128, 128, 128)  # 灰色
        else:
            color = self.color
            
        pygame.draw.rect(screen, color, player_rect, border_radius=8)
        
        # 绘制玩家眼睛（增加细节）
        eye_radius = int(5 * self.screen_adapter.scale_x)
        left_eye = (self.x + self.width // 3, self.y + self.height // 3)
        right_eye = (self.x + 2 * self.width // 3, self.y + self.height // 3)
        pygame.draw.circle(screen, (255, 255, 255), left_eye, eye_radius)
        pygame.draw.circle(screen, (255, 255, 255), right_eye, eye_radius)
        
        # 绘制能量条
        energy_bar_width = int(100 * self.screen_adapter.scale_x)
        energy_bar_height = int(10 * self.screen_adapter.scale_y)
        energy_bar_x = self.x
        energy_bar_y = self.y - 20
        
        # 能量条背景
        pygame.draw.rect(screen, (50, 50, 50), 
                         (energy_bar_x, energy_bar_y, energy_bar_width, energy_bar_height), 
                         border_radius=3)
        
        # 能量条填充
        energy_width = int((self.energy / self.max_energy) * energy_bar_width)
        energy_color = (50, 205, 50) if self.energy > 30 else (220, 20, 60)
        pygame.draw.rect(screen, energy_color, 
                         (energy_bar_x, energy_bar_y, energy_width, energy_bar_height), 
                         border_radius=3)
                         
        # 超级速度充能条
        if self.super_speed_charge > 0:
            charge_bar_width = int(80 * self.screen_adapter.scale_x)
            charge_bar_height = int(6 * self.screen_adapter.scale_y)
            charge_bar_x = self.x + 10
            charge_bar_y = self.y - 35
            
            # 充能条背景
            pygame.draw.rect(screen, (50, 50, 50), 
                             (charge_bar_x, charge_bar_y, charge_bar_width, charge_bar_height), 
                             border_radius=2)
            
            # 充能条填充
            charge_width = int((self.super_speed_charge / 100) * charge_bar_width)
            charge_color = (255, 215, 0)  # 金色
            pygame.draw.rect(screen, charge_color, 
                             (charge_bar_x, charge_bar_y, charge_width, charge_bar_height), 
                             border_radius=2)

# 障碍物类
class Obstacle:
    def __init__(self, screen_adapter, obstacle_type, x, y):
        self.screen_adapter = screen_adapter
        self.obstacle_type = obstacle_type
        self.x = x
        self.y = y
        self.active = True
        
        # 根据障碍物类型设置大小和颜色
        if obstacle_type == ObstacleType.SIMPLE:
            self.width = int(30 * screen_adapter.scale_x)
            self.height = int(50 * screen_adapter.scale_y)
            self.color = (139, 0, 0)  # 深红色
        elif obstacle_type == ObstacleType.SPEED_REDUCER:
            self.width = int(40 * screen_adapter.scale_x)
            self.height = int(60 * screen_adapter.scale_y)
            self.color = (255, 140, 0)  # 深橙色
        elif obstacle_type == ObstacleType.BOOST_BLOCK:
            self.width = int(35 * screen_adapter.scale_x)
            self.height = int(35 * screen_adapter.scale_y)
            self.color = (50, 205, 50)  # 酸橙色
        elif obstacle_type == ObstacleType.WALL:
            self.width = int(60 * screen_adapter.scale_x)
            self.height = int(120 * screen_adapter.scale_y)
            self.color = (105, 105, 105)  # 暗灰色
            
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def update(self, scroll_speed):
        self.x -= scroll_speed
        self.rect.x = self.x
        
    def draw(self, screen):
        if self.active:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
            
            # 根据障碍物类型添加标记
            if self.obstacle_type == ObstacleType.SPEED_REDUCER:
                # 绘制减速符号
                pygame.draw.line(screen, (255, 255, 255), 
                                 (self.x + self.width//2 - 10, self.y + self.height//2),
                                 (self.x + self.width//2 + 10, self.y + self.height//2), 3)
            elif self.obstacle_type == ObstacleType.BOOST_BLOCK:
                # 绘制加号
                pygame.draw.line(screen, (255, 255, 255), 
                                 (self.x + self.width//2, self.y + 10),
                                 (self.x + self.width//2, self.y + self.height - 10), 3)
                pygame.draw.line(screen, (255, 255, 255), 
                                 (self.x + 10, self.y + self.height//2),
                                 (self.x + self.width - 10, self.y + self.height//2), 3)

# 游戏主类
class BoostGame:
    def __init__(self):
        self.screen_adapter = ScreenAdapter()
        self.screen = self.screen_adapter.screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = GameState.RUNNING
        
        # 游戏元素
        self.player = Player(self.screen_adapter)
        self.obstacles = []
        self.scroll_speed = 5
        self.obstacle_timer = 0
        self.score = 0
        self.distance = 0
        
        # 背景
        self.background_color = (25, 25, 40)
        self.ground_color = (60, 45, 30)
        self.ground_height = int(100 * self.screen_adapter.scale_y)
        
        # 字体
        self.font_large = pygame.font.SysFont(None, int(48 * self.screen_adapter.scale_x))
        self.font_medium = pygame.font.SysFont(None, int(32 * self.screen_adapter.scale_x))
        self.font_small = pygame.font.SysFont(None, int(24 * self.screen_adapter.scale_x))
        
        # 游戏参数
        self.obstacle_spawn_rate = 90  # 障碍物生成频率（帧数）
        self.speed_increase_rate = 0.001  # 速度随时间增加
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    
                elif event.key == pygame.K_SPACE:
                    if self.game_state == GameState.RUNNING:
                        self.player.jump()
                    elif self.game_state == GameState.GAME_OVER:
                        self.reset_game()
                        
                elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                    if self.game_state == GameState.RUNNING:
                        self.player.boost()
                        
                elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    if self.game_state == GameState.RUNNING:
                        self.player.super_boost()
                        
                elif event.key == pygame.K_p:
                    self.toggle_pause()
                    
            elif event.type == pygame.VIDEORESIZE:
                # 处理窗口大小调整
                self.screen_adapter.screen_width = event.w
                self.screen_adapter.screen_height = event.h
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.screen_adapter.scale_x = self.screen_adapter.screen_width / self.screen_adapter.base_width
                self.screen_adapter.scale_y = self.screen_adapter.screen_height / self.screen_adapter.base_height
                
    def toggle_pause(self):
        if self.game_state == GameState.RUNNING:
            self.game_state = GameState.PAUSED
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.RUNNING
            
    def update(self):
        if self.game_state != GameState.RUNNING:
            return
            
        # 更新玩家
        self.player.update(self.obstacles)
        
        # 更新障碍物
        for obstacle in self.obstacles[:]:
            obstacle.update(self.scroll_speed)
            
            # 移除屏幕外的障碍物
            if obstacle.x + obstacle.width < 0:
                self.obstacles.remove(obstacle)
                self.score += 10
                
        # 生成新障碍物
        self.obstacle_timer += 1
        if self.obstacle_timer >= self.obstacle_spawn_rate:
            self.spawn_obstacle()
            self.obstacle_timer = 0
            
        # 更新游戏参数
        self.distance += self.player.current_speed / 10
        self.scroll_speed = self.player.current_speed
        self.base_speed = min(15, 5 + self.distance / 1000)  # 随着距离增加基础速度
        
        # 游戏结束条件
        if self.player.y > self.screen_adapter.screen_height:
            self.game_state = GameState.GAME_OVER
            
    def spawn_obstacle(self):
        ground_level = self.screen_adapter.screen_height - 100
        
        # 随机选择障碍物类型
        obstacle_type_weights = {
            ObstacleType.SIMPLE: 40,
            ObstacleType.SPEED_REDUCER: 25,
            ObstacleType.BOOST_BLOCK: 20,
            ObstacleType.WALL: 15
        }
        
        obstacle_type = random.choices(
            list(obstacle_type_weights.keys()),
            weights=list(obstacle_type_weights.values())
        )[0]
        
        # 设置障碍物位置
        x = self.screen_adapter.screen_width
        
        if obstacle_type == ObstacleType.WALL:
            y = ground_level - 120
        else:
            y = ground_level - random.randint(50, 80)
            
        # 创建障碍物
        obstacle = Obstacle(self.screen_adapter, obstacle_type, x, y)
        self.obstacles.append(obstacle)
        
    def draw(self):
        # 绘制背景
        self.screen.fill(self.background_color)
        
        # 绘制地面
        ground_rect = pygame.Rect(0, 
                                 self.screen_adapter.screen_height - self.ground_height,
                                 self.screen_adapter.screen_width,
                                 self.ground_height)
        pygame.draw.rect(self.screen, self.ground_color, ground_rect)
        
        # 绘制地面纹理
        for i in range(0, self.screen_adapter.screen_width, 30):
            pygame.draw.line(self.screen, (80, 65, 50),
                            (i, self.screen_adapter.screen_height - self.ground_height),
                            (i, self.screen_adapter.screen_height), 2)
                            
        # 绘制距离标记
        for i in range(0, int(self.distance) + 100, 100):
            mark_x = (self.screen_adapter.screen_width - (i % 1000)) % 1000
            pygame.draw.line(self.screen, (200, 200, 200),
                            (mark_x, self.screen_adapter.screen_height - self.ground_height),
                            (mark_x, self.screen_adapter.screen_height - self.ground_height + 20), 2)
                            
            if i % 500 == 0:
                distance_text = self.font_small.render(f"{i}m", True, (200, 200, 200))
                self.screen.blit(distance_text, (mark_x + 5, self.screen_adapter.screen_height - self.ground_height + 25))
                
        # 绘制障碍物
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
            
        # 绘制玩家
        self.player.draw(self.screen)
        
        # 绘制UI
        self.draw_ui()
        
        # 绘制游戏状态
        if self.game_state == GameState.PAUSED:
            self.draw_pause_screen()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_game_over_screen()
            
        # 更新显示
        pygame.display.flip()
        
    def draw_ui(self):
        # 绘制分数
        score_text = self.font_medium.render(f"分数: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))
        
        # 绘制距离
        distance_text = self.font_medium.render(f"距离: {int(self.distance)}m", True, (255, 255, 255))
        self.screen.blit(distance_text, (20, 60))
        
        # 绘制速度
        speed_text = self.font_medium.render(f"速度: {self.player.current_speed:.1f}x", True, (255, 255, 255))
        self.screen.blit(speed_text, (20, 100))
        
        # 绘制状态
        status_text = self.font_small.render(f"状态: {self.player.boost_state.name}", True, (255, 255, 255))
        self.screen.blit(status_text, (20, 140))
        
        # 绘制控制说明
        controls_y = self.screen_adapter.screen_height - 150
        controls = [
            "空格: 跳跃",
            "Shift: 加速 (消耗能量)",
            "Ctrl: 超级加速 (需要充能)",
            "P: 暂停游戏",
            "ESC: 退出游戏"
        ]
        
        for i, control in enumerate(controls):
            control_text = self.font_small.render(control, True, (200, 200, 200))
            self.screen.blit(control_text, (self.screen_adapter.screen_width - 250, controls_y + i * 25))
            
        # 绘制速度指示器
        self.draw_speed_indicator()
        
    def draw_speed_indicator(self):
        # 绘制速度计背景
        indicator_x = self.screen_adapter.screen_width - 220
        indicator_y = 20
        indicator_width = 200
        indicator_height = 25
        
        pygame.draw.rect(self.screen, (50, 50, 50), 
                         (indicator_x, indicator_y, indicator_width, indicator_height), 
                         border_radius=5)
        
        # 计算速度百分比
        speed_percent = (self.player.current_speed - self.player.min_speed) / (self.player.max_speed - self.player.min_speed)
        speed_width = int(speed_percent * indicator_width)
        
        # 根据速度选择颜色
        if speed_percent < 0.3:
            speed_color = (50, 205, 50)  # 绿色
        elif speed_percent < 0.7:
            speed_color = (255, 215, 0)  # 金色
        else:
            speed_color = (220, 20, 60)  # 深红色
            
        # 绘制速度条
        pygame.draw.rect(self.screen, speed_color, 
                         (indicator_x, indicator_y, speed_width, indicator_height), 
                         border_radius=5)
        
        # 绘制速度计标签
        speed_label = self.font_small.render("速度计", True, (255, 255, 255))
        self.screen.blit(speed_label, (indicator_x, indicator_y + indicator_height + 5))
        
    def draw_pause_screen(self):
        # 半透明覆盖层
        overlay = pygame.Surface((self.screen_adapter.screen_width, self.screen_adapter.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # 暂停文本
        pause_text = self.font_large.render("游戏暂停", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(self.screen_adapter.screen_width // 2, self.screen_adapter.screen_height // 2 - 50))
        self.screen.blit(pause_text, text_rect)
        
        # 继续提示
        continue_text = self.font_medium.render("按 P 键继续游戏", True, (200, 200, 200))
        continue_rect = continue_text.get_rect(center=(self.screen_adapter.screen_width // 2, self.screen_adapter.screen_height // 2 + 50))
        self.screen.blit(continue_text, continue_rect)
        
    def draw_game_over_screen(self):
        # 半透明覆盖层
        overlay = pygame.Surface((self.screen_adapter.screen_width, self.screen_adapter.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 游戏结束文本
        game_over_text = self.font_large.render("游戏结束", True, (220, 20, 60))
        text_rect = game_over_text.get_rect(center=(self.screen_adapter.screen_width // 2, self.screen_adapter.screen_height // 2 - 100))
        self.screen.blit(game_over_text, text_rect)
        
        # 最终分数
        score_text = self.font_medium.render(f"最终分数: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.screen_adapter.screen_width // 2, self.screen_adapter.screen_height // 2 - 30))
        self.screen.blit(score_text, score_rect)
        
        # 最终距离
        distance_text = self.font_medium.render(f"奔跑距离: {int(self.distance)}m", True, (255, 255, 255))
        distance_rect = distance_text.get_rect(center=(self.screen_adapter.screen_width // 2, self.screen_adapter.screen_height // 2 + 10))
        self.screen.blit(distance_text, distance_rect)
        
        # 重新开始提示
        restart_text = self.font_medium.render("按空格键重新开始", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(self.screen_adapter.screen_width // 2, self.screen_adapter.screen_height // 2 + 80))
        self.screen.blit(restart_text, restart_rect)
        
    def reset_game(self):
        self.player = Player(self.screen_adapter)
        self.obstacles = []
        self.obstacle_timer = 0
        self.score = 0
        self.distance = 0
        self.scroll_speed = 5
        self.game_state = GameState.RUNNING
        
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

# 启动游戏
if __name__ == "__main__":
    game = BoostGame()
    game.run()
