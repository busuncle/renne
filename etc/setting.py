import os
import constant as cfg
import pygame
from pygame.locals import *

pygame.init()

FPS = 60
DEBUG_MODE = False



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


class GameRole(object):
    pass


class Renne(GameRole):
    NAME = "Renne"
    HP = 300
    STAMINA = 100
    ATK = 30
    DFS = 5

    STAMINA_COST_RATE = 15
    STAMINA_RECOVERY_RATE = 12
    # sprite radius
    RADIUS = 18 
    # distance from coord to sprite foot
    D_COORD_TO_FOOT = 40

    D_COORD_TO_SHADOW = 50
    SHADOW_INDEX = 1


    FRAME_RATES = {
        cfg.HeroAction.STAND: 12,
        cfg.HeroAction.WALK: 14,
        cfg.HeroAction.RUN: 16,
        cfg.HeroAction.ATTACK: 20,
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
    D_COORD_TO_FOOT = 40
    D_COORD_TO_SHADOW = 60
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
    D_COORD_TO_FOOT = 40
    D_COORD_TO_SHADOW = 60
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
    CHAPTERS = [1, 2]



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



class GameStatus(object):
    NUMBER_RECT = (0, 280, 340, 60)
    NUMBER_SIZE = (34, 60)
    # all words
    WORDS = {
        "hero_hp": pygame.font.SysFont("arial", 12).render("HP", True, pygame.Color("white")),
        "hero_sp": pygame.font.SysFont("arial", 12).render("SP", True, pygame.Color("white")),
        "continue": pygame.font.SysFont("arial", 32).render(
            "press enter to continue", True, pygame.Color("white")),
        "loading": pygame.font.SysFont("arial", 32).render(
            "now loading ...", True, pygame.Color("white")),
        "busuncle_works": pygame.font.SysFont("arial", 32).render(
            "Busuncle's works", True, pygame.Color("white")),
        "the_end": pygame.font.SysFont("arial", 64).render(
            "The End", True, pygame.Color("white")),
    }
    # init status persist 3 seconds
    INIT_PERSIST_TIME = 3
    CHAPTER_PANEL_RECT = (156, 0, 50, 52)
    CHAPTER_PANEL_BLIT_POS = (965, 5)
    CHAPTER_FONT = {"name": "arial", "size": 14, "italic": True, "pre": "CH", "antialias": True, 
        "color": pygame.Color("gray")}
    CHAPTER_INFO_BLIT_POS = (12, 16)
    # health point related
    SPRITE_HP_COLORS = {
        cfg.SpriteStatus.HEALTHY: pygame.Color(0, 128, 0, 128),
        cfg.SpriteStatus.WOUNDED: pygame.Color(128, 128, 0, 128),
        cfg.SpriteStatus.DANGER: pygame.Color(128, 0, 0, 128),
        cfg.SpriteStatus.DIE: pygame.Color(128, 128, 128, 128),
    }
    SPRITE_BAR_BG_COLOR = pygame.Color(0, 0, 0, 128)
    HERO_ALL_BAR_SIZE = (100, 10)
    HERO_HP_TITLE_BLIT_POS = (80, 18)
    HERO_HP_BLIT_POS = (100, 20)
    # stamina point related
    HERO_SP_COLOR = pygame.Color(0, 64, 128, 128),
    HERO_SP_TITLE_BLIT_POS = (80, 33)
    HERO_SP_BLIT_POS = (100, 35)

    HERO_PANEL_RECT = (0, 0, 144, 56)
    HERO_PANEL_SCALE_SIZE = (1.5, 1.66)
    HERO_PANEL_BLIT_POS = (2, 2)
    HERO_HEAD_SIZE = (128, 128)
    HERO_HEAD_BLIT_POS = (-22, -40)

    ENEMY_HP_BAR_SIZE = (50, 5)

    HERO_WIN_PANEL_RECT = (0, 0, 1024, 170)
    HERO_LOSE_PANEL_RECT = (0, 170, 1024, 170)
    HERO_WIN_BLIT_POS = (0, 280)
    HERO_LOSE_BLIT_POS = (0, 280)
    NUMBER_BLIT_POS = (500, 360)

    CONTINUE_BLIT_POS = (650, 700)
    LOADING_BLIT_POS = (780, 700)



class START_GAME(object):
    PICTURE_FADEIN_TIME = 4 # in second unit, show up the picture
    MENU_ON_COLOR = pygame.Color("white")
    MENU_OFF_COLOR = pygame.Color("gray")
    MENU_ON_SIZE = 48
    MENU_OFF_SIZE = 32
    MENU_LIST = ["START", "QUIT"]
    MENU_OPTION_RECT = (0, 0, 256, 64)
    PICTURE_BLIT_Y = 100
    MENU_BLIT_Y = 600



class MapEditor(object):
    SCREEN_MOVE_SPEED = 400



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

#SPRITE_SETTING_MAPPING = {cls.ID: cls for cls in SPRITE_SETTING_LIST}
#STATIC_OBJECT_SETTING_MAPPING = {cls.ID: cls for cls in STATIC_OBJECT_SETTING_LIST}
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
})

BATTLE_IMAGES = ("battle", {
    "renne_head": "renne_head.png",
    "status": "status.png",
    "status2": "status2.png", 
    "status3": "status3.png", 
    "status4": "status4.png", 
})

CG_IMAGES = ("cg", {
    1: "1.png",
    2: "2.png", 
})

