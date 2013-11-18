# -*- coding: gbk -*-

import pygame
from pygame.locals import *
import random
from time import time
import math
from gameobjects.vector2 import Vector2
import simulator
from animation import SpriteEmotionAnimator, RenneAnimator, EnemyAnimator
from musicbox import SoundBox
import controller
from gameworld import StaticObjectGroup
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
        self.status = self.gen_sprite_init_status()
        self.buff = {}
        self.sound_box = SoundBox()
        self.pos = Vector2(pos)
        self.direction = direction

        self.action = cfg.SpriteAction.STAND
        self.frame_action = None
        self.key_vec = Vector2() # a normal vector represents the direction


    def gen_sprite_init_status(self):
        # a common value set a sprite,
        # a chaos dict that holding many kinds of status, i don't want many attributes, so i use it
        return {"hp": cfg.HpStatus.HEALTHY, "emotion": cfg.SpriteEmotion.NORMAL}
        

    def cal_sprite_status(self, current_hp, full_hp):
        # calculate the sprite status according the current hp and full hp
        if current_hp > full_hp * sfg.SpriteStatus.HEALTHY_RATIO_FLOOR:
            return cfg.HpStatus.HEALTHY
        elif current_hp > full_hp * sfg.SpriteStatus.WOUNDED_RATIO_FLOOR:
            return cfg.HpStatus.WOUNDED
        elif current_hp > full_hp * sfg.SpriteStatus.DANGER_RATIO_FLOOR:
            return cfg.HpStatus.DANGER
        else:
            return cfg.HpStatus.DIE


    def is_collide_map_boundry(self, pos=None):
        max_x, max_y = self.game_map.size
        p = pos or self.pos
        if p.x < 0 or p.y < 0 or p.x > max_x or p.y > max_y:
            return True
        return False


    def get_collide_static_object(self):
        for v in self.static_objects:
            if self.area.colliderect(v.area):
                return v


    def adjust_rect(self):
        self.animation.adjust_rect()


    def reset_action(self, force=True):
        if force:
            self.action = cfg.SpriteAction.STAND
            self.attacker.finish()
            self.frame_action = None
            self.animation.reset_frame_adds()
        else:
            if self.action != cfg.SpriteAction.ATTACK:
                self.action = cfg.SpriteAction.STAND


    def set_emotion(self, emotion, force=False):
        if not force and self.status["emotion"] in (cfg.SpriteEmotion.STUN, cfg.SpriteEmotion.DIZZY):
            return

        self.emotion_animation.reset_frame(self.status["emotion"])
        self.status["emotion"] = emotion


    def update_status(self, passed_seconds):
        # update the status attribute
        if self.status.get(cfg.SpriteStatus.UNDER_ATTACK) is not None:
            self.status[cfg.SpriteStatus.UNDER_ATTACK]["time"] -= passed_seconds
            if self.status[cfg.SpriteStatus.UNDER_ATTACK]["time"] < 0:
                self.status.pop(cfg.SpriteStatus.UNDER_ATTACK)

        if self.status.get(cfg.SpriteStatus.RECOVER_HP) is not None:
            self.status[cfg.SpriteStatus.RECOVER_HP]["time"] -= passed_seconds
            if self.status[cfg.SpriteStatus.RECOVER_HP]["time"] < 0:
                self.status.pop(cfg.SpriteStatus.RECOVER_HP)

        if self.status.get(cfg.SpriteStatus.STUN) is not None:
            self.animation.set_init_frame(cfg.SpriteAction.STAND)
            self.status[cfg.SpriteStatus.STUN]["time"] -= passed_seconds
            if self.status[cfg.SpriteStatus.STUN]["time"] < 0:
                self.status.pop(cfg.SpriteStatus.STUN)
                self.set_emotion(cfg.SpriteEmotion.NORMAL, force=True)

        if self.status.get(cfg.SpriteStatus.DIZZY) is not None:
            self.animation.set_init_frame(cfg.SpriteAction.STAND)
            self.status[cfg.SpriteStatus.DIZZY]["time"] -= passed_seconds
            if self.status[cfg.SpriteStatus.DIZZY]["time"] < 0:
                self.status.pop(cfg.SpriteStatus.DIZZY)
                self.set_emotion(cfg.SpriteEmotion.NORMAL, force=True)

        if self.status.get(cfg.SpriteStatus.BODY_SHAKE) is not None:
            self.status[cfg.SpriteStatus.BODY_SHAKE]["dx"] = random.randint(-5, 5)
            self.status[cfg.SpriteStatus.BODY_SHAKE]["dy"] = random.randint(-3, 3)
            self.status[cfg.SpriteStatus.BODY_SHAKE]["time"] -= passed_seconds
            if self.status[cfg.SpriteStatus.BODY_SHAKE]["time"] < 0:
                self.status.pop(cfg.SpriteStatus.BODY_SHAKE)

        if self.status.get(cfg.SpriteStatus.INVISIBLE) is not None:
            self.status[cfg.SpriteStatus.INVISIBLE]["time"]-= passed_seconds
            if self.status[cfg.SpriteStatus.INVISIBLE]["time"] < 0:
                self.status.pop(cfg.SpriteStatus.INVISIBLE)

        if self.status.get(cfg.SpriteStatus.CRICK) is not None:
            self.action = cfg.SpriteAction.UNCONTROLLED
            self.status[cfg.SpriteStatus.CRICK]["time"] -= passed_seconds
            if self.status[cfg.SpriteStatus.CRICK]["time"] <= 0:
                # reset to old action
                self.action = self.status[cfg.SpriteStatus.CRICK]["old_action"]
                self.status.pop(cfg.SpriteStatus.CRICK)

        if self.status.get(cfg.SpriteStatus.UNDER_THUMP) is not None:
            self.action = cfg.SpriteStatus.UNDER_THUMP
            # friction is an negative acceleration variable
            friction = - sfg.Physics.FRICTION_FACTOR * self.setting.WEIGHT
            self.status[cfg.SpriteStatus.UNDER_THUMP]["out_speed"] = max(0, 
                self.status[cfg.SpriteStatus.UNDER_THUMP]["out_speed"] + friction * passed_seconds)
            self.status[cfg.SpriteStatus.UNDER_THUMP]["crick_time"] -= passed_seconds
            if self.status[cfg.SpriteStatus.UNDER_THUMP]["crick_time"] <= 0:
                self.reset_action()
                self.status.pop(cfg.SpriteStatus.UNDER_THUMP)

        if self.status.get(cfg.SpriteStatus.POISON) is not None:
            poison = self.status[cfg.SpriteStatus.POISON]
            if poison["time_left"] < 0:
                self.status.pop(cfg.SpriteStatus.POISON)
            else:
                poison["time_left"] -= passed_seconds
                if len(poison["time_list"]) > 0 and poison["time_left"] <= poison["time_list"][-1]:
                    poison["time_list"].pop()
                    self.hp -= poison["dps"]
                    self.status["hp"] = self.cal_sprite_status(self.hp, self.setting.HP)
                    self.animation.show_cost_hp(poison["dps"])

        if self.status.get(cfg.SpriteStatus.FROZEN) is not None:
            self.status[cfg.SpriteStatus.FROZEN]["time_left"] -= passed_seconds
            if self.status[cfg.SpriteStatus.FROZEN]["time_left"] < 0:
                self.status.pop(cfg.SpriteStatus.FROZEN)

        if self.status.get(cfg.SpriteStatus.WEAK) is not None:
            self.status[cfg.SpriteStatus.WEAK]["time_left"] -= passed_seconds
            if self.status[cfg.SpriteStatus.WEAK]["time_left"] < 0:
                self.status.pop(cfg.SpriteStatus.WEAK)
                # return normal atk and dfs
                self.atk = self.setting.ATK
                self.dfs = self.setting.DFS

        if self.status.get(cfg.SpriteStatus.UNDER_PULL) is not None:
            speed = self.status[cfg.SpriteStatus.UNDER_PULL]["speed"]
            key_vec = self.status[cfg.SpriteStatus.UNDER_PULL]["key_vec"]
            self.move(speed, passed_seconds, key_vec)


    def update(self, passed_seconds):
        pass


    def draw(self, camera):
        pass



