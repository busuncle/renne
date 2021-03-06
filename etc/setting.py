# -*- coding: gbk -*-

import os
from base import constant as cfg
import pygame
from pygame.locals import *

pygame.init()

FPS = 60
DEBUG_MODE = False


CONFIG = {
    # some default config, may be overwritten by config.txt
    "hero": "renne", 
}
CONFIG_CONSTRAINT = {
    # constraint set for config
    "hero": lambda x: x in ("renne", "joshua"),
}
with open("config.txt") as fp:
    # read config from config.txt file, may be opened to player
    for line in fp:
        kv = line.lower().split("=")
        if len(kv) != 2:
            continue

        k = kv[0].strip()
        v = kv[1].strip()
        if k not in CONFIG_CONSTRAINT or not CONFIG_CONSTRAINT[k](v):
            continue

        # valid key-value, overwrite the default one
        CONFIG[k] = v



class Font(object):
    ARIAL_FILEPATH = os.path.join("res", "font",  "arial.ttf")
    ARIAL_BOLD_FILEPATH = os.path.join("res", "font", "arial_bold.ttf")
    ARIAL_BLACK_FILEPATH = os.path.join("res", "font", "arial_black.ttf")
    HOLLOW_FILEPATH = os.path.join("res", "font", "hollow.ttf")
    MSYH_FILEPATH = os.path.join("res", "font", "msyh.ttf")

    MSYH_12= pygame.font.Font(MSYH_FILEPATH, 12)
    MSYH_16 = pygame.font.Font(MSYH_FILEPATH, 16)
    MSYH_24 = pygame.font.Font(MSYH_FILEPATH, 24)
    MSYH_32 = pygame.font.Font(MSYH_FILEPATH, 32)
    MSYH_48 = pygame.font.Font(MSYH_FILEPATH, 48)

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
        "options": [
            {"name": u"继续游戏", "mark": "continue", "display": True},
            {"name": u"主菜单", "mark": "main", "display": True}, 
            {"name": u"离开游戏", "mark": "quit", "display": True},
        ],
        "option_rect": (0, 0, 224, 32),
        "blit_y": 320,
        "font_on": Font.MSYH_32,
        "font_off": Font.MSYH_24,
        "color_on": pygame.Color("white"),
        "color_off": pygame.Color("gray"),
    }

    START_GAME = {
        "options": [
            {"name": u"读取存档", "mark": "load", "display": False},
            {"name": u"闯关模式", "mark": "start", "display": True}, 
            {"name": u"无限模式", "mark": "dead_mode", "display": True}, 
            {"name": u"退出", "mark": "quit", "display": True},
        ],
        "option_rect": (0, 0, 256, 48),
        "blit_y": 520,
        "font_on": Font.MSYH_48,
        "font_off": Font.MSYH_32,
        "color_on": pygame.Color("white"),
        "color_off": pygame.Color("gray"),
    }



class UserKey(object):
    UP = K_w
    DOWN = K_s
    LEFT = K_a
    RIGHT = K_d
    ATTACK = K_j
    REST = K_k
    MAGIC_SKILL_1 = K_u
    MAGIC_SKILL_2 = K_i
    MAGIC_SKILL_3 = K_o
    MAGIC_SKILL_4 = K_h

    ONE_PRESSED_KEYS = (ATTACK, MAGIC_SKILL_1, MAGIC_SKILL_2, MAGIC_SKILL_3, MAGIC_SKILL_4)
    ONE_PRESSED_KEY_CD = 0.1

    CONTINUE_PRESSED_KEYS = (UP, DOWN, LEFT, RIGHT, REST)

    DIRECTION_KEYS = (UP, DOWN, LEFT, RIGHT)
    DIRECTION_KEY_TO_DIRECT = {
        UP: cfg.Direction.NORTH,
        DOWN: cfg.Direction.SOUTH,
        LEFT: cfg.Direction.WEST,
        RIGHT: cfg.Direction.EAST,
    }
    DIRECT_TO_DIRECTION_KEY = dict((v, k) for k, v in DIRECTION_KEY_TO_DIRECT.iteritems())

    PAUSE = K_ESCAPE
    OK = K_RETURN

    # double press some direction key to run, this is the threshold between 2 presses
    RUN_THRESHOLD = 0.2



class Screen(object):
    SIZE = [1024, 768]
    INNER_SIZE = [SIZE[0] / 4, SIZE[1] / 4]
    DEFAULT_SCREEN = pygame.display.set_mode(SIZE)
    DEFAULT_SURFACE = pygame.Surface(SIZE).convert_alpha()



class Stuff(object):
    # some common stuff, may be used everywhere if needed
    MASK_ALPHA_128 = pygame.Color(0, 0, 0, 128)



class Physics(object):
    # define all physics constants, it's only values, not included direction, add it if necessary
    SPRITE_FLOOR_FRICTION_ACCELERATION = 4500
    FRICTION_FACTOR = 45
    GRAVITY_ACCELERATION = 1200



class Sprite(object):
    SHADOW_IMAGE_KEY = "sprite_shadow"
    UNDER_ATTACK_MIX_COLOR = pygame.Color("gray")
    UNDER_ATTACK_EFFECT_TIME = 0.05
    RECOVER_HP_MIX_COLOR = pygame.Color("gray")
    RECOVER_HP_EFFECT_TIME = 0.08



class Hero(object):
    ROLE = cfg.SpriteRole.HERO
    LEVEL_EXP = (0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5000)
    #LEVEL_EXP = tuple(range(0, 28, 3))
    MAX_LEVEL = len(LEVEL_EXP)
    MAX_EXP = LEVEL_EXP[MAX_LEVEL - 1]



