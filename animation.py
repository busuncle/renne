import pygame
from pygame.locals import BLEND_ADD
from time import time
from random import randint
from base.util import ImageController, SpriteImageController, Timer
import etc.setting as sfg
import etc.constant as cfg


# init SpriteImageController
sprite_image_contollers = {}
for k, v in sfg.SPRITE_FRAMES.iteritems():
    sprite_image_contollers[k] = SpriteImageController(v[0])


basic_image_controller = ImageController(sfg.BASIC_IMAGES[0])
basic_image_controller.add_from_list(sfg.BASIC_IMAGES[1])

cg_image_controller = ImageController(sfg.CG_IMAGES[0])
cg_image_controller.add_from_list(sfg.CG_IMAGES[1])



class WordsRenderer(object):
    def __init__(self):
        self.blit_list = []


    def add_blit_words(self, words, rel_pos, time_len):
        self.blit_list.append({"words": words, "rel_pos": rel_pos, "timer": Timer(time_len)})


    def update(self):
        for i, bw in enumerate(self.blit_list):
            if not bw["timer"].is_begin():
                bw["timer"].begin()
            elif bw["timer"].exceed():
                self.blit_list.pop(i)


    def draw(self, camera):
        for bw in self.blit_list:
            camera.screen.blit(bw["words"], (bw["rel_pos"][0] - camera.rect.left, 
                bw["rel_pos"][1] - camera.rect.top))



class SpriteAnimator(object):
    def __init__(self, sprite):
        self.sprite = sprite
        self.sprite_image_contoller = sprite_image_contollers[sprite.setting.ID]
        # frames init
        self.sprite_image_contoller.init_frames(sfg.SPRITE_FRAMES[sprite.setting.ID][1])
        self.frame_rates = sprite.setting.FRAME_RATES
        self.frame_nums = sprite.setting.FRAME_NUMS
        self.frame_adds = dict((k, 0) for k in self.frame_rates.keys()) 

        self.image = self.sprite_image_contoller.get_surface(sprite.action)[sprite.direction]
        self.rect = self.image.get_rect()
        self.shadow_image = self.gen_shadow_image(sprite.setting.SHADOW_INDEX)
        self.shadow_rect = self.shadow_image.get_rect()
        self.words_renderer = WordsRenderer()


    def gen_shadow_image(self, shadow_index):
        return basic_image_controller.get("sprite_shadow").convert_alpha().subsurface(
            pygame.Rect((64 * (shadow_index % 4), 128 * (shadow_index / 4)), (64, 128))
        )


    def get_current_frame_add(self, action):
        return self.frame_adds[action]


    def show_cost_hp(self, hp):
        sp = self.sprite
        words = sfg.SpriteStatus.COST_HP_WORDS_FONT.render("-%s" % hp, True, 
            sfg.SpriteStatus.COST_HP_WORDS_COLOR)

        dx = sfg.SpriteStatus.COST_HP_WORDS_BLIT_X_SIGMA
        dy = sfg.SpriteStatus.COST_HP_WORDS_BLIT_Y_SIGMA
        x = sp.pos.x
        y = sp.pos.y / 2 - sp.setting.HEIGHT - sfg.SpriteStatus.COST_HP_WORDS_BLIT_HEIGHT_OFFSET
        rel_pos = (randint(int(x - dx), int(x + dx)), randint(int(y - dy), int(y + dy)))
        self.words_renderer.add_blit_words(words, rel_pos, sfg.SpriteStatus.COST_HP_WORDS_SHOW_TIME)


    def run_circle_frame(self, action, passed_seconds):
        # animation will be running in a circle way
        self.frame_adds[action] += passed_seconds * self.frame_rates[action]
        self.frame_adds[action] %= self.frame_nums[action]
        self.image = self.sprite_image_contoller.get_surface(action)[
            self.sprite.direction + cfg.Direction.TOTAL * int(self.frame_adds[action])]


    def run_sequence_frame(self, action, passed_seconds):
        # animation will be running only once util the next event occurs
        # return True is a sequence frames is finish else False
        self.frame_adds[action] += passed_seconds * self.frame_rates[action]
        if self.frame_adds[action] >= self.frame_nums[action]:
            self.frame_adds[action] = 0
            return True
        else:
            self.image = self.sprite_image_contoller.get_surface(action)[
                self.sprite.direction + cfg.Direction.TOTAL * int(self.frame_adds[action])]
            return False


    def update(self):
        if self.sprite.status["under_attack"]:
            self.sprite.attacker.under_attack_tick()
            image_mix = self.image.copy()
            image_mix.fill(pygame.Color("gray"), special_flags=BLEND_ADD)
            self.image = image_mix

        self.words_renderer.update()


    def draw(self, camera):
        if self.image is not None:
            # don't modify rect itself, but pass the relative topleft point to the blit function
            image_blit_pos = (self.rect.left - camera.rect.left, self.rect.top - camera.rect.top)
            shadow_blit_pos = (self.shadow_rect.left - camera.rect.left, self.shadow_rect.top - camera.rect.top)

            # draw shadow first, and then the sprite itself
            camera.screen.blit(self.shadow_image, shadow_blit_pos)
            camera.screen.blit(self.image, image_blit_pos)

        self.words_renderer.draw(camera)



class RenneAnimator(SpriteAnimator):
    def __init__(self, sprite):
        super(RenneAnimator, self).__init__(sprite)

    def _run_renne_win_frame(self, passed_seconds):
        # a fancy egg for Renne, ^o^
        action = cfg.HeroAction.WIN
        self.frame_adds[action] += passed_seconds * self.frame_rates[action]
        if self.frame_adds[action] >= self.frame_nums[action]:
            if self.frame_adds[action] < self.frame_nums[action] + 12:
                # delay for better effect
                self.image = self.sprite_image_contoller.get_surface(action)[self.frame_nums[action] - 1]
                return False
            else:
                self.frame_adds[action] = 0
                self.sprite.direction = cfg.Direction.SOUTH
                return True
        else:
            self.image = self.sprite_image_contoller.get_surface(action)[int(self.frame_adds[action])]
            return False



class EnemyAnimator(SpriteAnimator):
    def __init__(self, sprite):
        super(EnemyAnimator, self).__init__(sprite)
        self.die_image = None
        self.dead_timer = Timer(sfg.Enemy.DEAD_TICK)
        self.dead_blink_unit = float(sfg.Enemy.DEAD_TICK) / sfg.Enemy.DEAD_BLINK_TIMES


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
            if pass_time % self.dead_blink_unit < self.dead_blink_unit * 0.5:
                self.image = self.die_image
            else:
                self.image = None

        return False



class SpriteEmotionAnimator(object):
    image_src = basic_image_controller.get("emotion")
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

        self.image_src = self.image_src.convert_alpha()
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


    def run_sequence_frame(self, emotion, passed_seconds):
        self.frame_adds[emotion] += passed_seconds * self.frame_rates[emotion]
        if self.frame_adds[emotion] >= self.frame_nums[emotion]:
            self.frame_adds[emotion] = 0
            self.image = None
            return True
        else:
            self.image = self.frame_mapping[emotion][int(self.frame_adds[emotion])]
            return False
