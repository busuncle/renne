from time import time
import pygame
from pygame.locals import *
from pygame.transform import smoothscale, scale2x
from base.util import ImageController
import etc.setting as sfg
import etc.constant as cfg
from base.util import Timer



screen_surface = sfg.Screen.DEFAULT_SURFACE

battle_images = ImageController(sfg.BATTLE_IMAGES[0])
battle_images.add_from_list(sfg.BATTLE_IMAGES[1])



def gen_panel(images, image_key, rect, scale=None):
    panel = images.get(image_key).convert_alpha().subsurface(pygame.Rect(rect))
    if scale is not None:
        panel = smoothscale(panel, (int(panel.get_width() * scale[0]), int(panel.get_height() * scale[1])))
    return panel


def gen_numbers(images, filekey, number_rect, number_size):
    res = {}
    number_panel = gen_panel(images, filekey, number_rect)
    w, h = number_size
    for i in xrange(10):
        res[i] = number_panel.subsurface(pygame.Rect((i * w, 0), (w, h)))

    return res



class GameStatus(object):
    def __init__(self, chapter, hero, enemy_list):
        self.chapter = chapter
        self.hero = hero
        self.enemy_list = enemy_list
        self.status = cfg.GameStatus.INIT
        self.win_panel = gen_panel(battle_images, "status2", sfg.GameStatus.HERO_WIN_PANEL_RECT)
        self.lose_panel = gen_panel(battle_images, "status2", sfg.GameStatus.HERO_LOSE_PANEL_RECT)
        self.numbers1 = gen_numbers(battle_images, "status4", sfg.GameStatus.NUMBER_RECT1, sfg.GameStatus.NUMBER_SIZE1)
        self.begin_timer = Timer()
        self.hero_status = HeroStatus(hero)
        self.achievement = Achievement(hero, enemy_list)


    def update(self):
        if self.hero.status["hp"] == cfg.SpriteStatus.DIE:
            # hero is dead, game over
            self.status = cfg.GameStatus.HERO_LOSE
            return

        if len(self.enemy_list) == 0:
            # all enemies are gone, hero win
            self.status = cfg.GameStatus.HERO_WIN
            return 

        remove_list = []
        for em in self.enemy_list:
            if em.status["hp"] == cfg.SpriteStatus.DIE:
                can_be_removed = em.animation.death_tick()
                if can_be_removed:
                    remove_list.append(em)

        for em in remove_list:
            self.enemy_list.remove(em)

        # achievement calculation here
        self.achievement.update()


    def draw(self, camera):
        # hero status draw here
        self.hero_status.draw(camera)

        # achievement draw here
        self.achievement.draw(camera)

        if self.status == cfg.GameStatus.INIT:
            if not self.begin_timer.is_begin():
                self.begin_timer.begin(sfg.GameStatus.INIT_PERSIST_TIME)

            if self.begin_timer.exceed():
                # game begin, change the status
                self.status = cfg.GameStatus.IN_PROGRESS
            else:
                # count down for game begin, draw corresponding count-down numbers
                left_time = sfg.GameStatus.INIT_PERSIST_TIME - self.begin_timer.passed_time()
                number_to_draw = self.numbers1[int(left_time)+1]
                camera.screen.blit(number_to_draw, sfg.GameStatus.BEGIN_NUMBER_BLIT_POS)

        elif self.status == cfg.GameStatus.HERO_WIN:
            screen_surface.fill(sfg.Stuff.MASK_ALPHA_128)
            camera.screen.blit(screen_surface, (0, 0))
            camera.screen.blit(self.win_panel, sfg.GameStatus.HERO_WIN_BLIT_POS)
        elif self.status == cfg.GameStatus.HERO_LOSE:
            screen_surface.fill(sfg.Stuff.MASK_ALPHA_128)
            camera.screen.blit(screen_surface, (0, 0))
            camera.screen.blit(self.lose_panel, sfg.GameStatus.HERO_LOSE_BLIT_POS)



