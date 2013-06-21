class Direction(object):
    # NW N NE
    # W     E
    # SW S SE
    # 1 2 3
    # 0   4
    # 7 6 5
    WEST = 0
    NORTH_WEST = 1
    NORTH = 2
    NORTH_EAST = 3
    EAST = 4
    SOUTH_EAST = 5
    SOUTH = 6
    SOUTH_WEST = 7

    TOTAL = 8 # 8 directions totally

    ALL = [
        WEST,
        NORTH_WEST,
        NORTH,
        NORTH_EAST,
        EAST,
        SOUTH_EAST,
        SOUTH,
        SOUTH_WEST,
    ]

    MARK_ALL = [
        "WEST",
        "NORTH_WEST",
        "NORTH",
        "NORTH_EAST",
        "EAST",
        "SOUTH_EAST",
        "SOUTH",
        "SOUTH_WEST",
    ]

    VEC_ALL = [
        (-1.0, 0.0),
        (-1.0, -1.0),
        (0.0, -1.0),
        (1.0, -1.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
        (-1.0, 1.0),
    ]

    DIRECT_TO_VEC = dict(zip(ALL, VEC_ALL))
    VEC_TO_DIRECT = dict(zip(VEC_ALL, ALL))
    DIRECT_TO_MARK = dict(zip(ALL, MARK_ALL))



class GameObject(object):
    TYPE_STATIC = 1
    TYPE_DYNAMIC = 2



class SpriteRole(object):
    HERO = 1
    ENEMY = 2



class SpriteAction(object):
    UNCONTROLLED = -1
    STAND = 1
    WALK = 2
    RUN = 3
    ATTACK = 4
    UNDER_THUMP = 5



class HeroAction(SpriteAction):
    SKILL = 16
    RUN_ATTACK = 17
    REST = 18
    WIN = 19



class EnemyAction(SpriteAction):
    UNDER_ATTACK = 21
    DIE = 22
    LOOKOUT = 23
    PATHFINDING = 24
    STEER = 25



class LeonHardtAction(EnemyAction):
    ATTACK2 = 41
    SKILL1 = 42
    SKILL2 = 43



class SpriteState(object):
    STAY = 1
    PATROL = 2
    CHASE = 3
    OFFENCE = 4
    DEFENCE = 5


class SpriteStatus(object):
    HEALTHY = 0
    WOUNDED = 1
    DANGER = 2
    DIE = 3
    VANISH = 4

    ALIVE = (HEALTHY, WOUNDED, DANGER)



class SpriteEmotion(object):
    NORMAL = 0
    ALERT = 1
    ANGRY = 2
    CHAOS = 3
    SILENT = 4
    STUN = 5
    DIZZY = 6



class SpriteImage(object):
    WIDTH = HEIGHT = 256
    SIZE = [WIDTH, HEIGHT]



class GameStatus(object):
    INIT = 0
    IN_PROGRESS = 1
    HERO_WIN = 2
    HERO_LOSE = 3
    PAUSE = 4
    ENTER_AMBUSH = 5

    STATUS_WITH_MASK = (HERO_WIN, HERO_LOSE, PAUSE)


class GameControl(object):
    NEXT = 0
    AGAIN = 1
    MAIN = 2
    QUIT = 3
    CONTINUE = 4


class Achievement(object):
    DOUBLE_HIT = 1
    TRIBLE_HIT = 2
    # a japanese word, here it's used to descript enemies is like yakitori,
    # and is cook by hero
    YAKITORI = 3    

    DOUBLE_KILL = 11
    TRIBLE_KILL = 12
    ULTRA_KILL = 13
    RAMPAGE = 14



class StaticObject(object):
    STATUS_NORMAL = 0
    STATUS_VANISH = 1

    ELIMINATION_TYPE_FOOD = 1



class Magic(object):
    STATUS_ALIVE = 0 
    STATUS_VANISH = 1



class Ammo(object):
    STATUS_ALIVE = 0
    STATUS_VANISH = 1



class Ambush(object):
    STATUS_INIT = 0
    STATUS_ENTER = 1
    STATUS_FINISH = 2

    APPEAR_TYPE_TOP_DOWN = 1
    APPEAR_TYPE_FADE_IN = 2
    APPEAR_TYPES = {
        APPEAR_TYPE_TOP_DOWN: "top_down",
        APPEAR_TYPE_FADE_IN: "fade_in",
    }
