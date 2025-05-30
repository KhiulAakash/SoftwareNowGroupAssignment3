# Import necessary modules
import pygame
import sys
import random

# ----------------------------
# Game Constants
# ----------------------------
WIDTH, HEIGHT = 900, 500          # Window size
FPS = 60                          # Frames per second
GRAVITY = 0.8                     # Force pulling the player downward
PLAYER_SPEED = 5                  # Left/right speed of the player
JUMP_POWER = 15                   # Strength of the jump
PROJECTILE_SPEED = 10             # Speed of the bullets
ENEMY_SPEED = 2                   # How fast enemies move
LEVEL_LENGTH = 3000               # Width of the level (scrollable area)
CAMERA_LAG = 0.1                  # Smooth camera follow factor

# Colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 220, 50)
BLUE = (50, 50, 220)
YELLOW = (255, 255, 0)
GRAY = (180, 180, 180)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Animal Hero Side-Scroller")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)  # Font for text

# ----------------------------
# Player Class
# ----------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))  # Player size
        self.image.fill(BLUE)  # Player color
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_y = 0
        self.on_ground = False
        self.health = 100
        self.lives = 3
        self.score = 0
        self.invincible = 0  # Time left where player can't take damage
        self.direction = 1   # 1 = right, -1 = left

    def update(self, platforms):
        # Handle keyboard input
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT]:
            dx = -PLAYER_SPEED
            self.direction = -1
        if keys[pygame.K_RIGHT]:
            dx = PLAYER_SPEED
            self.direction = 1
        self.rect.x += dx

        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # Collision with platforms
        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel_y > 0:
                    self.rect.bottom = plat.rect.top
                    self.vel_y = 0
                    self.on_ground = True

        # Invincibility countdown
        if self.invincible > 0:
            self.invincible -= 1

    def jump(self):
        # Jump only if on the ground
        if self.on_ground:
            self.vel_y = -JUMP_POWER

    def shoot(self, projectiles):
        # Shoot a bullet in the current direction
        if self.direction == 1:
            proj = Projectile(self.rect.right, self.rect.centery, PROJECTILE_SPEED)
        else:
            proj = Projectile(self.rect.left, self.rect.centery, -PROJECTILE_SPEED)
        projectiles.add(proj)

    def take_damage(self, amount):
        # Lose health/lives when hit by an enemy
        if self.invincible == 0:
            self.health -= amount
            self.invincible = 60  # 1-second cooldown
            if self.health <= 0:
                self.lives -= 1
                self.health = 100  # Reset health

# ----------------------------
# Projectile Class
# ----------------------------
class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = pygame.Surface((15, 5))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self):
        # Move the bullet
        self.rect.x += self.speed
        # Remove if off-screen
        if self.rect.left > LEVEL_LENGTH or self.rect.right < 0:
            self.kill()

