from random import randint, choice, gauss
import etc.constant as cfg
import etc.setting as sfg



class AIBase(object):
    # ai event tick, need not change at most time
    TICK = 0.5


class NormalAI(AIBase):
    # used in gauss function, MU is the mean, SIGMA is the standard deviation
    STAY_TIME_MU = 1
    STAY_TIME_SIGMA = 0.1
    WALK_TIME_MU = 0.8
    WALK_TIME_SIGMA = 0.1

    # the probability(between 0 and 1, both sides include) that give rise an emotion on the sprite
    EMOTION_SILENT_PROB = 0.3

    CHASE_GO_DELAY_TIME = 0.5
    OFFENCE_GO_DELAY_TIME_MU = 0.5
    OFFENCE_GO_DELAY_TIME_SIGMA = 0.1

    STAY_TO_PATROL_PROB = 0.3
