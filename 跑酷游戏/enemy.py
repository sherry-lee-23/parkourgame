"""敌人和战斗系统集成模块。
该模块从原有的“打怪系统”草稿整理而来，提供：
- 基础的怪物（仅保留绵羊）、子弹、技能定义
- 敌人管理器（生成、更新、绘制、碰撞检测）
- 资源加载占位与缺失记录
"""

import os
import random
from typing import Dict, List, Optional

import pygame


class Monster:
    """简单的怪物实体（仅保留绵羊）。"""

    def __init__(self, x: int, y: int, monster_type: str, image: Optional[pygame.Surface] = None):
        self.rect = pygame.Rect(x, y, 60, 60)
        self.type = monster_type  # 固定为 sheep

        # 战斗属性（调整为绵羊的属性）
        self.health = 80  # 绵羊血量
        self.max_health = 80
        self.damage = 8   # 绵羊攻击伤害
        self.speed = 1    # 绵羊移动速度（比原来慢）
        self.attack_range = 40  # 攻击范围
        self.attack_cooldown = 0

        # 状态
        self.is_alive = True
        self.is_attacking = False

        # 视觉
        self.image = image if image else self._build_fallback_surface()
        self.color = self._get_color_by_type()
        self.animation_frame = 0

    @property
    def x(self):
        return self.rect.x

    @property
    def y(self):
        return self.rect.y

    def _get_color_by_type(self):
        """仅保留绵羊的颜色（白色+浅灰色）"""
        colors = {
            "sheep": (240, 240, 240),  # 绵羊专属颜色（浅白色）
        }
        return colors.get(self.type, (128, 128, 128))

    def _build_fallback_surface(self):
        """生成绵羊的占位图（浅白色矩形）"""
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        surface.fill(self._get_color_by_type())
        pygame.draw.rect(surface, (200, 200, 200), surface.get_rect(), 2)  # 边框浅灰色
        return surface

    def update(self, scroll_speed: int):
        if not self.is_alive:
            return

        # 绵羊向左移动，叠加基础速度
        self.rect.x -= scroll_speed + self.speed

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        self.animation_frame = (self.animation_frame + 1) % 60

    def take_damage(self, damage: int) -> bool:
        self.health -= damage
        if self.health <= 0:
            self.die()
            return True
        return False

    def die(self):
        self.is_alive = False

    def attack(self, player_rect: pygame.Rect) -> bool:
        if self.attack_cooldown > 0:
            return False

        distance = abs(self.rect.centerx - player_rect.centerx)
        if distance <= self.attack_range:
            self.is_attacking = True
            self.attack_cooldown = 30
            return True
        return False

    def draw(self, screen: pygame.Surface):
        if not self.is_alive:
            return

        screen.blit(self.image, self.rect)
        self._draw_health_bar(screen)

        if self.is_attacking:
            self._draw_attack_effect(screen)
            self.is_attacking = False

    def _draw_health_bar(self, screen: pygame.Surface):
        bar_width = self.rect.width
        bar_height = 5
        health_percent = max(self.health, 0) / self.max_health

        pygame.draw.rect(screen, (255, 0, 0), (self.rect.x, self.rect.y - 10, bar_width, bar_height))
        pygame.draw.rect(
            screen,
            (0, 255, 0),
            (self.rect.x, self.rect.y - 10, bar_width * health_percent, bar_height),
        )

    def _draw_attack_effect(self, screen: pygame.Surface):
        """绵羊攻击特效（浅黄色小矩形）"""
        effect_rect = pygame.Rect(self.rect.centerx, self.rect.centery - 10, 20, 20)
        pygame.draw.rect(screen, (255, 240, 200), effect_rect, border_radius=3)


class Bullet:
    """子弹类（保留原有逻辑，无改动）"""
    def __init__(self, x: int, y: int, direction: str = "right", damage: int = 20,
                 image: Optional[pygame.Surface] = None):
        self.image = image
        if self.image:
            if direction == "right":
                self.rect = self.image.get_rect(midleft=(x, y))
            else:
                self.rect = self.image.get_rect(midright=(x, y))
        else:
            self.rect = pygame.Rect(x, y, 15, 5)
        self.speed = 10
        self.damage = damage
        self.direction = direction
        self.is_active = True

    def update(self):
        if self.direction == "right":
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        if self.rect.x > 1000 or self.rect.x < -50:
            self.is_active = False

    def draw(self, screen: pygame.Surface):
        if not self.is_active:
            return
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, (255, 240, 0), self.rect)
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 1)


