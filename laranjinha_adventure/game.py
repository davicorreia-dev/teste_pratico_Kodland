import pgzrun
import random
from pygame import Rect

# CONSTANTES
WIDTH = 800
HEIGHT = 600
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 2.5  # Velocidade do Herói
ENEMY_SPEED = 1.0   # Velocidade Base do Inimigo
SPRITE_WIDTH = 48 
SPRITE_HEIGHT = 48
GOAL_WIDTH = 100
GOAL_HEIGHT = 50
GROUND_TOP = HEIGHT - 50

# VARIÁVEIS DE ESTADO 
game_state = 'menu'
selected_option = 0
menu_options = ['Começar Jogo', 'Ativar/Desativar Som', 'Sair'] 
sound_enabled = True
hero = None
platforms = []
goal_rect = Rect(700, GROUND_TOP - GOAL_HEIGHT, GOAL_WIDTH, GOAL_HEIGHT)
enemies = []
game_over_reason = ''
goal_actor = None 

# INICIALIZAÇÃO DE MÚSICA 
try:
    music.set_volume(0.4) 
    music.play('background') 
    if not sound_enabled:
        music.pause()

except Exception:
    print("Aviso: Arquivos de som podem estar faltando.")
    pass

def setup_platforms():
    # Retorna a lista de retângulos (chão e plataformas)
    return [
        Rect(0, GROUND_TOP, WIDTH, 50),
        Rect(150, HEIGHT - 150, 150, 20),
        Rect(400, HEIGHT - 200, 150, 20),
        Rect(600, HEIGHT - 250, 150, 20),
    ]

# CLASSE BASE PARA PERSONAGENS ANIMADOS
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
        self.actor = Actor(self.idle_images[0])
        self.actor.anchor = ('center', 'bottom') 
        self.actor.scale = 1.0 
        # Rect é a caixa de colisão
        self.rect = Rect(x, y, SPRITE_WIDTH, SPRITE_HEIGHT)
        self.update_position()

    def update_position(self):
        # Sincroniza o Actor visual com a parte de baixo do rect de colisão
        self.actor.pos = (self.rect.centerx, self.rect.bottom) 

    def check_collisions(self, platforms_list):
        self.rect.x += (self.facing_right * 2 - 1) * self.is_moving * 4 
        
        # Colisão horizontal básica
        for p in platforms_list:
            if self.rect.colliderect(p) and (self.rect.bottom > p.top + 5 and self.rect.top < p.bottom - 5):
                self.rect.right = p.left if self.facing_right else self.rect.left
                self.rect.left = p.right if not self.facing_right else self.rect.left

        # Aplica gravidade
        self.vy += GRAVITY
        self.rect.y += self.vy
        self.on_ground = False
        
        # Colisão vertical (chão e plataformas)
        for p in platforms_list:
            if self.rect.colliderect(p):
                if self.vy > 0: # Caindo
                    self.rect.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0: # Pulando para cima
                    self.rect.top = p.bottom 
                    self.vy = 0
        
        # Colisão com o chão principal da tela
        if self.rect.bottom > GROUND_TOP:
            self.rect.bottom = GROUND_TOP
            self.vy = 0
            self.on_ground = True
        self.update_position()

    def update_animation(self):
        img = self.idle_images[0]

        # Lógica para alternar os sprites
        if self.is_moving and self.walk_images:
            self.walk_frame += self.walk_anim_speed

            if self.walk_frame >= len(self.walk_images):
                self.walk_frame = 0

            img = self.walk_images[int(self.walk_frame)]

        elif not self.on_ground:
            img = self.idle_images[-1] # Frame de pulo
                
        self.actor.image = img
        
        # Garante que a escala visual do Actor seja SPRITE_HEIGHT
        try:
            ch = self.actor.image.get_height()
            if ch > 0:
                self.actor.scale = SPRITE_HEIGHT / ch
        except Exception:
            self.actor.scale = 1.0
            
        self.update_position()
        self.actor.flip_x = not self.facing_right

# CLASSE HERÓI
class Hero(AnimatedSprite):
    def __init__(self):
        super().__init__(50, GROUND_TOP - SPRITE_HEIGHT, ['hero/hero_front', 'hero/hero_jump'], ['hero/hero_walk_a', 'hero/hero_walk_b']) 
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

