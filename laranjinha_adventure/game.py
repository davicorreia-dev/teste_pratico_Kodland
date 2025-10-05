import pgzrun
import random
from pygame import Rect

# -----------------------
# Constants
# -----------------------
WIDTH = 800
HEIGHT = 600
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 4
ENEMY_SPEED = 1.5
SPRITE_WIDTH = 48
SPRITE_HEIGHT = 48
GOAL_WIDTH = 100
GOAL_HEIGHT = 50
GROUND_TOP = HEIGHT - 50

# -----------------------
# Game State
# -----------------------
game_state = 'menu'
selected_option = 0
menu_options = ['Start Game', 'Toggle Sound', 'Exit'] # <-- NOVO: Opção de som
sound_enabled = True # <-- NOVO: Variável de controle de som
hero = None
platforms = []
goal_rect = Rect(700, GROUND_TOP - GOAL_HEIGHT, GOAL_WIDTH, GOAL_HEIGHT)
enemies = []
game_over_reason = ''

# -----------------------
# Platform Setup
# -----------------------
def setup_platforms():
    return [
        Rect(0, GROUND_TOP, WIDTH, 50),  # Ground
        Rect(150, HEIGHT - 150, 150, 20),
        Rect(400, HEIGHT - 200, 150, 20),
        Rect(600, HEIGHT - 250, 150, 20),
    ]

# -----------------------
# Base Sprite Class
# -----------------------
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
        self.rect = Rect(self.x, self.y, SPRITE_WIDTH, SPRITE_HEIGHT)
        self.update_position()

    def update_position(self):
        # O Actor usa o centro para o pos, mas a física usa o topleft do Rect
        self.actor.pos = self.rect.center
        self.x = self.rect.x
        self.y = self.rect.y

    def apply_gravity(self):
        self.vy += GRAVITY
        # Não aplicamos o self.y aqui, para que a colisão seja verificada ANTES de mover o rect.
        # Vamos mover o rect em check_collisions.
        pass

    def check_vertical_collisions(self, platforms_list):
        
        # 1. Aplica a mudança de posição VERTICAL
        self.rect.y += self.vy
        
        self.on_ground = False
        
        # 2. Verifica a colisão com plataformas (e corrige a posição se necessário)
        for platform in platforms_list:
            if self.rect.colliderect(platform):
                
                # Colisão Vindo de Cima (Pouso)
                if self.vy > 0:
                    self.rect.bottom = platform.top # Força o pouso no topo
                    self.vy = 0
                    self.on_ground = True
                
                # Colisão Vindo de Baixo (Bateu a Cabeça)
                elif self.vy < 0:
                    self.rect.top = platform.bottom # Força o topo para baixo
                    self.vy = 0
        
        # 3. Colisão com o chão principal (como backup, se não estiver na lista de plataformas)
        if self.rect.bottom > GROUND_TOP:
            self.rect.bottom = GROUND_TOP
            self.vy = 0
            self.on_ground = True

    def check_horizontal_collisions(self, platforms_list):
        
        # O movimento horizontal já foi aplicado na classe Hero/Enemy.
        # Aqui, apenas corrigimos se houve colisão.
        
        for platform in platforms_list:
            if self.rect.colliderect(platform):
                # Para evitar conflito com a colisão vertical, verificamos se a
                # colisão ocorre no meio da altura (onde não há plataforma).
                
                if self.rect.bottom > platform.top + 5 and self.rect.top < platform.bottom - 5:
                    
                    # Colisão Vindo da Direita
                    if self.facing_right:
                        self.rect.right = platform.left
                    
                    # Colisão Vindo da Esquerda
                    else:
                        self.rect.left = platform.right

    def check_collisions(self, platforms_list):
        # 1. Movimento Horizontal e Colisão
        self.check_horizontal_collisions(platforms_list)
        
        # 2. Gravidade e Colisão Vertical
        self.apply_gravity() # Atualiza apenas self.vy, não self.y
        self.check_vertical_collisions(platforms_list)
        
        # 3. Atualiza a posição do ator visual
        self.update_position()

    def update_animation(self):
        if self.is_moving and self.walk_images:
            self.walk_frame += self.walk_anim_speed
            if self.walk_frame >= len(self.walk_images):
                self.walk_frame = 0
            image_name = self.walk_images[int(self.walk_frame)]
        else:
            if not self.on_ground:
                # Usa imagem de pulo se estiver no ar
                image_name = self.idle_images[1] 
            else:
                self.idle_frame += self.idle_anim_speed
                if self.idle_frame >= len(self.idle_images):
                    self.idle_frame = 0
                image_name = self.idle_images[0] # Usa imagem parada no chão
                
        self.actor.image = image_name
        self.actor.flip_x = not self.facing_right

