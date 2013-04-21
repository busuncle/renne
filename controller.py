from gameobjects.vector2 import Vector2
import math
import os
from time import time
from random import randint, choice, gauss, random
import etc.constant as cfg
import etc.setting as sfg
import pathfinding
from base.util import cos_for_vec, Timer



########### some tools #########################
def cal_face_direct(start_point, end_point):
    best_direct = None
    cos_min = -1
    vec_to_target = Vector2.from_points(start_point, end_point)
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



class Steerer(object):
    def __init__(self, sprite):
        self.sprite = sprite

    def path_smoothing(self, coord_list):
        # coord_list will be a list containing the path goes *backwards*, that means:
        # [last_coord, last_coord_but_one, ..., second_coord, first_coord]
        new_coord_list = []
        direct_list = []

        # so looping backwards using list.pop, that will produce a new sequence-order coord-list
        new_coord_list.append(coord_list.pop())
        old_direct = None
        while coord_list:
            next_coord = coord_list.pop()
            dx = next_coord[0] - new_coord_list[-1][0]
            dy = next_coord[1] - new_coord_list[-1][1]
            # make both dx and dy be in [-1.0, 1.0], as to decide the direction
            dx = min(max(dx, -1.0), 1.0)
            dy = min(max(dy, -1.0), 1.0)

            next_direct = cfg.Direction.VEC_TO_DIRECT[(dx, dy)]
            if next_direct != old_direct:
                old_direct = next_direct
                new_coord_list.append(next_coord)
                direct_list.append(next_direct)    
            else:
                new_coord_list[-1] = next_coord

        # because list only has pop method, 
        # so reverse the 2 lists will make it convinient for steer
        new_coord_list.reverse()
        direct_list.reverse()
        return new_coord_list, direct_list


    def init(self, coord_list):
        if coord_list is None or len(coord_list) == 0:
            self.is_ok = False
            return

        self.is_ok = True
        self.coord_list, self.direct_list = self.path_smoothing(coord_list)
        self.next_coord = self.coord_list.pop()
        self.cur_direct = None
        self.delta = 2
        self.is_end = False


    def run(self):
        sp = self.sprite
        dx = self.next_coord[0] - sp.pos.x 
        dy = self.next_coord[1] - sp.pos.y

        if (abs(dx) < self.delta and abs(dy) < self.delta):
            # reach target coord, try next
            if len(self.coord_list) == 0:
                # reach the end
                self.is_end = True
            else:
                self.next_coord = self.coord_list.pop()
                self.cur_direct = self.direct_list.pop()
        
        if self.cur_direct:
            sp.direction = self.cur_direct
            sp.key_vec.x, sp.key_vec.y = cfg.Direction.DIRECT_TO_VEC[sp.direction]
        else:
            sp.key_vec.x = sp.key_vec.y = 0.0
            if dx > self.delta:
                sp.key_vec.x = 1.0
            if dx < -self.delta:
                sp.key_vec.x = -1.0
            if dy > self.delta:
                sp.key_vec.y = 1.0
            if dy < -self.delta:
                sp.key_vec.y = -1.0

            sp.direction = cfg.Direction.VEC_TO_DIRECT.get(sp.key_vec.as_tuple(), sp.direction)



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
        self.states = {}
        self.active_state = None
        self.last_state = None
        self.timer = Timer(tick)
        self.timer.begin()


    def add_state(self, state):
        self.states[state.id] = state


    def run(self):
        new_state_id = None
        # ai event tick, interrupt event will trigger condition calculation at once
        if self.sprite.brain.interrupt or self.timer.exceed():
            self.timer.begin()
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
    def __init__(self, sprite, ai, waypoints):
        self.sprite = sprite
        self.ai = ai
        self.target = None
        self.destination = None
        self.path = None
        self.interrupt = False
        self.persistent = False
        self.actions = ()

        self.state_machine = StateMachine(sprite, ai.TICK)

        stay_state = SpriteStay(sprite, ai)
        patrol_state = SpritePatrol(sprite, ai)
        chase_state = SpriteChase(sprite, ai, waypoints)
        offence_state = SpriteOffence(sprite, ai)

        self.state_machine.add_state(stay_state)
        self.state_machine.add_state(patrol_state)
        self.state_machine.add_state(chase_state)
        self.state_machine.add_state(offence_state)

        # initial the sprite state, mostly, a "STAY" state works well
        self.state_machine.set_state(cfg.SpriteState.STAY)


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
        self.enter_timer = Timer()


    def enter(self, last_state):
        self.enter_timer.begin(gauss(self.ai.STAY_TIME_MU, self.ai.STAY_TIME_SIGMA))
        # turn for a random direction if the last state is the same "stay"
        if last_state and last_state.id == cfg.SpriteState.STAY \
            and happen(self.ai.STAY_CHANGE_DIRECTION_PROB):
            self.sprite.direction = choice(cfg.Direction.ALL)   # a random direction from "all"

        if happen(self.ai.EMOTION_SILENT_PROB):
            self.sprite.set_emotion(cfg.SpriteEmotion.SILENT)


    def send_actions(self):
        return (cfg.EnemyAction.LOOKOUT, cfg.EnemyAction.STAND)


    def check_conditions(self):
        sp = self.sprite
        if sp.brain.target is not None:
            # discover a target
            if sp.attacker.chance(sp.brain.target):
                #print "to attack"
                return cfg.SpriteState.OFFENCE

            return cfg.SpriteState.CHASE

        if self.enter_timer.exceed():
            if happen(self.ai.STAY_TO_PATROL_PROB):
                #print "stay to patrol"
                return cfg.SpriteState.PATROL
            else:
                return cfg.SpriteState.STAY


    def exit(self):
        self.enter_timer.clear()



