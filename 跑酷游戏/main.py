# main.py
import pygame
import sys
import time
import os
from player import Player
from obstacle import ObstacleManager
from coin import CoinManager

# 初始化pygame
pygame.init()

class Game:
    def __init__(self):
        # 创建窗口
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("跑酷游戏 - 单角色版")

        # 创建时钟
        self.clock = pygame.time.Clock()
        self.running = True

        # 游戏状态
        self.state = "menu"  # menu, playing, game_over
        self.game_over_time = 0

        # 角色选择状态
        self.selected_character = None  # 1或2，None表示未选择
        self.player = None  # 玩家对象

        # 角色图片路径
        self.character_animation_folders = {
            1: 'gif',  # 角色1动画帧文件夹
            2: 'gif'  # 角色2动画帧文件夹
        }

        # 角色能力
        self.character_abilities = {
            1: {"can_double_jump": False, "name": "单段跳角色"},
            2: {"can_double_jump": True, "name": "二段跳角色"}
        }

        # 创建障碍物管理器
        self.obstacle_manager = ObstacleManager()

        # 创建金币管理器（新增）
        self.coin_manager = CoinManager(self.obstacle_manager)

        # 分数
        self.score = 0
        self.high_score = 0
        self.coins = 0  # 新增：收集的金币数量
        self.max_coins = 0  # 新增：最高金币记录

        # 金币收集效果（新增）
        self.coin_effect_timer = 0
        self.coin_effect_text = ""
        self.coin_effect_pos = (0, 0)
        self.show_coin_effect = False

        # 加载背景图片
        self.background = self.load_background()

        # 加载菜单UI背景图片
        self.menu_background = self.load_uibackground()

        #滚动背景位置
        self.bg_x1 = 0
        self.bg_x2 = 800

        # 字体
        self.font = pygame.font.Font('image/STKAITI.TTF', 48)
        self.medium_font = pygame.font.Font('image/STKAITI.TTF', 36)
        self.small_font = pygame.font.Font('image/STKAITI.TTF', 24)
        self.ui_font = pygame.font.Font('image/STKAITI.TTF', 28)

        # 鼠标状态
        self.mouse_pos = (0, 0)

    def load_background(self):
        """加载背景图片"""
        # 尝试加载背景图片
        background_path = 'image/像素背景.png'
        # 加载图片并调整大小为800x600
        background = pygame.image.load(background_path).convert()
        background = pygame.transform.scale(background, (800, 600))
        print(f"成功加载背景图片: {background_path}")
        return background

    def load_uibackground(self):
        """加载背景图片"""
        # 尝试加载背景图片
        uibackground_path = 'image/背景.jpg'
        # 加载图片并调整大小为800x600
        uibackground = pygame.image.load(uibackground_path).convert()
        uibackground = pygame.transform.scale(uibackground, (800, 600))
        print(f"成功加载背景图片: {uibackground_path}")
        return uibackground

    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:#退出游戏
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    self.mouse_pos = event.pos

                    # 菜单状态下的点击
                    if self.state == "menu":
                        # 检查是否点击了角色1选择区域
                        if 250 <= self.mouse_pos[0] <= 350 and 250 <= self.mouse_pos[1] <= 400:
                            self.selected_character = 1
                            self.start_game()

                        # 检查是否点击了角色2选择区域
                        elif 450 <= self.mouse_pos[0] <= 550 and 250 <= self.mouse_pos[1] <= 400:
                            self.selected_character = 2
                            self.start_game()

                        # 检查是否点击了退出按钮
                        elif 300 <= self.mouse_pos[0] <= 500 and 450 <= self.mouse_pos[1] <= 510:
                            self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.state == "playing":
                    # 空格键跳跃
                    if event.key == pygame.K_SPACE:
                        if self.player:
                            self.player.jump()

                    # 返回菜单
                    elif event.key == pygame.K_ESCAPE:#游戏过程中ESC也会退回主页面
                        self.state = "menu"
                        self.reset_game()

                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                        self.reset_game()

                elif self.state == "menu":
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_1:
                        self.selected_character = 1
                        self.start_game()
                    elif event.key == pygame.K_2:
                        self.selected_character = 2
                        self.start_game()

        # 更新鼠标位置
        self.mouse_pos = pygame.mouse.get_pos()

    def update(self):
        """更新游戏状态"""
        if self.state == "playing":

            # 获取背景滚动速度
            scroll_speed = 8  # 与背景滚动速度相同

            #更新背景滚动
            self.update_background()

            # 更新玩家
            if self.player:
                self.player.update()

            # 更新障碍物
            self.obstacle_manager.update()

            #更新金币
            self.coin_manager.update(scroll_speed)

            # 检测金币收集（新增）
            if self.player:
                collected = self.coin_manager.check_collections(self.player.rect)
                if collected > 0:
                    # 每次收集的金币累加到总金币数
                    self.coins += collected
                    self.score += collected * 10  # 每个金币加10分

                    # 显示金币收集效果
                    self.show_coin_effect = True
                    self.coin_effect_timer = 30  # 显示30帧
                    self.coin_effect_text = f"+{collected}"  # 改为显示"+1"
                    self.coin_effect_pos = (self.player.rect.x, self.player.rect.y - 50)

            # 增加分数
            self.score += 0.1

            # 检测碰撞
            if self.player and self.obstacle_manager.check_collisions(self.player.rect):
                self.state = "game_over"  # 碰撞即跳到游戏结束页面
                self.game_over_time = time.time()
                if self.score > self.high_score:  # 更新最高分
                    self.high_score = int(self.score)
                if self.coins > self.max_coins:  # 新增：更新最多金币记录
                    self.max_coins = self.coins

            # 更新金币收集效果（新增）
            if self.show_coin_effect:
                self.coin_effect_timer -= 1
                if self.coin_effect_timer <= 0:
                    self.show_coin_effect = False


        elif self.state == "game_over":
            # 5秒后自动返回菜单
            if time.time() - self.game_over_time > 5:
                self.state = "menu"
                self.reset_game()

    def update_background(self):
        """更新背景滚动位置"""
        # 使用与障碍物相同的速度滚动背景
        # 障碍物默认速度为2（在obstacle.py中设置）
        scroll_speed = 8

        # 更新背景位置
        self.bg_x1 -= scroll_speed
        self.bg_x2 -= scroll_speed

        # 如果背景图片完全移出屏幕，重置到右侧
        if self.bg_x1 <= -800:
            self.bg_x1 = 800
        if self.bg_x2 <= -800:
            self.bg_x2 = 800

    def start_game(self):
        """开始游戏"""
        # 如果没有选择角色，默认选择角色1
        if not self.selected_character:
            self.selected_character = 1

        # 创建玩家对象（使用动画帧方案1）
        ability = self.character_abilities[self.selected_character]
        animation_folder = self.character_animation_folders[self.selected_character]

        self.player = Player(100, 250,
                             can_double_jump=ability["can_double_jump"],
                             player_id=self.selected_character,
                             image_folder=animation_folder)

        # 重置游戏状态（金币不清零）
        self.score = 0
        self.obstacle_manager.clear()
        self.coin_manager.clear()  # 新增：清空金币
        self.state = "playing"

    def reset_game(self):
        """重置游戏"""
        # 重置玩家位置
        if self.player:
            self.player.reset_position(100, 250)

        # 清空障碍物
        self.obstacle_manager.clear()
        self.coin_manager.clear()  # 新增：清空金币

        # 重置分数
        self.score = 0

    def draw(self):
        """绘制游戏画面"""
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "game_over":
            self.draw_game_over()

        # 更新显示
        pygame.display.flip()

    def draw_menu(self):
        """绘制主菜单"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("选择你的角色", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 150))
        self.screen.blit(title_text, title_rect)

        # 绘制总金币数（新增）
        coins_text = self.medium_font.render(f"总金币: {self.coins}", True, (255, 255, 100))
        coins_rect = coins_text.get_rect(center=(400, 180))
        self.screen.blit(coins_text, coins_rect)

        # 绘制角色1选择框
        char1_rect = pygame.Rect(250, 250, 100, 150)
        char1_hovered = char1_rect.collidepoint(self.mouse_pos)
        char1_color = (100, 150, 200) if char1_hovered else (70, 120, 170)
        pygame.draw.rect(self.screen, char1_color, char1_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), char1_rect, 3, border_radius=10)

        # 绘制角色1图片或占位符
        img = pygame.image.load('gif/Image_1765010414800_frame_1.png').convert_alpha()
        img = pygame.transform.scale(img, (80, 80))
        self.screen.blit(img, (260, 260))

        # 绘制角色1描述
        char1_text = self.small_font.render("角色1", True, (255, 255, 255))
        self.screen.blit(char1_text, (300 - char1_text.get_width() // 2, 350))
        ability_text = self.small_font.render("单段跳", True, (200, 200, 255))
        self.screen.blit(ability_text, (300 - ability_text.get_width() // 2, 375))
        key_text = self.small_font.render("按1键选择", True, (200, 255, 200))
        self.screen.blit(key_text, (300 - key_text.get_width() // 2, 400))

        # 绘制角色2选择框
        char2_rect = pygame.Rect(450, 250, 100, 150)
        char2_hovered = char2_rect.collidepoint(self.mouse_pos)
        char2_color = (100, 200, 150) if char2_hovered else (70, 170, 120)
        pygame.draw.rect(self.screen, char2_color, char2_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), char2_rect, 3, border_radius=10)

        # 绘制角色2图片或占位符
        img = pygame.image.load('gif/Image_1765010414800_frame_10.png').convert_alpha()
        img = pygame.transform.scale(img, (80, 80))
        self.screen.blit(img, (460, 260))


        # 绘制角色2描述
        char2_text = self.small_font.render("角色2", True, (255, 255, 255))
        self.screen.blit(char2_text, (500 - char2_text.get_width() // 2, 350))
        ability_text = self.small_font.render("二段跳", True, (200, 200, 255))
        self.screen.blit(ability_text, (500 - ability_text.get_width() // 2, 375))
        key_text = self.small_font.render("按2键选择", True, (200, 255, 200))
        self.screen.blit(key_text, (500 - key_text.get_width() // 2, 400))

        # 绘制退出按钮
        quit_rect = pygame.Rect(300, 450, 200, 60)
        quit_hovered = quit_rect.collidepoint(self.mouse_pos)
        quit_color = (200, 100, 100) if quit_hovered else (170, 70, 70)
        pygame.draw.rect(self.screen, quit_color, quit_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), quit_rect, 3, border_radius=10)

        quit_text = self.medium_font.render("退出游戏", True, (255, 255, 255))
        self.screen.blit(quit_text, (400 - quit_text.get_width() // 2, 480 - quit_text.get_height() // 2))

        # 绘制操作说明
        controls = [
            "点击角色图标选择角色开始游戏",
            "或按1键选择角色1，按2键选择角色2",
            "游戏中: 空格键跳跃，ESC键返回菜单",
            "游戏结束后5秒自动返回菜单"
        ]

        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(control_text, (400 - control_text.get_width() // 2, 530 + i * 25))

        # 重置金币效果（新增）
        self.show_coin_effect = False

    def draw_game(self):
        """绘制游戏画面"""
        # 绘制背景
        self.screen.blit(self.background, (self.bg_x1, 0))
        self.screen.blit(self.background, (self.bg_x2, 0))
        # 绘制障碍物
        self.obstacle_manager.draw(self.screen)

        # 绘制金币（新增）
        self.coin_manager.draw(self.screen)

        # 绘制玩家
        if self.player:
            self.player.draw(self.screen)

        # 绘制金币收集效果（新增）
        if self.show_coin_effect:
            self.draw_coin_effect()

        # 绘制UI信息
        self.draw_ui()

    def draw_coin_effect(self):  # 新增方法
        """绘制金币收集效果"""
        # 创建效果文本
        effect_font = pygame.font.Font('image/STKAITI.TTF', 32)
        effect_text = effect_font.render(self.coin_effect_text, True, (255, 255, 100))

        # 添加透明度效果
        alpha = min(255, self.coin_effect_timer * 8)
        temp_surface = effect_text.copy()
        temp_surface.set_alpha(alpha)

        # 绘制效果文本
        effect_rect = effect_text.get_rect(center=self.coin_effect_pos)
        self.screen.blit(temp_surface, effect_rect)

        # 更新位置（向上移动）
        self.coin_effect_pos = (self.coin_effect_pos[0], self.coin_effect_pos[1] - 1)



    def draw_ui(self):
        """绘制游戏UI"""
        if not self.player:
            return

        # 绘制分数
        score_text = self.medium_font.render(f"分数: {int(self.score)}", True, (0, 0, 0))
        self.screen.blit(score_text, (10, 10))

        # 绘制最高分
        high_score_text = self.medium_font.render(f"最高分: {self.high_score}", True, (0, 0, 0))
        self.screen.blit(high_score_text, (10, 50))

        # 绘制总金币（新增）
        coins_text = self.ui_font.render(f"总金币: {self.coins}", True, (255, 255, 100))
        self.screen.blit(coins_text, (250, 20))

        # 绘制当前玩家信息
        player_name = self.character_abilities[self.selected_character]["name"]
        player_text = self.small_font.render(f"当前角色: {player_name}", True, (255, 0, 0))
        self.screen.blit(player_text, (300, 10))

        # 绘制控制说明
        controls = [
            "空格键: 跳跃",
            "ESC键: 返回菜单"
        ]

        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, (0, 0, 0))
            self.screen.blit(control_text, (600, 10 + i * 25))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 首先绘制游戏画面
        self.draw_game()

        # 半透明覆盖层
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # 计算剩余时间
        time_left = max(0, 5 - (time.time() - self.game_over_time))

        # 游戏结束文字
        game_over_text = self.font.render("游戏结束!", True, (255, 50, 50))
        score_text = self.font.render(f"最终分数: {int(self.score)}", True, (255, 255, 255))
        high_score_text = self.font.render(f"最高分: {self.high_score}", True, (255, 255, 100))
        coins_text = self.font.render(f"总金币: {self.coins}", True, (255, 255, 100))  # 新增
        restart_text = self.medium_font.render(f"自动返回菜单: {int(time_left)}秒", True, (100, 255, 100))
        manual_text = self.small_font.render("按 R 键立即重玩，ESC 返回菜单", True, (200, 255, 200))

        # 居中显示
        self.screen.blit(game_over_text, (400 - game_over_text.get_width() // 2, 180))
        self.screen.blit(score_text, (400 - score_text.get_width() // 2, 240))
        self.screen.blit(high_score_text, (400 - high_score_text.get_width() // 2, 290))
        self.screen.blit(coins_text, (400 - coins_text.get_width() // 2, 340))  # 新增
        self.screen.blit(restart_text, (400 - restart_text.get_width() // 2, 400))
        self.screen.blit(manual_text, (400 - manual_text.get_width() // 2, 450))

    def run(self):
        """运行游戏主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS

        # 退出游戏
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()