import pygame
from pygame.locals import BLEND_ADD
from pygame import transform
from base.util import LineSegment, line_segment_intersect_with_rect, cos_for_vec
from base.util import manhattan_distance, Timer, happen, Blink
import math
from random import gauss, randint, choice, random
from math import pow, radians, sqrt, tan, cos
from time import time
from gameobjects.vector2 import Vector2
import animation
from base import constant as cfg
from etc import setting as sfg



class MagicSprite(pygame.sprite.DirtySprite):
    """
    represent some magic unit
    """
    def __init__(self, pos, radius, dx, dy, damage, image, shadow):
        super(MagicSprite, self).__init__()
        self.pos = Vector2(pos)
        self.area = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.area.center = self.pos
        self.damage = damage
        self.dx = dx
        self.dy = dy
        self.image = image
        self.shadow = shadow
        self.status = cfg.Magic.STATUS_ALIVE


    def update(self, passed_seconds):
        pass


    def draw_shadow(self, camera):
        if self.shadow is not None:
            shd_rect = self.shadow["image"].get_rect()
            shd_rect.center = self.pos
            camera.screen.blit(self.shadow["image"],
                (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y - self.shadow["dy"]))


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            camera.screen.blit(self.image,
                (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy))
            #self.draw_area(camera)


    def draw_area(self, camera):
        # for debug
        r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        r.center = (self.pos.x, self.pos.y * 0.5)
        r.top -= camera.rect.top
        r.left -= camera.rect.left
        pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)



class MagicSkill(object):
    # represent a magic skill, it may contain one or more magic sprite(s)
    # it's a member in magic_list
    def __init__(self):
        self.status = cfg.Magic.STATUS_ALIVE


    def update(self, passed_seconds):
        pass


    def draw(self, camera):
        pass



class Bomb(MagicSprite):
    bombs_image = animation.effect_image_controller.get(
        sfg.Effect.BOMB_IMAGE_KEY).subsurface(sfg.Effect.BOMB_RECT).convert_alpha()
    bomb_images = [bombs_image.subsurface((i * 64, 0, 64, 64)) for i in xrange(3)]
    def __init__(self, pos, dx, dy, damage, angle, scale):
        super(Bomb, self).__init__(pos, sfg.Effect.BOMB_RADIUS, dx, dy, damage, None, None)
        self.angle = angle
        self.scale = scale
        self.image = transform.rotozoom(self.bomb_images[0], self.angle, self.scale)
        self.rate = sfg.Effect.BOMB_RATE
        self.frame_add = 0


    def update(self, passed_seconds):
        cur_frame_add = self.frame_add + self.rate * passed_seconds
        if cur_frame_add > len(self.bomb_images):
            self.status = cfg.Magic.STATUS_VANISH
        else:
            if int(cur_frame_add) != int(self.frame_add):
                # change bomb image
                self.image = transform.rotozoom(
                    self.bomb_images[int(cur_frame_add)], self.angle, self.scale)

            self.frame_add = cur_frame_add



class SelfDestruction(MagicSkill):
    def __init__(self, sprite, target_list, damage, trigger_times, 
        thump_crick_time, thump_acceleration, thump_out_speed):
        super(SelfDestruction, self).__init__()
        self.sprite = sprite
        self.damage = damage
        self.thump_crick_time = thump_crick_time
        self.thump_acceleration = thump_acceleration
        self.thump_out_speed = thump_out_speed
        self.target_list = target_list
        self.has_hits = set()
        self.trigger_times = trigger_times
        self.passed_seconds = 0
        self.magic_sprites = []


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            self.trigger_times.pop(0)
            pos = self.sprite.pos.copy()
            pos.x = randint(int(pos.x - 30), int(pos.x + 30))
            pos.y = randint(int(pos.y - 30), int(pos.y + 30))
            scale = max(0.9, random() * 2)
            dx = 32 * scale
            dy = randint(64, 96)
            #scale = 1
            angle = randint(-180, 180)
            bomb = Bomb(pos, dx, dy, self.damage, angle, scale)
            self.magic_sprites.append(bomb)

        for i, bomb in enumerate(self.magic_sprites):
            bomb.update(passed_seconds)
            if bomb.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)
                continue

            for sp in self.target_list:
                if sp not in self.has_hits and sp.area.colliderect(bomb.area):
                    self.has_hits.add(sp)
                    damage = bomb.damage
                    sp.attacker.handle_under_attack(self.sprite, damage)
                    sp.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                        {"crick_time": self.thump_crick_time, 
                        "out_speed": self.thump_out_speed, 
                        "acceleration": self.thump_acceleration,
                        "key_vec": Vector2.from_points(self.sprite.pos, sp.pos)})

        if len(self.trigger_times) == 0 and len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH



