import pygame
from pygame.locals import *
import random
from gameobjects.vector2 import Vector2
import simulator
from animation import SpriteEmotionAnimator, RenneAnimator, EnemyAnimator
from musicbox import SoundBox
import controller
from base.util import Timer, happen
from base import constant as cfg
from etc import setting as sfg



############## some tools for sprites ####################

def enemy_in_one_screen(hero, enemy):
    if abs(enemy.pos[0] - hero.pos[0]) > sfg.GameMap.ONE_SCREEN_DISTANCE_WIDTH or \
        abs(enemy.pos[1] - hero.pos[1]) > sfg.GameMap.ONE_SCREEN_DISTANCE_HEIGHT:
        # the distance between renne and enemy is beyond one screen size, ignore it for saving cpu
        return False
    return True



############## sprite module ###########################

class GameSprite(pygame.sprite.DirtySprite):
    """
    basic sprite class having basic attribute
    """

    def __init__(self, 
            name, 
            hp, # health point
            atk, # physical attack
            dfs, # defense
            pos, # position on the map, not screen
            direction # sprite direction it faces
        ):
        super(GameSprite, self).__init__()
        self.name = name
        self.hp = hp
        self.atk = atk
        self.dfs = dfs
        # a chaos dict that holding many kinds of status, i don't want many attributes, so i use it
        self.status = {"hp": cfg.SpriteStatus.HEALTHY, 
            "recover_hp_effect_time": 0, "under_attack_effect_time": 0, "stun_time": 0,
            "dizzy_time": 0}
        self.pos = Vector2(pos)
        self.direction = direction

        self.action = cfg.SpriteAction.STAND
        self.key_vec = Vector2() # a normal vector represents the direction
        

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


    def is_collide_map_boundry(self):
        max_w, max_h = self.game_map.size
        w, h = self.area.center
        if w <= 0 or h <= 0 or w >= max_w or h >= max_h:
            return True
        return False


    def is_collide_static_objects(self):
        for v in self.static_objects:
            if v.setting.IS_BLOCK and self.area.colliderect(v.area):
                return True


    def get_collide_static_object(self):
        for v in self.static_objects:
            if self.area.colliderect(v.area):
                return v


    def update(self):
        pass


    def adjust_rect(self):
        # for drawing to the screen, 
        # y-axis should be a half of pos[1] and considering the distance from pos to image center
        # both rect and shadow_rect
        rect = self.animation.rect
        rect.center = (self.pos.x, self.pos.y / 2 - self.setting.POS_RECT_DELTA_Y)
        shadow_rect = self.animation.shadow_rect
        shadow_rect.center = (rect.center[0], rect.center[1] + self.setting.SHADOW_RECT_DELTA_Y)


    def draw(self, camera):
        pass



