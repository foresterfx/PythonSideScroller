import pygame
import os
import random
import csv
from button import button

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Game')

# framerate limit
clock = pygame.time.Clock()
FPS = 60

# game variables
GRAVITY = 0.4
SCALE = 2
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
SCROLL_THRESHOLD = 200
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False


#load images
pine1 = pygame.image.load('imgs/background/pine1.png')
pine2 = pygame.image.load('imgs/background/pine2.png')
mountain = pygame.image.load('imgs/background/mountain.png')
sky_cloud = pygame.image.load('imgs/background/sky_cloud.png')
#button images
start_img = pygame.image.load('imgs/start_btn.png').convert_alpha()
exit_img = pygame.image.load('imgs/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('imgs/restart_btn.png').convert_alpha()

#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'imgs/tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)
health_box_img = pygame.image.load('imgs/icons/health_box.png').convert_alpha()

item_boxes = {
	'Health'	: health_box_img
}

# define colors
BG = (125,125,125)
GRASS = (0,173,0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

FLOOR = 400

# defining player action variables
moving_left = False
moving_right = False

def draw_bg():
    screen.fill(BG)
    width = sky_cloud.get_width() # sky is shortest
    for x in range(10): # loop background
        screen.blit(sky_cloud,((x * width) - bg_scroll * .2, 0))
        screen.blit(mountain, ((x * width) - bg_scroll * .6 ,SCREEN_HEIGHT - mountain.get_height() - 300))
        screen.blit(pine1, ((x * width) - bg_scroll * .8 , SCREEN_HEIGHT - pine1.get_height() - 150))
        screen.blit(pine2, ((x * width) - bg_scroll * .9, SCREEN_HEIGHT - pine2.get_height()))
#function to reset level
def reset_level():
    enemy_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data

class Character(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, hp):
        pygame.sprite.Sprite.__init__(self)
        # all sprite variables
        self.alive = True
        self.hit = False
        self.char_type = char_type
        self.speed = speed
        self.hp = hp
        self.max_hp = hp
        self.direction = 1
        self.y_velocity = 0
        self.attack = False
        self.jump = False
        self.crouch = False
        self.slide = False
        self.in_air = True
        self.flip = False
        # animation list and index
        self.anime_list = []
        self.frame = 0
        self.action = 0
        # enemy ai variables
        self.move_counter = 0
        self.attack_cd = 0
        self.vision = pygame.Rect(0, 0, 20, 20)
        self.idling = 0
        self.idling_counter = 0
        self.update_time = pygame.time.get_ticks()

        # load all character animations
        # index number correlates to action number
        if char_type == "player":
            anime_types = ['idle', 'move', 'die', 'hit', 'attack', 'jump', 'slide', 'crouch']
        else:
            anime_types = ['idle', 'move', 'die', 'hit', 'attack']
        for animation in anime_types:
            # reset temporary animation list
            temp_list = []
            # animation
            anime_count = len(os.listdir(f'imgs/{self.char_type}/{animation}'))
            for i in range(anime_count):
                img = pygame.image.load(f'imgs/{self.char_type}/{animation}/{i}.png')
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.anime_list.append(temp_list)

        self.image = self.anime_list[self.action][self.frame]

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        '''
        updates sprite animations
        '''
        self.check_alive()
        self.update_anime()
        # update cooldown for attacking
        if self.attack_cd > 0:
            self.attack_cd -= 1

    def check_alive(self):
        '''
        checks if sprite is alive
        '''
        if self.hp <= 0:
            self.hp = 0
            self.speed = 0
            self.alive = False
            self.update_action(2)

    def move(self, moving_left, moving_right):
        '''
        Controls and moves character sprites along with collisions
        '''
        # reset movement variables (delta x/y)
        screen_scroll = 0
        dx = 0
        dy = 0
        # assign left/right movement variables
        if moving_left:
            dx = -self.speed
            if self.char_type == 'enemy/slime':
                self.flip = False
            else:
                self.flip = True
            self.direction = -1

        if moving_right:
            dx = self.speed
            if self.char_type == 'enemy/slime':
                # slime sprites are mirrored from others
                self.flip = True
            else:
                self.flip = False
            self.direction = 1

        # jumping and prevents multi-jumping
        if self.jump and not self.in_air:
            self.y_velocity = -11
            self.jump = False
            self.in_air = True

        # gravity
        self.y_velocity += GRAVITY
        if self.y_velocity > 10:
            self.y_velocity = 10
        # increase dy position by jump
        dy += self.y_velocity

        # check for collision
        for tile in world.obstacle_list:
            # check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
            # check for collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # check if below the ground, i.e. jumping
                if self.y_velocity < 0:
                    self.y_velocity = 0
                    dy = tile[1].bottom - self.rect.top
                # check if above the ground, i.e. falling
                elif self.y_velocity >= 0:
                    self.y_velocity = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
        # check if going off the edges of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0
        # check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True
        # check if fallen off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.hp = 0
        # check for collision with water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.hp = 0
        # update sprite position
        self.rect.x += dx
        self.rect.y += dy

        # background scrolling based on player movement
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESHOLD and bg_scroll < (
                    world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESHOLD and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        return screen_scroll, level_complete

    def draw(self):
        """
        Character Drawing on Screen
        """
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


    def update_anime(self):
        '''
        Sprite updater with animation timer
        '''
        ANIMATION_COOLDOWN = 200
        # update image for frame
        self.image = self.anime_list[self.action][self.frame]
        # check if time to update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame += 1
            # prevents sprite from looping hit/attack animation
            if (self.action == 4 or self.action == 3) and self.frame == len(self.anime_list[self.action]):
                self.action = 0
                self.frame = 0
                self.attack = False
                self.hit = False
                return
        # loop animation
        if self.frame >= len(self.anime_list[self.action]):
            if self.action == 2 or self.slide:
                # prevents player from sliding forever or looping death
                self.frame = len(self.anime_list[self.action]) - 1
                self.slide = False
            else:
                self.frame = 0


    def update_action(self, new_action):
        '''
        Check if action is new or same
        '''
        if new_action != self.action:
            self.action = new_action
            # update the animation settings
            self.frame = 0
            self.update_time = pygame.time.get_ticks()

    def ai(self):
        '''
        AI for NPC sprites
        '''
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)  # 0: idle
                self.idling = True
                self.idling_counter = 50
            # check if ncp near player
            if self.vision.colliderect(player.rect):
                # face player
                if self.direction != player.direction * -1:
                    self.direction *= -1
                # attack player
                self.char_hit()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)  # 1: run
                    self.move_counter += 1
                    # update ai vision as the enemy moves
                    self.vision.center = (self.rect.centerx * self.direction, self.rect.centery)
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        #scroll characters
        self.rect.x += screen_scroll

    def char_hit(self):
        '''
        All sprite hit opportunities
        '''
        # stop attacking if player is dead
        if player.alive == False:
            return
        # enemy attacking logic
        for enemy in enemy_group:
            if self == enemy and enemy.attack_cd == 0:
                if pygame.sprite.collide_rect(enemy, player) and enemy.alive:
                    if player.hit == False and enemy.attack == False:
                        enemy.update_action(4)
                        enemy.attack = True
                        player.hit = True
                        enemy.attack_cd = 100
                        if self.char_type == 'enemy/slime':
                            player.hp -= 50
                        else:
                            player.hp -= 150
                        enemy.update()
                enemy.attack = False
                enemy.hit = False
                enemy.update()
            # player attacking logic
            if self == player:
                player.attack_cd = 100
                if pygame.sprite.collide_rect(player, enemy):
                    if enemy.hit == False and player.attack:
                        enemy.hit = True
                        enemy.hp -= 10
                if player.attack_cd == 0:
                    player.attack = False


class HealthBar():
    '''
    Player health bar
    '''
    def __init__(self, x, y, hp, max_hp):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = max_hp

    def draw(self, hp):
        #update with new health
        self.hp = hp
        #calculate health ratio
        ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class World():
    '''
    Overworld Creation imported from CSV's -> tiles dictated by CSV value
    '''
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        # iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    # dirt blocks -> add to obstacle list
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:  # create player
                        player = Character('player', x * TILE_SIZE, y * TILE_SIZE, SCALE/1.5, 5, 2000)
                        health_bar = HealthBar(10, 10, player.max_hp, player.hp)
                    elif tile == 16:  # create enemies
                        enemy = Character('enemy/slime', x * TILE_SIZE, y * TILE_SIZE/2, SCALE/2, 2, 1000)
                        enemy_group.add(enemy)
                    elif tile == 17:  # create enemy Knight
                        enemy = Character('enemy/knight', x * TILE_SIZE - 3, y * TILE_SIZE / 2, SCALE / 2, 2, 2000)
                        enemy_group.add(enemy)
                    elif tile == 18:  # create another tile
                        enemy = Character('enemy/shade', x * TILE_SIZE - 9, y * TILE_SIZE / 2, SCALE/3, 2, 2000)
                        enemy_group.add(enemy)
                    elif tile == 19:  # create health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:  # create exit
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])

