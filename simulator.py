import pygame
from pygame.locals import BLEND_ADD
from base.util import LineSegment, line_segment_intersect_with_rect, cos_for_vec
from base.util import manhattan_distance, Timer, happen
import math
from math import pow, radians, sqrt, tan, cos
from time import time
from gameobjects.vector2 import Vector2
import animation
from base import constant as cfg
from etc import setting as sfg



class Blink(object):
    def __init__(self, rate=256, depth_section=(32, 128)):
        self.rate = rate
        self.depth_section = depth_section
        self.depth = self.depth_section[0]
        self.direct = 1


    def make(self, image, passed_seconds):
        image_mix = image.copy()
        self.depth += self.rate * self.direct * passed_seconds
        if self.depth < self.depth_section[0]:
            self.depth = self.depth_section[0]
            self.direct = 1
        elif self.depth > self.depth_section[1]:
            self.depth = self.depth_section[1]
            self.direct = -1

        self.depth = int(self.depth)

        image_mix.fill(pygame.Color(self.depth, self.depth, self.depth), special_flags=BLEND_ADD)
        return image_mix



class EnergyBall(object):
    def __init__(self, image, sprite, target_list, static_objects, params, pos, target_pos):
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.damage = params["damage"]
        self.range = params["range"]
        self.height = params["height"]
        self.pos = pos.copy()
        self.origin_pos = self.pos.copy()
        self.area = pygame.Rect(0, 0, params["radius"] * 2, params["radius"] * 2)
        self.speed = params["speed"]
        self.status = cfg.Magic.STATUS_ALIVE
        self.key_vec = Vector2.from_points(pos, target_pos)
        self.key_vec.normalize()
        self.image = image
        self.image_mix = None
        self.blink = Blink()
        self.has_hits= set()


    def update(self, passed_seconds):
        self.pos += self.key_vec * self.speed * passed_seconds
        self.area.center = self.pos("xy")
        for sp in self.target_list:
            if sp in self.has_hits:
                continue
            if sp.area.colliderect(self.area):
                sp.attacker.handle_under_attack(self.sprite, self.damage)
                self.has_hits.add(sp)

        self.image_mix = self.blink.make(self.image, passed_seconds)

        if self.origin_pos.get_distance_to(self.pos) > self.range:
            self.status = cfg.Magic.STATUS_VANISH

        for obj in self.static_objects:
            if obj.area.colliderect(self.area):
                self.status = cfg.Magic.STATUS_VANISH
                return


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            camera.screen.blit(self.image_mix,
                (self.area.x - camera.rect.x, self.area.y / 2 - camera.rect.y - self.height))



class DestroyFire(EnergyBall):
    # Renne skill
    destroy_fire_image = animation.effect_image_controller.get("e2").convert_alpha().subsurface(
        sfg.Effect.DESTROY_FIRE_RECT)
    def __init__(self, sprite, target_list, static_objects, params, pos, target_pos):
        super(DestroyFire, self).__init__(self.destroy_fire_image,
            sprite, target_list, static_objects, params, pos, target_pos)



class DestroyBomb(object):
    # Renne skill
    pass



class DeathCoil(EnergyBall):
    death_coil_image = animation.effect_image_controller.get("e1").convert_alpha().subsurface(
        sfg.Effect.DEATH_COIL_RECT)
    def __init__(self, sprite, target_list, static_objects, params, pos, target_pos):
        super(DeathCoil, self).__init__(self.death_coil_image,
            sprite, target_list, static_objects, params, pos, target_pos)



class Attacker(object):
    """
    attack related calculation in one attack action
    """

    def __init__(self, sprite):
        self.sprite = sprite
        # during one attack(will be clear after when the attack is finish)
        self.has_hits = set()
        self.under_attack_timer = Timer(0.05)


    def run(self):
        pass


    def hit(self):
        pass


    def under_attack_tick(self):
        if self.under_attack_timer.exceed():
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


    def handle_under_attack(self, from_who, cost_hp):
        sp = self.sprite
        sp.hp = max(sp.hp - cost_hp, 0)
        sp.status["hp"] = self.cal_sprite_status(sp.hp, sp.setting.HP)
        sp.status["under_attack"] = True
        self.under_attack_timer.begin()
        sp.animation.show_cost_hp(cost_hp)
        if sp.setting.ROLE == cfg.SpriteRole.ENEMY:
            sp.cal_angry(cost_hp)
            sp.get_target(from_who)


    def finish(self):
        pass



class AngleAttacker(Attacker):
    """
    calculate attack according the attack range, and considering the angle between sprite direction vector 
    and the line segment of the 2 units
    """
    
    def __init__(self, sprite, attack_range, angle, key_frames):
        # angle should be a degree value, like 45 degree
        super(AngleAttacker, self).__init__(sprite)
        self.attack_range = attack_range
        self.key_frames = key_frames
        # cosine is a decrease function between 0 and 180 degree, 
        # so we need angle to be calculated as the min cosine value
        # angle needs to be divide by 2 because of the symmetry
        assert 0 <= angle <= 180
        self.cos_min = cos(radians(angle / 2))


    def hit(self, target, current_frame_add):
        if int(current_frame_add) not in self.key_frames:
            return False

        if target in self.has_hits:
            return False

        sp = self.sprite
        direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
        vec_to_target = Vector2.from_points(sp.area.center, target.area.center)
        cos_val = cos_for_vec(direct_vec, vec_to_target)
        if self.attack_range + target.setting.RADIUS > vec_to_target.get_length() \
            and cos_val >= self.cos_min and target.status["hp"] != cfg.SpriteStatus.DIE:
            self.has_hits.add(target)
            return True

        return False