class Renne(Hero):
    NAME = "Renne"

    HP = 150
    MP = 80
    SP = 60
    ATK = 10
    MAGIC_SKILL_DAMAGE_RATIO = 1
    DFS = 1

    MP_RECOVERY_RATE = 10
    SP_COST_RATE = 12
    SP_RECOVERY_RATE = 15

    # sprite radius
    RADIUS = 18 
    HEIGHT = 70
    WEIGHT = 100

    # distance from coord to sprite foot
    POS_RECT_DELTA_Y = 40

    SHADOW_RECT_DELTA_Y = 50
    SHADOW_INDEX = 1

    # move speed, in pixel unit
    WALK_SPEED = 100
    RUN_SPEED = 200

    # values for every level
    LEVEL_HP = (150, 200, 250, 300, 350, 400, 480, 560, 640, 720)
    LEVEL_MP = (80, 120, 160, 220, 280, 360, 440, 520, 600, 680)
    LEVEL_SP = (60, 80, 100, 120, 140, 160, 170, 180, 190, 200)
    LEVEL_ATK = (10, 12, 14, 16, 18, 20, 24, 28, 32, 36)
    LEVEL_MAGIC_SKILL_DAMAGE_RATIO = (1, 1.1, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0)
    LEVEL_DFS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

    ATTACKER_PARAMS = {
        "attack1":{
            "range": 100,
            "angle": 120,
            "atk_ratio": 1,
            "damage": ATK,
            "crick_time": 0.25,
            "key_frames": (4, ),
            "start_frame": 4,
            "end_frame": 7,
            "self_crick_time": 0.08,
        },
        "attack2": {
            "range": 110, 
            "angle": 160,
            "atk_ratio": 1.5,
            "damage": ATK,
            "key_frames": (4, 5),
            "accumulate_power_frame": 2,
            "accumulate_power_time": 0.08,
            "thump_crick_time": 0.3,
            "thump_out_speed": 900,
            "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
            "self_crick_time": 0.15,
        },
        "attack_combo_time_delta": 0.6,
        "key_frames": (4, 5),
        "run_attack": {
            "atk_ratio": 1.8,
            "damage": ATK,
            "crick_time": 0.4,
            "out_speed": 1000,
            "acceleration": -400,
            "self_crick_time": 0.1,
            "end_frame": 8,
        },
        "destroy_fire": {
            "range": 400,
            "damage": 50,
            "speed": 300,
            "radius": 18,
            "crick_time": 0.3,
            "dx": 32,
            "dy": 48,
            "mana": 20,
            "cd": 1,
        },
        "destroy_bomb": {
            "range": 360,
            "damage": 80,
            "speed": 260,
            "mana": 50,
            "cd": 5,
            "bomb_radius": 18,
            "dx": 32,
            "dy": 52,
            "body_shake_time": 0.25,
            "action_rate_scale_ratio": 0.5,
            "action_rate_scale_time": 3,
            "bombs_direct_num": 5,
            "bomb_shake_on_x": 5,
            "bomb_shake_on_y": 5,
            "bomb_life": 0.4,
            "bomb_ranges": range(40, 330, 20),
        },
        "destroy_aerolite": {
            "key_frames": (1, ),
            "fall_range": 160,
            "damage": 100,
            "acceleration": Physics.GRAVITY_ACCELERATION,
            "mana": 60,
            "cd": 10,
            "dx": 32,
            "dy": 240,
            "trigger_times": (0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2),
            #"trigger_times": (0.2, ),
            "aerolite_radius": 18,
            "aerolite_damage_cal_time": 0.4,
            "aerolite_life": 1.5,
            "aerolite_shake_on_x": 100,
            "aerolite_shake_on_y": 100,
            "stun_time": 5,
        },
        "dizzy": {
            "prob": 0.99,
            "range": 400,
            "cd": 30,
            "mana": 80,
            "time": 15,
            "effective_time": 1.2,
            "key_frames": (5, 6),
            "gen_leaf_cd": 0.08,
            "leaf_life": 2,
            "leaf_z": 100,
            "leaf_vec_z": -30,
        },
    }

    # very special setting for a win frame delay effect
    WIN_FRAME_DELAY = 1



