import pygame
from pygame.locals import BLEND_ADD
from base.util import LineSegment, line_segment_intersect_with_rect, cos_for_vec
from base.util import manhattan_distance, Timer, happen, Blink
import math
from random import gauss, randint, choice
from math import pow, radians, sqrt, tan, cos
from time import time
from gameobjects.vector2 import Vector2
import animation
from base import constant as cfg
from etc import setting as sfg



class MagicSprite(pygame.sprite.DirtySprite):
    def __init__(self, pos, radius, dx, dy, damage, image):
        super(MagicSprite, self).__init__()
        self.pos = Vector2(pos)
        self.area = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.area.center = self.pos
        self.damage = damage
        self.dx = dx
        self.dy = dy
        self.image = image
        self.status = cfg.Magic.STATUS_ALIVE


    def update(self, passed_seconds):
        pass


    def draw_shadow(self, camera):
        pass


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            camera.screen.blit(self.image,
                (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy))

        #r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        #r.center = (self.pos.x, self.pos.y * 0.5)
        #r.top -= camera.rect.top
        #r.left -= camera.rect.left
        #pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)



class EnergyBall(MagicSprite):
    def __init__(self, pos, radius, dx, dy, damage, image, shadow, target_pos, range, speed):
        super(EnergyBall, self).__init__(pos, radius, dx, dy, damage, image)
        self.range = range
        self.speed = speed
        self.origin_pos = self.pos.copy()
        self.key_vec = Vector2.from_points(pos, target_pos)
        self.key_vec.normalize()
        self.image_mix = self.image.copy()
        self.shadow = shadow
        self.blink = Blink()

        
    def update(self, passed_seconds):
        self.pos += self.key_vec * self.speed * passed_seconds
        self.area.center = self.pos("xy")
        self.image_mix = self.blink.make(self.image, passed_seconds)
        if self.origin_pos.get_distance_to(self.pos) > self.range:
            self.status = cfg.Magic.STATUS_VANISH


    def draw_shadow(self, camera):
        shd_rect = self.shadow["image"].get_rect()
        shd_rect.center = self.pos
        camera.screen.blit(self.shadow["image"],
            (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y - self.shadow["dy"]))


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            camera.screen.blit(self.image_mix,
                (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy))
            #r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
            #r.center = (self.pos.x, self.pos.y * 0.5)
            #r.top -= camera.rect.top
            #r.left -= camera.rect.left
            #pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)



class EnergyBallSet(object):
    def __init__(self, image, shadow, sprite, target_list, static_objects, params, pos, target_pos):
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.status = cfg.Magic.STATUS_ALIVE
        self.has_hits = set()
        self.magic_sprites = []
        # only one ball right now
        self.magic_sprites.append(EnergyBall(pos, params["radius"], params["dx"], params["dy"], 
            params["damage"], image, shadow, target_pos, params["range"], params["speed"]))


    def update(self, passed_seconds):
        vanish_num = 0
        for msp in self.magic_sprites:
            if msp.status == cfg.Magic.STATUS_VANISH:
                vanish_num += 1
                continue

            msp.update(passed_seconds)

            for sp in self.target_list:
                if sp in self.has_hits:
                    continue

                if sp.area.colliderect(msp.area):
                    sp.attacker.handle_under_attack(self.sprite, msp.damage)
                    self.has_hits.add(sp)

            for obj in self.static_objects:
                if not obj.setting.IS_ELIMINABLE and obj.area.colliderect(msp.area):
                    msp.status = cfg.Magic.STATUS_VANISH

        if vanish_num == len(self.magic_sprites):
            self.status = cfg.Magic.STATUS_VANISH


    def draw(self, camera):
        for msp in self.magic_sprites:
            msp.draw(camera)



class DestroyFire(EnergyBallSet):
    # Renne skill
    destroy_fire_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_FIRE_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_FIRE_RECT)
    shadow_image = animation.get_shadow_image(sfg.Effect.DESTROY_FIRE_SHADOW_INDEX)
    shadow_rect_delta_y = sfg.Effect.DESTROY_FIRE_SHADOW_RECT_DELTA_Y
    def __init__(self, sprite, target_list, static_objects, params, pos, target_pos):
        shadow = {"image": self.shadow_image, "dy": self.shadow_rect_delta_y}
        super(DestroyFire, self).__init__(self.destroy_fire_image, shadow,
            sprite, target_list, static_objects, params, pos, target_pos)



