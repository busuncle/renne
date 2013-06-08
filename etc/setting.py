import os
from base import constant as cfg
import pygame
from pygame.locals import *

pygame.init()

FPS = 60
DEBUG_MODE = False



class Font(object):
    ARIAL_FILEPATH = os.path.join("res", "font",  "arial.ttf")
    ARIAL_BOLD_FILEPATH = os.path.join("res", "font", "arial_bold.ttf")
    ARIAL_BLACK_FILEPATH = os.path.join("res", "font", "arial_black.ttf")
    HOLLOW_FILEPATH = os.path.join("res", "font", "hollow.ttf")

    ARIAL_16 = pygame.font.Font(ARIAL_FILEPATH, 16)
    ARIAL_32 = pygame.font.Font(ARIAL_FILEPATH, 32)

    ARIAL_BOLD_12 = pygame.font.Font(ARIAL_BOLD_FILEPATH, 12)
    ARIAL_BOLD_16 = pygame.font.Font(ARIAL_BOLD_FILEPATH, 16)
    ARIAL_BOLD_32 = pygame.font.Font(ARIAL_BOLD_FILEPATH, 32)

    ARIAL_BLACK_16 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 16)
    ARIAL_BLACK_24 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 24)
    ARIAL_BLACK_28 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 28)
    ARIAL_BLACK_32 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 32)
    ARIAL_BLACK_48 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 48)

    HOLLOW_16 = pygame.font.Font(HOLLOW_FILEPATH, 16)
    HOLLOW_32 = pygame.font.Font(HOLLOW_FILEPATH, 32)
    HOLLOW_48 = pygame.font.Font(HOLLOW_FILEPATH, 48)



class Menu(object):
    RENNE_CURSOR_IMAGE_KEY = "head_status"
    RENNE_CURSOR_RECT = (224, 64, 32, 32)
    PAUSE = {
        "options": ["CONTINUE", "MAIN", "QUIT"],
        "option_rect": (0, 0, 224, 32),
        "blit_y": 320,
        "font_on": Font.ARIAL_BLACK_32,
        "font_off": Font.ARIAL_BLACK_28,
        "color_on": pygame.Color("white"),
        "color_off": pygame.Color("gray"),
    }

    START_GAME = {
        "options": ["START", "QUIT"],
        "option_rect": (0, 0, 256, 48),
        "blit_y": 540,
        "font_on": Font.ARIAL_BLACK_48,
        "font_off": Font.ARIAL_BLACK_32,
        "color_on": pygame.Color("white"),
        "color_off": pygame.Color("gray"),
    }



class UserKey(object):
    UP = K_w
    DOWN = K_s
    LEFT = K_a
    RIGHT = K_d
    ATTACK = K_j
    ATTACK_DESTROY_FIRE = K_u
    ATTACK_DESTROY_BOMB = K_i
    ATTACK_DESTROY_AEROLITE = K_o
    REST = K_k
    WIN = K_h

    DIRECTION_KEYS = (UP, DOWN, LEFT, RIGHT)
    # double press some direction key to run, this is the threshold between 2 presses
    RUN_THRESHOLD = 0.2



class Screen(object):
    SIZE = [1024, 768]
    INNER_SIZE = [SIZE[0] / 4, SIZE[1] / 4]
    DEFAULT_SCREEN = pygame.display.set_mode(SIZE, HWSURFACE|DOUBLEBUF)
    DEFAULT_SURFACE = pygame.Surface(SIZE).convert_alpha()



class Stuff(object):
    # some common stuff, may be used everywhere if needed
    MASK_ALPHA_128 = pygame.Color(0, 0, 0, 128)



class Sprite(object):
    SHADOW_IMAGE_KEY = "sprite_shadow"
    UNDER_ATTACK_MIX_COLOR = pygame.Color("gray")
    UNDER_ATTACK_EFFECT_TIME = 0.05
    RECOVER_HP_MIX_COLOR = pygame.Color("gray")
    RECOVER_HP_EFFECT_TIME = 0.08



class Renne(object):
    NAME = "Renne"
    ROLE = cfg.SpriteRole.HERO
    HP = 300
    MP = 200
    MP_RECOVERY_RATE = 10
    SP = 180
    SP_COST_RATE = 15
    SP_RECOVERY_RATE = 20
    ATK = 30
    DFS = 2

    # sprite radius
    RADIUS = 18 
    HEIGHT = 60
    # distance from coord to sprite foot
    POS_RECT_DELTA_Y = 40

    SHADOW_RECT_DELTA_Y = 50
    SHADOW_INDEX = 1

    # move speed, in pixel unit
    WALK_SPEED = 100
    RUN_SPEED = 200

    ATTACKER_PARAMS = {
        "range": 100,
        "angle": 120,
        "key_frames": (4, 5),
        "run_attack": {
            "crick_time": 0.4,
            "out_speed": 1000,
            "acceleration": -4500,
        },
        "destroy_fire": {
            "range": 300,
            "damage": 40,
            "speed": 250,
            "radius": 18,
            "crick_time": 0.3,
            "dx": 32,
            "dy": 48,
            "mana": 30,
            "cd": 3,
        },
        "destroy_bomb": {
            "range": 360,
            "damage": 60,
            "speed": 280,
            "mana": 60,
            "cd": 5,
            "bomb_radius": 18,
            "dx": 32,
            "dy": 52,
            "bombs_direct_num": 5,
            "bomb_shake_on_x": 10,
            "bomb_shake_on_y": 10,
            "bomb_life": 0.4,
            "bomb_ranges": range(50, 360, 25),
        },
        "destroy_aerolite": {
            "key_frames": (1, ),
            "fall_range": 128,
            "damage": 70,
            "acceleration": 400,
            "mana": 80,
            "cd": 10,
            #"mana": 6,
            "dx": 32,
            "dy": 240,
            "trigger_times": (0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2),
            #"trigger_times": (0.2, ),
            "aerolite_radius": 18,
            "aerolite_damage_cal_time": 0.4,
            "aerolite_life": 1.5,
            "aerolite_shake_on_x": 150,
            "aerolite_shake_on_y": 150,
            "stun_time": 5,
        },
        "dizzy": {
            "prob": 0.25,
            "range": 700,
            "cd": 30,
            "time": 15,
            "effective_time": 2,
            "key_frames": (5, 6),
        },
    }


                
