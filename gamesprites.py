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
            "recover_hp_effect_time": 0, "under_attack_effect_time": 0}
        self.buff = {}
        self.debuff = {}
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


    def get_collide_static_object(self):
        for v in self.static_objects:
            if self.area.colliderect(v.area):
                return v


    def reset_action(self):
        self.action = cfg.HeroAction.STAND
        self.animation.reset_frame_adds()


    def update_status(self, passed_seconds):
        # update the status attribute
        self.status["under_attack_effect_time"] = max(0,
            self.status["under_attack_effect_time"] - passed_seconds)
        self.status["recover_hp_effect_time"] = max(0,
            self.status["recover_hp_effect_time"] - passed_seconds)


    def update(self, passed_seconds):
        pass


    def adjust_rect(self):
        # for drawing to the screen, 
        # y-axis should be a half of pos[1] and considering the distance from pos to image center
        # both rect and shadow_rect
        rect = self.animation.rect
        rect.center = (self.pos.x, self.pos.y * 0.5 - self.setting.POS_RECT_DELTA_Y)
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
        self.atk = self.setting.ATK
        self.dfs = self.setting.DFS
        self.status = {"hp": cfg.SpriteStatus.HEALTHY, 
            "recover_hp_effect_time": 0, "under_attack_effect_time": 0}
        self.buff = {}
        self.debuff = {}


    def place(self, pos, direction):
        # place renne at some position, facing some direction
        self.pos = Vector2(pos)
        self.direction = direction


    def draw(self, camera):
        self.animation.draw(camera)


    def move(self, speed, passed_seconds, key_vec=None):
        # try x and y direction move, go back to the old position when collided with something unwalkable
        k_vec = key_vec or self.key_vec
        k_vec.normalize()
        for coord in ("x", "y"):
            key_vec_coord = getattr(k_vec, coord)
            if key_vec_coord != 0:
                old_coord = getattr(self.pos, coord)
                setattr(self.pos, coord, old_coord + key_vec_coord * speed * passed_seconds)
                self.area.center = self.pos("xy")
                collided_obj = self.get_collide_static_object()
                if (collided_obj is not None and collided_obj.setting.IS_BLOCK) \
                    or self.is_collide_map_boundry():
                    setattr(self.pos, coord, old_coord)
                    self.area.center = self.pos("xy")

                elif collided_obj is not None and collided_obj.setting.IS_ELIMINABLE \
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
        if self.status.get("action_rate_scale") is not None:
            self.move(self.setting.WALK_SPEED * self.status["action_rate_scale"], passed_seconds)
        else:
            self.move(self.setting.WALK_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.WALK, passed_seconds)


    def run(self, passed_seconds):
        # cost some stamina when running
        self.sp = max(0, self.sp - self.setting.SP_COST_RATE * passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)
        if self.status.get("action_rate_scale") is not None:
            self.move(self.setting.RUN_SPEED * self.status["action_rate_scale"], passed_seconds)
        else:
            self.move(self.setting.RUN_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.RUN, passed_seconds)


    def attack(self, passed_seconds):
        if self.attacker.method == "destroy_aerolite":
            # use another action frame for this skill
            frame_action = cfg.HeroAction.SKILL
        else:
            frame_action = cfg.HeroAction.ATTACK

        is_finish = self.animation.run_sequence_frame(frame_action, passed_seconds)

        if is_finish:
            self.attacker.finish()
            self.action = cfg.HeroAction.STAND
        else:
            if self.attacker.method == "regular":
                hit_count = 0
                for em in self.enemies:
                    hit_it = self.attacker.run(em, self.animation.get_current_frame_add(frame_action))
                    if hit_it:
                        hit_count += 1

                if hit_count > 0:
                    self.sound_box.play(random.choice(sfg.Sound.RENNE_ATTACK_HITS))

            elif self.attacker.method == "destroy_fire":
                self.attacker.destroy_fire(self.animation.get_current_frame_add(frame_action))

            elif self.attacker.method == "destroy_bomb":
                self.attacker.destroy_bomb(self.animation.get_current_frame_add(frame_action))

            elif self.attacker.method == "destroy_aerolite":
                self.attacker.destroy_aerolite(self.animation.get_current_frame_add(frame_action))


    def run_attack(self, passed_seconds):
        # a special attack type, when hero is running and press attack
        self.animation.run_sequence_frame(cfg.HeroAction.ATTACK, passed_seconds)
        if self.animation.get_current_frame_add(cfg.HeroAction.ATTACK) > 8:
            # don't full-run the attack frame for better effect
            self.animation.reset_frame_adds()
            self.attacker.finish()
            self.action = cfg.HeroAction.STAND
        else:
            self.move(self.setting.RUN_SPEED * 0.6, passed_seconds)
            hit_count = 0
            for em in self.enemies:
                hit_it = self.attacker.run(em, self.animation.get_current_frame_add(cfg.HeroAction.ATTACK))
                if hit_it and not hasattr(em.setting, "ANTI_THUMP"):
                    em.status["under_thump"] = {
                        "crick_time": self.setting.ATTACKER_PARAMS["run_attack"]["crick_time"],
                        "out_speed": self.setting.ATTACKER_PARAMS["run_attack"]["out_speed"], 
                        "acceleration": self.setting.ATTACKER_PARAMS["run_attack"]["acceleration"],
                        "key_vec": Vector2.from_points(self.pos, em.pos)}
                    hit_count += 1

            if hit_count > 0:
                self.sound_box.play(random.choice(sfg.Sound.RENNE_ATTACK_HITS))


    def win(self, passed_seconds):
        is_finish = self.animation._run_renne_win_frame(passed_seconds)
        if is_finish:
            self.attacker.finish()
            self.action = cfg.HeroAction.STAND
        else:
            self.attacker.dizzy(self.animation.get_current_frame_add(cfg.HeroAction.WIN))


    def locked(self):
        # check whether renne is locked, if so, and lock her without handling any event from user input
        if self.action in (cfg.HeroAction.ATTACK, cfg.HeroAction.RUN_ATTACK):
            # attacking, return directly
            return True

        if self.action == cfg.HeroAction.WIN:
            # painted egg, return directly
            return True

        return False
        

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
                # do nothing
                return

        if self.locked():
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
            if self.action == cfg.HeroAction.RUN and self.sp > 0:
                self.action = cfg.HeroAction.RUN_ATTACK
            else:
                self.action = cfg.HeroAction.ATTACK
                self.attacker.method = "regular"
            atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS)
            self.sound_box.play(atk_snd)

        elif pressed_keys[sfg.UserKey.ATTACK_DESTROY_FIRE]:
            if self.mp > self.attacker.destroy_fire_params["mana"] \
                and self.attacker.magic_cds["destroy_fire"] == 0:
                atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS2)
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK
                self.attacker.method = "destroy_fire"

        elif pressed_keys[sfg.UserKey.ATTACK_DESTROY_BOMB]:
            if self.mp > self.attacker.destroy_bomb_params["mana"] \
                and self.attacker.magic_cds["destroy_bomb"] == 0:
                atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS2)
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK
                self.attacker.method = "destroy_bomb"

        elif pressed_keys[sfg.UserKey.ATTACK_DESTROY_AEROLITE]:
            if self.mp > self.attacker.destroy_aerolite_params["mana"] \
                and self.attacker.magic_cds["destroy_aerolite"] == 0:
                atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS2)
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK
                self.attacker.method = "destroy_aerolite"

        elif pressed_keys[sfg.UserKey.REST]:
            self.action = cfg.HeroAction.REST

        elif pressed_keys[sfg.UserKey.WIN]:
            if self.attacker.magic_cds["dizzy"] == 0:
                self.action = cfg.HeroAction.WIN
                self.sound_box.play(sfg.Sound.RENNE_WIN)

        elif self.key_vec:
            if self.action == cfg.HeroAction.RUN and self.sp > 0:
                # press run and stamina enough
                self.action = cfg.HeroAction.RUN
            else:
                self.action = cfg.HeroAction.WALK

        else:
            self.action = cfg.HeroAction.STAND


    def update_status(self, passed_seconds):
        super(Renne, self).update_status(passed_seconds)
        if self.status.get("under_thump") is not None:
            self.action = cfg.HeroAction.UNCONTROLLED
            self.move(self.status["under_thump"]["out_speed"], passed_seconds, 
                self.status["under_thump"]["key_vec"])
            self.status["under_thump"]["out_speed"] = max(0, self.status["under_thump"]["out_speed"] \
                + self.status["under_thump"]["acceleration"] * passed_seconds)
            self.status["under_thump"]["crick_time"] -= passed_seconds
            if self.status["under_thump"]["crick_time"] <= 0:
                self.reset_action()
                self.status.pop("under_thump")


    def update(self, passed_seconds, external_event=None):
        if external_event is not None:
            if external_event == cfg.GameStatus.PAUSE:
                # user pause the game, don't update animation
                return

        self.update_status(passed_seconds)

        if self.action == cfg.HeroAction.ATTACK:
            self.attack(passed_seconds)

        elif self.action == cfg.HeroAction.RUN_ATTACK:
            self.run_attack(passed_seconds)

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

        # update some debuff
        if self.debuff.get("poison") is not None:
            poison = self.debuff["poison"]
            if poison["time_left"] < 0:
                self.debuff.pop("poison")
            else:
                poison["time_left"] -= passed_seconds
                if len(poison["time_list"]) > 0 and poison["time_left"] <= poison["time_list"][-1]:
                    poison["time_list"].pop()
                    self.hp -= poison["dps"]
                    self.status["hp"] = self.cal_sprite_status(self.hp, self.setting.HP)
                    self.animation.show_cost_hp(poison["dps"])

        if self.debuff.get("frozen") is not None:
            self.debuff["frozen"]["time_left"] -= passed_seconds
            if self.debuff["frozen"]["time_left"] < 0:
                self.debuff.pop("frozen")

        if self.debuff.get("weak") is not None:
            self.debuff["weak"]["time_left"] -= passed_seconds
            if self.debuff["weak"]["time_left"] < 0:
                self.debuff.pop("weak")
                # return normal atk and dfs
                self.atk = self.setting.ATK
                self.dfs = self.setting.DFS

        if self.status.get("action_rate_scale") is not None:
            self.status["action_rate_scale_time"] -= passed_seconds
            if self.status["action_rate_scale_time"] < 0:
                self.status.pop("action_rate_scale")
                self.status.pop("action_rate_scale_time")

        self.animation.update(passed_seconds)

        # update magic cd
        for magic_name in self.attacker.magic_cds:
            self.attacker.magic_cds[magic_name] = max(0, 
                self.attacker.magic_cds[magic_name] - passed_seconds)



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
        self.attacker = simulator.ENEMY_ATTACKER_MAPPING[self.setting.ID](
            self, self.setting.ATTACKER_PARAMS)
        self.view_sensor = simulator.ViewSensor(self, angle=self.setting.VIEW_ANGLE)
        self.brain = controller.SpriteBrain(self, ai, game_map.waypoints)


    def draw(self, camera):
        self.animation.draw(camera)

        if self.status["hp"] == cfg.SpriteStatus.DIE:
            return

        self.emotion_animation.draw(camera)


    def move(self, speed, passed_seconds, check_reachable=False, key_vec=None):
        k_vec = key_vec or self.key_vec
        k_vec.normalize()
        old_pos = self.pos.copy()
        self.pos += k_vec * speed * passed_seconds
        self.area.center = self.pos("xy")
        if check_reachable and not self.reachable():
            self.pos = old_pos
            self.area.center = self.pos("xy")
            self.brain.interrupt = True


    def reachable(self):
        # use waypoints to check whether the current self.pos is reachable
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
                self.sound_box.play(random.choice(sfg.Sound.ENEMY_ATTACK_HITS))


    def under_thump(self, passed_seconds):
        self.move(self.status["under_thump"]["out_speed"], passed_seconds,
            check_reachable=True, key_vec=self.status["under_thump"]["key_vec"])
        self.animation.run_circle_frame(cfg.EnemyAction.UNDER_THUMP, passed_seconds) 


    def reset_action(self, force=False):
        if force:
            # reset all related things for enemy by force!
            self.brain.persistent = False
            self.brain.interrupt = False
            self.attacker.finish()
            self.action = cfg.EnemyAction.STAND
            self.animation.reset_frame_adds()
        else:
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


    def event_handle(self, pressed_keys=None, external_event=None):
        # perception and belief control level
        if external_event is not None and external_event != cfg.GameStatus.IN_PROGRESS:
            if external_event == cfg.GameStatus.INIT:
                self.action = cfg.EnemyAction.STAND
            elif external_event == cfg.GameStatus.HERO_LOSE:
                self.reset_action()

            return

        if self.status["hp"] == cfg.SpriteStatus.DIE:
            return

        if self.status.get("stun_time", 0) > 0 or self.status.get("dizzy_time", 0) > 0:
            self.reset_action(force=True)
            return

        if self.action == cfg.EnemyAction.UNDER_THUMP:
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


    def update_status(self, passed_seconds):
        super(Enemy, self).update_status(passed_seconds)
        if self.status.get("stun_time", 0) > 0:
            self.animation.set_init_frame(cfg.EnemyAction.STAND)
            self.status["stun_time"] = max(0, self.status["stun_time"] - passed_seconds)
            if self.status["stun_time"] == 0:
                self.set_emotion(cfg.SpriteEmotion.NORMAL, force=True)
        if self.status.get("dizzy_time", 0) > 0:
            self.animation.set_init_frame(cfg.EnemyAction.STAND)
            self.status["dizzy_time"] = max(0, self.status["dizzy_time"] - passed_seconds)
            if self.status["dizzy_time"] == 0:
                self.set_emotion(cfg.SpriteEmotion.NORMAL, force=True)
        if self.status.get("under_thump") is not None:
            self.action = cfg.EnemyAction.UNDER_THUMP
            self.status["under_thump"]["out_speed"] = max(0, self.status["under_thump"]["out_speed"] \
                + self.status["under_thump"]["acceleration"] * passed_seconds)
            self.status["under_thump"]["crick_time"] -= passed_seconds
            if self.status["under_thump"]["crick_time"] <= 0:
                self.reset_action(force=True)
                self.status.pop("under_thump")
        if self.status.get("crick") is not None:
            self.action = cfg.EnemyAction.UNCONTROLLED
            self.status["crick"]["time"] -= passed_seconds
            if self.status["crick"]["time"] <= 0:
                # reset to old action
                self.action = self.status["crick"]["old_action"]
                self.status.pop("crick")
                 

    def update(self, passed_seconds, external_event=None):
        # physics level
        if external_event is not None:
            if external_event == cfg.GameStatus.PAUSE:
                # user pause the game, don't update animation
                return

        self.update_status(passed_seconds)

        if self.status["hp"] != cfg.SpriteStatus.DIE \
            and self.status.get("stun_time", 0) == 0 and self.status.get("dizzy_time", 0) == 0:

            if self.action == cfg.EnemyAction.ATTACK:
                self.attack(passed_seconds)

            elif self.action == cfg.EnemyAction.STEER:
                self.walk(passed_seconds)

            elif self.action == cfg.EnemyAction.STAND:
                self.stand(passed_seconds)

            elif self.action == cfg.EnemyAction.WALK:
                self.walk(passed_seconds, True)

            elif self.action == cfg.EnemyAction.UNDER_THUMP:
                self.under_thump(passed_seconds)

        self.animation.update(passed_seconds)
        self.emotion_animation.update(passed_seconds)