class DestroyBomb(MagicSprite):
    shadow_image = animation.get_shadow_image(sfg.Effect.DESTROY_BOMB_SHADOW_INDEX)
    shadow_rect_delta_y = sfg.Effect.DESTROY_BOMB_SHADOW_RECT_DELTA_Y
    def __init__(self, pos, radius, dx, dy, damage, image, life, shake_on_x, shake_on_y):
        super(DestroyBomb, self).__init__(pos, radius, dx, dy, damage, image)
        self.pos.x = gauss(self.pos.x, shake_on_x)
        self.pos.y = gauss(self.pos.y, shake_on_y)
        self.area.center = self.pos
        self.life = life
        self.alive_time = 0


    def update(self, passed_seconds):
        self.alive_time += passed_seconds
        if self.alive_time > self.life:
            self.status = cfg.Magic.STATUS_VANISH
        

    def draw_shadow(self, camera):
        shd_rect = self.shadow_image.get_rect()
        shd_rect.center = self.pos
        camera.screen.blit(self.shadow_image,
            (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y - self.shadow_rect_delta_y))



class DestroyBombSet(object):
    # Renne skill
    destroy_bombs_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_BOMB_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_BOMB_RECT)
    destroy_bomb_images = []
    for i in xrange(3):
        for j in xrange(2):
            destroy_bomb_images.append(destroy_bombs_image.subsurface((i * 64, j * 64, 64, 64)))

    def __init__(self, sprite, target_list, static_objects, params, pos, direction):
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.origin_pos = pos.copy()
        self.params = params
        self.speed = params["speed"]
        self.range = params["range"]
        self.status = cfg.Magic.STATUS_ALIVE

        # this 3 list are related, put them together
        self.pos_list = []
        self.bomb_ranges_list = []
        for i in xrange(params["bombs_direct_num"]):
            self.pos_list.append(pos.copy())
            self.bomb_ranges_list.append(list(params["bomb_ranges"]))
        vec = Vector2(cfg.Direction.DIRECT_TO_VEC[direction])
        vec_left = Vector2(cfg.Direction.DIRECT_TO_VEC[(direction - 1) % cfg.Direction.TOTAL])
        vec_right = Vector2(cfg.Direction.DIRECT_TO_VEC[(direction + 1) % cfg.Direction.TOTAL])
        self.key_vec_list = [vec, vec_left, vec_right, 
            self.normalized_vec_between_two(vec, vec_left), self.normalized_vec_between_two(vec, vec_right)]

        self.magic_sprites = []
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
                bomb = DestroyBomb(pos, self.params["bomb_radius"], self.params["dx"],
                    self.params["dy"], self.params["damage"], choice(self.destroy_bomb_images),
                    self.params["bomb_life"], self.params["bomb_shake_on_x"], self.params["bomb_shake_on_y"])

                can_create = True
                for obj in self.static_objects:
                    if not obj.setting.IS_ELIMINABLE and obj.area.colliderect(bomb.area):
                        can_create = False
                        break

                if can_create:
                    self.magic_sprites.append(bomb)
                else:
                    # this line can be dropped
                    self.pos_list.pop(i)

        if range_over_num == len(self.pos_list):
            self.status = cfg.Magic.STATUS_VANISH

        for sp in self.target_list:
            if sp in self.has_hits:
                continue

            for bomb in self.magic_sprites:
                if sp.area.colliderect(bomb.area):
                    sp.attacker.handle_under_attack(self.sprite, bomb.damage)
                    self.has_hits.add(sp)
                    break

        for i, bomb in enumerate(self.magic_sprites):
            bomb.update(passed_seconds)
            if bomb.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)
        

    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            for bomb in self.magic_sprites:
                bomb.draw(camera)



