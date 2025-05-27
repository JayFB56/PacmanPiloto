# Pacman in Python with PyGame
import pygame
import math
import random
import os
from pygame import time

# Configuración inicial
pygame.init()
screen = pygame.display.set_mode([606, 606])
pygame.display.set_caption('Pacman')
clock = pygame.time.Clock()

# Colores
black = (0, 0, 0)
white = (255, 255, 255)
yellow = (255, 255, 0)
blue = (0, 0, 255)
vulnerable_color = (33, 33, 255)  # Azul oscuro para fantasmas vulnerables
blink_colors = [(33, 33, 255), (255, 255, 255)]  # Parpadeo: azul y blanco


# Cargar imágenes de fantasmas
def load_ghost_images():
    ghost_images = {}
    try:
        ghost_images['red'] = pygame.image.load(os.path.join('imagenes', 'rojo.png')).convert_alpha()
        ghost_images['pink'] = pygame.image.load(os.path.join('imagenes', 'rosa.png')).convert_alpha()
        ghost_images['orange'] = pygame.image.load(os.path.join('imagenes', 'naranja.png')).convert_alpha()

        # Escalar imágenes si es necesario (ajustar al tamaño del juego)
        for color in ghost_images:
            ghost_images[color] = pygame.transform.scale(ghost_images[color], (20, 20))

        # Crear versiones vulnerables y parpadeantes
        ghost_images['vulnerable'] = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(ghost_images['vulnerable'], vulnerable_color, [0, 0, 20, 20])

        ghost_images['blink'] = [
            ghost_images['vulnerable'],
            pygame.Surface((20, 20), pygame.SRCALPHA)
        ]
        pygame.draw.ellipse(ghost_images['blink'][1], white, [0, 0, 20, 20])

        return ghost_images
    except Exception as e:
        print(f"Error cargando imágenes de fantasmas: {e}. Usando cuadros de colores.")
        return None


ghost_images = load_ghost_images()


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.top = y
        self.rect.left = x
        self.image.fill((0, 0, 0))
        self.image.fill(blue)
        pygame.draw.rect(self.image, (0, 0, 255), self.image.get_rect(), width=4)

# Coordenadas y dimensiones de los muros en la sala (x, y, ancho, alto)
def setupRoomOne(all_sprites_list):
    wall_list = pygame.sprite.RenderPlain()
    walls = [
        [0, 0, 6, 600], [0, 0, 600, 6], [0, 600, 606, 6], [600, 0, 6, 606],
        [300, 0, 6, 66], [60, 60, 186, 6], [360, 60, 186, 6], [60, 120, 66, 6],
        [60, 120, 6, 126], [180, 120, 246, 6], [300, 120, 6, 66], [480, 120, 66, 6],
        [540, 120, 6, 126], [120, 180, 126, 6], [120, 180, 6, 126], [360, 180, 126, 6],
        [480, 180, 6, 126], [180, 240, 6, 126], [180, 360, 246, 6], [420, 240, 6, 126],
        [240, 240, 42, 6], [324, 240, 42, 6], [240, 240, 6, 66], [240, 300, 126, 6],
        [360, 240, 6, 66], [0, 300, 66, 6], [540, 300, 66, 6], [60, 360, 66, 6],
        [60, 360, 6, 186], [480, 360, 66, 6], [540, 360, 6, 186], [120, 420, 366, 6],
        [120, 420, 6, 66], [480, 420, 6, 66], [180, 480, 246, 6], [300, 480, 6, 66],
        [120, 540, 126, 6], [360, 540, 126, 6]
    ]

    for item in walls:
        wall = Wall(item[0], item[1], item[2], item[3], blue)
        wall_list.add(wall)
        all_sprites_list.add(wall)
    return wall_list


def setupGate(all_sprites_list):
    gate = pygame.sprite.RenderPlain()
    gate.add(Wall(282, 242, 42, 2, white))
    all_sprites_list.add(gate)
    return gate


class Block(pygame.sprite.Sprite):
    def __init__(self, color, width, height, is_special=False):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(black)
        self.image.set_colorkey(black)
        pygame.draw.ellipse(self.image, color, [0, 0, width, height])
        self.rect = self.image.get_rect()
        self.is_special = is_special


