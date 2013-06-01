from random import randint, choice, gauss
from base import constant as cfg
from etc import setting as sfg



class AIBase(object):
    # ai event tick, need not change at most time
    TICK = 0.5
    # when hp drops to 0.5 * full-hp, monster gets angry
    ANGRY_HP_RATIO = 0.5

    # used in gauss function, MU is the mean, SIGMA is the standard deviation
    STAY_TIME_MU = 1
    STAY_TIME_SIGMA = 0.1
    WALK_TIME_MU = 0.8
    WALK_TIME_SIGMA = 0.1



class ShortNormalAI(AIBase):
    # this ai is for some short-distance-attack monster

    CHASE_RANGE = 520

    # the probability(between 0 and 1, both sides include) that give rise an emotion on the sprite
    EMOTION_SILENT_PROB = 0.2

    CHASE_GO_DELAY_TIME = 0.5
    OFFENCE_GO_DELAY_TIME_MU = 0.8
    OFFENCE_GO_DELAY_TIME_SIGMA = 0.1

    STAY_CHANGE_DIRECTION_PROB = 0.5

    # all states transition probability
    STAY_TO_PATROL_PROB = 0.2
    STAY_TO_OFFENCE_PROB = 0.8
    STAY_TO_CHASE_PROB = 0.8

    PATROL_TO_CHASE_PROB = 1

    CHASE_TO_OFFENCE_PROB = 0.8
    CHASE_TO_DEFENCE_PROB = 0.05

    OFFENCE_TO_CHASE_PROB = 0.9

    DEFENCE_TO_OFFENCE_PROB = 0.9
    DEFENCE_TO_CHASE_PROB = 0.8



class LongNormalAI(AIBase):
    # this ai is for some long-distance-attack monster

    CHASE_RANGE = 580

    # the probability(between 0 and 1, both sides include) that give rise an emotion on the sprite
    EMOTION_SILENT_PROB = 0.2

    CHASE_GO_DELAY_TIME = 0.5
    OFFENCE_GO_DELAY_TIME_MU = 1.2
    OFFENCE_GO_DELAY_TIME_SIGMA = 0.1

    STAY_CHANGE_DIRECTION_PROB = 0.5

    # all states transition probability
    STAY_TO_PATROL_PROB = 0.01
    STAY_TO_OFFENCE_PROB = 1
    STAY_TO_CHASE_PROB = 0.2

    PATROL_TO_CHASE_PROB = 0.2

    CHASE_TO_OFFENCE_PROB = 1
    CHASE_TO_DEFENCE_PROB = 0.2

    OFFENCE_TO_CHASE_PROB = 0.1

    DEFENCE_TO_OFFENCE_PROB = 0.9
    DEFENCE_TO_CHASE_PROB = 0.1



class LeonHardtAI(AIBase):

    CHASE_RANGE = 1500

    # the probability(between 0 and 1, both sides include) that give rise an emotion on the sprite
    EMOTION_SILENT_PROB = 0

    CHASE_GO_DELAY_TIME = 0.5
    OFFENCE_GO_DELAY_TIME_MU = 0.5
    OFFENCE_GO_DELAY_TIME_SIGMA = 0.1

    STAY_CHANGE_DIRECTION_PROB = 0

    # all states transition probability
    STAY_TO_PATROL_PROB = 0
    STAY_TO_OFFENCE_PROB = 0.9
    STAY_TO_CHASE_PROB = 0.7

    PATROL_TO_CHASE_PROB = 1

    CHASE_TO_OFFENCE_PROB = 0.9
    CHASE_TO_DEFENCE_PROB = 0.05

    OFFENCE_TO_CHASE_PROB = 0.4

    DEFENCE_TO_OFFENCE_PROB = 0.8
    DEFENCE_TO_CHASE_PROB = 0.4

    # attack method related
    ATTACK_REGULAR_PROB = 0.7
    ATTACK_DEATH_COIL_PROB = 0.3
    ATTACK_HELL_CLAW_PROB = 0.3



class SwordRobberAI(ShortNormalAI):
    STAY_CHANGE_DIRECTION_PROB = 0.1
    STAY_TO_PATROL_PROB = 0.05



class ArmouredShooterAI(LongNormalAI):
    STAY_CHANGE_DIRECTION_PROB = 0.1
    STAY_TO_PATROL_PROB = 0.05



class WerwolfAI(ShortNormalAI):
    STAY_CHANGE_DIRECTION_PROB = 0.001
    STAY_TO_PATROL_PROB = 0



class TwoHeadSkeletonAI(ShortNormalAI):
    STAY_CHANGE_DIRECTION_PROB = 0.001
    STAY_TO_PATROL_PROB = 0



class SilverImpaleAI(ShortNormalAI):
    EMOTION_SILENT_PROB = 0.001
    STAY_CHANGE_DIRECTION_PROB = 0.1

    STAY_TO_OFFENCE_PROB = 0.3
    STAY_TO_CHASE_PROB = 0.3

    CHASE_TO_OFFENCE_PROB = 0.3
    CHASE_TO_DEFENCE_PROB = 0.8

    OFFENCE_TO_CHASE_PROB = 0.3



AI_MAPPING = {
    sfg.SkeletonWarrior.ID: ShortNormalAI,
    sfg.CastleWarrior.ID: ShortNormalAI,
    sfg.SkeletonArcher.ID: LongNormalAI,
    sfg.LeonHardt.ID: LeonHardtAI,
    sfg.ArmouredShooter.ID: ArmouredShooterAI,
    sfg.SwordRobber.ID: SwordRobberAI,
    sfg.SkeletonWarrior2.ID: ShortNormalAI,
    sfg.Ghost.ID: ShortNormalAI,
    sfg.TwoHeadSkeleton.ID: TwoHeadSkeletonAI,
    sfg.Werwolf.ID: WerwolfAI,
    sfg.SilverImpale.ID: SilverImpaleAI,
}