class Enemy(object):
    ROLE = cfg.SpriteRole.ENEMY
    DEAD_TICK = 1.5
    DEAD_BLINK_TIMES = 3
    VIEW_RANGE = 480
    VIEW_ANGLE = 160 
    NEARBY_ALLIANCE_RANGE = 300



class SkeletonWarrior(Enemy):
    NAME = "SkeletonWarrior"
    HP = 300
    ATK = 35
    DFS = 2

    RADIUS = 24
    HEIGHT = 80
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 60,
        "angle": 90,
        "key_frames": (3, 4),
    }

    WALK_SPEED = 110



class CastleWarrior(Enemy):
    NAME = "CastleWarrior" 
    HP = 550
    ATK = 45
    DFS = 4

    RADIUS = 24
    HEIGHT = 82
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 90,
        "angle": 60,
        "key_frames": (3, 4),
        "thump_prob": 0.4,
        "thump_crick_time": 0.3,
        "thump_out_speed": 1000,
        "thump_acceleration": -4500,
    }

    WALK_SPEED = 100



class SkeletonArcher(Enemy):
    NAME = "SkeletonArcher"
    HP = 300
    ATK = 35
    DFS = 2

    RADIUS = 24
    HEIGHT = 65
    POS_RECT_DELTA_Y = 35
    SHADOW_RECT_DELTA_Y = 55
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 400,
        "angle": 6,
        "key_frames": (4, 5),
        "arrow_radius": 18, 
        "arrow_speed": 300, 
        "arrow_dx": 32,
        "arrow_dy": 50,
        "arrow_damage": 35,
    }

    WALK_SPEED = 105



class LeonHardt(Enemy):
    # override some attribute
    VIEW_RANGE = 520
    VIEW_ANGLE = 180

    IS_BOSS = True
    NAME = "LeonHardt"
    HP = 2000
    MP = 1000
    ATK = 60
    DFS = 5
    MP_RECOVERY_RATE = 10

    RADIUS = 24
    HEIGHT = 80
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 2

    ATTACKER_PARAMS = {
        "range": 70,
        "angle": 60,
        "key_frames": (4, 5),
        "death_coil": {
            "key_frames": (1, ),
            "range": 300,
            "damage": 60,
            "speed": 250,
            "radius": 15,
            "dx": 32,
            "dy": 64,
            "mana": 80,
        },
        "hell_claw": {
            "range": 300,
            "damage": 80,
            "claw_radius": 18,
            "dx": 32, 
            "dy": 64,
            "trigger_times": (0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6),
            "claw_damage_cal_time": 0.2,
            "claw_life": 0.6,
            "claw_shake_on_x": 120,
            "claw_shake_on_y": 120,
            "mana": 120,
        }
    }

    RUN_SPEED = 200



class ArmouredShooter(Enemy):
    NAME = "ArmouredShooter"
    HP = 400
    ATK = 38
    DFS = 4

    # overwrite
    VIEW_RANGE = 500
    VIEW_ANGLE = 180 

    RADIUS = 24
    HEIGHT = 70
    POS_RECT_DELTA_Y = 35
    SHADOW_RECT_DELTA_Y = 55
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 420,
        "angle": 12,
        "key_frames": (5, 6),
    }

    WALK_SPEED = 150



class SwordRobber(Enemy):
    NAME = "SwordRobber"
    HP = 500
    ATK = 45
    DFS = 4

    RADIUS = 24
    HEIGHT = 75
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 90,
        "angle": 60,
        "key_frames": (3, 4),
        "weak_prob": 0.6,
        "weak_time": 6,
        "weak_atk": 15,
        "weak_dfs": 5,
    }

    WALK_SPEED = 165



class SkeletonWarrior2(Enemy):
    NAME = "SkeletonWarrior2"
    HP = 350
    ATK = 30
    DFS = 2

    RADIUS = 24
    HEIGHT = 75
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 60,
        "angle": 90,
        "key_frames": (4, 5),
        "poison_damage_per_second": 5,
        "poison_persist_time": 5,
        "poison_prob": 0.6,
    }

    WALK_SPEED = 160



