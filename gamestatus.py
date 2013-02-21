from time import time
import pygame
from pygame.locals import *
from pygame.transform import smoothscale
from util import ImageController
import etc.setting as sfg
import etc.constant as cfg



class GameStatus(object):
    battle_images = ImageController(sfg.BATTLE_IMAGES[0])
    battle_images.add_from_list(sfg.BATTLE_IMAGES[1])

    def __init__(self, chapter, hero, enemies):
        self.chapter = chapter
        self.hero = hero
        self.enemies = enemies
        self.info_titles = sfg.GameStatus.INFO_TITLES
        self.status_panel = self.gen_panel("status", 
            sfg.GameStatus.HERO_PANEL_RECT, sfg.GameStatus.HERO_PANEL_SCALE_SIZE)
        self.head_images_list = self.gen_head_images_list()
        self.sprite_hp_colors = sfg.GameStatus.SPRITE_HP_COLORS
        self.status = cfg.GameStatus.INIT
        self.chapter_panel = self.gen_panel("status3", sfg.GameStatus.CHAPTER_PANEL_RECT)
        self.chapter_info = self.gen_chapter_info()
        self.win_panel = self.gen_panel("status2", sfg.GameStatus.HERO_WIN_PANEL_RECT)
        self.lose_panel = self.gen_panel("status2", sfg.GameStatus.HERO_LOSE_PANEL_RECT)
        self.numbers = self.gen_numbers()
        self.begin_time = None


    def gen_panel(self, image_key, rect, scale=None):
        panel = self.battle_images.get(image_key).convert_alpha().subsurface(pygame.Rect(rect))
        if scale is not None:
            panel = smoothscale(panel, (int(panel.get_width() * scale[0]), int(panel.get_height() * scale[1])))
        return panel


    def gen_chapter_info(self):
        f = sfg.GameStatus.CHAPTER_FONT
        return pygame.font.SysFont(f["name"], f["size"], italic=f["italic"]).render(
            "%s %s" % (f["pre"], self.chapter), f["antialias"], f["color"])


    def gen_numbers(self):
        res = {}
        number_panel = self.gen_panel("status4", sfg.GameStatus.NUMBER_RECT)
        w, h = sfg.GameStatus.NUMBER_SIZE
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
        if self.hero.status == cfg.SpriteStatus.DIE:
            # hero is dead, game over
            self.status = cfg.GameStatus.HERO_LOSE
            return

        if len(self.enemies) == 0:
            self.status = cfg.GameStatus.HERO_WIN
            return 

        remove_list = []
        for em in self.enemies:
            if em.status == cfg.SpriteStatus.DIE:
                can_be_removed = em.animation.death_tick()
                if can_be_removed:
                    remove_list.append(em)

        for em in remove_list:
            self.enemies.remove(em)


    def make_bar(self, size, curren_val, full_val, bar_color, background_color):
        bar = pygame.Surface(size, flags=SRCALPHA, depth=32).convert_alpha()
        bar.fill(background_color)
        bar_rect = bar.get_rect()
        bar_rect.width *= float(curren_val) / full_val
        bar.fill(bar_color, bar_rect)
        return bar


    def draw_enemy_hp_bar(self, enemy, camera):
        hp_color = self.sprite_hp_colors[enemy.status]
        hp_bar = self.make_bar(sfg.GameStatus.ENEMY_HP_BAR_SIZE, enemy.hp, enemy.setting.HP,
            self.sprite_hp_colors[enemy.status], sfg.GameStatus.SPRITE_BAR_BG_COLOR)
        r = hp_bar.get_rect() 
        r.center = (enemy.pos.x, enemy.pos.y / 2 - enemy.setting.HEIGHT)
        r.top -= camera.rect.top
        r.left -= camera.rect.left
        camera.screen.blit(hp_bar, r)


    def draw(self, camera):
        camera.screen.blit(self.status_panel, sfg.GameStatus.HERO_PANEL_BLIT_POS)

        self.status_panel.blit(self.info_titles["hero_hp"], sfg.GameStatus.HERO_HP_TITLE_BLIT_POS)
        self.status_panel.blit(self.info_titles["hero_sp"], sfg.GameStatus.HERO_SP_TITLE_BLIT_POS)

        # Renne's head, showing her status
        self.status_panel.blit(self.get_current_head(self.hero.status), sfg.GameStatus.HERO_HEAD_BLIT_POS)

        # draw the hp bar for Renne
        hp_bar = self.make_bar(sfg.GameStatus.HERO_ALL_BAR_SIZE, self.hero.hp, self.hero.setting.HP,
            self.sprite_hp_colors[self.hero.status], sfg.GameStatus.SPRITE_BAR_BG_COLOR)
        self.status_panel.blit(hp_bar, sfg.GameStatus.HERO_HP_BLIT_POS)

        # draw the sp bar for Renne
        sp_bar = self.make_bar(sfg.GameStatus.HERO_ALL_BAR_SIZE, self.hero.stamina, self.hero.setting.STAMINA,
            sfg.GameStatus.HERO_SP_COLOR, sfg.GameStatus.SPRITE_BAR_BG_COLOR)
        self.status_panel.blit(sp_bar, sfg.GameStatus.HERO_SP_BLIT_POS)

        for enemy in self.enemies:
            # draw the hp bar for all enemies
            if enemy.emotion_animation.image is not None:
                # don't draw the hp bar when the enemy is in some emotion
                continue

            self.draw_enemy_hp_bar(enemy, camera)

        # chapter info
        self.chapter_panel.blit(self.chapter_info, sfg.GameStatus.CHAPTER_INFO_BLIT_POS)
        camera.screen.blit(self.chapter_panel, sfg.GameStatus.CHAPTER_PANEL_BLIT_POS)

        if self.status == cfg.GameStatus.INIT:
            if self.begin_time is None:
                self.begin_time = time()
            else:
                pass_time = time() - self.begin_time
                if pass_time >= sfg.GameStatus.INIT_PERSIST_TIME:
                    # game begin, change the status
                    self.status = cfg.GameStatus.IN_PROGRESS
                else:
                    # count down for game begin
                    left_time = sfg.GameStatus.INIT_PERSIST_TIME - pass_time
                    number_to_draw = self.numbers[int(left_time)+1]
                    camera.screen.blit(number_to_draw, sfg.GameStatus.NUMBER_BLIT_POS)

        elif self.status == cfg.GameStatus.HERO_WIN:
            camera.screen.blit(self.win_panel, sfg.GameStatus.HERO_WIN_BLIT_POS)
        elif self.status == cfg.GameStatus.HERO_LOSE:
            camera.screen.blit(self.lose_panel, sfg.GameStatus.HERO_LOSE_BLIT_POS)