# -----------------------
# Hero Class
# -----------------------
class Hero(AnimatedSprite):
    def __init__(self):
        idle = ['hero/hero_front', 'hero/hero_jump']
        walk = ['hero/hero_walk_a', 'hero/hero_walk_b']
        # Começa no topleft corrigido pelo rect do chão
        super().__init__(50, GROUND_TOP - SPRITE_HEIGHT, idle, walk) 
        self.speed = PLAYER_SPEED

    def move(self, dx):
        self.is_moving = dx != 0
        if dx != 0:
            # Aplica o movimento diretamente ao Rect.x
            self.rect.x += dx * self.speed 
            self.facing_right = dx > 0

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms_list):
        self.check_collisions(platforms_list)
        self.update_animation()

# -----------------------
# Enemy Class
# -----------------------
class Enemy(AnimatedSprite):
    # ... (A classe Enemy permanece a mesma, pois as colisões foram melhoradas na classe base) ...
    def __init__(self, x, y):
        idle = ['enemy/snail_rest', 'enemy/snail_shell']
        walk = ['enemy/snail_walk_a', 'enemy/snail_walk_b']
        super().__init__(x, y, idle, walk)
        self.speed = ENEMY_SPEED + random.random() * 0.5
        self.direction = random.choice([-1, 1])
        self.min_x = max(0, x - 150)
        self.max_x = min(WIDTH - SPRITE_WIDTH, x + 150)
        self.is_moving = True
        self.idle_counter = 0
        self.facing_right = self.direction > 0
        
    def move(self):
         # Aplica o movimento diretamente ao Rect.x
        self.rect.x += self.speed * self.direction
        
    def update(self, platforms_list):
        # Move horizontally
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

# -----------------------
# Game Management
# -----------------------
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
        
    # Reinicia o som
    if sound_enabled:
        # music.play('background') 
        music.set_volume(0.3)
    else:
        music.stop()

def check_goal_collision():
    global game_state, game_over_reason
    if hero and hero.rect.colliderect(goal_rect):
        game_state = 'game_over'
        game_over_reason = 'You Win!'

def check_enemy_collision():
    global game_state, game_over_reason
    for enemy in enemies:
        if hero and hero.rect.colliderect(enemy.rect):
            game_state = 'game_over'
            game_over_reason = 'Game Over! You were caught!'

# -----------------------
# PGZero Update
# -----------------------
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

# -----------------------
# Input
# -----------------------
def on_key_down(key):
    global game_state, selected_option, sound_enabled # <-- NOVO: sound_enabled
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
            if option == 'Start Game':
                game_state = 'playing'
                reset_game()
            elif option == 'Toggle Sound': # <-- NOVO: Lógica do Toggle
                sound_enabled = not sound_enabled
                menu_options[1] = 'Toggle Sound' 
                if sound_enabled:
                    music.unpause()
                else:
                    music.pause()
            elif option == 'Exit':
                exit()
    elif game_state == 'game_over':
        if key in [keys.RETURN, keys.SPACE]:
            game_state = 'menu'

# -----------------------
# Drawing
# -----------------------
def draw():
    screen.fill((100, 149, 237))  # Fundo azul
    if game_state == 'menu':
        screen.draw.text('Platform Adventure', center=(WIDTH/2, 150), fontsize=48, color='white')
        
        # Ajusta o texto do Toggle para refletir o estado atual
        display_options = list(menu_options)
        if 'Toggle Sound' in display_options:
            display_options[display_options.index('Toggle Sound')] = f"Toggle Sound ({'ON' if sound_enabled else 'OFF'})"
            
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
            screen.draw.text('Press ENTER or SPACE to return to menu', center=(WIDTH/2, HEIGHT/2+50), fontsize=20, color='white')

# -----------------------
# Start Game
# -----------------------
platforms = setup_platforms()
pgzrun.go()