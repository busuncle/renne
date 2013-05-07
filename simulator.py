import pygame
from pygame.locals import BLEND_ADD
from base.util import LineSegment, line_segment_intersect_with_rect, cos_for_vec
from base.util import manhattan_distance, Timer, happen
import math
from random import gauss, randint
from math import pow, radians, sqrt, tan, cos
from time import time
from gameobjects.vector2 import Vector2
import animation
from base import constant as cfg
from etc import setting as sfg



class Blink(object):
    def __init__(self, rate=sfg.Effect.BLINK_RATE, depth_section=sfg.Effect.BLINK_DEPTH_SECTION):
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
        self.dx = params["dx"]
        self.dy = params["dy"]
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
                (self.area.x - camera.rect.x - self.dx, self.area.y / 2 - camera.rect.y - self.dy))



class DestroyFire(EnergyBall):
    # Renne skill
    destroy_fire_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_FIRE_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_FIRE_RECT)
    def __init__(self, sprite, target_list, static_objects, params, pos, target_pos):
        super(DestroyFire, self).__init__(self.destroy_fire_image,
            sprite, target_list, static_objects, params, pos, target_pos)



class DestroyBomb(object):
    # Renne skill
    destroy_bombs_image = animation.effect_image_controller.get(
        sfg.Effect.DESTORY_BOMB_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTORY_BOMB_RECT)
    destroy_bomb_images = []
    for i in xrange(3):
        for j in xrange(2):
            destroy_bomb_images.append(destroy_bombs_image.subsurface((i * 64, j * 64, 64, 64)))

    def __init__(self, sprite, target_list, static_objects, params, pos, direction):
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.origin_pos = pos.copy()
        self.bomb_radius = params["bomb_radius"]
        self.damage = params["damage"]
        self.dx = params["dx"]
        self.dy = params["dy"]
        self.speed = params["speed"]
        self.range = params["range"]
        self.bomb_life = params["bomb_life"]
        self.bombs_direct_num = params["bombs_direct_num"]
        self.bomb_shake_on_x = params["bomb_shake_on_x"]
        self.bomb_shake_on_y = params["bomb_shake_on_y"]
        self.status = cfg.Magic.STATUS_ALIVE

        # this 3 list are related, put them together
        self.pos_list = []
        self.bomb_ranges_list = []
        for i in xrange(self.bombs_direct_num):
            self.pos_list.append(pos.copy())
            self.bomb_ranges_list.append(list(params["bomb_ranges"]))
        vec = Vector2(cfg.Direction.DIRECT_TO_VEC[direction])
        vec_left = Vector2(cfg.Direction.DIRECT_TO_VEC[(direction - 1) % cfg.Direction.TOTAL])
        vec_right = Vector2(cfg.Direction.DIRECT_TO_VEC[(direction + 1) % cfg.Direction.TOTAL])
        self.key_vec_list = [vec, vec_left, vec_right, 
            self.normalized_vec_between_two(vec, vec_left), self.normalized_vec_between_two(vec, vec_right)]

        self.bomb_list = []
        self.has_hits = set()


    def normalized_vec_between_two(self, vec1, vec2):
        v = vec1 + vec2
        v.normalize()
        return v


    def update(self, passed_seconds):
        range_over_num = 0
        for i, pos in enumerate(self.pos_list):
            pos += self.key_vec_list[i] * self.speed * passed_seconds
            pos_range = self.origin_pos.get_distance_to(pos)
            if pos_range > self.range:
                range_over_num += 1
            if len(self.bomb_ranges_list[i]) > 0 and pos_range > self.bomb_ranges_list[i][0]:
                # create bomb and pop this range
                self.bomb_ranges_list[i].pop(0)
                b_rect = pygame.Rect(0, 0, self.bomb_radius * 2, self.bomb_radius * 2)
                #b_rect.center = pos
                b_rect.center = (gauss(pos.x, self.bomb_shake_on_x), 
                    gauss(pos.y, self.bomb_shake_on_y))
                can_create = True
                for obj in self.static_objects:
                    if obj.area.colliderect(b_rect):
                        can_create = False
                        break

                if can_create:
                    img_id = randint(0, len(self.destroy_bomb_images) - 1)
                    self.bomb_list.append({"img_id": img_id, "area": b_rect, "alive_time": 0})
                else:
                    # this line can be dropped
                    self.pos_list.pop(i)

        if range_over_num == len(self.pos_list):
            self.status = cfg.Magic.STATUS_VANISH

        for sp in self.target_list:
            if sp in self.has_hits:
                continue
            for bomb in self.bomb_list:
                if sp.area.colliderect(bomb["area"]):
                    sp.attacker.handle_under_attack(self.sprite, self.damage)
                    self.has_hits.add(sp)
                    break

        for i, bomb in enumerate(self.bomb_list):
            bomb["alive_time"] += passed_seconds
            if bomb["alive_time"] > self.bomb_life:
                self.bomb_list.pop(i)
        

    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            for bomb in self.bomb_list:
                p = bomb["area"].center
                b_id = bomb["img_id"]
                camera.screen.blit(self.destroy_bomb_images[b_id],
                    (p[0] - camera.rect.x - self.dx, p[1] / 2 - camera.rect.y - self.dy))



