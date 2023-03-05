
from curses import KEY_MOUSE
import pyxel
from random import randint
import time

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

def get_tile(tile_x, tile_y):
    return pyxel.tilemap(0).pget(tile_x, tile_y)

def is_colliding_with_position(x, y, w, h, positions):
    is_colliding = False
    point_x = 0
    point_y = 0
    x = pyxel.floor(x)
    y = pyxel.floor(y)
    for yi in range(y, y + h):
        for xi in range(x, x + w):
            for position in positions:
                if (xi // 8, yi // 8) == (position[0] // 8, position[1] // 8):
                    is_colliding = True
                    point_x = position[0]
                    point_y = position[1]
                    break
            
    return is_colliding, point_x, point_y

def collide(x1, x2, y1, y2, w1, w2, h1, h2):
        if x1 + w1 >= x2 and x1 <= x2 + w2 and y1 + h1 >= y2 and y1 <= y2 + h2:
            return True

# find location of tiles
def find_tile(level_x, level_y, tile_list):
    list_of_tiles = []
    for x in range(pyxel.floor(level_x * (SCREEN_WIDTH / 8)), pyxel.floor(level_x * (SCREEN_WIDTH / 8) + (SCREEN_WIDTH / 8))):
        for y in range(pyxel.floor(level_y * (SCREEN_HEIGHT / 8)), pyxel.floor(level_y * (SCREEN_HEIGHT / 8) + (SCREEN_HEIGHT / 8))):
            if get_tile(x, y) in tile_list:
                list_of_tiles.append((x * 8, y * 8))
    return(list_of_tiles)

def is_colliding_with_tile(x, y, w, h, tile_list):
    is_colliding = False
    
    x = pyxel.floor(x)
    y = pyxel.floor(y)
    for yi in range(y, y + h):
        for xi in range(x, x + w):
            if get_tile(xi // 8, yi // 8) in tile_list:
                is_colliding = True
    
    return is_colliding

class Player:
    def __init__(self, x, y):
        self.w = 8
        self.h = 8
        self.x = x
        self.y = y
        self.xv = 0
        self.yv = 0
        self.direction = 1
        self.horizontal_damping_basic = 0.6
        self.horizontal_damping_in_air = 0.9
        self.jump_power = -7
        self.is_grounded = True
        self.cut_jump_height = 0.3
        self.max_fall = 7
        self.jump_press_time = 0
        self.jump_time_to_set = 0.15
        self.grounded_remember = 0
        self.grounded_time_to_set = 0.1
        self.grounded_last_frame = True
        self.speed = 1
        self.max_speed = 7 # Don't set max_speed greater than tile width/height
        self.frame = 0
        self.max_frame = 7

        self.controls_enabled = True
        
        self.checkpoint_x = x
        self.checkpoint_y = y
        self.checkpoint_timer = 0

        self.in_lair = False
    
    def draw(self):
        pyxel.blt(self.x, self.y, 0, 0 + (self.frame * 8), 248, 8 * self.direction, 8, 14)

class Particle:
    def __init__(self):
        self.data = []
    
    def create(self, x, y, xv, yv, size, color, friction, lifespan):
        self.data.append([x, y, xv, yv, size, color, friction, lifespan])
    
    def update(self):
        index_offset = 0
        for i in range(len(particle.data)):
            # x update
            self.data[i - index_offset][2] *= self.data[i - index_offset][6]
            self.data[i - index_offset][0] += self.data[i - index_offset][2]
            
            # y update
            self.data[i - index_offset][3] *= self.data[i - index_offset][6]
            self.data[i - index_offset][1] += self.data[i - index_offset][3]

            self.data[i - index_offset][7] -= 1
            if self.data[i - index_offset][7] <= 0:
                del self.data[i - index_offset]
                index_offset += 1
    
    def draw(self):
        for i in range(len(particle.data)):    
            pyxel.circ(self.data[i][0], self.data[i][1], self.data[i][4], self.data[i][5])

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.old_x = 0
        self.old_y = 0

class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title = 'TSA_Video_Game_Design_2023', fps= 30)
        pyxel.load("TSA_Video_Game_Design_2023.pyxres")
        
        pyxel.colors.from_list([0x000000, 0x1D2B53, 0x541749, 0x008751, 0xdc6909, 0x5F574F, 0xC2C3C7, 0xFFF1E8, 0xFF004D, 0xFFA300, 0xeedb00, 0x00E436, 0x29ADFF, 0x8f8f8f, 0xFF77A8, 0xe2aa82])
        global player
        player = Player(5 * 8, 18 * 8)

        self.player_entering = False

        global particle
        particle = Particle()
        
        global camera
        camera = Camera()

        self.normal_portal_positions = []

        self.checkpoint_positions = []

        self.solid_tiles = [(1, 0), (2, 0), (3, 0), (4,0), 
                            (1, 1), (2, 1), (3, 1), (4, 1),
                            (1, 2), (2, 2), (3, 2), (4, 2),
                            (1, 3), (2, 3), (3, 3), (4, 3),
                            (1, 4), (2, 4), (3, 4), (4, 4),
                            (1, 5), (2, 5), (3, 5),
                            (1, 6), (2, 6),

                            (1, 6), (2, 6), (3, 6), (4, 6),
                            (1, 7), (4, 7),
                            (1, 8), (4, 8),
                            (1, 9), (2, 9), (3, 9), (5, 9),
        (6, 0), (6, 1), (6, 2)]
        self.harmful_tiles = [(7,0), (7, 1), (7, 2), (7, 3), (7, 4)]
        self.checkpoint_tiles = [(8, 0)]
        
        self.normal_portal_tiles = [(5, 0)]
        self.typeofportal_portal_tiles = [(5, 1)]
        self.othertypeofportal_portal_tiles = [(5, 2)]
        
        self.lair_door_tiles = [(6, 6)]

        self.up_push_tiles = [(6, 0)]
        self.left_push_tiles = [(6, 2)]
        self.right_push_tiles = [(6, 1)]
        
        self.level_x = 0
        self.level_y = 0

        self.water_list = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        self.button_frame = 0
        self.button_corners = [(239 * 8, 52 * 8)]
        self.shake = 0

        # delta time variables
        self.time_of_previous_frame = time.time()
        self.delta_time = 0
        
        self.game_fin = False

        pyxel.playm(0, True)

        pyxel.run(self.update, self.draw)

    def update(self):
            
        if not self.game_fin:
            ######### player update ###############################################################################
            
            if player.controls_enabled:
                # x movement

                if pyxel.btnp(pyxel.KEY_LEFT):
                    player.max_frame = 7
                    player.frame = 0
                    player.direction = -1
                            
                if pyxel.btnp(pyxel.KEY_RIGHT):
                    player.max_frame = 7
                    player.frame = 0
                    player.direction = 1
                
                if not player.is_grounded:
                    player.frame = 31
                    if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_RIGHT):
                        if pyxel.btnr(pyxel.KEY_LEFT):
                            player.direction = 1
                        if pyxel.btnr(pyxel.KEY_RIGHT):
                            player.direction = -1
                
                elif pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_RIGHT):
                    if pyxel.btnr(pyxel.KEY_LEFT):
                        player.direction = 1
                    if pyxel.btnr(pyxel.KEY_RIGHT):
                        player.direction = -1
                    
                    if pyxel.frame_count % 2 == 0:
                        player.frame += 1

                    if player.frame > player.max_frame:
                        player.frame = 0
                else:
                    if player.frame < 8:
                        player.frame = 8
                            
                    player.max_frame = 9
                            
                    if pyxel.frame_count % 10 == 0:
                        player.frame += 1
                            
                    if player.frame > player.max_frame:
                        player.frame = 8

                player.grounded_last_frame = player.is_grounded
                
                if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_RIGHT):
                    if player.is_grounded:
                        player.xv += player.speed * player.direction
                    else:
                        player.xv += player.speed * player.direction * 0.4
                
                if player.xv > player.max_speed:
                    player.xv = player.max_speed
                if player.xv < -1 * player.max_speed:
                    player.xv = -1 * player.max_speed
                
                # left pusher
                if is_colliding_with_tile(player.x, player.y + 8, 8, player.h, self.left_push_tiles):
                    player.xv = -10
                # right pusher
                if is_colliding_with_tile(player.x, player.y + 8, 8, player.h, self.right_push_tiles):
                    player.xv = 10

                player.x += player.xv

                if player.is_grounded:
                    player.xv *= player.horizontal_damping_basic
                else:
                    player.xv *= player.horizontal_damping_in_air
                
                if player.x < 0:
                    player.x = 0
                elif player.x > 255 * 8:
                    player.x = 255 * 8
                
                # x collisions #
                if player.xv < 0:   
                    # left
                    if is_colliding_with_tile(player.x, player.y, 1, player.h, self.solid_tiles):
                        player.x = pyxel.floor((player.x + 7) / 8 ) * 8
                        player.xv = 0

                elif player.xv > 0:    
                    # right
                    if is_colliding_with_tile(player.x + 7, player.y, 1, player.h, self.solid_tiles):
                        player.x = pyxel.floor((player.x) / 8 ) * 8
                        player.xv = 0

                # y movement
                
                player.yv = min(player.yv + 1, player.max_fall)

                # delta time calculator
                time_of_current_frame = time.time()
                self.delta_time = time_of_current_frame - self.time_of_previous_frame
                self.time_of_previous_frame = time_of_current_frame

                # remembers when the jump button was last pressed
                player.jump_press_time -= self.delta_time
                if pyxel.btnp(pyxel.KEY_UP):
                    player.jump_press_time = player.jump_time_to_set

                # remembers when the player was grounded
                player.grounded_remember -= self.delta_time
                if player.is_grounded:
                    player.grounded_remember = player.grounded_time_to_set
                
                # jumps
                if player.jump_press_time > 0  and player.grounded_remember > 0:
                    player.jump_press_time = 0
                    player.yv = player.jump_power
                    player.grounded_remember = 0
                    player.is_grounded = False
                    player.frame = 31
                    # play jump sound
                    pyxel.play(3, 63)
                    # make dust particles
                    for i in range(5):
                        particle.create(player.x + 4 + randint(-4, 4), player.y + 8, randint(-2, 2), randint(-2, 0) / 2, 1, 7, 0.9, randint(6, 10))

                # # controls height of jump
                if pyxel.btnr(pyxel.KEY_UP):
                    if player.yv < 0:
                        player.yv *= player.cut_jump_height

                player.y += pyxel.floor(player.yv)
                
                if player.yv >= 2:
                    player.is_grounded = False

                if player.y < 0:
                    player.y = 0
                elif player.y > 255 * 8:
                    player.y = 255 * 8
                
                if player.yv > 0:
                    # bottom
                    while is_colliding_with_tile(player.x, player.y + 7, player.w, 1, self.solid_tiles):
                        player.y -= 1
                        player.yv = 0
                        player.is_grounded = True

                elif player.yv < 0:
                    # top
                    while is_colliding_with_tile(player.x, player.y, player.w, 1, self.solid_tiles):
                        player.y += 1
                        player.yv = 0
                
                # up_pusher
                if is_colliding_with_tile(player.x, player.y + 8, player.w, 1, self.up_push_tiles):
                    player.yv = -12
                
                if not player.is_grounded:
                    player.frame = 31
                
                # Harm detection
                
                if is_colliding_with_tile(player.x, player.y, player.w, player.h, self.harmful_tiles):
                    player.xv = 0
                    player.yv = 0

                    # play death sound
                    pyxel.play(3, 60)

                    particle.create(player.x + 4, player.y + 4, 0, -3, 2, 8, 0.9, 10)
                    particle.create(player.x + 4, player.y + 4, 3, -3, 2, 8, 0.9, 10)
                    particle.create(player.x + 4, player.y + 4, 3, 0, 2, 8, 0.9, 10)
                    particle.create(player.x + 4, player.y + 4, 3, 3, 2, 8, 0.9, 10)
                    particle.create(player.x + 4, player.y + 4, 0, 3, 2, 8, 0.9, 10)
                    particle.create(player.x + 4, player.y + 4, -3, 3, 2, 8, 0.9, 10)
                    particle.create(player.x + 4, player.y + 4, -3, 0, 2, 8, 0.9, 10)
                    particle.create(player.x + 4, player.y + 4, -3, -3, 2, 8, 0.9, 10)

                    player.x = player.checkpoint_x
                    player.y = player.checkpoint_y 
                    if not pyxel.btn(pyxel.KEY_LEFT):
                        player.direction = 1
                    player.frame = 1

                    if is_colliding_with_tile(player.checkpoint_x, player.checkpoint_y + 8, 8, 1, self.solid_tiles):
                        player.grounded_last_frame = True
                        player.is_grounded = True
                    else:
                        player.is_grounded = False
                        player.grounded_last_frame = False
                        
                    player.grounded_remember = 0
                    player.jump_press_time = 0
                    player.checkpoint_timer = 15
                
                # checkpoint 
                
                self.checkpoint_positions = find_tile(self.level_x, self.level_y, self.checkpoint_tiles)
                
                is_colliding_with_checkpoint, point_x, point_y = is_colliding_with_position(player.x, player.y, player.w, player.h, self.checkpoint_positions)
                if is_colliding_with_checkpoint:
                    player.checkpoint_x = point_x
                    player.checkpoint_y = point_y
                
                ######### portal code #######################################################################
                self.normal_portal_positions = find_tile(self.level_x, self.level_y, self.normal_portal_tiles)
                if self.normal_portal_positions:
                    self.normal_portal_x = self.normal_portal_positions[0][0]
                    self.normal_portal_y = self.normal_portal_positions[0][1]

                    if pyxel.btnp(pyxel.KEY_Z):
                        particle.create(player.x + 4, player.y + 4, 0, -3, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, 3, -3, 1, 0, 0.8, 10)
                        particle.create(player.x + 4, player.y + 4, 3, 0, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, 3, 3, 1, 0, 0.8, 10)
                        particle.create(player.x + 4, player.y + 4, 0, 3, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, -3, 3, 1, 0, 0.8, 10)
                        particle.create(player.x + 4, player.y + 4, -3, 0, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, -3, -3, 1, 0, 0.8, 10)
                        
                        player.x = self.normal_portal_x
                        player.y = self.normal_portal_y

                        particle.create(player.x + 4, player.y + 4, 0, -3, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, 3, -3, 1, 0, 0.8, 10)
                        particle.create(player.x + 4, player.y + 4, 3, 0, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, 3, 3, 1, 0, 0.8, 10)
                        particle.create(player.x + 4, player.y + 4, 0, 3, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, -3, 3, 1, 0, 0.8, 10)
                        particle.create(player.x + 4, player.y + 4, -3, 0, 1, 0, 0.9, 10)
                        particle.create(player.x + 4, player.y + 4, -3, -3, 1, 0, 0.8, 10)

                        # play portal sound
                        pyxel.play(3, 61)

                        if is_colliding_with_tile(self.normal_portal_x, self.normal_portal_y + 8, 8, 1, self.solid_tiles):
                            player.grounded_last_frame = True
                            player.is_grounded = True
                        else:
                            player.is_grounded = False
                            player.grounded_last_frame = False

                        player.grounded_remember = 0
                        player.jump_press_time = 0
                
                # door to lair
                if is_colliding_with_tile(player.x, player.y, player.w, player.h, self.lair_door_tiles):
                    player.controls_enabled = False
                    self.player_entering = True
                    player.frame = 26
                
                # squish looks better at the end like this

                if player.grounded_last_frame == False and player.is_grounded == True:
                    player.frame = 30
                    # play hit ground sound
                    pyxel.play(3, 62)
                    # make dust particles
                    for i in range(5):
                        particle.create(player.x + 4 + randint(-4, 4), player.y + 8, randint(-2, 2), randint(-2, 0) / 2, 1, 7, 0.9, randint(6, 10))
                
                # CHEEEEEEEAAAATTT
                # if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
                #     player.x = pyxel.mouse_x + self.level_x * 256
                #     player.y = pyxel.mouse_y + self.level_y * 256
            
            ######### player entering animation #############################################################
            if self.player_entering:
                player.x = 241 * 8
                player.y = 19 * 8
                if pyxel.frame_count % 10 == 0:
                    player.frame += 1
                
                if player.frame >= 30:
                    player.x = 10 * 8
                    player.y = 47 * 8
                    self.player_entering = False
                    player.controls_enabled = True
                    player.xv = 0
                    player.yv = 0
                    player.in_lair = True
                    self.level_x = 0
                    self.level_y = 1
                    pyxel.stop()
                    pyxel.playm(2, True)

            ######### portal particle update #######################################################################
            
            if self.normal_portal_positions:
                particle.create(self.normal_portal_x + 4, self.normal_portal_y + 4, randint(-3, 3), randint(-3, 3), 2, 0, 0.7, 10)
            
            ######### particle update #####################################################################
            particle.update()
            
            ######### camera update ###############################################################################
            
            camera.old_x = camera.x
            camera.old_y = camera.y
            
            camera.x = pyxel.floor((player.x + 4) / SCREEN_WIDTH) * SCREEN_WIDTH
            camera.y = pyxel.floor((player.y + 4) / SCREEN_HEIGHT) * SCREEN_HEIGHT

            # if camera.x > camera.old_x:
            #     self.level_x += 1
            # elif camera.x < camera.old_x:
            #     self.level_x -= 1
            
            # if camera.y > camera.old_y:
            #     self.level_y += 1
            # elif camera.y < camera.old_y:
            #     self.level_y -= 1

            self.level_x = int(camera.x / 256)
            self.level_y = int(camera.y / 256)
            
            if camera.x != camera.old_x or camera.y > camera.old_y:
                player.grounded_remember = 0

            ########## water update ##############################################################

            for i in range(len(self.water_list)):
                self.water_list[i] = (pyxel.sin(((pyxel.frame_count) + i) * 4) * 3)
            
            ########## button update ####################################################################

            if collide(player.x, self.button_corners[0][0], player.y, self.button_corners[0][1], player.w,  16, player.h, 16) and self.shake == 0:
                self.button_frame = 1
                self.shake = 60
                pyxel.stop()
                pyxel.play(0, 59)
            
            if self.shake > 0:
                if pyxel.frame_count % 4 == 0:
                    camera.x += 1
                if pyxel.frame_count % 4 == 1:
                    camera.y += 1
                    camera.x += 1
                if pyxel.frame_count % 4 == 2:
                    camera.y += 1
                
                self.shake -= 1

                if self.shake == 0:
                    pyxel.stop()
                    pyxel.playm(1, True)
                    self.game_fin = True


    def draw(self):

        if self.game_fin:
            pyxel.camera(0, 0)
            
            pyxel.colors.from_list([0x000000, 0x1D2B53, 0x541749, 0x008751, 0xdc6909, 0x5F574F, 0xC2C3C7, 0xFFF1E8, 0xFF004D, 0xFFA300, 0xeedb00, 0x00E436, 0x29ADFF, 0x8f8f8f, 0xFF77A8, 0xe2aa82])
            pyxel.cls(7)

            pyxel.text(40, 64, "YOU SUCCESSFULLY SHUT DOWN THE DOOMSDAY MACHINE.", 0)
            pyxel.text(40, 74, "THANKS FOR PLAYING!", 0)


        else:    
            if player.in_lair:
                if pyxel.frame_count % 30 > 10:
                    pyxel.colors.from_list([0x000000, 0x1D2B53, 0x541749, 0x008751, 0xdc6909, 0x5F574F, 0xC2C3C7, 0xFFF1E8, 0xFF004D, 0xFFA300, 0xeedb00, 0x00E436, 0x29ADFF, 0x8f8f8f, 0xFF77A8, 0xe2aa82])
                if pyxel.frame_count % 30 <= 10:
                    pyxel.colors.from_list([0x000000, 0x3b2b53, 0x721749, 0x1e8751, 0xfa6809, 0x7d574f, 0xe0aaaa, 0xffd3ca, 0xff0019, 0xff8c00, 0xffcc00, 0x1ee435, 0x47acff, 0xad8f8f, 0xff6495, 0xffa47d])
                if pyxel.frame_count % 30 <= 7:
                    pyxel.colors.from_list([0x000000, 0x6d2b53, 0xa41748, 0x508751, 0xff5000, 0xaf574f, 0xff9696, 0xffb4aa, 0xff0000, 0xff6600, 0xff9600, 0x64c819, 0x78acff, 0xdc8f8f, 0xff466e, 0xff875f])
                if pyxel.frame_count % 30 <= 3:
                    pyxel.colors.from_list([0x000000, 0x3b2b53, 0x721749, 0x1e8751, 0xfa6809, 0x7d574f, 0xe0aaaa, 0xffd3ca, 0xff0019, 0xff8c00, 0xffcc00, 0x1ee435, 0x47acff, 0xad8f8f, 0xff6495, 0xffa47d])
            
            if player.in_lair:    
                pyxel.cls(6)
            else:
                pyxel.cls(12)

                # Draw Background
                # clouds
                pyxel.bltm(((pyxel.frame_count / 8) % 256) + camera.x, 0, 0, 0, 240*8, 256, 128, 14)
                pyxel.bltm((((pyxel.frame_count / 8) % 256) - 257) + camera.x, 0, 0, 0, 240*8, 256, 128, 14)

            # Draw level
            pyxel.bltm(0, 0, 0, 0, 0, SCREEN_WIDTH * 8, SCREEN_HEIGHT * 8, 14)
            
            pyxel.camera(camera.x, camera.y)
            
            # Draw Characters
            player.draw()
            
            # Draw Water
            if not player.in_lair:
                for i in range(len(self.water_list)):
                    pyxel.blt((0 + (i * 16) + camera.x), 244 + self.water_list[i], 0, 0, 224, 16, 24, 14)

            # Button Draw
            pyxel.blt(239 * 8, 52 * 8, 0, 40 + self.button_frame * 16, 64, 16, 16, 14)

            particle.draw()
            
            
            if self.level_y == 0:
                if self.level_x == 0:
                    pyxel.text(120 + self.level_x * 256, 200 + self.level_y * 256, "PRESS Z TO TELEPORT", 0)
                elif self.level_x == 1:
                    pyxel.text(20 + self.level_x * 256, 64 + self.level_y * 256, "GREEN CUBE = CHECKPOINT", 0)
                    pyxel.text(170 + self.level_x * 256, 200 + self.level_y * 256, "JUMP + TELEPORT", 0)
                elif self.level_x == 2:
                    pyxel.text(20 + self.level_x * 256, 64 + self.level_y * 256, "VELOCITY IS CONSERVED", 0)
            

App()