class Renne(GameSprite):
    def __init__(self, setting, pos, direction):
        super(Renne, self).__init__(setting.NAME, setting.HP, setting.ATK, setting.DFS, pos, direction)

        self.setting = setting
        self.magic_skill_damage_ratio = self.setting.MAGIC_SKILL_DAMAGE_RATIO
        self.mp = self.setting.MP
        self.sp = self.setting.SP
        self.level = 1
        self.exp = 0

        self.animation = RenneAnimator(self)
        self.emotion_animation = SpriteEmotionAnimator(self)
        self.attacker = simulator.RenneAttacker(self, self.setting.ATTACKER_PARAMS)

        # represent the sprite area, used for deciding frame layer and collide, attack computing or so
        self.area = pygame.Rect(0, 0, self.setting.RADIUS * 2, self.setting.RADIUS * 2)

        # for regular attack combo
        self.attack_combo = {"count": 0, "last_time": time(), 
            "time_delta": self.setting.ATTACKER_PARAMS["attack_combo_time_delta"], 
            "count_max": self.setting.ATTACKER_PARAMS["attack_combo_count_max"]}
        self.attack1_start_frame = self.setting.ATTACKER_PARAMS["attack1"]["start_frame"]
        self.attack1_end_frame = self.setting.ATTACKER_PARAMS["attack1"]["end_frame"]
        self.attack2_accumulate_power_frame = self.setting.ATTACKER_PARAMS["attack2"]["accumulate_power_frame"]
        self.attack2_accumulate_power_time = self.setting.ATTACKER_PARAMS["attack2"]["accumulate_power_time"]
        self.run_attack_params = self.setting.ATTACKER_PARAMS["run_attack"]


    def activate(self, allsprites, enemies, static_objects, game_map):
        self.area.center = self.pos("xy")
        self.allsprites = allsprites
        self.enemies = enemies
        self.static_objects = static_objects
        self.game_map = game_map


    def recover(self, level=None):
        # recover renne's whole status, usually when the current chapter pass
        self.level = level or self.level
        idx = self.level - 1
        self.hp = self.setting.HP = self.setting.LEVEL_HP[idx]
        self.mp = self.setting.MP = self.setting.LEVEL_MP[idx]
        self.sp = self.setting.SP = self.setting.LEVEL_SP[idx]
        self.atk = self.setting.ATK = self.setting.LEVEL_ATK[idx]
        self.magic_skill_damage_ratio = self.setting.MAGIC_SKILL_DAMAGE_RATIO = self.setting.LEVEL_MAGIC_SKILL_DAMAGE_RATIO[idx]
        self.dfs = self.setting.DFS = self.setting.LEVEL_DFS[idx]
        self.attacker.cal_real_attack_damage()
        self.attacker.refresh_skill()
        self.status = self.gen_sprite_init_status()


    def place(self, pos, direction):
        # place renne at some position, facing some direction
        self.pos = Vector2(pos)
        self.direction = direction


    def add_exp(self, exp):
        self.exp = min(self.exp + exp, self.setting.MAX_EXP)

        # level starts from 1, LEVEL_EXP list starts from 0
        new_level = self.level
        while new_level < self.setting.MAX_LEVEL and self.exp >= self.setting.LEVEL_EXP[new_level]:
            new_level += 1

        if new_level > self.level:
            # level up and recover status
            self.recover(new_level)
            # show level up words
            level_up_words = sfg.SpriteStatus.LEVEL_UP_WORDS_FONT.render(u"����!", True, sfg.SpriteStatus.LEVEL_UP_WORDS_COLOR)
            self.animation.show_follow_sprite_words(level_up_words, self.pos, 
                sfg.SpriteStatus.LEVEL_UP_WORDS_SHOW_TIME,
                self.setting.HEIGHT * 0.5, sfg.SpriteStatus.LEVEL_UP_WORDS_VEC_Z, self)
            # use recover hp effect to indicate level, dirty and work
            self.status[cfg.SpriteStatus.RECOVER_HP] = {"time": sfg.Sprite.RECOVER_HP_EFFECT_TIME * 2}

            self.animation.add_level_up_effect()


    def draw(self, camera):
        self.animation.draw(camera)
        self.emotion_animation.draw(camera)


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
                    self.status[cfg.SpriteStatus.RECOVER_HP] = {"time": sfg.Sprite.RECOVER_HP_EFFECT_TIME}
                    self.animation.show_recover_hp(real_recover_hp)
                    collided_obj.status = cfg.StaticObject.STATUS_VANISH
                    collided_obj.kill()


    def stand(self, passed_seconds):
        if self.status["hp"] != cfg.HpStatus.DIE:
            self.sp = min(self.setting.SP, self.sp + self.setting.SP_RECOVERY_RATE * passed_seconds)
            self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.STAND, passed_seconds)


    def rest(self, passed_seconds):
        self.sp = min(self.setting.SP, self.sp + self.setting.SP_RECOVERY_RATE * 2 * passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * 2 * passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.REST, passed_seconds)


    def walk(self, passed_seconds):
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)
        if self.status.get(cfg.SpriteStatus.FROZEN) is not None:
            self.move(self.setting.WALK_SPEED * self.status[cfg.SpriteStatus.FROZEN]["action_rate_scale"], 
                passed_seconds)
        else:
            self.move(self.setting.WALK_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.WALK, passed_seconds)


    def run(self, passed_seconds):
        # cost some stamina when running
        self.sp = max(0, self.sp - self.setting.SP_COST_RATE * passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)
        if self.status.get(cfg.SpriteStatus.FROZEN) is not None:
            self.move(self.setting.RUN_SPEED * self.status[cfg.SpriteStatus.FROZEN]["action_rate_scale"], 
                passed_seconds)
        else:
            self.move(self.setting.RUN_SPEED, passed_seconds)
        self.animation.run_circle_frame(cfg.HeroAction.RUN, passed_seconds)


    def attack(self, passed_seconds):
        if self.attacker.method == "regular1":
            self.attack1(passed_seconds)
        elif self.attacker.method == "regular2":
            self.attack2(passed_seconds)
        elif self.attacker.method == "destroy_fire":
            self.destroy_fire(passed_seconds)
        elif self.attacker.method == "destroy_bomb":
            self.destroy_bomb(passed_seconds)
        elif self.attacker.method == "destroy_aerolite":
            self.destroy_aerolite(passed_seconds)


    def destroy_fire(self, passed_seconds):
        self.frame_action = cfg.HeroAction.ATTACK
        is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
        if is_finish:
            self.reset_action()
        else:
            self.attacker.destroy_fire(self.animation.get_current_frame_add(self.frame_action))


    def destroy_bomb(self, passed_seconds):
        self.frame_action = cfg.HeroAction.ATTACK
        is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
        if is_finish:
            self.reset_action()
        else:
            self.attacker.destroy_bomb(self.animation.get_current_frame_add(self.frame_action))


    def destroy_aerolite(self, passed_seconds):
        self.frame_action = cfg.HeroAction.SKILL
        is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
        if is_finish:
            self.reset_action()
        else:
            self.attacker.destroy_aerolite(self.animation.get_current_frame_add(self.frame_action))


    def attack1(self, passed_seconds):
        self.frame_action = cfg.HeroAction.ATTACK
        current_frame_add = self.animation.get_current_frame_add(cfg.HeroAction.ATTACK)
        if current_frame_add < self.attack1_start_frame:
            # short attack starts
            self.animation.set_frame_add(cfg.HeroAction.ATTACK, self.attack1_start_frame)

        if current_frame_add >= self.attack1_end_frame:

            # ends at this frame
            self.reset_action()
        else:
            hit_count = 0
            for em in self.enemies:
                hit_it = self.attacker.regular1(em, current_frame_add)
                if hit_it:
                    hit_count += 1
            if hit_count > 0:
                self.sound_box.play(random.choice(sfg.Sound.RENNE_ATTACK_HITS))

                # change combo count if this attack has hit some one
                attack_time = time()
                if self.attack_combo["count"] == 0 \
                    or attack_time - self.attack_combo["last_time"] <= self.attack_combo["time_delta"]:
                    self.attack_combo["count"] += 1
                else:
                    self.attack_combo["count"] = max(self.attack_combo["count"] - 1, 0)

                self.attack_combo["last_time"] = attack_time

        self.animation.run_sequence_frame(cfg.HeroAction.ATTACK, passed_seconds)


    def attack2(self, passed_seconds):
        self.frame_action = cfg.HeroAction.ATTACK
        current_frame_add = self.animation.get_current_frame_add(self.frame_action)
        if int(current_frame_add) == self.attack2_accumulate_power_frame \
            and self.attack2_accumulate_power_time > 0:
            self.attack2_accumulate_power_time -= passed_seconds
        else:
            is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
            if is_finish:
                self.reset_action()
                # clean combo count after an "attack2"
                self.attack_combo["count"] = 0
                self.attack2_accumulate_power_time = self.setting.ATTACKER_PARAMS["attack2"]["accumulate_power_time"]
            else:
                hit_count = 0
                for em in self.enemies:
                    hit_it = self.attacker.regular2(em, self.animation.get_current_frame_add(self.frame_action))
                    if hit_it:
                        hit_count += 1

                if hit_count > 0:
                    self.sound_box.play(random.choice(sfg.Sound.RENNE_ATTACK_HITS))


    def run_attack(self, passed_seconds):
        # a special attack type, when hero is running and press attack
        self.animation.run_sequence_frame(cfg.HeroAction.ATTACK, passed_seconds)
        if self.animation.get_current_frame_add(cfg.HeroAction.ATTACK) > self.run_attack_params["end_frame"]:
            # don't full-run the attack frame for better effect
            self.animation.reset_frame_adds()
            self.attacker.finish()
            self.action = cfg.HeroAction.STAND
        else:
            self.move(self.setting.RUN_SPEED * self.run_attack_params["run_speed_ratio"], passed_seconds)
            hit_count = 0
            for em in self.enemies:
                hit_it = self.attacker.run_attack(em, self.animation.get_current_frame_add(cfg.HeroAction.ATTACK))
                if hit_it:
                    hit_count += 1

            if hit_count > 0:
                self.sound_box.play(random.choice(sfg.Sound.RENNE_ATTACK_HITS))


    def win(self, passed_seconds):
        # win will dispel some bad status
        for status in cfg.SpriteStatus.BAD_STATUS_LIST:
            if self.status.get(status) is not None:
                self.status.pop(status)

        is_finish = self.animation._run_renne_win_frame(passed_seconds)
        if is_finish:
            self.attacker.finish()
            self.action = cfg.HeroAction.STAND
        else:
            self.attacker.dizzy(self.animation.get_current_frame_add(cfg.HeroAction.WIN))


    def locked(self):
        # check whether renne is locked, if so, and lock her without handling any event from user input
        if self.action in (cfg.HeroAction.ATTACK, cfg.HeroAction.RUN_ATTACK, 
            cfg.HeroAction.SKILL):
            # attacking, return directly
            return True

        if self.action == cfg.HeroAction.WIN:
            # painted egg, return directly
            return True

        if self.action == cfg.SpriteAction.UNCONTROLLED:
            return True

        if cfg.SpriteStatus.CRICK in self.status \
            or cfg.SpriteStatus.UNDER_THUMP in self.status:
            return True

        return False


    def event_handle(self, battle_keys, external_event=None):
        if external_event is not None:
            if external_event == cfg.GameStatus.INIT:
                self.action = cfg.HeroAction.STAND
                return
            elif external_event == cfg.GameStatus.HERO_LOSE:
                self.reset_action(force=False)
                return 
            elif external_event == cfg.GameStatus.ENTER_AMBUSH:
                self.reset_action(force=False)
                return 
            elif external_event == cfg.GameStatus.STORY:
                self.reset_action(force=False)
                return
            elif external_event == cfg.GameStatus.PAUSE:
                # do nothing
                return

        if self.locked():
            return

        # calculate direction
        self.key_vec.x = self.key_vec.y = 0.0
        if battle_keys[sfg.UserKey.LEFT]["pressed"]:
            self.key_vec.x -= 1.0
        if battle_keys[sfg.UserKey.RIGHT]["pressed"]:
            self.key_vec.x += 1.0
        if battle_keys[sfg.UserKey.UP]["pressed"]:
            self.key_vec.y -= 1.0
        if battle_keys[sfg.UserKey.DOWN]["pressed"]:
            self.key_vec.y += 1.0
        self.direction = cfg.Direction.VEC_TO_DIRECT.get(self.key_vec.as_tuple(), self.direction)

        if battle_keys[sfg.UserKey.ATTACK]["pressed"]:
            if self.action == cfg.HeroAction.RUN and self.sp > 0:
                self.attacker.method = "run_attack"
            else:
                if self.attack_combo["count"] < self.attack_combo["count_max"] \
                    or time() - self.attack_combo["last_time"] > self.attack_combo["time_delta"]:
                    self.attacker.method = "regular1"
                else:
                    self.attacker.method = "regular2"
                    atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS)
                    self.sound_box.play(atk_snd)

            self.action = cfg.HeroAction.ATTACK

        elif battle_keys[sfg.UserKey.MAGIC_SKILL_1]["pressed"]:
            if self.mp >= self.attacker.magic_skill_1_params["mana"] \
                and self.attacker.magic_cds["magic_skill_1"] == 0:
                atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS2)
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK
                self.attacker.method = "destroy_fire"

        elif battle_keys[sfg.UserKey.MAGIC_SKILL_2]["pressed"]:
            if self.mp >= self.attacker.magic_skill_2_params["mana"] \
                and self.attacker.magic_cds["magic_skill_2"] == 0:
                atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS2)
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.ATTACK
                self.attacker.method = "destroy_bomb"

        elif battle_keys[sfg.UserKey.MAGIC_SKILL_3]["pressed"]:
            if self.mp >= self.attacker.magic_skill_3_params["mana"] \
                and self.attacker.magic_cds["magic_skill_3"] == 0:
                atk_snd = random.choice(sfg.Sound.RENNE_ATTACKS2)
                self.sound_box.play(atk_snd)
                self.action = cfg.HeroAction.SKILL
                self.attacker.method = "destroy_aerolite"

        elif battle_keys[sfg.UserKey.MAGIC_SKILL_4]["pressed"]:
            if self.mp >= self.attacker.magic_skill_4_params["mana"] \
                and self.attacker.magic_cds["magic_skill_4"] == 0:
                self.action = cfg.HeroAction.WIN
                self.sound_box.play(sfg.Sound.RENNE_WIN)

        elif battle_keys[sfg.UserKey.REST]["pressed"]:
            self.action = cfg.HeroAction.REST

        elif self.key_vec:
            if self.action == cfg.HeroAction.RUN and self.sp > 0:
                # just keep running
                self.action = cfg.HeroAction.RUN
            elif self.direction in sfg.UserKey.DIRECT_TO_DIRECTION_KEY:
                direct_key = sfg.UserKey.DIRECT_TO_DIRECTION_KEY[self.direction]
                if direct_key == battle_keys["last_direct_key_up"]["key"] \
                    and time() - battle_keys["last_direct_key_up"]["time"] < sfg.UserKey.RUN_THRESHOLD \
                    and self.sp > 0:
                    self.action = cfg.HeroAction.RUN
                else:
                    self.action = cfg.HeroAction.WALK
            else:
                self.action = cfg.HeroAction.WALK

        else:
            self.action = cfg.HeroAction.STAND


    def under_thump(self, passed_seconds):
        self.move(self.status[cfg.SpriteStatus.UNDER_THUMP]["out_speed"], passed_seconds, 
            self.status[cfg.SpriteStatus.UNDER_THUMP]["key_vec"])
        self.animation.run_circle_frame(cfg.HeroAction.UNDER_THUMP, passed_seconds)


    def update(self, passed_seconds, external_event=None):
        if external_event is not None:
            if external_event == cfg.GameStatus.PAUSE:
                # user pause the game, don't update animation
                return

        self.update_status(passed_seconds)

        if self.action == cfg.HeroAction.ATTACK:
            if self.attacker.method == "run_attack":
                self.run_attack(passed_seconds)
            else:
                self.attack(passed_seconds)

        elif self.action == cfg.HeroAction.SKILL:
            self.attack(passed_seconds)

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

        elif self.action == cfg.HeroAction.UNDER_THUMP:
            self.under_thump(passed_seconds)


        self.animation.update(passed_seconds)
        self.emotion_animation.update(passed_seconds)

        # update magic cd
        for magic_name in self.attacker.magic_cds:
            self.attacker.magic_cds[magic_name] = max(0, 
                self.attacker.magic_cds[magic_name] - passed_seconds)



