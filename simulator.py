# -*- coding: gbk -*-

import pygame
from pygame.locals import BLEND_ADD
from pygame import transform
from base.util import LineSegment, line_segment_intersect_with_rect, cos_for_vec
from base.util import manhattan_distance, Timer, happen, Blink
import math
from random import gauss, randint, choice, random, sample
from math import pow, radians, sqrt, tan, cos
from time import time
from gameobjects.vector2 import Vector2
import animation
from controller import cal_face_direct
from base import constant as cfg
from etc import setting as sfg



class MagicSprite(pygame.sprite.DirtySprite):
    """
    represent some magic unit
    """
    def __init__(self, pos, radius, dx, dy, damage, image, shadow=None):
        super(MagicSprite, self).__init__()
        self.pos = Vector2(pos)
        self.area = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.area.center = self.pos
        self.damage = damage
        # dx and dy is used to fix the blit position for sprite image, x and y axis respectively
        self.dx = dx
        self.dy = dy
        self.image = image
        self.shadow = shadow
        self.status = cfg.Magic.STATUS_ALIVE
        self.layer = cfg.Magic.LAYER_AIR


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
    def __init__(self, sprite, target_list):
        self.sprite = sprite
        self.block_points = sprite.game_map.block_points
        self.target_list = target_list
        self.status = cfg.Magic.STATUS_ALIVE
        self.has_hits = set()
        self.magic_sprites = []


    def reachable(self, p):
        bps = self.block_points
        step = sfg.BlockPoint.STEP_WIDTH
        block_cnt = 0
        x0 = p.x - p.x % step
        y0 = p.y - p.y % step
        for p in ((x0, y0), (x0 + step, y0), (x0, y0 + step), (x0 + step, y0 + step)):
            if p in bps:
                block_cnt += 1

        return block_cnt < 2


    def update(self, passed_seconds):
        pass


    def draw(self, camera):
        pass



class IceColumn(MagicSprite):
    ice_column_image = animation.effect_image_controller.get(
        sfg.Effect.ICE_IMAGE_KEY).subsurface(sfg.Effect.ICE_COLUMN_RECT).convert_alpha()
    def __init__(self, pos, damage, life):
        super(IceColumn, self).__init__(pos, sfg.Effect.ICE_COLUMN_RADIUS, 
            sfg.Effect.ICE_COLUMN_DX, sfg.Effect.ICE_COLUMN_DY, damage, self.ice_column_image)
        self.life = life


    def update(self, passed_seconds):
        self.life -= passed_seconds
        if self.life < 0:
            self.status = cfg.Magic.STATUS_VANISH



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



class Poison(MagicSprite):
    def __init__(self, pos, radius, dx, dy, damage, image, height, key_vec, speed, fall_acceleration, 
        life_time):
        super(Poison, self).__init__(pos, radius, dx, dy, damage, image)
        self.origin_image_on_floor = None
        self.origin_dy = self.dy
        self.key_vec = key_vec
        self.speed = speed
        # notice here, if height is positive, fall_acceleration should be negative
        self.height = abs(height)
        self.fall_acceleration = -abs(fall_acceleration)
        self.v_y = 0
        self.life_time_left = life_time
        self.fade_out_list = [{"life_time_left": i * life_time, "scale_ratio": i} for i in [0.7, 0.5]]
        self.effective = True


    def update(self, passed_seconds):
        self.life_time_left -= passed_seconds
        if self.height <= 0:
            # on the floor
            if len(self.fade_out_list) > 0 and self.life_time_left < self.fade_out_list[0]["life_time_left"]:
                # change image, fade it out step by step
                scale_ratio = self.fade_out_list.pop(0)["scale_ratio"]
                self.image = transform.rotozoom(self.origin_image_on_floor, 0, scale_ratio)
                self.dx *= scale_ratio
                self.dy *= scale_ratio
                self.area.width *= scale_ratio
                self.area.height *= scale_ratio
                self.area.center = self.pos("xy") # reassign area center
                if len(self.fade_out_list) == 0:
                    self.effective = False

        else:
            # in the air
            self.pos += self.key_vec * self.speed * passed_seconds
            self.area.center = self.pos("xy")
            self.height += self.v_y * passed_seconds + 0.5 * self.fall_acceleration * pow(passed_seconds, 2)
            self.v_y += self.fall_acceleration * passed_seconds
            self.dy = self.origin_dy + self.height
            if self.height <= 0:
                # the poison is now on the floor, keep an original image copy for scale further
                self.origin_image_on_floor = self.image.copy()
                self.layer = cfg.Magic.LAYER_FLOOR

        if self.life_time_left <= 0:
            self.status = cfg.Magic.STATUS_VANISH



class PoisonSet(MagicSkill):
    poison_image_list = []
    def __init__(self, sprite, target_list, static_objects, params):
        super(PoisonSet, self).__init__(sprite, target_list)
        self.init_poison_image_list()
        self.static_objects = static_objects
        self.params = params
        self.gen_magic_sprites()


    def init_poison_image_list(self):
        if len(self.poison_image_list) == 0:
            img = animation.effect_image_controller.get(sfg.Effect.POISON_IMAGE_KEY)

            img1 = img.subsurface(sfg.Effect.POISON_RECT1).convert_alpha()
            self.poison_image_list.extend([img1.subsurface((i * 32, 0, 32, 32)) for i in xrange(3)])

            img2 = img.subsurface(sfg.Effect.POISON_RECT2).convert_alpha()
            self.poison_image_list.extend([img2.subsurface((i * 32, 0, 32, 32)) for i in xrange(4)])
            self.poison_image_list.extend([img2.subsurface((i * 32, 32, 32, 32)) for i in xrange(4)])

            img3 = img.subsurface(sfg.Effect.POISON_RECT3).convert_alpha()
            self.poison_image_list.append(img3.subsurface((64, 0, 64, 64)))
            self.poison_image_list.append(img3.subsurface((0, 64, 64, 64)))
            self.poison_image_list.append(img3.subsurface((64, 64, 64, 64)))


    def gen_magic_sprites(self):
        sp = self.sprite
        imgs = sample(self.poison_image_list, self.params["num"])
        for img in imgs:
            # add some noise for key_vec of poison that spit out!
            key_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
            key_vec.x = gauss(key_vec.x, 0.1)
            key_vec.y = gauss(key_vec.y, 0.1)
            radius = img.get_width() * 0.5
            # add some noise for speed
            speed = gauss(self.params["speed"], self.params["speed"] / 5)

            img = transform.rotate(img, randint(-180, 180))
            tf_img = transform.smoothscale(img, (img.get_width(), img.get_height() / 2))
            dx = tf_img.get_width() * 0.5
            dy = tf_img.get_height() * 0.5

            # add some noise for life time
            life_time = gauss(self.params["life_time"], self.params["life_time"] / 5)

            poison = Poison(sp.pos, radius, dx, dy, self.params["damage"], tf_img, self.params["height"],
                key_vec, speed, self.params["fall_acceleration"], life_time)
            self.magic_sprites.append(poison)


    def update(self, passed_seconds):
        sp = self.sprite
        for i, poison in enumerate(self.magic_sprites):
            for target in self.target_list:
                if target not in self.has_hits \
                    and poison.effective \
                    and poison.area.colliderect(target.area):
                    self.has_hits.add(target)
                    target.attacker.handle_additional_status(cfg.SpriteStatus.POISON,
                        {"dps": self.params["damage"], "time_list": range(self.params["damage_time"]),
                        "time_left": self.params["damage_time"]})
                    target.status[cfg.SpriteStatus.UNDER_ATTACK] = {"time": sfg.Sprite.UNDER_ATTACK_EFFECT_TIME}

            if poison.height > 0 and (not self.reachable(poison.pos)):
                # this poison will no longer move horizontally
                poison.key_vec = Vector2(0, 0)

            poison.update(passed_seconds)
            if poison.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)

        if len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH



class Blood(MagicSprite):
    # handle blood as a MagicSprite
    def __init__(self, pos, radius, dx, dy, image, height, key_vec, speed, fall_acceleration, life_time):
        super(Blood, self).__init__(pos, radius, dx, dy, 0, image)
        self.origin_dy = self.dy
        self.key_vec = key_vec
        self.speed = speed
        self.height = abs(height)
        self.fall_acceleration = -abs(fall_acceleration)
        self.v_y = 0
        self.life_time = life_time


    def update(self, passed_seconds):
        self.life_time -= passed_seconds
        if self.life_time <= 0:
            self.status = cfg.Magic.STATUS_VANISH
            return

        if self.height <= 0:
            return

        self.pos += self.key_vec * self.speed * passed_seconds
        self.area.center = self.pos("xy")
        self.height += self.v_y * passed_seconds + 0.5 * self.fall_acceleration * pow(passed_seconds, 2)
        self.v_y += self.fall_acceleration * passed_seconds
        self.dy = self.origin_dy + self.height
        if self.height <= 0:
            self.layer = cfg.Magic.LAYER_FLOOR



class BloodSet(MagicSkill):
    # handle blood set as a MagicSkill
    image_list = []
    img = animation.effect_image_controller.get(sfg.Effect.BLOOD_IMAGE_KEY)
    for rect in sfg.Effect.BLOOD_RECT_LIST:
        image_list.append(img.subsurface(rect).convert_alpha())

    def __init__(self, sprite, jet_pos, jet_height, blood_num=8):
        super(BloodSet, self).__init__(sprite, [])
        self.blood_num = blood_num
        self.jet_pos = jet_pos
        self.jet_height = jet_height
        self.gen_magic_sprites()


    def gen_magic_sprites(self):
        sp = self.sprite
        vec = cfg.Direction.DIRECT_TO_VEC[(sp.direction + 4) % 8]
        rand_x_min, rand_x_max = (-100, 100) if vec[0] == 0 else (min(vec[0] * 100, 0), max(vec[0] * 100, 0))
        rand_y_min, rand_y_max = (-100, 100) if vec[1] == 0 else (min(vec[1] * 100, 0), max(vec[1] * 100, 0))

        for _tmp in xrange(self.blood_num):
            img = choice(self.image_list)
            key_vec = Vector2(randint(rand_x_min, rand_x_max), randint(rand_y_min, rand_y_max))
            key_vec.normalize()
            radius = img.get_width() * 0.5
            speed = gauss(200, 50)

            r_img = transform.rotate(img, randint(-180, 180))
            tf_img = transform.smoothscale(r_img, (r_img.get_width(), r_img.get_height() / 2))
            dx = tf_img.get_width() * 0.5
            dy = tf_img.get_height() * 0.5
            life_time = gauss(sfg.Effect.BLOOD_LIFE_TIME, 2)

            blood = Blood(self.jet_pos, radius, dx, dy, tf_img, self.jet_height, key_vec, speed,
                sfg.Physics.GRAVITY_ACCELERATION, life_time)
            self.magic_sprites.append(blood)


    def update(self, passed_seconds):
        for i, blood in enumerate(self.magic_sprites):
            blood.update(passed_seconds)
            if blood.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)

        if len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH
    