class Skill:
    """技能类（保留原有逻辑，无改动）"""
    def __init__(self, name: str, skill_type: str, cooldown: int, damage: int, effect: Optional[str]):
        self.name = name
        self.type = skill_type
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.damage = damage
        self.effect = effect
        self.is_ready = True

    def update(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
            if self.current_cooldown <= 0:
                self.is_ready = True

    def use(self, player_rect: pygame.Rect, target_pos=None):
        if not self.is_ready:
            return None

        self.current_cooldown = self.cooldown
        self.is_ready = False

        if self.type == "projectile":
            return Bullet(x=player_rect.right, y=player_rect.centery, direction="right", damage=self.damage)
        elif self.type == "area":
            return {
                "x": player_rect.x - 50,
                "y": player_rect.y - 50,
                "width": 150,
                "height": 150,
                "damage": self.damage,
                "duration": 10,
            }
        elif self.type == "buff":
            return None


class EnemyManager:
    """统一管理怪物（仅绵羊）和战斗交互。"""

    def __init__(self):
        self.monsters: List[Monster] = []
        self.player_bullets: List[Bullet] = []
        self.spawn_timer = 0
        self.spawn_interval = 120  # 绵羊生成间隔（可自行调整）
        self.missing_assets: List[str] = []

        self.monster_images = self._load_monster_images()
        self.bullet_image = self._load_bullet_image()

    def _load_monster_images(self) -> Dict[str, pygame.Surface]:
        """仅加载绵羊的图片"""
        images: Dict[str, pygame.Surface] = {}
        # 仅保留绵羊的图片路径，优先使用仓库现有的贴图
        base_dir = os.path.dirname(__file__)
        expected = {
            "sheep": os.path.join(base_dir, "assets", "sheep.png"),  # 绵羊图片路径（修正为实际位置）          
        }
        for monster_type, path in expected.items():
            if os.path.exists(path):
                loaded = pygame.image.load(path).convert_alpha()
                loaded = pygame.transform.scale(loaded, (60, 60))
                images[monster_type] = loaded
            else:
                self.missing_assets.append(path)

        return images

    def _load_bullet_image(self) -> Optional[pygame.Surface]:
        base_dir = os.path.dirname(__file__)
        bullet_path = os.path.join(base_dir, "image", "player_bullet.png")
        if not os.path.exists(bullet_path):
            self.missing_assets.append(bullet_path)
            return None
        loaded = pygame.image.load(bullet_path).convert_alpha()
        return pygame.transform.scale(loaded, (20, 10))

    def reset(self):
        """重置怪物列表"""
        self.monsters.clear()
        self.player_bullets.clear()
        self.spawn_timer = 0

    def spawn_monster(self):
        """仅生成绵羊怪物"""
        monster_type = "sheep"  # 固定生成绵羊
        if monster_type not in self.monster_images:
            return  # 缺少贴图时不生成白块占位
        ground_y = 400 - 60     # 地面y坐标（和原来一致）
        new_monster = Monster(800, ground_y, monster_type, self.monster_images.get(monster_type))
        self.monsters.append(new_monster)

    def spawn_player_bullet(self, player_rect: pygame.Rect, damage: int = 25):
        """生成玩家子弹（无改动）"""
        bullet = Bullet(
            x=player_rect.right,
            y=player_rect.centery,
            direction="right",
            damage=damage,
            image=self.bullet_image,
        )
        self.player_bullets.append(bullet)

    def update(self, scroll_speed: int, player_rect: Optional[pygame.Rect]) -> bool:
        """更新怪物和战斗逻辑（仅生成绵羊）"""
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_monster()
            self.spawn_interval = random.randint(100, 160)  # 生成间隔随机
            self.spawn_timer = 0

        player_hit = False

        # 更新绵羊怪物
        for monster in self.monsters[:]:
            monster.update(scroll_speed)
            if monster.rect.right < 0 or not monster.is_alive:
                self.monsters.remove(monster)

        # 更新子弹碰撞
        for bullet in self.player_bullets[:]:
            bullet.update()
            if not bullet.is_active:
                self.player_bullets.remove(bullet)
                continue

            for monster in self.monsters[:]:
                if bullet.rect.colliderect(monster.rect) and monster.is_alive:
                    bullet.is_active = False
                    is_dead = monster.take_damage(bullet.damage)
                    if is_dead:
                        self.monsters.remove(monster)
                    break

        # 检测绵羊攻击玩家
        if player_rect:
            for monster in self.monsters:
                if monster.attack(player_rect):
                    player_hit = True

        return player_hit

    def draw(self, screen: pygame.Surface):
        """绘制绵羊和子弹"""
        for monster in self.monsters:
            monster.draw(screen)

        for bullet in self.player_bullets:
            bullet.draw(screen)