class Enemy(GameSprite):
    def __init__(self, setting, pos, direction):
        super(Enemy, self).__init__(setting.NAME, setting.HP, setting.ATK, setting.DFS, pos, direction)
        self.setting = setting
        self.emotion_animation = SpriteEmotionAnimator(self)

        self.animation = EnemyAnimator(self)

        self.area = pygame.Rect(0, 0, self.setting.RADIUS * 2, self.setting.RADIUS * 2)
        self.area.center = self.pos('xy')
        self.check_reachable = False


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
        if self.status["hp"] == cfg.HpStatus.DIE:
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


    def reachable(self, pos=None):
        if self.is_collide_map_boundry():
            return False

        p = pos or self.pos
        bps = self.game_map.block_points
        step = sfg.BlockPoint.STEP_WIDTH
        x0 = p.x - p.x % step
        y0 = p.y - p.y % step
        for p in ((x0, y0), (x0 + step, y0), (x0, y0 + step), (x0 + step, y0 + step)):
            if p in bps:
                return False
        return True


    def reachable_old(self, pos=None):
        # use waypoints to check whether the current self.pos is reachable
        p = pos or self.pos
        wps = self.brain.waypoints
        step = sfg.WayPoint.STEP_WIDTH
        x0 = p.x - p.x % step
        y0 = p.y - p.y % step
        for p2 in ((x0, y0), (x0 + step, y0), (x0, y0 + step), (x0 + step, y0 + step)):
            if p2 not in wps:
                return False
        return True


    def stand(self, passed_seconds):
        self.animation.run_circle_frame(cfg.EnemyAction.STAND, passed_seconds)


    def walk(self, passed_seconds, check_reachable=False):
        self.move(self.setting.WALK_SPEED, passed_seconds, check_reachable)
        self.animation.run_circle_frame(cfg.EnemyAction.WALK, passed_seconds)


    def backward(self, passed_seconds):
        self.move(self.setting.WALK_SPEED * 0.5, passed_seconds, check_reachable=True)
        self.animation.run_circle_frame_backward(cfg.EnemyAction.WALK, passed_seconds)


    def attack(self, passed_seconds):
        hit = False
        finish = self.animation.run_sequence_frame(cfg.EnemyAction.ATTACK, passed_seconds)
        if finish:
            self.reset_action(force=True)
        else:
            hit = self.attacker.run(self.brain.target, 
                self.animation.get_current_frame_add(cfg.EnemyAction.ATTACK))
            if hit:
                self.sound_box.play(random.choice(sfg.Sound.ENEMY_ATTACK_HITS))

        return finish, hit


    def under_thump(self, passed_seconds):
        self.move(self.status[cfg.SpriteStatus.UNDER_THUMP]["out_speed"], passed_seconds,
            check_reachable=True, key_vec=self.status[cfg.SpriteStatus.UNDER_THUMP]["key_vec"])
        self.animation.run_circle_frame(cfg.EnemyAction.UNDER_THUMP, passed_seconds) 


    def reset_action(self, force=True):
        if force:
            # reset all related things for enemy by force!
            self.brain.persistent = False
            self.brain.interrupt = False
            self.attacker.finish()
            self.action = cfg.EnemyAction.STAND
            self.animation.reset_frame_adds()
            self.frame_action = None
            if self.status.get(cfg.SpriteStatus.BODY_SHAKE) is not None:
                self.status.pop(cfg.SpriteStatus.BODY_SHAKE)
        else:
            if not self.brain.persistent:
                self.action = cfg.EnemyAction.STAND


    def cal_angry(self, damage):
        # calculate enemy's emotion
        angry_hp_threshold = self.setting.HP * self.brain.ai.ANGRY_HP_RATIO
        if self.hp < angry_hp_threshold and self.hp + damage >= angry_hp_threshold \
            and happen(self.brain.ai.EMOTION_ANGRY_PROB):
            self.set_emotion(cfg.SpriteEmotion.ANGRY)


    def set_target(self, target):
        if self.brain.target is None:
            self.brain.set_target(target)


    def event_handle(self, external_event=None):
        # perception and belief control level
        if external_event is not None and external_event != cfg.GameStatus.IN_PROGRESS:
            if external_event == cfg.GameStatus.INIT:
                self.action = cfg.EnemyAction.STAND
                return
            elif external_event == cfg.GameStatus.HERO_LOSE:
                self.reset_action(force=False)
                return
            elif external_event == cfg.GameStatus.ENTER_AMBUSH:
                self.reset_action(force=False)
                return
            elif external_event == cfg.GameStatus.STORY:
                self.reset_action(force=False)
                return
            elif external_event == cfg.GameStatus.PAUSE:
                # do nothing
                return

        if self.status["hp"] == cfg.HpStatus.DIE:
            return

        if self.status.get(cfg.SpriteStatus.STUN) is not None \
            or self.status.get(cfg.SpriteStatus.DIZZY) is not None:
            self.reset_action(force=True)
            return

        if self.action == cfg.EnemyAction.UNDER_THUMP:
            return

        self.brain.think()
        for action in self.brain.actions:

            if action == cfg.EnemyAction.ATTACK:
                self.action = cfg.EnemyAction.ATTACK
            
            elif action == cfg.EnemyAction.STEER:
                self.action = cfg.EnemyAction.WALK
                self.check_reachable = False
                self.allsprites.notify_nearby_alliance_for_target(self, self.brain.target)

            elif action == cfg.EnemyAction.LOOKOUT:
                # tell its brain the current target found(or None if no target in view scope)
                target = self.brain.target or self.view_sensor.detect(self.hero)
                self.brain.set_target(target)

            elif action == cfg.EnemyAction.STAND:
                self.action = cfg.EnemyAction.STAND

            elif action == cfg.EnemyAction.WALK:
                self.action = cfg.EnemyAction.WALK
                self.check_reachable = True
                self.key_vec.x, self.key_vec.y = cfg.Direction.DIRECT_TO_VEC[self.direction] 

            elif action == cfg.EnemyAction.BACKWARD:
                self.action = cfg.EnemyAction.BACKWARD
                self.key_vec.x, self.key_vec.y = cfg.Direction.DIRECT_TO_VEC[
                    (self.direction + 4) % cfg.Direction.TOTAL]


    def update_status(self, passed_seconds):
        super(Enemy, self).update_status(passed_seconds)

        if self.status.get(cfg.SpriteStatus.AMBUSH) is not None:
            if self.status[cfg.SpriteStatus.AMBUSH]["status"] == cfg.Ambush.STATUS_INIT:
                self.status[cfg.SpriteStatus.AMBUSH]["init_delay"] -= passed_seconds
                if self.status[cfg.SpriteStatus.AMBUSH]["init_delay"] < 0:
                    # delay time is over, turn to *STATUS_ENTER*
                    self.status[cfg.SpriteStatus.AMBUSH]["status"] = cfg.Ambush.STATUS_ENTER
            elif self.status[cfg.SpriteStatus.AMBUSH]["status"] == cfg.Ambush.STATUS_ENTER:
                v0 = self.status[cfg.SpriteStatus.AMBUSH]["speed"]
                a = self.status[cfg.SpriteStatus.AMBUSH]["acceleration"]
                s =  v0 * passed_seconds + 0.5 * a * pow(passed_seconds, 2)
                self.status[cfg.SpriteStatus.AMBUSH]["height"] = max(0, 
                    self.status[cfg.SpriteStatus.AMBUSH]["height"] - s)
                if self.status[cfg.SpriteStatus.AMBUSH]["height"] == 0:
                    self.status[cfg.SpriteStatus.AMBUSH]["status"] = cfg.Ambush.STATUS_FINISH
                    self.action = cfg.EnemyAction.STAND
                else:
                    self.action = cfg.EnemyAction.UNCONTROLLED
                    self.status[cfg.SpriteStatus.AMBUSH]["speed"] = v0 + a * passed_seconds
                 

    def update(self, passed_seconds, external_event=None):
        # physics level
        if external_event is not None:
            if external_event == cfg.GameStatus.PAUSE:
                # user pause the game, don't update animation
                return

        self.update_status(passed_seconds)

        if self.status["hp"] != cfg.HpStatus.DIE \
            and self.status.get(cfg.SpriteStatus.STUN) is None \
            and self.status.get(cfg.SpriteStatus.DIZZY) is None:

            if self.action == cfg.EnemyAction.ATTACK:
                self.attack(passed_seconds)

            elif self.action == cfg.EnemyAction.STAND:
                self.stand(passed_seconds)

            elif self.action == cfg.EnemyAction.WALK:
                self.walk(passed_seconds, self.check_reachable)

            elif self.action == cfg.EnemyAction.UNDER_THUMP:
                self.under_thump(passed_seconds)

            elif self.action == cfg.EnemyAction.BACKWARD:
                self.frame_action = cfg.EnemyAction.WALK
                self.backward(passed_seconds)

        self.animation.update(passed_seconds)
        self.emotion_animation.update(passed_seconds)



