import os
import constant as cfg
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

    ARIAL_BLACK_28 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 28)
    ARIAL_BLACK_32 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 32)
    ARIAL_BLACK_48 = pygame.font.Font(ARIAL_BLACK_FILEPATH, 48)

    HOLLOW_16 = pygame.font.Font(HOLLOW_FILEPATH, 16)



class Menu(object):
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
        "blit_y": 550,
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
    RUN = K_l
    WIN = K_u



class Screen(object):
    SIZE = [1024, 768]
    INNER_SIZE = [SIZE[0] / 4, SIZE[1] / 4]
    DEFAULT_SCREEN = pygame.display.set_mode(SIZE, HWSURFACE|DOUBLEBUF)
    DEFAULT_SURFACE = pygame.Surface(SIZE).convert_alpha()



class Stuff(object):
    # some common stuff, may be used everywhere if needed
    MASK_ALPHA_128 = pygame.Color(0, 0, 0, 128)



class GameRole(object):
    pass



class Renne(GameRole):
    NAME = "Renne"
    HP = 300
    # stamina
    SP = 100
    ATK = 30
    DFS = 5

    SP_COST_RATE = 15
    SP_RECOVERY_RATE = 12
    # sprite radius
    RADIUS = 18 
    # distance from coord to sprite foot
    POS_RECT_DELTA_Y = 40

    SHADOW_RECT_DELTA_Y = 50
    SHADOW_INDEX = 1


    FRAME_RATES = {
        cfg.HeroAction.STAND: 12,
        cfg.HeroAction.WALK: 14,
        cfg.HeroAction.RUN: 16,
        cfg.HeroAction.ATTACK: 18,
        cfg.HeroAction.WIN: 14,
    }

    FRAME_NUMS = {
        # the number of a frame sheet
        cfg.HeroAction.STAND: 8,
        cfg.HeroAction.WALK: 8,
        cfg.HeroAction.RUN: 8,
        cfg.HeroAction.ATTACK: 14,
        cfg.HeroAction.WIN: 31,
    }

    # move speed, in pixel unit
    WALK_SPEED = 100
    RUN_SPEED = 200

    ATTACK_RANGE = 100
    ATTACK_ANGLE = 90
    ATTACK_CAL_FRAMES = (4, 5)


                
class SkeletonWarrior(GameRole):
    NAME = "SkeletonWarrior"
    HP = 200
    ATK = 40
    DFS = 2

    RADIUS = 24
    HEIGHT = 80
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    FRAME_RATES = {
        cfg.EnemyAction.STAND: 12,
        cfg.EnemyAction.WALK: 14,
        cfg.EnemyAction.ATTACK: 12,
    }

    FRAME_NUMS = {
        cfg.EnemyAction.STAND: 8,
        cfg.EnemyAction.WALK: 8,
        cfg.EnemyAction.ATTACK: 8,
    }

    ATTACK_CAL_FRAMES = (3, 4)

    WALK_SPEED = 160
    ATTACK_RANGE = 60
    ATTACK_ANGLE = 60
    VIEW_RANGE = 380
    VIEW_ANGLE = 120 
    CHASE_RANGE = VIEW_RANGE + 20
    NEARBY_ALLIANCE_RANGE = 300



class CastleWarrior(GameRole):
    NAME = "CastleWarrior" 
    HP = 250
    ATK = 50
    DFS = 3

    RADIUS = 24
    HEIGHT = 82
    POS_RECT_DELTA_Y = 40
    SHADOW_RECT_DELTA_Y = 60
    SHADOW_INDEX = 3

    FRAME_RATES = {
        cfg.EnemyAction.STAND: 12,
        cfg.EnemyAction.WALK: 14,
        cfg.EnemyAction.ATTACK: 12,
    }

    FRAME_NUMS = {
        cfg.EnemyAction.STAND: 8,
        cfg.EnemyAction.WALK: 8,
        cfg.EnemyAction.ATTACK: 8,
    }

    ATTACK_CAL_FRAMES = (3, 4)
    WALK_SPEED = 160
    ATTACK_RANGE = 100
    ATTACK_ANGLE = 40
    VIEW_RANGE = 380
    VIEW_ANGLE = 120 
    CHASE_RANGE = VIEW_RANGE + 20
    NEARBY_ALLIANCE_RANGE = 300



class GameMap(object):
    TILE_SIZE = 256
    ONE_SCREEN_DISTANCE_WIDTH = TILE_SIZE * 4
    ONE_SCREEN_DISTANCE_HEIGHT = TILE_SIZE * 6
    CHAPTERS = [0, 1, 2, 3]



