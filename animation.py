import pygame
from time import time
from base.util import ImageController, SpriteImageController
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


    def gen_shadow_image(self, shadow_index):
        return basic_image_controller.get("sprite_shadow").convert_alpha().subsurface(
            pygame.Rect((64 * (shadow_index % 4), 128 * (shadow_index / 4)), (64, 128))
        )


    def get_current_frame_add(self, action):
        return self.frame_adds[action]


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
        self.die_begin_time = None


    def death_tick(self):
        assert(self.sprite.status["hp"] == cfg.SpriteStatus.DIE)

        if self.die_begin_time is None:
            self.die_image = self.image.copy()
            self.die_begin_time = time()
        else:
            pass_time = time() - self.die_begin_time
            # blink 3 times, persistant 0.5 second everytime
            if pass_time > 1.5:
                self.image = None
                return True

            if pass_time % 0.5 < 0.25:
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
