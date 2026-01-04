import pygame


class BattleBullet:
    def __init__(self, x, y, speed, direction="right", image=None, damage=1):
        self.rect = pygame.Rect(x, y, 20, 10)
        self.speed = speed
        self.direction = direction
        self.image = image
        self.damage = damage
        self.active = True

    def update(self):
        if self.direction == "right":
            self.rect.x += self.speed
        else:
            self.rect.x -= self.speed

        if self.rect.right < -50 or self.rect.left > 850:
            self.active = False

    def draw(self, screen):
        if not self.active:
            return
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, (255, 255, 255), self.rect)


class BattleMonster:
    def __init__(self, x, y, image=None, health=20):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.image = image
        self.health = health
        self.max_health = health
        self.fire_cooldown = 0

    @property
    def alive(self):
        return self.health > 0

    def update(self):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def take_hit(self, damage=1):
        self.health = max(0, self.health - damage)

    def ready_to_fire(self):
        return self.fire_cooldown <= 0

    def reset_fire_cooldown(self, cooldown):
        self.fire_cooldown = cooldown

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.rect(screen, (200, 100, 100), self.rect)

        # health bar
        bar_width = self.rect.width
        health_ratio = self.health / self.max_health if self.max_health else 0
        pygame.draw.rect(screen, (200, 50, 50), (self.rect.x, self.rect.y - 10, bar_width, 6))
        pygame.draw.rect(screen, (50, 200, 50),
                         (self.rect.x, self.rect.y - 10, bar_width * health_ratio, 6))