class HeroStatus(object):
    def __init__(self, hero):
        self.hero = hero
        self.head_images_list = self.gen_head_images_list()
        self.status_panel = gen_panel(battle_images, "status", 
            sfg.SpriteStatus.HERO_PANEL_RECT, sfg.SpriteStatus.HERO_PANEL_SCALE_SIZE)
        self.hero_hp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE).convert_alpha()
        self.hero_sp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE).convert_alpha()


    def gen_head_images_list(self):
        # generate the head image in status panel for Renne
        res = []
        w, h = sfg.SpriteStatus.HERO_HEAD_SIZE
        for row in (0, 1):
            for column in (0, 1):
                res.append(battle_images.get("renne_head").convert_alpha().subsurface(
                    pygame.Rect(w * column, h * row, w, h)
                ))
        return res


    def get_current_head(self, status):
        return self.head_images_list[status]


    def draw_hero_bar(self, camera, current_value, full_value, bar, bar_color, blit_pos):
        bar.fill(sfg.SpriteStatus.SPRITE_BAR_BG_COLOR)
        r = bar.get_rect()
        r.width *= float(current_value) / full_value
        bar.fill(bar_color, r)
        camera.screen.blit(bar, blit_pos)


    def draw(self, camera):
        # panel first, other things over it
        camera.screen.blit(self.status_panel, sfg.SpriteStatus.HERO_PANEL_BLIT_POS)

        # Renne's head, showing her status
        camera.screen.blit(self.get_current_head(self.hero.status["hp"]), sfg.SpriteStatus.HERO_HEAD_BLIT_POS)

        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_hp"], sfg.SpriteStatus.HERO_HP_TITLE_BLIT_POS)
        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_sp"], sfg.SpriteStatus.HERO_SP_TITLE_BLIT_POS)

        # draw the hp bar for Renne
        self.draw_hero_bar(camera, self.hero.hp, self.hero.setting.HP, self.hero_hp_bar, 
            sfg.SpriteStatus.SPRITE_HP_COLORS[self.hero.status["hp"]], 
            sfg.SpriteStatus.HERO_HP_BLIT_POS)

        # draw the sp bar for Renne
        self.draw_hero_bar(camera, self.hero.sp, self.hero.setting.SP, self.hero_sp_bar,
            sfg.SpriteStatus.HERO_SP_COLOR, sfg.SpriteStatus.HERO_SP_BLIT_POS)



class Achievement(object):
    def __init__(self, hero, enemy_list):
        self.hero = hero
        self.enemy_list = enemy_list
        self.total_enemy_num = len(self.enemy_list)
        self.kill_num = 0
        self.n_hit_list = []
        self.n_kill_list = []
        self.kill_time_list = []
        self.current_n_kill_index = 0
        self.current_kill_time_index = 0
        self.kill_icon = gen_panel(battle_images, "status5", sfg.Achievement.KILL_ICON_RECT)
        self.numbers2 = gen_numbers(battle_images, "icon1", sfg.GameStatus.NUMBER_RECT2, sfg.GameStatus.NUMBER_SIZE2)


    def update(self):
        # calculate kill num
        self.kill_num = self.total_enemy_num - len(self.enemy_list)

        # calculate n_hit
        if len(self.hero.attacker.hit_record) > 0:
            for record in self.hero.attacker.hit_record:
                if record["n_hit"] > 1:
                    print "%s hit!" % record["n_hit"]
                    self.n_hit_list.append(record["n_hit"])

            self.hero.attacker.hit_record = []

        # calculate n_kill
        if len(self.hero.attacker.kill_record) > 0:
            for record in self.hero.attacker.kill_record:
                self.kill_time_list.append(record["time"])
                if len(self.kill_time_list) == 1:
                    self.n_kill_list.append(1)
                else:
                    if self.kill_time_list[-1] - self.kill_time_list[-2] <= sfg.Achievement.N_KILL_TIMEDELTA:
                        self.n_kill_list.append(self.n_kill_list[-1] + 1)
                        print "%s kill!" % self.n_kill_list[-1]
                    else:
                        self.n_kill_list.append(1)

            self.hero.attacker.kill_record = []


    def draw(self, camera):
        # suppose(be sure) kill_num < 100, e.g. 12, so "kill_num / 10" gets 1, and "kill_num % 10" is 2
        camera.screen.blit(self.kill_icon, sfg.Achievement.KILL_ICON_BLIT_POS)
        camera.screen.blit(scale2x(self.numbers2[self.kill_num / 10]), 
            sfg.Achievement.KILL_NUM_BLIT_POS)
        camera.screen.blit(scale2x(self.numbers2[self.kill_num % 10]), 
            sfg.Achievement.KILL_NUM_BLIT_POS2)