class Joshua(Hero):
    NAME = "Joshua"

    HP = 200
    MP = 60
    SP = 100
    ATK = 12
    MAGIC_SKILL_DAMAGE_RATIO = 1
    DFS = 2

    MP_RECOVERY_RATE = 10
    SP_COST_RATE = 12
    SP_RECOVERY_RATE = 15

    # sprite radius
    RADIUS = 18 
    HEIGHT = 80
    WEIGHT = 100

    # distance from coord to sprite foot
    POS_RECT_DELTA_Y = 40

    SHADOW_RECT_DELTA_Y = 50
    SHADOW_INDEX = 1

    # move speed, in pixel unit
    WALK_SPEED = 120
    RUN_SPEED = 240

    # values for every level
    LEVEL_HP = (200, 250, 300, 360, 450, 550, 650, 750, 850, 1000)
    LEVEL_MP = (60, 80, 120, 160, 200, 240, 280, 320, 360, 400)
    LEVEL_SP = (100, 120, 140, 160, 200, 240, 280, 320, 360, 400)
    LEVEL_ATK = (12, 15, 18, 20, 25, 30, 35, 40, 45, 50)
    LEVEL_MAGIC_SKILL_DAMAGE_RATIO = (1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0)
    LEVEL_DFS = (2, 3, 5, 8, 10, 12, 15, 18, 20, 22)

    ATTACKER_PARAMS = {
        "attack1": {
            "range": 90,
            "angle": 120,
            "atk_ratio": 1.0,
            "damage": ATK, 
            "key_frames": (4, ),
            "start_frame": 0,
            "end_frame": 4.5,
            "start_frame2": 3,
            "crick_time": 0.2,
            "self_crick_time": 0.05,
        },
        "attack2": {
            "range": 100,
            "angle": 120,
            "atk_ratio": 1.2,
            "damage": ATK, 
            "key_frames": (6, 7),
            "start_frame": 5, 
            "end_frame": 9,
            "crick_time": 0.3,
            "self_crick_time": 0.05,
        },
        "attack3": {
            "range": 120,
            "angle": 160,
            "atk_ratio": 1.5,
            "damage": ATK, 
            "key_frames": (6, ),
            "start_frame": 2,
            "end_frame": 13,
            "crick_time": 1,
            "thump_crick_time": 0.5,
            "thump_out_speed": 1200,
            "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
        },
        "attack_combo_time_delta": 0.6,
        "run_attack": {
            "range": 120,
            "angle": 160,
            "atk_ratio": 1.8,
            "damage": ATK, 
            "key_frames": (6, ),
            "start_frame": 0,
            "end_frame": 12,
            "acceleration": -400,
            "crick_time": 0.5,
            "out_speed": 1200,
            "self_crick_time": 0.1,
        },
        "x1": {
            "key_frames": (8, ),
            "mana": 20,
            "cd": 8,
            "end_frame": 9,
            "stun_time": 5,
            "damage_ratio": 5,
            "slide_time": 0.08,
            "slide_speed": 800,
            "thump_out_speed": 1200,
            "thump_crick_time": 0.4,
            "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
        },
        "x2": {
            "key_frames": (1, ),
            "mana": 30,
            "trigger_times": (0.1, 0.2, 0.3),
            "trigger_ranges": (80, 120, 160),
            "cd": 10,
            "frozen_time": 5,
            "ice_column_damage_ratio": 3,
            "ice_column_life": 0.8,
            "action_rate_scale_ratio": 0.2,
            "ice_block_gen_num": 6,
            "ice_block_pos_shake_x": 30,
            "ice_fog_per_column_gen_num": 3,
            "ice_fog_pos_shake_x": 30,
            "ice_fog_vec_z": 10,
            "ice_fog_life": 1,
        },
        "x3": {
            "mana": 10,
            "cd": 5,
            "slide_time": 0.6,
            "slide_speed": 280,
            "action_rate_scale_radius": 120,
            "action_rate_scale_ratio": 0.2,
            "action_rate_scale_time": 3,
            "self_action_rate_scale_ratio": 1.5,
            "end_frame": 3,
        },
        "x4": {
            "mana": 60,
            "cd": 50,
            "damage_ratio": 5,
            "lock_distance": 680,
            "key_frames": (12, 20, 36),
            "end_frame": 37,
            "post_kneel_time": 0.8,
            "post_kneel_frame": 3,
            "thump_out_speed": 1200,
            "thump_crick_time": 1,
            "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
        },
    }

    WIN_FRAME_DELAY = 1


                
############ enemy models #############
class Enemy(object):
    ROLE = cfg.SpriteRole.ENEMY
    DEAD_TICK = 1.5
    DEAD_BLINK_TIMES = 3
    VIEW_RANGE = 480
    VIEW_ANGLE = 160 
    NEARBY_ALLIANCE_RANGE = 300



class SkeletonWarrior(Enemy):
    NAME = "SkeletonWarrior"
    HP = 200
    ATK = 35
    DFS = 2
    EXP = 30

    RADIUS = 24
    HEIGHT = 80
    WEIGHT = 100
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
    HP = 350
    ATK = 45
    DFS = 4
    EXP = 50

    RADIUS = 24
    HEIGHT = 82
    WEIGHT = 110
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 90,
        "angle": 60,
        "key_frames": (4, ),
        "thump_crick_time": 0.3,
        "thump_out_speed": 1000,
        "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
        "thump_pre_freeze_time": 1,
        "thump_last_freeze_time": 0.8,
        "thump_pre_frames": (0, 1, 2),
        "thump_pre_rate": 6,
        "thump_frame": 4,
        "thump_slide_time": 0.5,
        "thump_slide_speed": 240,
        "thump_cos_min": 0.9,
    }

    WALK_SPEED = 100



class SkeletonArcher(Enemy):
    NAME = "SkeletonArcher"
    HP = 180
    ATK = 35
    DFS = 2
    EXP = 35

    RADIUS = 24
    HEIGHT = 65
    WEIGHT = 100
    POS_RECT_DELTA_Y = 35
    SHADOW_RECT_DELTA_Y = 55
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 480,
        "angle": 12,
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
    HP = 10000
    MP = 2000
    ATK = 60
    DFS = 5
    MP_RECOVERY_RATE = 10
    EXP = 1000

    RADIUS = 24
    HEIGHT = 80
    WEIGHT = 100
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 2

    ATTACKER_PARAMS = {
        "range": 80,
        "angle": 60,
        "key_frames": (4, 5),
        "death_coil": {
            "key_frames": (1, ),
            "range": 250,
            "damage": 60,
            "speed": 250,
            "radius": 15,
            "dx": 32,
            "dy": 64,
            "mana": 80,
            "split_num": 6,
            "split_dx": 200,
            "split_dy": 200,
        },
        "hell_claw": {
            "range": 500,
            "damage": 80,
            "claw_radius": 18,
            "dx": 32, 
            "dy": 64,
            #"trigger_times": (0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6),
            "trigger_times": (1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2),
            "claw_damage_cal_time": 0.2,
            "claw_life": 0.6,
            "claw_shake_on_x": 120,
            "claw_shake_on_y": 120,
            "mana": 120,
            "last_freeze_time": 2.2,
        },
        "death_domain": {
            "damage": 30,
            "hit_cd": 1,
            "radius": 300,
            "range": 400,
            "pre_run_time": 2,
            "run_time": 6,
            "post_run_time": 2,
            "rotate_rate": 48,
            "sword_up_speed": 500,
            "sword_up_life_time": 0.2,
            "mana": 200,
            "pull_speed": 120,
            "crick_time": 0.15,
        }
    }
    WALK_SPEED = 200