class Ghost(Enemy):
    NAME = "Ghost"
    HP = 600
    ATK = 45
    DFS = 3

    RADIUS = 24
    HEIGHT = 90
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 60,
        "angle": 90,
        "key_frames": (4, 5),
        "leak_prob": 0.7,
        "leak_mp": 60,
        "leak_sp": 60,
    }

    WALK_SPEED = 130



class TwoHeadSkeleton(Enemy):
    NAME = "TwoHeadSkeleton"
    HP = 800
    ATK = 52
    DFS = 5

    RADIUS = 24
    HEIGHT = 120
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 80,
        "angle": 60,
        "key_frames": (6, 7),
        "suck_blood_ratio": 0.5,
    }

    WALK_SPEED = 140



class Werwolf(Enemy):
    NAME = "Werwolf"
    HP = 700
    ATK = 50
    DFS = 4

    RADIUS = 24
    HEIGHT = 85 
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 70,
        "angle": 80,
        "key_frames": (4, 5),
        "frozen_prob": 0.6,
        "frozen_time": 5,
        "action_rate_scale": 0.5,
    }

    WALK_SPEED = 170



class SilverTentacle(Enemy):
    NAME = "SilverTentacle"
    HP = 400
    ATK = 40
    DFS = 4

    RADIUS = 24
    HEIGHT = 75
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 80,
        "angle": 90,
        "key_frames": (4,),
    }

    WALK_SPEED = 150
    # special attribute
    ATK_REBOUNCE = True
    ANTI_THUMP = True
    MAGIC_RESISTANCE_SCALE = 0.5



class GameMap(object):
    TILE_SIZE = 256
    ONE_SCREEN_DISTANCE_WIDTH = TILE_SIZE * 4
    ONE_SCREEN_DISTANCE_HEIGHT = TILE_SIZE * 6
    CHAPTERS = [0, 1, 2, 3, 4, 5]