class RenneAttacker(AngleAttacker):
    def __init__(self, sprite, attacker_params):
        super(RenneAttacker, self).__init__(sprite, 
            attacker_params["range"], attacker_params["angle"], attacker_params["key_frames"])
        self.hit_record = []
        self.kill_record = []
        self.destroy_fire_params = attacker_params["destroy_fire"]
        self.magic_list = []
        self.current_magic = None
        self.method = None


    def run(self, enemy, current_frame_add):
        if self.hit(enemy, current_frame_add):
            damage = self.sprite.atk - enemy.dfs
            enemy.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False


    def destroy_fire(self, current_frame_add):
        sp = self.sprite
        direct_vec = cfg.Direction.DIRECT_TO_VEC[sp.direction]
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.destroy_fire_params["mana"]
            self.current_magic = DestroyFire(sp, sp.enemies,
                sp.static_objects, self.destroy_fire_params, sp.pos, sp.pos + direct_vec)
            self.magic_list.append(self.current_magic)


    def finish(self):
        if len(self.has_hits) > 0:
            self.hit_record.append({"time": time(), "n_hit": len(self.has_hits)})
            for sp in self.has_hits:
                if sp.status["hp"] == cfg.SpriteStatus.DIE:
                    self.kill_record.append({"time": time()})
            self.has_hits.clear()

        self.method = None
        self.current_magic = None



class EnemyShortAttacker(AngleAttacker):
    def __init__(self, sprite, attacker_params):
        super(EnemyShortAttacker, self).__init__(sprite, 
            attacker_params["range"], attacker_params["angle"], attacker_params["key_frames"])


    def chance(self, target):
        # totally for ai, because player can judge whether it's a good attack chance himself
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if distance_to_target <= self.attack_range:
            return True
        return False


    def run(self, hero, current_frame_add):
        if self.hit(hero, current_frame_add):
            damage = self.sprite.atk - hero.dfs
            hero.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False
        

    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()



class EnemyLongAttacker(AngleAttacker):
    def __init__(self, sprite, attacker_params):
        attack_range = attacker_params["range"]
        angle = attacker_params["angle"]
        key_frames = attacker_params["key_frames"]
        super(EnemyLongAttacker, self).__init__(sprite, attack_range, angle, key_frames)


    def chance(self, target):
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if distance_to_target <= self.attack_range:
            direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
            vec_to_target = Vector2.from_points(sp.area.center, target.area.center)
            cos_val = cos_for_vec(direct_vec, vec_to_target)
            if cos_val >= self.cos_min:
                return True

        return False


    def run(self, hero, current_frame_add):
        if self.hit(hero, current_frame_add):
            damage = self.sprite.atk - hero.dfs
            hero.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False


    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()



class LeonhardtAttacker(AngleAttacker):
    def __init__(self, sprite, attacker_params):
        super(LeonhardtAttacker, self).__init__(sprite, 
            attacker_params["range"], attacker_params["angle"], attacker_params["key_frames"])
        self.death_coil_params = attacker_params["death_coil"]
        self.magic_list = []
        self.current_magic = None
        self.method = None


    def chance(self, target):
        # totally for ai, because player can judge whether it's a good attack chance himself
        # at the same time, choose which method to attack hero
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if happen(sp.brain.ai.ATTACK_REGULAR_PROB) \
            and distance_to_target <= self.attack_range:
            self.method = "regular"
            return True
        if happen(sp.brain.ai.ATTACK_ENERGY_BALL_PROB) \
            and sp.mp > self.death_coil_params["mana"] \
            and distance_to_target <= self.death_coil_params["range"]:
            self.method = "death_coil"
            return True
        return False


    def death_coil(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.death_coil_params["mana"]
            self.current_magic = DeathCoil(sp, [target, ],
                sp.static_objects, self.death_coil_params, sp.pos, target.pos)
            self.magic_list.append(self.current_magic)


    def run(self, hero, current_frame_add):
        if self.hit(hero, current_frame_add):
            damage = self.sprite.atk - hero.dfs
            hero.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False


    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()
        self.method = None
        self.current_magic = None



class ViewSensor(object):
    """
    a view sensor for detecting target
    """

    def __init__(self, sprite, angle=120):
        self.sprite = sprite
        self.cos_min = cos(radians(angle / 2))


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
            if cos_for_vec(direct_vec, vec_to_target) >= self.cos_min:
                # and then check whether the line is blocked by some static objects
                line_seg = LineSegment(p_sprite, p_target)
                for obj in sp.static_objects:
                    if obj.setting.IS_VIEW_BLOCK and line_segment_intersect_with_rect(line_seg, obj.area):
                        return None

                return target

        return None



ENEMY_ATTACKER_MAPPING = {
    cfg.SpriteAttackType.SHORT: EnemyShortAttacker,
    cfg.SpriteAttackType.LONG: EnemyLongAttacker,
    cfg.SpriteAttackType.LEONHARDT: LeonhardtAttacker,
    cfg.SpriteAttackType.SWORDROBBER: EnemyShortAttacker,
    cfg.SpriteAttackType.ARMOUREDSHOOTER: EnemyLongAttacker,
}


if __name__ == "__main__":
    pass
