# main.py
import pygame
import sys
import time
import os
import random
from player import Player
from obstacle import ObstacleManager
from coin import CoinManager
from save_system import SaveSystem

# 初始化pygame
pygame.init()


class Game:
    def __init__(self):
        """初始化游戏"""
        # 1. 创建窗口和时钟
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("跑酷游戏 - 商店系统版")
        self.clock = pygame.time.Clock()

        # 2. 游戏状态
        self.state = "title"  # 可能的状态: title, menu, shop, playing, game_over, load_save, create_save, saves_list, leaderboard
        self.running = True

        # 3. 游戏核心对象
        self.player = None
        self.obstacle_manager = ObstacleManager()
        self.coin_manager = CoinManager(self.obstacle_manager)
        self.save_system = SaveSystem()

        # 4. 游戏数据
        self.score = 0
        self.high_score = 0
        self.coins = 0
        self.current_game_coins = 0
        self.game_over_time = 0

        # 5. 角色系统
        self.selected_character = None  # 1或2，None表示未选择
        self.character_animation_folders = {1: 'gif', 2: 'gif'}
        self.character_abilities = {
            1: {"can_double_jump": False, "name": "单段跳角色"},
            2: {"can_double_jump": True, "name": "二段跳角色"}
        }

        # 6. 商店系统
        self.shop_items = [
            {"name": "额外生命", "price": 100, "description": "本局游戏获得一次额外生命机会", "type": "extra_life"},
            {"name": "金币翻倍", "price": 150, "description": "本局游戏金币收集数量翻倍", "type": "coin_double"},
            {"name": "星星特效", "price": 200, "description": "跑步时身后有绚丽的星星效果", "type": "star_effect"}
        ]
        self.purchased_items = []

        # 7. 物品效果状态
        self.extra_life_active = False
        self.extra_life_used = False
        self.coin_double_active = False
        self.star_effect_active = False
        self.stars = []  # 星星粒子效果列表

        # 8. 背景系统
        self.background = self.load_background()
        self.menu_background = self.load_uibackground()
        self.shop_background = self.load_shop_background()
        self.bg_x1 = 0
        self.bg_x2 = 800

        # 9. 字体系统
        self.font = pygame.font.Font('image/STKAITI.TTF', 48)
        self.medium_font = pygame.font.Font('image/STKAITI.TTF', 36)
        self.small_font = pygame.font.Font('image/STKAITI.TTF', 24)
        self.ui_font = pygame.font.Font('image/STKAITI.TTF', 28)
        self.input_font = pygame.font.Font('image/STKAITI.TTF', 36)

        # 10. 输入系统
        self.input_text = ""
        self.input_active = False
        self.input_rect = pygame.Rect(300, 350, 200, 40)
        self.input_prompt = "请输入玩家名字:"
        self.input_surface = self.input_font.render("", True, (255, 255, 255))

        # 11. 存档系统相关
        self.save_list_offset = 0
        self.selected_save_index = -1

        # 12. 金币效果系统
        self.coin_effect_timer = 0
        self.coin_effect_text = ""
        self.coin_effect_pos = (0, 0)
        self.show_coin_effect = False

        # 13. 鼠标系统
        self.mouse_pos = (0, 0)

        # 14. 帧率控制
        self.target_fps = 60
        self.last_frame_time = 0
        self.frame_count = 0
        self.frame_timer = 0

        # 15. 加载商店图片
        self.shop_images = self.load_shop_images()

    # ==================== 资源加载方法 ====================
    def load_background(self):
        """加载游戏背景图片"""
        try:
            background_path = 'image/像素背景.png'
            background = pygame.image.load(background_path).convert()
            background = pygame.transform.scale(background, (800, 600))
            print(f"成功加载游戏背景: {background_path}")
            return background
        except Exception as e:
            print(f"加载游戏背景失败: {e}")
            return pygame.Surface((800, 600), pygame.SRCALPHA)

    def load_uibackground(self):
        """加载UI背景图片"""
        try:
            uibackground_path = 'image/背景.jpg'
            uibackground = pygame.image.load(uibackground_path).convert()
            uibackground = pygame.transform.scale(uibackground, (800, 600))
            print(f"成功加载UI背景: {uibackground_path}")
            return uibackground
        except Exception as e:
            print(f"加载UI背景失败: {e}")
            return pygame.Surface((800, 600))

    def load_shop_background(self):
        """加载商店背景图片"""
        try:
            background_path = 'image/shop.png'
            background = pygame.image.load(background_path).convert()
            background = pygame.transform.scale(background, (800, 600))
            print(f"成功加载商店背景: {background_path}")
            return background
        except Exception as e:
            print(f"加载商店背景失败，使用默认背景: {e}")
            # 创建默认商店背景
            background = pygame.Surface((800, 600))
            background.fill((50, 30, 20))  # 深棕色背景
            pygame.draw.rect(background, (139, 69, 19), (50, 100, 700, 400))  # 柜台
            pygame.draw.rect(background, (160, 120, 90), (50, 100, 700, 400), 5)  # 柜台边框
            return background

    def load_shop_images(self):
        """加载商店物品图片"""
        shop_images = {}
        item_images = {
            "extra_life": 'image/heart.png',
            "coin_double": 'image/coin.png',
            "star_effect": 'image/star.png'
        }

        for item_type, path in item_images.items():
            try:
                if os.path.exists(path):
                    image = pygame.image.load(path).convert_alpha()
                    image = pygame.transform.scale(image, (80, 80))
                    shop_images[item_type] = image
                else:
                    # 创建默认图片
                    default_img = pygame.Surface((80, 80), pygame.SRCALPHA)
                    if item_type == "extra_life":
                        # 心形
                        pygame.draw.polygon(default_img, (255, 50, 50),
                                            [(40, 20), (50, 10), (70, 20), (70, 50), (40, 80), (10, 50), (10, 20),
                                             (30, 10)])
                    elif item_type == "coin_double":
                        # 金币
                        pygame.draw.circle(default_img, (255, 215, 0), (40, 40), 35)
                        pygame.draw.circle(default_img, (255, 255, 0), (40, 40), 35, 3)
                        font = pygame.font.Font(None, 40)
                        coin_text = font.render("2X", True, (255, 255, 200))
                        text_rect = coin_text.get_rect(center=(40, 40))
                        default_img.blit(coin_text, text_rect)
                    elif item_type == "star_effect":
                        # 星星
                        points = [(40, 10), (48, 30), (70, 30), (52, 42),
                                  (60, 65), (40, 50), (20, 65), (28, 42),
                                  (10, 30), (32, 30)]
                        pygame.draw.polygon(default_img, (255, 255, 0), points)

                    shop_images[item_type] = default_img
                    print(f"为{item_type}创建了默认图片")
            except Exception as e:
                print(f"加载商店图片失败 {path}: {e}")
                # 创建简单方块作为备用
                default_img = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.rect(default_img, (100, 100, 200), (0, 0, 80, 80))
                shop_images[item_type] = default_img

        return shop_images

    # ==================== 游戏核心控制方法 ====================
    def run(self):
        """运行游戏主循环"""
        while self.running:
            current_time = pygame.time.get_ticks()

            # 计算帧时间
            frame_time = current_time - self.last_frame_time
            self.last_frame_time = current_time

            self.handle_events()
            self.update()
            self.draw()

            if self.state == "create_save" and self.input_active:
                self.clock.tick(30)  # 输入状态下降低帧率
            else:
                self.clock.tick(self.target_fps)  # 正常帧率

        # 退出游戏
        pygame.quit()
        sys.exit()

    def start_game(self):
        """开始游戏"""
        # 如果没有选择角色，默认选择角色1
        if not self.selected_character:
            self.selected_character = 1

        # 应用购买的物品效果
        self.apply_purchased_items()

        # 创建玩家对象
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
        self.stars = []  # 清空星星特效

        # 进入游戏状态
        self.state = "playing"

    def reset_game(self):
        """重置游戏"""
        if self.player:
            self.player.reset_position(100, 250)

        self.obstacle_manager.clear()
        self.coin_manager.clear()
        self.stars = []

        # 重置当前游戏数据
        self.score = 0
        self.current_game_coins = 0

        # 重置物品效果
        self.extra_life_active = False
        self.coin_double_active = False
        self.star_effect_active = False
        self.extra_life_used = False
        self.purchased_items = []

    # ==================== 事件处理方法 ====================
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    self.mouse_pos = event.pos
                    self.handle_mouse_click()

            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

        # 更新鼠标位置
        self.mouse_pos = pygame.mouse.get_pos()

    def handle_keydown(self, event):
        """处理键盘按下事件"""
        if self.state == "playing":
            self.handle_playing_keydown(event)
        elif self.state == "game_over":
            self.handle_game_over_keydown(event)
        elif self.state == "menu":
            self.handle_menu_keydown(event)
        elif self.state == "title":
            self.handle_title_keydown(event)
        elif self.state == "create_save" and self.input_active:
            self.handle_create_save_keydown(event)
        elif self.state == "shop":
            self.handle_shop_keydown(event)

    def handle_playing_keydown(self, event):
        """游戏中按键处理"""
        if event.key == pygame.K_SPACE:
            if self.player:
                self.player.jump()
        elif event.key == pygame.K_ESCAPE:
            self.state = "menu"
            self.reset_game()

    def handle_game_over_keydown(self, event):
        """游戏结束按键处理"""
        if event.key == pygame.K_r:
            self.start_game()
        elif event.key == pygame.K_ESCAPE:
            self.state = "menu"
            self.reset_game()

    def handle_menu_keydown(self, event):
        """主菜单按键处理"""
        if event.key == pygame.K_ESCAPE:
            self.state = "title"
        elif event.key == pygame.K_1:
            self.selected_character = 1
            self.state = "shop"
        elif event.key == pygame.K_2:
            self.selected_character = 2
            self.state = "shop"
        elif event.key == pygame.K_s:
            self.state = "saves_list"
        elif event.key == pygame.K_l:
            self.state = "leaderboard"

    def handle_title_keydown(self, event):
        """标题屏幕按键处理"""
        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_1:
            self.state = "load_save"
        elif event.key == pygame.K_2:
            self.state = "create_save"
            self.input_active = True
            self.input_text = ""
        elif event.key == pygame.K_3:
            self.state = "saves_list"
        elif event.key == pygame.K_4:
            self.state = "leaderboard"

    def handle_create_save_keydown(self, event):
        """创建存档按键处理"""
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

    def handle_shop_keydown(self, event):
        """商店按键处理"""
        if event.key == pygame.K_ESCAPE:
            self.state = "menu"
            self.purchased_items = []  # 退出商店时清空购买记录
        elif event.key == pygame.K_1:
            self.purchase_item(0)  # 购买第一个物品
        elif event.key == pygame.K_2:
            self.purchase_item(1)  # 购买第二个物品
        elif event.key == pygame.K_3:
            self.purchase_item(2)  # 购买第三个物品
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            self.start_game()  # 开始游戏

    def handle_mouse_click(self):
        """处理鼠标点击"""
        if self.state == "title":
            self.handle_title_mouse_click()
        elif self.state == "create_save":
            self.handle_create_save_mouse_click()
        elif self.state == "load_save":
            self.handle_load_save_mouse_click()
        elif self.state == "saves_list":
            self.handle_saves_list_mouse_click()
        elif self.state == "leaderboard":
            self.handle_leaderboard_mouse_click()
        elif self.state == "menu":
            self.handle_menu_mouse_click()
        elif self.state == "shop":
            self.handle_shop_mouse_click()

    def handle_title_mouse_click(self):
        """标题屏幕鼠标点击"""
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

    def handle_create_save_mouse_click(self):
        """创建存档屏幕鼠标点击"""
        # 文本输入框点击激活
        if self.input_rect.collidepoint(self.mouse_pos):
            self.input_active = True
        else:
            self.input_active = False

    def handle_load_save_mouse_click(self):
        """加载存档屏幕鼠标点击"""
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

    def handle_saves_list_mouse_click(self):
        """存档列表屏幕鼠标点击"""
        # 返回按钮
        if 650 <= self.mouse_pos[0] <= 750 and 500 <= self.mouse_pos[1] <= 550:
            self.state = "menu"

    def handle_leaderboard_mouse_click(self):
        """排行榜屏幕鼠标点击"""
        # 返回按钮
        if 650 <= self.mouse_pos[0] <= 750 and 500 <= self.mouse_pos[1] <= 550:
            self.state = "menu"

    def handle_menu_mouse_click(self):
        """主菜单鼠标点击"""
        # 角色选择按钮
        if 250 <= self.mouse_pos[0] <= 350 and 250 <= self.mouse_pos[1] <= 400:
            self.selected_character = 1
            self.state = "shop"
        elif 450 <= self.mouse_pos[0] <= 550 and 250 <= self.mouse_pos[1] <= 400:
            self.selected_character = 2
            self.state = "shop"
        elif 300 <= self.mouse_pos[0] <= 500 and 450 <= self.mouse_pos[1] <= 510:
            self.state = "title"

    def handle_shop_mouse_click(self):
        """商店界面鼠标点击"""
        # 物品点击
        x_start = 200
        item_width = 150
        item_height = 200
        item_spacing = 50

        for i in range(3):
            item_rect = pygame.Rect(x_start + i * (item_width + item_spacing), 200, item_width, item_height)
            if item_rect.collidepoint(self.mouse_pos):
                self.purchase_item(i)
                break

        # 开始游戏按钮
        start_rect = pygame.Rect(300, 450, 200, 60)
        if start_rect.collidepoint(self.mouse_pos):
            self.start_game()

        # 返回按钮
        back_rect = pygame.Rect(50, 500, 100, 50)
        if back_rect.collidepoint(self.mouse_pos):
            self.state = "menu"
            self.purchased_items = []

    # ==================== 商店系统方法 ====================
    def purchase_item(self, item_index):
        """购买物品"""
        if item_index < 0 or item_index >= len(self.shop_items):
            return

        item = self.shop_items[item_index]

        # 检查是否已经购买过
        for purchased in self.purchased_items:
            if purchased["type"] == item["type"]:
                return  # 已经购买过这个类型的物品

        # 检查金币是否足够
        if self.coins >= item["price"]:
            # 扣除金币
            self.coins -= item["price"]
            # 添加到购买列表
            self.purchased_items.append(item.copy())

            # 更新存档中的金币数量
            if self.save_system.current_save:
                self.save_system.current_save["total_coins"] = self.coins
                self.save_system.save_all_saves()

            print(f"购买了 {item['name']}，花费 {item['price']} 金币")

    def apply_purchased_items(self):
        """应用购买的物品效果"""
        self.extra_life_active = False
        self.coin_double_active = False
        self.star_effect_active = False
        self.extra_life_used = False

        for item in self.purchased_items:
            if item["type"] == "extra_life":
                self.extra_life_active = True
            elif item["type"] == "coin_double":
                self.coin_double_active = True
            elif item["type"] == "star_effect":
                self.star_effect_active = True

        # 购买记录会在游戏开始后清空

    # ==================== 存档系统方法 ====================
    def update_game_data_from_save(self):
        """从存档更新游戏数据"""
        if self.save_system.current_save:
            save_info = self.save_system.get_current_save_info()
            if save_info:
                self.coins = save_info["total_coins"]

    # ==================== 游戏更新方法 ====================
    def update(self):
        """更新游戏状态"""
        if self.state == "playing":
            self.update_playing()
        elif self.state == "game_over":
            self.update_game_over()
        elif self.state == "shop":
            self.update_shop()

    def update_playing(self):
        """更新游戏进行状态"""
        # 获取背景滚动速度
        scroll_speed = 8

        # 更新背景滚动
        self.update_background()

        # 更新玩家
        if self.player:
            self.player.update()

        # 更新障碍物
        self.obstacle_manager.update(scroll_speed, self.coin_manager)

        # 更新金币
        self.coin_manager.update(scroll_speed)

        # 检测金币收集
        if self.player:
            # 计算金币倍数
            coin_multiplier = 2 if self.coin_double_active else 1
            collected = self.coin_manager.check_collections(self.player.rect)
            if collected > 0:
                # 应用金币翻倍效果
                collected *= coin_multiplier
                # 每次收集的金币累加到总金币数
                self.coins += collected
                self.current_game_coins += collected
                self.score += collected * 10

                # 显示金币收集效果
                self.show_coin_effect = True
                self.coin_effect_timer = 30
                self.coin_effect_text = f"+{collected}" if coin_multiplier == 1 else f"+{collected // coin_multiplier}×{coin_multiplier}"
                self.coin_effect_pos = (self.player.rect.x, self.player.rect.y - 50)

        # 增加分数
        self.score += 0.1

        # 检测碰撞
        if self.player and self.obstacle_manager.check_collisions(self.player.rect):
            if self.extra_life_active and not self.extra_life_used:
                # 使用额外生命，清除碰撞的障碍物
                self.extra_life_used = True
                # 清除所有与玩家碰撞的障碍物
                for obstacle in self.obstacle_manager.obstacles[:]:
                    if obstacle.rect.colliderect(self.player.rect):
                        obstacle.is_active = False
            else:
                self.state = "game_over"
                self.game_over_time = time.time()

                # 保存游戏记录到存档
                if self.save_system.current_save:
                    # 如果有金币翻倍效果，调整最终金币数
                    final_coins = self.current_game_coins
                    if self.coin_double_active:
                        final_coins *= 2

                    self.save_system.update_save(self.score, final_coins, self.selected_character)
                    self.update_game_data_from_save()

        # 更新星星特效
        if self.star_effect_active and self.player:
            self.update_star_effect()

        # 更新金币收集效果
        if self.show_coin_effect:
            self.coin_effect_timer -= 1
            if self.coin_effect_timer <= 0:
                self.show_coin_effect = False

    def update_game_over(self):
        """更新游戏结束状态"""
        # 5秒后自动返回菜单
        if time.time() - self.game_over_time > 5:
            self.state = "menu"
            self.reset_game()

    def update_shop(self):
        """更新商店状态"""
        # 商店界面不需要特殊更新逻辑
        pass

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

    def update_star_effect(self):
        """更新星星特效"""
        # 每隔一定时间生成新的星星
        if pygame.time.get_ticks() % 5 == 0:
            # 在玩家身后生成星星
            star_x = self.player.rect.x - 20
            star_y = self.player.rect.y + random.randint(-10, 40)
            star_size = random.randint(3, 8)
            star_speed = random.uniform(1.0, 3.0)
            star_color = random.choice([
                (255, 255, 0),  # 黄色
                (255, 200, 0),  # 橙色
                (255, 255, 200),  # 淡黄色
                (255, 100, 100),  # 淡红色
                (100, 255, 255)  # 青色
            ])

            self.stars.append({
                'x': star_x,
                'y': star_y,
                'size': star_size,
                'speed': star_speed,
                'alpha': 255,
                'color': star_color
            })

        # 更新现有星星
        for star in self.stars[:]:
            star['x'] -= star['speed']
            star['alpha'] -= 5

            if star['alpha'] <= 0:
                self.stars.remove(star)

    # ==================== 绘制方法 ====================
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
            self.draw_menu_screen()
        elif self.state == "shop":
            self.draw_shop_screen()
        elif self.state == "playing":
            self.draw_game_screen()
        elif self.state == "game_over":
            self.draw_game_over_screen()

        # 更新显示
        pygame.display.flip()

    # ==================== 各个界面的绘制方法 ====================
    def draw_title_screen(self):
        """绘制标题屏幕"""
        # 绘制背景
        self.screen.blit(self.menu_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("跑酷游戏", True, (255, 255, 255))
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

    def draw_menu_screen(self):
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

        # 绘制角色1图片
        try:
            img = pygame.image.load('gif/Image_1765010414800_frame_1.png').convert_alpha()
            img = pygame.transform.scale(img, (80, 80))
            self.screen.blit(img, (260, 260))
        except:
            pass

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

        # 绘制角色2图片
        try:
            img = pygame.image.load('gif/Image_1765010414800_frame_10.png').convert_alpha()
            img = pygame.transform.scale(img, (80, 80))
            self.screen.blit(img, (460, 260))
        except:
            pass

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
            "点击角色图标选择角色进入商店",
            "或按1键选择角色1，按2键选择角色2",
            "游戏中: 空格键跳跃，ESC键返回菜单",
            "游戏结束后5秒自动返回菜单"
        ]

        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(control_text, (400 - control_text.get_width() // 2, 530 + i * 25))

        # 重置金币效果
        self.show_coin_effect = False

    def draw_shop_screen(self):
        """绘制商店界面"""
        # 绘制背景
        self.screen.blit(self.shop_background, (0, 0))

        # 绘制标题
        title_text = self.font.render("道 具 商 店", True, (255, 255, 200))
        title_rect = title_text.get_rect(center=(400, 80))
        self.screen.blit(title_text, title_rect)

        # 显示当前金币
        coins_text = self.medium_font.render(f"当前金币: {self.coins}", True, (255, 255, 100))
        self.screen.blit(coins_text, (400 - coins_text.get_width() // 2, 130))

        # 显示当前角色
        if self.selected_character:
            char_name = self.character_abilities[self.selected_character]["name"]
            char_text = self.small_font.render(f"当前角色: {char_name}", True, (200, 200, 255))
            self.screen.blit(char_text, (400 - char_text.get_width() // 2, 160))

        # 绘制物品
        x_start = 200
        item_width = 150
        item_height = 200
        item_spacing = 50

        for i, item in enumerate(self.shop_items):
            x_pos = x_start + i * (item_width + item_spacing)
            y_pos = 200

            # 检查是否已购买
            purchased = False
            for purchased_item in self.purchased_items:
                if purchased_item["type"] == item["type"]:
                    purchased = True
                    break

            # 检查是否可购买
            can_purchase = self.coins >= item["price"] and not purchased

            # 绘制物品框
            item_rect = pygame.Rect(x_pos, y_pos, item_width, item_height)
            hovered = item_rect.collidepoint(self.mouse_pos)

            # 选择颜色
            if purchased:
                box_color = (100, 200, 100)  # 已购买，绿色
            elif can_purchase and hovered:
                box_color = (150, 200, 250)  # 可购买且悬停，亮蓝色
            elif can_purchase:
                box_color = (100, 150, 200)  # 可购买，蓝色
            else:
                box_color = (100, 100, 100)  # 不可购买，灰色

            pygame.draw.rect(self.screen, box_color, item_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), item_rect, 3, border_radius=10)

            # 绘制物品图片
            if item["type"] in self.shop_images:
                img = self.shop_images[item["type"]]
                img_rect = img.get_rect(center=(x_pos + item_width // 2, y_pos + 60))
                self.screen.blit(img, img_rect)

            # 绘制物品名称
            name_text = self.small_font.render(item["name"], True, (255, 255, 255))
            self.screen.blit(name_text, (x_pos + item_width // 2 - name_text.get_width() // 2, y_pos + 110))

            # 绘制价格
            price_color = (255, 255, 100) if can_purchase else (150, 150, 150)
            price_text = self.small_font.render(f"价格: {item['price']}金币", True, price_color)
            self.screen.blit(price_text, (x_pos + item_width // 2 - price_text.get_width() // 2, y_pos + 140))

            # 如果已购买，显示"已购买"
            if purchased:
                purchased_text = self.small_font.render("已购买", True, (100, 255, 100))
                self.screen.blit(purchased_text,
                                 (x_pos + item_width // 2 - purchased_text.get_width() // 2, y_pos + 165))

            # 显示快捷键
            key_text = self.small_font.render(f"按 {i + 1} 键购买", True, (200, 255, 200))
            self.screen.blit(key_text, (x_pos + item_width // 2 - key_text.get_width() // 2, y_pos + 185))

        # 绘制物品描述区域
        desc_rect = pygame.Rect(100, 420, 600, 100)
        pygame.draw.rect(self.screen, (40, 40, 40, 200), desc_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), desc_rect, 2)

        # 显示鼠标悬停的物品描述
        hovered_item = None
        for i, item in enumerate(self.shop_items):
            item_rect = pygame.Rect(x_start + i * (item_width + item_spacing), 200, item_width, item_height)
            if item_rect.collidepoint(self.mouse_pos):
                hovered_item = item
                break

        if hovered_item:
            desc_lines = hovered_item["description"].split("，")
            for j, line in enumerate(desc_lines):
                desc_text = self.small_font.render(line, True, (255, 255, 200))
                self.screen.blit(desc_text, (desc_rect.x + 20, desc_rect.y + 10 + j * 25))

        # 绘制已购买物品列表
        if self.purchased_items:
            purchased_text = self.medium_font.render("已购买物品:", True, (100, 255, 100))
            self.screen.blit(purchased_text, (100, 520))

            for i, item in enumerate(self.purchased_items):
                item_text = self.small_font.render(f"✓ {item['name']}", True, (200, 255, 200))
                self.screen.blit(item_text, (250 + i * 150, 520))

        # 绘制开始游戏按钮
        start_rect = pygame.Rect(300, 450, 200, 60)
        start_hovered = start_rect.collidepoint(self.mouse_pos)
        start_color = (100, 200, 100) if start_hovered else (70, 170, 70)

        pygame.draw.rect(self.screen, start_color, start_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), start_rect, 3, border_radius=10)

        start_text = self.medium_font.render("开始游戏", True, (255, 255, 255))
        self.screen.blit(start_text, (400 - start_text.get_width() // 2, 480 - start_text.get_height() // 2))

        # 绘制返回按钮
        back_rect = pygame.Rect(50, 500, 100, 50)
        back_hovered = back_rect.collidepoint(self.mouse_pos)
        back_color = (200, 100, 100) if back_hovered else (170, 70, 70)

        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 3, border_radius=10)

        back_text = self.small_font.render("返回", True, (255, 255, 255))
        self.screen.blit(back_text, (100 - back_text.get_width() // 2, 525 - back_text.get_height() // 2))

        # 绘制操作说明
        instructions = [
            "点击物品或按数字键1-3购买",
            "按空格键或回车键开始游戏",
            "按ESC键返回菜单",
            "购买的商品只在本局游戏有效"
        ]

        for i, text in enumerate(instructions):
            instr_text = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(instr_text, (400 - instr_text.get_width() // 2, 570 + i * 20))

    def draw_game_screen(self):
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

        # 绘制星星特效
        if self.star_effect_active:
            self.draw_star_effect()

        # 绘制金币收集效果
        if self.show_coin_effect:
            self.draw_coin_effect()

        # 绘制UI信息
        self.draw_ui()

    def draw_game_over_screen(self):
        """绘制游戏结束画面"""
        # 首先绘制游戏画面
        self.draw_game_screen()

        # 半透明覆盖层
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # 计算剩余时间
        time_left = max(0, 5 - (time.time() - self.game_over_time))

        # 获取当前存档的最高分
        high_score = 0
        if self.save_system.current_save:
            high_score = self.save_system.current_save["high_score"]

        # 游戏结束文字
        game_over_text = self.font.render("游戏结束!", True, (255, 50, 50))
        score_text = self.font.render(f"最终分数: {int(self.score)}", True, (255, 255, 255))
        high_score_text = self.font.render(f"最高分: {high_score}", True, (255, 255, 100))

        # 计算最终金币（考虑金币翻倍效果）
        final_coins = self.current_game_coins
        if self.coin_double_active:
            final_coins *= 2

        coins_text = self.font.render(f"本局金币: {final_coins}", True, (255, 255, 100))
        restart_text = self.medium_font.render(f"自动返回菜单: {int(time_left)}秒", True, (100, 255, 100))
        manual_text = self.small_font.render("按 R 键立即重玩，ESC 返回菜单", True, (200, 255, 200))

        # 居中显示
        self.screen.blit(game_over_text, (400 - game_over_text.get_width() // 2, 180))
        self.screen.blit(score_text, (400 - score_text.get_width() // 2, 240))
        self.screen.blit(high_score_text, (400 - high_score_text.get_width() // 2, 290))
        self.screen.blit(coins_text, (400 - coins_text.get_width() // 2, 340))
        self.screen.blit(restart_text, (400 - restart_text.get_width() // 2, 400))
        self.screen.blit(manual_text, (400 - manual_text.get_width() // 2, 450))

    # ==================== 特效绘制方法 ====================
    def draw_coin_effect(self):
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

    def draw_star_effect(self):
        """绘制星星特效"""
        for star in self.stars:
            # 创建带透明度的星星
            star_surface = pygame.Surface((star['size'] * 2, star['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(star_surface, (*star['color'], star['alpha']),
                               (star['size'], star['size']), star['size'])
            self.screen.blit(star_surface, (star['x'], star['y']))

    def draw_ui(self):
        """绘制游戏UI（增强版）"""
        if not self.player:
            return

        # 绘制分数
        score_text = self.medium_font.render(f"分数: {int(self.score)}", True, (0, 0, 0))
        self.screen.blit(score_text, (10, 10))

        # 绘制最高分
        high_score = 0
        if self.save_system.current_save:
            high_score = self.save_system.current_save["high_score"]
        high_score_text = self.medium_font.render(f"最高分: {high_score}", True, (0, 0, 0))
        self.screen.blit(high_score_text, (10, 50))

        # 绘制总金币
        coins_text = self.ui_font.render(f"总金币: {self.coins}", True, (255, 255, 100))
        self.screen.blit(coins_text, (250, 20))

        # 绘制当前玩家信息
        player_name = self.character_abilities[self.selected_character]["name"]
        player_text = self.small_font.render(f"当前角色: {player_name}", True, (255, 0, 0))
        self.screen.blit(player_text, (300, 10))

        # 显示当前激活的物品效果（增强版）
        effects_y = 80

        # 绘制效果标题
        effects_title = self.small_font.render("当前效果:", True, (200, 200, 200))
        self.screen.blit(effects_title, (10, effects_y))
        effects_y += 25

        # 效果列表，包含图标、文本和颜色
        effects = []

        # 额外生命效果
        if self.extra_life_active and not self.extra_life_used:
            effects.append(("♥ 额外生命: 激活", (100, 255, 100)))
        elif self.extra_life_used:
            effects.append(("♥ 额外生命: 已使用", (255, 100, 100)))

        # 金币翻倍效果
        if self.coin_double_active:
            effects.append(("✪ 金币翻倍: 激活", (255, 255, 100)))

        # 星星特效
        if self.star_effect_active:
            effects.append(("☆ 星星特效: 激活", (255, 200, 50)))

        # 如果没有效果，显示提示
        if not effects:
            no_effects_text = self.small_font.render("无激活效果", True, (150, 150, 150))
            self.screen.blit(no_effects_text, (10, effects_y))
        else:
            # 绘制所有效果
            for i, (text, color) in enumerate(effects):
                # 绘制效果文本
                effect_text = self.small_font.render(text, True, color)
                self.screen.blit(effect_text, (10, effects_y + i * 28))

        # 绘制控制说明
        controls = [
            "空格键: 跳跃",
            "ESC键: 返回菜单"
        ]

        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, (0, 0, 0))
            self.screen.blit(control_text, (600, 10 + i * 25))


if __name__ == "__main__":
    game = Game()
    game.run()