class EnergyBall(MagicSprite):
    def __init__(self, pos, radius, dx, dy, damage, image, shadow, target_pos, range, speed):
        super(EnergyBall, self).__init__(pos, radius, dx, dy, damage, image, shadow)
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


    def draw(self, camera):
        if self.status == cfg.Magic.STATUS_ALIVE:
            camera.screen.blit(self.image_mix,
                (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy))
            #r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
            #r.center = (self.pos.x, self.pos.y * 0.5)
            #r.top -= camera.rect.top
            #r.left -= camera.rect.left
            #pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)



class EnergyBallSet(MagicSkill):
    def __init__(self, image, shadow, sprite, target_list, static_objects, params, pos, target_pos):
        super(EnergyBallSet, self).__init__()
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
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

                if sp.status.get(cfg.SpriteStatus.IN_AIR) is None and sp.area.colliderect(msp.area):
                    damage = msp.damage
                    if hasattr(sp.setting, "MAGIC_RESISTANCE_SCALE"):
                        damage = int(damage / sp.setting.MAGIC_RESISTANCE_SCALE)
                    sp.attacker.handle_under_attack(self.sprite, damage)
                    self.has_hits.add(sp)

            for obj in self.static_objects:
                if not obj.setting.IS_ELIMINABLE and obj.area.colliderect(msp.area):
                    msp.status = cfg.Magic.STATUS_VANISH

        if vanish_num == len(self.magic_sprites):
            self.status = cfg.Magic.STATUS_VANISH



class DestroyFire(EnergyBallSet):
    # Renne skill
    destroy_fire_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_FIRE_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_FIRE_RECT)
    shadow = {"image": animation.get_shadow_image(sfg.Effect.DESTROY_FIRE_SHADOW_INDEX),
        "dy": sfg.Effect.DESTROY_FIRE_SHADOW_RECT_DELTA_Y}
    def __init__(self, sprite, target_list, static_objects, params, pos, target_pos):
        super(DestroyFire, self).__init__(self.destroy_fire_image, self.shadow,
            sprite, target_list, static_objects, params, pos, target_pos)
        self.crick_time = params["crick_time"]
        self.tag_cricks = set()


    def update(self, passed_seconds):
        super(DestroyFire, self).update(passed_seconds)
        for sp in self.has_hits:
            if sp in self.tag_cricks:
                continue

            self.tag_cricks.add(sp)
            sp.attacker.handle_additional_status(cfg.SpriteStatus.CRICK, 
                {"time": self.crick_time, "old_action": sp.action})



class DestroyBomb(MagicSprite):
    shadow = {"image": animation.get_shadow_image(sfg.Effect.DESTROY_BOMB_SHADOW_INDEX),
        "dy": sfg.Effect.DESTROY_BOMB_SHADOW_RECT_DELTA_Y}
    def __init__(self, pos, radius, dx, dy, damage, image, life, shake_on_x, shake_on_y):
        super(DestroyBomb, self).__init__(pos, radius, dx, dy, damage, image, self.shadow)
        self.pos.x = gauss(self.pos.x, shake_on_x)
        self.pos.y = gauss(self.pos.y, shake_on_y)
        self.area.center = self.pos
        self.life = life
        self.alive_time = 0


    def update(self, passed_seconds):
        self.alive_time += passed_seconds
        if self.alive_time > self.life:
            self.status = cfg.Magic.STATUS_VANISH
        


class DestroyBombSet(MagicSkill):
    # Renne skill
    destroy_bombs_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_BOMB_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_BOMB_RECT)
    destroy_bomb_images = []
    for i in xrange(3):
        for j in xrange(2):
            destroy_bomb_images.append(destroy_bombs_image.subsurface((i * 64, j * 64, 64, 64)))

    def __init__(self, sprite, target_list, static_objects, params, pos, direction):
        super(DestroyBombSet, self).__init__()
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.origin_pos = pos.copy()
        self.params = params
        self.speed = params["speed"]
        self.range = params["range"]

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
            (vec + vec_left).normalize(), (vec + vec_right).normalize()]

        self.magic_sprites = []
        self.has_hits = set()


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
                if sp.status.get(cfg.SpriteStatus.IN_AIR) is None and sp.area.colliderect(bomb.area):
                    damage = bomb.damage
                    if hasattr(sp.setting, "MAGIC_RESISTANCE_SCALE"):
                        damage = int(damage / sp.setting.MAGIC_RESISTANCE_SCALE)
                    sp.attacker.handle_under_attack(self.sprite, damage)
                    self.has_hits.add(sp)
                    break

        for i, bomb in enumerate(self.magic_sprites):
            bomb.update(passed_seconds)
            if bomb.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)