class ArmouredShooter(Enemy):
    NAME = "ArmouredShooter"
    HP = 300
    ATK = 38
    DFS = 4
    EXP = 50

    # overwrite
    VIEW_RANGE = 500
    VIEW_ANGLE = 180 

    RADIUS = 24
    HEIGHT = 70
    WEIGHT = 100
    POS_RECT_DELTA_Y = 35
    SHADOW_RECT_DELTA_Y = 55
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 420,
        "angle": 12,
        "key_frames": (5, 6),
        "grenade": {
            "key_frames": [1, ],
            "damage": 80,
            "trigger_times": [3.0, 3.1, 3.25, 3.2, 3.25, 3.3, 3.35, 3.4, 3.5, 3.6],
            "thump_crick_time": 0.3,
            "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
            "thump_out_speed": 1000,
            "init_height": 50,
            "init_vx": 300,
            "init_vy": 0,
            "fall_acceleration": Physics.GRAVITY_ACCELERATION,
            "max_num": 3,
        },
    }

    WALK_SPEED = 110



class SwordRobber(Enemy):
    NAME = "SwordRobber"
    HP = 400
    ATK = 45
    DFS = 4
    EXP = 60

    RADIUS = 24
    HEIGHT = 75
    WEIGHT = 100
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
        "whirlwind": {
            "pre_frame": 5,
            "pre_time": 1,
            "rotate_rate": 36,
            "rotate_time": 3,
            "move_speed": 180,
            "reach_delta": 10,
            "offset_time": 0.08,
            "self_stun_prob": 0.9,
            "self_stun_time": 3,
            "thump_crick_time": 0.3,
            "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
            "thump_out_speed": 1000,
        }
    }

    WALK_SPEED = 120



class GanDie(Enemy):
    NAME = "GanDie"
    HP = 250
    ATK = 30
    DFS = 2
    EXP = 55

    RADIUS = 24
    HEIGHT = 75
    WEIGHT = 100
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3
    WALK_SPEED = 110

    ATTACKER_PARAMS = {
        "range": 60,
        "angle": 90,
        "key_frames": (4, 5),
        "poison_damage_per_second": 5,
        "poison_persist_time": 5,
        "poison_prob": 0.6,
        "spit_poison": {
            "damage": 5,
            "damage_time": 5,
            "speed": 600,
            "fall_acceleration": Physics.GRAVITY_ACCELERATION,
            "life_time": 10,
            "height": 60,
            "num": 10,
            "max_time": 2,
            "ready_time": 0.6,
            "hold_time": 0.5,
        },
    }




class Ghost(Enemy):
    NAME = "Ghost"
    HP = 300
    ATK = 45
    DFS = 3
    EXP = 80

    RADIUS = 24
    HEIGHT = 90
    WEIGHT = 95
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 80,
        "angle": 80,
        "key_frames": (4, 5),
        "mp_burn_prob": 0.8,
        "mp_burn": 60,
        "invisible": {
            "pre_enter_time": 0.5,
            "time": 3,
        }
    }

    WALK_SPEED = 100



class TwoHeadSkeleton(Enemy):
    NAME = "TwoHeadSkeleton"
    HP = 800
    ATK = 52
    DFS = 5
    EXP = 120

    RADIUS = 24
    HEIGHT = 120
    WEIGHT = 120
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 80,
        "angle": 60,
        "key_frames": (6, 7),
        "suck_blood_ratio": 0.5,
        "fall_range": (100, 600),
        "fall_run_up_time": 0.8,
        "fall_run_up_rate": 30,
        "fall_kneel_time": 0.5,
        "fall_acceleration": -Physics.GRAVITY_ACCELERATION,
        "fall_v0_y": 600,
        "fall_back_v0_y": 300,
        "fall_damage": 80,
        "fall_thump_crick_time": 0.3,
        "fall_thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
        "fall_thump_out_speed": 1000,
    }

    WALK_SPEED = 90



class Werwolf(Enemy):
    NAME = "Werwolf"
    HP = 700
    ATK = 50
    DFS = 4
    EXP = 150

    RADIUS = 24
    HEIGHT = 85 
    WEIGHT = 110
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3
    WALK_SPEED = 130

    ATTACKER_PARAMS = {
        "range": 70,
        "angle": 80,
        "key_frames": (4, 5),
        "frozen_prob": 0.6,
        "frozen_time": 5,
        "action_rate_scale": 0.5,
        "catch": {
            "chance_range_min": 200,
            "ready_time": 0.5,
            "hold_time_a": 0.5,
            "hold_time_b": 0.5,
            "run_speed_scale": 3,
            "run_speed_max": 400,
            "run_frame_rate": 42,
            "friction": -520,
            "damage_a": 25,
            "damage_b": 35,
            "key_frame_a": 4,
            "key_frame_b": 2,
            "thump_out_speed": 1500,
            "thump_crick_time": 0.5,
            "thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
        },
    }



class SilverTentacle(Enemy):
    NAME = "SilverTentacle"
    HP = 300
    ATK = 40
    DFS = 4
    EXP = 70

    RADIUS = 24
    HEIGHT = 75
    WEIGHT = 95
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 80,
        "angle": 90,
        "key_frames": (4,),
    }

    WALK_SPEED = 110



class Robot(Enemy):
    NAME = "Robot"
    HP = 200
    ATK = 10
    DFS = 1
    EXP = 80

    RADIUS = 24
    HEIGHT = 60
    WEIGHT = 95
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    ATTACKER_PARAMS = {
        "range": 90,
        "angle": 80,
        "key_frames": (4, 5),
        "bomb_damage": 100, 
        "bomb_run_up_time": 1,
        "bomb_acceleration": 1500,
        "bomb_lock_distance": 200,
        "bomb_trigger_times": [0.35, 0.4, 0.45, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9],
        #"bomb_trigger_times": [0.2, ],
        "bomb_thump_crick_time": 0.3,
        "bomb_thump_acceleration": -Physics.SPRITE_FLOOR_FRICTION_ACCELERATION,
        "bomb_thump_out_speed": 1000,
    }

    WALK_SPEED = 120



