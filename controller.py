from gameobjects.vector2 import Vector2
import etc.constant as cfg
import etc.setting as sfg
from time import time
from random import randint, choice, gauss
import math
from util import cos_for_vec



########### some tools #########################
def cal_face_direct(sprite, target):
    best_direct = sprite.direction
    cos_min = -1
    vec_to_target = Vector2.from_points(sprite.area.center, target.area.center)
    for vec_point, direct in cfg.Direction.VEC_TO_DIRECT.iteritems():
        vec = Vector2(vec_point)

        # cosine law for 2 vectors
        cos_current = cos_for_vec(vec, vec_to_target)
        if cos_current > cos_min:
            cos_min = cos_current
            best_direct = direct

    return best_direct



########### state machine ####################
class State(object):
    def __init__(self, state_id):
        self.id = state_id

    def send_actions(self):
        pass

    def check_conditions(self):
        pass

    def enter(self, last_state):
        pass

    def exit(self):
        pass


class StateMachine(object):
    def __init__(self, sprite):
        self.sprite = sprite
        self.states = {}
        self.active_state = None
        self.last_state = None
        self.last_time = time()


    def add_state(self, state):
        self.states[state.id] = state


    def run(self):
        if self.active_state is None:
            return

        new_state_id = None
        current_time = time()
        # 0.5 seconds for a loop, interrupt event will trigger condition calculation at once
        if self.sprite.brain.interrupt or current_time - self.last_time > 0.5:
            self.last_time = current_time
            new_state_id = self.active_state.check_conditions()
        
        if new_state_id is not None:
            self.set_state(new_state_id)

        self.sprite.brain.actions = self.active_state.send_actions()


    def set_state(self, new_state_id):
        if self.active_state is not None:
            self.last_state = self.active_state
            self.active_state.exit()

        self.active_state = self.states[new_state_id]
        self.active_state.enter(self.last_state)



class SpriteBrain(object):
    def __init__(self, sprite):
        self.sprite = sprite
        self.target = None
        self.destination = None
        self.path = None
        self.interrupt = False
        self.persistent = False
        self.actions = ()

        self.state_machine = StateMachine(sprite)

        stay_state = SpriteStay(sprite)
        patrol_state = SpritePatrol(sprite)
        chase_state = SpriteChase(sprite)
        offence_state = SpriteOffence(sprite)

        self.state_machine.add_state(stay_state)
        self.state_machine.add_state(patrol_state)
        self.state_machine.add_state(chase_state)
        self.state_machine.add_state(offence_state)
        self.state_machine.set_state(cfg.SpriteState.STAY)


    @property
    def active_state_id(self):
        return self.state_machine.active_state.id

    def think(self):
        # call state_machine's kernel method for choosing the action
        self.state_machine.run()



class SpriteStay(State):
    def __init__(self, sprite):
        super(SpriteStay, self).__init__(cfg.SpriteState.STAY)
        self.sprite = sprite


    def enter(self, last_state):
        self.begin_time = time()
        self.stay_time = gauss(1, 0.1)   # stay here for about 1 second
        # turn for a random direction if the last state is the same "stay"
        if last_state and last_state.id == cfg.SpriteState.STAY:
            self.sprite.direction = choice(cfg.Direction.ALL)   # a random direction from "all"
            if randint(0, 1) == 0:
                self.sprite.set_emotion(cfg.SpriteEmotion.SILENT)


    def send_actions(self):
        return (cfg.EnemyAction.LOOKOUT, cfg.EnemyAction.STAND)


    def check_conditions(self):
        sp = self.sprite
        if sp.brain.target is not None:
            # discover a target
            distance_to_target = sp.pos.get_distance_to(sp.brain.target.pos)
            if distance_to_target <= sp.setting.ATTACK_RANGE:
                print "to attack"
                return cfg.SpriteState.OFFENCE

            return cfg.SpriteState.CHASE

        if time() - self.begin_time >= self.stay_time:
            if randint(1, 3) == 1:
                # 1/3 probability turn to patrol
                print "stay to patrol"
                return cfg.SpriteState.PATROL
            else:
                return cfg.SpriteState.STAY


    def exit(self):
        self.begin_time, self.stay_seconds = None, None