class Leonhardt(Enemy):
    def __init__(self, setting, pos, direction):
        super(Leonhardt, self).__init__(setting, pos, direction)
        self.mp = self.setting.MP


    def stand(self, passed_seconds):
        super(Leonhardt, self).stand(passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)


    def walk(self, passed_seconds, check_reachable):
        super(Leonhardt, self).walk(passed_seconds)
        self.mp = min(self.setting.MP, self.mp + self.setting.MP_RECOVERY_RATE * passed_seconds)


    def regular(self, passed_seconds):
        if self.frame_action is None or self.frame_action == cfg.EnemyAction.STAND:
            self.sound_box.play(sfg.Sound.LEONHARDT_ATTACKS[0])
            self.frame_action = random.choice(
                (cfg.LeonHardtAction.ATTACK, cfg.LeonHardtAction.ATTACK2))

        is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
        if is_finish:
            self.reset_action(force=True)
        else:
            hit_it = self.attacker.run(self.brain.target, 
                self.animation.get_current_frame_add(self.frame_action))
            if hit_it:
                self.sound_box.play(random.choice(sfg.Sound.ENEMY_ATTACK_HITS))


    def death_coil(self, passed_seconds):
        if self.frame_action is None or self.frame_action == cfg.EnemyAction.STAND:
            self.sound_box.play(sfg.Sound.LEONHARDT_ATTACKS[1])
            self.frame_action = cfg.LeonHardtAction.SKILL1

        is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
        if is_finish:
            self.reset_action(force=True)
        else:
            self.attacker.death_coil(self.brain.target, 
                self.animation.get_current_frame_add(self.frame_action))


    def hell_claw(self, passed_seconds):
        if self.frame_action is None or self.frame_action == cfg.EnemyAction.STAND:
            self.sound_box.play(sfg.Sound.LEONHARDT_ATTACKS[2])
            self.frame_action = cfg.LeonHardtAction.SKILL2

        ak = self.attacker
        if ak.hell_claw_last_freeze_time_add == 0:
            is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
            if is_finish:
                ak.hell_claw_last_freeze_time_add += passed_seconds
                self.animation.set_frame_add(self.frame_action, 
                    self.animation.get_frame_num(self.frame_action) - 1)
            else:
                ak.hell_claw(self.brain.target, 
                    self.animation.get_current_frame_add(self.frame_action))

        elif ak.hell_claw_last_freeze_time_add < ak.hell_claw_params["last_freeze_time"]:
            ak.hell_claw_last_freeze_time_add += passed_seconds
            self.animation.set_frame_add(self.frame_action, 
                self.animation.get_frame_num(self.frame_action) - 1)

        else:
            self.reset_action(force=True)


    def death_domain(self, passed_seconds):
        if self.frame_action is None or self.frame_action == cfg.EnemyAction.STAND:
            self.sound_box.play(sfg.Sound.LEONHARDT_ATTACKS[3])
            self.frame_action = cfg.LeonHardtAction.SKILL2

        ak = self.attacker
        if ak.death_domain_pre_run_time_add == 0:
            is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
            if is_finish:
                ak.death_domain_pre_run_time_add += passed_seconds
                self.animation.set_frame_add(self.frame_action,
                    self.animation.get_frame_num(self.frame_action) - 1)
                # timing! fire the skill!
                ak.death_domain(self.brain.target, self.animation.get_current_frame_add(self.frame_action))

        elif ak.death_domain_pre_run_time_add < ak.death_domain_params["pre_run_time"]: 
            self.animation.set_frame_add(self.frame_action,
                self.animation.get_frame_num(self.frame_action) - 1)
            ak.death_domain_pre_run_time_add += passed_seconds

            # set super body in pre_run_time
            if cfg.SpriteStatus.SUPER_BODY not in self.status:
                self.status[cfg.SpriteStatus.SUPER_BODY] = True

        elif ak.death_domain_run_time_add < ak.death_domain_params["run_time"]:
            ak.death_domain_run_time_add += passed_seconds 
            ak.direction_add = (ak.direction_add + ak.death_domain_params["rotate_rate"] * passed_seconds) % cfg.Direction.TOTAL
            self.direction = int(ak.direction_add)

        elif ak.death_domain_post_run_time_add < ak.death_domain_params["post_run_time"]:
            ak.death_domain_post_run_time_add += passed_seconds
            if self.brain.target.status.get(cfg.SpriteStatus.UNDER_PULL) is not None:
                # clean pull status 
                self.brain.target.status.pop(cfg.SpriteStatus.UNDER_PULL)

            # clean super body in post_run_time
            if cfg.SpriteStatus.SUPER_BODY in self.status:
                self.status.pop(cfg.SpriteStatus.SUPER_BODY)

        else:
            self.reset_action(force=True)


    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            self.regular(passed_seconds)
        elif self.attacker.method == "death_coil":
            self.death_coil(passed_seconds)
        elif self.attacker.method == "hell_claw":
            self.hell_claw(passed_seconds)
        elif self.attacker.method == "death_domain":
            self.death_domain(passed_seconds)