class DestroyAerolite(MagicSprite):
    shadow_image = animation.get_shadow_image(sfg.Effect.DESTROY_AEROLITE_SHADOW_INDEX)
    shadow_rect_delta_y = sfg.Effect.DESTROY_AEROLITE_SHADOW_RECT_DELTA_Y
    def __init__(self, pos, radius, dx, dy, damage, image, fall_range, acceleration, damage_cal_time,
            life, shake_on_x, shake_on_y):
        super(DestroyAerolite, self).__init__(pos, radius, dx, dy, damage, image)
        self.pos.x = gauss(self.pos.x, shake_on_x)
        self.pos.y = gauss(self.pos.y, shake_on_y)
        self.area.center = self.pos
        self.fall_range = fall_range
        self.acceleration = acceleration
        self.damage_cal_time = damage_cal_time
        self.life = life
        self.fall_v = 0
        self.fall_s = 0
        self.alive_time = 0
        self.blink = Blink()
        self.image_mix = None


    def update(self, passed_seconds):
        self.image_mix = self.blink.make(self.image, passed_seconds)
        if self.fall_s < self.fall_range:
            # s = v0 * t + a * t^2 / 2
            s = self.fall_v * passed_seconds + 0.5 * self.acceleration * pow(passed_seconds, 2)
            self.fall_s += s
            # v = v0 + a * t
            self.fall_v += self.acceleration * passed_seconds

        self.alive_time += passed_seconds
        if self.alive_time > self.life:
            self.status = cfg.Magic.STATUS_VANISH


    def draw_shadow(self, camera):
        shd_rect = self.shadow_image.get_rect()
        shd_rect.center = self.pos
        camera.screen.blit(self.shadow_image,
            (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y - self.shadow_rect_delta_y))
        #if self.alive_time > self.damage_cal_time:
        #    r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        #    r.center = (self.pos.x, self.pos.y * 0.5)
        #    r.top -= camera.rect.top
        #    r.left -= camera.rect.left
        #    pygame.draw.rect(camera.screen, pygame.Color("red"), r, 1)


    def draw(self, camera):
        camera.screen.blit(self.image_mix,
            (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy + self.fall_s))
        


