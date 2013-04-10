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



class SpriteAction(object):
    STAND = 1
    WALK = 2
    RUN = 3
    ATTACK = 4



class HeroAction(SpriteAction):
    WIN = 13



class EnemyAction(SpriteAction):
    UNDER_ATTACK = 21
    DIE = 22
    LOOKOUT = 23
    PATHFINDING = 24
    STEER = 25



class SpriteState(object):
    STAY = 1
    PATROL = 2
    CHASE = 3
    OFFENCE = 4
    ESCAPE = 5


class SpriteStatus(object):
    HEALTHY = 0
    WOUNDED = 1
    DANGER = 2
    DIE = 3


class SpriteEmotion(object):
    NORMAL = 0
    ALERT = 1
    ANGRY = 2
    CHAOS = 3
    SILENT = 4



class SpriteImage(object):
    WIDTH = HEIGHT = 256
    SIZE = [WIDTH, HEIGHT]


class GameStatus(object):
    INIT = 0
    IN_PROGRESS = 1
    HERO_WIN = 2
    HERO_LOSE = 3
    PAUSE = 4


class GameControl(object):
    NEXT = 0
    AGAIN = 1
    MAIN = 2
    QUIT = 3
