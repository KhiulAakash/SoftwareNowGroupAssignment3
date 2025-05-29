import pygame
import sys
import random

# === Constants ===
WIDTH, HEIGHT    = 800, 600
FPS              = 60
LEVEL_WIDTH      = 2400   # total level width

# Player sprite size and physics
SPRITE_WIDTH     = 40
SPRITE_HEIGHT    = 60
COYOTE_FRAMES    = 6      # frames of jump grace
GRAVITY          = 0.8
TERMINAL_VY      = 12

# Villain (boss) sprite size
VILLAIN_WIDTH    = 80
VILLAIN_HEIGHT   = 100
# Enemy vertical offset so it doesn't touch platforms
ENEMY_OFFSET     = 5

# Colors
WHITE    = (255,255,255)
BLACK    = (  0,  0,  0)
RED      = (255,  0,  0)
GREEN    = (  0,255,  0)
YELLOW   = (255,255,  0)
BLUE     = (  0,  0,255)
SKY_BLUE = (135,206,235)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Load player sprite
        img = pygame.image.load("assets/boxy_01.png").convert_alpha()
        self.base_image = pygame.transform.scale(img, (SPRITE_WIDTH, SPRITE_HEIGHT))
        self.image = self.base_image
        self.rect  = self.image.get_rect(topleft=(x, y))

        # movement & state
        self.vel              = pygame.math.Vector2(0, 0)
        self.speed            = 5
        self.jump_strength    = 15
        self.on_ground        = False
        self.coyote_timer     = 0
        self.facing           = 1  # 1 = right, -1 = left

        # health/invincibility
        self.health           = 100
        self.max_health       = 100
        self.lives            = 3
        self.invincible_timer = 0

    def move(self, dx):
        self.vel.x = dx * self.speed
        if dx < 0:
            self.facing = -1
        elif dx > 0:
            self.facing = 1

    def jump(self):
        if self.on_ground or self.coyote_timer > 0:
            self.vel.y = -self.jump_strength
            self.on_ground = False
            self.coyote_timer = 0

    def shoot(self, projectiles_group):
        proj = Projectile(self.rect.centerx, self.rect.centery, 10, 0)
        projectiles_group.add(proj)

    def take_damage(self, dmg):
        if self.invincible_timer <= 0:
            self.health -= dmg
            self.invincible_timer = FPS  # 1s invincibility
            if self.health <= 0:
                self.lives -= 1
                self.health = self.max_health if self.lives > 0 else 0

    def update(self):
        # gravity
        self.vel.y = min(self.vel.y + GRAVITY, TERMINAL_VY)
        # invincibility countdown
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        # flip sprite based on facing
        if self.facing < 0:
            self.image = pygame.transform.flip(self.base_image, True, False)
        else:
            self.image = self.base_image


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy):
        super().__init__()
        self.image  = pygame.Surface((10,5))
        self.image.fill(YELLOW)
        self.rect   = self.image.get_rect(center=(x, y))
        self.vel    = pygame.math.Vector2(vx, vy)
        self.damage = 25

    def update(self):
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        if (self.rect.right < 0 or self.rect.left > LEVEL_WIDTH
            or self.rect.bottom < 0 or self.rect.top > HEIGHT):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_width=200):
        super().__init__()
        # Load enemy sprite
        img = pygame.image.load("/Users/roshan/Desktop/assignment_asim/first_task/assets/ogre_02.png").convert_alpha()
        self.image = pygame.transform.scale(img, (40, 50))
        # position with a small vertical offset
        self.rect = self.image.get_rect(topleft=(x, y - ENEMY_OFFSET))
        self.start_x      = x
        self.patrol_width = patrol_width
        self.vel          = pygame.math.Vector2(2, 0)
        self.health       = 50

    def take_damage(self, dmg):
        self.health -= dmg
        if self.health <= 0:
            self.kill()

    def update(self):
        self.rect.x += int(self.vel.x)
        if self.rect.x < self.start_x or self.rect.x > self.start_x + self.patrol_width:
            self.vel.x *= -1


class BossEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, patrol_width=200)
        # Load villain sprite
        img = pygame.image.load("/Users/roshan/Desktop/assignment_asim/first_task/assets/ogre_02.png").convert_alpha()
        self.image = pygame.transform.scale(img, (VILLAIN_WIDTH, VILLAIN_HEIGHT))
        self.rect  = self.image.get_rect(topleft=(x, y))
        self.health      = 300
        self.shoot_timer = FPS * 2

    def update(self):
        # allow boss to patrol like a regular enemy
        super().update()
        # shooting logic
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = FPS * 2
            self.fire()
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = FPS * 2
            self.fire()

    def fire(self):
        direction = pygame.math.Vector2(player.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction.length() != 0:
            direction = direction.normalize() * 7
        proj = Projectile(self.rect.centerx, self.rect.centery,
                          direction.x, direction.y)
        all_sprites.add(proj)
        enemy_projectiles.add(proj)


class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y, type_):
        super().__init__()
        self.type = type_
        self.image = pygame.Surface((20,20))
        # Use defined colors
        self.image.fill(BLUE if type_=='score' else GREEN if type_=='health' else YELLOW)
        self.rect  = self.image.get_rect(center=(x, y))
        self.value = 10 if type_=='score' else 30 if type_=='health' else 1

    def apply(self, player):
        if self.type == 'score':
            game.score += self.value
        elif self.type == 'health':
            player.health = min(player.max_health, player.health + self.value)
        else:
            player.lives += 1
        self.kill()