class GameMap(object):
    TILE_SIZE = 256
    ONE_SCREEN_DISTANCE_WIDTH = TILE_SIZE * 4
    ONE_SCREEN_DISTANCE_HEIGHT = TILE_SIZE * 6
    CHAPTERS = ["1", "2", "3", "4", "5"]



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



class Food(object):
    IS_BLOCK = False
    IS_VIEW_BLOCK = False
    IS_ELIMINABLE = True
    ELIMINATION_TYPE = cfg.StaticObject.ELIMINATION_TYPE_FOOD



class RoastChicken(Food):
    NAME = "RoastChicken"
    IMAGE_KEY = "food"
    IMAGE_RECT = (192, 192, 64, 64)
    POS_RECT_DELTA_Y = 8
    AREA_RECT = (0, 0, 32, 32)
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class Omelette(Food):
    NAME = "Omelette"
    IMAGE_KEY = "food"
    IMAGE_RECT = (192, 128, 64, 64)
    POS_RECT_DELTA_Y = 8
    AREA_RECT = (0, 0, 32, 32)
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class BreadBasket(Food):
    NAME = "BreadBasket"
    IMAGE_KEY = "food"
    IMAGE_RECT = (64, 128, 64, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 32, 32)
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class Salad(Food):
    NAME = "Salad"
    IMAGE_KEY = "food"
    IMAGE_RECT = (192, 64, 64, 64)
    POS_RECT_DELTA_Y = 16
    AREA_RECT = (0, 0, 32, 32)
    RECOVER_HP = 100
    SHADOW_INDEX = 3
    SHADOW_RECT_DELTA_Y = 12



class Wine(Food):
    NAME = "Wine"
    IMAGE_KEY = "food"
    IMAGE_RECT = (0, 160, 32, 64)
    POS_RECT_DELTA_Y = 24
    AREA_RECT = (0, 0, 16, 16)
    RECOVER_HP = 50
    SHADOW_INDEX = 0
    SHADOW_RECT_DELTA_Y = 16



class WayPoint(object):
    STEP_WIDTH = 32
    BOUNDING_BOX_RECT = (0, 0, STEP_WIDTH * 2, STEP_WIDTH * 2)



class BlockPoint(object):
    STEP_WIDTH = 32



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
    HERO_HEAD_IMAGE_KEY = "%s_head" % CONFIG["hero"]

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
        "hero_exp": Font.ARIAL_BOLD_12.render("EX", True, pygame.Color("white")),
    }
    LEVEL_TITLE_FONT = Font.ARIAL_BOLD_12
    LEVEL_TITLE_COLOR = pygame.Color("white")

    # health point related
    SPRITE_HP_COLORS = {
        cfg.HpStatus.HEALTHY: pygame.Color(0, 128, 0),
        cfg.HpStatus.WOUNDED: pygame.Color(128, 128, 0),
        cfg.HpStatus.DANGER: pygame.Color(128, 0, 0),
        cfg.HpStatus.DIE: pygame.Color(128, 128, 128),
    }
    SPRITE_BAR_BG_COLOR = pygame.Color(0, 0, 0, 224)
    HERO_ALL_BAR_SIZE = (100, 10)

    # hp related
    HERO_HP_TITLE_BLIT_POS = (84, 10)
    HERO_HP_BLIT_POS = (104, 12)
    # mp related
    HERO_MP_COLOR = pygame.Color(0, 128, 128),
    HERO_MP_TITLE_BLIT_POS = (84, 26)
    HERO_MP_BLIT_POS = (104, 28)
    # sp related
    HERO_SP_COLOR = pygame.Color(0, 64, 128),
    HERO_SP_TITLE_BLIT_POS = (84, 42)
    HERO_SP_BLIT_POS = (104, 44)
    # exp related
    HERO_EXP_COLOR = pygame.Color(128, 128, 0)
    HERO_EXP_TITTLE_BLIT_POS = (84, 58)
    HERO_EXP_BLIT_POS = (104, 60)
    # level related
    HERO_LEVEL_BLIT_POS = (84, 74)

    ENEMY_HP_BAR_SIZE = (50, 5)

    HERO_PANEL_RECT = (0, 0, 144, 56)
    HERO_PANEL_SCALE_SIZE = (216, 92)
    HERO_PANEL_BLIT_POS = (2, 2)
    HERO_HEAD_SIZE = (128, 128)
    HERO_HEAD_BLIT_POS = (-20, -39)

    # Renne magic skill icons
    MAGIC_SKILL_1_ICON_IMAGE_KEY = "e4"
    MAGIC_SKILL_2_ICON_IMAGE_KEY = "e4"
    MAGIC_SKILL_3_ICON_IMAGE_KEY = "e4"
    MAGIC_SKILL_4_ICON_IMAGE_KEY = "e4"
    SKILL_ICON_FRAME_IMAGE_KEY = "status3"

    MAGIC_SKILL_1_ICON_RECT = (64, 64, 32, 32)
    MAGIC_SKILL_2_ICON_RECT = (128, 64, 32, 32)
    MAGIC_SKILL_3_ICON_RECT = (192, 64, 32, 32)
    MAGIC_SKILL_4_ICON_RECT = (96, 64, 32, 32)
    SKILL_CD_MASK_COLOR = pygame.Color(128, 128, 128, 128)
    SKILL_ICON_FRAME_RECT = (36, 228, 24, 24)
    SKILL_ICON_SIZE = (32, 32)

    MAGIC_SKILL_1_ICON_BLIT_POS = (8, 100)
    MAGIC_SKILL_2_ICON_BLIT_POS = (58, 100)
    MAGIC_SKILL_3_ICON_BLIT_POS = (108, 100)
    MAGIC_SKILL_4_ICON_BLIT_POS = (158, 100)

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

    LEVEL_UP_WORDS_COLOR = pygame.Color("yellow")
    LEVEL_UP_WORDS_FONT = Font.MSYH_32
    LEVEL_UP_WORDS_SHOW_TIME = 1.5
    LEVEL_UP_WORDS_VEC_Z = 60

    NO_MANA_WORDS_COLOR = pygame.Color("blue")
    NO_MANA_WORDS_FONT = Font.MSYH_16
    NO_MANA_WORDS_SHOW_TIME = 0.8
    NO_MANA_WORDS_VEC_Z = 20

    NO_CD_WORDS_COLOR = pygame.Color("blue")
    NO_CD_WORDS_FONT = Font.MSYH_16
    NO_CD_WORDS_SHOW_TIME = 0.8
    NO_CD_WORDS_VEC_Z = 20

    # weaken status
    MP_SP_DOWN_WORDS_COLOR = pygame.Color("black")
    MP_SP_DOWN_WORDS_FONT = Font.ARIAL_BLACK_16
    MP_SP_DOWN_WORDS_SHOW_TIME = 0.5
    MP_SP_DOWN_WORDS_BLIT_HEIGHT_OFFSET = 35
    MP_SP_DOWN_WORDS_BLIT_X_SIGMA = 20
    MP_SP_DOWN_WORDS_BLIT_Y_SIGMA = 10
    MP_SP_DOWN_WORDS_POS_MOVE_RATE = (0, 20)

    SPD_UP_IMAGE_KEY = "status"
    SPD_UP_RECT = (64, 240, 16, 16)

    SPD_DOWN_IMAGE_KEY = "status"
    SPD_DOWN_RECT = (80, 240, 16, 16)

    POISON_IMAGE_KEY = "status"
    POISON_RECT = (0, 224, 16, 16)



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
        "per_hit": 5,
        "per_kill": 50,
        "per_n_kill": 10,
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

    CHAPTER_NEXT = Font.MSYH_32.render(u"按回车继续", True, pygame.Color("gray"))
    CHAPTER_NEXT_BLIT_Y = 500

    CHAPTER_AGAIN = Font.MSYH_32.render(u"按回车重来", True, pygame.Color("gray"))
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
    LOADING_WORD = Font.MSYH_24.render(u"游戏加载中...", True, pygame.Color("white"))
    LOADING_WORD_BLIT_POS = (840, 700)

    ALL = ("1", "2", "3", "4", "5")

    WIN_CONDITION_NONE = 0
    WIN_CONDITION_ALL_ENEMY_DIE = 1
    WIN_CONDITION_BOSS_DIE = 2

    WIN_CONDITION = {
        "1": WIN_CONDITION_ALL_ENEMY_DIE,
        "2": WIN_CONDITION_ALL_ENEMY_DIE,
        "3": WIN_CONDITION_ALL_ENEMY_DIE,
        "4": WIN_CONDITION_ALL_ENEMY_DIE,
        "5": WIN_CONDITION_BOSS_DIE,
        "999": WIN_CONDITION_ALL_ENEMY_DIE,
        "998": WIN_CONDITION_ALL_ENEMY_DIE,
    }



