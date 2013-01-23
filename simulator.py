from util import LineSegment, line_segment_intersect_with_rect, cos_for_vec, manhattan_distance
import constant as cfg
import math
from math import pow, radians, sqrt, tan, cos
from time import time
from gameobjects.vector2 import Vector2
import pygame


class Attacker(object):
    """
    attack related calculation in one attack action
    """

    def __init__(self, sprite):
        self.sprite = sprite
        # a list containing enemies that attacked by the sprite, it have to be cleaned after finsh the attack
        self.hit_list = set()


    def hit(self, enemy):
        self.hit_list.add(id(enemy))
        damage = self.sprite.atk - enemy.dfs
        enemy.attack_receiver.recv(self.sprite, damage)
        print "%s hit %s at %s damage!%s hp: %s" % \
            (self.sprite.name, enemy.name, damage, enemy.name, enemy.hp)


    def finish_attack(self):
        pass



class AttackReceiver(object):
    """
    receive an attack, tell the sprite to do some reaction
    """
    
    def __init__(self, sprite):
        self.sprite = sprite
        self.under_attack = False


    def cal_sprite_status(self, current_hp, full_hp):
        # calculate the sprite status according the current hp and full hp
        if current_hp >= full_hp * 2.0 / 3:
            return cfg.SpriteStatus.HEALTHY
        elif full_hp / 3.0 <= current_hp < full_hp * 2.0 / 3:
            return cfg.SpriteStatus.WOUNDED
        elif 0 < current_hp < full_hp / 3.0:
            return cfg.SpriteStatus.DANGER
        else:
            return cfg.SpriteStatus.DIE


    def recv(self, who, damage):
        old_hp = self.sprite.hp
        self.sprite.hp = max(old_hp - damage, 0)

        self.sprite.status = self.cal_sprite_status(self.sprite.hp, self.sprite.setting.HP)
        self.begin_time = time()
        self.under_attack = True

        if not hasattr(self.sprite, "brain"):
            # only npc has brain 
            return

        if old_hp >= self.sprite.setting.HP / 2.0 and self.sprite.hp < self.sprite.setting.HP / 2.0:
            # set angry to sprite if the damage make hp below half of full
            self.sprite.set_emotion(cfg.SpriteEmotion.ANGRY)

        if self.sprite.brain.target is None:
            # under attack when not having the target
            self.sprite.brain.target = who


    def tick(self):
        # an emprivical value for blinking the body
        if time() - self.begin_time > 0.04:
            self.under_attack = False



class AngleAttacker(Attacker):
    """
    calculate attack according the attack range, and considering the angle between sprite direction vector 
    and the line segment of the 2 units
    """
    
    def __init__(self, sprite, angle, cal_frames):
        # angle should be a degree value, like 45 degree
        super(AngleAttacker, self).__init__(sprite)
        # 2 of 8 attack frames to check
        self.cal_frames = cal_frames
        self.attack_range = sprite.setting.ATTACK_RANGE
        # cosine is a decrease function between 0 and 180 degree, 
        # so we need angle to be calculated as the min cosine value
        self.cos_min = cos(radians(angle))


    def do_attack(self, target, current_frame_add):
        sp = self.sprite
        if int(current_frame_add) not in self.cal_frames:
            return

        direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
        if id(target) in self.hit_list:
            return

        vec_to_target = Vector2.from_points(sp.area.center, target.area.center)
        cos_val = cos_for_vec(direct_vec, vec_to_target)
        if self.attack_range + target.setting.RADIUS > vec_to_target.get_length() and cos_val > self.cos_min:
            self.hit(target)


    def finish_attack(self):
        self.hit_list.clear()




class ViewSensor(object):
    """
    a view sensor for detecting target
    """

    def __init__(self, sprite, angle=90):
        self.sprite = sprite
        self.cos_min = cos(radians(angle))


    def do_view_sense(self, target):
        sp = self.sprite

        if manhattan_distance(sp.pos, target.pos) > sp.setting.VIEW_RANGE + target.setting.RADIUS:
            # quick check
            return None

        if sp.pos.get_distance_to(target.pos) > sp.setting.VIEW_RANGE + target.setting.RADIUS:
            return None

        p_sprite = sp.area.center
        direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])

        # check 4 corner points and center point of the target's aabb
        for point_attr in ("center", "topleft", "topright", "bottomleft", "bottomright"):
            p_target = getattr(target.area, point_attr)
            vec_to_target = Vector2.from_points(p_sprite, p_target)
            if cos_for_vec(direct_vec, vec_to_target) > self.cos_min:
                # and then check whether the line is blocked by some static objects
                line_seg = LineSegment(p_sprite, p_target)
                blocked_objs = filter(lambda s_obj: \
                    s_obj.is_view_block and line_segment_intersect_with_rect(line_seg, s_obj.area), 
                    sp.static_objects)
                if len(blocked_objs) == 0:
                    # no static objects block this view line segment!
                    return target

        return None



class Steerer(object):
    def __init__(self, sprite):
        self.sprite = sprite

    def path_smoothing(self, coord_list):
        new_coord_list = []
        direct_list = []

        new_coord_list.append(coord_list.pop())
        old_direct = None
        while coord_list:
            next_coord = coord_list.pop()
            dx = next_coord[0] - new_coord_list[-1][0]
            dy = next_coord[1] - new_coord_list[-1][1]
            if dx > 0:
                dx = 1.0
            elif dx < 0:
                dx = -1.0
            if dy > 0:
                dy = 1.0
            elif dy < 0:
                dy = -1.0

            next_direct = cfg.Direction.VEC_TO_DIRECT[(dx, dy)]
            if next_direct != old_direct:
                old_direct = next_direct
                new_coord_list.append(next_coord)
                direct_list.append(next_direct)    
            else:
                new_coord_list[-1] = next_coord

        new_coord_list.reverse()
        direct_list.reverse()
        return new_coord_list, direct_list


    def steer_init(self, coord_list):
        self.coord_list, self.direct_list = self.path_smoothing(coord_list)
        self.next_coord = self.coord_list.pop()
        self.cur_direct = None
        self.delta = 2
        self.last_delta = 99999999
        self.is_end = False


    def steer(self):
        sp = self.sprite
        dx = self.next_coord[0] - sp.pos.x 
        dy = self.next_coord[1] - sp.pos.y
        if abs(dx) + abs(dy) < self.last_delta:
            self.last_delta = abs(dx) + abs(dy)

        if (abs(dx) < self.delta and abs(dy) < self.delta) or (abs(dx) + abs(dy) > self.last_delta):
            # reach target coord, try next
            # a delta in x, y less than threshold, or delta is getting greater(important case), 
            # will be regarded as reaching the target
            self.last_delta = 99999999
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