class Renne(GameSprite):
    def __init__(self, setting, pos, direction):
        super(Renne, self).__init__(setting.NAME, setting.HP, setting.ATK, setting.DFS, pos, direction)

        self.setting = setting
        self.mp = self.setting.MP
        self.sp = self.setting.SP
        self.level = 1
        self.exp = 0

        self.animation = RenneAnimator(self)
        self.sound_box = SoundBox()

        # represent the sprite area, used for deciding frame layer and collide, attack computing or so
        self.area = pygame.Rect(0, 0, self.setting.RADIUS * 2, self.setting.RADIUS * 2)
        self.area.center = self.pos('xy')

        self.dizzy_targets = set()


    def activate(self, allsprites, enemies, static_objects, game_map):
        self.allsprites = allsprites
        self.enemies = enemies
        self.static_objects = static_objects
        self.game_map = game_map
        self.attacker = simulator.RenneAttacker(self, self.setting.ATTACKER_PARAMS)


    def recover(self):
        # recover renne's whole status, usually when the current chapter pass
        self.hp = self.setting.HP
        self.mp = self.setting.MP
        self.sp = self.setting.SP
        self.status["hp"] = cfg.SpriteStatus.HEALTHY 
        self.status["under_attack_effect_time"] = 0
        self.status["recover_hp_effect_time"] = 0
        self.status["stun_time"] = 0


    def place(self, pos, direction):
        # place renne at some position, facing some direction
        self.pos = Vector2(pos)
        self.direction = direction


    def draw(self, camera):
        self.animation.draw(camera)


    def move(self, speed, passed_seconds):
        # try x and y direction move, go back to the old position when collided with something unwalkable
        self.key_vec.normalize()
        for coord in ("x", "y"):
            key_vec_coord = getattr(self.key_vec, coord)
            if key_vec_coord != 0:
                old_coord = getattr(self.pos, coord)
                setattr(self.pos, coord, old_coord + key_vec_coord * speed * passed_seconds)
                self.area.center = self.pos("xy")
                collided_obj = self.get_collide_static_object()
                if collided_obj is None:
                    continue

                if collided_obj.setting.IS_BLOCK or self.is_collide_map_boundry():
                    setattr(self.pos, coord, old_coord)
                    self.area.center = self.pos("xy")

                elif collided_obj.setting.IS_ELIMINABLE \
                    and collided_obj.setting.ELIMINATION_TYPE == cfg.StaticObject.ELIMINATION_TYPE_FOOD:
                    real_recover_hp = min(self.setting.HP - self.hp, 
                        collided_obj.setting.RECOVER_HP)
                    self.hp += real_recover_hp
                    self.status["hp"] = self.cal_sprite_status(self.hp, self.setting.HP)
                    self.status["recover_hp_effect_time"] = sfg.Sprite.RECOVER_HP_EFFECT_TIME
                    self.animation.show_recover_hp(real_recover_hp)
                    collided_obj.status = cfg.StaticObject.STATUS_VANISH
                    collided_obj.kill()


    def stand(self, passed_seconds):
        if self.status["hp"] != cfg.SpriteStatus.DIE:
            self.sp = min(self.setting.SP, self.sp + self.setting.SP_RECOVERY_RATE * passed_seconds)
            self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.STAND, passed_seconds)


    def rest(self, passed_seconds):
        self.sp = min(self.setting.SP, self.sp + self.setting.SP_RECOVERY_RATE * 2 * passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * 2 * passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.REST, passed_seconds)


    def walk(self, passed_seconds):
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)
        self.move(self.setting.WALK_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.WALK, passed_seconds)


    def run(self, passed_seconds):
        # cost some stamina when running
        self.sp = max(0, self.sp - self.setting.SP_COST_RATE * passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)
        self.move(self.setting.RUN_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.RUN, passed_seconds)


    def attack(self, method, passed_seconds):
        if self.attacker.method is None:
            self.attacker.method = method
        is_finish = self.animation.run_sequence_frame(cfg.HeroAction.ATTACK, passed_seconds)
        if is_finish:
            self.attacker.finish()
            self.action = cfg.HeroAction.STAND
        else:
            if self.attacker.method == "regular":
                hit_count = 0
                for em in self.enemies:
                    hit_it = self.attacker.run(em, self.animation.get_current_frame_add(cfg.HeroAction.ATTACK))
                    if hit_it:
                        hit_count += 1

                if hit_count > 0:
                    self.sound_box.play(random.choice(("attack_hit", "attack_hit2")))

            elif self.attacker.method == "destroy_fire":
                self.attacker.destroy_fire(self.animation.get_current_frame_add(cfg.HeroAction.ATTACK))

            elif self.attacker.method == "destroy_bomb":
                self.attacker.destroy_bomb(self.animation.get_current_frame_add(cfg.HeroAction.ATTACK))

            elif self.attacker.method == "destroy_aerolite":
                self.attacker.destroy_aerolite(self.animation.get_current_frame_add(cfg.HeroAction.ATTACK))


    def win(self, passed_seconds):
        is_finish = self.animation._run_renne_win_frame(passed_seconds)
        if int(self.animation.get_current_frame_add(self.action)) in self.setting.DIZZY_KEY_FRAME:
            for sp in self.enemies:
                if self.pos.get_distance_to(sp.pos) < self.setting.DIZZY_RANGE \
                    and sp not in self.dizzy_targets:
                    self.dizzy_targets.add(sp)
                    if happen(self.setting.DIZZY_PROB):
                        sp.status["dizzy_time"] = self.setting.DIZZY_TIME
                        sp.set_emotion(cfg.SpriteEmotion.DIZZY)

        if is_finish:
            self.dizzy_targets.clear()
            self.action = cfg.HeroAction.STAND
        

    def event_handle(self, pressed_keys, external_event=None):
        if external_event is not None:
            if external_event == cfg.GameStatus.INIT:
                self.action = cfg.HeroAction.STAND
                return
            elif external_event == cfg.GameStatus.HERO_LOSE:
                if self.action != cfg.HeroAction.ATTACK:
                    self.action = cfg.HeroAction.STAND
                return 
            elif external_event == cfg.GameStatus.PAUSE:
                # do nothin
                return

        if self.action in (cfg.HeroAction.ATTACK, 
            cfg.HeroAction.ATTACK_DESTROY_FIRE, cfg.HeroAction.ATTACK_DESTROY_BOMB,
            cfg.HeroAction.ATTACK_DESTROY_AEROLITE):
            # attacking, return directly
            return

        if self.action == cfg.HeroAction.WIN:
            # painted egg, return directly
            return

        # calculate direction
        self.key_vec.x = self.key_vec.y = 0.0
        if pressed_keys[sfg.UserKey.LEFT]:
            self.key_vec.x -= 1.0
        if pressed_keys[sfg.UserKey.RIGHT]:
            self.key_vec.x += 1.0
        if pressed_keys[sfg.UserKey.UP]:
            self.key_vec.y -= 1.0
        if pressed_keys[sfg.UserKey.DOWN]:
            self.key_vec.y += 1.0
        self.direction = cfg.Direction.VEC_TO_DIRECT.get(self.key_vec.as_tuple(), self.direction)

        if pressed_keys[sfg.UserKey.ATTACK]:
            self.action = cfg.HeroAction.ATTACK
            atk_snd = random.choice(("renne_attack", "renne_attack2", "renne_attack3", 
                "renne_attack0", "renne_attack0", "renne_attack0"))
            if atk_snd is not None:
                self.sound_box.play(atk_snd)

        elif pressed_keys[sfg.UserKey.ATTACK_DESTROY_FIRE]:
            if self.mp > self.attacker.destroy_fire_params["mana"]:
                atk_snd = random.choice(("renne_attack", "renne_attack2", "renne_attack3"))
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK_DESTROY_FIRE

        elif pressed_keys[sfg.UserKey.ATTACK_DESTROY_BOMB]:
            if self.mp > self.attacker.destroy_bomb_params["mana"]:
                atk_snd = random.choice(("renne_attack", "renne_attack2", "renne_attack3"))
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK_DESTROY_BOMB

        elif pressed_keys[sfg.UserKey.ATTACK_DESTROY_AEROLITE]:
            if self.mp > self.attacker.destroy_aerolite_params["mana"]:
                atk_snd = random.choice(("renne_attack", "renne_attack2", "renne_attack3"))
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK_DESTROY_AEROLITE

        elif pressed_keys[sfg.UserKey.REST]:
            self.action = cfg.HeroAction.REST

        elif self.key_vec:
            if pressed_keys[sfg.UserKey.RUN] and self.sp > 0:
                # press run and stamina enough
                self.action = cfg.HeroAction.RUN
            else:
                self.action = cfg.HeroAction.WALK

        elif pressed_keys[sfg.UserKey.WIN]:
            # egg, show win animation
            if self.mp > self.setting.DIZZY_MANA:
                self.mp = max(0, self.mp - self.setting.DIZZY_MANA)
                self.action = cfg.HeroAction.WIN
                self.sound_box.play("renne_win")

        else:
            self.action = cfg.HeroAction.STAND


    def update(self, passed_seconds, external_event=None):
        if external_event is not None:
            if external_event == cfg.GameStatus.PAUSE:
                # user pause the game, don't update animation
                return

        if self.action == cfg.HeroAction.ATTACK:
            self.attack("regular", passed_seconds)

        elif self.action == cfg.HeroAction.ATTACK_DESTROY_FIRE:
            self.attack("destroy_fire", passed_seconds)

        elif self.action == cfg.HeroAction.ATTACK_DESTROY_BOMB:
            self.attack("destroy_bomb", passed_seconds)

        elif self.action == cfg.HeroAction.ATTACK_DESTROY_AEROLITE:
            self.attack("destroy_aerolite", passed_seconds)

        elif self.action == cfg.HeroAction.RUN:
            self.run(passed_seconds)

        elif self.action == cfg.HeroAction.WALK:
            self.walk(passed_seconds)

        elif self.action == cfg.HeroAction.WIN:
            self.win(passed_seconds)

        elif self.action == cfg.HeroAction.REST:
            self.rest(passed_seconds)

        elif self.action == cfg.HeroAction.STAND:
            self.stand(passed_seconds)

        self.animation.update(passed_seconds)

        for i, magic in enumerate(self.attacker.magic_list):
            if magic.status == cfg.Magic.STATUS_VANISH:
                self.attacker.magic_list.pop(i)
            else:
                magic.update(passed_seconds)