class CastleWarrior(Enemy):
    def __init__(self, setting, pos, direction):
        super(CastleWarrior, self).__init__(setting, pos, direction)


    def thump(self, passed_seconds):
        if self.attacker.thump_pre_freeze_time_add == 0:
            self.animation.run_sequence_frame(cfg.EnemyAction.ATTACK, passed_seconds, 
                self.attacker.thump_pre_rate)
            if self.animation.get_current_frame_add(cfg.EnemyAction.ATTACK) \
                > self.attacker.thump_pre_frames[-1]:
                # pre -> pre_freeze
                self.animation.set_frame_add(cfg.EnemyAction, self.attacker.thump_pre_frames[-1]) 
                self.attacker.thump_pre_freeze_time_add += passed_seconds

        elif self.attacker.thump_pre_freeze_time_add < self.attacker.thump_pre_freeze_time:
            self.animation.set_frame_add(cfg.EnemyAction.ATTACK, 
                self.attacker.thump_pre_frames[-1]) 
            self.attacker.thump_pre_freeze_time_add += passed_seconds
                
        elif self.attacker.thump_slide_time_add < self.attacker.thump_slide_time:
            self.attacker.thump_slide_time_add += passed_seconds
            self.animation.set_frame_add(cfg.EnemyAction.ATTACK, self.attacker.thump_frame)
            self.move(self.attacker.thump_slide_speed, passed_seconds, 
                check_reachable=True, key_vec=self.attacker.key_vec)
            hit_it = self.attacker.run(self.brain.target, self.attacker.thump_frame)
            if hit_it:
                self.sound_box.play(random.choice(sfg.Sound.ENEMY_ATTACK_HITS))
                words = sfg.Effect.THUMP_WORD_FONT.render(sfg.Effect.THUMP_WORD, True, 
                    sfg.Effect.THUMP_WORD_COLOR)
                self.animation.show_words(words, sfg.Effect.THUMP_WORD_SHOW_TIME, 
                    (self.pos.x - words.get_width() * 0.5, 
                    self.pos.y * 0.5 - self.setting.HEIGHT - sfg.Effect.THUMP_WORD_DY))

        elif self.attacker.thump_last_freeze_time_add < self.attacker.thump_last_freeze_time:
            # freeze for a short time
            self.attacker.thump_last_freeze_time_add += passed_seconds

        else:
            self.reset_action(force=True)


    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            super(CastleWarrior, self).attack(passed_seconds)
        elif self.attacker.method == "thump":
            self.thump(passed_seconds)