class DestroyAeroliteSet(object):
    # Renne skill
    destroy_aerolite_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_AEROLITE_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_AEROLITE_RECT)
    def __init__(self, sprite, target_list, static_objects, params, pos):
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.params = params
        self.has_hits = set()
        self.status = cfg.Magic.STATUS_ALIVE
        self.passed_seconds = 0
        self.trigger_times = list(params["trigger_times"])
        self.magic_sprites = []


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            # trigger a aerolite
            self.trigger_times.pop(0)
            aerolite = DestroyAerolite(self.sprite.pos, self.params["aerolite_radius"], self.params["dx"],
                self.params["dy"], self.params["damage"], self.destroy_aerolite_image, 
                self.params["fall_range"], self.params["acceleration"], 
                self.params["aerolite_damage_cal_time"], self.params["aerolite_life"],
                self.params["aerolite_shake_on_x"], self.params["aerolite_shake_on_y"])

            can_create = True
            for obj in self.static_objects:
                if not obj.setting.IS_ELIMINABLE and obj.area.colliderect(aerolite.area):
                    can_create = False
                    break
            
            if can_create:
                self.magic_sprites.append(aerolite)

        for i, aerolite in enumerate(self.magic_sprites):
            aerolite.update(passed_seconds)
            if aerolite.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)
                continue

            for sp in self.target_list:
                if sp not in self.has_hits \
                    and aerolite.alive_time > aerolite.damage_cal_time \
                    and sp.area.colliderect(aerolite.area):
                    self.has_hits.add(sp)
                    sp.attacker.handle_under_attack(self.sprite, aerolite.damage)
                    sp.status["stun_time"] = self.params["stun_time"]
                    sp.set_emotion(cfg.SpriteEmotion.STUN)

        if len(self.trigger_times) == 0 and len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH


    def draw_shadow(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            for aerolite in self.magic_sprites:
                shd_rect = self.shadow_image.get_rect()
                shd_rect.center = aerolite["area"].center
                camera.screen.blit(self.shadow_image, 
                    (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y))


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            for aerolite in sorted(self.magic_sprites, key=lambda x: x.area.centery):
                aerolite.draw(camera)



class RenneDizzy(object):
    # Renne skill
    def __init__(self, sprite, target_list, dizzy_range, dizzy_time, effective_time, prob):
        self.sprite = sprite
        self.target_list = target_list
        self.dizzy_range = dizzy_range
        self.dizzy_time = dizzy_time
        self.effective_time = effective_time
        self.prob = prob
        self.dizzy_targets = set()
        self.status = cfg.Magic.STATUS_ALIVE
        # actually no magic sprite in this skill, but this variable should exist in every magic skill
        self.magic_sprites = []


    def update(self, passed_seconds):
        sp = self.sprite
        for target in self.target_list:
            if sp.pos.get_distance_to(target.pos) < self.dizzy_range \
                and target not in self.dizzy_targets:
                self.dizzy_targets.add(target)
                if happen(self.prob):
                    target.status["dizzy_time"] = self.dizzy_time
                    target.set_emotion(cfg.SpriteEmotion.DIZZY)

        self.effective_time -= passed_seconds
        if self.effective_time <= 0:
            self.status = cfg.Magic.STATUS_VANISH



class DeathCoil(EnergyBallSet):
    # Leon Hardt skill
    death_coil_image = animation.effect_image_controller.get(
        sfg.Effect.DEATH_COIL_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DEATH_COIL_RECT)
    image_list = [death_coil_image.subsurface((i * 64, 0, 64, 64)) for i in xrange(2)]
    shadow_image = animation.get_shadow_image(sfg.Effect.DEATH_COIL_SHADOW_INDEX)
    shadow_rect_delta_y = sfg.Effect.DEATH_COIL_SHADOW_RECT_DELTA_Y
    def __init__(self, sprite, target, static_objects, params, pos, target_pos):
        shadow = {"image": self.shadow_image, "dy": self.shadow_rect_delta_y}
        super(DeathCoil, self).__init__(choice(self.image_list), shadow,
            sprite, [target], static_objects, params, pos, target_pos)



class HellClaw(MagicSprite):
    shadow_image = animation.get_shadow_image(sfg.Effect.HELL_CLAW_SHADOW_INDEX)
    shadow_rect_delta_y = sfg.Effect.HELL_CLAW_SHADOW_RECT_DELTA_Y
    def __init__(self, pos, radius, dx, dy, damage, image, life, damage_cal_time,
            shake_on_x, shake_on_y):
        super(HellClaw, self).__init__(pos, radius, dx, dy, damage, image)
        self.pos.x = gauss(self.pos.x, shake_on_x)
        self.pos.y = gauss(self.pos.y, shake_on_y)
        self.area.center = self.pos
        self.damage = damage
        self.life = life
        self.damage_cal_time = damage_cal_time
        self.alive_time = 0
        self.image_mix = None
        self.blink = Blink()


    def update(self, passed_seconds):
        self.image_mix = self.blink.make(self.image, passed_seconds)
        self.alive_time += passed_seconds
        if self.alive_time > self.life:
            self.status = cfg.Magic.STATUS_VANISH


    def draw_shadow(self, camera):
        shd_rect = self.shadow_image.get_rect()
        shd_rect.center = self.pos
        camera.screen.blit(self.shadow_image,
            (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y - self.shadow_rect_delta_y))


    def draw(self, camera):
        camera.screen.blit(self.image_mix,
            (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy))
        #r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        #r.center = (self.pos.x, self.pos.y * 0.5)
        #r.top -= camera.rect.top
        #r.left -= camera.rect.left
        #pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)



class HellClawSet(object):
    # Leon Hardt skill
    hell_claw_image = animation.effect_image_controller.get(
        sfg.Effect.HELL_CLAW_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.HELL_CLAW_RECT)
    claw_image_list = [hell_claw_image.subsurface((i * 64, 0, 64, 72)) for i in xrange(2)]
    def __init__(self, sprite, target, static_objects, params):
        self.sprite = sprite
        self.target = target
        self.target_pos = target.pos.copy()
        self.static_objects = static_objects
        self.range = params["range"]
        self.params = params
        self.trigger_times = list(params["trigger_times"])
        self.passed_seconds = 0
        self.status = cfg.Magic.STATUS_ALIVE
        self.img_id = 0
        self.has_hits = set()
        self.magic_sprites = []


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            # trigger a hell claw
            self.trigger_times.pop(0)
            claw = HellClaw(self.target_pos, self.params["claw_radius"], self.params["dx"], self.params["dy"],
                self.params["damage"], self.claw_image_list[self.img_id], self.params["claw_life"],
                self.params["claw_damage_cal_time"],
                self.params["claw_shake_on_x"], self.params["claw_shake_on_y"])

            can_create = True
            for obj in self.static_objects:
                if not obj.setting.IS_ELIMINABLE and obj.area.colliderect(claw.area):
                    can_create = False
                    break

            if can_create:
                self.magic_sprites.append(claw)
                self.img_id = 1 - self.img_id

        for i, claw in enumerate(self.magic_sprites):
            if self.target not in self.has_hits \
                and claw.alive_time > claw.damage_cal_time \
                and claw.area.colliderect(self.target.area):
                self.has_hits.add(self.target)
                self.target.attacker.handle_under_attack(self.sprite, claw.damage)

            claw.update(passed_seconds)
            if claw.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)

        if len(self.trigger_times) == 0 and len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            for claw in self.magic_sprites:
                claw.draw(camera)



