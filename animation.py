import pygame
from pygame.locals import BLEND_ADD
from time import time
from random import randint, gauss
from gameobjects.vector2 import Vector2
from base.util import ImageController, SpriteImageController, Timer, Blink
from base import constant as cfg
from etc import setting as sfg


# init SpriteImageController and related frame_nums, frame_rates
sprite_image_contollers = {}
sprite_frame_files = {}
sprite_frame_nums = {}
sprite_frame_rates = {}
for sprite_id, (image_folder, res_mapping) in sfg.SPRITE_FRAMES.iteritems():
    sprite_image_contollers[sprite_id] = SpriteImageController(image_folder)
    sprite_frame_files[sprite_id] = {}
    sprite_frame_nums[sprite_id] = {}
    sprite_frame_rates[sprite_id] = {}
    for action, (image_name, frame_num, frame_rate) in res_mapping.iteritems():
        sprite_frame_files[sprite_id][action] = image_name
        sprite_frame_nums[sprite_id][action] = frame_num
        sprite_frame_rates[sprite_id][action] = frame_rate

battle_images = ImageController(sfg.BATTLE_IMAGES[0])
battle_images.add_from_list(sfg.BATTLE_IMAGES[1])

basic_image_controller = ImageController(sfg.BASIC_IMAGES[0])
basic_image_controller.add_from_list(sfg.BASIC_IMAGES[1])

cg_image_controller = ImageController(sfg.CG_IMAGES[0])
cg_image_controller.add_from_list(sfg.CG_IMAGES[1])

effect_image_controller = ImageController(sfg.EFFECT[0])
effect_image_controller.add_from_list(sfg.EFFECT[1])

shadow_images = basic_image_controller.get(sfg.Sprite.SHADOW_IMAGE_KEY).convert_alpha()



def get_shadow_image(shadow_index):
    return shadow_images.subsurface(
        pygame.Rect((64 * (shadow_index % 4), 128 * (shadow_index / 4)), (64, 128)))


class WordsRenderer(object):
    def __init__(self):
        self.blit_list = []


    def add_blit_words(self, words, rel_pos, time_len, pos_move_rate=None, make_blink=False):
        w = {"words": words, "rel_pos": rel_pos, 
            "timer": Timer(time_len), "pos_move_rate": pos_move_rate}
        if make_blink:
            w["words_mix"] = None
            w["blink"] = Blink(sfg.Effect.BLINK_RATE3, sfg.Effect.BLINK_DEPTH_SECTION3)
        self.blit_list.append(w)


    def add_follow_sprite_words(self, words, pos, time_len, z, vec_z, follow_sprite):
        w = {"words": words, "pos": Vector2(pos), "timer": Timer(time_len), 
            "z": z, "vec_z": vec_z, "follow_sprite": follow_sprite, 
            "follow_sprite_pos": follow_sprite.pos.copy(),
            "words_mix": None, "blink": Blink(sfg.Effect.BLINK_RATE3, sfg.Effect.BLINK_DEPTH_SECTION3),
        }
        self.blit_list.append(w)


    def update(self, passed_seconds):
        for i, bw in enumerate(self.blit_list):
            if bw.get("blink") is not None:
                bw["words_mix"] = bw["blink"].make(bw["words"], passed_seconds)

            if not bw["timer"].is_begin():
                bw["timer"].begin()
            elif bw["timer"].exceed():
                self.blit_list.pop(i)
            else:
                mr = bw.get("pos_move_rate")
                if mr is not None:
                    x, y = bw["rel_pos"]
                    x += mr[0] * passed_seconds
                    y += mr[1] * passed_seconds
                    bw["rel_pos"] = (x, y)

                z = bw.get("z")
                if z is not None:
                    bw["z"] += bw["vec_z"] * passed_seconds
                    bw["pos"] += bw["follow_sprite"].pos - bw["follow_sprite_pos"]
                    bw["follow_sprite_pos"] = bw["follow_sprite"].pos.copy()



    def draw(self, camera):
        for bw in self.blit_list:
            words = bw.get("words_mix") or bw.get("words")
            if bw.get("rel_pos"):
                camera.screen.blit(words, (bw["rel_pos"][0] - camera.rect.x, bw["rel_pos"][1] - camera.rect.y))
            elif bw.get("pos"):
                pos = bw["pos"]
                z = bw.get("z", 0)
                camera.screen.blit(words, (pos.x - words.get_width() * 0.5 - camera.rect.x,  
                    pos.y * 0.5 - camera.rect.y - z))