class DestroyAerolite(MagicSprite):
    shadow = {"image": animation.get_shadow_image(sfg.Effect.DESTROY_AEROLITE_SHADOW_INDEX),
        "dy": sfg.Effect.DESTROY_AEROLITE_SHADOW_RECT_DELTA_Y}
    def __init__(self, pos, radius, dx, dy, damage, image, fall_range, acceleration, damage_cal_time,
            life, shake_on_x, shake_on_y):
        super(DestroyAerolite, self).__init__(pos, radius, dx, dy, damage, image, self.shadow)
        self.pos.x = randint(int(self.pos.x - shake_on_x), int(self.pos.x + shake_on_x))
        self.pos.y = randint(int(self.pos.y - shake_on_y), int(self.pos.y + shake_on_y))
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

        #if self.alive_time > self.damage_cal_time:
        #    r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        #    r.center = (self.pos.x, self.pos.y * 0.5)
        #    r.top -= camera.rect.top
        #    r.left -= camera.rect.left
        #    pygame.draw.rect(camera.screen, pygame.Color("red"), r, 1)


    def draw(self, camera):
        # overwrite for special method
        camera.screen.blit(self.image_mix,
            (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy + self.fall_s))
        


class DestroyAeroliteSet(MagicSkill):
    # Renne skill
    destroy_aerolite_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_AEROLITE_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_AEROLITE_RECT)
    def __init__(self, sprite, target_list, static_objects, params, pos):
        super(DestroyAeroliteSet, self).__init__()
        self.sprite = sprite
        self.target_list = target_list
        self.static_objects = static_objects
        self.params = params
        self.has_hits = set()
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
                    and sp.status.get(cfg.SpriteStatus.IN_AIR) is None \
                    and aerolite.alive_time > aerolite.damage_cal_time \
                    and sp.area.colliderect(aerolite.area):
                    # aerolite hit the target
                    self.has_hits.add(sp)
                    damage = aerolite.damage
                    if hasattr(sp.setting, "MAGIC_RESISTANCE_SCALE"):
                        damage = int(damage / sp.setting.MAGIC_RESISTANCE_SCALE)
                    sp.attacker.handle_under_attack(self.sprite, damage)
                    sp.attacker.handle_additional_status(cfg.SpriteStatus.STUN, 
                        {"time": self.params["stun_time"]})
                    sp.set_emotion(cfg.SpriteEmotion.STUN)

        if len(self.trigger_times) == 0 and len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH



class RenneDizzy(MagicSkill):
    # Renne skill
    def __init__(self, sprite, target_list, dizzy_range, dizzy_time, effective_time, prob):
        super(RenneDizzy, self).__init__()
        self.sprite = sprite
        self.target_list = target_list
        self.dizzy_range = dizzy_range
        self.dizzy_time = dizzy_time
        self.effective_time = effective_time
        self.prob = prob
        self.dizzy_targets = set()
        # actually no magic sprite in this skill, but this variable should exist in every magic skill
        self.magic_sprites = []


    def update(self, passed_seconds):
        sp = self.sprite
        for target in self.target_list:
            if sp.pos.get_distance_to(target.pos) < self.dizzy_range \
                and target not in self.dizzy_targets:
                self.dizzy_targets.add(target)
                if happen(self.prob):
                    target.attacker.handle_additional_status(cfg.SpriteStatus.DIZZY, 
                        {"time": self.dizzy_time})
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
    shadow = {"image": animation.get_shadow_image(sfg.Effect.DEATH_COIL_SHADOW_INDEX),
        "dy": sfg.Effect.DEATH_COIL_SHADOW_RECT_DELTA_Y}
    def __init__(self, sprite, target, static_objects, params, pos, target_pos):
        super(DeathCoil, self).__init__(choice(self.image_list), self.shadow,
            sprite, [target], static_objects, params, pos, target_pos)