class Attacker(object):
    """
    attack related calculation in one attack action
    """

    def __init__(self, sprite):
        self.sprite = sprite
        # during one attack(will be clear after when the attack is finish)
        self.has_hits = set()


    def run(self):
        pass


    def hit(self):
        pass


    def handle_under_attack(self, from_who, cost_hp):
        sp = self.sprite
        sp.hp = max(sp.hp - cost_hp, 0)
        sp.status["hp"] = sp.cal_sprite_status(sp.hp, sp.setting.HP)
        sp.status["under_attack_effect_time"] = sfg.Sprite.UNDER_ATTACK_EFFECT_TIME
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
        self.cos_min = cos(radians(angle * 0.5))


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
        self.dizzy_params = attacker_params["dizzy"]
        self.magic_cds = {"destroy_fire": 0, "destroy_bomb": 0, "destroy_aerolite": 0, "dizzy": 0}
        self.magic_list = []
        # a lock, only one magic is running in an attack
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
            self.magic_cds["destroy_fire"] = self.destroy_fire_params["cd"]
            self.current_magic = DestroyFire(sp, sp.enemies,
                sp.static_objects, self.destroy_fire_params, sp.pos, sp.pos + direct_vec)
            self.magic_list.append(self.current_magic)


    def destroy_bomb(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.destroy_bomb_params["mana"]
            self.magic_cds["destroy_bomb"] = self.destroy_bomb_params["cd"]
            self.current_magic = DestroyBombSet(sp, sp.enemies,
                sp.static_objects, self.destroy_bomb_params, sp.pos, sp.direction)
            self.magic_list.append(self.current_magic)


    def destroy_aerolite(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.destroy_aerolite_params["mana"]
            self.magic_cds["destroy_aerolite"] = self.destroy_aerolite_params["cd"]
            self.current_magic = DestroyAeroliteSet(sp, sp.enemies, 
                sp.static_objects, self.destroy_aerolite_params, sp.pos)
            self.magic_list.append(self.current_magic)


    def dizzy(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.dizzy_params["key_frames"]:
            self.magic_cds["dizzy"] = self.dizzy_params["cd"]
            self.current_magic = RenneDizzy(sp, sp.enemies, self.dizzy_params["range"],
                self.dizzy_params["time"], self.dizzy_params["effective_time"],
                self.dizzy_params["prob"])
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
            self.current_magic = HellClawSet(sp, target, 
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
        self.cos_min = cos(radians(angle * 0.5))


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
    sfg.SkeletonWarrior.ID: EnemyShortAttacker,
    sfg.CastleWarrior.ID: EnemyShortAttacker,
    sfg.SkeletonArcher.ID: EnemyLongAttacker,
    sfg.LeonHardt.ID: LeonhardtAttacker,
    sfg.ArmouredShooter.ID: EnemyLongAttacker,
    sfg.SwordRobber.ID: EnemyShortAttacker,
}


if __name__ == "__main__":
    pass