class Particle(pygame.sprite.DirtySprite):
    def __init__(self, image, pos, radius, dx, dy, vec, acc, life, z=0, vec_z=None, acc_z=None, 
            pre_hide_time=0, follow_sprite=None):
        super(Particle, self).__init__()
        self.image = image
        self.pos = Vector2(pos)
        self.pos.y += 5 # trick, make sure particle effect appear in front of the sprite
        self.area = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.area.center = self.pos
        self.dx = dx
        self.dy = dy
        self.vec = Vector2(vec)
        self.acc = acc
        self.life = life
        self.z = z
        self.vec_z = vec_z
        self.acc_z = acc_z
        self.pre_hide_time = pre_hide_time
        self.follow_sprite = follow_sprite
        self.follow_sprite_pos = follow_sprite.pos.copy() if follow_sprite is not None else None


    def update(self, passed_seconds):
        self.pre_hide_time -= passed_seconds
        self.life -= passed_seconds

        if self.follow_sprite:
            self.pos += self.follow_sprite.pos - self.follow_sprite_pos
            self.follow_sprite_pos = self.follow_sprite.pos.copy()
        else:
            self.pos += self.vec * passed_seconds
            self.vec += self.acc * passed_seconds

        if self.vec_z:
            self.z += self.vec_z * passed_seconds
            if self.acc_z:
                self.vec_z += self.acc_z * passed_seconds


    def draw(self, camera):
        if self.pre_hide_time > 0:
            return 

        z = self.z
        if self.follow_sprite and self.follow_sprite.status.get(cfg.SpriteStatus.IN_AIR):
            z += self.follow_sprite.status[cfg.SpriteStatus.IN_AIR]["height"]
        camera.screen.blit(self.image,
            (self.pos.x - camera.rect.x - self.dx, self.pos.y * 0.5 - camera.rect.y - self.dy - z))


    def draw_area(self, camera):
        # for debug
        r = pygame.Rect(0, 0, self.area.width, self.area.height * 0.5)
        r.center = (self.pos.x, self.pos.y * 0.5)
        r.top -= camera.rect.top
        r.left -= camera.rect.left
        pygame.draw.rect(camera.screen, pygame.Color("white"), r, 1)