class Exit(pygame.sprite.Sprite):
    '''
    Exit Sign sprites -> transition to next level
    '''
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class ItemBox(pygame.sprite.Sprite):
    '''
    ItemBox sprites -> included for world-filling material
    '''
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll
        #check if the player has picked up the box
        if pygame.sprite.collide_rect(self, player):
            #check what kind of box it was
            if self.item_type == 'Health':
                player.hp += 150
                if player.hp > player.max_hp:
                    player.hp = player.max_hp
            #delete the item box
            self.kill()

class Decoration(pygame.sprite.Sprite):
    '''
    Create sprites for decorations -> grass, rocks, etc.
    '''
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    '''
    Create sprites for water
    '''
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class ScreenFade():
    '''
    Level Screen Fading Transition
    '''
    def __init__(self, direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0


    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1: # whole screen fade
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT // 2 +self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2: # vertical screen fade down
            pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True

        return fade_complete

#create screen fades
intro_fade = ScreenFade(1, BLACK, 6)
death_fade = ScreenFade(2, RED, 6)
# create menu buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

# create sprite groups
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


#create empty tile list
world_data = []
for row in range(ROWS):
	r = [-1] * COLS
	world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)


run = True
while run:
    clock.tick(FPS)
    if start_game == False:
        # draw menu
        screen.fill(BG)
        # add buttons
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            run = False
    else:
        # draw background
        draw_bg()
        # draw world
        world.draw()
        # player health
        health_bar.draw(player.hp)
        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()
            # ['idle', 'move', 'die', 'hit', 'attack']
            if enemy.alive:
                if enemy.hit:
                    enemy.update_action(3)
                    enemy.hit = False

        # update and draw sprite groups
        decoration_group.update()
        water_group.update()
        exit_group.update()
        item_box_group.update()

        decoration_group.draw(screen)
        item_box_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        # show intro
        if start_intro == True:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0

    # update player action while player is alive
    # anime_types = ['idle', 'move', 'die', 'hit', 'attack' 'jump', 'slide', 'crouch']
    if player.alive:
        if player.crouch:
            player.update_action(7) # crouching
        elif player.slide:
            player.update_action(6) # sliding
        elif player.in_air:
            player.update_action(5) # jumping
        elif player.attack:
            player.update_action(4)
            player.char_hit() # attacking
        elif player.hit:
            player.update_action(3) # hit by enemy
        elif moving_left or moving_right:
            player.update_action(1) # running
        else:
            player.update_action(0) # idle
        screen_scroll, level_complete = player.move(moving_left, moving_right)
        bg_scroll -= screen_scroll
        # if level completed -> jump to next level
        if level_complete:
            start_intro = True
            level += 1
            bg_scroll = 0
            world_data = reset_level()
            if level <= MAX_LEVELS:
                # load in level data and create world
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)
    # if player dies -> show restart button
    elif not player.alive:
        player.update_action(2) # dies
        if death_fade.fade():
            if restart_button.draw(screen):
                death_fade.fade_counter = 0
                start_intro = True
                screen_scroll = 0
                bg_scroll = 0
                world_data = reset_level()
                # load in level data and create world
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)

    # keymapping
    for event in pygame.event.get():
        # quits game
        if event.type == pygame.QUIT:
            run = False
        # key pressed
        if event.type == pygame.KEYDOWN:
            # move left
            if event.key == pygame.K_a:
                moving_left = True
                player.crouch = False
                player.attack = False
            # move right
            if event.key == pygame.K_d:
                moving_right = True
                player.crouch = False
                player.attack = False
            # jumping
            if event.key == pygame.K_w:
                player.jump = True
            # sliding and crouching
            if event.key == pygame.K_s:
                if moving_right or moving_left:
                    player.slide = True
                else:
                    player.crouch = True
                    player.slide = False
            # attacking
            if event.key == pygame.K_SPACE:
                moving_left = False
                moving_right = False
                player.slide = False
                player.attack = True
            # escape exits game
            if event.key == pygame.K_ESCAPE:
                run = False
        # key released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_s:
                player.crouch = False
                player.slide = False
            # if event.key == pygame.K_SPACE:
            #     player.attack = False
            # breaks animation logic, placed elsewhere
    pygame.display.update()
pygame.quit()