class StaticObject(object):
    pass



class WoodenCase(StaticObject):
    NAME = "WoodenCase"
    IMAGE_KEY = "s1"
    IMAGE_RECT = (64, 64, 48, 64)
    IMAGE_POS_DELTA_Y = -16
    AREA_RECT = (0, 0, 48, 66)
    IS_BLOCK = True
    IS_VIEW_BLOCK = False



class IronCase(StaticObject):
    NAME = "IronCase"
    IMAGE_KEY = "s2"
    IMAGE_RECT = (174, 112, 70, 132)
    IMAGE_POS_DELTA_Y = -36
    AREA_RECT = (0, 0, 70, 124)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True 

    

class ThickGrass(StaticObject):
    NAME = "ThickGrass"
    IMAGE_KEY = "s3"
    IMAGE_RECT = (192, 64, 64, 64)
    IMAGE_POS_DELTA_Y = -26
    AREA_RECT = (0, 0, 64, 64)
    IS_BLOCK = False 
    IS_VIEW_BLOCK = True 


class GrassWall(StaticObject):
    NAME = "GrassWall"
    IMAGE_KEY = "s4"
    IMAGE_RECT = (0, 0, 64, 104)
    IMAGE_POS_DELTA_Y = -36
    AREA_RECT = (0, 0, 64, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True


class StoneWall(StaticObject):
    NAME = "StoneWall"
    IMAGE_KEY = "s5"
    IMAGE_RECT = (192, 0, 64, 160)
    IMAGE_POS_DELTA_Y = - 48
    AREA_RECT = (0, 0, 64, 128)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True


class StoneWall2(StaticObject):
    NAME = "StoneWall2"
    IMAGE_KEY = "s6"
    IMAGE_RECT = (0, 0, 256, 192)
    IMAGE_POS_DELTA_Y = -80
    AREA_RECT = (0, 0, 256, 64)
    IS_BLOCK = True
    IS_VIEW_BLOCK = True


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
    }



