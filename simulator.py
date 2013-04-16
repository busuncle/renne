from base.util import LineSegment, line_segment_intersect_with_rect, cos_for_vec, manhattan_distance
import etc.constant as cfg
import etc.setting as sfg
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
        # during one attack(will be clear after when the attack is finish)
        self.has_hits = set()
        self.under_attack_begin_time = None


    def run(self):
        pass


    def hit(self):
        pass


    def under_attack_tick(self):
        if time() - self.under_attack_begin_time > 0.05:
            self.sprite.status["under_attack"] = False


    def cal_sprite_status(self, current_hp, full_hp):
        # calculate the sprite status according the current hp and full hp
        if current_hp > full_hp * sfg.SpriteStatus.HEALTHY_RATIO_FLOOR:
            return cfg.SpriteStatus.HEALTHY
        elif current_hp > full_hp * sfg.SpriteStatus.WOUNDED_RATIO_FLOOR:
            return cfg.SpriteStatus.WOUNDED
        elif current_hp > full_hp * sfg.SpriteStatus.DANGER_RATIO_FLOOR:
            return cfg.SpriteStatus.DANGER
        else:
            return cfg.SpriteStatus.DIE


    def finish(self):
        pass



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


    def hit(self, target, current_frame_add):
        if int(current_frame_add) not in self.cal_frames:
            return False

        if target in self.has_hits:
            return False

        sp = self.sprite
        direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
        vec_to_target = Vector2.from_points(sp.area.center, target.area.center)
        cos_val = cos_for_vec(direct_vec, vec_to_target)
        if self.attack_range + target.setting.RADIUS > vec_to_target.get_length() \
            and cos_val > self.cos_min and target.status["hp"] != cfg.SpriteStatus.DIE:
            self.has_hits.add(target)
            return True

        return False



class RenneAttacker(AngleAttacker):
    def __init__(self, sprite, angle, cal_frames):
        super(RenneAttacker, self).__init__(sprite, angle, cal_frames)
        self.hit_record = []
        self.kill_record = []


    def run(self, enemy, current_frame_add):
        if self.hit(enemy, current_frame_add):
            damage = self.sprite.atk - enemy.dfs
            enemy.hp = max(enemy.hp - damage, 0)
            enemy.status["hp"] = enemy.attacker.cal_sprite_status(enemy.hp, enemy.setting.HP)
            enemy.status["under_attack"] = True
            enemy.attacker.under_attack_begin_time = time()

            # calculate enemy's emotion
            angry_hp_threshold = enemy.setting.HP * enemy.brain.ai.ANGRY_HP_RATIO
            if enemy.hp < angry_hp_threshold and enemy.hp + damage >= angry_hp_threshold:
                enemy.set_emotion(cfg.SpriteEmotion.ANGRY)

            if enemy.brain.target is None:
                enemy.brain.target = self.sprite

            return True
        return False


    def finish(self):
        if len(self.has_hits) > 0:
            self.hit_record.append({"time": time(), "n_hit": len(self.has_hits)})
            for sp in self.has_hits:
                if sp.status["hp"] == cfg.SpriteStatus.DIE:
                    self.kill_record.append({"time": time()})
            self.has_hits.clear()



class EnemyAttacker(AngleAttacker):
    def __init__(self, sprite, angle, cal_frames):
        super(EnemyAttacker, self).__init__(sprite, angle, cal_frames)


    def run(self, hero, current_frame_add):
        if self.hit(hero, current_frame_add):
            damage = self.sprite.atk - hero.dfs
            hero.hp = max(hero.hp - damage, 0)
            hero.status["hp"] = hero.attacker.cal_sprite_status(hero.hp, hero.setting.HP)
            hero.status["under_attack"] = True
            hero.attacker.under_attack_begin_time = time()
            return True
        return False
        

    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()



class ViewSensor(object):
    """
    a view sensor for detecting target
    """

    def __init__(self, sprite, angle=90):
        self.sprite = sprite
        self.cos_min = cos(radians(angle))


    def detect(self, target):
        sp = self.sprite

        if manhattan_distance(sp.pos, target.pos) > sp.setting.VIEW_RANGE + target.setting.RADIUS:
            # quick check
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
                for obj in sp.static_objects:
                    if obj.is_view_block and line_segment_intersect_with_rect(line_seg, obj.area):
                        return None

                return target

        return None



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


    def steer_init(self, coord_list):
        self.coord_list, self.direct_list = self.path_smoothing(coord_list)
        self.next_coord = self.coord_list.pop()
        self.cur_direct = None
        self.delta = 2
        self.is_end = False


    def steer(self):
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



if __name__ == "__main__":
    st = Steerer(None)
    coord_list = [(4, 2), (3, 2), (2, 1), (1, 0), (0, 0)]
    #coord_list = [(1, 1), (0, 0)]
    #coord_list = [(0, 0)]
    st.steer_init(coord_list)
    print st.next_coord
    print list(reversed(st.coord_list))
    print map(lambda x: cfg.Direction.DIRECT_TO_MARK[x], reversed(st.direct_list))