class TwoHeadSkeleton(Enemy):
    def __init__(self, setting, pos, direction):
        super(TwoHeadSkeleton, self).__init__(setting, pos, direction)


    def fall(self, passed_seconds):
        ak = self.attacker
        if ak.fall_run_up_time_add < ak.fall_run_up_time:
            ak.fall_run_up_time_add += passed_seconds
            self.frame_action = cfg.EnemyAction.WALK
            self.animation.run_circle_frame(cfg.EnemyAction.WALK, passed_seconds, ak.fall_run_up_rate)

        elif ak.fall_kneel_time_add < ak.fall_kneel_time:
            self.frame_action = cfg.EnemyAction.KNEEL
            self.animation.run_circle_frame(cfg.EnemyAction.KNEEL, passed_seconds)
            ak.fall_kneel_time_add += passed_seconds
            if ak.fall_kneel_time_add >= ak.fall_kneel_time:
                # a timing for setting vector and speed for x axis
                ak.fall_in_air_v_x = Vector2.from_points(self.pos, self.brain.target.pos)
                ak.fall_in_air_v_x *= 0.9
                ak.fall_in_air_speed_x = ak.fall_in_air_v_x.get_length() / ak.fall_in_air_time
                self.status[cfg.SpriteStatus.IN_AIR] = {"height": 0}

        elif ak.fall_in_air_time_add < ak.fall_in_air_time:
            ak.fall_in_air_time_add += passed_seconds

            self.frame_action = cfg.EnemyAction.STAND
            self.animation.set_frame_add(cfg.EnemyAction.STAND, 0)

            ak.fall_in_air_height = ak.fall_v0_y * ak.fall_in_air_time_add \
                + 0.5 * ak.fall_acceleration * pow(ak.fall_in_air_time_add, 2)
            self.status[cfg.SpriteStatus.IN_AIR]["height"] = ak.fall_in_air_height

            self.move(ak.fall_in_air_speed_x, passed_seconds, check_reachable=False, 
                key_vec=ak.fall_in_air_v_x)

            if ak.fall_in_air_time_add >= ak.fall_in_air_time:
                # timing for attack calculation
                hit_it = ak.run(self.brain.target, None)
                if hit_it:
                    self.sound_box.play(random.choice(sfg.Sound.ENEMY_ATTACK_HITS))

                # fall back in air
                ak.fall_in_air_v_x.x = - ak.fall_in_air_v_x.x
                ak.fall_in_air_v_x.y = - ak.fall_in_air_v_x.y
                ak.fall_in_air_speed_x *= 0.25

        elif ak.fall_back_in_air_time_add < ak.fall_back_in_air_time:
            ak.fall_back_in_air_time_add += passed_seconds

            self.frame_action = cfg.EnemyAction.WALK
            self.animation.run_sequence_frame(cfg.EnemyAction.WALK, passed_seconds, ak.fall_run_up_rate)

            ak.fall_in_air_height = ak.fall_back_v0_y * ak.fall_back_in_air_time_add \
                + 0.5 * ak.fall_acceleration * pow(ak.fall_back_in_air_time_add, 2)
            self.status[cfg.SpriteStatus.IN_AIR]["height"] = ak.fall_in_air_height

            self.move(ak.fall_in_air_speed_x, passed_seconds, check_reachable=True, 
                key_vec=ak.fall_in_air_v_x)

        else:
            self.status.pop(cfg.SpriteStatus.IN_AIR)
            self.reset_action(force=True)


    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            super(TwoHeadSkeleton, self).attack(passed_seconds)
        elif self.attacker.method == "fall":
            self.fall(passed_seconds)