class SpritePatrol(State):
    def __init__(self, sprite, ai):
        super(SpritePatrol, self).__init__(cfg.SpriteState.PATROL)
        self.sprite = sprite
        self.ai = ai
        self.enter_timer = Timer()


    def choose_a_backside_direction(self, current_direction):
        total = cfg.Direction.TOTAL
        opposite_direction = (current_direction + 4) % total
        return choice([(opposite_direction - 1) % total, opposite_direction,
            (opposite_direction + 1) % total])


    def enter(self, last_state):
        self.enter_timer.begin(gauss(self.ai.WALK_TIME_MU, self.ai.WALK_TIME_SIGMA))
        self.sprite.direction = self.choose_a_backside_direction(self.sprite.direction)

    
    def send_actions(self):
        return (cfg.EnemyAction.LOOKOUT, cfg.EnemyAction.WALK)


    def check_conditions(self):
        sp = self.sprite
        if sp.brain.target is not None:
            if sp.attacker.chance(sp.brain.target):
                #print "patrol to attack"
                return cfg.SpriteState.OFFENCE

            #print "patrol to chase"
            return cfg.SpriteState.CHASE

        if sp.brain.interrupt:
            sp.brain.interrupt = False
            return cfg.SpriteState.STAY

        if self.enter_timer.exceed():
            return cfg.SpriteState.STAY


    def exit(self):
        self.enter_timer.clear()