class SelfDestruction(MagicSkill):
    def __init__(self, sprite, target_list, damage, trigger_times, 
        thump_crick_time, thump_acceleration, thump_out_speed):
        super(SelfDestruction, self).__init__(sprite, target_list)
        self.damage = damage
        self.thump_crick_time = thump_crick_time
        self.thump_acceleration = thump_acceleration
        self.thump_out_speed = thump_out_speed
        self.trigger_times = trigger_times
        self.passed_seconds = 0


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
                    sp.attacker.handle_under_attack(self.sprite, damage, attack_method=cfg.Attack.METHOD_MAGIC)
                    sp.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                        {"crick_time": self.thump_crick_time, 
                        "out_speed": self.thump_out_speed, 
                        "acceleration": self.thump_acceleration,
                        "key_vec": Vector2.from_points(self.sprite.pos, sp.pos)})

        if len(self.trigger_times) == 0 and len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH



class Grenade(MagicSprite):
    g_image = animation.effect_image_controller.get(
        sfg.Effect.GRENADE_IMAGE_KEY).subsurface(sfg.Effect.GRENADE_RECT).convert_alpha()
    land_height_threshold = sfg.Effect.GRENADE_LAND_HEIGHT_THRESHOLD
    vx_loss_rate = sfg.Effect.GRENADE_VX_LOSS_RATE
    vy_loss_rate = sfg.Effect.GRENADE_VY_LOSS_RATE
    def __init__(self, pos, radius, target_list, params):
        super(Grenade, self).__init__(pos, radius, sfg.Effect.GRENADE_DX, sfg.Effect.GRENADE_DY, 0,
            transform.rotate(self.g_image, choice((0, 90, 180, 270))))
        self.origin_image = self.image.copy()
        self.origin_dy = self.dy
        self.blink = Blink()
        self.passed_seconds = 0
        self.gen_bomb_num = 0
        self.phase = "in_air" # in_air, on_floor, disapear

        self.key_vec = Vector2.from_points(self.pos, target_list[0].pos).normalize()
        self.height = params["init_height"]
        self.vx = self.pos.get_distance_to(target_list[0].pos) / self.vx_loss_rate
        self.vy = params["init_vy"]
        # fall_acceleration must be negative against height
        self.fall_acceleration = -abs(params["fall_acceleration"])
        self.trigger_times = list(params["trigger_times"])


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if self.phase == "in_air":
            # s = v0 * t + 0.5 * a * t^2
            s = self.vy * passed_seconds + 0.5 * self.fall_acceleration * pow(passed_seconds, 2)
            self.height += s  
            v1 = self.vy + self.fall_acceleration * passed_seconds
            if self.vy > 0 and v1 <= 0 and self.height <= self.land_height_threshold:
                # land on the floor
                self.phase = "on_floor"
                self.vy = 0
                self.vx = 0

            else:
                self.vy = v1
                if self.height < 0:
                    # touch the floor, vy must set to the same direction with height
                    self.height = abs(self.height)
                    self.vy = abs(self.vy) * self.vy_loss_rate
                    self.vx *= self.vx_loss_rate

                self.pos += self.key_vec * self.vx * passed_seconds

            self.dy = self.origin_dy + self.height

        elif self.phase == "on_floor":
            self.image = self.blink.make(self.origin_image, passed_seconds)
            if self.passed_seconds > self.trigger_times[0]:
                self.phase = "bomb"

        elif self.phase == "bomb":
            if len(self.trigger_times) > 0:
                if self.passed_seconds > self.trigger_times[0]:
                    self.trigger_times.pop(0)
                    self.gen_bomb_num += 1
            else:
                self.status = cfg.Magic.STATUS_VANISH



class GrenadeBomb(MagicSkill):
    def __init__(self, sprite, target_list, params):
        super(GrenadeBomb, self).__init__(sprite, target_list)
        self.damage = params["damage"]
        self.thump_crick_time = params["thump_crick_time"]
        self.thump_acceleration = params["thump_acceleration"]
        self.thump_out_speed = params["thump_out_speed"]
        self.grenades = []
        self.bombs = []
        # only one grenade right now, and double insertion
        gr = Grenade(sprite.pos, sfg.Effect.GRENADE_RADIUS, target_list, params)
        self.grenades.append(gr)
        self.magic_sprites.append(gr)


    def update(self, passed_seconds):
        for i, gr in enumerate(self.grenades):
            gr.update(passed_seconds)
            while gr.gen_bomb_num > 0:
                gr.gen_bomb_num -= 1
                pos = gr.pos.copy()
                pos.x = randint(int(pos.x - 30), int(pos.x + 30))
                pos.y = randint(int(pos.y - 30), int(pos.y + 30))
                scale = max(0.9, random() * 2)
                dx = 32 * scale
                dy = randint(64, 96)
                angle = randint(-180, 180)
                bomb = Bomb(pos, dx, dy, self.damage, angle, scale)
                self.bombs.append(bomb)
                self.magic_sprites.append(bomb)

            if gr.status == cfg.Magic.STATUS_VANISH:
                self.grenades.pop(i)

        for i, bomb in enumerate(self.bombs):
            bomb.update(passed_seconds)
            if bomb.status == cfg.Magic.STATUS_VANISH:
                self.bombs.pop(i)
                continue

            for sp in self.target_list:
                if sp not in self.has_hits and sp.area.colliderect(bomb.area):
                    self.has_hits.add(sp)
                    damage = bomb.damage
                    sp.attacker.handle_under_attack(self.sprite, damage, attack_method=cfg.Attack.METHOD_MAGIC)
                    sp.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                        {"crick_time": self.thump_crick_time, 
                        "out_speed": self.thump_out_speed, 
                        "acceleration": self.thump_acceleration,
                        "key_vec": Vector2.from_points(bomb.pos, sp.pos).normalize()})

        if len(self.grenades) == 0 and len(self.bombs) == 0:
            self.status = cfg.Magic.STATUS_VANISH



class EnergyBall(MagicSprite):
    def __init__(self, pos, radius, dx, dy, damage, image, shadow, target_pos, range, speed):
        super(EnergyBall, self).__init__(pos, radius, dx, dy, damage, image, shadow)
        self.range = range
        self.speed = speed
        self.life_time = float(range) / speed
        self.key_vec = Vector2.from_points(pos, target_pos)
        self.key_vec.normalize()
        self.shadow = shadow
        self.origin_image = self.image.copy()
        self.blink = Blink()

        
    def update(self, passed_seconds):
        self.pos += self.key_vec * self.speed * passed_seconds
        self.area.center = self.pos("xy")
        self.image = self.blink.make(self.origin_image, passed_seconds)
        self.life_time -= passed_seconds
        if self.life_time <= 0:
            self.status = cfg.Magic.STATUS_VANISH



class EnergyBallSet(MagicSkill):
    def __init__(self, image, shadow, sprite, target_list, static_objects, params, pos, target_pos):
        super(EnergyBallSet, self).__init__(sprite, target_list)
        self.static_objects = static_objects
        damage = params["damage"]
        if hasattr(sprite, "magic_skill_damage_ratio"):
            damage *= sprite.magic_skill_damage_ratio
        # only one ball right now
        ball = EnergyBall(pos, params["radius"], params["dx"], params["dy"], 
            damage, image, shadow, target_pos, params["range"], params["speed"])
        self.magic_sprites.append(ball)


    def update(self, passed_seconds):
        vanish_num = 0
        for msp in self.magic_sprites:
            if msp.status == cfg.Magic.STATUS_VANISH:
                vanish_num += 1
                continue

            msp.update(passed_seconds)

            for target in self.target_list:
                if target in self.has_hits:
                    continue

                if target.status.get(cfg.SpriteStatus.IN_AIR) is None and target.area.colliderect(msp.area):
                    damage = msp.damage
                    target.attacker.handle_under_attack(self.sprite, damage, cfg.Attack.METHOD_MAGIC)
                    self.has_hits.add(target)

            if not self.reachable(msp.pos):
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

    bomb_over_effect_id_list = (4, 5)

    def __init__(self, sprite, target_list, static_objects, params, pos, direction):
        super(DestroyBombSet, self).__init__(sprite, target_list)
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

                if self.reachable(bomb.pos):
                    self.magic_sprites.append(bomb)
                else:
                    # this line can be dropped
                    self.pos_list.pop(i)

        if range_over_num == len(self.pos_list):
            self.status = cfg.Magic.STATUS_VANISH

        for target in self.target_list:
            if target in self.has_hits:
                continue

            for bomb in self.magic_sprites:
                if target.status.get(cfg.SpriteStatus.IN_AIR) is None and target.area.colliderect(bomb.area):
                    damage = bomb.damage * self.sprite.magic_skill_damage_ratio
                    target.attacker.handle_under_attack(self.sprite, damage, cfg.Attack.METHOD_MAGIC)
                    target.attacker.handle_additional_status(cfg.SpriteStatus.BODY_SHAKE, 
                        {"dx": randint(-5, 5), "dy": randint(-3, 3), "time": self.params["body_shake_time"]})
                    target.attacker.handle_additional_status(cfg.SpriteStatus.ACTION_RATE_SCALE,
                        {"ratio": self.params["action_rate_scale_ratio"], 
                        "time": self.params["action_rate_scale_time"]})

                    effect_delta = 0.5
                    exist_time = 0.08
                    for i in xrange(int(self.params["action_rate_scale_time"] / effect_delta)):
                        x = randint(int(target.pos.x - target.setting.RADIUS * 1.5), 
                            int(target.pos.x + target.setting.RADIUS * 1.5))
                        y = target.pos.y
                        img = transform.rotate(
                            self.destroy_bomb_images[choice(self.bomb_over_effect_id_list)],
                            choice((90, 180, 270))
                        )
                        r = img.get_width() * 0.5
                        target.animation.particle_list.append(animation.Particle(
                            img, Vector2(x, y), r, r, r, Vector2(0, 0), Vector2(0, 0),
                            i * effect_delta,
                            randint(int(target.setting.HEIGHT * 0.3), int(target.setting.HEIGHT * 0.6)),
                            0, 0, i * (effect_delta - exist_time), target))

                    self.has_hits.add(target)
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
        self.origin_image = self.image.copy()
        self.origin_dy = self.dy
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
        self.image = self.blink.make(self.origin_image, passed_seconds)
        if self.fall_s < self.fall_range:
            # s = v0 * t + a * t^2 / 2
            s = self.fall_v * passed_seconds + 0.5 * self.acceleration * pow(passed_seconds, 2)
            self.fall_s += s
            # v = v0 + a * t
            self.fall_v += self.acceleration * passed_seconds

            self.dy = self.origin_dy - self.fall_s

        self.alive_time += passed_seconds
        if self.alive_time > self.life:
            self.status = cfg.Magic.STATUS_VANISH
        