class Ghost(pygame.sprite.Sprite):
    def __init__(self, color, x, y):
        super().__init__()
        self.color_name = color
        self.original_color = color
        self.spawn_point = (x, y)
        self.active = True

        # Configurar imagen según si hay imágenes cargadas
        if ghost_images:
            if color == 'red':
                self.original_image = ghost_images['red']
            elif color == 'pink':
                self.original_image = ghost_images['pink']
            elif color == 'orange':
                self.original_image = ghost_images['orange']
            self.image = self.original_image.copy()
        else:
            # Modo alternativo sin imágenes
            self.original_image = pygame.Surface([20, 20])
            if color == 'red':
                self.original_image.fill((255, 0, 0))
            elif color == 'pink':
                self.original_image.fill((255, 105, 180))
            elif color == 'orange':
                self.original_image.fill((255, 165, 0))
            self.image = self.original_image.copy()

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = pygame.Vector2(2, 0)
        self.vulnerable = False
        self.vulnerable_time = 0
        self.blinking = False

    def update(self, walls, gate=None):
        if not self.active:
            return

        # Actualizar apariencia según estado
        if self.vulnerable:
            current_time = pygame.time.get_ticks()
            elapsed = (current_time - self.vulnerable_time) / 1000

            if elapsed > 7:
                self.end_vulnerability()
            elif elapsed > 4:
                self.blinking = True
                if ghost_images:
                    if int(elapsed * 5) % 2 == 0:
                        self.image = ghost_images['blink'][0]
                    else:
                        self.image = ghost_images['blink'][1]
                else:
                    if int(elapsed * 5) % 2 == 0:
                        self.image.fill(blink_colors[0])
                    else:
                        self.image.fill(blink_colors[1])
            else:
                if ghost_images:
                    self.image = ghost_images['vulnerable']
                else:
                    self.image.fill(vulnerable_color)
        else:
            if ghost_images:
                if self.color_name == 'red':
                    self.image = ghost_images['red']
                elif self.color_name == 'pink':
                    self.image = ghost_images['pink']
                elif self.color_name == 'orange':
                    self.image = ghost_images['orange']
            else:
                if self.color_name == 'red':
                    self.image.fill((255, 0, 0))
                elif self.color_name == 'pink':
                    self.image.fill((255, 105, 180))
                elif self.color_name == 'orange':
                    self.image.fill((255, 165, 0))

        # Movimiento
        old_x, old_y = self.rect.topleft
        self.rect.x += self.direction.x
        self.rect.y += self.direction.y

        hit_wall = pygame.sprite.spritecollideany(self, walls)
        if gate and pygame.sprite.spritecollideany(self, gate):
            hit_wall = True

        if hit_wall:
            self.rect.topleft = (old_x, old_y)
            self.choose_new_direction(walls)

    def make_vulnerable(self):
        self.vulnerable = True
        self.vulnerable_time = pygame.time.get_ticks()
        if ghost_images:
            self.image = ghost_images['vulnerable']
        else:
            self.image.fill(vulnerable_color)

    def end_vulnerability(self):
        self.vulnerable = False
        self.blinking = False
        if ghost_images:
            if self.color_name == 'red':
                self.image = ghost_images['red']
            elif self.color_name == 'pink':
                self.image = ghost_images['pink']
            elif self.color_name == 'orange':
                self.image = ghost_images['orange']
        else:
            if self.color_name == 'red':
                self.image.fill((255, 0, 0))
            elif self.color_name == 'pink':
                self.image.fill((255, 105, 180))
            elif self.color_name == 'orange':
                self.image.fill((255, 165, 0))

    def respawn(self):
        self.rect.center = self.spawn_point
        self.vulnerable = False
        self.blinking = False
        self.active = True
        self.end_vulnerability()

    def choose_new_direction(self, walls):
        directions = [pygame.Vector2(2, 0), pygame.Vector2(-2, 0),
                      pygame.Vector2(0, 2), pygame.Vector2(0, -2)]
        random.shuffle(directions)
        for d in directions:
            self.rect.x += d.x
            self.rect.y += d.y
            if not pygame.sprite.spritecollideany(self, walls):
                self.direction = d
                self.rect.x -= d.x
                self.rect.y -= d.y
                return
            self.rect.x -= d.x
            self.rect.y -= d.y


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.radius = 20
        self.image = pygame.Surface([self.radius * 2, self.radius * 2], pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = 'RIGHT'
        self.mouth_opening = 0
        self.mouth_opening_direction = 1
        self.change_x = 0
        self.change_y = 0
        self.update_image()

    def changespeed(self, x, y):
        self.change_x = x
        self.change_y = y
        if x > 0:
            self.direction = 'RIGHT'
        elif x < 0:
            self.direction = 'LEFT'
        elif y > 0:
            self.direction = 'DOWN'
        elif y < 0:
            self.direction = 'UP'

    def update_image(self):
        self.image.fill((0, 0, 0, 0))
        max_mouth_angle = 40
        angle = max_mouth_angle * self.mouth_opening / 10

        if self.direction == 'RIGHT':
            start_angle, end_angle = angle, 360 - angle
        elif self.direction == 'LEFT':
            start_angle, end_angle = 180 + angle, 180 - angle
        elif self.direction == 'UP':
            start_angle, end_angle = 90 + angle, 90 - angle
        else:
            start_angle, end_angle = 270 + angle, 270 - angle

        center = (self.radius, self.radius)
        points = [center]
        steps = 30

        for i in range(steps + 1):
            if start_angle < end_angle:
                current_angle = start_angle + (end_angle - start_angle) * i / steps
            else:
                current_angle = start_angle + (360 - start_angle + end_angle) * i / steps
                if current_angle > 360:
                    current_angle -= 360
            rad = math.radians(current_angle)
            x = center[0] + self.radius * math.cos(rad)
            y = center[1] - self.radius * math.sin(rad)
            points.append((x, y))

        pygame.draw.polygon(self.image, yellow, points)

    def update(self, walls, gate):
        old_x, old_y = self.rect.left, self.rect.top
        self.rect.left += self.change_x
        hit_wall = pygame.sprite.spritecollide(self, walls, False)
        if gate: hit_wall += pygame.sprite.spritecollide(self, gate, False)
        if hit_wall: self.rect.left = old_x

        self.rect.top += self.change_y
        hit_wall = pygame.sprite.spritecollide(self, walls, False)
        if gate: hit_wall += pygame.sprite.spritecollide(self, gate, False)
        if hit_wall: self.rect.top = old_y

        self.mouth_opening += self.mouth_opening_direction
        if self.mouth_opening >= 10:
            self.mouth_opening_direction = -1
        elif self.mouth_opening <= 0:
            self.mouth_opening_direction = 1
        self.update_image()


def main():
    def create_game():
        all_sprites_list = pygame.sprite.RenderPlain()
        wall_list = setupRoomOne(all_sprites_list)
        gate = setupGate(all_sprites_list)

        player = Player(300, 400)
        all_sprites_list.add(player)

        # Puntos normales (amarillos)
        pellet_list = pygame.sprite.RenderPlain()
        for row in range(15):
            for column in range(15):
                if (row, column) not in [(1, 1), (1, 13), (5, 5), (5, 9), (9, 5), (9, 9), (13, 7)]:
                    pellet = Block(yellow, 12, 12)
                    pellet.rect.centerx = (column * 40) + 20
                    pellet.rect.centery = (row * 40) + 20
                    if not any(pellet.rect.colliderect(w.rect) for w in wall_list):
                        pellet_list.add(pellet)
                        all_sprites_list.add(pellet)

        # Puntos especiales (blancos, más grandes)
        special_pellets = pygame.sprite.RenderPlain()
        special_positions = [(1, 1), (1, 13), (5, 5), (5, 9), (9, 5), (9, 9), (13, 7)]
        for row, column in special_positions:
            pellet = Block(white, 16, 16, is_special=True)
            pellet.rect.centerx = (column * 40) + 20
            pellet.rect.centery = (row * 40) + 20
            if not any(pellet.rect.colliderect(w.rect) for w in wall_list):
                special_pellets.add(pellet)
                all_sprites_list.add(pellet)

        # Fantasmas (usando imágenes si están disponibles)
        ghost_types = ['red', 'pink', 'orange']
        ghost_positions = [(150, 200), (300, 200), (450, 200)]
        ghost_list = pygame.sprite.RenderPlain()

        for ghost_type, pos in zip(ghost_types, ghost_positions):
            ghost = Ghost(ghost_type, pos[0], pos[1])
            ghost_list.add(ghost)
            all_sprites_list.add(ghost)

        return all_sprites_list, wall_list, gate, player, pellet_list, ghost_list, special_pellets

    def show_message(text):
        font = pygame.font.SysFont('Arial', 32, bold=True)  # Tamaño reducido de 48 a 32

        parts = text.split("DESDOLARIZO")
        text1 = font.render(parts[0], True, (200, 0, 0))  # rojo suave
        word = font.render("DESDOLARIZO", True, (0, 200, 0))  # verde
        text2 = font.render(parts[1], True, (200, 0, 0))  # rojo suave

        total_width = text1.get_width() + word.get_width() + text2.get_width()
        x = (606 - total_width) // 2
        y = 280  # Bajamos un poco el texto para que se vea mejor

        screen.blit(text1, (x, y))
        screen.blit(word, (x + text1.get_width(), y))
        screen.blit(text2, (x + text1.get_width() + word.get_width(), y))

    all_sprites_list, wall_list, gate, player, pellet_list, ghost_list, special_pellets = create_game()
    game_over = False
    score = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and game_over:
                    all_sprites_list, wall_list, gate, player, pellet_list, ghost_list, special_pellets = create_game()
                    game_over = False
                    score = 0
                if not game_over:
                    if event.key == pygame.K_LEFT:
                        player.changespeed(-4, 0)
                    elif event.key == pygame.K_RIGHT:
                        player.changespeed(4, 0)
                    elif event.key == pygame.K_UP:
                        player.changespeed(0, -4)
                    elif event.key == pygame.K_DOWN:
                        player.changespeed(0, 4)

            elif event.type == pygame.KEYUP and not game_over:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                    player.changespeed(0, player.change_y)
                elif event.key in [pygame.K_UP, pygame.K_DOWN]:
                    player.changespeed(player.change_x, 0)

            # Eventos de reaparición de fantasmas
            elif event.type >= pygame.USEREVENT and event.type < pygame.USEREVENT + len(ghost_list):
                ghost_index = event.type - pygame.USEREVENT
                if ghost_index < len(ghost_list.sprites()):
                    ghost_list.sprites()[ghost_index].respawn()

        if not game_over:
            player.update(wall_list, gate)
            ghost_list.update(wall_list, gate)

            # Colisión con puntos normales
            pellet_hit_list = pygame.sprite.spritecollide(player, pellet_list, True)
            for pellet in pellet_hit_list:
                score += 10

            # Colisión con puntos especiales
            special_hit_list = pygame.sprite.spritecollide(player, special_pellets, True)
            for pellet in special_hit_list:
                score += 50
                for ghost in ghost_list:
                    ghost.make_vulnerable()

            # Colisión con fantasmas
            ghost_hit_list = pygame.sprite.spritecollide(player, ghost_list, False)
            for ghost in ghost_hit_list:
                if ghost.vulnerable and ghost.active:
                    ghost.active = False
                    score += 200
                    # Reaparecer después de 5 segundos
                    pygame.time.set_timer(pygame.USEREVENT + ghost_list.sprites().index(ghost), 5000, True)
                elif not ghost.vulnerable:
                    game_over = True

        screen.fill(black)
        all_sprites_list.draw(screen)

        # Mostrar puntaje
        font = pygame.font.SysFont('Arial', 24)
        score_text = font.render(f"Puntaje: {score}", True, white)
        screen.blit(score_text, (10, 10))

        if game_over:
            show_message("JA JA TE DESDOLARIZO LUISA")

        pygame.display.flip()
        clock.tick(30)


if __name__ == '__main__':
    main()