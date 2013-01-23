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

    TOTAL = 8 # 8 directions totally

    VEC_TO_DIRECT = {
        (-1.0, 0.0): WEST,
        (-1.0, -1.0): NORTH_WEST,
        (0.0, -1.0): NORTH,
        (1.0, -1.0): NORTH_EAST,
        (1.0, 0.0): EAST,
        (1.0, 1.0): SOUTH_EAST,
        (0.0, 1.0): SOUTH,
        (-1.0, 1.0): SOUTH_WEST,
    }

    DIRECT_TO_VEC = dict((v, k) for k, v in VEC_TO_DIRECT.iteritems())



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