class HellClaw(MagicSprite):
    shadow = {"image": animation.get_shadow_image(sfg.Effect.HELL_CLAW_SHADOW_INDEX),
        "dy": sfg.Effect.HELL_CLAW_SHADOW_RECT_DELTA_Y}
    def __init__(self, pos, radius, dx, dy, damage, image, life, damage_cal_time,
            shake_on_x, shake_on_y):
        super(HellClaw, self).__init__(pos, radius, dx, dy, damage, image, self.shadow)
        # make it in a circle
        real_shake_x = randint(-shake_on_x, shake_on_x)
        shake_on_y = int(sqrt(pow(shake_on_x, 2) - pow(real_shake_x, 2)))
        real_shake_y = randint(-shake_on_y, shake_on_y)
        self.pos.x += real_shake_x
        self.pos.y += real_shake_y
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


    def draw(self, camera):
        camera.screen.blit(self.image_mix,
            (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy))
        #r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        #r.center = (self.pos.x, self.pos.y * 0.5)
        #r.top -= camera.rect.top
        #r.left -= camera.rect.left
        #pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)



class HellClawSet(MagicSkill):
    # Leon Hardt skill
    hell_claw_image = animation.effect_image_controller.get(
        sfg.Effect.HELL_CLAW_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.HELL_CLAW_RECT)
    claw_image_list = [hell_claw_image.subsurface((i * 64, 0, 64, 72)) for i in xrange(2)]
    def __init__(self, sprite, target, static_objects, params):
        super(HellClawSet, self).__init__()
        self.sprite = sprite
        self.target = target
        self.target_pos = target.pos.copy()
        self.static_objects = static_objects
        self.range = params["range"]
        self.params = params
        self.trigger_times = list(params["trigger_times"])
        self.passed_seconds = 0
        self.img_id = 0
        self.has_hits = set()
        self.magic_sprites = []

        # hell claw has a ellipse for telling the player that this skill is coming!
        self.tips_area = pygame.Surface((
            self.params["claw_shake_on_x"] * 2 + 20, 
            self.params["claw_shake_on_x"] + 10)).convert_alpha()
        self.tips_area.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.ellipse(self.tips_area, pygame.Color(255, 0, 0, 128), self.tips_area.get_rect())
        self.blink = Blink()
        self.tips_area_mix = self.tips_area.copy()


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
        else:
            # update tips area util this magic skill is vanish
            self.tips_area_mix = self.blink.make(self.tips_area, passed_seconds)


    def draw(self, camera):
        r = self.tips_area_mix.get_rect()
        r.center = self.target_pos("xy")
        r.centery *= 0.5
        camera.screen.blit(self.tips_area_mix, (r.x - camera.rect.x, r.y - camera.rect.y))



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
        sp.status[cfg.SpriteStatus.UNDER_ATTACK] = {"time": sfg.Sprite.UNDER_ATTACK_EFFECT_TIME}
        sp.animation.show_cost_hp(cost_hp)
        if sp.setting.ROLE == cfg.SpriteRole.ENEMY:
            sp.cal_angry(cost_hp)
            sp.set_target(from_who)


    def handle_additional_status(self, status_id, status_object):
        # do some rejection check for some status
        sp = self.sprite
        if status_id == cfg.SpriteStatus.UNDER_THUMP:
            for reject_thump_status in cfg.SpriteStatus.REJECT_THUMP_STATUS_LIST:
                if sp.status.get(reject_thump_status) is not None:
                    return

        sp.status[status_id] = status_object


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
            and cos_val >= self.cos_min and target.status["hp"] != cfg.HpStatus.DIE:
            if target.status.get(cfg.SpriteStatus.IN_AIR) is not None:
                # check whether target is in air status, then compare in-air height with its own height
                if sp.setting.HEIGHT * 0.5 < target.status[cfg.SpriteStatus.IN_AIR]["height"]:
                    return False

            self.has_hits.add(target)
            return True

        return False