class SpriteAnimator(object):
    def __init__(self, sprite):
        self.sprite = sprite
        self.sprite_image_contoller = sprite_image_contollers[sprite.setting.ID]
        # frames init
        self.sprite_image_contoller.init_frames(sprite_frame_files[sprite.setting.ID])
        self.frame_nums = sprite_frame_nums[sprite.setting.ID]
        self.frame_rates = sprite_frame_rates[sprite.setting.ID]
        self.frame_adds = dict((k, 0) for k in self.frame_rates.keys()) 

        self.image = self.sprite_image_contoller.get_surface(sprite.action)[sprite.direction]
        self.image_mix = None
        self.rect = self.image.get_rect()
        self.shadow_image = get_shadow_image(sprite.setting.SHADOW_INDEX)
        self.shadow_rect = self.shadow_image.get_rect()
        self.words_renderer = WordsRenderer()
        self.blink = Blink()
        self.particle_list = []

        # frame_action that only has one direction(facing the player, eg. renne's win action)
        self.one_direction_frame_actions = set()


    def get_current_frame_add(self, action):
        return self.frame_adds[action]


    def get_frame_num(self, action):
        return self.frame_nums[action]


    def show_words(self, words, show_time, rel_pos, move_rate=None, make_blink=False):
        self.words_renderer.add_blit_words(words, rel_pos, show_time, move_rate, make_blink)


    def show_follow_sprite_words(self, words, pos, time_len, z, vec_z, follow_sprite):
        self.words_renderer.add_follow_sprite_words(words, pos, time_len, z, vec_z, follow_sprite)
        

    def show_cost_hp(self, hp):
        sp = self.sprite
        words = sfg.SpriteStatus.COST_HP_WORDS_FONT.render("-%s" % hp, True, 
            sfg.SpriteStatus.COST_HP_WORDS_COLOR)

        dx = sfg.SpriteStatus.COST_HP_WORDS_BLIT_X_SIGMA
        dy = sfg.SpriteStatus.COST_HP_WORDS_BLIT_Y_SIGMA
        x = sp.pos.x
        y = sp.pos.y * 0.5 - sp.setting.HEIGHT - sfg.SpriteStatus.COST_HP_WORDS_BLIT_HEIGHT_OFFSET
        rel_pos = (randint(int(x - dx), int(x + dx)), randint(int(y - dy), int(y + dy)))
        self.words_renderer.add_blit_words(words, rel_pos, 
            sfg.SpriteStatus.COST_HP_WORDS_SHOW_TIME,
            sfg.SpriteStatus.COST_HP_WORDS_POS_MOVE_RATE, True)


    def show_recover_hp(self, hp):
        sp = self.sprite
        words = sfg.SpriteStatus.RECOVER_HP_WORDS_FONT.render("+%s" % hp, True,
            sfg.SpriteStatus.RECOVER_HP_WORDS_COLOR)

        dx = sfg.SpriteStatus.RECOVER_HP_WORDS_BLIT_X_SIGMA
        dy = sfg.SpriteStatus.RECOVER_HP_WORDS_BLIT_Y_SIGMA
        x = sp.pos.x
        y = sp.pos.y * 0.5 - sp.setting.HEIGHT - sfg.SpriteStatus.RECOVER_HP_WORDS_BLIT_HEIGHT_OFFSET
        rel_pos = (randint(int(x - dx), int(x + dx)), randint(int(y - dy), int(y + dy)))
        self.words_renderer.add_blit_words(words, rel_pos,
            sfg.SpriteStatus.RECOVER_HP_WORDS_SHOW_TIME,
            sfg.SpriteStatus.RECOVER_HP_WORDS_POS_MOVE_RATE, True)


    def show_cost_mp_sp(self):
        sp = self.sprite
        words = sfg.SpriteStatus.MP_SP_DOWN_WORDS_FONT.render("-MP -SP", True,
            sfg.SpriteStatus.MP_SP_DOWN_WORDS_COLOR)
        dx = sfg.SpriteStatus.MP_SP_DOWN_WORDS_BLIT_X_SIGMA
        dy = sfg.SpriteStatus.MP_SP_DOWN_WORDS_BLIT_Y_SIGMA
        x = sp.pos.x
        y = sp.pos.y * 0.5 - sp.setting.HEIGHT - sfg.SpriteStatus.MP_SP_DOWN_WORDS_BLIT_HEIGHT_OFFSET
        rel_pos = (randint(int(x - dx), int(x + dx)), randint(int(y - dy), int(y + dy)))
        self.words_renderer.add_blit_words(words, rel_pos,
            sfg.SpriteStatus.MP_SP_DOWN_WORDS_SHOW_TIME,
            sfg.SpriteStatus.MP_SP_DOWN_WORDS_POS_MOVE_RATE)


    def set_init_frame(self, action):
        self.image = self.sprite_image_contoller.get_surface(action)[self.sprite.direction]


    def set_frame_add(self, action, frame_add):
        self.frame_adds[action] = frame_add


    def reset_frame_adds(self):
        for action in self.frame_adds.iterkeys():
            self.frame_adds[action] = 0


    def run_circle_frame(self, action, passed_seconds, frame_rate=None):
        # animation will be running in a circle way
        sp = self.sprite
        rate = frame_rate or self.frame_rates[action]
        if sp.status.get(cfg.SpriteStatus.ACTION_RATE_SCALE) is not None:
            rate *= sp.status[cfg.SpriteStatus.ACTION_RATE_SCALE]["ratio"]
        self.frame_adds[action] += passed_seconds * rate
        self.frame_adds[action] %= self.frame_nums[action]


    def run_circle_frame_backward(self, action, passed_seconds):
        # run circle frame in backward way
        sp = self.sprite
        self.frame_adds[action] -= passed_seconds * self.frame_rates[action]
        self.frame_adds[action] %= self.frame_nums[action]


    def run_sequence_frame(self, action, passed_seconds, frame_rate=None):
        # animation will be running only once util the next event occurs
        # return True is a sequence frames is finish else False
        sp = self.sprite
        rate = frame_rate or self.frame_rates[action]
        if sp.status.get(cfg.SpriteStatus.ACTION_RATE_SCALE) is not None:
            rate *= sp.status[cfg.SpriteStatus.ACTION_RATE_SCALE]["ratio"]
        self.frame_adds[action] += passed_seconds * rate

        if self.frame_adds[action] >= self.frame_nums[action]:
            self.frame_adds[action] = 0
            return True

        return False


    def update_image(self):
        sp = self.sprite
        action = sp.frame_action or sp.action
        if action in self.frame_adds:
            if action in self.one_direction_frame_actions:
                self.image = self.sprite_image_contoller.get_surface(
                    action)[int(self.frame_adds[action])]
            else:
                self.image = self.sprite_image_contoller.get_subsurface(action,
                    sp.direction, self.frame_adds[action])


    def update_image_mix(self, passed_seconds):
        sp = self.sprite
        self.image_mix = None

        if sp.status.get(cfg.SpriteStatus.WEAK) is not None:
            sp.status[cfg.SpriteStatus.WEAK]["y"] += sfg.SpriteStatus.DEBUFF_WEAK_Y_MOVE_RATE * passed_seconds
            sp.status[cfg.SpriteStatus.WEAK]["y"] %= sfg.SpriteStatus.DEBUFF_WEAK_Y_MAX

        if sp.hp_status != cfg.HpStatus.DIE \
            and sp.status.get(cfg.SpriteStatus.UNDER_ATTACK) is not None:
            self.image_mix = self.image.copy()
            self.image_mix.fill(sfg.Sprite.UNDER_ATTACK_MIX_COLOR, special_flags=BLEND_ADD)

        if sp.status.get(cfg.SpriteStatus.RECOVER_HP) is not None:
            self.image_mix = self.image.copy()
            self.image_mix.fill(sfg.Sprite.RECOVER_HP_MIX_COLOR, special_flags=BLEND_ADD)


    def update(self, passed_seconds):
        # update image related
        self.update_image()
        self.update_image_mix(passed_seconds)
        self.words_renderer.update(passed_seconds)


    def adjust_rect(self):
        # for drawing to the screen, 
        # y-axis should be a half of pos[1] and considering the distance from pos to image center
        # both rect and shadow_rect
        sp = self.sprite
        rect = self.rect
        rect.center = (sp.pos.x, sp.pos.y * 0.5 - sp.setting.POS_RECT_DELTA_Y)
        shadow_rect = self.shadow_rect
        shadow_rect.center = (rect.center[0], rect.center[1] + sp.setting.SHADOW_RECT_DELTA_Y)


    def draw_shadow(self, camera):
        if not self.rect.colliderect(camera.rect):
            return 

        if self.image is None:
            return

        if self.sprite.status.get(cfg.SpriteStatus.INVISIBLE) is not None:
            return

        shadow_blit_pos = (self.shadow_rect.left - camera.rect.left, self.shadow_rect.top - camera.rect.top)
        camera.screen.blit(self.shadow_image, shadow_blit_pos)


    def draw(self, camera):
        if not self.rect.colliderect(camera.rect):
            return 

        sp = self.sprite
        if self.image_mix is not None:
            # image_mix will overwrite image if it is not none
            image_blit_pos = (self.rect.left - camera.rect.left, self.rect.top - camera.rect.top)
            camera.screen.blit(self.image_mix, image_blit_pos)

        elif self.image is not None:
            # don't modify rect itself, but pass the relative topleft point to the blit function
            if sp.status.get(cfg.SpriteStatus.IN_AIR) is not None:
                image_blit_pos = (self.rect.left - camera.rect.left, 
                    self.rect.top - camera.rect.top - sp.status[cfg.SpriteStatus.IN_AIR]["height"])
            else:
                image_blit_pos = (self.rect.left - camera.rect.left, self.rect.top - camera.rect.top)

            if sp.status.get(cfg.SpriteStatus.BODY_SHAKE) is not None:
                image_blit_pos = (image_blit_pos[0] + sp.status[cfg.SpriteStatus.BODY_SHAKE]["dx"],
                    image_blit_pos[1] + sp.status[cfg.SpriteStatus.BODY_SHAKE]["dy"])

            camera.screen.blit(self.image, image_blit_pos)

        if self.sprite.status.get(cfg.SpriteStatus.WEAK) is not None:
            weak_icon = battle_images.get(sfg.SpriteStatus.DEBUFF_WEAK_IMAGE_KEY).subsurface(
                sfg.SpriteStatus.DEBUFF_WEAK_RECT).convert_alpha()
            sp = self.sprite
            dy = self.sprite.status[cfg.SpriteStatus.WEAK]["y"]
            camera.screen.blit(weak_icon, (sp.pos.x - camera.rect.x - weak_icon.get_width() * 0.5, 
                sp.pos.y * 0.5 - camera.rect.y - sp.setting.HEIGHT - \
                    sfg.SpriteStatus.DEBUFF_WEAK_BLIT_HEIGHT_DELTA + dy))

        if self.sprite.hp_status != cfg.HpStatus.VANISH:
            self.words_renderer.draw(camera)



