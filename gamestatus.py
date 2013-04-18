from time import time
import pygame
from pygame.locals import *
from pygame.transform import smoothscale, scale2x
from base.util import ImageController
import etc.setting as sfg
import etc.constant as cfg
from base.util import Timer



class GameStatus(object):
    battle_images = ImageController(sfg.BATTLE_IMAGES[0])
    battle_images.add_from_list(sfg.BATTLE_IMAGES[1])

    def __init__(self, chapter, hero, enemies):
        self.chapter = chapter
        self.hero = hero
        self.enemies = enemies
        self.head_images_list = self.gen_head_images_list()
        self.status_panel = self.gen_panel("status", 
            sfg.GameStatus.HERO_PANEL_RECT, sfg.GameStatus.HERO_PANEL_SCALE_SIZE)
        self.hero_hp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE, 
            flags=SRCALPHA, depth=32).convert_alpha()
        self.hero_sp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE,
            flags=SRCALPHA, depth=32).convert_alpha()
        self.status = cfg.GameStatus.INIT
        self.win_panel = self.gen_panel("status2", sfg.GameStatus.HERO_WIN_PANEL_RECT)
        self.lose_panel = self.gen_panel("status2", sfg.GameStatus.HERO_LOSE_PANEL_RECT)
        self.kill_icon = self.gen_panel("status5", sfg.GameStatus.KILL_ICON_RECT)
        self.numbers1 = self.gen_numbers("status4", sfg.GameStatus.NUMBER_RECT1, sfg.GameStatus.NUMBER_SIZE1)
        self.numbers2 = self.gen_numbers("icon1", sfg.GameStatus.NUMBER_RECT2, sfg.GameStatus.NUMBER_SIZE2)
        self.begin_timer = Timer()
        self.total_enemy_num = len(self.enemies)
        self.current_enemy_num = self.total_enemy_num


    def gen_panel(self, image_key, rect, scale=None):
        panel = self.battle_images.get(image_key).convert_alpha().subsurface(pygame.Rect(rect))
        if scale is not None:
            panel = smoothscale(panel, (int(panel.get_width() * scale[0]), int(panel.get_height() * scale[1])))
        return panel


    def gen_numbers(self, filekey, number_rect, number_size):
        res = {}
        number_panel = self.gen_panel(filekey, number_rect)
        w, h = number_size
        for i in xrange(10):
            res[i] = number_panel.subsurface(pygame.Rect((i * w, 0), (w, h)))

        return res


    def gen_head_images_list(self):
        # generate the head image in status panel for Renne
        res = []
        w, h = sfg.GameStatus.HERO_HEAD_SIZE
        for row in (0, 1):
            for column in (0, 1):
                res.append(self.battle_images.get("renne_head").convert_alpha().subsurface(
                    pygame.Rect(w * column, h * row, w, h)
                ))
        return res


    def get_current_head(self, status):
        return self.head_images_list[status]


    def update(self):
        if self.hero.status["hp"] == cfg.SpriteStatus.DIE:
            # hero is dead, game over
            self.status = cfg.GameStatus.HERO_LOSE
            return

        if len(self.enemies) == 0:
            self.status = cfg.GameStatus.HERO_WIN
            return 

        remove_list = []
        for em in self.enemies:
            if em.status["hp"] == cfg.SpriteStatus.DIE:
                can_be_removed = em.animation.death_tick()
                if can_be_removed:
                    remove_list.append(em)

        for em in remove_list:
            self.enemies.remove(em)

        self.current_enemy_num = len(self.enemies)


    def draw_hero_bar(self, camera, bar, bar_color, blit_pos):
        bar.fill(sfg.SpriteStatus.SPRITE_BAR_BG_COLOR)
        r = self.bar.get_rect()
        r.width *= float(self.hero.hp) / self.hero.HP
        bar.fill(bar_color, r)
        camera.screen.blit(bar, blit_pos)


    def draw(self, camera):
        # panel first, other things over it
        camera.screen.blit(self.status_panel, sfg.GameStatus.HERO_PANEL_BLIT_POS)

        # Renne's head, showing her status
        camera.screen.blit(self.get_current_head(self.hero.status["hp"]), sfg.GameStatus.HERO_HEAD_BLIT_POS)

        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_hp"], sfg.SpriteStatus.HERO_HP_TITLE_BLIT_POS)
        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_sp"], sfg.SpriteStatus.HERO_SP_TITLE_BLIT_POS)

        # draw the hp bar for Renne
        self.draw_hero_bar(camera, self.hero_hp_bar, 
            sfg.SpriteStatus.SPRITE_HP_COLORS[self.hero.status["hp"]], 
            sfg.SpriteStatus.HERO_HP_BLIT_POS)

        # draw the sp bar for Renne
        self.draw_hero_bar(camera, self.hero_sp_bar,
            sfg.SpriteStatus.HERO_SP_COLOR, sfg.SpriteStatus.HERO_SP_BLIT_POS)

        camera.screen.blit(self.kill_icon, sfg.GameStatus.KILL_ICON_BLIT_POS)

        kill_num = self.total_enemy_num - self.current_enemy_num
        # suppose(be sure) kill_num < 100, e.g. 12, so "kill_num / 10" gets 1, and "kill_num % 10" is 2
        camera.screen.blit(scale2x(self.numbers2[kill_num / 10]), sfg.GameStatus.KILL_NUM_BLIT_POS)
        camera.screen.blit(scale2x(self.numbers2[kill_num % 10]), sfg.GameStatus.KILL_NUM_BLIT_POS2)

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
            camera.screen.blit(self.win_panel, sfg.GameStatus.HERO_WIN_BLIT_POS)
        elif self.status == cfg.GameStatus.HERO_LOSE:
            camera.screen.blit(self.lose_panel, sfg.GameStatus.HERO_LOSE_BLIT_POS)