class SpriteChase(State):
    def __init__(self, sprite, ai, waypoints):
        super(SpriteChase, self).__init__(cfg.SpriteState.CHASE)
        self.sprite = sprite
        self.ai = ai
        self.pathfinder = pathfinding.Astar(sprite, waypoints)
        self.steerer = Steerer(sprite)
        self.enter_timer = Timer()


    def add_noise_to_dest(self, target_pos):
        pos = target_pos.copy()
        pos.x = gauss(pos.x, sfg.WayPoint.STEP_WIDTH)
        pos.y = gauss(pos.y, sfg.WayPoint.STEP_WIDTH)
        return pos
        

    def enter(self, last_state):
        sp = self.sprite
        if last_state and last_state.id in (cfg.SpriteState.STAY, cfg.SpriteState.PATROL):
            # discover hero right now, record the time for action delay
            self.enter_timer.begin(self.ai.CHASE_GO_DELAY_TIME)
            # set corresponding emotion
            sp.set_emotion(cfg.SpriteEmotion.ALERT)

        sp.direction = cal_face_direct(sp.pos.as_tuple(), sp.brain.target.pos.as_tuple())
        self.target_move_threshold = sp.brain.target.setting.RADIUS * 4
        sp.brain.destination = self.add_noise_to_dest(sp.brain.target.pos)
        path = self.pathfinder.find(sp.brain.destination.as_tuple(), sp.setting.ATTACK_RANGE)
        self.steerer.init(path)


    def send_actions(self):
        if self.enter_timer.is_begin() and not self.enter_timer.exceed():
            # delay chase action for a more real effect
            return (cfg.EnemyAction.STAND, )

        if self.steerer.is_ok:
            self.steerer.run()
            if not self.steerer.is_end:
                return (cfg.EnemyAction.STEER, )

        return (cfg.EnemyAction.STAND, )


    def check_conditions(self):
        sp = self.sprite

        distance_to_target = sp.pos.get_distance_to(sp.brain.target.pos)
        if sp.attacker.chance(sp.brain.target):
            #print "to attack"
            return cfg.SpriteState.OFFENCE

        elif sp.setting.ATTACK_RANGE < distance_to_target <= sp.setting.CHASE_RANGE:
            target_move = sp.brain.destination.get_distance_to(sp.brain.target.pos)
            if target_move > self.target_move_threshold or self.steerer.is_end:
                #print "chase to chase"
                return cfg.SpriteState.CHASE
        else:
            # lose target
            #print "lose target"
            sp.brain.target = None
            sp.set_emotion(cfg.SpriteEmotion.CHAOS)
            return cfg.SpriteState.STAY


    def exit(self):
        self.sprite.brain.destination = None
        self.enter_timer.clear()



class SpriteOffence(State):
    def __init__(self, sprite, ai):
        super(SpriteOffence, self).__init__(cfg.SpriteState.OFFENCE)
        self.sprite = sprite
        self.ai = ai
        self.enter_timer = Timer()

    def enter(self, last_state):
        sp = self.sprite
        sp.brain.persistent = True
        sp.direction = cal_face_direct(sp.pos.as_tuple(), sp.brain.target.pos.as_tuple())
        self.enter_timer.begin(gauss(self.ai.OFFENCE_GO_DELAY_TIME_MU, self.ai.OFFENCE_GO_DELAY_TIME_SIGMA))


    def send_actions(self):
        if not self.enter_timer.exceed():
            # add delay time for attack
            return (cfg.EnemyAction.STAND, )

        sp = self.sprite
        return (cfg.EnemyAction.ATTACK, ) if sp.brain.persistent else (cfg.EnemyAction.STAND, )


    def check_conditions(self):
        sp = self.sprite
        if sp.brain.persistent:
            return 

        if sp.attacker.chance(sp.brain.target):
            return cfg.SpriteState.OFFENCE
        else:
            return cfg.SpriteState.CHASE


    def exit(self):
        self.enter_timer.clear()
        self.sprite.brain.persistent = False
        


if __name__ == "__main__":
    st = Steerer(None)
    coord_list = [(4, 2), (3, 2), (2, 1), (1, 0), (0, 0)]
    #coord_list = [(1, 1), (0, 0)]
    #coord_list = [(0, 0)]
    st.steer_init(coord_list)
    print st.next_coord
    print list(reversed(st.coord_list))
    print map(lambda x: cfg.Direction.DIRECT_TO_MARK[x], reversed(st.direct_list))
