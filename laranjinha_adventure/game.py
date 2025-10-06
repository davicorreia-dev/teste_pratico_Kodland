import pgzrun
import random
import math
from pygame import Rect

# CONSTANTES GLOBAIS
TITLE = "Laranjinha Adventure"  
WIDTH = 800
HEIGHT = 600
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 2.5
ENEMY_SPEED = 1.0
SPRITE_SIZE = 48 
GROUND_TOP = HEIGHT - 50
GOAL_WIDTH = 100
GOAL_HEIGHT = 50
GOAL_POS = (700, GROUND_TOP - GOAL_HEIGHT) # Posição do Objetivo

# VARIÁVEIS DE ESTADO
game_state = 'menu'
selected_option = 0
menu_options = ['Começar Jogo', 'Som', 'Sair do Jogo'] 
sound_enabled = True
hero = None
platforms = []
goal_rect = Rect(GOAL_POS, (GOAL_WIDTH, GOAL_HEIGHT))
enemies = []
game_over_reason = ''
goal_actor = None 

# FUNÇÕES DE INICIAÇÃO DO JOGO
def setup_platforms():
    # Retorna a lista de retângulos (chão e plataformas)
    return [
        Rect(0, GROUND_TOP, WIDTH, 50),
        Rect(150, HEIGHT - 150, 150, 20),
        Rect(400, HEIGHT - 200, 150, 20),
        Rect(600, HEIGHT - 250, 150, 20),
    ]

try:
    music.set_volume(0.4) 
    music.play('background') 
    if not sound_enabled:
        music.pause()

except Exception:
    pass # Ignora se não houver arquivos de música

# CLASSE BASE
class AnimatedSprite:
    def __init__(self, x, y, idle_images, walk_images):
        self.vy = 0
        self.facing_right = True
        self.is_moving = False
        self.on_ground = False
        self.walk_frame = 0
        self.walk_anim_speed = 0.2
        self.idle_images = idle_images
        self.walk_images = walk_images
        
        # Inicialização do Actor e Rect
        self.actor = Actor(self.idle_images[0])
        self.actor.anchor = ('center', 'bottom') 
        self.rect = Rect(x, y, SPRITE_SIZE, SPRITE_SIZE)
        
        # Variáveis de respiração
        self.breath_timer = random.uniform(0, math.pi * 2) 
        self.initial_bottom = self.rect.bottom 
        self.update_position()

    def update_position(self):
        # Lógica de Respiração 
        offset_y = 0
        if self.on_ground:
            self.breath_timer += 0.05
            offset_y = math.sin(self.breath_timer) * 0.5 
            
        self.rect.bottom = self.initial_bottom 
        self.actor.pos = (self.rect.centerx, self.rect.bottom + offset_y) 

    def check_collisions(self, platforms_list):
        # Determina a direção do movimento.
        self.rect.x += (self.facing_right * 2 - 1) * self.is_moving * self.speed 

        # Lógica da colisão horizontal 
        for p in platforms_list:
             if self.rect.colliderect(p) and (self.rect.bottom > p.top + 5 and self.rect.top < p.bottom - 5):
                 # Empurra o sprite para fora da plataforma
                 if self.facing_right:
                     self.rect.right = p.left
                 else:
                     self.rect.left = p.right

        # Lógica de Gravidade
        self.vy += GRAVITY
        self.rect.y += self.vy
        self.on_ground = False
        
        # Lógica de Colisão Vertical
        for p in platforms_list:
            if self.rect.colliderect(p):
                if self.vy > 0:
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.bottom 
                    self.vy = 0
        
        if self.rect.bottom > GROUND_TOP:
            self.rect.bottom = GROUND_TOP
            self.vy = 0
            self.on_ground = True

        # Atualiza a posição de base do chão para a respiração
        self.initial_bottom = self.rect.bottom 
        self.update_position()

    def update_animation(self):
        img = self.idle_images[0]
        
        # Lógica de animação de caminhada 
        if self.is_moving and self.walk_images and len(self.walk_images) > 1: 
            self.walk_frame += self.walk_anim_speed

            if self.walk_frame >= len(self.walk_images):
                self.walk_frame = 0

            img = self.walk_images[int(self.walk_frame)]
        
        elif not self.on_ground and len(self.idle_images) > 1:
            img = self.idle_images[-1] # Frame de pulo 
                
        self.actor.image = img
        
        # Evitar erro de não carregar a imagem
        if hasattr(self.actor.image, 'get_height'):
             self.actor.scale = SPRITE_SIZE / self.actor.image.get_height()
            
        self.update_position()
        self.actor.flip_x = not self.facing_right

# CLASSE HEROI
class Hero(AnimatedSprite):
    def __init__(self):
        super().__init__(50, GROUND_TOP - SPRITE_SIZE, 
        ['hero/hero_front', 'hero/hero_jump'], 
        ['hero/hero_walk_a', 'hero/hero_walk_b']) 
        self.speed = PLAYER_SPEED

    def move(self, dx):
        self.is_moving = dx != 0
        if dx != 0:
            # O movimento de 'self.rect.x' não é feito aqui, é feito no check_collisions
            self.facing_right = dx > 0

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms_list):
        # A velocidade de movimento do Hero é transmitida pelo 'self.is_moving' e 'self.facing_right'
        self.check_collisions(platforms_list)
        self.update_animation()