class Ammo(pygame.sprite.DirtySprite):
    """
    just like a magic sprite
    """
    def __init__(self, pos, radius, speed, key_vec, dx, dy, damage, image, shadow):
        super(Ammo, self).__init__()
        self.pos = Vector2(pos)
        self.origin_pos = self.pos.copy()
        self.area = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.area.center = self.pos
        self.speed = speed
        self.key_vec = Vector2(key_vec).normalize()
        self.damage = damage
        self.dx = dx
        self.dy = dy
        self.image = image
        self.shadow = shadow


    def update(self, passed_seconds):
        self.pos += self.key_vec * self.speed * passed_seconds
        self.area.center = self.pos("xy")


    def draw_shadow(self, camera):
        shd_rect = self.shadow["image"].get_rect()
        shd_rect.center = self.pos
        camera.screen.blit(self.shadow["image"],
            (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y - self.shadow["dy"]))


    def draw(self, camera):
        if self.image is not None:
            camera.screen.blit(self.image,
                (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy))

        #r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        #r.center = (self.pos.x, self.pos.y * 0.5)
        #r.top -= camera.rect.top
        #r.left -= camera.rect.left
        #pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)



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
        # magic_list has kinds of magics, eg. DestroyBombSet and DestroyAeroliteSet, 
        # every magic has one or more magic sprite(s), eg. DestroyBombSet has many "bombs"
        self.magic_list = []
        # a lock, only one magic is running in an attack
        self.current_magic = None
        self.method = None


    def run(self, enemy, current_frame_add):
        if self.hit(enemy, current_frame_add):
            damage = max(0, self.sprite.atk - enemy.dfs)
            enemy.attacker.handle_under_attack(self.sprite, damage)
            if hasattr(enemy.setting, "ATK_REBOUNCE"):
                self.sprite.attacker.handle_under_attack(enemy, damage)
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
        if self.current_magic is None and int(current_frame_add) in self.destroy_aerolite_params["key_frames"]:
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
                if sp.status["hp"] == cfg.HpStatus.DIE:
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
            damage = max(0, self.sprite.atk - hero.dfs)
            hero.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False
        

    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()



class EnemyPoisonShortAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(EnemyPoisonShortAttacker, self).__init__(sprite, attacker_params)
        self.poison_dps = attacker_params["poison_damage_per_second"]
        self.poison_time = attacker_params["poison_persist_time"]
        self.poison_prob = attacker_params["poison_prob"]


    def run(self, hero, current_frame_add):
        hit_it = super(EnemyPoisonShortAttacker, self).run(hero, current_frame_add)
        # add additional poison damage
        if hit_it and happen(self.poison_prob):
            hero.attacker.handle_additional_status(cfg.SpriteStatus.POISON, 
                {"dps": self.poison_dps, "time_list": range(self.poison_time), 
                "time_left": self.poison_time})
            words = sfg.Font.ARIAL_BLACK_24.render("Poison!", True, pygame.Color("green"))
            sp = self.sprite
            sp.animation.show_words(words, 0.3, 
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))
        return hit_it



class EnemyLeakShortAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(EnemyLeakShortAttacker, self).__init__(sprite, attacker_params)
        self.leak_prob = attacker_params["leak_prob"]
        self.leak_mp = attacker_params["leak_mp"]
        self.leak_sp = attacker_params["leak_sp"]


    def run(self, hero, current_frame_add):
        hit_it = super(EnemyLeakShortAttacker, self).run(hero, current_frame_add)
        if hit_it and happen(self.leak_prob):
            hero.mp = max(0, hero.mp - self.leak_mp)
            hero.sp = max(0, hero.sp - self.leak_sp)
            words = sfg.Font.ARIAL_BLACK_24.render("Leak!", True, pygame.Color("black"))
            sp = self.sprite
            sp.animation.show_words(words, 0.3, 
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))

        return hit_it



class EnemyThumpShortAttacker(EnemyShortAttacker):
    # thump hero, make her back a distance
    def __init__(self, sprite, attacker_params):
        super(EnemyThumpShortAttacker, self).__init__(sprite, attacker_params)
        self.thump_crick_time = attacker_params["thump_crick_time"]
        self.thump_out_speed = attacker_params["thump_out_speed"]
        self.thump_acceleration = attacker_params["thump_acceleration"]
        self.thump_pre_freeze_time = attacker_params["thump_pre_freeze_time"]
        self.thump_pre_frames = attacker_params["thump_pre_frames"]
        self.thump_pre_rate = attacker_params["thump_pre_rate"]
        self.thump_frame = attacker_params["thump_frame"]
        self.thump_slide_time = attacker_params["thump_slide_time"]
        self.thump_slide_speed = attacker_params["thump_slide_speed"]
        self.thump_slide_range = self.thump_slide_speed * self.thump_slide_time
        self.thump_cos_min = attacker_params["thump_cos_min"]
        self.thump_slide_time_add = 0
        self.thump_pre_freeze_time_add = 0
        self.method = None


    def thump_chance(self, target):
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if distance_to_target <= self.attack_range + self.thump_slide_range:
            direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
            vec_to_target = Vector2.from_points(sp.area.center, target.area.center)
            cos_val = cos_for_vec(direct_vec, vec_to_target)
            if cos_val >= self.thump_cos_min and \
                self.sprite.view_sensor.detect(target) is not None:
                return True

        return False


    def chance(self, target):
        sp = self.sprite
        if happen(sp.brain.ai.ATTACK_THUMP_PROB) and self.thump_chance(target):
            self.method = "thump"
            return True

        if super(EnemyThumpShortAttacker, self).chance(target):
            self.method = "regular"
            return True

        return False


    def run(self, hero, current_frame_add):
        sp = self.sprite
        if self.hit(hero, current_frame_add):
            atk = sp.atk
            if self.method == "thump":
                # thump results in a double attack and hero-fallback
                atk *= 2
                words = sfg.Font.ARIAL_BLACK_24.render("Thump!", True, pygame.Color("gold"))
                sp.animation.show_words(words, 0.3, 
                    (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))
                if hero.status.get(cfg.SpriteStatus.UNDER_THUMP) is None:
                    hero.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                        {"crick_time": self.thump_crick_time, 
                        "out_speed": self.thump_out_speed, 
                        "acceleration": self.thump_acceleration,
                        "key_vec": Vector2.from_points(sp.pos, hero.pos)})

            damage = max(0, atk - hero.dfs)
            hero.attacker.handle_under_attack(sp, damage)
            return True

        return False


    def finish(self):
        super(EnemyThumpShortAttacker, self).finish()
        self.method = None
        self.thump_slide_time_add = 0
        self.thump_pre_freeze_time_add = 0