class HeroAnimator(SpriteAnimator):
    def __init__(self, sprite):
        super(HeroAnimator, self).__init__(sprite)


    def add_level_up_effect(self):
        white_circle_image = effect_image_controller.get(
            sfg.Effect.WHITE_CIRCLE_IMAGE_KEY).subsurface(sfg.Effect.WHITE_CIRCLE_RECT).convert_alpha()
        width = white_circle_image.get_width()
        pos = self.sprite.pos
        delta = sfg.Effect.WHITE_CIRCLE_POS_DELTA
        for i in xrange(sfg.Effect.WHITE_CIRCLE_GEN_NUM):
            x = randint(int(pos.x - delta), int(pos.x + delta))
            y = randint(int(pos.y - delta), int(pos.y + delta))
            circle = Particle(white_circle_image, Vector2(x, y), width * 0.5, width * 0.5, width * 0.5, 
                Vector2(0, 0), Vector2(0, 0), 
                gauss(sfg.Effect.WHITE_CIRCLE_LIFE_MEAN, sfg.Effect.WHITE_CIRCLE_LIFE_SIGMA), 
                gauss(sfg.Effect.WHITE_CIRCLE_Z_MEAN, sfg.Effect.WHITE_CIRCLE_Z_SIGMA), 
                gauss(sfg.Effect.WHITE_CIRCLE_VEC_Z_MEAN, sfg.Effect.WHITE_CIRCLE_VEC_Z_SIGMA), 
                None, 
                gauss(sfg.Effect.WHITE_CIRCLE_PRE_HIDE_TIME_MEAN, sfg.Effect.WHITE_CIRCLE_PRE_HIDE_TIME_SIGMA),
                self.sprite)
            self.particle_list.append(circle)