class Camera:
    def __init__(self, width, height):
        self.rect = pygame.Rect(0, 0, width, height)

    def apply(self, spr):
        return spr.rect.move(-self.rect.x, -self.rect.y)

    def update(self, target):
        x = target.rect.centerx - WIDTH//2
        y = target.rect.centery - HEIGHT//2
        x = max(0, min(x, self.rect.width - WIDTH))
        y = max(0, min(y, self.rect.height - HEIGHT))
        self.rect.topleft = (x, y)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Side-Scroller Final")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock  = pygame.time.Clock()

        global all_sprites, enemies, projectiles, enemy_projectiles, collectibles, platforms, player
        all_sprites       = pygame.sprite.Group()
        enemies           = pygame.sprite.Group()
        projectiles       = pygame.sprite.Group()
        enemy_projectiles = pygame.sprite.Group()
        collectibles      = pygame.sprite.Group()
        platforms         = pygame.sprite.Group()
        self.platforms    = platforms

        # build platforms
        PLATFORM_DATA = [
            (0,   HEIGHT-40, LEVEL_WIDTH, 40),
            (300, HEIGHT-140, 200, 20),
            (700, HEIGHT-200, 200, 20),
            (1100,HEIGHT-260, 200,20),
            (1500,HEIGHT-200,200,20),
            (1900,HEIGHT-140,200,20),
        ]
        for x,y,w,h in PLATFORM_DATA:
            p = pygame.sprite.Sprite()
            p.image = pygame.Surface((w,h))
            p.image.fill(BLACK)
            p.rect  = p.image.get_rect(topleft=(x,y))
            platforms.add(p)
            all_sprites.add(p)

        self.camera    = Camera(LEVEL_WIDTH, HEIGHT)
        self.level     = 1
        self.score     = 0
        self.game_over = False

        spawn_y = HEIGHT-40-SPRITE_HEIGHT
        player = Player(50, spawn_y)
        all_sprites.add(player)
        self.load_level()

    def load_level(self):
        enemies.empty(); projectiles.empty(); enemy_projectiles.empty(); collectibles.empty()
        ENEMY_POSITIONS = {1: [(500,HEIGHT-90),(900,HEIGHT-150)],
                           2: [(1300,HEIGHT-90),(1700,HEIGHT-150),(2100,HEIGHT-90)],
                           3: [(600,HEIGHT-90),(1000,HEIGHT-150),(1400,HEIGHT-90),(1800,HEIGHT-150)]}
        COLLECTIBLES     = {1: [('score',350,HEIGHT-160),('health',800,HEIGHT-220)],
                           2: [('score',1250,HEIGHT-160),('life',1650,HEIGHT-220)],
                           3: [('score',950,HEIGHT-160),('health',1550,HEIGHT-220),('life',2050,HEIGHT-160)]}
        for x,y in ENEMY_POSITIONS[self.level]:
            cls = BossEnemy if self.level==3 and x>1700 else Enemy
            e = cls(x,y); enemies.add(e); all_sprites.add(e)
        for t,x,y in COLLECTIBLES[self.level]:
            c = Collectible(x,y,t); collectibles.add(c); all_sprites.add(c)

    def run(self):
        while True:
            self.clock.tick(FPS); self.handle_events();
            if not self.game_over: self.update()
            self.draw()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            elif e.type==pygame.KEYDOWN:
                if not self.game_over:
                    if e.key in (pygame.K_w,pygame.K_UP): player.jump()
                    elif e.key==pygame.K_SPACE: player.shoot(projectiles); all_sprites.add(projectiles)
                else:
                    if e.key==pygame.K_r: self.__init__()
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        player.move(dx)

    def update(self):
        player.on_ground=False; player.update()
        # Horizontal
        player.rect.x+=int(player.vel.x)
        for p in pygame.sprite.spritecollide(player,self.platforms,False):
            if player.vel.x>0: player.rect.right=p.rect.left
            elif player.vel.x<0: player.rect.left=p.rect.right
            player.vel.x=0
        # Vertical
        player.rect.y+=int(player.vel.y)
        for p in pygame.sprite.spritecollide(player,self.platforms,False):
            if player.vel.y>0:
                player.rect.bottom=p.rect.top; player.vel.y=0; player.on_ground=True
            elif player.vel.y<0:
                player.rect.top=p.rect.bottom; player.vel.y=0
        if player.on_ground: player.coyote_timer=COYOTE_FRAMES
        elif player.coyote_timer>0: player.coyote_timer-=1
        for proj in pygame.sprite.spritecollide(player,enemy_projectiles,True): player.take_damage(proj.damage)
        if pygame.sprite.spritecollide(player,enemies,False): player.take_damage(1)
        for enemy,projs in pygame.sprite.groupcollide(enemies,projectiles,False,True).items():
            for proj in projs:
                enemy.take_damage(proj.damage)
                if not enemy.alive(): self.score+=50
        for c in pygame.sprite.spritecollide(player,collectibles,False): c.apply(player)
        if player.rect.x>LEVEL_WIDTH-50:
            if self.level<3: self.level+=1; self.load_level(); player.rect.topleft=(50,HEIGHT-100); self.camera.rect.topleft=(0,0)
            else: self.game_over=True
        if player.lives<=0: self.game_over=True
        self.camera.update(player)

    def draw(self):
        self.screen.fill(SKY_BLUE)
        for spr in all_sprites: self.screen.blit(spr.image,self.camera.apply(spr))
        self.draw_hud()
        if self.game_over: self.draw_game_over()
        pygame.display.flip()

    def draw_hud(self):
        bar_len,bar_h=200,20; fill=(player.health/player.max_health)*bar_len
        pygame.draw.rect(self.screen,RED,(10,10,fill,bar_h)); pygame.draw.rect(self.screen,BLACK,(10,10,bar_len,bar_h),2)
        for i in range(player.lives): pygame.draw.rect(self.screen,GREEN,(10+i*30,40,20,20))
        font=pygame.font.SysFont(None,24); surf=font.render(f"Score: {self.score}",True,BLACK); self.screen.blit(surf,(WIDTH-120,10))

    def draw_game_over(self):
        font=pygame.font.SysFont(None,72); go=font.render("GAME OVER",True,RED); self.screen.blit(go,go.get_rect(center=(WIDTH//2,HEIGHT//2-50)))
        msg=pygame.font.SysFont(None,36).render("Press R to Restart",True,BLACK); self.screen.blit(msg,msg.get_rect(center=(WIDTH//2,HEIGHT//2+20)))

if __name__=="__main__": game=Game(); game.run()