class Leonhardt(Enemy):
    def __init__(self, setting, pos, direction):
        super(Leonhardt, self).__init__(setting, pos, direction)
        self.mp = self.setting.MP
        self.running_attack_frame_type = None


    def stand(self, passed_seconds):
        super(Leonhardt, self).stand(passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)


    def run(self, passed_seconds):
        self.move(self.setting.RUN_SPEED, passed_seconds, check_reachable=False)
        self.animation.run_circle_frame(cfg.LeonHardtAction.RUN, passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)


    def walk(self, passed_seconds):
        # Leon doesn't walk, he always runs
        self.run(passed_seconds)


    def attack(self, passed_seconds):
        if self.running_attack_frame_type is None:
            if self.attacker.method == "death_coil":
                # death coil use this attack frame
                self.running_attack_frame_type = cfg.LeonHardtAction.SKILL1
            elif self.attacker.method == "hell_claw":
                # hell claw use this attack frame
                self.running_attack_frame_type = cfg.LeonHardtAction.SKILL2
            else:
                # random attack frame for others
                self.running_attack_frame_type = random.choice(
                    (cfg.LeonHardtAction.ATTACK, cfg.LeonHardtAction.ATTACK2))
            self.sound_box.play(random.choice(sfg.Sound.LEONHARDT_ATTACKS))

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
                    self.sound_box.play(random.choice(sfg.Sound.ENEMY_ATTACK_HITS))

            elif self.attacker.method == "death_coil":
                self.attacker.death_coil(self.brain.target, 
                    self.animation.get_current_frame_add(self.running_attack_frame_type))

            elif self.attacker.method == "hell_claw":
                self.attacker.hell_claw(self.brain.target,
                    self.animation.get_current_frame_add(self.running_attack_frame_type))



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
    sfg.SkeletonWarrior2.ID: Enemy,
    sfg.Ghost.ID: Enemy,
    sfg.TwoHeadSkeleton.ID: Enemy,
    sfg.Werwolf.ID: Enemy,
    sfg.SilverImpale.ID: Enemy,
}