class WoodenCase(object):
    NAME = "WoodenCase"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (64, 64, 48, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 48, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = False



class WoodenCase2(object):
    NAME = "WoodenCase2"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (112, 64, 48, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 48, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = False



class WoodenCase2_1(object):
    NAME = "WoodenCase2_1"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (0, 64, 32, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 32, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = False



class WoodenCase2_2(object):
    NAME = "WoodenCase2_2"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (32, 64, 32, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 32, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = False



class WoodenCase3(object):
    NAME = "WoodenCase3"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (32, 128, 48, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 48, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = False



class WoodenCase3_1(object):
    NAME = "WoodenCase3_1"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (0, 128, 32, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 32, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = False



class WoodenCase4(object):
    NAME = "WoodenCase4"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (112, 128, 48, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 48, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = False



class IronCase(object):
    NAME = "IronCase"
    IMAGE_KEY = "s2"
    IMAGE_RECT = (174, 112, 70, 132)
    POS_RECT_DELTA_Y = 36
    AREA_RECT = (0, 0, 70, 124)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True 
    IS_ELIMINABLE = False

    

class IronCase2(object):
    NAME = "IronCase2"
    IMAGE_KEY = "s9"
    IMAGE_RECT = (64, 0, 64, 128)
    POS_RECT_DELTA_Y = 32
    AREA_RECT = (0, 0, 64, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class GrassWall(object):
    NAME = "GrassWall"
    IMAGE_KEY = "s4"
    IMAGE_RECT = (0, 0, 64, 104)
    POS_RECT_DELTA_Y = 36
    AREA_RECT = (0, 0, 64, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall(object):
    NAME = "StoneWall"
    IMAGE_KEY = "s5"
    IMAGE_RECT = (192, 0, 64, 160)
    POS_RECT_DELTA_Y = 48
    AREA_RECT = (0, 0, 64, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall2(object):
    NAME = "StoneWall2"
    IMAGE_KEY = "s6"
    IMAGE_RECT = (0, 0, 256, 192)
    POS_RECT_DELTA_Y = 80
    AREA_RECT = (0, 0, 256, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall2_1(object):
    NAME = "StoneWall2_1"
    IMAGE_KEY = "s6"
    IMAGE_RECT = (32, 0, 96, 192)
    POS_RECT_DELTA_Y = 80
    AREA_RECT = (0, 0, 96, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall3(object):
    NAME = "StoneWall3"
    IMAGE_KEY = "s7"
    IMAGE_RECT = (0, 128, 128, 128)
    POS_RECT_DELTA_Y = 32
    AREA_RECT = (0, 0, 128, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall4(object):
    NAME = "StoneWall4"
    IMAGE_KEY = "s8"
    IMAGE_RECT = (0, 0, 256, 128)
    POS_RECT_DELTA_Y = 32
    AREA_RECT = (0, 0, 256, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall4_2(object):
    NAME = "StoneWall4_2"
    IMAGE_KEY = "s8"
    IMAGE_RECT = (0, 128, 256, 128)
    POS_RECT_DELTA_Y = 32
    AREA_RECT = (0, 0, 256, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall5(object):
    NAME = "StoneWall5"
    IMAGE_KEY = "s5"
    IMAGE_RECT = (0, 64, 64, 192)
    POS_RECT_DELTA_Y = 48
    AREA_RECT = (0, 0, 64, 192)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall6(object):
    NAME = "StoneWall6"
    IMAGE_KEY = "s10"
    IMAGE_RECT = (0, 128, 128, 128)
    POS_RECT_DELTA_Y = 32
    AREA_RECT = (0, 0, 128, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall7(object):
    NAME = "StoneWall7"
    IMAGE_KEY = "s11"
    IMAGE_RECT = (0, 0, 256, 128)
    POS_RECT_DELTA_Y = 32
    AREA_RECT = (0, 0, 256, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class StoneWall7_1(object):
    NAME = "StoneWall7_1"
    IMAGE_KEY = "s11"
    IMAGE_RECT = (0, 128, 256, 128)
    POS_RECT_DELTA_Y = 32
    AREA_RECT = (0, 0, 256, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True
    IS_ELIMINABLE = False



class RoastChicken(object):
    NAME = "RoastChicken"
    IMAGE_KEY = "food"
    IMAGE_RECT = (192, 192, 64, 64)
    POS_RECT_DELTA_Y = 8
    AREA_RECT = (0, 0, 32, 32)
    IS_BLOCK = False
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = True
    ELIMINATION_TYPE = cfg.StaticObject.ELIMINATION_TYPE_FOOD
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class Omelette(object):
    NAME = "Omelette"
    IMAGE_KEY = "food"
    IMAGE_RECT = (192, 128, 64, 64)
    POS_RECT_DELTA_Y = 8
    AREA_RECT = (0, 0, 32, 32)
    IS_BLOCK = False
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = True
    ELIMINATION_TYPE = cfg.StaticObject.ELIMINATION_TYPE_FOOD
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class BreadBasket(object):
    NAME = "BreadBasket"
    IMAGE_KEY = "food"
    IMAGE_RECT = (64, 128, 64, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 32, 32)
    IS_BLOCK = False
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = True
    ELIMINATION_TYPE = cfg.StaticObject.ELIMINATION_TYPE_FOOD
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class Salad(object):
    NAME = "Salad"
    IMAGE_KEY = "food"
    IMAGE_RECT = (192, 64, 64, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 32, 32)
    IS_BLOCK = False
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = True
    ELIMINATION_TYPE = cfg.StaticObject.ELIMINATION_TYPE_FOOD
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class Wine(object):
    NAME = "Wine"
    IMAGE_KEY = "food"
    IMAGE_RECT = (0, 160, 32, 64)
    POS_RECT_DELTA_Y = 24
    AREA_RECT = (0, 0, 16, 16)
    IS_BLOCK = False
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = True
    ELIMINATION_TYPE = cfg.StaticObject.ELIMINATION_TYPE_FOOD
    RECOVER_HP = 50
    SHADOW_INDEX = 0
    SHADOW_RECT_DELTA_Y = 16



class WayPoint(object):
    DIR = os.path.join("etc", "waypoints")
    STEP_WIDTH = 24
    BOUNDING_BOX_RECT = (0, 0, 48, 48)



class EmotionImage(object):
    # a 8*8 image source
    ROW = 8
    COLUMN = 8

    # sub image size
    WIDTH = 32
    HEIGHT = 32
    SIZE = (WIDTH, HEIGHT)

    FRAMES = {
        # emotion_id: ((begin, end+1), frame_num, frame_rate)
        cfg.SpriteEmotion.ALERT: ((2, 8), 6, 6),
        cfg.SpriteEmotion.ANGRY: ((12, 14), 2, 2),
        cfg.SpriteEmotion.CHAOS: ((14, 16), 2, 2),
        cfg.SpriteEmotion.SILENT: ((24, 28), 4, 3),
        cfg.SpriteEmotion.STUN: ((48, 51), 3, 6),
        cfg.SpriteEmotion.DIZZY: ((51, 54), 3, 6),
    }



class SpriteStatus(object):
    HERO_PANEL_IMAGE_KEY = "status"
    HERO_HEAD_IMAGE_KEY = "renne_head"

    HEALTHY_RATIO_FLOOR = 2.0 / 3
    WOUNDED_RATIO_FLOOR = 1.0 / 3
    DANGER_RATIO_FLOOR = 0

    DEBUFF_POISON_MIX_COLOR = pygame.Color("green")
    DEBUFF_FROZON_MIX_COLOR = pygame.Color("blue")
    DEBUFF_WEAK_IMAGE_KEY = "status"
    DEBUFF_WEAK_RECT = (16, 240, 16, 16)
    DEBUFF_WEAK_BLIT_HEIGHT_DELTA = 15
    DEBUFF_WEAK_Y_MOVE_RATE = 15
    DEBUFF_WEAK_Y_MAX = 10

    # all words
    WORDS = {
        "hero_hp": Font.ARIAL_BOLD_12.render("HP", True, pygame.Color("white")),
        "hero_mp": Font.ARIAL_BOLD_12.render("MP", True, pygame.Color("white")),
        "hero_sp": Font.ARIAL_BOLD_12.render("SP", True, pygame.Color("white")),
    }

    # health point related
    SPRITE_HP_COLORS = {
        cfg.SpriteStatus.HEALTHY: pygame.Color(0, 128, 0, 128),
        cfg.SpriteStatus.WOUNDED: pygame.Color(128, 128, 0, 128),
        cfg.SpriteStatus.DANGER: pygame.Color(128, 0, 0, 128),
        cfg.SpriteStatus.DIE: pygame.Color(128, 128, 128, 128),
    }
    SPRITE_BAR_BG_COLOR = pygame.Color(0, 0, 0, 128)
    HERO_ALL_BAR_SIZE = (100, 10)

    # hp related
    HERO_HP_TITLE_BLIT_POS = (82, 14)
    HERO_HP_BLIT_POS = (104, 16)

    # mp related
    HERO_MP_COLOR = pygame.Color(0, 128, 128, 128),
    HERO_MP_TITLE_BLIT_POS = (82, 31)
    HERO_MP_BLIT_POS = (104, 33)

    # sp related
    HERO_SP_COLOR = pygame.Color(0, 64, 128, 128),
    HERO_SP_TITLE_BLIT_POS = (82, 48)
    HERO_SP_BLIT_POS = (104, 50)

    ENEMY_HP_BAR_SIZE = (50, 5)

    HERO_PANEL_RECT = (0, 0, 144, 56)
    HERO_PANEL_SCALE_SIZE = (216, 92)
    HERO_PANEL_BLIT_POS = (2, 2)
    HERO_HEAD_SIZE = (128, 128)
    HERO_HEAD_BLIT_POS = (-20, -38)

    # Renne magic skill icons
    DESTROY_FIRE_ICON_IMAGE_KEY = "e4"
    DESTROY_BOMB_ICON_IMAGE_KEY = "e4"
    DESTROY_AEROLITE_ICON_IMAGE_KEY = "e4"
    DIZZY_ICON_IMAGE_KEY = "e4"
    SKILL_ICON_FRAME_IMAGE_KEY = "status3"

    DESTROY_FIRE_ICON_RECT = (64, 64, 32, 32)
    DESTROY_BOMB_ICON_RECT = (128, 64, 32, 32)
    DESTROY_AEROLITE_ICON_RECT = (192, 64, 32, 32)
    DIZZY_ICON_RECT = (96, 64, 32, 32)
    SKILL_CD_MASK_COLOR = pygame.Color(128, 128, 128, 128)
    SKILL_ICON_FRAME_RECT = (36, 228, 24, 24)
    SKILL_ICON_SIZE = (32, 32)

    DESTROY_FIRE_ICON_BLIT_POS = (8, 100)
    DESTROY_BOMB_ICON_BLIT_POS = (58, 100)
    DESTROY_AEROLITE_ICON_BLIT_POS = (108, 100)
    DIZZY_ICON_BLIT_POS = (158, 100)

    COST_HP_WORDS_COLOR = pygame.Color("red")
    COST_HP_WORDS_FONT = Font.ARIAL_BLACK_32
    COST_HP_WORDS_SHOW_TIME = 0.3
    COST_HP_WORDS_BLIT_HEIGHT_OFFSET = 35
    COST_HP_WORDS_BLIT_X_SIGMA = 20
    COST_HP_WORDS_BLIT_Y_SIGMA = 10
    COST_HP_WORDS_POS_MOVE_RATE = (0, -60)

    RECOVER_HP_WORDS_COLOR = pygame.Color("green")
    RECOVER_HP_WORDS_FONT = Font.ARIAL_BLACK_32
    RECOVER_HP_WORDS_SHOW_TIME = 0.3
    RECOVER_HP_WORDS_BLIT_HEIGHT_OFFSET = 35
    RECOVER_HP_WORDS_BLIT_X_SIGMA = 20
    RECOVER_HP_WORDS_BLIT_Y_SIGMA = 10
    RECOVER_HP_WORDS_POS_MOVE_RATE = (0, -60)

    # weaken status
    MP_SP_DOWN_WORDS_COLOR = pygame.Color("black")
    MP_SP_DOWN_WORDS_FONT = Font.ARIAL_BLACK_16
    MP_SP_DOWN_WORDS_SHOW_TIME = 0.5
    MP_SP_DOWN_WORDS_BLIT_HEIGHT_OFFSET = 35
    MP_SP_DOWN_WORDS_BLIT_X_SIGMA = 20
    MP_SP_DOWN_WORDS_BLIT_Y_SIGMA = 10
    MP_SP_DOWN_WORDS_POS_MOVE_RATE = (0, 20)


class Achievement(object):
    KILL_ICON_IMAGE_KEY = "status5"
    N_HIT_ICON_IMAGE_KEY = "status5"
    N_KILL_ICON_IMAGE_KEY = "status5"
    SCORE_PANEL_IMAGE_KEY = "status"
    KILL_ICON_RECT = (224, 0, 32, 32)
    N_HIT_ICON_RECT = (192, 32, 32, 32)
    N_KILL_ICON_RECT = (192, 0, 32, 32)
    SCORE_PANEL_RECT = (0, 0, 144, 56)
    SCORE_PANEL_SCALE_SIZE = (220, 36)

    SCORE_PANEL_BLIT_POS1 = (234, 8)
    SCORE_PANEL_BLIT_POS2 = (474, 8)
    SCORE_PANEL_BLIT_POS3 = (714, 8)

    KILL_ICON_BLIT_POS = (240, 10)
    N_HIT_ICON_BLIT_POS = (480, 10)
    N_KILL_ICON_BLIT_POS = (720, 10)

    SCORE_RUN_RATE = 100

    SCORE_COLOR = pygame.Color("white"),
    SCORE_FONT = Font.HOLLOW_32

    N_KILL_TIMEDELTA = 20   # in second unit

    KILL_SCORE = {
        "blit_pos": (280, 7),
        "font": Font.HOLLOW_32,
        "color": SCORE_COLOR,
    }

    N_HIT_SCORE = {
        "blit_pos": (520, 7),
        "font": Font.HOLLOW_32,
        "color": SCORE_COLOR,
    }

    N_KILL_SCORE = {
        "blit_pos": (760, 7),
        "font": Font.HOLLOW_32,
        "color": SCORE_COLOR,
    }

    SCORE = {
        "per_hit": 10,
        "per_kill": 100,
        "per_n_kill": 20,
    }



class GameStatus(object):
    HERO_WIN_PANEL_IMAGE_KEY = "status2"
    HERO_LOSE_PANEL_IMAGE_KEY = "status2"
    CHAPTER_SCORE_ICON_IMAGE_KEY = "status2"
    BONUS_ICON_IMAGE_KEY = "status6"
    CHAPTER_SCORE_LINE_IMAGE_KEY = "status3"
    NUMBER_IMAGE_KEY1 = "status4"

    NUMBER_RECT1 = (0, 280, 340, 60)
    NUMBER_SIZE1 = (34, 60)
    NUMBER_RECT2 = (96, 160, 160, 16)
    NUMBER_SIZE2 = (16, 16)
    BEGIN_NUMBER_BLIT_POS = (500, 360)

    # init status persist 3 seconds
    INIT_PERSIST_TIME = 3

    HERO_WIN_PANEL_RECT = (0, 0, 1024, 170)
    HERO_LOSE_PANEL_RECT = (0, 170, 1024, 170)
    BONUS_ICON_RECT = (128, 224, 62, 16)

    CHAPTER_SCORE_ICON_RECT = (294, 720, 68, 74)
    CHAPTER_SCORE_ICON_SCALE_SIZE = (56, 60)
    CHAPTER_SCORE_LINE_RECT = (58, 98, 28, 10)
    CHAPTER_SCORE_LINE_SCALE_SIZE = (320, 10)

    HERO_WIN_BLIT_POS = (0, 340)
    HERO_LOSE_BLIT_POS = (0, 300)

    CHAPTER_KILL_ICON_BLIT_POS = (380, 140)
    CHAPTER_N_HIT_ICON_BLIT_POS = (380, 180)
    CHAPTER_N_KILL_ICON_BLIT_POS = (380, 220)
    CHAPTER_SCORE_LINE_BLIT_POS = (340, 260)
    CHAPTER_SCORE_ICON_BLIT_POS = (360, 280)

    BONUS_ICON_BLIT_POS1 = (640, 190)
    BONUS_ICON_BLIT_POS2 = (640, 230)

    CHAPTER_KILL_BLIT_POS = (440, 137)
    CHAPTER_N_HIT_BLIT_POS = (440, 177)
    CHAPTER_N_KILL_BLIT_POS = (440, 217)
    CHAPTER_SCORE_BLIT_POS = (440, 286)

    CHAPTER_SCORE_FONT = Font.HOLLOW_48
    CHAPTER_SCORE_COLOR = pygame.Color("white")

    CHAPTER_NEXT = Font.ARIAL_BLACK_32.render("press enter to continue", True, pygame.Color("gray"))
    CHAPTER_NEXT_BLIT_Y = 500

    CHAPTER_AGAIN = Font.ARIAL_BLACK_32.render("press enter to play again", True, pygame.Color("gray"))
    CHAPTER_AGAIN_BLIT_Y = 460

    CHAPTER_SCORE = {
        "font": CHAPTER_SCORE_FONT,
        "color": CHAPTER_SCORE_COLOR,
        "blit_pos": CHAPTER_SCORE_BLIT_POS,
    }



class Chapter(object):
    LOADING_PICTURE_IMAGE_KEY = "loading_chapter"
    LOADING_PICTURE_RECT = (0, 0, 640, 480)
    LOADING_PICTURE_FADE_IN_TIME = 1    # in second unit, show up the picture
    LOADING_WORD = Font.ARIAL_BLACK_28.render("now loading ...", True, pygame.Color("white"))
    LOADING_WORD_BLIT_POS = (760, 700)

    WIN_CONDITION_ALL_ENEMY_DIE = 1
    WIN_CONDITION_BOSS_DIE = 2

    WIN_CONDITION = {
        1: WIN_CONDITION_ALL_ENEMY_DIE,
        2: WIN_CONDITION_ALL_ENEMY_DIE,
        3: WIN_CONDITION_ALL_ENEMY_DIE,
        4: WIN_CONDITION_ALL_ENEMY_DIE,
        5: WIN_CONDITION_BOSS_DIE,
        999: WIN_CONDITION_ALL_ENEMY_DIE,
    }



class StartGame(object):
    PICTURE_IMAGE_KEY = "start_game"
    PICTURE_FADE_IN_TIME = 3 # in second unit, show up the picture
    PICTURE_BLIT_Y = 30



class EndGame(object):
    THE_END_IMAGE_KEY = "the_end"
    THE_END_IMAGE_RECT = (0, 0, 640, 480)
    THE_END_WORD = Font.ARIAL_BLACK_32.render("The End", True, pygame.Color("white"))
    THE_END_SHOW_DELAY_TIME = 1.5
    ENDING_FADEIN_TIME = 5
    BUSUNCLE_WORKS = Font.ARIAL_BLACK_32.render("Busuncle's works", True, pygame.Color("white"))
    BUSUNCLE_WORKS_BLIT_Y = 450
    RENNE_IMAGE_BLIT_Y = 360
    CHAPTER_WIN_SCREEN_IMAGE_SHOW_DELAY_TIME = 1.5



class MapEditor(object):
    SCREEN_MOVE_SPEED = 400



class Music(object):
    BACKGROUND_VOLUME = 0.4
    SOUND_VOLUME = 0.2
    START_GAME_KEY = "start_game"
    END_GAME_KEY = "end_game"
    CHAPTER_KEY_PREFIX = "chapter_"
    HERO_WIN_KEY = "hero_win"
    HERO_LOSE_KEY = "hero_lose"



class Sound(object):
    RENNE_ATTACKS = ("renne_attack", "renne_attack2", "renne_attack3", 
        "attack0", "attack0", "attack0")
    RENNE_ATTACKS2 = ("renne_attack", "renne_attack2", "renne_attack3")
    RENNE_ATTACK_HITS = ("attack_hit", "attack_hit2")
    RENNE_WIN = "renne_win"

    ENEMY_ATTACK_HITS = ("attack_hit", "attack_hit2", "attack_hit3")

    LEONHARDT_ATTACKS = ("leonhardt_attack", "leonhardt_attack2", "leonhardt_attack3")



class Effect(object):
    DESTROY_FIRE_IMAGE_KEY = "e2"
    DESTROY_FIRE_RECT = (64, 0, 64, 64)
    DESTROY_FIRE_SHADOW_INDEX = 3
    DESTROY_FIRE_SHADOW_RECT_DELTA_Y = 8

    DESTROY_BOMB_IMAGE_KEY = "e3"
    DESTROY_BOMB_RECT = (0, 0, 192, 128)
    DESTROY_BOMB_SHADOW_INDEX = 1
    DESTROY_BOMB_SHADOW_RECT_DELTA_Y = 18

    DESTROY_AEROLITE_IMAGE_KEY = "e3"
    DESTROY_AEROLITE_RECT = (192, 0, 64, 128)
    DESTROY_AEROLITE_SHADOW_INDEX = 3
    DESTROY_AEROLITE_SHADOW_RECT_DELTA_Y = 8

    DEATH_COIL_IMAGE_KEY = "e1"
    DEATH_COIL_RECT = (128, 192, 128, 64)
    DEATH_COIL_SHADOW_INDEX = 0
    DEATH_COIL_SHADOW_RECT_DELTA_Y = 20

    HELL_CLAW_IMAGE_KEY = "e1"
    HELL_CLAW_RECT = (0, 184, 128, 72)
    HELL_CLAW_SHADOW_INDEX = 1
    HELL_CLAW_SHADOW_RECT_DELTA_Y = 18

    BLINK_RATE = 256
    BLINK_DEPTH_SECTION = (32, 128)

    BLINK_RATE2 = 128
    BLINK_DEPTH_SECTION2 = (0, 96)

    BLINK_RATE3 = 1024
    BLINK_DEPTH_SECTION3 = (0, 192)



class Ammo(object):
    ARROW_SHADOW_INDEX = 2
    ARROW_SHADOW_DY = 15

    ARROW_IMAGE_KEY = "arrow"
    ARROW_WIDTH = 64
    ARROW_HEIGHT = 32



######### mapping for factory ########
# control all objects in list, their order will detemine the attribute "ID" of their own
SPRITE_SETTING_LIST = [
    SkeletonWarrior,
    CastleWarrior,
    SkeletonArcher,
    LeonHardt,
    ArmouredShooter,
    SwordRobber,
    SkeletonWarrior2,
    Ghost,
    TwoHeadSkeleton,
    Werwolf,
    SilverTentacle,
]

STATIC_OBJECT_SETTING_LIST = [
    WoodenCase,
    IronCase,
    IronCase2,
    GrassWall,
    StoneWall,
    StoneWall2,
    StoneWall2_1,
    StoneWall3,
    WoodenCase2,
    WoodenCase2_1,
    WoodenCase2_2,
    WoodenCase3,
    WoodenCase3_1,
    WoodenCase4,
    StoneWall4,
    StoneWall4_2,
    StoneWall5,
    StoneWall6,
    StoneWall7,
    StoneWall7_1,
    RoastChicken,
    Omelette,
    BreadBasket,
    Salad,
    Wine,
]


# set attribute "ID" for all objects, start from 1, Renne is special for 0
Renne.ID = 0
Renne.GAME_OBJECT_TYPE = cfg.GameObject.TYPE_DYNAMIC
for i, cls in enumerate(SPRITE_SETTING_LIST):
    cls.ID = i + 1
    cls.GAME_OBJECT_TYPE = cfg.GameObject.TYPE_DYNAMIC
for i, cls in enumerate(STATIC_OBJECT_SETTING_LIST):
    cls.ID = i + 1
    cls.GAME_OBJECT_TYPE = cfg.GameObject.TYPE_STATIC


SPRITE_SETTING_MAPPING = dict((cls.ID, cls) for cls in SPRITE_SETTING_LIST)
STATIC_OBJECT_SETTING_MAPPING = dict((cls.ID, cls) for cls in STATIC_OBJECT_SETTING_LIST)


SPRITES_WITH_MAGIC_SKILL = (Renne.ID, LeonHardt.ID)
SPRITES_WITH_AMMO = (SkeletonArcher.ID, )


########### resource mapping ###########
RENNE_IMAGE_FILENAME = "renne.png"

SPRITE_FRAMES = {
    # {sprite_id: (folder, {sprite_action: (image_filename, frame_num, frame_rate), ...}), ...}
    Renne.ID: ("renne", {
        cfg.HeroAction.STAND: ("stand_8.png", 8, 12),
        cfg.HeroAction.WALK: ("walk_8.png", 8, 14),
        cfg.HeroAction.RUN: ("run_8.png", 8, 16),
        cfg.HeroAction.ATTACK: ("attack_14.png", 14, 18),
        cfg.HeroAction.WIN: ("win_31.png", 31, 14),
        cfg.HeroAction.REST: ("rest_4.png", 4, 8),
        cfg.HeroAction.SKILL: ("skill_2.png", 2, 2),
        cfg.HeroAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    SkeletonWarrior.ID: ("skeleton_warrior", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 10),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    CastleWarrior.ID: ("castle_warrior", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 10),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    SkeletonArcher.ID: ("skeleton_archer", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 10),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 8),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    LeonHardt.ID: ("leonhardt", {
        cfg.LeonHardtAction.STAND: ("stand_8.png", 8, 12),
        cfg.LeonHardtAction.RUN: ("run_8.png", 8, 14),
        cfg.LeonHardtAction.ATTACK: ("attack_8.png", 8, 12),
        cfg.LeonHardtAction.ATTACK2: ("attack2_8.png", 8, 12),
        cfg.LeonHardtAction.SKILL1: ("skill1_2.png", 2, 2),
        cfg.LeonHardtAction.SKILL2: ("skill2_8.png", 8, 10),
        cfg.LeonHardtAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    ArmouredShooter.ID: ("armoured_shooter", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 12),
        cfg.EnemyAction.ATTACK: ("attack_10.png", 10, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    SwordRobber.ID: ("sword_robber", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_7.png", 7, 8),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    SkeletonWarrior2.ID: ("skeleton_warrior2", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    Ghost.ID: ("ghost", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    TwoHeadSkeleton.ID: ("two_head_skeleton", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    Werwolf.ID: ("werwolf", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    SilverTentacle.ID: ("silver_tentacle", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_5.png", 5, 6),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
}

# (folder, {image_key: image_filename, ...})
STATIC_OBJECT_IMAGES = ("static_object", {
    "s1": "s1.png",
    "s2": "s2.png", 
    #"s3": "s3.png",
    "s4": "s4.png",
    "s5": "s5.png",
    "s6": "s6.png", 
    "s7": "s7.png", 
    "s8": "s8.png",
    "s9": "s9.png",
    "s10": "s10.png",
    "s11": "s11.png",
    "food": "food.png",
})

# (folder, {image_key: image_filename, ...})
TILE_IMAGES = ("tiles", {
    1: "1.png", 
    2: "2.png",
    3: "3.png", 
    4: "4.png", 
    5: "5.png", 
    #6: "6.png", 
    #7: "7.png", 
    8: "8.png", 
})

# (folder, {image_key: image_filename, ...})
BASIC_IMAGES = ("basic", {
    "sprite_shadow": "sprite_shadow.png",
    "emotion": "sprite_emotion.png",
    "head_status": "head_status.png",
})

BATTLE_IMAGES = ("battle", {
    "renne_head": "renne_head.png",
    "status": "status.png",
    "status2": "status2.png", 
    "status3": "status3.png", 
    "status4": "status4.png", 
    "status5": "status5.png",
    "status6": "status6.png",
    #"icon1": "icon1.png",
    "arrow": "arrow.png",
})

CG_IMAGES = ("cg", {
    "start_game": "1.png",
    #"loading_chapter": "2.png", 
    "loading_chapter": "3.png", 
    "the_end": "4.png",
})


BACKGROUND_MUSICS = ("background", {
    "start_game": "start_game.ogg", 
    "end_game": "end_game.ogg", 
    "chapter_1": "chapter_1.ogg",
    "chapter_2": "chapter_2.ogg",
    "chapter_3": "chapter_3.ogg",
    "chapter_4": "chapter_4.ogg",
    "chapter_5": "chapter_5.ogg",
    "chapter_999": "chapter_5.ogg",
    "hero_win": "hero_win.wav",
    "hero_lose": "hero_lose.wav",
})

SOUND_EFFECT = ("sound", {
    "attack0": "attack0.wav",
    "renne_attack": "renne_attack.wav",
    "renne_attack2": "renne_attack2.wav",
    "renne_attack3": "renne_attack3.wav",
    "renne_under_attack": "renne_under_attack.wav",
    "renne_win": "renne_win.wav",
    "attack_hit": "attack_hit.wav",
    "attack_hit2": "attack_hit2.wav",
    "attack_hit3": "attack_hit3.wav",
    "leonhardt_attack": "leonhardt_attack.wav",
    "leonhardt_attack2": "leonhardt_attack2.wav",
    "leonhardt_attack3": "leonhardt_attack3.wav",
})

EFFECT = ("effect", {
    "e1": "e1.png",
    "e2": "e2.png",
    "e3": "e3.png",
    "e4": "e4.png",
})