class RenneAnimator(HeroAnimator):
    def __init__(self, sprite):
        super(RenneAnimator, self).__init__(sprite)
        self.one_direction_frame_actions.add(cfg.RenneAction.WIN)
        self.win_frame_delay_add = 0
        self.win_frame_delay = sfg.Renne.WIN_FRAME_DELAY


    def _run_renne_win_frame(self, passed_seconds):
        # a fancy egg for Renne, ^o^
        action = cfg.RenneAction.WIN
        self.frame_adds[action] += passed_seconds * self.frame_rates[action]
        if self.frame_adds[action] >= self.frame_nums[action] or self.win_frame_delay_add > 0:
            self.frame_adds[action] = self.frame_nums[action] - 1
            self.win_frame_delay_add += passed_seconds
            if self.win_frame_delay_add < self.win_frame_delay:
                # delay for better effect
                return False
            else:
                self.win_frame_delay_add = 0
                self.frame_adds[action] = 0
                self.sprite.direction = cfg.Direction.SOUTH
                return True

        return False



class JoshuaAnimator(HeroAnimator):
    def __init__(self, sprite):
        super(JoshuaAnimator, self).__init__(sprite)
        self.one_direction_frame_actions.add(cfg.JoshuaAction.WIN)
        self.one_direction_frame_actions.add(cfg.JoshuaAction.BIG_SKILL)