class Robot(Enemy):
    def __init__(self, setting, pos, direction):
        super(Robot, self).__init__(setting, pos, direction)


    def attack(self, passed_seconds):
        ak = self.attacker
        if ak.bomb_run_up_time_add < ak.bomb_run_up_time:
            ak.bomb_run_up_time_add += passed_seconds
            self.animation.run_circle_frame(cfg.EnemyAction.ATTACK, passed_seconds)
        else:
            if ak.bomb_begin:
                self.frame_action = cfg.EnemyAction.KNEEL
            else:
                self.animation.run_circle_frame(cfg.EnemyAction.ATTACK, passed_seconds)
                if ak.final_bomb_time is None:
                    distance_to_target = self.pos.get_distance_to(self.brain.target.pos)
                    if distance_to_target <= ak.bomb_lock_distance:
                        # root formula 
                        # 0.5 * a * t^2 + v0 * t - s = 0
                        # we want to get "t", then use this formula:
                        # -b +- sqrt(b^2 - 4ac) / 2a 
                        # here "a" is "0.5 * a", "b" is "v0", "c" is "-s", we discard the negative root,
                        # only use the positive root
                        v0 = ak.speed
                        a = ak.bomb_acceleration
                        s = distance_to_target
                        t = (math.sqrt(pow(v0, 2) + 2 * a * s) - v0) / a
                        ak.final_bomb_time = t
                    else:
                        # if not reaching the lock distance, calculate key_vec every time
                        ak.key_vec = Vector2.from_points(self.pos, self.brain.target.pos)

                else:
                    ak.final_bomb_time -= passed_seconds
                    if ak.final_bomb_time <= 0:
                        ak.set_self_destruction(self.brain.target)

                self.move(ak.speed, passed_seconds, check_reachable=True, key_vec=ak.key_vec)
                if self.brain.interrupt:
                    # collide some blocks when move! self destruction at once
                    ak.set_self_destruction(self.brain.target)
                else:
                    ak.speed += ak.bomb_acceleration * passed_seconds



class GanDie(Enemy):
    def __init__(self, setting, pos, direction):
        super(GanDie, self).__init__(setting, pos, direction)


    def spit_poison(self, passed_seconds):
        ak = self.attacker
        if ak.spit_poison_ready_time_add == 0:
            # first time into spit poison, add body shake status
            ak.spit_poison_ready_time_add += passed_seconds
            self.status[cfg.SpriteStatus.BODY_SHAKE] = {"dx": random.randint(-5, 5), 
                "dy": random.randint(-3, 3), "time": 999}

        elif ak.spit_poison_ready_time_add < ak.spit_poison_ready_time:
            ak.spit_poison_ready_time_add += passed_seconds
            self.frame_action = cfg.EnemyAction.UNDER_THUMP
            if ak.spit_poison_ready_time_add >= ak.spit_poison_ready_time:
                self.status.pop(cfg.SpriteStatus.BODY_SHAKE)

        elif ak.spit_poison_hold_time_add < ak.spit_poison_hold_time:
            ak.spit_poison_hold_time_add += passed_seconds
            self.frame_action = cfg.EnemyAction.STAND
            ak.spit_poison(self.brain.target)

        else:
            self.reset_action(force=True)

    
    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            finish, hit = super(GanDie, self).attack(passed_seconds)
            if hit and self.attacker.poison_happen:
                words = sfg.Effect.POISON_WORD_FONT.render(sfg.Effect.POISON_WORD, True, 
                    sfg.Effect.POISON_WORD_COLOR)
                self.animation.show_words(words, sfg.Effect.POISON_WORD_SHOW_TIME,
                    (self.pos.x - words.get_width() * 0.5, 
                    self.pos.y * 0.5 - self.setting.HEIGHT - sfg.Effect.POISON_WORD_DY))
        elif self.attacker.method == "spit_poison":
            self.spit_poison(passed_seconds)



class ArmouredShooter(Enemy):
    def __init__(self, setting, pos, direction):
        super(ArmouredShooter, self).__init__(setting, pos, direction)


    def grenade(self, passed_seconds):
        self.frame_action = cfg.EnemyAction.SKILL
        is_finish = self.animation.run_sequence_frame(self.frame_action, passed_seconds)
        if is_finish:
            self.reset_action(force=True)
        else:
            self.attacker.grenade(self.brain.target, 
                self.animation.get_current_frame_add(self.frame_action))

            
    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            super(ArmouredShooter, self).attack(passed_seconds)
        elif self.attacker.method == "grenade":
            self.grenade(passed_seconds)



class Ghost(Enemy):
    def __init__(self, setting, pos, direction):
        super(Ghost, self).__init__(setting, pos, direction)


    def invisible(self, passed_seconds):
        ak = self.attacker
        if ak.pre_enter_invisible_time_add < ak.pre_enter_invisible_time:
            ak.pre_enter_invisible_time_add += passed_seconds
            self.frame_action = cfg.EnemyAction.STAND
            key_vec = Vector2.from_points(self.pos, self.brain.target.pos)
            self.move(self.setting.WALK_SPEED * 0.8, passed_seconds, check_reachable=True, key_vec=key_vec)
        else:
            self.status[cfg.SpriteStatus.INVISIBLE] = {"time": ak.invisible_time}
            self.reset_action(force=True)


    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            finish, hit = super(Ghost, self).attack(passed_seconds)
            if hit and self.attacker.leak_happen:
                words = sfg.Effect.MP_BURN_WORD_FONT.render(sfg.Effect.MP_BURN_WORD, True, 
                    sfg.Effect.MP_BURN_WORD_COLOR)
                self.animation.show_words(words, sfg.Effect.MP_BURN_WORD_SHOW_TIME, 
                    (self.pos.x - words.get_width() * 0.5, 
                    self.pos.y * 0.5 - self.setting.HEIGHT - sfg.Effect.MP_BURN_WORD_DY))
            if self.status.get(cfg.SpriteStatus.INVISIBLE) is not None:
                # when ghost attack, it will be visible
                self.status.pop(cfg.SpriteStatus.INVISIBLE)

        elif self.attacker.method == "invisible":
            self.invisible(passed_seconds)
        


class Werwolf(Enemy):
    def __init__(self, setting, pos, direction):
        super(Werwolf, self).__init__(setting, pos, direction)


    def catch(self, passed_seconds):
        ak = self.attacker
        target = self.brain.target
        if ak.ready_time_add < ak.ready_time:
            ak.ready_time_add += passed_seconds
            self.frame_action = cfg.EnemyAction.UNDER_THUMP
            self.animation.run_circle_frame(cfg.EnemyAction.UNDER_THUMP, passed_seconds) 

        elif ak.hold_time_a_add < ak.hold_time_a:
            if ak.catch_hit(target):
                self.frame_action = cfg.EnemyAction.ATTACK
                self.animation.set_frame_add(cfg.EnemyAction.ATTACK, ak.key_frame_a)
                target.action = cfg.SpriteAction.UNCONTROLLED
                target.frame_action = cfg.SpriteAction.UNDER_THUMP
                target.direction = (self.direction + 4) % cfg.Direction.TOTAL
                ak.catch_run_a(target)
                ak.speed = 0

            if ak.speed == 0:
                if len(ak.has_hits) == 0:
                    # no one hit, reset action
                    self.reset_action(force=True)
                else:
                    ak.hold_time_a_add += passed_seconds
                    if ak.hold_time_a_add >= ak.hold_time_a:
                        # give a thump!
                        ak.catch_run_b(target)
                        target.direction = (target.direction + 4) % cfg.Direction.TOTAL
            else:
                if ak.speed < ak.run_speed \
                    or self.pos.get_distance_to(ak.target_pos) < ak.attack_range:
                    # change a pose and speed down
                    self.frame_action = cfg.EnemyAction.ATTACK
                    self.animation.set_frame_add(cfg.EnemyAction.ATTACK, ak.key_frame_a)
                    ak.speed = max(ak.speed + ak.friction * passed_seconds, 0)
                    if ak.speed > 0:
                        self.move(ak.speed, passed_seconds, check_reachable=True, key_vec=ak.key_vec)
                else:
                    self.frame_action = cfg.EnemyAction.WALK
                    self.animation.run_circle_frame(cfg.EnemyAction.WALK, passed_seconds, ak.run_frame_rate)
                    self.move(ak.speed, passed_seconds, check_reachable=False, key_vec=ak.key_vec)
                    if self.brain.interrupt:
                        self.reset_action(force=True)

        elif ak.hold_time_b_add < ak.hold_time_b:
            ak.hold_time_b_add += passed_seconds
            self.frame_action = cfg.EnemyAction.ATTACK
            self.animation.set_frame_add(cfg.EnemyAction.ATTACK, ak.key_frame_b)

        else:
            self.reset_action(force=True)


    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            super(Werwolf, self).attack(passed_seconds)
        elif self.attacker.method == "catch":
            self.catch(passed_seconds)