class SpritePatrol(State):
    def __init__(self, sprite):
        super(SpritePatrol, self).__init__(cfg.SpriteState.PATROL)
        self.sprite = sprite


    def enter(self, last_state):
        self.begin_time = time()
        self.walk_time = gauss(0.8, 0.1)   # walk straight for about 1 second
        # choose a opposite direction 
        d_num = cfg.Direction.TOTAL
        opp_d = (self.sprite.direction + 4) % d_num
        self.sprite.direction = choice(((opp_d -1) % d_num, opp_d, (opp_d + 1) % d_num))

    
    def send_actions(self):
        return (cfg.EnemyAction.LOOKOUT, cfg.EnemyAction.WALK)


    def check_conditions(self):
        sp = self.sprite
        if sp.brain.target is not None:
            distance_to_target = sp.pos.get_distance_to(sp.brain.target.pos)
            if distance_to_target <= sp.setting.ATTACK_RANGE:
                print "patrol to attack"
                return cfg.SpriteState.OFFENCE

            print "patrol to chase"
            return cfg.SpriteState.CHASE

        if sp.brain.interrupt:
            sp.brain.interrupt = False
            return cfg.SpriteState.STAY

        if time() - self.begin_time >= self.walk_time:
            return cfg.SpriteState.STAY


    def exit(self):
        self.begin_time, self.walk_time = None, None


class SpriteChase(State):
    def __init__(self, sprite):
        super(SpriteChase, self).__init__(cfg.SpriteState.CHASE)
        self.sprite = sprite
        self.see_hero_time = None


    def add_noise_to_dest(self, target_pos):
        pos = target_pos.copy()
        pos.x = gauss(pos.x, sfg.WayPoint.STEP_WIDTH)
        pos.y = gauss(pos.y, sfg.WayPoint.STEP_WIDTH)
        return pos
        

    def enter(self, last_state):
        sp = self.sprite
        if last_state and last_state.id in (cfg.SpriteState.STAY, cfg.SpriteState.PATROL):
            # discover hero right now, record the time for action delay
            self.see_hero_time = time()
            # set corresponding emotion
            sp.set_emotion(cfg.SpriteEmotion.ALERT)

        sp.direction = cal_face_direct(sp, sp.brain.target)
        self.target_move_threshold = sp.brain.target.setting.RADIUS * 4
        sp.brain.destination = self.add_noise_to_dest(sp.brain.target.pos)
        path = sp.pathfinder.find(sp.brain.destination.as_tuple(), sp.setting.ATTACK_RANGE)
        if path and len(path) > 0:
            sp.steerer.steer_init(path)
            self.can_steer = True
        else:
            self.can_steer = False


    def send_actions(self):
        if self.see_hero_time is not None:
            if time() - self.see_hero_time < 0.5:
                # delay chase action for a more real effect
                return (cfg.EnemyAction.STAND, )

        return (cfg.EnemyAction.STEER, ) if self.can_steer else (cfg.EnemyAction.STAND, )


    def check_conditions(self):
        sp = self.sprite

        distance_to_target = sp.pos.get_distance_to(sp.brain.target.pos)

        if distance_to_target <= sp.setting.ATTACK_RANGE:
            print "to attack"
            return cfg.SpriteState.OFFENCE

        elif sp.setting.ATTACK_RANGE < distance_to_target <= sp.setting.CHASE_RANGE:
            target_move = sp.brain.destination.get_distance_to(sp.brain.target.pos)
            if target_move > self.target_move_threshold or sp.steerer.is_end:
                "print chase to chase"
                return cfg.SpriteState.CHASE
        else:
            # lose target
            print "lose target"
            sp.brain.target = None
            sp.set_emotion(cfg.SpriteEmotion.CHAOS)
            return cfg.SpriteState.STAY


    def exit(self):
        self.sprite.brain.destination = None
        self.see_hero_time = None


class SpriteOffence(State):
    def __init__(self, sprite):
        super(SpriteOffence, self).__init__(cfg.SpriteState.OFFENCE)
        self.sprite = sprite

    def enter(self, last_state):
        sp = self.sprite
        sp.brain.persistent = True
        sp.direction = cal_face_direct(sp, sp.brain.target)
        self.enter_time = time()


    def send_actions(self):
        if time() - self.enter_time < 0.2:
            # add delay time for attack
            return (cfg.EnemyAction.STAND, )

        sp = self.sprite
        return (cfg.EnemyAction.ATTACK, ) if sp.brain.persistent else (cfg.EnemyAction.STAND, )


    def check_conditions(self):
        sp = self.sprite
        if sp.brain.persistent:
            return 

        distance_to_target = sp.pos.get_distance_to(sp.brain.target.pos)
        if distance_to_target <= sp.setting.ATTACK_RANGE:
            return cfg.SpriteState.OFFENCE
        else:
            return cfg.SpriteState.CHASE


    def exit(self):
        self.sprite.brain.persistent = False
        