class DestroyAeroliteSet(MagicSkill):
    # Renne skill
    destroy_aerolite_image = animation.effect_image_controller.get(
        sfg.Effect.DESTROY_AEROLITE_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DESTROY_AEROLITE_RECT)
    def __init__(self, sprite, target_list, static_objects, params, pos):
        super(DestroyAeroliteSet, self).__init__(sprite, target_list)
        self.static_objects = static_objects
        self.params = params
        self.passed_seconds = 0
        self.trigger_times = list(params["trigger_times"])

        # do some modification for trigger_pos
        delta_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[self.sprite.direction]).normalize()
        delta_vec.x *= self.params["fall_range"]
        delta_vec.y *= self.params["fall_range"]
        self.trigger_pos = self.sprite.pos + delta_vec


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            # trigger a aerolite
            self.trigger_times.pop(0)
            aerolite = DestroyAerolite(self.trigger_pos, self.params["aerolite_radius"], self.params["dx"],
                self.params["dy"], self.params["damage"], self.destroy_aerolite_image, 
                self.params["fall_range"], self.params["acceleration"], 
                self.params["aerolite_damage_cal_time"], self.params["aerolite_life"],
                self.params["aerolite_shake_on_x"], self.params["aerolite_shake_on_y"])

            self.magic_sprites.append(aerolite)

        for i, aerolite in enumerate(self.magic_sprites):
            aerolite.update(passed_seconds)
            if aerolite.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)
                continue

            for target in self.target_list:
                if target not in self.has_hits \
                    and target.status.get(cfg.SpriteStatus.IN_AIR) is None \
                    and aerolite.alive_time > aerolite.damage_cal_time \
                    and target.area.colliderect(aerolite.area):
                    # aerolite hit the target
                    self.has_hits.add(target)
                    damage = aerolite.damage * self.sprite.magic_skill_damage_ratio
                    target.attacker.handle_under_attack(self.sprite, damage, cfg.Attack.METHOD_MAGIC)
                    target.attacker.handle_additional_status(cfg.SpriteStatus.STUN, 
                        {"time": self.params["stun_time"]})
                    target.set_emotion(cfg.SpriteEmotion.STUN)

        if len(self.trigger_times) == 0 and len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH



class RenneDizzyLeaf(MagicSprite):
    leaf_image = animation.effect_image_controller.get(
        sfg.Effect.RENNE_DIZZY_LEAF_IMAGE_KEY).subsurface(sfg.Effect.RENNE_DIZZY_LEAF_RECT).convert_alpha()
    dx = leaf_image.get_width() * 0.5
    dy = leaf_image.get_width() * 0.5
    def __init__(self, pos, life, vec, z, vec_z):
        super(RenneDizzyLeaf, self).__init__(pos, self.dx, self.dx, self.dy, 0, 
            transform.rotate(self.leaf_image, choice((0, 90, 180, 270))))
        self.origin_dy = self.dy
        self.life = life
        self.vec = Vector2(vec)
        self.z = z
        self.vec_z = vec_z


    def update(self, passed_seconds):
        self.life -= passed_seconds
        if self.life < 0:
            self.status = cfg.Magic.STATUS_VANISH
        else:
            self.pos += self.vec * passed_seconds
            self.z += self.vec_z * passed_seconds
            self.dy = self.origin_dy + self.z
        


class RenneDizzy(MagicSkill):
    # Renne skill
    def __init__(self, sprite, target_list, params):
        super(RenneDizzy, self).__init__(sprite, target_list)
        self.dizzy_range = params["range"]
        self.dizzy_time = params["time"]
        self.effective_time = params["effective_time"]
        self.prob = params["prob"] 
        self.gen_leaf_cd = params["gen_leaf_cd"]
        self.gen_leaf_cd_add = 0
        self.leaf_life = params["leaf_life"]
        self.leaf_z = params["leaf_z"]
        self.leaf_vec_z = params["leaf_vec_z"]
        self.dizzy_targets = set()
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
            if len(self.magic_sprites) == 0:
                self.status = cfg.Magic.STATUS_VANISH
        else:
            if self.gen_leaf_cd_add == 0:
                self.gen_leaf_cd_add = self.gen_leaf_cd
                p = sp.pos.copy()
                p.x += randint(-self.dizzy_range, self.dizzy_range)
                p.y += randint(-self.dizzy_range, self.dizzy_range)
                leaf = RenneDizzyLeaf(p, self.leaf_life, Vector2(0, 0), self.leaf_z, self.leaf_vec_z)
                self.magic_sprites.append(leaf)
            else:
                self.gen_leaf_cd_add = max(self.gen_leaf_cd_add - passed_seconds, 0)

        for i, msp in enumerate(self.magic_sprites):
            msp.update(passed_seconds)
            if msp.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)



class DeathCoilSet(MagicSkill):
    # Leon Hardt skill
    death_coil_image = animation.effect_image_controller.get(
        sfg.Effect.DEATH_COIL_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DEATH_COIL_RECT)
    image_list = [death_coil_image.subsurface((i * 64, 0, 64, 64)) for i in xrange(2)]
    shadow = {"image": animation.get_shadow_image(sfg.Effect.DEATH_COIL_SHADOW_INDEX),
        "dy": sfg.Effect.DEATH_COIL_SHADOW_RECT_DELTA_Y}
    def __init__(self, sprite, target_list, static_objects, params, pos, target_pos):
        super(DeathCoilSet,  self).__init__(sprite, target_list)
        self.static_objects = static_objects
        ball = EnergyBall(pos, params["radius"], params["dx"], params["dy"], 
            params["damage"], choice(self.image_list), self.shadow, target_pos, 
            params["range"], params["speed"])
        ball.can_split = True
        self.magic_sprites.append(ball)
        self.params = params


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
                    sp.attacker.handle_under_attack(self.sprite, damage, cfg.Attack.METHOD_MAGIC)
                    self.has_hits.add(sp)

            if not self.reachable(msp.pos):
                msp.status = cfg.Magic.STATUS_VANISH

            # check whether can split
            if msp.status == cfg.Magic.STATUS_VANISH and msp.can_split:
                msp.can_split = False
                p = self.params
                for sn in xrange(p["split_num"]):
                    target_pos = choice(self.target_list).pos.copy()
                    target_pos.x = randint(int(target_pos.x - p["split_dx"]), int(target_pos.x + p["split_dx"]))
                    target_pos.y = randint(int(target_pos.y - p["split_dy"]), int(target_pos.y + p["split_dy"]))
                    ball = EnergyBall(msp.pos, p["radius"], p["dx"], p["dy"],
                        p["damage"], choice(self.image_list), self.shadow, target_pos, p["range"], p["speed"]
                    )
                    ball.can_split = False
                    self.magic_sprites.append(ball)

        if vanish_num == len(self.magic_sprites):
            self.status = cfg.Magic.STATUS_VANISH



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
        self.origin_image = self.image.copy()
        self.blink = Blink()


    def update(self, passed_seconds):
        self.image = self.blink.make(self.origin_image, passed_seconds)
        self.alive_time += passed_seconds
        if self.alive_time > self.life:
            self.status = cfg.Magic.STATUS_VANISH



class HellClawSet(MagicSkill):
    # Leon Hardt skill
    hell_claw_image = animation.effect_image_controller.get(
        sfg.Effect.HELL_CLAW_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.HELL_CLAW_RECT)
    claw_image_list = [hell_claw_image.subsurface((i * 64, 0, 64, 72)) for i in xrange(2)]
    def __init__(self, sprite, target_list, static_objects, params):
        super(HellClawSet, self).__init__(sprite, target_list)
        self.target_pos = self.cal_target_pos(target_list)
        self.static_objects = static_objects
        self.range = params["range"]
        self.params = params
        self.trigger_times = list(params["trigger_times"])
        self.passed_seconds = 0
        self.img_id = 0

        # hell claw has a ellipse for telling the player that this skill is coming!
        self.tips_area = pygame.Surface((
            self.params["claw_shake_on_x"] * 2 + 20, 
            self.params["claw_shake_on_x"] + 10)).convert_alpha()
        self.tips_area.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.ellipse(self.tips_area, pygame.Color(255, 0, 0, 128), self.tips_area.get_rect())
        self.blink = Blink()
        self.tips_area_mix = self.tips_area.copy()


    def cal_target_pos(self, target_list):
        s_x = 0.0
        s_y = 0.0
        n = len(target_list)
        for target in target_list:
            s_x += target.pos.x
            s_y += target.pos.y

        return Vector2(s_x / n, s_y / n)


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            # trigger a hell claw
            self.trigger_times.pop(0)
            claw = HellClaw(self.target_pos, self.params["claw_radius"], self.params["dx"], self.params["dy"],
                self.params["damage"], self.claw_image_list[self.img_id], self.params["claw_life"],
                self.params["claw_damage_cal_time"],
                self.params["claw_shake_on_x"], self.params["claw_shake_on_y"])

            if self.reachable(claw.pos):
                self.magic_sprites.append(claw)
                self.img_id = 1 - self.img_id

        for i, claw in enumerate(self.magic_sprites):
            for target in self.target_list:
                if target not in self.has_hits \
                    and claw.alive_time > claw.damage_cal_time \
                    and claw.area.colliderect(target.area):
                    self.has_hits.add(target)
                    target.attacker.handle_under_attack(self.sprite, claw.damage, cfg.Attack.METHOD_MAGIC)

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