# CLASSE INIMIGO 
class Enemy(AnimatedSprite):
    def __init__(self, x, y):
        super().__init__(x, GROUND_TOP - SPRITE_HEIGHT, ['enemy/snail_rest', 'enemy/snail_shell', 'enemy/snail_rest'], ['enemy/snail_walk_a', 'enemy/snail_walk_b']) 
        # Adiciona variação aleatória de velocidade para o inimigo
        self.speed = ENEMY_SPEED + random.random() * 0.5 
        self.direction = random.choice([-1, 1])
        self.min_x = max(0, x - 100) # Limite de patrulha
        self.max_x = min(WIDTH - SPRITE_WIDTH, x + 100)
        self.is_moving = True
        self.idle_counter = 0
        self.facing_right = self.direction > 0
        
    def move(self):
        self.rect.x += self.speed * self.direction
        
    def update(self, platforms_list):
        # Lógica de patrulha e pausa
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

# FUNÇÕES GLOBAIS 
def reset_game():
    global hero, platforms, goal_rect, enemies, goal_actor 
    
    # Posições X fixas para os caracóis
    enemy_start_x = [200, 450, 650] 
    
    hero = Hero()
    platforms[:] = setup_platforms()
    goal_rect.topleft = (700, GROUND_TOP - GOAL_HEIGHT)
    enemies.clear()
    
    # Cria os inimigos em posições fixas
    ey = GROUND_TOP - SPRITE_HEIGHT 
    for ex in enemy_start_x:
        enemies.append(Enemy(ex, ey))
        
    global goal_actor
    goal_actor = Actor('goal.png') 
    goal_actor.centerx = goal_rect.centerx
    goal_actor.bottom = goal_rect.top 
    
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

    if game_state != 'playing': return # Evita checagem se não estiver jogando

    for enemy in enemies:
        if hero and hero.rect.colliderect(enemy.rect):
            game_state = 'game_over'
            game_over_reason = 'Game Over! Você foi pego!'
            if sound_enabled:
                try:
                    music.stop()
                    sounds.impact.set_volume(1.0)
                    sounds.impact.play(0)
                except Exception:
                    print("ERRO DE SOM: Não foi possível tocar 'impact.ogg'.")
            return

def update():
    if game_state == 'playing' and hero:
        hero.move(int(keyboard.right) - int(keyboard.left))
        if keyboard.space: hero.jump()
        hero.update(platforms)
        for enemy in enemies: enemy.update(platforms)
        check_enemy_collision()
        check_goal_collision()

def on_key_down(key):
    global game_state, selected_option, sound_enabled
    
    # Tecla ESC
    if key == keys.ESCAPE:
        if game_state in ['playing', 'game_over']:
            game_state = 'menu'
        else:
            exit()
            
    elif game_state == 'menu':
        
        # Navegação do Menu
        if key == keys.UP:
            selected_option = (selected_option - 1) % len(menu_options)
        elif key == keys.DOWN:
            selected_option = (selected_option + 1) % len(menu_options)
        
        # Seleção da Opção 
        elif key == keys.RETURN:
            # Opção 'Começar Jogo'
            if selected_option == 0:
                game_state = 'playing'
                reset_game()
            
            # Opção 'Ativar/Desativar Som'
            elif selected_option == 1:
                sound_enabled = not sound_enabled
                try: 
                    if sound_enabled:
                        music.unpause()
                    else:
                        music.pause()
                except Exception: 
                    pass
            
            # Opção 'Sair'
            elif selected_option == 2:
                exit()
    
    # Lógica da Tela de Fim de Jogo
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
        
        # Exibe a opção de som no menu
        d = list(menu_options)
        d[1] = f"Som: {'Ativado' if sound_enabled else 'Desativado'}"
            
        for i, option in enumerate(d):
            color = 'yellow' if i == selected_option else 'white'
            screen.draw.text(option, center=(WIDTH/2, 250 + i*60), fontsize=32, color=color)
            
    else:
        # Desenha plataformas 
        for p in platforms: screen.draw.filled_rect(p, 'darkgreen' if p.top == GROUND_TOP else 'brown')
        
        screen.draw.filled_rect(goal_rect, 'gold')
        if goal_actor: goal_actor.draw() # Desenha a imagem da bandeira
        
        if hero: hero.actor.draw()
        for enemy in enemies: enemy.actor.draw()

        if game_state == 'game_over': #Tela de Game Over
            screen.draw.filled_rect(Rect(0,0,WIDTH,HEIGHT),(0,0,0,128))
            screen.draw.text(game_over_reason, center=(WIDTH/2, HEIGHT/2-50), fontsize=32, color='white')
            screen.draw.text('Pressione ENTER ou ESPAÇO para voltar ao menu', center=(WIDTH/2, HEIGHT/2+50), fontsize=20, color='white')

platforms = setup_platforms()
pgzrun.go()