class EnemyBloodShortAttacker(EnemyShortAttacker):
    # suck blood in attack
    def __init__(self, sprite, attacker_params):
        super(EnemyBloodShortAttacker, self).__init__(sprite, attacker_params)
        self.suck_blood_ratio = attacker_params["suck_blood_ratio"]


    def run(self, hero, current_frame_add):
        hit_it = super(EnemyBloodShortAttacker, self).run(hero, current_frame_add)
        if hit_it:
            sp = self.sprite
            sp.hp = min(sp.hp + self.suck_blood_ratio * sp.setting.ATK, sp.setting.HP)
            sp.status["hp"] = sp.cal_sprite_status(sp.hp, sp.setting.HP)
            words = sfg.Font.ARIAL_BLACK_24.render("Blood!", True, pygame.Color("darkred"))
            sp.animation.show_words(words, 0.3,
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))

        return hit_it



class TwoHeadSkeletonAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(TwoHeadSkeletonAttacker, self).__init__(sprite, attacker_params)
        self.method = None
        self.fall_range = attacker_params["fall_range"]
        self.fall_run_up_time = attacker_params["fall_run_up_time"]
        self.fall_run_up_rate = attacker_params["fall_run_up_rate"]
        self.fall_kneel_time = attacker_params["fall_kneel_time"]
        self.fall_acceleration = attacker_params["fall_acceleration"]
        self.fall_v0_y = attacker_params["fall_v0_y"]
        self.fall_back_v0_y = attacker_params["fall_back_v0_y"]
        self.fall_in_air_time = (-self.fall_v0_y * 2.0) / self.fall_acceleration
        self.fall_back_in_air_time = (-self.fall_back_v0_y * 2.0) / self.fall_acceleration
        self.fall_damage = attacker_params["fall_damage"]
        self.fall_thump_crick_time = attacker_params["fall_thump_crick_time"]
        self.fall_thump_acceleration = attacker_params["fall_thump_acceleration"]
        self.fall_thump_out_speed = attacker_params["fall_thump_out_speed"]

        self.fall_run_up_time_add = 0
        self.fall_kneel_time_add = 0
        self.fall_in_air_time_add = 0
        self.fall_back_in_air_time_add = 0
        self.fall_in_air_height = 0
        self.fall_in_air_v_x = None
        self.fall_in_air_speed_x = None


    def fall_chance(self, target):
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if self.fall_range[0] <= distance_to_target <= self.fall_range[1]:
            self.fall_in_air_v_x = float(distance_to_target) / self.fall_in_air_time
            return True
        return False


    def fall_hit(self, hero):
        if hero in self.has_hits:
            return False

        sp = self.sprite
        if sp.area.colliderect(hero.area):
            self.has_hits.add(hero)
            return True

        return False


    def chance(self, target):
        sp = self.sprite
        if happen(sp.brain.ai.ATTACK_FALL_PROB) and self.fall_chance(target):
            self.method = "fall"
            return True

        if super(TwoHeadSkeletonAttacker, self).chance(target):
            self.method = "regular"
            return True

        return False


    def run(self, hero, current_frame_add):
        if self.method == "regular":
            return super(TwoHeadSkeletonAttacker, self).run(hero, current_frame_add)
        elif self.method == "fall":
            if self.fall_hit(hero):
                sp = self.sprite
                hero.attacker.handle_under_attack(sp, self.fall_damage)
                hero.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP, 
                    {"crick_time": self.fall_thump_crick_time, "out_speed": self.fall_thump_out_speed,
                    "acceleration": self.fall_thump_acceleration, 
                    "key_vec": Vector2.from_points(sp.pos, hero.pos)})
                return True

        return False


    def finish(self):
        super(TwoHeadSkeletonAttacker, self).finish()
        self.method = None
        self.fall_run_up_time_add = 0
        self.fall_kneel_time_add = 0
        self.fall_in_air_time_add = 0
        self.fall_back_in_air_time_add = 0
        self.fall_in_air_height = 0
        self.fall_in_air_v_x = None
        self.fall_in_air_speed_x = None