class EnemyAnimator(SpriteAnimator):
    def __init__(self, sprite):
        super(EnemyAnimator, self).__init__(sprite)
        self.die_image = None
        self.dead_timer = Timer(sfg.Enemy.DEAD_TICK)
        self.hp_bar = pygame.Surface(sfg.SpriteStatus.ENEMY_HP_BAR_SIZE).convert_alpha()


    def dead_tick(self):
        if not self.dead_timer.is_begin():
            self.die_image = self.image.copy()
            self.dead_timer.begin()
        else:
            if self.dead_timer.exceed():
                self.image = None
                return True

            pass_time = self.dead_timer.passed_time()
            # in 1 blink unit, one half show image, another half hide it
            # make it like a blink effect
            dead_blink_unit = float(sfg.Enemy.DEAD_TICK) / sfg.Enemy.DEAD_BLINK_TIMES
            if pass_time % dead_blink_unit < dead_blink_unit * 0.5:
                self.image = self.die_image
            else:
                self.image = None

        return False


    def draw_hp_bar(self, camera):
        # fill color to hp_bar according to the sprite hp
        sp = self.sprite
        self.hp_bar.fill(sfg.SpriteStatus.SPRITE_BAR_BG_COLOR)
        r = self.hp_bar.get_rect()
        r.width *= float(sp.hp) / sp.setting.HP
        hp_color = sfg.SpriteStatus.SPRITE_HP_COLORS[sp.hp_status]
        self.hp_bar.fill(hp_color, r)

        # adjust hp_bar position relative to screen
        r = self.hp_bar.get_rect()
        r.center = (sp.pos.x, sp.pos.y * 0.5 - sp.setting.HEIGHT)
        r.left -= camera.rect.left
        r.top -= camera.rect.top
        if sp.status.get(cfg.SpriteStatus.IN_AIR) is not None:
            r.top -= sp.status[cfg.SpriteStatus.IN_AIR]["height"]
        camera.screen.blit(self.hp_bar, r)


    def draw_with_height(self, camera, height):
        image_blit_pos = (self.rect.x - camera.rect.x, self.rect.y - camera.rect.y - height)
        camera.screen.blit(self.image, image_blit_pos)


    def draw(self, camera):
        sp = self.sprite
        if sp.status.get(cfg.SpriteStatus.AMBUSH) is not None:
            # this enemy is in ambush status, draw it according the corresponding status stage
            if sp.status[cfg.SpriteStatus.AMBUSH]["status"] == cfg.Ambush.STATUS_INIT:
                # don't draw it because hero doesn't enter this ambush
                return

            elif sp.status[cfg.SpriteStatus.AMBUSH]["status"] == cfg.Ambush.STATUS_ENTER:
                # hero enter the ambush, draw corresponding episode
                if sp.status[cfg.SpriteStatus.AMBUSH]["type"] == cfg.Ambush.APPEAR_TYPE_TOP_DOWN:
                    self.draw_with_height(camera, 
                        sp.status[cfg.SpriteStatus.AMBUSH]["height"])
                return

        if sp.status.get(cfg.SpriteStatus.INVISIBLE) is not None:
            return

        super(EnemyAnimator, self).draw(camera)
        if sp.hp_status in cfg.HpStatus.ALIVE:
            self.draw_hp_bar(camera)