class DestroyAerolite(object):
    # Renne skill
    destroy_aerolite_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_AEROLITE_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_AEROLITE_RECT)
    def __init__(self, sprite, target_list, static_objects, params, pos):
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.fall_range = params["fall_range"]
        self.damage = params["damage"]
        self.acceleration = params["acceleration"]
        self.aerolite_radius = params["aerolite_radius"]
        self.aerolite_damage_cal_time = params["aerolite_damage_cal_time"]
        self.aerolite_alive_time = params["aerolite_alive_time"]
        self.dx = params["dx"]
        self.dy = params["dy"]
        self.aerolite_list = []
        self.has_hits = set()
        self.status = cfg.Magic.STATUS_ALIVE
        self.passed_seconds = 0
        self.trigger_times = list(params["trigger_times"])
        self.aerolite_shake_on_x = params["aerolite_shake_on_x"]
        self.aerolite_shake_on_y = params["aerolite_shake_on_y"]


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            # trigger a aerolite
            self.trigger_times.pop(0)
            a_rect = pygame.Rect(0, 0, self.aerolite_radius * 2, self.aerolite_radius * 2)
            #a_rect.center = (self.sprite.pos.x, self.sprite.pos.y)
            a_rect.center = (gauss(self.sprite.pos.x, self.aerolite_shake_on_x),
                gauss(self.sprite.pos.y, self.aerolite_shake_on_y))
            can_create = True
            for obj in self.static_objects:
                if obj.area.colliderect(a_rect):
                    can_create = False
                    break
            
            if can_create:
                self.aerolite_list.append({"area": a_rect, "alive_time": 0, "blink": Blink(),
                    "v": 0, "s": 0})

        for i, aerolite in enumerate(self.aerolite_list):
            # s = v0 * t + a * t^2 / 2
            if aerolite["s"] < self.fall_range:
                s = aerolite["v"] * passed_seconds + 0.5 * self.acceleration * pow(passed_seconds, 2)
                aerolite["s"] += s
                # v = v0 + a * t
                aerolite["v"] += self.acceleration * passed_seconds

                for sp in self.target_list:
                    if sp not in self.has_hits \
                        and aerolite["alive_time"] > self.aerolite_damage_cal_time \
                        and aerolite["area"].colliderect(sp.area):
                        self.has_hits.add(sp)
                        sp.attacker.handle_under_attack(self.sprite, self.damage)

            aerolite["alive_time"] += passed_seconds
            if aerolite["alive_time"] > self.aerolite_alive_time:
                self.aerolite_list.pop(i)
            else:
                aerolite["img_mix"] = aerolite["blink"].make(self.destroy_aerolite_image, passed_seconds)

        if len(self.trigger_times) == 0 and len(self.aerolite_list) == 0:
            self.status = cfg.Magic.STATUS_VANISH


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            for aerolite in self.aerolite_list:
                p = aerolite["area"].center
                camera.screen.blit(aerolite["img_mix"],
                    (p[0] - camera.rect.x - self.dx, p[1] / 2 - camera.rect.y - self.dy + aerolite["s"]))



class DeathCoil(EnergyBall):
    # Leon Hardt skill
    death_coil_image = animation.effect_image_controller.get(
        sfg.Effect.DEATH_COIL_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DEATH_COIL_RECT)
    def __init__(self, sprite, target, static_objects, params, pos, target_pos):
        super(DeathCoil, self).__init__(self.death_coil_image,
            sprite, [target], static_objects, params, pos, target_pos)