class StartGame(object):
    PICTURE_IMAGE_KEY = "start_game_%s" % CONFIG["hero"]
    PICTURE_FADE_IN_TIME = 2 # in second unit, show up the picture
    PICTURE_BLIT_Y = 10



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



class DeadMode(object):
    MAP_CHAPTER = "deadmode"
    ADD_ENEMY_TIME_DELTA = 3
    ENEMY_ADD_INIT_NUM = 10
    ENEMY_ADD_DELTA = 5
    ENEMY_ADD_MAX = 50
    ENEMY_LEFT_INFO_BLIT_POS = (780, 720)
    CURRENT_ROUND_INFO_BLIT_POS = (40, 720)



class MapEditor(object):
    STEP_WIDTH = 8
    SCREEN_MOVE_SPEED = 400

    KEY_STATIC_OBJECT = K_1
    KEY_ENEMY = K_2
    KEY_AMBUSH = K_3
    KEY_ERASE_SELECTED_OBJECT = K_e
    KEY_TURN_DIRECTION = K_t
    KEY_CTRL_SAVE = K_s
    KEY_ALT_SWITCH_POS = K_p
    KEY_ALT_SWITCH_AREA = K_a
    KEY_ALT_SWITCH_WAYPOINT = K_z
    KEY_ALT_SWITCH_BLOCK_POINT = K_x



class Music(object):
    BACKGROUND_VOLUME = 0.4
    SOUND_VOLUME = 0.2
    START_GAME_KEY = "start_game"
    END_GAME_KEY = "end_game"
    CHAPTER_KEY_PREFIX = "chapter_"
    HERO_WIN_KEY = "%s_win" % CONFIG["hero"]
    HERO_LOSE_KEY = "%s_lose" % CONFIG["hero"]