class EnemyFrozenShortAttacker(EnemyShortAttacker):
    # frozen effect attacker
    def __init__(self, sprite, attacker_params):
        super(EnemyFrozenShortAttacker, self).__init__(sprite, attacker_params)
        self.frozen_prob = attacker_params["frozen_prob"]
        self.frozen_time = attacker_params["frozen_time"]
        self.action_rate_scale = attacker_params["action_rate_scale"]


    def run(self, hero, current_frame_add):
        hit_it = super(EnemyFrozenShortAttacker, self).run(hero, current_frame_add)
        if hit_it and happen(self.frozen_prob):
            hero.attacker.handle_additional_status(cfg.SpriteStatus.FROZEN, 
                {"time_left": self.frozen_time, "action_rate_scale": self.action_rate_scale})
            words = sfg.Font.ARIAL_BLACK_24.render("Frozen!", True, pygame.Color("cyan"))
            sp = self.sprite
            sp.animation.show_words(words, 0.3, 
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))
        return hit_it



class EnemyWeakShortAttacker(EnemyShortAttacker):
    # give hero weak status
    def __init__(self, sprite, attacker_params):
        super(EnemyWeakShortAttacker, self).__init__(sprite, attacker_params)
        self.weak_prob = attacker_params["weak_prob"]
        self.weak_time = attacker_params["weak_time"]
        self.weak_atk = attacker_params["weak_atk"]
        self.weak_dfs = attacker_params["weak_dfs"]
    

    def run(self, hero, current_frame_add):
        hit_it = super(EnemyWeakShortAttacker, self).run(hero, current_frame_add)
        if hit_it and happen(self.weak_prob):
            hero.attacker.handle_additional_status(cfg.SpriteStatus.WEAK, 
                {"time_left": self.weak_time, "y": 0})
            hero.atk = max(0, hero.atk - self.weak_atk)
            hero.dfs = max(0, hero.dfs - self.weak_dfs)
            words = sfg.Font.ARIAL_BLACK_24.render("Weak!", True, pygame.Color("gray"))
            sp = self.sprite
            sp.animation.show_words(words, 0.3, 
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))
        return hit_it



class EnemyImpaleShortAttacker(EnemyShortAttacker):
    def run(self, hero, current_frame_add):
        if self.hit(hero, current_frame_add):
            # regardless of hero's dfs
            damage = self.sprite.atk
            hero.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False



class EnemySelfDestructionAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(EnemySelfDestructionAttacker, self).__init__(sprite, attacker_params)
        self.magic_list = []
        self.method = None
        self.bomb_damage = attacker_params["bomb_damage"]
        self.bomb_trigger_times = list(attacker_params["bomb_trigger_times"])
        self.bomb_thump_crick_time = attacker_params["bomb_thump_crick_time"]
        self.bomb_thump_acceleration = attacker_params["bomb_thump_acceleration"]
        self.bomb_thump_out_speed = attacker_params["bomb_thump_out_speed"]


    def run(self, hero, current_frame_add):
        if self.method is None:
            # only use self-destruction
            self.method = "self_destruction"
            self_destruction = SelfDestruction(self.sprite, [hero, ], self.bomb_damage, self.bomb_trigger_times, 
                self.bomb_thump_crick_time, self.bomb_thump_acceleration, self.bomb_thump_out_speed)
            self.magic_list.append(self_destruction)
            return False
        else:
            if len(self.magic_list) == 0:
                # self-destruction is over!
                return True
            else:
                return False



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
            if cos_val >= self.cos_min and self.sprite.view_sensor.detect(target) is not None:
                return True

        return False


    def run(self, hero, current_frame_add):
        if self.hit(hero, current_frame_add):
            damage = max(0, self.sprite.atk - hero.dfs)
            hero.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False


    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()