class Enemy(GameSprite):
    def __init__(self, setting, pos, direction):
        super(Enemy, self).__init__(setting.NAME, setting.HP, setting.ATK, setting.DFS, pos, direction)
        self.setting = setting
        self.status["emotion"] = cfg.SpriteEmotion.NORMAL
        self.emotion_animation = SpriteEmotionAnimator(self)

        self.animation = EnemyAnimator(self)
        self.sound_box = SoundBox()

        self.area = pygame.Rect(0, 0, self.setting.RADIUS * 2, self.setting.RADIUS * 2)
        self.area.center = self.pos('xy')


    def activate(self, ai, allsprites, hero, static_objects, game_map):
        # activate the enemy by passing all the nessary external information and ai to it
        self.game_map = game_map
        self.allsprites = allsprites
        self.hero = hero
        self.static_objects = static_objects
        self.attacker = simulator.ENEMY_ATTACKER_MAPPING[self.setting.ATTACKTYPE](
            self, self.setting.ATTACKER_PARAMS)
        self.view_sensor = simulator.ViewSensor(self, angle=self.setting.VIEW_ANGLE)
        self.brain = controller.SpriteBrain(self, ai, game_map.waypoints)


    def draw(self, camera):
        self.animation.draw(camera)

        if self.status["hp"] == cfg.SpriteStatus.DIE:
            return

        self.emotion_animation.draw(camera)


    def move(self, speed, passed_seconds, check_reachable=False):
        self.key_vec.normalize()
        old_pos = self.pos.copy()
        self.pos += self.key_vec * speed * passed_seconds
        self.area.center = self.pos("xy")
        if check_reachable and not self.reachable():
            self.pos = old_pos
            self.area.center = self.pos("xy")
            self.brain.interrupt = True


    def reachable(self):
        wps = self.brain.waypoints
        step = sfg.WayPoint.STEP_WIDTH
        x0 = self.pos.x - self.pos.x % step
        y0 = self.pos.y - self.pos.y % step
        for p in ((x0, y0), (x0 + step, y0), (x0, y0 + step), (x0 + step, y0 + step)):
            if p not in wps:
                return False
        return True


    def stand(self, passed_seconds):
        self.animation.run_circle_frame(cfg.EnemyAction.STAND, passed_seconds)


    def walk(self, passed_seconds, check_reachable=False):
        self.move(self.setting.WALK_SPEED, passed_seconds, check_reachable)
        self.animation.run_circle_frame(cfg.EnemyAction.WALK, passed_seconds)


    def attack(self, passed_seconds):
        is_finish = self.animation.run_sequence_frame(cfg.EnemyAction.ATTACK, passed_seconds)
        if is_finish:
            self.attacker.finish()
            self.brain.persistent = False
        else:
            hit_it = self.attacker.run(self.brain.target, 
                self.animation.get_current_frame_add(cfg.EnemyAction.ATTACK))
            if hit_it:
                self.sound_box.play(random.choice(("attack_hit", "attack_hit2", "attack_hit3")))


    def reset_action(self, force=False):
        if force:
            self.brain.persistent = False
            self.action = cfg.EnemyAction.STAND

        if not self.brain.persistent:
            self.action = cfg.EnemyAction.STAND


    def cal_angry(self, damage):
        # calculate enemy's emotion
        angry_hp_threshold = self.setting.HP * self.brain.ai.ANGRY_HP_RATIO
        if self.hp < angry_hp_threshold and self.hp + damage >= angry_hp_threshold:
            self.set_emotion(cfg.SpriteEmotion.ANGRY)


    def get_target(self, target):
        if self.brain.target is None:
            self.brain.target = target


    def set_emotion(self, emotion, force=False):
        if not force and self.status["emotion"] in (cfg.SpriteEmotion.STUN, cfg.SpriteEmotion.DIZZY):
            return

        self.emotion_animation.reset_frame(self.status["emotion"])
        self.status["emotion"] = emotion


    def external_event_handle(self, external_event):
        if external_event == cfg.GameStatus.INIT:
            self.action = cfg.EnemyAction.STAND
        elif external_event == cfg.GameStatus.HERO_LOSE:
            self.reset_action()
        elif external_event == cfg.GameStatus.PAUSE:
            # do nothing
            pass


    def event_handle(self, pressed_keys=None, external_event=None):
        # perception and belief control level
        if external_event is not None and external_event != cfg.GameStatus.IN_PROGRESS:
            self.external_event_handle(external_event)
            return

        if self.status["hp"] == cfg.SpriteStatus.DIE:
            return

        if self.status["stun_time"] > 0 or self.status["dizzy_time"] > 0:
            self.reset_action(force=True)
            return

        self.brain.think()
        for action in self.brain.actions:

            if action == cfg.EnemyAction.ATTACK:
                self.action = cfg.EnemyAction.ATTACK
            
            elif action == cfg.EnemyAction.STEER:
                self.action = cfg.EnemyAction.STEER
                self.allsprites.notify_nearby_alliance_for_target(self, self.brain.target)

            elif action == cfg.EnemyAction.LOOKOUT:
                # tell its brain the current target found(or None if no target in view scope)
                self.brain.target = self.brain.target or self.view_sensor.detect(self.hero)

            elif action == cfg.EnemyAction.STAND:
                self.action = cfg.EnemyAction.STAND

            elif action == cfg.EnemyAction.WALK:
                self.action = cfg.EnemyAction.WALK
                self.key_vec.x, self.key_vec.y = cfg.Direction.DIRECT_TO_VEC[self.direction] 


    def update_stun(self, passed_seconds):
        if self.status["stun_time"] > 0:
            self.animation.set_init_frame(cfg.EnemyAction.STAND)
            self.status["stun_time"] = max(0, self.status["stun_time"] - passed_seconds)
            if self.status["stun_time"] == 0:
                self.set_emotion(cfg.SpriteEmotion.NORMAL, force=True)


    def update_dizzy(self, passed_seconds):
        if self.status["dizzy_time"] > 0:
            self.animation.set_init_frame(cfg.EnemyAction.STAND)
            self.status["dizzy_time"] = max(0, self.status["dizzy_time"] - passed_seconds)
            if self.status["dizzy_time"] == 0:
                self.set_emotion(cfg.SpriteEmotion.NORMAL, force=True)
    

    def update(self, passed_seconds, external_event=None):
        # physics level
        if external_event is not None:
            if external_event == cfg.GameStatus.PAUSE:
                # user pause the game, don't update animation
                return

        self.update_stun(passed_seconds)
        self.update_dizzy(passed_seconds)

        if self.status["hp"] != cfg.SpriteStatus.DIE \
            and self.status["stun_time"] == 0 and self.status["dizzy_time"] == 0:

            if self.action == cfg.EnemyAction.ATTACK:
                self.attack(passed_seconds)

            elif self.action == cfg.EnemyAction.STEER:
                self.walk(passed_seconds)

            elif self.action == cfg.EnemyAction.STAND:
                self.stand(passed_seconds)

            elif self.action == cfg.EnemyAction.WALK:
                self.walk(passed_seconds, True)

        self.animation.update(passed_seconds)
        self.emotion_animation.update(passed_seconds)