class DeathDomainSign(MagicSprite):
    radius = sfg.Effect.DEATH_DOMAIN_SIGN_DX
    dx = sfg.Effect.DEATH_DOMAIN_SIGN_DX
    dy = sfg.Effect.DEATH_DOMAIN_SIGN_DY
    origin_image = animation.effect_image_controller.get(
        sfg.Effect.DEATH_DOMAIN_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DEATH_DOMAIN_SIGN_RECT)

    def __init__(self, pos):
        super(DeathDomainSign, self).__init__(pos, self.radius, self.dx, self.dy, 0, self.origin_image.copy())
        self.blink = Blink()


    def update(self, passed_seconds):
        self.image = self.blink.make(self.origin_image, passed_seconds)



class DeathDomainSword(MagicSprite):
    radius = sfg.Effect.DEATH_DOMAIN_SWORD_DX
    dx = sfg.Effect.DEATH_DOMAIN_SWORD_DX
    dy = sfg.Effect.DEATH_DOMAIN_SWORD_DY
    image = animation.effect_image_controller.get(
        sfg.Effect.DEATH_DOMAIN_IMAGE_KEY).convert_alpha().subsurface(
        sfg.Effect.DEATH_DOMAIN_SWORD_RECT)

    def __init__(self, pos, up_speed, life_time):
        super(DeathDomainSword, self).__init__(pos, self.radius, self.dx, self.dy, 0, self.image)
        self.up_speed = up_speed
        self.life_time = life_time


    def update(self, passed_seconds):
        # move up when time passed
        self.dy += self.up_speed * passed_seconds
        self.life_time -= passed_seconds
        if self.life_time <= 0:
            self.status = cfg.Magic.STATUS_VANISH



class DeathDomain(MagicSkill):
    # Leon's big magic skill, big!
    def __init__(self, sprite, target_list, static_objects, params):
        super(DeathDomain, self).__init__(sprite, target_list)
        self.init_pos = sprite.pos.copy()
        self.static_objects = static_objects
        self.radius = params["radius"]
        self.run_time = params["run_time"]
        self.params = params
        self.death_domain_sign = DeathDomainSign(self.sprite.pos)
        self.magic_sprites.append(self.death_domain_sign)
        self.hit_cds = {}
        self.pre_run_time = params["pre_run_time"]
        self.pre_run_time_add = 0

        # death domain tips
        self.tips_area = pygame.Surface((
            self.radius * 2 + 20,
            self.radius + 10)).convert_alpha()
        self.tips_area.fill(pygame.Color(0, 0, 0, 0))
        pygame.draw.ellipse(self.tips_area, pygame.Color(255, 0, 0, 128), self.tips_area.get_rect())
        self.blink = Blink()
        self.tips_area_mix = self.tips_area.copy()


    def update(self, passed_seconds):
        sp = self.sprite
        if sp.pos.x != self.init_pos.x or sp.pos.y != self.init_pos.y:
            # sprite was moved, stop the skill
            self.status = cfg.Magic.STATUS_VANISH
            return

        self.tips_area_mix = self.blink.make(self.tips_area, passed_seconds)
        if self.pre_run_time_add < self.pre_run_time:
            self.pre_run_time_add += passed_seconds
            # DeathDomainSign update
            self.death_domain_sign.update(passed_seconds)
            return

        dx = randint(-self.radius, self.radius)
        y_range = int(sqrt(pow(self.radius, 2) - pow(dx, 2)))
        dy = randint(-y_range, y_range)

        p = self.init_pos.copy()
        p.x += dx
        p.y += dy

        sword = DeathDomainSword(p, self.params["sword_up_speed"], self.params["sword_up_life_time"])
        self.magic_sprites.append(sword)

        for i, msp in enumerate(self.magic_sprites):
            msp.update(passed_seconds)
            if msp.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)

        for target in self.target_list:
            # pull target to the center
            pull_vec = Vector2.from_points(target.pos, self.init_pos)
            pull_vec.normalize()
            if target.status.get(cfg.SpriteStatus.UNDER_PULL) is None:
                target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_PULL,
                    {"key_vec": pull_vec, "speed": self.params["pull_speed"]})
            else:
                target.status[cfg.SpriteStatus.UNDER_PULL]["key_vec"] = pull_vec

            if self.init_pos.get_distance_to(target.pos) < self.radius \
                and self.hit_cds.get(id(target), 0) == 0:
                target.attacker.handle_under_attack(sp, self.params["damage"], cfg.Attack.METHOD_MAGIC)
                target.attacker.handle_additional_status(cfg.SpriteStatus.CRICK,
                    {"time": self.params["crick_time"], "old_action": target.action})
                self.hit_cds[id(target)] = self.params["hit_cd"]

        for k in self.hit_cds:
            self.hit_cds[k] = max(0, self.hit_cds[k] - passed_seconds)

        self.run_time -= passed_seconds
        if self.run_time <= 0:
            self.status = cfg.Magic.STATUS_VANISH


    def draw(self, camera):
        r = self.tips_area_mix.get_rect()
        r.center = self.init_pos("xy")
        r.centery *= 0.5
        camera.screen.blit(self.tips_area_mix, (r.x - camera.rect.x, r.y - camera.rect.y))



class IceColumnBomb(MagicSkill):
    ice_block1_image = animation.effect_image_controller.get(
        sfg.Effect.ICE_IMAGE_KEY).subsurface(sfg.Effect.ICE_BLOCK1_RECT).convert_alpha()
    ice_fog_images = []
    for r in (sfg.Effect.ICE_FOG1_RECT, sfg.Effect.ICE_FOG2_RECT):
        ice_fog_images.append(animation.effect_image_controller.get(
            sfg.Effect.ICE_IMAGE_KEY).subsurface(r).convert_alpha())

    def __init__(self, sprite, target_list, params):
        super(IceColumnBomb, self).__init__(sprite, target_list)
        self.init_pos = sprite.pos.copy()
        self.center_rect = sprite.area.copy()
        self.trigger_times = list(params["trigger_times"])
        self.trigger_ranges = list(params["trigger_ranges"])
        self.ice_column_damage = params["ice_column_damage"]
        self.ice_column_life = params["ice_column_life"]
        self.frozen_time = params["frozen_time"]
        self.action_rate_scale_ratio = params["action_rate_scale_ratio"]
        self.ice_block_gen_num = params["ice_block_gen_num"]
        self.ice_block_pos_shake_x = params["ice_block_pos_shake_x"]
        self.ice_fog_per_column_gen_num = params["ice_fog_per_column_gen_num"]
        self.ice_fog_pos_shake_x = params["ice_fog_pos_shake_x"]
        self.ice_fog_vec_z = params["ice_fog_vec_z"]
        self.ice_fog_life = params["ice_fog_life"]
        self.passed_seconds = 0


    def update(self, passed_seconds):
        self.passed_seconds += passed_seconds
        if len(self.trigger_times) > 0 and self.passed_seconds > self.trigger_times[0]:
            self.trigger_times.pop(0)
            rng = self.trigger_ranges.pop(0)
            for vec in cfg.Direction.VEC_ALL:
                delta_vec = Vector2(vec).normalize()
                delta_vec.x *= rng
                delta_vec.y *= rng
                pos = self.init_pos + delta_vec
                ice_column = IceColumn(pos, self.ice_column_damage, self.ice_column_life)
                self.magic_sprites.append(ice_column)
                for _i in xrange(self.ice_fog_per_column_gen_num):
                    x = randint(int(pos.x - self.ice_fog_pos_shake_x),
                            int(pos.x + self.ice_fog_pos_shake_x))
                    y = pos.y
                    img = transform.rotate(choice(self.ice_fog_images), choice((90, 180, 270)))
                    self.sprite.animation.particle_list.append(animation.Particle(
                        img, Vector2(x, y), sfg.Effect.ICE_FOG_RADIUS,
                        sfg.Effect.ICE_FOG_DX, sfg.Effect.ICE_FOG_DY, Vector2(0, 0), Vector2(0, 0),
                        self.ice_fog_life, 
                        randint(0, sfg.Effect.ICE_FOG_RADIUS),
                        self.ice_fog_vec_z, 0, pre_hide_time=random()))

        for _i, ice_column in enumerate(self.magic_sprites):
            for target in self.target_list:
                if target not in self.has_hits and \
                    target.status.get(cfg.SpriteStatus.IN_AIR) is None and \
                    (ice_column.area.colliderect(target.area) or self.center_rect.colliderect(target.area)):
                    self.has_hits.add(target)
                    target.attacker.handle_under_attack(self.sprite, self.ice_column_damage, 
                        cfg.Attack.METHOD_MAGIC)
                    target.attacker.handle_additional_status(cfg.SpriteStatus.ACTION_RATE_SCALE,
                        {"ratio": self.action_rate_scale_ratio, "time": self.frozen_time})
                    for _j in xrange(self.ice_block_gen_num):
                        x = randint(int(target.pos.x - self.ice_block_pos_shake_x), 
                                int(target.pos.x + self.ice_block_pos_shake_x))
                        y = target.pos.y
                        img = transform.rotate(self.ice_block1_image, choice((90, 180, 270)))
                        target.animation.particle_list.append(animation.Particle(
                            img, Vector2(x, y), sfg.Effect.ICE_BLOCK1_RADIUS,
                            sfg.Effect.ICE_BLOCK1_DX, sfg.Effect.ICE_BLOCK1_DY, Vector2(0, 0), Vector2(0, 0),
                            self.frozen_time,
                            randint(0, target.setting.HEIGHT),
                            follow_sprite=target))

        for i, ice_column in enumerate(self.magic_sprites):
            ice_column.update(passed_seconds)
            if ice_column.status == cfg.Magic.STATUS_VANISH:
                self.magic_sprites.pop(i)

        if len(self.trigger_times) == 0 and len(self.magic_sprites) == 0:
            self.status = cfg.Magic.STATUS_VANISH



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


    def handle_under_attack(self, from_who, cost_hp, attack_method=cfg.Attack.METHOD_REGULAR):
        sp = self.sprite
        cost_hp = int(cost_hp)
        sp.hp = max(sp.hp - cost_hp, 0)
        sp.hp_status = sp.cal_sprite_status(sp.hp, sp.setting.HP)
        sp.status[cfg.SpriteStatus.UNDER_ATTACK] = {"time": sfg.Sprite.UNDER_ATTACK_EFFECT_TIME}
        sp.animation.show_cost_hp(cost_hp)


    def handle_additional_status(self, status_id, status_object):
        # do some rejection check for some status
        sp = self.sprite
        if status_id == cfg.SpriteStatus.UNDER_THUMP:
            for reject_status in cfg.SpriteStatus.REJECT_THUMP_STATUS_LIST:
                if sp.status.get(reject_status) is not None:
                    return False

            sp.direction = cal_face_direct(sp.pos + status_object["key_vec"], sp.pos)

        elif status_id == cfg.SpriteStatus.CRICK:
            for reject_status in cfg.SpriteStatus.REJECT_CRICK_STATUS_LIST:
                if sp.status.get(reject_status) is not None:
                    return False

        elif status_id == cfg.SpriteStatus.DIZZY:
            for reject_status in cfg.SpriteStatus.REJECT_DIZZY_STATUS_LIST:
                if sp.status.get(reject_status) is not None:
                    return False

        elif status_id == cfg.SpriteStatus.STUN:
            for reject_status in cfg.SpriteStatus.REJECT_STUN_STATUS_LIST:
                if sp.status.get(reject_status) is not None:
                    return False

        sp.status[status_id] = status_object
        return True


    def is_static_object_block(self, target):
        sp = self.sprite
        x_min = min(sp.area.left, target.area.left)
        y_min = min(sp.area.top, target.area.top)
        x_max = max(sp.area.right, target.area.right)
        y_max = max(sp.area.bottom, target.area.bottom)
        w = x_max - x_min
        h = y_max - y_min
        r = pygame.Rect((x_min, y_min, w, h))
        for obj in sp.static_objects:
            if obj.setting.IS_BLOCK and obj.area.colliderect(r):
                return True

        return False


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


    def in_angle_scope(self, target, attack_range, cos_min):
        sp = self.sprite
        direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
        vec_to_target = Vector2.from_points(sp.pos, target.pos)
        cos_val = cos_for_vec(direct_vec, vec_to_target)
        if attack_range + target.setting.RADIUS > vec_to_target.get_length() \
            and cos_val >= cos_min:
            return True

        return False


    def in_hit_condition(self, target, current_frame_add, key_frames=None):
        sp = self.sprite
        real_key_frames = key_frames or self.key_frames
        if int(current_frame_add) not in real_key_frames:
            return False

        if target in self.has_hits:
            return False

        if target.hp_status not in cfg.HpStatus.ALIVE:
            return False

        if target.status.get(cfg.SpriteStatus.IN_AIR) is not None \
            and sp.setting.HEIGHT * 0.5 < target.status[cfg.SpriteStatus.IN_AIR]["height"]:
            # check whether target is in air status, then compare in-air height with its own height
            return False
        return True


    def hit(self, target, current_frame_add):
        if not self.in_hit_condition(target, current_frame_add):
            return False

        # check whether target in angle scope
        if self.in_angle_scope(target, self.attack_range, self.cos_min):
            # add target to has_hits by the way
            self.has_hits.add(target)
            return True

        return False


    def hit_with_many_params(self, target, current_frame_add, key_frames, attack_range, cos_min):
        if not self.in_hit_condition(target, current_frame_add, key_frames):
            return False

        if self.in_angle_scope(target, attack_range, cos_min):
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