class SwordRobber(Enemy):
    def __init__(self, setting, pos, direction):
        super(SwordRobber, self).__init__(setting, pos, direction)


    def whirlwind(self, passed_seconds):
        ak = self.attacker
        target = self.brain.target
        if ak.pre_time_add == 0:
            ak.pre_time_add += passed_seconds
            words = sfg.Effect.WHIRLWIND_WORD_FONT.render(sfg.Effect.WHIRLWIND_WORD, True,
                sfg.Effect.WHIRLWIND_WORD_COLOR)
            self.animation.show_words(words, sfg.Effect.WHIRLWIND_WORD_SHOW_TIME,
                (self.pos.x - words.get_width() * 0.5, 
                self.pos.y * 0.5 - self.setting.HEIGHT - sfg.Effect.WHIRLWIND_WORD_DY))
        elif ak.pre_time_add < ak.pre_time:
            ak.pre_time_add += passed_seconds
            self.animation.set_frame_add(cfg.EnemyAction.ATTACK, ak.pre_frame)

        elif ak.rotate_time_add < ak.rotate_time:
            ak.rotate_time_add += passed_seconds
            self.frame_action = cfg.EnemyAction.UNDER_THUMP
            ak.direction_add = (ak.direction_add + ak.rotate_rate * passed_seconds) % cfg.Direction.TOTAL
            self.direction = int(ak.direction_add)
            self.move(ak.move_speed, passed_seconds, check_reachable=False, key_vec=ak.key_vec)
            if self.pos.get_distance_to(ak.target_pos) < ak.reach_delta:
                ak.rotate_time_add = ak.rotate_time

            ak.offset_time_add += passed_seconds
            if ak.offset_time_add > ak.offset_time:
                # modify offset_vec, turn a direction
                ak.offset_time_add = 0
                ak.offset_vec = -ak.offset_vec
                v = Vector2.from_points(self.pos, ak.target_pos)
                ak.key_vec = (v + v * ak.offset_vec).normalize()
            if self.brain.interrupt:
                self.reset_action(force=True)
            ak.whirlwind_run(target)
        else:
            self.reset_action(force=True)
            if happen(ak.self_stun_prob):
                ak.handle_additional_status(cfg.SpriteStatus.STUN, {"time": ak.self_stun_time})
                self.set_emotion(cfg.SpriteEmotion.STUN)

    
    def attack(self, passed_seconds):
        if self.attacker.method == "regular":
            super(SwordRobber, self).attack(passed_seconds)
        elif self.attacker.method == "whirlwind":
            self.whirlwind(passed_seconds)


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

            other.brain.set_target(target)



class Ambush(pygame.sprite.LayeredDirty):
    # containing a group of "pending" enemies, that will appear when hero enter some area it belongs to
    def __init__(self, pos, surround_area_width, enter_area_width, appear_type):
        super(Ambush, self).__init__()
        self.pos = pos
        self.surround_area = pygame.Rect((0, 0, surround_area_width, surround_area_width))
        self.enter_area = pygame.Rect((0,  0, enter_area_width, enter_area_width))
        self.appear_type = appear_type
        self.delay_time = 0
        self.status = cfg.Ambush.STATUS_INIT
        self.adjust_model()


    def adjust_model(self):
        self.surround_area.center = self.pos
        self.enter_area.center = self.pos


    def init_sprite_status(self):
        for sp in self.sprites():
            if self.appear_type == cfg.Ambush.APPEAR_TYPE_TOP_DOWN:
                sp.status[cfg.SpriteStatus.AMBUSH] = {"type": self.appear_type, 
                    "height": random.randint(*sfg.Ambush.APPEAR_TYPE_TOP_DOWN_HEIGHT_RAND_RANGE),
                    "speed": 0,
                    "acceleration": sfg.Physics.GRAVITY_ACCELERATION,
                    "init_delay": random.uniform(*sfg.Ambush.APPEAR_TYPE_TOP_DOWN_INIT_DELAY_RAND_RANGE),
                    "status": cfg.Ambush.STATUS_INIT}


    def enter(self, hero):
        if self.status == cfg.Ambush.STATUS_INIT and hero.area.colliderect(self.enter_area):
            self.status = cfg.Ambush.STATUS_ENTER
            return True
        return False


    def update(self, passed_seconds):
        finish_num = 0
        for sp in self.sprites():
            if sp.status[cfg.SpriteStatus.AMBUSH]["status"] == cfg.Ambush.STATUS_FINISH:
                finish_num += 1

        if finish_num == len(self.sprites()):
            if self.delay_time < sfg.Ambush.APPEAR_TYPE_TOP_DOWN_FINISH_DELAY:
                self.delay_time += passed_seconds
            else:
                self.status = cfg.Ambush.STATUS_FINISH


    def draw(self, camera):
        # ambush usually is invisible, here this function is only for map_editor
        for area in (self.surround_area, self.enter_area):
            r = pygame.Rect(0, 0, area.width, area.height * 0.5)
            r.center = (self.pos[0], self.pos[1] * 0.5)
            r.x -= camera.rect.x
            r.y -= camera.rect.y
            pygame.draw.rect(camera.screen, pygame.Color("red"), r, 1)

        render_str = "Ambush '%s' with %s sprites" \
            % (cfg.Ambush.APPEAR_TYPES[self.appear_type], len(self.sprites()))
        name = sfg.Font.ARIAL_16.render(render_str, True, pygame.Color("red"))
        camera.screen.blit(name, 
            (self.surround_area.x - camera.rect.x, self.surround_area.y * 0.5 - camera.rect.y))



ENEMY_CLASS_MAPPING = {
    sfg.SkeletonWarrior.ID: Enemy,
    sfg.CastleWarrior.ID: CastleWarrior,
    sfg.SkeletonArcher.ID: Enemy,
    sfg.LeonHardt.ID: Leonhardt,
    sfg.ArmouredShooter.ID: ArmouredShooter,
    sfg.SwordRobber.ID: SwordRobber,
    sfg.GanDie.ID: GanDie,
    sfg.Ghost.ID: Ghost,
    sfg.TwoHeadSkeleton.ID: TwoHeadSkeleton,
    sfg.Werwolf.ID: Werwolf,
    sfg.SilverTentacle.ID: Enemy,
    sfg.Robot.ID: Robot,
}