# ----------------------------
# Enemy Class
# ----------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health=40, boss=False):
        super().__init__()
        self.boss = boss
        w, h = (60, 90) if boss else (40, 60)
        self.image = pygame.Surface((w, h))
        self.image.fill(RED if not boss else (120, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = health if not boss else 200
        self.speed = ENEMY_SPEED if not boss else ENEMY_SPEED // 2
        self.direction = 1  # Moving right initially

    def update(self, platforms):
        # Move enemy left or right
        self.rect.x += self.speed * self.direction

        # Reverse direction if at edge
        on_platform = False
        for plat in platforms:
            if plat.rect.collidepoint(self.rect.midbottom):
                on_platform = True
        if not on_platform:
            self.direction *= -1
            self.rect.x += self.speed * self.direction * 2

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()

# ----------------------------
# Collectible Class (health, life)
# ----------------------------
class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((30, 30))
        if kind == "health":
            self.image.fill(GREEN)
        elif kind == "life":
            self.image.fill(WHITE)
        else:
            self.image.fill(GRAY)
        self.rect = self.image.get_rect(center=(x, y))

# ----------------------------
# Platform Class
# ----------------------------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))

# ----------------------------
# Generate Platforms, Enemies, and Collectibles
# ----------------------------
def make_level(level_num):
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    collectibles = pygame.sprite.Group()

    # Add the ground
    platforms.add(Platform(0, HEIGHT-40, LEVEL_LENGTH, 40))

    # Create platforms + enemies + items
    for i in range(10):
        x = 300 + i * 250 + random.randint(-50, 50)
        y = HEIGHT - 120 - random.randint(0, 120)
        platforms.add(Platform(x, y, 120, 20))
        if i % 3 == 0:
            enemies.add(Enemy(x + 60, y - 60))
        if i % 4 == 0:
            collectibles.add(Collectible(x + 60, y - 40, "health"))
        if i == 7 and level_num == 2:
            collectibles.add(Collectible(x + 60, y - 40, "life"))

    # Add a boss in level 3
    if level_num == 3:
        enemies.add(Enemy(LEVEL_LENGTH - 200, HEIGHT - 130, boss=True))

    return platforms, enemies, collectibles

# ----------------------------
# Camera for Side-Scrolling
# ----------------------------
class Camera:
    def __init__(self):
        self.x = 0

    def update(self, target_rect):
        # Smooth follow player
        target_x = target_rect.centerx - WIDTH // 3
        self.x += (target_x - self.x) * CAMERA_LAG
        self.x = max(0, min(self.x, LEVEL_LENGTH - WIDTH))

    def apply(self, rect):
        # Move object based on camera x
        return rect.move(-self.x, 0)

# ----------------------------
# Health Bar Drawing Function
# ----------------------------
def draw_health_bar(surf, x, y, pct, max_width=100):
    pct = max(0, pct)
    fill = int(max_width * pct / 100)
    pygame.draw.rect(surf, RED, pygame.Rect(x, y, fill, 10))
    pygame.draw.rect(surf, WHITE, pygame.Rect(x, y, max_width, 10), 2)

# ----------------------------
# Game Over Screen
# ----------------------------
def game_over_screen(player):
    screen.fill(BLACK)
    msg = "GAME OVER"
    score_msg = f"Score: {player.score}"
    restart_msg = "Press R to Restart or Q to Quit"
    screen.blit(font.render(msg, True, WHITE), (WIDTH//2 - 80, HEIGHT//2 - 60))
    screen.blit(font.render(score_msg, True, WHITE), (WIDTH//2 - 80, HEIGHT//2 - 20))
    screen.blit(font.render(restart_msg, True, WHITE), (WIDTH//2 - 180, HEIGHT//2 + 20))
    pygame.display.flip()

    # Wait for player input
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()

# ----------------------------
# Main Game Function
# ----------------------------
def main():
    level = 1
    camera = Camera()
    player = Player(100, HEIGHT - 100)
    projectiles = pygame.sprite.Group()
    platforms, enemies, collectibles = make_level(level)
    running = True
    game_over = False

    while running:
        clock.tick(FPS)

        # --- Handle events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()
                if event.key == pygame.K_f:
                    player.shoot(projectiles)

        # --- Update game logic ---
        if not game_over:
            player.update(platforms)
            projectiles.update()
            for enemy in enemies:
                enemy.update(platforms)
            camera.update(player.rect)

            # Check for projectile-enemy collisions
            for proj in projectiles:
                hit = pygame.sprite.spritecollideany(proj, enemies)
                if hit:
                    hit.take_damage(40)
                    proj.kill()
                    if not hit.alive():
                        player.score += 100 if not getattr(hit, 'boss', False) else 1000

            # Player touching enemies
            for enemy in enemies:
                if player.rect.colliderect(enemy.rect):
                    player.take_damage(20 if not getattr(enemy, 'boss', False) else 40)

            # Player collecting items
            for c in pygame.sprite.spritecollide(player, collectibles, True):
                if c.kind == "health":
                    player.health = min(100, player.health + 30)
                    player.score += 20
                elif c.kind == "life":
                    player.lives += 1
                    player.score += 100

            # Check for level completion
            if player.rect.left > LEVEL_LENGTH - 60:
                level += 1
                if level > 3:
                    game_over = True
                else:
                    player.rect.topleft = (100, HEIGHT - 100)
                    platforms, enemies, collectibles = make_level(level)

            # If player lost all lives
            if player.lives <= 0:
                game_over = True

        # --- Drawing on screen ---
        screen.fill((120, 200, 255))  # Background color

        for plat in platforms:
            screen.blit(plat.image, camera.apply(plat.rect))
        for c in collectibles:
            screen.blit(c.image, camera.apply(c.rect))
        for enemy in enemies:
            screen.blit(enemy.image, camera.apply(enemy.rect))
            draw_health_bar(screen, camera.apply(enemy.rect).x, camera.apply(enemy.rect).y - 12, enemy.health if not getattr(enemy, 'boss', False) else enemy.health / 2)
        for proj in projectiles:
            screen.blit(proj.image, camera.apply(proj.rect))
        screen.blit(player.image, camera.apply(player.rect))

        # Display UI (health, lives, score, level)
        draw_health_bar(screen, 20, 20, player.health)
        screen.blit(font.render(f"Lives: {player.lives}", True, WHITE), (20, 40))
        screen.blit(font.render(f"Score: {player.score}", True, WHITE), (20, 65))
        screen.blit(font.render(f"Level: {level}", True, WHITE), (WIDTH - 120, 20))

        # Game over screen
        if game_over:
            game_over_screen(player)
            # Reset game state
            level = 1
            camera = Camera()
            player = Player(100, HEIGHT - 100)
            projectiles = pygame.sprite.Group()
            platforms, enemies, collectibles = make_level(level)
            game_over = False

        pygame.display.flip()  # Show everything

# ----------------------------
# Start the game
# ----------------------------
if __name__ == "__main__":
    main()
    pygame.quit()