class Sound(object):
    RENNE_ATTACKS = ("renne_attack", "renne_attack2", "renne_attack3", "attack0")
    RENNE_ATTACKS2 = ("renne_attack", "renne_attack2", "renne_attack3")
    RENNE_WIN = "renne_win"

    JOSHUA_ATTACKS = ("joshua_attack1", "joshua_attack2", "joshua_attack3", "joshua_attack4")
    JOSHUA_BIG_SKILL = "joshua_big_skill"

    SWORD_HITS = ("attack_hit", "attack_hit2", "attack_hit5")

    ENEMY_ATTACK_HITS = ("attack_hit", "attack_hit2", "attack_hit3")

    LEONHARDT_ATTACKS = ("leonhardt_attack", "leonhardt_attack2", "leonhardt_attack3", 
        "leonhardt_attack4")



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

    RENNE_DIZZY_LEAF_IMAGE_KEY = "e8"
    RENNE_DIZZY_LEAF_RECT = (0, 0, 32, 32)

    DEATH_COIL_IMAGE_KEY = "e1"
    DEATH_COIL_RECT = (128, 192, 128, 64)
    DEATH_COIL_SHADOW_INDEX = 0
    DEATH_COIL_SHADOW_RECT_DELTA_Y = 20

    ICE_IMAGE_KEY = "e10"
    ICE_FOG1_RECT = (0, 0, 64, 64)
    ICE_FOG2_RECT = (64, 0, 64, 64)
    ICE_FOG_RADIUS = 32
    ICE_FOG_DX = 32
    ICE_FOG_DY = 32
    ICE_BLOCK1_RECT = (128, 0, 64, 64)
    ICE_BLOCK1_RADIUS = 32
    ICE_BLOCK1_DX = 32
    ICE_BLOCK1_DY = 32
    ICE_COLUMN_RECT = (192, 0, 64, 128)
    ICE_COLUMN_RADIUS = 32
    ICE_COLUMN_DX = 32
    ICE_COLUMN_DY = 106

    HELL_CLAW_IMAGE_KEY = "e1"
    HELL_CLAW_RECT = (0, 184, 128, 72)
    HELL_CLAW_SHADOW_INDEX = 1
    HELL_CLAW_SHADOW_RECT_DELTA_Y = 18

    DEATH_DOMAIN_IMAGE_KEY = "e8"
    DEATH_DOMAIN_SIGN_RECT = (64, 64, 128, 128)
    DEATH_DOMAIN_SIGN_DX = 64
    DEATH_DOMAIN_SIGN_DY = 224
    DEATH_DOMAIN_SWORD_RECT = (192, 0, 64, 160)
    DEATH_DOMAIN_SWORD_DX = 32
    DEATH_DOMAIN_SWORD_DY = 128

    BOMB_IMAGE_KEY = "e2"
    BOMB_RECT = (0, 64, 192, 64)
    BOMB_RADIUS = 32
    BOMB_RATE = 6

    POISON_IMAGE_KEY = "e6"
    POISON_RECT1 = (0, 32, 96, 32)
    POISON_RECT2 = (0, 192, 128, 64)
    POISON_RECT3 = (128, 128, 128, 128)

    POISON_FOG_IMAGE_KEY = "e7"
    POISON_FOG_RECT = (160, 32, 32, 32)
    POISON_FOG_GEN_NUM = 8
    POISON_FOG_VEC_Z = 15

    BLOOD_IMAGE_KEY = "e9"
    BLOOD_RECT_LIST = (
        (0, 32, 32, 32),
        (32, 32, 32, 32),
        (64, 32, 32, 32),
        (64, 192, 32, 32),
        (64, 224, 32, 32),
        (96, 224, 32, 32),
    )
    BLOOD_LIFE_TIME = 6

    BOMB2_IMAGE_KEY = "e5"

    GRENADE_IMAGE_KEY = "e7"
    GRENADE_RECT = (224, 0, 32, 32)
    GRENADE_RADIUS = 16
    GRENADE_DX = 16
    GRENADE_DY = 16
    GRENADE_VX_LOSS_RATE = 0.8
    GRENADE_VY_LOSS_RATE = 0.5
    GRENADE_LAND_HEIGHT_THRESHOLD = 5

    BLINK_RATE = 256
    BLINK_DEPTH_SECTION = (32, 128)

    BLINK_RATE2 = 128
    BLINK_DEPTH_SECTION2 = (0, 96)

    BLINK_RATE3 = 1024
    BLINK_DEPTH_SECTION3 = (0, 192)

    WHITE_CIRCLE_IMAGE_KEY = "e7"
    WHITE_CIRCLE_RECT = (128, 0, 32, 32)
    WHITE_CIRCLE_POS_DELTA = 50
    WHITE_CIRCLE_GEN_NUM = 10
    WHITE_CIRCLE_LIFE_MEAN = 1.5
    WHITE_CIRCLE_LIFE_SIGMA = 0.5
    WHITE_CIRCLE_PRE_HIDE_TIME_MEAN = 0.5
    WHITE_CIRCLE_PRE_HIDE_TIME_SIGMA = 0.5
    WHITE_CIRCLE_Z_MEAN = 20
    WHITE_CIRCLE_Z_SIGMA = 10
    WHITE_CIRCLE_VEC_Z_MEAN = 40
    WHITE_CIRCLE_VEC_Z_SIGMA = 10

    THUMP_WORD = u"重击!"
    THUMP_WORD_FONT = Font.MSYH_24
    THUMP_WORD_COLOR = pygame.Color("gold")
    THUMP_WORD_SHOW_TIME = 0.5
    THUMP_WORD_DY = 50

    MP_BURN_WORD = u"法力燃烧!"
    MP_BURN_WORD_FONT = Font.MSYH_24
    MP_BURN_WORD_COLOR = pygame.Color("black")
    MP_BURN_WORD_SHOW_TIME = 0.5
    MP_BURN_WORD_DY = 50

    POISON_WORD = u"九阴白骨爪!"
    POISON_WORD_FONT = Font.MSYH_24
    POISON_WORD_COLOR = pygame.Color("green")
    POISON_WORD_SHOW_TIME = 0.5
    POISON_WORD_DY = 50

    WHIRLWIND_WORD = u"旋风斩!"
    WHIRLWIND_WORD_FONT = Font.MSYH_24
    WHIRLWIND_WORD_COLOR = pygame.Color("blue")
    WHIRLWIND_WORD_SHOW_TIME = 0.8
    WHIRLWIND_WORD_DY = 50



class Ammo(object):
    ARROW_SHADOW_INDEX = 2
    ARROW_SHADOW_DY = 15

    ARROW_IMAGE_KEY = "arrow"
    ARROW_WIDTH = 64
    ARROW_HEIGHT = 32