class ArrowAttacker(EnemyLongAttacker):
    """
    attacker that has ammo sprite to calculate hit and draw
    """
    arrow_images = animation.battle_images.get(sfg.Ammo.ARROW_IMAGE_KEY)
    arrow_image_list = [arrow_images.subsurface(
        pygame.Rect((0, i * sfg.Ammo.ARROW_HEIGHT), (sfg.Ammo.ARROW_WIDTH, sfg.Ammo.ARROW_HEIGHT))) \
        for i in xrange(cfg.Direction.TOTAL)]
    shadow = {"image": animation.get_shadow_image(sfg.Ammo.ARROW_SHADOW_INDEX),
        "dy": sfg.Ammo.ARROW_SHADOW_DY}
    def __init__(self, sprite, attacker_params):
        super(ArrowAttacker, self).__init__(sprite, attacker_params)
        self.hero = sprite.hero # you see it's an attacker only for enemy...
        self.static_objects = sprite.static_objects
        self.current_ammo = None
        self.ammo_list = []
        self.arrow_radius = attacker_params["arrow_radius"]
        self.arrow_speed = attacker_params["arrow_speed"]
        self.arrow_dx = attacker_params["arrow_dx"]
        self.arrow_dy = attacker_params["arrow_dy"]
        self.arrow_damage = attacker_params["arrow_damage"]


    def run(self, hero, current_frame_add):
        sp = self.sprite
        if self.current_ammo is None and int(current_frame_add) in self.key_frames:
            # generate arrow
            self.current_ammo = Ammo(sp.pos, self.arrow_radius, self.arrow_speed, 
                cfg.Direction.DIRECT_TO_VEC[sp.direction], self.arrow_dx, self.arrow_dy, self.arrow_damage, 
                self.arrow_image_list[sp.direction], self.shadow)
            self.ammo_list.append(self.current_ammo)


    def update_ammo(self, passed_seconds):
        for i, am in enumerate(self.ammo_list):
            am.update(passed_seconds)
            if am.area.colliderect(self.hero.area):
                self.hero.attacker.handle_under_attack(self.sprite, self.arrow_damage)
                self.ammo_list.pop(i)

            elif am.pos.get_distance_to(am.origin_pos) > self.attack_range:
                self.ammo_list.pop(i)

            else:
                for obj in self.static_objects:
                    if not obj.setting.IS_ELIMINABLE and \
                        obj.setting.IS_VIEW_BLOCK and \
                        am.area.colliderect(obj.area):
                        self.ammo_list.pop(i)
                        break


    def finish(self):
        self.current_ammo = None



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
        if self.current_magic is None and int(current_frame_add) in self.death_coil_params["key_frames"]:
            sp.mp -= self.death_coil_params["mana"]
            self.current_magic = DeathCoil(sp, target,
                sp.static_objects, self.death_coil_params, sp.pos, target.pos)
            self.magic_list.append(self.current_magic)


    def hell_claw(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None:
            # this magic trigger at once for showing the tips, 
            # but damage claws will trigger at a certain delay
            sp.mp -= self.hell_claw_params["mana"]
            self.current_magic = HellClawSet(sp, target, 
                sp.static_objects, self.hell_claw_params)
            self.magic_list.append(self.current_magic)


    def run(self, hero, current_frame_add):
        if self.hit(hero, current_frame_add):
            damage = max(0, self.sprite.atk - hero.dfs)
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
    sfg.CastleWarrior.ID: EnemyThumpShortAttacker,
    sfg.SkeletonArcher.ID: ArrowAttacker,
    sfg.LeonHardt.ID: LeonhardtAttacker,
    sfg.ArmouredShooter.ID: EnemyLongAttacker,
    sfg.SwordRobber.ID: EnemyWeakShortAttacker,
    sfg.SkeletonWarrior2.ID: EnemyPoisonShortAttacker,
    sfg.Ghost.ID: EnemyLeakShortAttacker,
    #sfg.TwoHeadSkeleton.ID: EnemyBloodShortAttacker,
    sfg.TwoHeadSkeleton.ID: TwoHeadSkeletonAttacker,
    sfg.Werwolf.ID: EnemyFrozenShortAttacker,
    sfg.SilverTentacle.ID: EnemyImpaleShortAttacker,
    sfg.Robot.ID: EnemySelfDestructionAttacker,
}


if __name__ == "__main__":
    pass
