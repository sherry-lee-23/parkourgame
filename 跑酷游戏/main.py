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
from battle_system import BattleBullet, BattleMonster
from enemy import EnemyManager


# 初始化pygame
pygame.init()


class Game:
    def __init__(self):
        """初始化游戏"""
        # 1. 创建窗口和时钟
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("跑酷游戏")
        self.clock = pygame.time.Clock()

        # 2. 游戏状态
        self.state = "title"  # 可能的状态: title, menu, shop, playing, battle, paused, game_over, load_save, saves_list
        self.running = True
        self.paused_state = None

        # 3. 游戏核心对象
        self.player = None
        self.obstacle_manager = ObstacleManager()
        self.coin_manager = CoinManager(self.obstacle_manager)
        self.save_system = SaveSystem()
        self.enemy_manager = EnemyManager()

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
            1: {"can_double_jump": False, "name": "角色一"},
            2: {"can_double_jump": True, "name": "角色二"}
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

        # 8. 背景系统（修改为三层背景）
        self.bg_layers = self.load_background_layers()  # 三层背景
        # 每层背景的x坐标（初始位置）
        self.bg1_x1, self.bg1_x2 = 0, 800  # 远层（最慢）
        self.bg2_x1, self.bg2_x2 = 0, 800  # 中层（中速）
        self.bg3_x1, self.bg3_x2 = 0, 800  # 近层（最快）
        # 每层背景的移动速度（可自定义）
        self.bg_speeds = {
            "bg1": 2,  # 远层：最慢
            "bg2": 5,  # 中层：中速
            "bg3": 8  # 近层：最快（原速度）
        }
        self.menu_background = self.load_uibackground()
        self.shop_background = self.load_shop_background()

        # 9. 字体系统
        self.font = pygame.font.Font('image/STKAITI.TTF', 48)
        self.medium_font = pygame.font.Font('image/STKAITI.TTF', 36)
        self.small_font = pygame.font.Font('image/STKAITI.TTF', 24)
        self.ui_font = pygame.font.Font('image/STKAITI.TTF', 28)

        # 10. 存档系统相关
        self.save_list_offset = 0
        self.selected_save_index = -1
        self.delete_confirm = None

        # 11. 金币效果系统
        self.coin_effect_timer = 0
        self.coin_effect_text = ""
        self.coin_effect_pos = (0, 0)
        self.show_coin_effect = False

        # 12. 鼠标系统
        self.mouse_pos = (0, 0)

        # 13. 帧率控制
        self.target_fps = 60
        self.last_frame_time = 0
        self.frame_count = 0
        self.frame_timer = 0
        # 14. 加载商店图片
        self.shop_images = self.load_shop_images()

        # 15. 战斗系统
        self.max_health = 100
        self.player_health = self.max_health
        self.battle_thresholds = [1000, 3000, 5000]
        self.completed_battles = set()
        self.battle_monster = None
        self.player_bullets = []
        self.monster_bullets = []
        self.player_shoot_cooldown = 0
        self.monster_fire_interval = 45
        self.battle_score_reward = 200
        self.battle_assets = self.load_battle_assets()

    # ==================== 资源加载方法 ====================
    def load_background_layers(self):
        """加载三层游戏背景图片（远/中/近）"""
        bg_layers = {}
        # 三层背景路径
        bg_paths = {
            "bg1": 'image/像素背景_远层.png',  # 远层（最慢）
            "bg2": 'image/像素背景_中层.png',  # 中层（中速）
            "bg3": 'image/像素背景.png'  # 近层（最快，原背景）
        }

        for layer_name, path in bg_paths.items():
            try:
                # 区分 PNG（透明）和其他格式（非透明）
                if path.lower().endswith('.png'):
                    background = pygame.image.load(path).convert_alpha()  # 保留透明通道
                else:
                    background = pygame.image.load(path).convert()
                background = pygame.transform.scale(background, (800, 600))
                bg_layers[layer_name] = background
                print(f"成功加载{layer_name}背景: {path}")
            except Exception as e:
                # 异常时也用 convert_alpha 加载默认背景（如果默认背景是PNG）
                print(f"加载{layer_name}失败({e})，使用默认背景")
                if '像素背景.png'.endswith('.png'):
                    background = pygame.image.load('image/像素背景.png').convert_alpha()
                else:
                    background = pygame.image.load('image/像素背景.png').convert()
                background = pygame.transform.scale(background, (800, 600))
                bg_layers[layer_name] = background
        return bg_layers

    def load_uibackground(self):
        """加载UI背景图片"""
        uibackground_path = 'image/背景.jpg'
        uibackground = pygame.image.load(uibackground_path).convert()
        uibackground = pygame.transform.scale(uibackground, (800, 600))
        print(f"成功加载UI背景: {uibackground_path}")
        return uibackground

    def load_shop_background(self):
        """加载商店背景图片"""
        background_path = 'image/shop.png'
        background = pygame.image.load(background_path).convert()
        background = pygame.transform.scale(background, (800, 600))
        print(f"成功加载商店背景: {background_path}")
        return background

    def load_shop_images(self):
        """加载商店物品图片（简化版）"""
        shop_images = {}
        item_images = {
            "extra_life": 'image/heart.png',
            "coin_double": 'image/coin.png',
            "star_effect": 'image/star.png'
        }


        for item_type, path in item_images.items():
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.scale(image, (80, 80))
            shop_images[item_type] = image
            print(f"成功加载商店图片: {path}")

        return shop_images

    def load_battle_assets(self):
        """加载战斗相关图片"""
        assets = {}
        paths = {
            "player_bullet": 'image/player_bullet.png',
            "monster_bullet": 'image/monster_bullet.png',
            "monster": 'image/monster.png',
            "player_shoot": 'image/player_shoot.png'
        }
        placeholder_sizes = {
            "player_bullet": (20, 10),
            "monster_bullet": (20, 10),
            "monster": (80, 80),
            "player_shoot": (50, 50),
        }

        def create_placeholder(size, color):
            surface = pygame.Surface(size, pygame.SRCALPHA)
            surface.fill(color)
            pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
            return surface

        for key, path in paths.items():
            if os.path.exists(path):
                loaded = pygame.image.load(path).convert_alpha()
                target_size = placeholder_sizes[key]
                assets[key] = pygame.transform.scale(loaded, target_size)
            else:
                # 使用占位图，确保战斗元素始终可见
                color = (255, 200, 80) if "bullet" in key else (200, 120, 120)
                assets[key] = create_placeholder(placeholder_sizes[key], color)
        return assets


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

            self.clock.tick(self.target_fps)

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
                             image_folder=animation_folder,
                             shoot_image_path="image/player_shoot.png")

        self.score = 0
        self.current_game_coins = 0
        self.obstacle_manager.clear()
        self.coin_manager.clear()
        self.enemy_manager.reset()
        self.stars = []  # 清空星星特效
        self.player_health = self.max_health
        self.completed_battles = set()
        self.player_bullets.clear()
        self.monster_bullets.clear()
        self.battle_monster = None
        self.state = "playing"

        # 进入游戏状态
        self.state = "playing"

    def reset_game(self):
        """重置游戏"""
        if self.player:
            self.player.reset_position(100, 250)
            self.player.health = 3
            self.player.is_invincible = False
            self.player.buff_timer = 0

        self.obstacle_manager.clear()
        self.coin_manager.clear()
        self.enemy_manager.reset()
        self.stars = []
        # 重置当前游戏数据
        self.score = 0
        self.current_game_coins = 0
        self.player_health = self.max_health
        self.player_bullets.clear()
        self.monster_bullets.clear()
        self.battle_monster = None
        self.completed_battles = set()
        if self.player:
            self.player.set_force_shoot_pose(False)

        # 重置物品效果
        self.extra_life_active = False
        self.coin_double_active = False
        self.star_effect_active = False
        self.extra_life_used = False
        self.purchased_items = []
        self.paused_state = None

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
        if event.key == pygame.K_p and self.state in ("playing", "battle", "paused"):
            self.toggle_pause()
            return
        if self.state in ("playing", "battle"):
            self.handle_playing_keydown(event)
    def handle_playing_keydown(self, event):
        """游戏中按键处理"""
        if event.key == pygame.K_SPACE:
            if self.player:
                self.player.jump()
        elif event.key == pygame.K_f:
            if self.state == "battle":
                if self.player and self.player_shoot_cooldown <= 0:
                    self.fire_player_bullet()
                    self.player_shoot_cooldown = 12
            elif self.player:
                self.enemy_manager.spawn_player_bullet(self.player.rect, self.player.attack_power)

    def handle_mouse_click(self):
        """处理鼠标点击"""
        if self.state == "title":
            self.handle_title_mouse_click()
        elif self.state == "load_save":
            self.handle_load_save_mouse_click()
        elif self.state == "saves_list":
            self.handle_saves_list_mouse_click()
        elif self.state == "menu":
            self.handle_menu_mouse_click()
        elif self.state == "shop":
            self.handle_shop_mouse_click()
        elif self.state == "game_over":
            self.handle_game_over_click()

    def handle_game_over_click(self):
        """游戏结束点击返回菜单"""
        self.state = "menu"
        self.reset_game()

    def handle_title_mouse_click(self):
        """标题屏幕鼠标点击"""
        # 标题屏幕按钮
        if 300 <= self.mouse_pos[0] <= 500 and 250 <= self.mouse_pos[1] <= 310:
            self.state = "load_save"
        elif 300 <= self.mouse_pos[0] <= 500 and 330 <= self.mouse_pos[1] <= 390:
            # 自动创建新存档
            if self.save_system.create_new_save():
                self.update_game_data_from_save()
                self.state = "menu"
                print("新存档创建成功")
        elif 300 <= self.mouse_pos[0] <= 500 and 410 <= self.mouse_pos[1] <= 470:
            self.state = "saves_list"
        elif 300 <= self.mouse_pos[0] <= 500 and 490 <= self.mouse_pos[1] <= 550:
            self.running = False

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
            self.state = "title"

    def handle_saves_list_mouse_click(self):
        """存档列表屏幕鼠标点击"""
        # 如果有确认删除的存档
        if self.delete_confirm:
            # 确认删除按钮
            confirm_rect = pygame.Rect(300, 350, 100, 50)
            cancel_rect = pygame.Rect(450, 350, 100, 50)

            if confirm_rect.collidepoint(self.mouse_pos):
                self.save_system.delete_save(self.delete_confirm)
                print(f"已删除存档: {self.delete_confirm}")
                self.delete_confirm = None
                return
            elif cancel_rect.collidepoint(self.mouse_pos):
                self.delete_confirm = None
                return

        # 获取所有存档
        all_saves = self.save_system.get_all_saves()

        # 计算存档显示位置
        y_pos = 220
        for i, save in enumerate(all_saves):
            if y_pos > 500:  # 限制显示数量
                break

            # 删除按钮位置（在存档信息右侧）
            delete_rect = pygame.Rect(650, y_pos, 80, 30)
            if delete_rect.collidepoint(self.mouse_pos):
                # 设置确认删除的存档
                self.delete_confirm = save["player_name"]
                return

            y_pos += 40

        # 返回按钮
        if 650 <= self.mouse_pos[0] <= 750 and 500 <= self.mouse_pos[1] <= 550:
            self.state = "title"

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
        # 重新计算物品位置（与draw_shop_screen保持一致）
        item_width = 150
        item_height = 200
        item_spacing = 50
        total_width = 3 * item_width + 2 * item_spacing  # 三个物品总宽度
        x_start = (800 - total_width) // 2  # 居中开始位置
        y_pos = 200

        # 物品点击
        for i in range(3):
            x_pos = x_start + i * (item_width + item_spacing)
            item_rect = pygame.Rect(x_pos, y_pos, item_width, item_height)
            if item_rect.collidepoint(self.mouse_pos):
                self.purchase_item(i)
                return  # 找到点击的物品后就返回，避免重复检测

        # 按钮参数
        button_width = 150
        button_height = 60
        button_y = 500

        # 开始游戏按钮（右下角）
        start_rect = pygame.Rect(800 - 50 - button_width, button_y, button_width, button_height)
        if start_rect.collidepoint(self.mouse_pos):
            self.start_game()
            return

        # 返回按钮（左下角）
        back_rect = pygame.Rect(50, button_y, button_width, button_height)
        if back_rect.collidepoint(self.mouse_pos):
            self.state = "menu"
            self.purchased_items = []
            return

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
        elif self.state == "battle":
            self.update_battle()
        elif self.state == "paused":
            pass
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

        # 更新敌人和子弹
        player_hit = self.enemy_manager.update(scroll_speed, self.player.rect if self.player else None)

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

        self.score += 0.1

        # 检查是否需要进入战斗
        self.try_trigger_battle()
        if self.state == "battle":
            return

        # 检测碰撞
        if self.player:
            hits = self.obstacle_manager.check_collisions(self.player.rect)
            if hits:
                if self.extra_life_active and not self.extra_life_used:
                    self.extra_life_used = True
                else:
                    self.apply_damage(1)

            if player_hit:
                self.apply_damage(1)        # 更新星星特效
        if self.star_effect_active and self.player:
            self.update_star_effect()

        # 更新金币收集效果
        if self.show_coin_effect:
            self.coin_effect_timer -= 1
            if self.coin_effect_timer <= 0:
                self.show_coin_effect = False

    def try_trigger_battle(self):
        """当分数达到阈值时进入打怪状态"""
        for threshold in self.battle_thresholds:
            if self.score >= threshold and threshold not in self.completed_battles:
                self.start_battle(threshold)
                break

    def start_battle(self, threshold):
        """开启打怪状态"""
        self.state = "battle"
        ground_y = 400 - 80  # 与玩家同一地面高度
        self.battle_monster = BattleMonster(600, ground_y,
                                            image=self.battle_assets.get("monster"),
                                            health=20)
        self.player_bullets.clear()
        self.monster_bullets.clear()
        self.player_shoot_cooldown = 0
        self.current_battle_threshold = threshold
        if self.player:
            self.player.set_force_shoot_pose(True)

    def end_battle(self, victory=True):
        """结束战斗并返回跑酷"""
        if victory:
            self.score += self.battle_score_reward
            if hasattr(self, "current_battle_threshold"):
                self.completed_battles.add(self.current_battle_threshold)
        self.state = "playing"
        self.battle_monster = None
        self.player_bullets.clear()
        self.monster_bullets.clear()
        if self.player:
            self.player.set_force_shoot_pose(False)

    def update_battle(self):
        """战斗状态更新"""
        # 背景不滚动，保持静止
        if self.player:
            self.player.update()

        # 玩家射击冷却
        if self.player_shoot_cooldown > 0:
            self.player_shoot_cooldown -= 1

        # 怪物攻击节奏
        if self.battle_monster:
            self.battle_monster.update()
            if self.battle_monster.ready_to_fire():
                self.fire_monster_bullet()
                self.battle_monster.reset_fire_cooldown(self.monster_fire_interval)

        # 更新子弹
        self.update_bullets()

        # 检测玩家是否死亡
        if self.player_health <= 0:
            self.state = "game_over"
            self.game_over_time = time.time()


        # 检测怪物是否死亡
        if self.battle_monster and not self.battle_monster.alive:
            self.end_battle(True)

    def fire_player_bullet(self):
        """生成玩家子弹"""
        if not self.player:
            return
        bullet = BattleBullet(
            self.player.rect.right,
            self.player.rect.centery - 5,
            speed=12,
            direction="right",
            image=self.battle_assets.get("player_bullet")
        )
        self.player_bullets.append(bullet)
        self.player.trigger_shooting_pose(10)

    def fire_monster_bullet(self):
        """生成怪物子弹"""
        if not self.battle_monster:
            return
        bullet = BattleBullet(
            self.battle_monster.rect.left - 20,
            self.battle_monster.rect.centery - 5,
            speed=8,
            direction="left",
            image=self.battle_assets.get("monster_bullet")
        )
        self.monster_bullets.append(bullet)

    def update_bullets(self):
        """更新战斗子弹并处理碰撞"""
        for bullet in self.player_bullets:
            bullet.update()
            if self.battle_monster and bullet.active and bullet.rect.colliderect(self.battle_monster.rect):
                self.battle_monster.take_hit(bullet.damage)
                bullet.active = False

        for bullet in self.monster_bullets:
            bullet.update()
            if self.player and bullet.active and bullet.rect.colliderect(self.player.rect):
                bullet.active = False
                self.apply_damage(1)

        self.player_bullets = [b for b in self.player_bullets if b.active]
        self.monster_bullets = [b for b in self.monster_bullets if b.active]

    def apply_damage(self, amount):
        """统一的扣血逻辑"""
        self.player_health = max(0, self.player_health - amount)
        if self.player_health <= 0:
            self.state = "game_over"
            self.game_over_time = time.time()

            if self.save_system.current_save:
                final_coins = self.current_game_coins
                if self.coin_double_active:
                    final_coins *= 2
                self.save_system.update_save(self.score, final_coins, self.selected_character)
                self.update_game_data_from_save()


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
        """更新三层背景滚动位置（不同速度）"""
        # 远层（最慢）
        self.bg1_x1 -= self.bg_speeds["bg1"]
        self.bg1_x2 -= self.bg_speeds["bg1"]
        if self.bg1_x1 <= -800:
            self.bg1_x1 = 800
        if self.bg1_x2 <= -800:
            self.bg1_x2 = 800

        # 中层（中速）
        self.bg2_x1 -= self.bg_speeds["bg2"]
        self.bg2_x2 -= self.bg_speeds["bg2"]
        if self.bg2_x1 <= -800:
            self.bg2_x1 = 800
        if self.bg2_x2 <= -800:
            self.bg2_x2 = 800

        # 近层（最快）
        self.bg3_x1 -= self.bg_speeds["bg3"]
        self.bg3_x2 -= self.bg_speeds["bg3"]
        if self.bg3_x1 <= -800:
            self.bg3_x1 = 800
        if self.bg3_x2 <= -800:
            self.bg3_x2 = 800

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
        elif self.state == "load_save":
            self.draw_load_save_screen()
        elif self.state == "saves_list":
            self.draw_saves_list_screen()
        elif self.state == "menu":
            self.draw_menu_screen()
        elif self.state == "shop":
            self.draw_shop_screen()
        elif self.state == "playing":
            self.draw_game_screen()
        elif self.state == "battle":
            self.draw_battle_screen()
        elif self.state == "paused":
            self.draw_pause_screen()
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
            "使用鼠标点击按钮进行操作"
        ]

        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(control_text, (400 - control_text.get_width() // 2, 530 + i * 25))

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
        instruction_text = self.small_font.render("点击存档加载，使用鼠标操作", True, (200, 200, 200))
        self.screen.blit(instruction_text, (400 - instruction_text.get_width() // 2, 560))

    def draw_saves_list_screen(self):
        """绘制存档列表屏幕"""
        # 如果有确认删除的存档，绘制确认界面
        if self.delete_confirm:
            self.draw_delete_confirmation()
            return

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

            # 存档信息
            save_info = f"{i + 1}. {save['player_name']} - 最高分: {save['high_score']} - 金币: {save['total_coins']}"
            if len(save_info) > 60:
                save_info = save_info[:57] + "..."
            save_text = self.small_font.render(save_info, True, (220, 220, 220))
            self.screen.blit(save_text, (100, y_pos))

            # 绘制删除按钮
            delete_rect = pygame.Rect(650, y_pos, 80, 30)
            is_current = save["player_name"] == self.save_system.current_save[
                "player_name"] if self.save_system.current_save else False
            delete_hovered = delete_rect.collidepoint(self.mouse_pos)

            if is_current:
                # 当前存档的删除按钮为灰色
                delete_color = (100, 100, 100)
                delete_text_color = (150, 150, 150)
            else:
                delete_color = (200, 100, 100) if delete_hovered else (170, 70, 70)
                delete_text_color = (255, 255, 255)

            pygame.draw.rect(self.screen, delete_color, delete_rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), delete_rect, 2, border_radius=5)

            delete_text = pygame.font.Font('image/STKAITI.TTF', 20).render("删除", True, delete_text_color)
            delete_text_rect = delete_text.get_rect(center=delete_rect.center)
            self.screen.blit(delete_text, delete_text_rect)

            y_pos += 40  # 减少行间距

        # 绘制说明文字
        instruction_text = self.small_font.render("点击删除按钮删除存档（当前存档不能删除）", True, (255, 200, 100))
        self.screen.blit(instruction_text, (400 - instruction_text.get_width() // 2, 520))

        # 绘制返回按钮 - 与事件检测位置保持一致 (650, 500, 100, 50)
        back_rect = pygame.Rect(650, 500, 100, 50)
        hovered = back_rect.collidepoint(self.mouse_pos)
        back_color = (200, 100, 100) if hovered else (170, 70, 70)
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 3, border_radius=10)

        back_text = self.small_font.render("返回", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.screen.blit(back_text, back_text_rect)

    def draw_delete_confirmation(self):
        """绘制删除确认界面"""
        # 半透明背景
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # 确认框
        confirm_rect = pygame.Rect(200, 200, 400, 200)
        pygame.draw.rect(self.screen, (50, 50, 80), confirm_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), confirm_rect, 3, border_radius=10)

        # 确认文字
        confirm_text = self.medium_font.render(f"确认删除存档: {self.delete_confirm}?", True, (255, 100, 100))
        self.screen.blit(confirm_text, (400 - confirm_text.get_width() // 2, 250))

        warning_text = self.small_font.render("此操作不可恢复！", True, (255, 200, 100))
        self.screen.blit(warning_text, (400 - warning_text.get_width() // 2, 290))

        # 确认按钮
        confirm_btn = pygame.Rect(300, 350, 100, 50)
        confirm_hovered = confirm_btn.collidepoint(self.mouse_pos)
        confirm_color = (200, 50, 50) if confirm_hovered else (170, 30, 30)
        pygame.draw.rect(self.screen, confirm_color, confirm_btn, border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255), confirm_btn, 2, border_radius=5)
        confirm_text = self.small_font.render("确认", True, (255, 255, 255))
        self.screen.blit(confirm_text, (350 - confirm_text.get_width() // 2, 375 - confirm_text.get_height() // 2))

        # 取消按钮
        cancel_btn = pygame.Rect(450, 350, 100, 50)
        cancel_hovered = cancel_btn.collidepoint(self.mouse_pos)
        cancel_color = (100, 100, 200) if cancel_hovered else (70, 70, 170)
        pygame.draw.rect(self.screen, cancel_color, cancel_btn, border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255), cancel_btn, 2, border_radius=5)
        cancel_text = self.small_font.render("取消", True, (255, 255, 255))
        self.screen.blit(cancel_text, (500 - cancel_text.get_width() // 2, 375 - cancel_text.get_height() // 2))

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
            img = pygame.image.load('gif/nick.png').convert_alpha()
            img = pygame.transform.scale(img, (80, 80))
            self.screen.blit(img, (260, 260))
        except:
            pass

        # 绘制角色1描述
        char1_text = self.small_font.render("尼克", True, (255, 255, 255))
        self.screen.blit(char1_text, (300 - char1_text.get_width() // 2, 350))
        ability_text = self.small_font.render("单段跳", True, (200, 200, 255))
        self.screen.blit(ability_text, (300 - ability_text.get_width() // 2, 375))

        # 绘制角色2选择框
        char2_rect = pygame.Rect(450, 250, 100, 150)
        char2_hovered = char2_rect.collidepoint(self.mouse_pos)
        char2_color = (100, 200, 150) if char2_hovered else (70, 170, 120)
        pygame.draw.rect(self.screen, char2_color, char2_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), char2_rect, 3, border_radius=10)

        # 绘制角色2图片
        try:
            img = pygame.image.load('gif/judy.png').convert_alpha()
            img = pygame.transform.scale(img, (80, 80))
            self.screen.blit(img, (460, 260))
        except:
            pass

        # 绘制角色2描述
        char2_text = self.small_font.render("朱迪", True, (255, 255, 255))
        self.screen.blit(char2_text, (500 - char2_text.get_width() // 2, 350))
        ability_text = self.small_font.render("二段跳", True, (200, 200, 255))
        self.screen.blit(ability_text, (500 - ability_text.get_width() // 2, 375))

        # 绘制退出按钮
        quit_rect = pygame.Rect(300, 450, 200, 60)
        quit_hovered = quit_rect.collidepoint(self.mouse_pos)
        quit_color = (200, 100, 100) if quit_hovered else (170, 70, 70)
        pygame.draw.rect(self.screen, quit_color, quit_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), quit_rect, 3, border_radius=10)

        quit_text = self.medium_font.render("返回主页", True, (255, 255, 255))
        self.screen.blit(quit_text, (400 - quit_text.get_width() // 2, 480 - quit_text.get_height() // 2))

        # 绘制操作说明
        controls = [
            "点击角色图标选择角色进入商店",
            "游戏中: 空格键跳跃",
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

        # 显示当前金币
        coins_text = self.medium_font.render(f"当前金币: {self.coins}", True, (255, 255, 100))
        self.screen.blit(coins_text, (400 - coins_text.get_width() // 2, 130))

        # 绘制物品 - 居中排列
        item_width = 150
        item_height = 200
        item_spacing = 50
        total_width = 3 * item_width + 2 * item_spacing  # 三个物品总宽度
        x_start = (800 - total_width) // 2  # 居中开始位置
        y_pos = 200

        for i, item in enumerate(self.shop_items):
            x_pos = x_start + i * (item_width + item_spacing)

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

        # 绘制物品描述区域
        desc_rect = pygame.Rect(100, 420, 600, 80)
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
                if j < 2:  # 限制显示行数
                    desc_text = self.small_font.render(line, True, (255, 255, 200))
                    self.screen.blit(desc_text, (desc_rect.x + 20, desc_rect.y + 10 + j * 25))

        # 绘制按钮区域
        button_width = 150
        button_height = 60
        button_y = 500

        # 绘制返回按钮（左下角）
        back_rect = pygame.Rect(50, button_y, button_width, button_height)
        back_hovered = back_rect.collidepoint(self.mouse_pos)
        back_color = (200, 100, 100) if back_hovered else (170, 70, 70)

        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 3, border_radius=10)

        back_text = self.medium_font.render("返回", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.screen.blit(back_text, back_text_rect)

        # 绘制开始游戏按钮（右下角）
        start_rect = pygame.Rect(800 - 50 - button_width, button_y, button_width, button_height)
        start_hovered = start_rect.collidepoint(self.mouse_pos)
        start_color = (100, 200, 100) if start_hovered else (70, 170, 70)

        pygame.draw.rect(self.screen, start_color, start_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), start_rect, 3, border_radius=10)

        start_text = self.medium_font.render("开始游戏", True, (255, 255, 255))
        start_text_rect = start_text.get_rect(center=start_rect.center)
        self.screen.blit(start_text, start_text_rect)


    def draw_game_screen(self):
        """绘制游戏画面"""
        # 先清屏，避免角色跳跃时的拖影
        self.screen.fill((0, 0, 0))
        # 绘制背景␊
        self.screen.blit(self.bg_layers['bg1'], (self.bg1_x1, 0))
        self.screen.blit(self.bg_layers['bg1'], (self.bg1_x2, 0))
        self.screen.blit(self.bg_layers['bg2'], (self.bg2_x1, 0))
        self.screen.blit(self.bg_layers['bg2'], (self.bg2_x2, 0))
        self.screen.blit(self.bg_layers['bg3'], (self.bg3_x1, 0))
        self.screen.blit(self.bg_layers['bg3'], (self.bg3_x2, 0))

        # 绘制障碍物
        self.obstacle_manager.draw(self.screen)

        # 绘制金币
        self.coin_manager.draw(self.screen)

        # 绘制敌人和战斗效果
        self.enemy_manager.draw(self.screen)

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

    def draw_battle_screen(self):
        """绘制战斗界面"""
        self.screen.fill((0, 0, 0))
        # 背景保持静止
        self.screen.blit(self.bg_layers['bg3'], (self.bg3_x1, 0))
        self.screen.blit(self.bg_layers['bg3'], (self.bg3_x2, 0))

        # 绘制玩家
        if self.player:
            self.player.draw(self.screen)

        # 绘制怪物和子弹
        if self.battle_monster:
            self.battle_monster.draw(self.screen)
        for bullet in self.player_bullets:
            bullet.draw(self.screen)
        for bullet in self.monster_bullets:
            bullet.draw(self.screen)

        # 提示文本
        battle_text = self.medium_font.render("打怪模式：击败怪物继续跑酷", True, (255, 255, 0))
        self.screen.blit(battle_text, (400 - battle_text.get_width() // 2, 40))

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

        # 计算最终金币
        final_coins = self.current_game_coins

        coins_text = self.font.render(f"本局金币: {final_coins}", True, (255, 255, 100))
        restart_text = self.medium_font.render(f"自动返回菜单: {int(time_left)}秒", True, (100, 255, 100))
        click_text = self.small_font.render("点击任意处返回主页面", True, (200, 200, 200))

        # 居中显示
        self.screen.blit(game_over_text, (400 - game_over_text.get_width() // 2, 180))
        self.screen.blit(score_text, (400 - score_text.get_width() // 2, 240))
        self.screen.blit(high_score_text, (400 - high_score_text.get_width() // 2, 290))
        self.screen.blit(coins_text, (400 - coins_text.get_width() // 2, 340))
        self.screen.blit(restart_text, (400 - restart_text.get_width() // 2, 400))
        self.screen.blit(click_text, (400 - click_text.get_width() // 2, 440))

    def draw_pause_screen(self):
        """绘制暂停画面"""
        if self.paused_state == "battle":
            self.draw_battle_screen()
        else:
            self.draw_game_screen()

        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font.render("已暂停", True, (255, 255, 255))
        hint_text = self.small_font.render("按 P 继续游戏", True, (200, 200, 200))
        self.screen.blit(pause_text, (400 - pause_text.get_width() // 2, 240))
        self.screen.blit(hint_text, (400 - hint_text.get_width() // 2, 320))

    def toggle_pause(self):
        """切换暂停状态"""
        if self.state == "paused":
            self.state = self.paused_state or "playing"
            self.paused_state = None
            return

        if self.state in ("playing", "battle"):
            self.paused_state = self.state
            self.state = "paused"

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
        self.screen.blit(score_text, (20, 10))

        # 绘制最高分
        high_score = 0
        if self.save_system.current_save:
            high_score = self.save_system.current_save["high_score"]
        high_score_text = self.medium_font.render(f"最高分: {high_score}", True, (0, 0, 0))
        self.screen.blit(high_score_text, (20, 50))

        # 绘制生命值
        health_ratio = self.player_health / self.max_health if self.max_health else 0
        health_bar_bg = pygame.Rect(10, 90, 200, 20)
        pygame.draw.rect(self.screen, (180, 50, 50), health_bar_bg, border_radius=5)
        pygame.draw.rect(self.screen, (50, 200, 50),
                         (10, 90, 200 * health_ratio, 20), border_radius=5)
        health_text = self.small_font.render(f"生命: {self.player_health}/{self.max_health}", True, (0, 0, 0))
        self.screen.blit(health_text, (15, 115))


        # 绘制本局金币
        coins_text = self.ui_font.render(f"金币: {self.current_game_coins}", True, (255, 255, 100))
        coins_rect = coins_text.get_rect(topright=(780, 20))
        self.screen.blit(coins_text, coins_rect)

        # 显示当前激活的物品效果（增强版）
        effects_y = 80

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


if __name__ == "__main__":
    game = Game()

    game.run()