class Ambush(object):
    SURROUND_AREA_WIDTH = 300
    ENTER_AREA_WIDTH = 100

    APPEAR_TYPE_TOP_DOWN_SPEED = 120
    APPEAR_TYPE_TOP_DOWN_HEIGHT_RAND_RANGE = (40, 90)
    APPEAR_TYPE_TOP_DOWN_INIT_DELAY_RAND_RANGE = (0.5, 1)
    APPEAR_TYPE_TOP_DOWN_FINISH_DELAY = 1



######### mapping for factory ########
# control all objects in list, their order will detemine the attribute "ID" of their own
SPRITE_SETTING_LIST = [
    SkeletonWarrior,
    CastleWarrior,
    SkeletonArcher,
    LeonHardt,
    ArmouredShooter,
    SwordRobber,
    GanDie,
    Ghost,
    TwoHeadSkeleton,
    Werwolf,
    SilverTentacle,
    Robot,
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
Joshua.ID = 1024
Joshua.GAME_OBJECT_TYPE = cfg.GameObject.TYPE_DYNAMIC
for i, cls in enumerate(SPRITE_SETTING_LIST):
    cls.ID = i + 1
    cls.GAME_OBJECT_TYPE = cfg.GameObject.TYPE_DYNAMIC
for i, cls in enumerate(STATIC_OBJECT_SETTING_LIST):
    cls.ID = i + 1
    cls.GAME_OBJECT_TYPE = cfg.GameObject.TYPE_STATIC


SPRITE_SETTING_MAPPING = dict((cls.ID, cls) for cls in SPRITE_SETTING_LIST)
STATIC_OBJECT_SETTING_MAPPING = dict((cls.ID, cls) for cls in STATIC_OBJECT_SETTING_LIST)

COMMON_MONSTER_ID_LIST = [k for k in SPRITE_SETTING_MAPPING if k not in \
    (Renne.ID, Joshua.ID, LeonHardt.ID)]

FOOD_ID_LIST = [v.ID for v in STATIC_OBJECT_SETTING_LIST \
    if v.IS_ELIMINABLE and v.ELIMINATION_TYPE == cfg.StaticObject.ELIMINATION_TYPE_FOOD]



########### resource mapping ###########
RENNE_IMAGE_FILENAME = "renne.png"

SPRITE_FRAMES = {
    # {sprite_id: (folder, {sprite_action: (image_filename, frame_num, frame_rate), ...}), ...}
    Renne.ID: ("renne", {
        cfg.RenneAction.STAND: ("stand_8.png", 8, 12),
        cfg.RenneAction.WALK: ("walk_8.png", 8, 14),
        cfg.RenneAction.RUN: ("run_8.png", 8, 16),
        cfg.RenneAction.ATTACK: ("attack_14.png", 14, 16),
        cfg.RenneAction.WIN: ("win_31.png", 31, 14),
        cfg.RenneAction.REST: ("rest_4.png", 4, 8),
        cfg.RenneAction.SKILL: ("skill_2.png", 2, 2),
        cfg.RenneAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    Joshua.ID: ("joshua", {
        cfg.JoshuaAction.STAND: ("stand_8.png", 8, 12),
        cfg.JoshuaAction.WALK: ("run_8.png", 8, 14),
        cfg.JoshuaAction.RUN: ("run_8.png", 8, 16),
        cfg.JoshuaAction.ATTACK: ("attack1_13.png", 13, 18),
        cfg.JoshuaAction.ATTACK2: ("attack2_14.png", 14, 22),
        cfg.JoshuaAction.SKILL: ("skill_10.png", 10, 16),
        cfg.JoshuaAction.BIG_SKILL: ("big_skill_38.png", 38, 16),
        cfg.JoshuaAction.KNEEL: ("kneel_4.png", 4, 10),
        cfg.JoshuaAction.REST: ("rest_4.png", 4, 8),
        cfg.JoshuaAction.ROAR: ("roar_2.png", 2, 4),
        cfg.JoshuaAction.UNDER_THUMP: ("under_thump.png", 1, 0),
        cfg.JoshuaAction.WIN: ("win_34.png", 34, 14),
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
        cfg.LeonHardtAction.WALK: ("walk_8.png", 8, 14),
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
        cfg.EnemyAction.SKILL: ("skill_2.png", 2, 2),
    }),
    SwordRobber.ID: ("sword_robber", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_7.png", 7, 8),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
    }),
    GanDie.ID: ("gan_die", {
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
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 10),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 10),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 8, 10),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
        cfg.EnemyAction.KNEEL: ("kneel.png", 1, 0),
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
    Robot.ID: ("robot", {
        cfg.EnemyAction.STAND: ("stand_8.png", 8, 12),
        cfg.EnemyAction.WALK: ("walk_8.png", 8, 14),
        cfg.EnemyAction.ATTACK: ("attack_8.png", 5, 12),
        cfg.EnemyAction.UNDER_THUMP: ("under_thump.png", 1, 0),
        cfg.EnemyAction.KNEEL: ("kneel.png", 1, 0),
    }),
}


def gen_res_mapping(filedir):
    res = {}
    for filename in os.listdir(filedir):
        if filename.startswith("."):
            continue
        k = filename.split(".")[0]
        res[k] = filename

    return res

# (folder, {image_key: image_filename, ...})
STATIC_OBJECT_IMAGES = ("static_object", gen_res_mapping(os.path.join("res", "image", "static_object")))

TILE_IMAGES = ("tiles", gen_res_mapping(os.path.join("res", "image", "tiles")))

BASIC_IMAGES = ("basic", gen_res_mapping(os.path.join("res", "image", "basic")))

BATTLE_IMAGES = ("battle", gen_res_mapping(os.path.join("res", "image", "battle")))

CG_IMAGES = ("cg", gen_res_mapping(os.path.join("res", "image", "cg")))

BACKGROUND_MUSICS = ("background", gen_res_mapping(os.path.join("res", "music", "background")))

SOUND_EFFECT = ("sound", gen_res_mapping(os.path.join("res", "music", "sound")))

EFFECT = ("effect", gen_res_mapping(os.path.join("res", "image", "effect")))