class Arrow(MagicSprite):
    """
    just like a magic sprite
    """
    arrow_images = animation.battle_images.get(sfg.Ammo.ARROW_IMAGE_KEY)
    arrow_image_list = [arrow_images.subsurface(
        pygame.Rect((0, i * sfg.Ammo.ARROW_HEIGHT), (sfg.Ammo.ARROW_WIDTH, sfg.Ammo.ARROW_HEIGHT))) \
        for i in xrange(cfg.Direction.TOTAL)]

    def __init__(self, pos, radius, dx, dy, damage, direction, speed, fly_range):
        super(Arrow, self).__init__(pos, radius, dx, dy, damage, self.arrow_image_list[direction])
        self.origin_pos = self.pos.copy()
        self.key_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[direction])
        self.speed = speed
        self.fly_range = fly_range


    def update(self, passed_seconds):
        self.pos += self.key_vec * self.speed * passed_seconds
        self.area.center = self.pos("xy")
        if self.pos.get_distance_to(self.origin_pos) > self.fly_range:
            self.status = cfg.Magic.STATUS_VANISH



class ArrowSet(MagicSkill):

    def __init__(self, sprite, target_list, params):
        super(ArrowSet, self).__init__(sprite, target_list)
        # only one arrow right now
        self.magic_sprites.append(Arrow(sprite.pos, params["arrow_radius"], params["arrow_dx"],
            params["arrow_dy"], params["arrow_damage"], sprite.direction, params["arrow_speed"], 
            params["range"]))


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
                    sp.attacker.handle_under_attack(self.sprite, msp.damage, cfg.Attack.METHOD_MAGIC)
                    self.has_hits.add(sp)

            if not self.reachable(msp.pos):
                msp.status = cfg.Magic.STATUS_VANISH

        if vanish_num == len(self.magic_sprites):
            self.status = cfg.Magic.STATUS_VANISH