# CLASSE INIMIGO
class Enemy(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__(x, GROUND_TOP - SPRITE_SIZE, ['enemy/snail_rest'], []) 
        
        self.shell_sprite = 'enemy/snail_shell'
        self.speed = ENEMY_SPEED + random.random() * 0.5 
        self.direction = random.choice([-1, 1])
        self.min_x = max(0, x - 100)
        self.max_x = min(WIDTH - SPRITE_SIZE, x + 100)
        self.is_moving = True
        self.idle_counter = 0 # Contador de pausa
        self.facing_right = self.direction > 0
        
    def move(self):
        # O rect.x é movido pelo AnimatedSprite.check_collisions, aqui apenas defini a direção
        pass 

    def update(self, platforms_list):
        # Lógica de patrulha
        if self.is_moving:
            # Move o retangulo (Apenas para o Enemy)
            self.rect.x += self.speed * self.direction
            
            if self.rect.x <= self.min_x or self.rect.x >= self.max_x:
                self.direction *= -1
                self.facing_right = self.direction > 0
                self.is_moving = False
                self.idle_counter = 0
        else:
            self.idle_counter += 1
            if self.idle_counter > 60: # Pausa de 1 segundo (60 frames)
                self.is_moving = True
                
        # O Hero usa self.is_moving para determinar o movimento, o Enemy para determinar o estado.
        self.check_collisions(platforms_list)
        self.update_animation()

    def update_animation(self):
        # Lógica: Casco se parado, Caracol se movendo
        img = self.shell_sprite if not self.is_moving else self.idle_images[0]
        
        self.actor.image = img
        
        if hasattr(self.actor.image, 'get_height'):
             self.actor.scale = SPRITE_SIZE / self.actor.image.get_height()
            
        self.update_position()
        self.actor.flip_x = not self.facing_right

# FUNÇÕES GLOBAIS DO JOGO
def reset_game():
    global hero, platforms, goal_actor, enemies
    
    enemy_start_x = [200, 450, 650] 
    start_y = GROUND_TOP - SPRITE_SIZE 
    
    hero = Hero()
    platforms[:] = setup_platforms()
    
    enemies.clear()
    for start_x in enemy_start_x:
        enemies.append(Enemy(start_x, start_y))
        
    # Inicialização do Actor da Bandeira
    global goal_actor
    goal_actor = Actor('goal.png') 
    goal_actor.center = goal_rect.center
    goal_actor.bottom = goal_rect.top 
    
    try:
        if sound_enabled and not music.is_playing('background'):
            music.play('background') 

        elif not sound_enabled:
            music.pause()

    except Exception:
        pass

def check_collisions():
    global game_state, game_over_reason

    if hero and hero.rect.colliderect(goal_rect):
        game_state = 'game_over'
        game_over_reason = 'Você Passou de Fase!'
        return

    for enemy in enemies:
        if hero and hero.rect.colliderect(enemy.rect):
            game_state = 'game_over'
            game_over_reason = 'Game Over! Você foi pego!'
            try:
                if sound_enabled: music.stop(); sounds.impact.play(0)
            except Exception: pass
            return

def update():
    if game_state == 'playing' and hero:
        hero.move(int(keyboard.right) - int(keyboard.left))

        if keyboard.space: hero.jump()

        hero.update(platforms)

        for enemy in enemies: enemy.update(platforms)
        check_collisions()

def on_key_down(key):
    global game_state, selected_option, sound_enabled
    
    if key == keys.ESCAPE:
        game_state = 'menu' if game_state in ['playing', 'game_over'] else exit()
            
    elif game_state == 'menu':
        if key == keys.UP: selected_option = (selected_option - 1) % len(menu_options)
        elif key == keys.DOWN: selected_option = (selected_option + 1) % len(menu_options)
        elif key == keys.RETURN:
            if selected_option == 0:
                game_state = 'playing'
                reset_game()
            elif selected_option == 1:
                sound_enabled = not sound_enabled
                try: music.unpause() if sound_enabled else music.pause()
                except Exception: pass
            elif selected_option == 2:
                exit()
    
    elif game_state == 'game_over':
        if key in [keys.RETURN, keys.SPACE]:
            game_state = 'menu'
            try:
                if sound_enabled: music.play('background')
                
            except Exception: pass

def draw():
    screen.fill((100, 149, 237))
    if game_state == 'menu':
        screen.draw.text('Laranjinha Adventure', center=(WIDTH/2, 150), fontsize=48, color='white')
        display_options = list(menu_options)
        display_options[1] = f"Som: {'Ativo' if sound_enabled else 'Desativado'}"
            
        for i, option in enumerate(display_options):
            color = 'yellow' if i == selected_option else 'white'
            screen.draw.text(option, center=(WIDTH/2, 250 + i*60), fontsize=32, color=color)
            
    else:
        # Desenha elementos do jogo
        for p in platforms: screen.draw.filled_rect(p, 'darkgreen' if p.top == GROUND_TOP else 'brown')
        screen.draw.filled_rect(goal_rect, 'gold')
        if goal_actor: goal_actor.draw() 
        if hero: hero.actor.draw()
        for enemy in enemies: enemy.actor.draw()

        if game_state == 'game_over':
            screen.draw.filled_rect(Rect(0,0,WIDTH,HEIGHT),(0,0,0,128))
            screen.draw.text(game_over_reason, center=(WIDTH/2, HEIGHT/2-50), fontsize=32, color='white')
            screen.draw.text('Pressione ENTER ou ESPAÇO para voltar ao menu', center=(WIDTH/2, HEIGHT/2+50), fontsize=20, color='white')

platforms = setup_platforms()
pgzrun.go()