# ui_components.py
import pygame


class Button:
    def __init__(self, x, y, width, height, text, font_size=36):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.normal_color = (70, 130, 180)
        self.hover_color = (100, 160, 210)
        self.text_color = (255, 255, 255)
        self.current_color = self.normal_color
        self.is_hovered = False

    def draw(self, screen):
        """绘制按钮"""
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=10)

        # 绘制文本
        font = pygame.font.Font('image/STKAITI.TTF', self.font_size)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos):
        """更新按钮状态"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.current_color = self.hover_color if self.is_hovered else self.normal_color
        return self.is_hovered

    def is_clicked(self, mouse_pos, mouse_clicked):
        """检查按钮是否被点击"""
        return self.rect.collidepoint(mouse_pos) and mouse_clicked


class TextInput:
    def __init__(self, x, y, width, height, prompt="", max_length=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.prompt = prompt
        self.text = ""
        self.max_length = max_length
        self.active = False
        self.font = pygame.font.Font('image/STKAITI.TTF', 32)
        self.prompt_font = pygame.font.Font('image/STKAITI.TTF', 36)
        self.cursor_visible = True
        self.cursor_timer = 0

    def draw(self, screen):
        """绘制文本输入框"""
        # 绘制提示文字
        if self.prompt:
            prompt_surface = self.prompt_font.render(self.prompt, True, (255, 255, 255))
            screen.blit(prompt_surface, (self.rect.centerx - prompt_surface.get_width() // 2, self.rect.y - 50))

        # 绘制输入框背景和边框
        border_color = (100, 160, 210) if self.active else (70, 130, 180)
        pygame.draw.rect(screen, (50, 50, 50), self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 3)

        # 绘制文本
        text_display = self.text
        if self.active and self.cursor_visible:
            text_display += "|"

        text_surface = self.font.render(text_display, True, (255, 255, 255))
        screen.blit(text_surface, (self.rect.x + 10, self.rect.centery - text_surface.get_height() // 2))

    def update(self, events):
        """更新文本输入框"""
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # 每30帧切换一次光标显示
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)

            elif event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif len(self.text) < self.max_length and event.unicode.isprintable():
                    self.text += event.unicode

    def get_text(self):
        """获取输入的文本"""
        return self.text.strip()

    def clear(self):
        """清空输入框"""
        self.text = ""


class CharacterCard:
    def __init__(self, x, y, width, height, player_id, can_double_jump, image_path=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.player_id = player_id
        self.can_double_jump = can_double_jump
        self.selected = False

        # 加载角色图片
        self.image = None
        if image_path:
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (80, 80))
            except:
                self.image = None

        # 如果没有图片，创建颜色方块
        if not self.image:
            self.color = (0, 255, 0) if can_double_jump else (0, 0, 255)

        # 卡片颜色
        self.normal_color = (80, 80, 120)
        self.selected_color = (120, 120, 180)
        self.border_color = (200, 200, 255)
        self.font = pygame.font.Font('image/STKAITI.TTF', 28)

    def draw(self, screen):
        """绘制角色卡片"""
        # 绘制卡片背景
        card_color = self.selected_color if self.selected else self.normal_color
        pygame.draw.rect(screen, card_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, self.border_color, self.rect, 3, border_radius=10)

        # 绘制角色图片或颜色方块
        if self.image:
            image_rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
            screen.blit(self.image, image_rect)
        else:
            square_rect = pygame.Rect(0, 0, 60, 60)
            square_rect.center = (self.rect.centerx, self.rect.centery - 20)
            pygame.draw.rect(screen, self.color, square_rect)
            pygame.draw.rect(screen, (255, 255, 255), square_rect, 2)

        # 绘制角色信息
        player_type = "二段跳角色" if self.can_double_jump else "单段跳角色"
        player_text = f"角色 {self.player_id}"
        type_text = f"({player_type})"

        player_surface = self.font.render(player_text, True, (255, 255, 255))
        type_surface = self.font.render(type_text, True, (255, 255, 200))

        player_rect = player_surface.get_rect(center=(self.rect.centerx, self.rect.bottom - 40))
        type_rect = type_surface.get_rect(center=(self.rect.centerx, self.rect.bottom - 15))

        screen.blit(player_surface, player_rect)
        screen.blit(type_surface, type_rect)

    def update(self, mouse_pos, mouse_clicked):
        """更新卡片状态"""
        if self.rect.collidepoint(mouse_pos) and mouse_clicked:
            self.selected = True
            return True
        return False