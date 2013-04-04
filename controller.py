from gameobjects.vector2 import Vector2
import math
import os
from time import time
from random import randint, choice, gauss, random
import etc.constant as cfg
import etc.setting as sfg
import pathfinding
from base.util import cos_for_vec



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


def happen(probability):
    # calculate whether the event will happen according the probability
    assert 0 <= probability <= 1
    return random() <= probability



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
    def __init__(self, sprite, tick):
        self.sprite = sprite
        self.tick = tick
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
        # ai event tick, interrupt event will trigger condition calculation at once
        if self.sprite.brain.interrupt or current_time - self.last_time > self.tick:
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
    waypoints = None
    def __init__(self, sprite, ai):
        self.sprite = sprite
        self.ai = ai
        self.target = None
        self.destination = None
        self.path = None
        self.interrupt = False
        self.persistent = False
        self.actions = ()
        if SpriteBrain.waypoints is None:
            SpriteBrain.waypoints = self.load_waypoints(sprite.game_map.chapter)

        self.state_machine = StateMachine(sprite, ai.TICK)

        stay_state = SpriteStay(sprite, ai)
        patrol_state = SpritePatrol(sprite, ai)
        chase_state = SpriteChase(sprite, ai, SpriteBrain.waypoints)
        offence_state = SpriteOffence(sprite, ai)

        self.state_machine.add_state(stay_state)
        self.state_machine.add_state(patrol_state)
        self.state_machine.add_state(chase_state)
        self.state_machine.add_state(offence_state)
        self.state_machine.set_state(cfg.SpriteState.STAY)


    def load_waypoints(self, chapter):
        res = set()
        fp = open(os.path.join(sfg.WayPoint.DIR, "%s.txt" % chapter))
        for line in fp:
            x, y = line.strip().split("\t")
            res.add((float(x), float(y)))

        return res


    @property
    def active_state_id(self):
        return self.state_machine.active_state.id

    def think(self):
        # call state_machine's kernel method for choosing the action
        self.state_machine.run()



class SpriteStay(State):
    def __init__(self, sprite, ai):
        super(SpriteStay, self).__init__(cfg.SpriteState.STAY)
        self.sprite = sprite
        self.ai = ai


    def enter(self, last_state):
        self.begin_time = time()
        self.stay_time = gauss(self.ai.STAY_TIME_MU, self.ai.STAY_TIME_SIGMA)   
        # turn for a random direction if the last state is the same "stay"
        if last_state and last_state.id == cfg.SpriteState.STAY:
            self.sprite.direction = choice(cfg.Direction.ALL)   # a random direction from "all"
            if happen(self.ai.EMOTION_SILENT_PROB):
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
            if happen(self.ai.STAY_TO_PATROL_PROB):
                print "stay to patrol"
                return cfg.SpriteState.PATROL
            else:
                return cfg.SpriteState.STAY


    def exit(self):
        self.begin_time, self.stay_seconds = None, None



class SpritePatrol(State):
    def __init__(self, sprite, ai):
        super(SpritePatrol, self).__init__(cfg.SpriteState.PATROL)
        self.sprite = sprite
        self.ai = ai


    def choose_a_backside_direction(self, current_direction):
        total = cfg.Direction.TOTAL
        opposite_direction = (current_direction + 4) % total
        return choice([(opposite_direction - 1) % total, opposite_direction,
            (opposite_direction + 1) % total])


    def enter(self, last_state):
        self.begin_time = time()
        self.walk_time = gauss(self.ai.WALK_TIME_MU, self.ai.WALK_TIME_SIGMA)   
        self.sprite.direction = self.choose_a_backside_direction(self.sprite.direction)

    
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
    def __init__(self, sprite, ai, waypoints):
        super(SpriteChase, self).__init__(cfg.SpriteState.CHASE)
        self.sprite = sprite
        self.ai = ai
        self.see_hero_time = None
        self.pathfinder = pathfinding.Astar(sprite, waypoints)


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
        path = self.pathfinder.find(sp.brain.destination.as_tuple(), sp.setting.ATTACK_RANGE)
        if path and len(path) > 0:
            sp.steerer.steer_init(path)
            self.can_steer = True
        else:
            self.can_steer = False


    def send_actions(self):
        if self.see_hero_time is not None:
            if time() - self.see_hero_time < self.ai.CHASE_GO_DELAY_TIME:
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
    def __init__(self, sprite, ai):
        super(SpriteOffence, self).__init__(cfg.SpriteState.OFFENCE)
        self.sprite = sprite
        self.ai = ai

    def enter(self, last_state):
        sp = self.sprite
        sp.brain.persistent = True
        sp.direction = cal_face_direct(sp, sp.brain.target)
        self.enter_time = time()
        self.delay_time = gauss(self.ai.OFFENCE_GO_DELAY_TIME_MU, self.ai.OFFENCE_GO_DELAY_TIME_SIGMA)


    def send_actions(self):
        if time() - self.enter_time < self.delay_time:
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
        

