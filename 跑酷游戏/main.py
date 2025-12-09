# main.py
import pygame
import sys
import time
import os
from player import Player
from obstacle import ObstacleManager

# 初始化pygame
pygame.init()

#增添一行来进行测试
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
        self.character_images = {
            1: 'gif/Image_1765010414800_frame_1.png',  # 角色1图片
            2: 'gif/Image_1765010414800_frame_13.png'  # 角色2图片
        }

        # 角色能力
        self.character_abilities = {
            1: {"can_double_jump": False, "name": "单段跳角色"},
            2: {"can_double_jump": True, "name": "二段跳角色"}
        }

        # 创建障碍物管理器
        self.obstacle_manager = ObstacleManager()

        # 分数
        self.score = 0
        self.high_score = 0

        # 加载背景图片
        self.background = self.load_background()

        # 字体
        self.font = pygame.font.Font('image/STKAITI.TTF', 48)
        self.medium_font = pygame.font.Font('image/STKAITI.TTF', 36)
        self.small_font = pygame.font.Font('image/STKAITI.TTF', 24)

        # 鼠标状态
        self.mouse_pos = (0, 0)

    def load_background(self):
        """加载背景图片"""
        # 尝试加载背景图片
        background_path = 'image/像素背景.png'

        if os.path.exists(background_path):
            try:
                # 加载图片并调整大小为800x600
                background = pygame.image.load(background_path).convert()
                background = pygame.transform.scale(background, (800, 600))
                print(f"成功加载背景图片: {background_path}")
                return background
            except Exception as e:
                print(f"无法加载背景图片 {background_path}: {e}")

        # 如果找不到背景图片，使用默认的纯色背景
        print("未找到背景图片，使用默认背景")
        return None

    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
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
                    elif event.key == pygame.K_ESCAPE:
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
            # 更新玩家
            if self.player:
                self.player.update()

            # 更新障碍物
            self.obstacle_manager.update()

            # 增加分数
            self.score += 0.1

            # 检测碰撞
            if self.player and self.obstacle_manager.check_collisions(self.player.rect):
                self.state = "game_over"
                self.game_over_time = time.time()
                if self.score > self.high_score:
                    self.high_score = int(self.score)

        elif self.state == "game_over":
            # 5秒后自动返回菜单
            if time.time() - self.game_over_time > 5:
                self.state = "menu"
                self.reset_game()

    def start_game(self):
        """开始游戏"""
        # 如果没有选择角色，默认选择角色1
        if not self.selected_character:
            self.selected_character = 1

        # 创建玩家对象
        ability = self.character_abilities[self.selected_character]
        image_path = self.character_images[self.selected_character]
        self.player = Player(100, 250,
                             can_double_jump=ability["can_double_jump"],
                             player_id=self.selected_character,
                             image_path=image_path)

        # 重置游戏状态
        self.score = 0
        self.obstacle_manager.clear()
        self.state = "playing"

    def reset_game(self):
        """重置游戏"""
        # 重置玩家位置
        if self.player:
            self.player.reset_position(100, 250)

        # 清空障碍物
        self.obstacle_manager.clear()

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
        self.screen.fill((50, 50, 80))

        # 绘制标题
        title_text = self.font.render("选择你的角色", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 150))
        self.screen.blit(title_text, title_rect)

        # 绘制角色1选择框
        char1_rect = pygame.Rect(250, 250, 100, 150)
        char1_hovered = char1_rect.collidepoint(self.mouse_pos)
        char1_color = (100, 150, 200) if char1_hovered else (70, 120, 170)
        pygame.draw.rect(self.screen, char1_color, char1_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), char1_rect, 3, border_radius=10)

        # 绘制角色1图片或占位符
        try:
            img = pygame.image.load(self.character_images[1]).convert_alpha()
            img = pygame.transform.scale(img, (80, 80))
            self.screen.blit(img, (260, 260))
        except:
            pygame.draw.rect(self.screen, (0, 0, 255), (260, 260, 80, 80))

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
        try:
            img = pygame.image.load(self.character_images[2]).convert_alpha()
            img = pygame.transform.scale(img, (80, 80))
            self.screen.blit(img, (460, 260))
        except:
            pygame.draw.rect(self.screen, (0, 255, 0), (460, 260, 80, 80))

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

    def draw_game(self):
        """绘制游戏画面"""
        # 绘制背景
        if self.background:
            # 使用背景图片
            self.screen.blit(self.background, (0, 0))
        else:
            # 如果没有背景图片，使用原来的纯色背景
            self.screen.fill((200, 230, 255))  # 淡蓝色天空
            # 绘制地面
            pygame.draw.rect(self.screen, (139, 69, 19), (0, 300, 800, 300))  # 棕色地面
            pygame.draw.line(self.screen, (160, 120, 80), (0, 300), (800, 300), 3)  # 地面线

        # 绘制障碍物
        self.obstacle_manager.draw(self.screen)

        # 绘制玩家
        if self.player:
            self.player.draw(self.screen)

        # 绘制UI信息
        self.draw_ui()

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
        game_over_text = self.font.render("游戏结束!", True, (255, 0, 0))
        score_text = self.font.render(f"最终分数: {int(self.score)}", True, (255, 255, 255))
        high_score_text = self.font.render(f"最高分: {self.high_score}", True, (255, 255, 0))
        restart_text = self.medium_font.render(f"自动返回菜单: {int(time_left)}秒", True, (0, 255, 0))
        manual_text = self.small_font.render("按 R 键立即重玩，ESC 返回菜单", True, (200, 255, 200))

        # 居中显示
        self.screen.blit(game_over_text, (400 - game_over_text.get_width() // 2, 200))
        self.screen.blit(score_text, (400 - score_text.get_width() // 2, 260))
        self.screen.blit(high_score_text, (400 - high_score_text.get_width() // 2, 310))
        self.screen.blit(restart_text, (400 - restart_text.get_width() // 2, 370))
        self.screen.blit(manual_text, (400 - manual_text.get_width() // 2, 420))

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