class RenneAttacker(AngleAttacker):
    def __init__(self, sprite, attacker_params):
        super(RenneAttacker, self).__init__(sprite, attacker_params["attack1"]["range"], 
            attacker_params["attack1"]["angle"], attacker_params["key_frames"])
        self.hit_record = []
        self.kill_record = []
        self.attack1_params = attacker_params["attack1"]
        self.attack2_params = attacker_params["attack2"]

        # calculate cos_min first
        self.attack1_params["cos_min"] = cos(radians(self.attack1_params["angle"] * 0.5))
        self.attack2_params["cos_min"] = cos(radians(self.attack2_params["angle"] * 0.5))

        self.run_attack_params = attacker_params["run_attack"]
        self.magic_skill_1_params = attacker_params["destroy_fire"]
        self.magic_skill_2_params = attacker_params["destroy_bomb"]
        self.magic_skill_3_params = attacker_params["destroy_aerolite"]
        self.magic_skill_4_params = attacker_params["dizzy"]
        self.magic_cds = {"magic_skill_1": 0, "magic_skill_2": 0, "magic_skill_3": 0, "magic_skill_4": 0}
        # magic_list has kinds of magics, eg. DestroyBombSet and DestroyAeroliteSet, 
        # every magic has one or more magic sprite(s), eg. DestroyBombSet has many "bombs"
        self.magic_list = []
        self.reset_vars()
        self.cal_real_attack_damage()


    def cal_real_attack_damage(self):
        sp = self.sprite
        atk = sp.setting.ATK
        self.attack1_params["damage"] = int(atk * self.attack1_params["atk_ratio"])
        self.attack2_params["damage"] = int(atk * self.attack2_params["atk_ratio"])
        self.run_attack_params["damage"] = int(atk * self.run_attack_params["atk_ratio"])


    def reset_vars(self):
        # a lock, only one magic is running in an attack
        self.method = None
        self.current_magic = None


    def refresh_skill(self, skill_key=None):
        if skill_key is not None:
            self.magic_cds[skill_key] = 0
        else:
            for key in self.magic_cds:
                self.magic_cds[key] = 0


    def attack1(self, target, current_frame_add):
        if self.hit_with_many_params(target, current_frame_add, self.attack1_params["key_frames"],
                self.attack1_params["range"], self.attack1_params["cos_min"]):
            damage = max(0, self.attack1_params["damage"] - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)
            target.attacker.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack1_params["crick_time"], "old_action": target.action})
            self.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack1_params["self_crick_time"], "old_action": self.sprite.action})
            return True
        return False


    def attack2(self, target, current_frame_add):
        if self.hit_with_many_params(target, current_frame_add, self.attack2_params["key_frames"], 
                self.attack2_params["range"], self.attack2_params["cos_min"]):
            damage = int(max(0, self.attack2_params["damage"] - target.dfs))
            target.attacker.handle_under_attack(self.sprite, damage)
            target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                {"crick_time": self.attack2_params["thump_crick_time"], 
                "out_speed": self.attack2_params["thump_out_speed"], 
                "acceleration": self.attack2_params["thump_acceleration"],
                "key_vec": Vector2.from_points(self.sprite.pos, target.pos)})
            self.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack2_params["self_crick_time"], "old_action": self.sprite.action})
            return True
        return False


    def run_attack(self, target, current_frame_add):
        if self.hit(target, current_frame_add):
            damage = max(0, self.run_attack_params["damage"] - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)
            target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                {"crick_time": self.run_attack_params["crick_time"],
                "out_speed": self.run_attack_params["out_speed"], 
                "acceleration": self.run_attack_params["acceleration"],
                "from_who": self.sprite,
                "key_vec": Vector2.from_points(self.sprite.pos, target.pos)})
            self.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.run_attack_params["self_crick_time"], "old_action": self.sprite.action})
            return True
        return False


    def destroy_fire(self, current_frame_add):
        sp = self.sprite
        direct_vec = cfg.Direction.DIRECT_TO_VEC[sp.direction]
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.magic_skill_1_params["mana"]
            self.magic_cds["magic_skill_1"] = self.magic_skill_1_params["cd"]
            self.current_magic = DestroyFire(sp, sp.enemies,
                sp.static_objects, self.magic_skill_1_params, sp.pos, sp.pos + direct_vec)
            self.magic_list.append(self.current_magic)


    def destroy_bomb(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:
            sp.mp -= self.magic_skill_2_params["mana"]
            self.magic_cds["magic_skill_2"] = self.magic_skill_2_params["cd"]
            self.current_magic = DestroyBombSet(sp, sp.enemies,
                sp.static_objects, self.magic_skill_2_params, sp.pos, sp.direction)
            self.magic_list.append(self.current_magic)


    def destroy_aerolite(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.magic_skill_3_params["key_frames"]:
            sp.mp -= self.magic_skill_3_params["mana"]
            self.magic_cds["magic_skill_3"] = self.magic_skill_3_params["cd"]
            self.current_magic = DestroyAeroliteSet(sp, sp.enemies, 
                sp.static_objects, self.magic_skill_3_params, sp.pos)
            self.magic_list.append(self.current_magic)


    def dizzy(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.magic_skill_4_params["key_frames"]:
            sp.mp -= self.magic_skill_4_params["mana"]
            self.magic_cds["magic_skill_4"] = self.magic_skill_4_params["cd"]
            self.current_magic = RenneDizzy(sp, sp.enemies, self.magic_skill_4_params)
            self.magic_list.append(self.current_magic)


    def finish(self):
        if len(self.has_hits) > 0:
            self.hit_record.append({"time": time(), "n_hit": len(self.has_hits)})
            for sp in self.has_hits:
                if sp.hp_status == cfg.HpStatus.DIE:
                    self.kill_record.append({"time": time()})
            self.has_hits.clear()

        self.reset_vars()



class JoshuaAttacker(AngleAttacker):
    def __init__(self, sprite, attacker_params):
        super(JoshuaAttacker, self).__init__(sprite, attacker_params["attack1"]["range"],
            attacker_params["attack1"]["angle"], attacker_params["attack1"]["key_frames"])
        self.hit_record = []
        self.kill_record = []
        self.attack1_params = attacker_params["attack1"]
        self.attack2_params = attacker_params["attack2"]
        self.attack3_params = attacker_params["attack3"]
        self.run_attack_params = attacker_params["run_attack"]

        # calculate cos_min first
        self.attack1_params["cos_min"] = cos(radians(self.attack1_params["angle"] * 0.5))
        self.attack2_params["cos_min"] = cos(radians(self.attack2_params["angle"] * 0.5))
        self.attack3_params["cos_min"] = cos(radians(self.attack3_params["angle"] * 0.5))
        self.run_attack_params["cos_min"] = cos(radians(self.run_attack_params["angle"] * 0.5))

        self.magic_skill_1_params = attacker_params["x1"]
        self.magic_skill_2_params = attacker_params["x2"]
        self.magic_skill_3_params = attacker_params["x3"]
        self.magic_skill_4_params = attacker_params["x4"]
        self.magic_cds = {"magic_skill_1": 0, "magic_skill_2": 0, "magic_skill_3": 0, "magic_skill_4": 0}
        self.magic_list = []
        self.reset_vars()
        self.cal_real_attack_damage()

        self.attack3_delay_hits = set()


    def cal_real_attack_damage(self):
        sp = self.sprite
        atk = sp.setting.ATK
        self.attack1_params["damage"] = int(atk * self.attack1_params["atk_ratio"])
        self.attack2_params["damage"] = int(atk * self.attack2_params["atk_ratio"])
        self.attack3_params["damage"] = int(atk * self.attack3_params["atk_ratio"])
        self.run_attack_params["damage"] = int(atk * self.run_attack_params["atk_ratio"])


    def refresh_skill(self, skill_key=None):
        if skill_key is not None:
            self.magic_cds[skill_key] = 0
        else:
            for key in self.magic_cds:
                self.magic_cds[key] = 0


    def reset_vars(self):
        # a lock, only one magic is running in an attack
        self.method = None
        self.current_magic = None


    def attack1(self, target, current_frame_add):
        if self.hit_with_many_params(target, current_frame_add, self.attack1_params["key_frames"],
                self.attack1_params["range"], self.attack1_params["cos_min"]):
            damage = max(0, self.attack1_params["damage"] - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)
            target.attacker.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack1_params["crick_time"], "old_action": target.action})
            self.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack1_params["self_crick_time"], "old_action": self.sprite.action})
            return True
        return False


    def attack2(self, target, current_frame_add):
        if self.hit_with_many_params(target, current_frame_add, self.attack2_params["key_frames"],
                self.attack2_params["range"], self.attack2_params["cos_min"]):
            damage = max(0, self.attack2_params["damage"] - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)
            target.attacker.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack2_params["crick_time"], "old_action": target.action})
            self.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack2_params["self_crick_time"], "old_action": self.sprite.action})
            return True
        return False


    def attack3(self, target, current_frame_add):
        if self.hit_with_many_params(target, current_frame_add, self.attack3_params["key_frames"], 
                self.attack3_params["range"], self.attack3_params["cos_min"]):
            target.attacker.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.attack3_params["crick_time"], "old_action": target.action})

        if int(current_frame_add) == self.attack3_params["end_frame"]:
            if target in self.has_hits and target not in self.attack3_delay_hits:
                self.attack3_delay_hits.add(target)
                damage = max(0, self.attack3_params["damage"] - target.dfs)
                target.attacker.handle_under_attack(self.sprite, damage)
                # remove crick status and add under_thump status
                cfg.SpriteStatus.CRICK in target.status and target.status.pop(cfg.SpriteStatus.CRICK)
                target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                    {"crick_time": self.attack3_params["thump_crick_time"], 
                    "out_speed": self.attack3_params["thump_out_speed"], 
                    "acceleration": self.attack3_params["thump_acceleration"],
                    "key_vec": Vector2.from_points(self.sprite.pos, target.pos)})
                blood_set = BloodSet(self.sprite, target.pos, target.setting.HEIGHT, 4)
                self.magic_list.append(blood_set)
                return True
        return False 


    def run_attack(self, target, current_frame_add):
        if self.hit_with_many_params(target, current_frame_add, self.run_attack_params["key_frames"], 
                self.run_attack_params["range"], self.run_attack_params["cos_min"]):

            damage = max(0, self.run_attack_params["damage"] - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)

            target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                {"crick_time": self.run_attack_params["crick_time"],
                "out_speed": self.run_attack_params["out_speed"], 
                "acceleration": self.run_attack_params["acceleration"],
                "from_who": self.sprite,
                "key_vec": Vector2.from_points(self.sprite.pos, target.pos)})

            blood_set = BloodSet(self.sprite, target.pos, target.setting.HEIGHT, 4)
            self.magic_list.append(blood_set)

            self.handle_additional_status(cfg.SpriteStatus.CRICK,
                {"time": self.run_attack_params["self_crick_time"], "old_action": self.sprite.action})

            return True
        return False


    def x1(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None:
            sp.mp -= self.magic_skill_1_params["mana"]
            self.current_magic = "x1"

        hit_count = 0
        for target in sp.enemies:
            if self.hit_with_many_params(target, current_frame_add, 
                self.magic_skill_1_params["key_frames"], self.attack3_params["range"],
                self.attack3_params["cos_min"]):
                
                damage = self.magic_skill_1_params["damage"]
                target.attacker.handle_under_attack(sp, damage)
                target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                    {"crick_time": self.magic_skill_1_params["thump_crick_time"],
                    "out_speed": self.magic_skill_1_params["thump_out_speed"],
                    "acceleration": self.magic_skill_1_params["thump_acceleration"],
                    "key_vec": Vector2.from_points(sp.pos, target.pos)})

                is_stun = target.attacker.handle_additional_status(cfg.SpriteStatus.STUN,
                    {"time": self.magic_skill_1_params["stun_time"]})
                if is_stun:
                    target.set_emotion(cfg.SpriteEmotion.STUN)

                hit_count += 1




    def x2(self, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.magic_skill_2_params["key_frames"]:
            sp.mp -= self.magic_skill_2_params["mana"]
            self.magic_cds["magic_skill_2"] = self.magic_skill_2_params["cd"]
            self.current_magic = IceColumnBomb(sp, sp.enemies, self.magic_skill_2_params)
            self.magic_list.append(self.current_magic)
            # change mana into sp the same time
            sp.sp = min(sp.sp + self.magic_skill_2_params["mana"] * 2, sp.setting.SP)


    def x3(self, current_frame_add):
        pass


    def x4(self, current_frame_add):
        pass


    def finish(self):
        self.has_hits.clear()
        self.attack3_delay_hits.clear()
        self.reset_vars()



class EnemyAngleAttacker(AngleAttacker):
    def handle_under_attack(self, from_who, cost_hp, attack_method=cfg.Attack.METHOD_REGULAR):
        sp = self.sprite
        if sp.hp_status not in cfg.HpStatus.ALIVE:
            return

        super(EnemyAngleAttacker, self).handle_under_attack(from_who, cost_hp, attack_method=attack_method)
        sp.cal_angry(cost_hp)
        sp.set_target(from_who)
        # add exp to hero if this enemy is die
        if sp.hp_status == cfg.HpStatus.DIE:
            from_who.add_exp(sp.setting.EXP)



class EnemyShortAttacker(EnemyAngleAttacker):
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


    def run(self, target, current_frame_add):
        if self.hit(target, current_frame_add):
            damage = max(0, self.sprite.atk - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False
        

    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()



class EnemyPoisonShortAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(EnemyPoisonShortAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        self.poison_dps = attacker_params["poison_damage_per_second"]
        self.poison_time = attacker_params["poison_persist_time"]
        self.poison_prob = attacker_params["poison_prob"]
        self.spit_poison_params = attacker_params["spit_poison"]
        self.spit_poison_max_time = self.spit_poison_params["max_time"]
        self.magic_list = []
        self.reset_vars()


    def reset_vars(self):
        self.method = None
        self.current_magic = None
        self.poison_happen = False


    def spit_poison_chance(self, target):
        sp = self.sprite
        if len(self.magic_list) >= self.spit_poison_max_time:
            return False

        distance_to_target = sp.pos.get_distance_to(target.pos)
        if distance_to_target <= self.attack_range * 5:
            if self.is_static_object_block(target):
                return False
            return True

        return False


    def chance(self, target):
        sp = self.sprite
        if happen(sp.brain.ai.ATTACK_SPIT_POISON) and self.spit_poison_chance(target):
            self.method = "spit_poison"
            return True

        if super(EnemyPoisonShortAttacker, self).chance(target):
            self.method = "regular"
            return True

        return False


    def spit_poison(self, target):
        sp = self.sprite
        if self.current_magic is None:
            self.current_magic = PoisonSet(sp, [target, ], sp.static_objects, self.spit_poison_params)
            self.magic_list.append(self.current_magic)


    def run(self, target, current_frame_add):
        hit_it = super(EnemyPoisonShortAttacker, self).run(target, current_frame_add)
        # add additional poison damage
        if hit_it and happen(self.poison_prob):
            target.attacker.handle_additional_status(cfg.SpriteStatus.POISON, 
                {"dps": self.poison_dps, "time_list": range(self.poison_time), 
                "time_left": self.poison_time})
            self.poison_happen = True
        return hit_it


    def finish(self):
        super(EnemyPoisonShortAttacker, self).finish()
        self.reset_vars()



class GhostAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(GhostAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        self.mp_burn_prob = attacker_params["mp_burn_prob"]
        self.mp_burn = attacker_params["mp_burn"]
        self.reset_vars()


    def reset_vars(self):
        self.method = None
        self.leak_happen = False


    def chance(self, target):
        sp = self.sprite
        if super(GhostAttacker, self).chance(target):
            self.method = "regular"
            return True

        if sp.status.get(cfg.SpriteStatus.INVISIBLE) is None \
            and happen(sp.brain.ai.ATTACK_ENTER_INVISIBLE_PROB):
            self.method = "invisible"
            return True

        return False


    def run(self, target, current_frame_add):
        hit_it = super(GhostAttacker, self).run(target, current_frame_add)
        if hit_it and happen(self.mp_burn_prob):
            self.leak_happen = True
            target.mp = max(0, target.mp - self.mp_burn)

        return hit_it


    def handle_under_attack(self, from_who, cost_hp, attack_method=cfg.Attack.METHOD_REGULAR):
        super(GhostAttacker, self).handle_under_attack(from_who, cost_hp, attack_method=cfg.Attack.METHOD_REGULAR)
        # when this enemy is under attack, it will lose invisible status
        if self.sprite.status.get(cfg.SpriteStatus.INVISIBLE) is not None:
            self.sprite.status.pop(cfg.SpriteStatus.INVISIBLE)


    def finish(self):
        super(GhostAttacker, self).finish()
        self.reset_vars()



class EnemyThumpShortAttacker(EnemyShortAttacker):
    # thump target, make it back a distance
    def __init__(self, sprite, attacker_params):
        super(EnemyThumpShortAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        self.thump_crick_time = attacker_params["thump_crick_time"]
        self.thump_out_speed = attacker_params["thump_out_speed"]
        self.thump_acceleration = attacker_params["thump_acceleration"]
        self.thump_slide_range = attacker_params["thump_slide_speed"] * attacker_params["thump_slide_time"]

        self.thump_cos_min = attacker_params["thump_cos_min"]
        self.magic_list = []
        self.reset_vars()


    def reset_vars(self):
        self.method = None


    def thump_chance(self, target):
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if distance_to_target <= self.attack_range + self.thump_slide_range:
            direct_vec = Vector2(cfg.Direction.DIRECT_TO_VEC[sp.direction])
            vec_to_target = Vector2.from_points(sp.area.center, target.area.center)
            cos_val = cos_for_vec(direct_vec, vec_to_target)
            if cos_val >= self.thump_cos_min \
                and (not self.is_static_object_block(target)):
                return True

        return False


    def chance(self, target):
        sp = self.sprite
        if happen(sp.brain.ai.ATTACK_THUMP_PROB) and self.thump_chance(target):
            self.method = "thump"
            self.key_vec = Vector2.from_points(sp.pos, target.pos)
            return True

        if super(EnemyThumpShortAttacker, self).chance(target):
            self.method = "regular"
            return True

        return False


    def run(self, target, current_frame_add):
        sp = self.sprite
        if self.hit(target, current_frame_add):
            atk = sp.atk
            if self.method == "thump":
                # thump results in a double attack and knockback
                atk *= 2

                blood_set = BloodSet(sp, target.pos, target.setting.HEIGHT)
                self.magic_list.append(blood_set)

                target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                    {"crick_time": self.thump_crick_time, 
                    "out_speed": self.thump_out_speed, 
                    "acceleration": self.thump_acceleration,
                    "key_vec": Vector2.from_points(sp.pos, target.pos)})

            damage = max(0, atk - target.dfs)
            target.attacker.handle_under_attack(sp, damage)
            return True

        return False


    def finish(self):
        super(EnemyThumpShortAttacker, self).finish()
        self.reset_vars()



class EnemyBloodShortAttacker(EnemyShortAttacker):
    # suck blood in attack
    def __init__(self, sprite, attacker_params):
        super(EnemyBloodShortAttacker, self).__init__(sprite, attacker_params)
        self.suck_blood_ratio = attacker_params["suck_blood_ratio"]


    def run(self, target, current_frame_add):
        hit_it = super(EnemyBloodShortAttacker, self).run(target, current_frame_add)
        if hit_it:
            sp = self.sprite
            sp.hp = min(sp.hp + self.suck_blood_ratio * sp.setting.ATK, sp.setting.HP)
            sp.hp_status = sp.cal_sprite_status(sp.hp, sp.setting.HP)
            words = sfg.Font.ARIAL_BLACK_24.render("Blood!", True, pygame.Color("darkred"))
            sp.animation.show_words(words, 0.3,
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))

        return hit_it



class TwoHeadSkeletonAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(TwoHeadSkeletonAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        self.fall_range = attacker_params["fall_range"]
        self.fall_damage = attacker_params["fall_damage"]
        self.fall_thump_crick_time = attacker_params["fall_thump_crick_time"]
        self.fall_thump_acceleration = attacker_params["fall_thump_acceleration"]
        self.fall_thump_out_speed = attacker_params["fall_thump_out_speed"]

        # some calculation for value not decided in setting
        self.params["fall_in_air_time"] = \
            (-attacker_params["fall_v0_y"] * 2.0) / attacker_params["fall_acceleration"]
        self.params["fall_back_in_air_time"] = \
            (-attacker_params["fall_back_v0_y"] * 2.0) / attacker_params["fall_acceleration"]

        self.magic_list = []
        self.reset_vars()


    def reset_vars(self):
        self.method = None


    def fall_chance(self, target):
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if self.fall_range[0] <= distance_to_target <= self.fall_range[1]:
            sp.fall_in_air_v_x = float(distance_to_target) / self.params["fall_in_air_time"]
            return True
        return False


    def fall_hit(self, target):
        if target in self.has_hits:
            return False

        sp = self.sprite
        if sp.area.colliderect(target.area):
            self.has_hits.add(target)
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


    def run(self, target, current_frame_add):
        if self.method == "regular":
            return super(TwoHeadSkeletonAttacker, self).run(target, current_frame_add)
        elif self.method == "fall":
            if self.fall_hit(target):
                sp = self.sprite
                target.attacker.handle_under_attack(sp, self.fall_damage)
                target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP, 
                    {"crick_time": self.fall_thump_crick_time, "out_speed": self.fall_thump_out_speed,
                    "acceleration": self.fall_thump_acceleration, 
                    "key_vec": Vector2.from_points(sp.pos, target.pos)})

                blood_set = BloodSet(sp, target.pos, target.setting.HEIGHT)
                self.magic_list.append(blood_set)

                return True

        return False


    def finish(self):
        super(TwoHeadSkeletonAttacker, self).finish()
        self.reset_vars()



class EnemyFrozenShortAttacker(EnemyShortAttacker):
    # frozen effect attacker
    def __init__(self, sprite, attacker_params):
        super(EnemyFrozenShortAttacker, self).__init__(sprite, attacker_params)
        self.frozen_prob = attacker_params["frozen_prob"]
        self.frozen_time = attacker_params["frozen_time"]
        self.action_rate_scale = attacker_params["action_rate_scale"]


    def run(self, target, current_frame_add):
        hit_it = super(EnemyFrozenShortAttacker, self).run(target, current_frame_add)
        if hit_it and happen(self.frozen_prob):
            target.attacker.handle_additional_status(cfg.SpriteStatus.FROZEN, 
                {"time": self.frozen_time, "action_rate_scale": self.action_rate_scale})
            words = sfg.Font.ARIAL_BLACK_24.render("Frozen!", True, pygame.Color("cyan"))
            sp = self.sprite
            sp.animation.show_words(words, 0.3, 
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))
        return hit_it



class EnemyWeakShortAttacker(EnemyShortAttacker):
    # give target weak status
    def __init__(self, sprite, attacker_params):
        super(EnemyWeakShortAttacker, self).__init__(sprite, attacker_params)
        self.weak_prob = attacker_params["weak_prob"]
        self.weak_time = attacker_params["weak_time"]
        self.weak_atk = attacker_params["weak_atk"]
        self.weak_dfs = attacker_params["weak_dfs"]
    

    def run(self, target, current_frame_add):
        hit_it = super(EnemyWeakShortAttacker, self).run(target, current_frame_add)
        if hit_it and happen(self.weak_prob):
            target.attacker.handle_additional_status(cfg.SpriteStatus.WEAK, 
                {"time_left": self.weak_time, "y": 0})
            target.atk = max(0, target.atk - self.weak_atk)
            target.dfs = max(0, target.dfs - self.weak_dfs)
            words = sfg.Font.ARIAL_BLACK_24.render("Weak!", True, pygame.Color("gray"))
            sp = self.sprite
            sp.animation.show_words(words, 0.3, 
                (sp.pos.x - words.get_width() * 0.5, sp.pos.y * 0.5 - sp.setting.HEIGHT - 50))
        return hit_it



class SwordRobberAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(SwordRobberAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        self.thump_crick_time = attacker_params["whirlwind"]["thump_crick_time"]
        self.thump_acceleration = attacker_params["whirlwind"]["thump_acceleration"]
        self.thump_out_speed = attacker_params["whirlwind"]["thump_out_speed"]


    def whirlwind_chance(self, target):
        if self.is_static_object_block(target):
            return False
        return True


    def chance(self, target):
        sp = self.sprite
        if happen(sp.brain.ai.ATTACK_WHIRLWIND_PROB) and self.whirlwind_chance(target):
            self.method = "whirlwind"
            return True

        if super(SwordRobberAttacker, self).chance(target):
            self.method = "regular"
            return True

        return False


    def whirlwind_hit(self, target):
        if target in self.has_hits:
            return False

        if self.sprite.area.colliderect(target.area):
            self.has_hits.add(target)
            return True

        return False

    def whirlwind_run(self, target):
        if self.whirlwind_hit(target):
            sp = self.sprite
            target.attacker.handle_under_attack(sp, sp.atk)
            target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
                {"crick_time": self.thump_crick_time, 
                "out_speed": self.thump_out_speed,
                "acceleration": self.thump_acceleration, 
                "key_vec": Vector2.from_points(sp.pos, target.pos)})


    def finish(self):
        super(SwordRobberAttacker, self).finish()



class EnemyImpaleShortAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(EnemyImpaleShortAttacker, self).__init__(sprite, attacker_params)
        self.magic_list = []


    def run(self, target, current_frame_add):
        if self.hit(target, current_frame_add):
            # regardless of target's dfs
            damage = self.sprite.atk
            target.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False


    def handle_under_attack(self, from_who, cost_hp, attack_method=cfg.Attack.METHOD_REGULAR):
        if attack_method == cfg.Attack.METHOD_REGULAR:
            # attack rebounce for this enemy
            super(EnemyImpaleShortAttacker, self).handle_under_attack(from_who, cost_hp, attack_method)
            from_who.attacker.handle_under_attack(self.sprite, cost_hp)
            blood_set = BloodSet(self.sprite, from_who.pos, from_who.setting.HEIGHT)
            self.magic_list.append(blood_set)

        elif attack_method == cfg.Attack.METHOD_MAGIC:
            # but recieve more hp-cost from magic attack
            super(EnemyImpaleShortAttacker, self).handle_under_attack(from_who, cost_hp * 2, attack_method)


    def handle_additional_status(self, status_id, status_object):
        if status_id == cfg.SpriteStatus.UNDER_THUMP:
            # anti under_thump
            from_who = status_object["from_who"]
            from_who.attacker.finish()
            from_who.animation.set_init_frame(cfg.SpriteAction.STAND)
            status_object["key_vec"] = Vector2.from_points(self.sprite.pos, from_who.pos)
            from_who.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP, status_object)
        else:
            super(EnemyImpaleShortAttacker, self).handle_additional_status(status_id, status_object)



class EnemySelfDestructionAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(EnemySelfDestructionAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        self.bomb_damage = attacker_params["bomb_damage"]
        self.bomb_trigger_times = list(attacker_params["bomb_trigger_times"])
        self.bomb_thump_crick_time = attacker_params["bomb_thump_crick_time"]
        self.bomb_thump_acceleration = attacker_params["bomb_thump_acceleration"]
        self.bomb_thump_out_speed = attacker_params["bomb_thump_out_speed"]

        self.magic_list = []
        self.bomb_begin = False


    def chance(self, target):
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if distance_to_target <= self.attack_range * 5:
            return True
        return False


    def set_self_destruction(self, target):
        self_destruction = SelfDestruction(self.sprite, [target, ], self.bomb_damage, self.bomb_trigger_times, 
            self.bomb_thump_crick_time, self.bomb_thump_acceleration, self.bomb_thump_out_speed)
        self.magic_list.append(self_destruction)
        self.bomb_begin = True
        self.sprite.hp_status = cfg.HpStatus.DIE



class EnemyLongAttacker(EnemyAngleAttacker):
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


    def run(self, target, current_frame_add):
        if self.hit(target, current_frame_add):
            damage = max(0, self.sprite.atk - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False


    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()



class ArrowAttacker(EnemyLongAttacker):
    """
    attacker that has ammo sprite to calculate hit and draw
    """
    def __init__(self, sprite, attacker_params):
        super(ArrowAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        self.current_magic = None
        self.magic_list = []


    def chance(self, target):
        sp = self.sprite
        if self.is_static_object_block(target):
            return False
        return True


    def reset_vars(self):
        # a lock, only one magic is running in an attack
        self.method = None
        self.current_magic = None


    def run(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.key_frames:

            # generate arrow
            self.current_magic = ArrowSet(sp, [target, ], self.params)
            self.magic_list.append(self.current_magic)


    def finish(self):
        self.reset_vars()



class ArmouredShooterAttacker(EnemyLongAttacker):
    def __init__(self, sprite, attacker_params):
        super(ArmouredShooterAttacker, self).__init__(sprite, attacker_params)
        self.grenade_params = attacker_params["grenade"]
        self.magic_list = []
        self.reset_vars()

    def reset_vars(self):
        self.method = None
        self.current_magic = None


    def chance(self, target):
        sp = self.sprite
        is_chance = super(ArmouredShooterAttacker, self).chance(target)
        if not is_chance:
            return False

        if happen(sp.brain.ai.ATTACK_GRENADE_PROB) \
            and (not self.is_static_object_block(target)) \
            and len(self.magic_list) < self.grenade_params["max_num"]:
            self.method = "grenade"
        else:
            self.method = "regular"

        return True


    def grenade(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.grenade_params["key_frames"]:
            self.current_magic = GrenadeBomb(sp, [target, ], self.grenade_params)
            self.magic_list.append(self.current_magic)


    def finish(self):
        super(ArmouredShooterAttacker, self).finish()
        self.reset_vars()



class WerwolfAttacker(EnemyShortAttacker):
    def __init__(self, sprite, attacker_params):
        super(WerwolfAttacker, self).__init__(sprite, attacker_params)
        self.params = attacker_params
        catch = attacker_params["catch"]
        self.chance_range_min = catch["chance_range_min"]
        #self.crick_time = catch["crick_time"]
        self.damage_a = catch["damage_a"]
        self.damage_b = catch["damage_b"]
        self.thump_out_speed = catch["thump_out_speed"]
        self.thump_crick_time = catch["thump_crick_time"]
        self.thump_acceleration = catch["thump_acceleration"]
        self.magic_list = []
        self.reset_vars()


    def reset_vars(self):
        self.method = None


    def catch_chance(self, target):
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        if distance_to_target < self.chance_range_min:
            return False

        if self.is_static_object_block(target):
            return False

        return True


    def chance(self, target):
        sp = self.sprite
        if happen(sp.brain.ai.ATTACK_CATCH_PROB) and self.catch_chance(target):
            self.method = "catch"
            return True

        if super(WerwolfAttacker, self).chance(target):
            self.method = "regular"
            return True

        return False


    def catch_hit(self, target):
        if target in self.has_hits:
            return False

        if self.sprite.area.collidepoint(target.pos.x, target.pos.y):
            self.has_hits.add(target)
            return True

        return False


    def catch_run_a(self, target):
        target.attacker.handle_under_attack(self.sprite, self.damage_a)
        blood_set = BloodSet(self.sprite, target.pos, target.setting.HEIGHT)
        self.magic_list.append(blood_set)


    def catch_run_b(self, target):
        sp = self.sprite
        target.attacker.handle_under_attack(sp, self.damage_b)
        target.attacker.handle_additional_status(cfg.SpriteStatus.UNDER_THUMP,
            {"crick_time": self.thump_crick_time, "out_speed": self.thump_out_speed,
            "acceleration": self.thump_acceleration, 
            "key_vec": -sp.key_vec})


    def finish(self):
        super(WerwolfAttacker, self).finish()
        self.reset_vars()



class LeonhardtAttacker(EnemyAngleAttacker):
    def __init__(self, sprite, attacker_params):
        super(LeonhardtAttacker, self).__init__(sprite, 
            attacker_params["range"], attacker_params["angle"], attacker_params["key_frames"])
        self.params = attacker_params
        self.death_coil_params = attacker_params["death_coil"]
        self.hell_claw_params = attacker_params["hell_claw"]
        self.death_domain_params = attacker_params["death_domain"]
        self.skill_used_count = {"death_coil": 0, "hell_claw": 0, "death_domain": 0}
        self.skill_continuously_use_max = 2
        self.magic_list = []
        self.reset_vars()


    def reset_vars(self):
        self.method = None
        self.current_magic = None


    def is_target_blocked(self, target):
        sp = self.sprite
        x = min(sp.pos.x, target.pos.x)
        y = min(sp.pos.y, target.pos.y)
        w = abs(sp.pos.x - target.pos.x)
        h = abs(sp.pos.y - target.pos.y)
        r = pygame.Rect((x, y, w, h))
        for obj in sp.static_objects:
            if obj.setting.IS_BLOCK and obj.area.colliderect(r):
                return True

        return False


    def chance(self, target):
        # totally for ai, because player can judge whether it's a good attack chance himself
        # at the same time, choose which method to attack target
        sp = self.sprite
        distance_to_target = sp.pos.get_distance_to(target.pos)
        blocked = self.is_target_blocked(target)
        if happen(sp.brain.ai.ATTACK_REGULAR_PROB) \
            and distance_to_target <= self.attack_range:
            self.method = "regular"
            return True

        if happen(sp.brain.ai.ATTACK_DEATH_COIL_PROB) \
            and self.skill_used_count["death_coil"] < self.skill_continuously_use_max \
            and sp.mp > self.death_coil_params["mana"] \
            and distance_to_target <= self.death_coil_params["range"] * 2 \
            and (not blocked):
            self.method = "death_coil"
            return True

        if happen(sp.brain.ai.ATTACK_HELL_CLAW_PROB) \
            and self.skill_used_count["hell_claw"] < self.skill_continuously_use_max \
            and sp.mp > self.hell_claw_params["mana"] \
            and distance_to_target <= self.hell_claw_params["range"] \
            and (not blocked):
            self.method = "hell_claw"
            return True

        if happen(sp.brain.ai.ATTACK_DEATH_DOMAIN_PROB) \
            and self.skill_used_count["death_domain"] < self.skill_continuously_use_max \
            and sp.mp > self.death_domain_params["mana"]:
            sp.death_domain_direction_add = sp.direction
            self.method = "death_domain"
            return True

        return False


    def death_coil(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None and int(current_frame_add) in self.death_coil_params["key_frames"]:
            sp.mp -= self.death_coil_params["mana"]
            self.current_magic = DeathCoilSet(sp, [target, ],
                sp.static_objects, self.death_coil_params, sp.pos, target.pos)
            self.magic_list.append(self.current_magic)


    def hell_claw(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None:
            # this magic trigger at once for showing the tips, 
            # but damage claws will trigger at a certain delay
            sp.mp -= self.hell_claw_params["mana"]
            self.current_magic = HellClawSet(sp, [target, ], 
                sp.static_objects, self.hell_claw_params)
            self.magic_list.append(self.current_magic)


    def death_domain(self, target, current_frame_add):
        sp = self.sprite
        if self.current_magic is None:
            sp.mp -= self.death_domain_params["mana"]
            self.current_magic = DeathDomain(sp, [target, ],
                sp.static_objects, self.death_domain_params)
            self.magic_list.append(self.current_magic)


    def run(self, target, current_frame_add):
        if self.hit(target, current_frame_add):
            damage = max(0, self.sprite.atk - target.dfs)
            target.attacker.handle_under_attack(self.sprite, damage)
            return True
        return False


    def finish(self):
        len(self.has_hits) > 0 and self.has_hits.clear()

        if self.method in self.skill_used_count:
            # balance all skills use
            self.skill_used_count[self.method] += 1
            for k, v in self.skill_used_count.iteritems():
                if k != self.method and v > 0:
                    self.skill_used_count[k] -= 1

        self.reset_vars()



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

        p_target = target.area.center
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
    sfg.ArmouredShooter.ID: ArmouredShooterAttacker,
    sfg.SwordRobber.ID: SwordRobberAttacker,
    sfg.GanDie.ID: EnemyPoisonShortAttacker,
    sfg.Ghost.ID: GhostAttacker,
    sfg.TwoHeadSkeleton.ID: TwoHeadSkeletonAttacker,
    sfg.Werwolf.ID: WerwolfAttacker,
    sfg.SilverTentacle.ID: EnemyImpaleShortAttacker,
    sfg.Robot.ID: EnemySelfDestructionAttacker,
}


if __name__ == "__main__":
    pass