class Leonhardt(Enemy):
    def __init__(self, setting, pos, direction):
        super(Leonhardt, self).__init__(setting, pos, direction)
        self.mp = self.setting.MP
        self.attack_frame_types = (cfg.EnemyAction.ATTACK, cfg.EnemyAction.ATTACK2, cfg.EnemyAction.ATTACK3)
        self.running_attack_frame_type = None


    def draw(self, camera):
        super(Leonhardt, self).draw(camera)


    def run(self, passed_seconds):
        self.move(self.setting.RUN_SPEED, passed_seconds, check_reachable=False)
        self.animation.run_circle_frame(cfg.EnemyAction.RUN, passed_seconds)


    def attack(self, passed_seconds):
        if self.running_attack_frame_type is None:
            if self.attacker.method == "hell_claw":
                # hell claw use this attack frame
                self.running_attack_frame_type = self.attack_frame_types[2]
            else:
                # random attack frame for others
                self.running_attack_frame_type = random.choice(self.attack_frame_types[:2])
            self.sound_box.play(random.choice(("leonhardt_attack", "leonhardt_attack2", "leonhardt_attack3")))

        is_finish = self.animation.run_sequence_frame(self.running_attack_frame_type, passed_seconds)
        if is_finish:
            self.attacker.finish()
            self.running_attack_frame_type = None
            self.brain.persistent = False
        else:
            if self.attacker.method == "regular":
                hit_it = self.attacker.run(self.brain.target, 
                    self.animation.get_current_frame_add(self.running_attack_frame_type))
                if hit_it:
                    self.sound_box.play(random.choice(("attack_hit", "attack_hit2", "attack_hit3")))

            elif self.attacker.method == "death_coil":
                self.attacker.death_coil(self.brain.target, 
                    self.animation.get_current_frame_add(self.running_attack_frame_type))

            elif self.attacker.method == "hell_claw":
                self.attacker.hell_claw(self.brain.target,
                    self.animation.get_current_frame_add(self.running_attack_frame_type))


    def event_handle(self, pressed_keys=None, external_event=None):
        if external_event is not None and external_event != cfg.GameStatus.IN_PROGRESS:
            self.external_event_handle(external_event)
            return

        if self.status["hp"] == cfg.SpriteStatus.DIE:
            return

        if self.status["stun_time"] > 0 or self.status["dizzy_time"] > 0:
            self.reset_action(force=True)
            return

        self.brain.think()
        for action in self.brain.actions:
            if action == cfg.EnemyAction.ATTACK:
                self.action = cfg.EnemyAction.ATTACK
            
            elif action == cfg.EnemyAction.STEER:
                self.action = cfg.EnemyAction.STEER

            elif action == cfg.EnemyAction.LOOKOUT:
                # tell its brain the current target found(or None if no target in view scope)
                self.brain.target = self.brain.target or self.view_sensor.detect(self.hero)

            elif action == cfg.EnemyAction.STAND:
                self.action = cfg.EnemyAction.STAND


    def update(self, passed_seconds, external_event=None):
        # physics level
        if external_event is not None:
            if external_event == cfg.GameStatus.PAUSE:
                # user pause the game, don't update animation
                return

        self.update_stun(passed_seconds)
        self.update_dizzy(passed_seconds)

        if self.status["hp"] != cfg.SpriteStatus.DIE:

            if self.action == cfg.EnemyAction.ATTACK:
                self.attack(passed_seconds)

            elif self.action == cfg.EnemyAction.STEER:
                self.run(passed_seconds)

            elif self.action == cfg.EnemyAction.STAND:
                self.stand(passed_seconds)

        self.animation.update(passed_seconds)
        self.emotion_animation.update(passed_seconds)

        # some attack effects
        for i, magic in enumerate(self.attacker.magic_list):
            if magic.status == cfg.Magic.STATUS_VANISH:
                self.attacker.magic_list.pop(i)
            else:
                magic.update(passed_seconds)

        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)




######## sprite group subclass ########
class GameSpritesGroup(pygame.sprite.LayeredDirty):
    def __init__(self):
        super(GameSpritesGroup, self).__init__()


    def update(self, passed_seconds):
        for v in self.sprites():
            v.update(passed_seconds)


    def notify_nearby_alliance_for_target(self, sprite, target):
        for other in self.sprites():
            if other is target or other is sprite or \
                sprite.pos.get_distance_to(other.pos) > sprite.setting.NEARBY_ALLIANCE_RANGE or \
                other.brain.target is not None:
                continue

            other.brain.target = target



ENEMY_CLASS_MAPPING = {
    sfg.SkeletonWarrior.ID: Enemy,
    sfg.CastleWarrior.ID: Enemy,
    sfg.SkeletonArcher.ID: Enemy,
    sfg.LeonHardt.ID: Leonhardt,
    sfg.ArmouredShooter.ID: Enemy,
    sfg.SwordRobber.ID: Enemy,
}