class SpriteEmotionAnimator(object):
    image_src = basic_image_controller.get("emotion").convert_alpha()
    frame_mapping = {}
    frame_nums = {}
    frame_rates = {}

    def __init__(self, sprite):
        self.sprite = sprite
        self.init_frames()
        self.frame_adds = dict((k, 0) for k in self.frame_mapping)
        self.image = None


    def init_frames(self):
        if set(self.frame_mapping.keys()) == set(sfg.EmotionImage.FRAMES.keys()):
            return

        all_images = []
        w, h = sfg.EmotionImage.SIZE
        for i in xrange(sfg.EmotionImage.ROW):
            for j in xrange(sfg.EmotionImage.COLUMN):
                all_images.append(self.image_src.subsurface(pygame.Rect((w * j, h * i), (w, h))))

        for emotion_id, ((begin, end), frame_num, frame_rate) in sfg.EmotionImage.FRAMES.iteritems():
            self.frame_mapping[emotion_id] = all_images[begin:end]
            self.frame_nums[emotion_id] = frame_num
            self.frame_rates[emotion_id] = frame_rate


    def reset_frame(self, emotion):
        self.frame_adds[emotion] = 0
        self.image = None


    def run_circle_frame(self, emotion, passed_seconds):
        self.frame_adds[emotion] += passed_seconds * self.frame_rates[emotion]
        self.frame_adds[emotion] %= self.frame_nums[emotion]
        self.image = self.frame_mapping[emotion][int(self.frame_adds[emotion])]

    def run_sequence_frame(self, emotion, passed_seconds):
        self.frame_adds[emotion] += passed_seconds * self.frame_rates[emotion]
        if self.frame_adds[emotion] >= self.frame_nums[emotion]:
            self.reset_frame(emotion)
            return True
        else:
            self.image = self.frame_mapping[emotion][int(self.frame_adds[emotion])]
            return False


    def update(self, passed_seconds):
        sp = self.sprite
        if sp.emotion != cfg.SpriteEmotion.NORMAL:
            if sp.emotion in (cfg.SpriteEmotion.STUN, cfg.SpriteEmotion.DIZZY):
                self.run_circle_frame(sp.emotion, passed_seconds)        
            else:
                is_finish = self.run_sequence_frame(sp.emotion, passed_seconds)
                if is_finish:
                    sp.emotion = cfg.SpriteEmotion.NORMAL


    def draw(self, camera):
        if self.image is not None:
            sp = self.sprite
            rect = self.image.get_rect()
            rect.center = (sp.pos.x, sp.pos.y * 0.5 - sp.setting.HEIGHT)
            camera.screen.blit(self.image, 
                (rect.left - camera.rect.left, rect.top - camera.rect.top))