class SpriteStatus(object):
    HEALTHY_RATIO_FLOOR = 2.0 / 3
    WOUNDED_RATIO_FLOOR = 1.0 / 3
    DANGER_RATIO_FLOOR = 0

    # all words
    WORDS = {
        "hero_hp": Font.ARIAL_BOLD_12.render("HP", True, pygame.Color("white")),
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
    HERO_HP_TITLE_BLIT_POS = (82, 20)
    HERO_HP_BLIT_POS = (104, 22)

    # stamina point related
    HERO_SP_COLOR = pygame.Color(0, 64, 128, 128),
    HERO_SP_TITLE_BLIT_POS = (82, 35)
    HERO_SP_BLIT_POS = (104, 37)

    ENEMY_HP_BAR_SIZE = (50, 5)

    HERO_PANEL_RECT = (0, 0, 144, 56)
    HERO_PANEL_SCALE_SIZE = (1.5, 1.66)
    HERO_PANEL_BLIT_POS = (2, 2)
    HERO_HEAD_SIZE = (128, 128)
    HERO_HEAD_BLIT_POS = (-20, -38)



class Achievement(object):
    N_KILL_TIMEDELTA = 20   # in second unit

    KILL_ICON_RECT = (224, 0, 32, 32)
    KILL_ICON_BLIT_POS = (220, 10)

    N_HIT_ICON_RECT = (192, 32, 32, 32)
    N_HIT_ICON_BLIT_POS = (360, 10)

    N_KILL_ICON_RECT = (192, 0, 32, 32)
    N_KILL_ICON_BLIT_POS = (500, 10)

    SCORE_RUN_RATE = 20

    KILL_SCORE = {
        "blit_pos": (260, 10),
        "font": Font.HOLLOW_16,
        "color": pygame.Color("gold"),
    }

    N_HIT_SCORE = {
        "blit_pos": (400, 10),
        "font": Font.HOLLOW_16,
        "color": pygame.Color("gold"),
    }

    N_KILL_SCORE = {
        "blit_pos": (540, 10),
        "font": Font.HOLLOW_16,
        "color": pygame.Color("gold"),
    }



class GameStatus(object):
    NUMBER_RECT1 = (0, 280, 340, 60)
    NUMBER_SIZE1 = (34, 60)
    NUMBER_RECT2 = (96, 160, 160, 16)
    NUMBER_SIZE2 = (16, 16)
    BEGIN_NUMBER_BLIT_POS = (500, 360)

    # init status persist 3 seconds
    INIT_PERSIST_TIME = 3

    HERO_WIN_PANEL_RECT = (0, 0, 1024, 170)
    HERO_LOSE_PANEL_RECT = (0, 170, 1024, 170)
    HERO_WIN_BLIT_POS = (0, 280)
    HERO_LOSE_BLIT_POS = (0, 280)



class Chapter(object):
    LOADING_PICTURE_FADE_IN_TIME = 1    # in second unit, show up the picture
    LOADING_WORD = Font.ARIAL_BLACK_28.render("now loading ...", True, pygame.Color("white"))
    LOADING_WORD_BLIT_POS = (760, 700)



class StartGame(object):
    PICTURE_FADE_IN_TIME = 3 # in second unit, show up the picture
    PICTURE_BLIT_Y = 30



class EndGame(object):
    ENDING_FADEIN_TIME = 5
    BUSUNCLE_WORKS = Font.ARIAL_BLACK_32.render("Busuncle's works", True, pygame.Color("white"))
    BUSUNCLE_WORKS_BLIT_Y = 450
    RENNE_IMAGE_BLIT_Y = 360



class MapEditor(object):
    SCREEN_MOVE_SPEED = 400



class Music(object):
    BACKGROUND_VOLUME = 0.4
    SOUND_VOLUME = 0.2



######### mapping for factory ########
# control all objects in list, their order will detemine the attribute "ID" of their own
SPRITE_SETTING_LIST = [
    SkeletonWarrior,
    CastleWarrior,
]

STATIC_OBJECT_SETTING_LIST = [
    WoodenCase,
    IronCase,
    ThickGrass,
    GrassWall,
    StoneWall,
    StoneWall2,
]

# set attribute "ID" for all objects, start from 1, Renne is special for 0
Renne.ID = 0
for i, cls in enumerate(SPRITE_SETTING_LIST):
    cls.ID = i + 1
for i, cls in enumerate(STATIC_OBJECT_SETTING_LIST):
    cls.ID = i + 1

SPRITE_SETTING_MAPPING = dict((cls.ID, cls) for cls in SPRITE_SETTING_LIST)
STATIC_OBJECT_SETTING_MAPPING = dict((cls.ID, cls) for cls in STATIC_OBJECT_SETTING_LIST)


########### resource mapping ###########
SPRITE_FRAMES = {
    # {sprite_id: (folder, {sprite_action: image_filename, ...}), ...}
    0: ("renne", {
        cfg.HeroAction.WALK: "walk_8.png",
        cfg.HeroAction.RUN: "run_8.png",
        cfg.HeroAction.ATTACK: "attack_14.png",
        cfg.HeroAction.STAND: "stand_8.png",
        cfg.HeroAction.WIN: "win_31.png",
    }),
    1: ("skeleton_warrior", {
        cfg.EnemyAction.WALK: "walk_8.png",
        cfg.EnemyAction.STAND: "stand_8.png",
        cfg.EnemyAction.ATTACK: "attack_8.png",
    }),
    2: ("castle_warrior", {
        cfg.EnemyAction.WALK: "walk_8.png",
        cfg.EnemyAction.STAND: "stand_8.png",
        cfg.EnemyAction.ATTACK: "attack_8.png",
    }),
}

# (folder, {image_key: image_filename, ...})
STATIC_OBJECT_IMAGES = ("static_object", {
    "s1": "s1.png",
    "s2": "s2.png", 
    "s3": "s3.png",
    "s4": "s4.png",
    "s5": "s5.png",
    "s6": "s6.png", 
})

# (folder, {image_key: image_filename, ...})
TILE_IMAGES = ("tiles", {
    1: "1.png", 
    2: "2.png",
    3: "3.png", 
    4: "4.png", 
    5: "5.png", 
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
    "icon1": "icon1.png",
})

CG_IMAGES = ("cg", {
    "start_game": "1.png",
    "loading_chapter": "2.png", 
})


BACKGROUND_MUSICS = ("background", {
    "start_game": "start_game.ogg", 
    "end_game": "end_game.ogg", 
    "chapter_1": "chapter_1.ogg",
    "chapter_2": "chapter_2.ogg",
    "chapter_3": "chapter_3.ogg",
})

SOUND_EFFECT = ("sound", {
    "renne_attack": "renne_attack.wav",
    "renne_under_attack": "renne_under_attack.wav",
    "renne_win": "renne_win.wav",
    "attack_hit": "attack_hit.wav",
})
