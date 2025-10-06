import pgzrun
import random
from pygame import Rect

# Constantes do Jogo
WIDTH = 800
HEIGHT = 600
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 4
ENEMY_SPEED = 1.5
SPRITE_WIDTH = 32
SPRITE_HEIGHT = 32 
GOAL_WIDTH = 100
GOAL_HEIGHT = 50
GROUND_TOP = HEIGHT - 50


# Estados do Jogo
game_state = 'menu'
selected_option = 0
menu_options = ['Começar Jogo', 'Ativar/Desativar Som', 'Sair'] 
sound_enabled = True
hero = None
platforms = []
goal_rect = Rect(700, GROUND_TOP - GOAL_HEIGHT, GOAL_WIDTH, GOAL_HEIGHT)
enemies = []
game_over_reason = ''

try:
    music.set_volume(0.4) 
    music.play('background') 

    if not sound_enabled:
        music.pause()

except Exception:
    print("Aviso: Arquivos de som 'background' ou 'jump' podem estar faltando.")
    pass


# Configurações das plataformas
def setup_platforms():
    return [
        Rect(0, GROUND_TOP, WIDTH, 50),
        Rect(150, HEIGHT - 150, 150, 20),
        Rect(400, HEIGHT - 200, 150, 20),
        Rect(600, HEIGHT - 250, 150, 20),
    ]

class AnimatedSprite:
    def __init__(self, x, y, idle_images, walk_images):
        self.x = x
        self.y = y
        self.vy = 0
        self.facing_right = True
        self.is_moving = False
        self.on_ground = False
        self.idle_frame = 0
        self.walk_frame = 0
        self.idle_anim_speed = 0.1
        self.walk_anim_speed = 0.2
        self.idle_images = idle_images
        self.walk_images = walk_images
        self.actor = Actor(self.idle_images[0])
        self.actor.anchor = ('center', 'bottom') 

        self.rect = Rect(self.x, self.y, SPRITE_WIDTH, SPRITE_HEIGHT)
        self.update_position()

    def update_position(self):
        self.actor.pos = (self.rect.centerx, self.rect.bottom) 
        self.x = self.rect.x
        self.y = self.rect.y

    def apply_gravity(self):
        self.vy += GRAVITY
        pass

    def check_vertical_collisions(self, platforms_list):
        self.rect.y += self.vy
        self.on_ground = False
        
        for platform in platforms_list:
            if self.rect.colliderect(platform):

                if self.vy > 0:
                    self.rect.bottom = platform.top
                    self.vy = 0
                    self.on_ground = True

                elif self.vy < 0:
                    self.rect.top = platform.bottom 
                    self.vy = 0
        
        if self.rect.bottom > GROUND_TOP:
            self.rect.bottom = GROUND_TOP
            self.vy = 0
            self.on_ground = True

    def check_horizontal_collisions(self, platforms_list):
        for platform in platforms_list:
            if self.rect.colliderect(platform):

                if (self.rect.bottom > platform.top + 5 and 
                    self.rect.top < platform.bottom - 5):

                    if self.facing_right:
                        self.rect.right = platform.left

                    else:
                        self.rect.left = platform.right

    def check_collisions(self, platforms_list):
        self.check_horizontal_collisions(platforms_list)
        self.apply_gravity()
        self.check_vertical_collisions(platforms_list)
        self.update_position()

    def update_animation(self):
        if self.is_moving and self.walk_images:
            self.walk_frame += self.walk_anim_speed

            if self.walk_frame >= len(self.walk_images):
                self.walk_frame = 0

            image_name = self.walk_images[int(self.walk_frame)]

        else:

            if not self.on_ground:
                image_name = self.idle_images[1] 

            else:
                self.idle_frame += self.idle_anim_speed
                if self.idle_frame >= len(self.idle_images):
                    self.idle_frame = 0
                image_name = self.idle_images[0] 
                
        self.actor.image = image_name
        self.actor.flip_x = not self.facing_right

class Hero(AnimatedSprite):
    def __init__(self):
        idle = ['hero/hero_front', 'hero/hero_jump']
        walk = ['hero/hero_walk_a', 'hero/hero_walk_b']
        super().__init__(50, GROUND_TOP - SPRITE_HEIGHT, idle, walk) 
        self.speed = PLAYER_SPEED

    def move(self, dx):
        self.is_moving = dx != 0
        if dx != 0:
            self.rect.x += dx * self.speed 
            self.facing_right = dx > 0

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms_list):
        self.check_collisions(platforms_list)
        self.update_animation()