class HellClaw(object):
    # Leon Hardt skill
    hell_claw_image = animation.effect_image_controller.get(
        sfg.Effect.HELL_CLAW_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.HELL_CLAW_RECT)
    claw_image_list = [hell_claw_image.subsurface((i * 64, 0, 64, 76)) for i in xrange(2)]
    def __init__(self, sprite, target, static_objects, params):
        self.sprite = sprite
        self.target = target
        self.target_pos = target.pos.copy()
        self.static_objects = static_objects
        self.range = params["range"]
        self.damage = params["damage"]
        self.claw_radius = params["claw_radius"]
        self.claw_alive_time = params["claw_alive_time"]
        self.claw_shake_on_x = params["claw_shake_on_x"]
        self.claw_shake_on_y = params["claw_shake_on_y"]
        self.dx = params["dx"]
        self.dy = params["dy"]
        self.trigger_times = list(params["trigger_times"])
        self.claw_damage_cal_time = params["claw_damage_cal_time"]
        self.passed_seconds = 0
        self.status = cfg.Magic.STATUS_ALIVE
        self.claw_list = []
        self.img_id = 0
        self.has_hits = set()


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            # trigger a hell claw
            self.trigger_times.pop(0)
            c_rect = pygame.Rect(0, 0, self.claw_radius * 2, self.claw_radius * 2)
            c_rect.center = (gauss(self.target_pos.x, self.claw_shake_on_x), 
                gauss(self.target_pos.y, self.claw_shake_on_y))
            can_create = True
            for obj in self.static_objects:
                if obj.area.colliderect(c_rect):
                    can_create = False
                    break

            if can_create:
                self.claw_list.append({"img_id": self.img_id, "area": c_rect, "alive_time": 0,
                    "blink": Blink()})
                self.img_id = 1 - self.img_id

        for i, claw in enumerate(self.claw_list):
            if self.target not in self.has_hits \
                and claw["alive_time"] > self.claw_damage_cal_time \
                and claw["area"].colliderect(self.target.area):
                self.has_hits.add(self.target)
                self.target.attacker.handle_under_attack(self.sprite, self.damage)

            claw["alive_time"] += passed_seconds
            if claw["alive_time"] > self.claw_alive_time:
                self.claw_list.pop(i)
            else:
                claw["img_mix"] = claw["blink"].make(
                    self.claw_image_list[claw["img_id"]], passed_seconds)

        if len(self.trigger_times) == 0 and len(self.claw_list) == 0:
            self.status = cfg.Magic.STATUS_VANISH


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            for claw in self.claw_list:
                p = claw["area"].center
                camera.screen.blit(claw["img_mix"], 
                    (p[0] - camera.rect.x - self.dx, p[1] / 2 - camera.rect.y - self.dy))



class Attacker(object):
    """
    attack related calculation in one attack action
    """

    def __init__(self, sprite):
        self.sprite = sprite
        # during one attack(will be clear after when the attack is finish)
        self.has_hits = set()
        self.under_attack_timer = Timer(sfg.Sprite.UNDER_ATTACK_TIMER_LEN)


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
        self.destroy_bomb_params = attacker_params["destroy_bomb"]
        self.destroy_aerolite_params = attacker_params["destroy_aerolite"]
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


    def destroy_bomb(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.destroy_bomb_params["mana"]
            self.current_magic = DestroyBomb(sp, sp.enemies,
                sp.static_objects, self.destroy_bomb_params, sp.pos, sp.direction)
            self.magic_list.append(self.current_magic)


    def destroy_aerolite(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.destroy_aerolite_params["mana"]
            self.current_magic = DestroyAerolite(sp, sp.enemies, 
                sp.static_objects, self.destroy_aerolite_params, sp.pos)
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
        self.hell_claw_params = attacker_params["hell_claw"]
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
        if happen(sp.brain.ai.ATTACK_DEATH_COIL_PROB) \
            and sp.mp > self.death_coil_params["mana"] \
            and distance_to_target <= self.death_coil_params["range"]:
            self.method = "death_coil"
            return True
        if happen(sp.brain.ai.ATTACK_HELL_CLAW_PROB) \
            and sp.mp > self.hell_claw_params["mana"] \
            and distance_to_target <= self.hell_claw_params["range"]:
            self.method = "hell_claw"
            return True
        return False


    def death_coil(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.death_coil_params["mana"]
            self.current_magic = DeathCoil(sp, target,
                sp.static_objects, self.death_coil_params, sp.pos, target.pos)
            self.magic_list.append(self.current_magic)


    def hell_claw(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.hell_claw_params["mana"]
            self.current_magic = HellClaw(sp, target, 
                sp.static_objects, self.hell_claw_params)
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
