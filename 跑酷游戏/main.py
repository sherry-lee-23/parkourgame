# main.py
import pygame
import sys
import time
import os
from player import Player
from obstacle import ObstacleManager
from coin import CoinManager
from save_system import SaveSystem

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
        self.state = "title"  # title, menu, playing, game_over, load_save, create_save, saves_list, leaderboard
        self.game_over_time = 0

        # 角色选择状态
        self.selected_character = None  # 1或2，None表示未选择
        self.player = None

        # 角色图片路径
        self.character_animation_folders = {
            1: 'gif',
            2: 'gif'
        }

        # 角色能力
        self.character_abilities = {
            1: {"can_double_jump": False, "name": "单段跳角色"},
            2: {"can_double_jump": True, "name": "二段跳角色"}
        }

        # 创建障碍物管理器
        self.obstacle_manager = ObstacleManager()

        # 创建金币管理器
        self.coin_manager = CoinManager(self.obstacle_manager)

        # 创建存档系统
        self.save_system = SaveSystem()

        # 分数
        self.score = 0
        self.high_score = 0
        self.coins = 0  # 新增：收集的金币数量
        self.max_coins = 0  # 新增：最高金币记录

        # 文本输入相关
        self.input_text = ""
        self.input_active = False
        self.input_rect = pygame.Rect(300, 350, 200, 40)
        self.input_prompt = "请输入玩家名字:"

        self.input_font = pygame.font.Font('image/STKAITI.TTF', 36)
        self.input_surface = self.input_font.render("", True, (255, 255, 255))

        # 存档列表相关（新增）
        self.save_list_offset = 0
        self.selected_save_index = -1

        # 金币收集效果
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

        # 帧率控制
        self.target_fps = 60
        self.last_frame_time = 0
        self.frame_count = 0
        self.frame_timer = 0

        # 鼠标状态
        self.mouse_pos = (0, 0)

        # 存档列表相关（新增）
        self.save_list_offset = 0
        self.selected_save_index = -1

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

    def run(self):
        """运行游戏主循环 - 优化版"""
        while self.running:
            current_time = pygame.time.get_ticks()

            # 计算帧时间
            frame_time = current_time - self.last_frame_time
            self.last_frame_time = current_time

            self.handle_events()
            self.update()
            self.draw()

            # 动态调整帧率，在输入界面降低渲染需求
            if self.state == "create_save" and self.input_active:
                # 在输入界面，可以稍微降低帧率以减少CPU占用
                self.clock.tick(30)
            else:
                self.clock.tick(self.target_fps)

    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 退出游戏
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    self.mouse_pos = event.pos
                    self.handle_mouse_click()  # 调用鼠标点击处理函数

            elif event.type == pygame.KEYDOWN:
                if self.state == "playing":
                    # 空格键跳跃
                    if event.key == pygame.K_SPACE:
                        if self.player:
                            self.player.jump()

                    # 返回菜单
                    elif event.key == pygame.K_ESCAPE:  # 游戏过程中ESC也会退回主页面
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
                        self.state = "title"
                    elif event.key == pygame.K_1:
                        self.selected_character = 1
                        self.start_game()
                    elif event.key == pygame.K_2:
                        self.selected_character = 2
                        self.start_game()
                    elif event.key == pygame.K_s:
                        self.state = "saves_list"
                    elif event.key == pygame.K_l:
                        self.state = "leaderboard"


                elif self.state == "title":
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_1:
                        self.state = "load_save"
                    elif event.key == pygame.K_2:
                        self.state = "create_save"
                        self.input_active = True  # 添加这一行
                        self.input_text = ""
                    elif event.key == pygame.K_3:
                        self.state = "saves_list"
                    elif event.key == pygame.K_4:
                        self.state = "leaderboard"



                elif self.state == "create_save" and self.input_active:
                    if event.key == pygame.K_RETURN:
                        if self.input_text.strip():
                            if self.save_system.create_new_save(self.input_text):
                                self.update_game_data_from_save()
                                self.state = "menu"
                        self.input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "title"

                    else:
                        if len(self.input_text) < 20 and event.unicode.isprintable():
                            self.input_text += event.unicode

                    display = self.input_text + ("|" if self.input_active else "")

                    self.input_surface = self.input_font.render(display, True, (255, 255, 255))

        # 更新鼠标位置
        self.mouse_pos = pygame.mouse.get_pos()

    def handle_mouse_click(self):
        """处理鼠标点击"""
        if self.state == "title":
            # 标题屏幕按钮
            if 300 <= self.mouse_pos[0] <= 500 and 250 <= self.mouse_pos[1] <= 310:
                self.state = "load_save"
            elif 300 <= self.mouse_pos[0] <= 500 and 330 <= self.mouse_pos[1] <= 390:
                self.state = "create_save"
                self.input_active = True
                self.input_text = ""
            elif 300 <= self.mouse_pos[0] <= 500 and 410 <= self.mouse_pos[1] <= 470:
                self.state = "saves_list"
            elif 300 <= self.mouse_pos[0] <= 500 and 490 <= self.mouse_pos[1] <= 550:
                self.running = False

        elif self.state == "create_save":
            # 文本输入框点击激活
            if self.input_rect.collidepoint(self.mouse_pos):
                self.input_active = True
            else:
                self.input_active = False

        elif self.state == "load_save":
            # 存档列表中的点击
            all_saves = self.save_system.get_all_saves()
            y_start = 150
            for i, save in enumerate(all_saves[self.save_list_offset:self.save_list_offset + 5]):
                save_rect = pygame.Rect(150, y_start + i * 80, 500, 70)
                if save_rect.collidepoint(self.mouse_pos):
                    if self.save_system.load_save(save["player_name"]):
                        self.update_game_data_from_save()
                        self.state = "menu"
                    break

            # 返回按钮
            if 650 <= self.mouse_pos[0] <= 750 and 500 <= self.mouse_pos[1] <= 550:
                self.state = "menu"

        elif self.state == "saves_list":
            # 返回按钮
            if 650 <= self.mouse_pos[0] <= 750 and 500 <= self.mouse_pos[1] <= 550:
                self.state = "menu"

        elif self.state == "leaderboard":
            # 返回按钮
            if 650 <= self.mouse_pos[0] <= 750 and 500 <= self.mouse_pos[1] <= 550:
                self.state = "menu"

        elif self.state == "menu":
            # 主菜单按钮
            if 250 <= self.mouse_pos[0] <= 350 and 250 <= self.mouse_pos[1] <= 400:
                self.selected_character = 1
                self.start_game()
            elif 450 <= self.mouse_pos[0] <= 550 and 250 <= self.mouse_pos[1] <= 400:
                self.selected_character = 2
                self.start_game()
            elif 300 <= self.mouse_pos[0] <= 500 and 450 <= self.mouse_pos[1] <= 510:
                self.state = "title"

    def update_game_data_from_save(self):
        """从存档更新游戏数据"""
        if self.save_system.current_save:
            save_info = self.save_system.get_current_save_info()
            if save_info:
                self.coins = save_info["total_coins"]
                # 最高分已在存档中，无需额外存储

    def update(self):
        """更新游戏状态"""
        if self.state == "playing":

            # 获取背景滚动速度
            scroll_speed = 8

            #更新背景滚动
            self.update_background()

            # 更新玩家
            if self.player:
                self.player.update()

            # 更新障碍物
            self.obstacle_manager.update(scroll_speed, self.coin_manager)

            #更新金币
            self.coin_manager.update(scroll_speed)

            # 检测金币收集
            if self.player:
                collected = self.coin_manager.check_collections(self.player.rect)
                if collected > 0:
                    # 每次收集的金币累加到总金币数
                    self.coins += collected
                    self.current_game_coins += collected
                    self.score += collected * 10

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

                # 保存游戏记录到存档
                if self.save_system.current_save:
                    self.save_system.update_save(self.score, self.current_game_coins, self.selected_character)
                    self.update_game_data_from_save()

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
        scroll_speed = 8

        # 更新背景位置
        self.bg_x1 -= scroll_speed
        self.bg_x2 -= scroll_speed

        # 如果背景图片完全移出屏幕，重置到右侧
        if self.bg_x1 <= -800:
            self.bg_x1 = 800
        if self.bg_x2 <= -800:
            self.bg_x2 = 800

    def update_game_data_from_save(self):
        """从存档更新游戏数据"""
        if self.save_system.current_save:
            save_info = self.save_system.get_current_save_info()
            if save_info:
                self.coins = save_info["total_coins"]
                # 最高分已在存档中，无需额外存储

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

        # 重置当前游戏数据
        self.score = 0
        self.current_game_coins = 0
        self.obstacle_manager.clear()
        self.coin_manager.clear()
        self.state = "playing"

    def reset_game(self):
        """重置游戏"""
        if self.player:
            self.player.reset_position(100, 250)

        self.obstacle_manager.clear()
        self.coin_manager.clear()

        # 重置当前游戏数据
        self.score = 0
        self.current_game_coins = 0

    def draw(self):
        """绘制游戏画面"""
        if self.state == "title":
            self.draw_title_screen()
        elif self.state == "create_save":
            self.draw_create_save_screen()
        elif self.state == "load_save":
            self.draw_load_save_screen()
        elif self.state == "saves_list":
            self.draw_saves_list_screen()
        elif self.state == "leaderboard":
            self.draw_leaderboard_screen()
        elif self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "game_over":
            self.draw_game_over()

        # 更新显示
        pygame.display.flip()

    def draw_title_screen(self):
        """绘制标题屏幕"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("跑酷游戏存档版", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 120))
        self.screen.blit(title_text, title_rect)

        # 绘制当前存档信息（如果有）
        if self.save_system.current_save:
            save_info = self.save_system.get_current_save_info()
            if save_info:
                current_save_text = self.medium_font.render(f"当前存档: {save_info['player_name']}", True,
                                                            (100, 255, 100))
                self.screen.blit(current_save_text, (400 - current_save_text.get_width() // 2, 180))

                score_text = self.small_font.render(
                    f"最高分: {save_info['high_score']} | 总金币: {save_info['total_coins']}", True, (200, 200, 255))
                self.screen.blit(score_text, (400 - score_text.get_width() // 2, 220))

        # 绘制菜单按钮
        button_options = [
            ("加载存档", 250, "load_save"),
            ("新建存档", 330, "create_save"),
            ("存档列表", 410, "saves_list"),
            ("退出游戏", 490, "quit")
        ]

        for text, y_pos, action in button_options:
            button_rect = pygame.Rect(300, y_pos, 200, 60)
            hovered = button_rect.collidepoint(self.mouse_pos)
            button_color = (100, 150, 200) if hovered else (70, 120, 170)

            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), button_rect, 3, border_radius=10)

            button_text = self.medium_font.render(text, True, (255, 255, 255))
            self.screen.blit(button_text,
                             (400 - button_text.get_width() // 2, y_pos + 30 - button_text.get_height() // 2))

        # 绘制操作说明
        controls = [
            "按1键: 加载存档",
            "按2键: 新建存档",
            "按3键: 查看存档列表",
            "按4键: 查看排行榜",
            "按ESC键: 退出游戏"
        ]

        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(control_text, (400 - control_text.get_width() // 2, 530 + i * 25))

    def draw_create_save_screen(self):
        """绘制创建存档屏幕"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("新建存档", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 150))
        self.screen.blit(title_text, title_rect)

        # 绘制输入提示
        prompt_text = self.medium_font.render(self.input_prompt, True, (255, 255, 255))
        self.screen.blit(prompt_text, (400 - prompt_text.get_width() // 2, 280))

        # 绘制输入框背景和边框
        pygame.draw.rect(self.screen, (50, 50, 50), self.input_rect)  # 背景
        pygame.draw.rect(self.screen, (255, 255, 255), self.input_rect, 2)  # 边框

        # 绘制输入文本
        input_display = self.input_text
        if self.input_active:
            # 光标闪烁效果：每500ms切换一次显示
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                input_display += "|"

        input_surface = self.input_font.render(input_display, True, (255, 255, 255))
        self.screen.blit(input_surface, (self.input_rect.x + 10, self.input_rect.y + 5))

        # 绘制操作说明
        instructions = [
            "输入玩家名字后按回车确认",
            "按ESC返回标题屏幕",
            "名字不能重复，最多20个字符"
        ]

        for i, text in enumerate(instructions):
            instruction_text = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(instruction_text, (400 - instruction_text.get_width() // 2, 420 + i * 30))

    def draw_load_save_screen(self):
        """绘制加载存档屏幕"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("加载存档", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 100))
        self.screen.blit(title_text, title_rect)

        # 获取所有存档
        all_saves = self.save_system.get_all_saves()

        if not all_saves:
            # 没有存档时显示提示
            no_saves_text = self.medium_font.render("暂无存档，请先创建存档", True, (255, 100, 100))
            self.screen.blit(no_saves_text, (400 - no_saves_text.get_width() // 2, 300))
        else:
            # 显示存档列表
            list_title = self.medium_font.render("选择存档:", True, (255, 255, 255))
            self.screen.blit(list_title, (150, 120))

            y_start = 150
            for i, save in enumerate(all_saves[self.save_list_offset:self.save_list_offset + 5]):
                save_rect = pygame.Rect(150, y_start + i * 80, 500, 70)
                hovered = save_rect.collidepoint(self.mouse_pos)
                save_color = (100, 150, 200) if hovered else (70, 120, 170)

                pygame.draw.rect(self.screen, save_color, save_rect, border_radius=10)
                pygame.draw.rect(self.screen, (255, 255, 255), save_rect, 3, border_radius=10)

                # 存档信息
                name_text = self.medium_font.render(f"{save['player_name']}", True, (255, 255, 255))
                self.screen.blit(name_text, (170, y_start + i * 80 + 15))

                info_text = self.small_font.render(
                    f"最高分: {save['high_score']} | 金币: {save['total_coins']} | 游戏次数: {save['games_played']}",
                    True, (200, 255, 200)
                )
                self.screen.blit(info_text, (170, y_start + i * 80 + 45))

        # 绘制返回按钮
        back_rect = pygame.Rect(650, 500, 100, 50)
        hovered = back_rect.collidepoint(self.mouse_pos)
        back_color = (200, 100, 100) if hovered else (170, 70, 70)
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 3, border_radius=10)

        back_text = self.small_font.render("返回", True, (255, 255, 255))
        self.screen.blit(back_text, (700 - back_text.get_width() // 2, 525 - back_text.get_height() // 2))

        # 绘制操作说明
        instruction_text = self.small_font.render("点击存档加载，按ESC返回菜单", True, (200, 200, 200))
        self.screen.blit(instruction_text, (400 - instruction_text.get_width() // 2, 560))

    def draw_saves_list_screen(self):
        """绘制存档列表屏幕"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("存档管理", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 80))
        self.screen.blit(title_text, title_rect)

        # 获取所有存档
        all_saves = self.save_system.get_all_saves()

        # 显示存档总数
        total_text = self.medium_font.render(f"总存档数: {len(all_saves)}", True, (255, 255, 255))
        self.screen.blit(total_text, (400 - total_text.get_width() // 2, 130))

        # 显示当前存档
        if self.save_system.current_save:
            current_text = self.medium_font.render(f"当前存档: {self.save_system.current_save['player_name']}", True,
                                                   (100, 255, 100))
            self.screen.blit(current_text, (400 - current_text.get_width() // 2, 170))

        # 显示所有存档详细信息
        y_pos = 220
        for i, save in enumerate(all_saves):
            if y_pos > 500:  # 限制显示数量
                break

            save_info = f"{i + 1}. {save['player_name']} - 最高分: {save['high_score']} - 金币: {save['total_coins']}"
            if len(save_info) > 60:
                save_info = save_info[:57] + "..."
            save_text = self.small_font.render(save_info, True, (220, 220, 220))
            self.screen.blit(save_text, (100, y_pos))

            date_text = self.small_font.render(f"最后游戏: {save['last_played']}", True, (180, 180, 200))
            self.screen.blit(date_text, (100, y_pos + 25))

            y_pos += 60

        # 绘制返回按钮
        back_rect = pygame.Rect(650, 500, 100, 50)
        hovered = back_rect.collidepoint(self.mouse_pos)
        back_color = (200, 100, 100) if hovered else (170, 70, 70)
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 3, border_radius=10)

        back_text = self.small_font.render("返回", True, (255, 255, 255))
        self.screen.blit(back_text, (700 - back_text.get_width() // 2, 525 - back_text.get_height() // 2))

    def draw_leaderboard_screen(self):
        """绘制排行榜屏幕"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("排行榜", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 80))
        self.screen.blit(title_text, title_rect)

        # 获取排行榜数据
        score_leaderboard = self.save_system.get_leaderboard(10)
        coins_leaderboard = self.save_system.get_coins_leaderboard(10)

        # 绘制最高分排行榜
        score_title = self.medium_font.render("最高分排行榜", True, (255, 200, 100))
        self.screen.blit(score_title, (150, 130))

        y_pos = 180
        for i, save in enumerate(score_leaderboard):
            rank_text = f"{i + 1}. {save['player_name']}: {save['high_score']}分"
            if i == 0:
                rank_color = (255, 215, 0)  # 金色
            elif i == 1:
                rank_color = (192, 192, 192)  # 银色
            elif i == 2:
                rank_color = (205, 127, 50)  # 铜色
            else:
                rank_color = (220, 220, 220)

            rank_surface = self.small_font.render(rank_text, True, rank_color)
            self.screen.blit(rank_surface, (150, y_pos))
            y_pos += 30

        # 绘制金币排行榜
        coins_title = self.medium_font.render("金币排行榜", True, (255, 200, 100))
        self.screen.blit(coins_title, (450, 130))

        y_pos = 180
        for i, save in enumerate(coins_leaderboard):
            rank_text = f"{i + 1}. {save['player_name']}: {save['total_coins']}金币"
            if i == 0:
                rank_color = (255, 215, 0)  # 金色
            elif i == 1:
                rank_color = (192, 192, 192)  # 银色
            elif i == 2:
                rank_color = (205, 127, 50)  # 铜色
            else:
                rank_color = (220, 220, 220)

            rank_surface = self.small_font.render(rank_text, True, rank_color)
            self.screen.blit(rank_surface, (450, y_pos))
            y_pos += 30

        # 绘制返回按钮
        back_rect = pygame.Rect(650, 500, 100, 50)
        hovered = back_rect.collidepoint(self.mouse_pos)
        back_color = (200, 100, 100) if hovered else (170, 70, 70)
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 3, border_radius=10)

        back_text = self.small_font.render("返回", True, (255, 255, 255))
        self.screen.blit(back_text, (700 - back_text.get_width() // 2, 525 - back_text.get_height() // 2))

    def draw_menu(self):
        """绘制主菜单"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("选择你的角色", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 150))
        self.screen.blit(title_text, title_rect)

        # 绘制当前存档信息
        if self.save_system.current_save:
            save_info = self.save_system.get_current_save_info()
            if save_info:
                player_text = self.medium_font.render(f"玩家: {save_info['player_name']}", True, (100, 255, 100))
                self.screen.blit(player_text, (400 - player_text.get_width() // 2, 170))

                stats_text = self.small_font.render(
                    f"最高分: {save_info['high_score']} | 总金币: {save_info['total_coins']}", True, (200, 200, 255))
                self.screen.blit(stats_text, (400 - stats_text.get_width() // 2, 210))

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

        # 重置金币效果
        self.show_coin_effect = False

    def draw_game(self):
        """绘制游戏画面"""
        # 绘制背景
        self.screen.blit(self.background, (self.bg_x1, 0))
        self.screen.blit(self.background, (self.bg_x2, 0))
        # 绘制障碍物
        self.obstacle_manager.draw(self.screen)

        # 绘制金币
        self.coin_manager.draw(self.screen)

        # 绘制玩家
        if self.player:
            self.player.draw(self.screen)

        # 绘制金币收集效果
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

        # 获取当前存档的最高分
        high_score = 0
        if self.save_system.current_save:
            high_score = self.save_system.current_save["high_score"]

        high_score_text = self.font.render(f"最高分: {high_score}", True, (255, 255, 100))
        coins_text = self.font.render(f"总金币: {self.coins}", True, (255, 255, 100))
        restart_text = self.medium_font.render(f"自动返回菜单: {int(time_left)}秒", True, (100, 255, 100))
        manual_text = self.small_font.render("按 R 键立即重玩，ESC 返回菜单", True, (200, 255, 200))

        # 居中显示
        self.screen.blit(game_over_text, (400 - game_over_text.get_width() // 2, 180))
        self.screen.blit(score_text, (400 - score_text.get_width() // 2, 240))
        self.screen.blit(high_score_text, (400 - high_score_text.get_width() // 2, 290))
        self.screen.blit(coins_text, (400 - coins_text.get_width() // 2, 340))
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