class Enemy(AnimatedSprite):
    def __init__(self, x, y):
        idle = ['enemy/snail_rest', 'enemy/snail_shell']
        walk = ['enemy/snail_walk_a', 'enemy/snail_walk_b']
        super().__init__(x, GROUND_TOP - SPRITE_HEIGHT, idle, walk) 
        self.speed = ENEMY_SPEED + random.random() * 0.5
        self.direction = random.choice([-1, 1])
        self.min_x = max(0, x - 150)
        self.max_x = min(WIDTH - SPRITE_WIDTH, x + 150)
        self.is_moving = True
        self.idle_counter = 0
        self.facing_right = self.direction > 0
        
    def move(self):
        self.rect.x += self.speed * self.direction
        
    def update(self, platforms_list):
        if self.is_moving:
            self.move()
            if self.rect.x <= self.min_x or self.rect.x >= self.max_x:
                self.direction *= -1
                self.facing_right = self.direction > 0
                self.is_moving = False
                self.idle_counter = 0
        else:
            self.idle_counter += 1
            if self.idle_counter > 60:
                self.is_moving = True
        
        self.check_collisions(platforms_list)
        self.update_animation()

def reset_game():
    global hero, platforms, goal_rect, enemies
    hero = Hero()
    platforms[:] = setup_platforms()
    goal_rect.topleft = (700, GROUND_TOP - GOAL_HEIGHT)
    enemies.clear()

    for _ in range(3):
        ex = random.randint(200, WIDTH - 200)
        ey = GROUND_TOP - SPRITE_HEIGHT 
        enemies.append(Enemy(ex, ey))
        
    try:
        if sound_enabled and not music.is_playing('background'):
            music.play('background') 
        elif not sound_enabled:
            music.pause()
    except Exception:
        pass

def check_goal_collision():
    global game_state, game_over_reason
    if hero and hero.rect.colliderect(goal_rect):
        game_state = 'game_over'
        game_over_reason = 'Você Passou de Fase!'

def check_enemy_collision():
    global game_state, game_over_reason
    for enemy in enemies:
        if hero and hero.rect.colliderect(enemy.rect):
            game_state = 'game_over'
            game_over_reason = 'Game Over! Você foi pego!'

def update():
    if game_state == 'playing' and hero:
        dx = int(keyboard.right) - int(keyboard.left)
        hero.move(dx)

        if keyboard.space:
            hero.jump()
        hero.update(platforms)

        for enemy in enemies:
            enemy.update(platforms)
        check_enemy_collision()
        check_goal_collision()

def on_key_down(key):
    global game_state, selected_option, sound_enabled
    if key == keys.ESCAPE:

        if game_state in ['playing', 'game_over']:
            game_state = 'menu'

        else:
            exit()

    elif game_state == 'menu':

        if key == keys.UP:
            selected_option = (selected_option - 1) % len(menu_options)

        elif key == keys.DOWN:
            selected_option = (selected_option + 1) % len(menu_options)

        elif key == keys.RETURN:
            option = menu_options[selected_option]

            if option == 'Começar Jogo':
                game_state = 'playing'
                reset_game()

            elif option == 'Ativar/Desativar Som': 
                sound_enabled = not sound_enabled

                try:
                    if sound_enabled:
                        music.unpause()

                    else:
                        music.pause()

                except Exception:
                    pass
                    
            elif option == 'Sair':
                exit()

    elif game_state == 'game_over':

        if key in [keys.RETURN, keys.SPACE]:
            game_state = 'menu'

            try:
                if sound_enabled:
                    music.play('background')

            except Exception:
                pass

def draw():
    screen.fill((100, 149, 237))

    if game_state == 'menu':
        screen.draw.text('Laranjinha Adventure', center=(WIDTH/2, 150), fontsize=48, color='white')
        
        display_options = list(menu_options)
        sound_index = display_options.index('Ativar/Desativar Som')
        display_options[sound_index] = f"Som: {'ON' if sound_enabled else 'OFF'}"
            
        for i, option in enumerate(display_options):
            color = 'yellow' if i == selected_option else 'white'
            screen.draw.text(option, center=(WIDTH/2, 250 + i*60), fontsize=32, color=color)

    else:
        for platform in platforms:
            color = 'darkgreen' if platform.top == GROUND_TOP else 'brown'
            screen.draw.filled_rect(platform, color)

        screen.draw.filled_rect(goal_rect, 'gold')
        screen.draw.text('GOAL', center=(goal_rect.centerx, goal_rect.centery), fontsize=20, color='black')
        
        if hero:
            hero.actor.draw()

        for enemy in enemies:
            enemy.actor.draw()
            
        if game_state == 'game_over':
            screen.draw.filled_rect(Rect(0,0,WIDTH,HEIGHT),(0,0,0,128))
            screen.draw.text(game_over_reason, center=(WIDTH/2, HEIGHT/2-50), fontsize=32, color='white')
            screen.draw.text('Pressione ENTER ou ESPAÇO para voltar ao menu', center=(WIDTH/2, HEIGHT/2+50), fontsize=20, color='white')

platforms = setup_platforms()
pgzrun.go()