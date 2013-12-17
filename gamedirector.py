from time import time
import pygame
from pygame.locals import *
from pygame.transform import smoothscale, scale2x
from animation import cg_image_controller, basic_image_controller, effect_image_controller, battle_images
from musicbox import BackgroundBox
from base.util import ImageController
from base.util import Timer, load_chapter_win_screen_image
from base import util
from base import constant as cfg
from etc import setting as sfg
import sys



bg_box = BackgroundBox()



def screen_draw_y_symmetric(camera, blit_surface, y):
    # given y, draw the surface to screen that it's y-axis symmetric
    r = blit_surface.get_rect()
    r.centerx = camera.size[0] * 0.5
    r.top = y
    camera.screen.blit(blit_surface, r)



def gen_panel(images, image_key, rect, scale=None):
    panel = images.get(image_key).convert_alpha().subsurface(pygame.Rect(rect))
    if scale is not None:
        panel = smoothscale(panel, scale)
    return panel



def gen_numbers(images, filekey, number_rect, number_size):
    res = {}
    number_panel = gen_panel(images, filekey, number_rect)
    w, h = number_size
    for i in xrange(10):
        res[i] = number_panel.subsurface(pygame.Rect((i * w, 0), (w, h)))

    return res



class Menu(object):
    def __init__(self, menu_setting):
        self.index = 0
        self.options = [v["name"] for v in menu_setting["options"] if v["display"]]
        self.marks = [v["mark"] for v in menu_setting["options"] if v["display"]]
        self.option_rect = pygame.Rect(menu_setting["option_rect"])
        self.blit_y = menu_setting["blit_y"]
        self.font_on = menu_setting["font_on"]
        self.font_off = menu_setting["font_off"]
        self.color_on = menu_setting["color_on"]
        self.color_off = menu_setting["color_off"]
        self.renne_cursor = basic_image_controller.get(
            sfg.Menu.RENNE_CURSOR_IMAGE_KEY).subsurface(
            pygame.Rect(sfg.Menu.RENNE_CURSOR_RECT)).convert_alpha()


    def get_current_mark(self):
        return self.marks[self.index]


    def update(self, key):
        # 0 <= menu_index <= len(menu_list) - 1
        if key in (sfg.UserKey.DOWN, K_DOWN):
            self.index = min(self.index + 1, len(self.options) - 1)
        elif key in (sfg.UserKey.UP, K_UP):
            self.index = max(0, self.index - 1)


    def draw(self, screen):
        menu_blit_y = self.blit_y
        screen_centerx = sfg.Screen.SIZE[0] * 0.5
        for i, menu_word in enumerate(self.options):
            if i == self.index:
                renne_cursor_rect = self.renne_cursor.get_rect()
                renne_cursor_rect.center = (screen_centerx - self.option_rect.width * 0.5,
                    menu_blit_y + self.option_rect.height * 0.5)
                screen.blit(self.renne_cursor, renne_cursor_rect)

                m_font = self.font_on
                m_color = self.color_on

            else:
                m_font = self.font_off
                m_color = self.color_off

            menu = m_font.render(menu_word, True, m_color)
            menu_rect = menu.get_rect()
            menu_rect.center = (screen_centerx, menu_blit_y + self.option_rect.height * 0.5)
            screen.blit(menu, menu_rect)

            menu_blit_y += self.option_rect.height



class Score(object):
    def __init__(self, score_setting):
        self.current_value = 0
        self.next_value = 0
        self.blit_pos = score_setting.get("blit_pos")
        self.font = score_setting.get("font")
        self.color = score_setting.get("color")
        self.score_run_rate = sfg.Achievement.SCORE_RUN_RATE


    def incr_next_value(self, delta):
        self.next_value += delta
        # change score_run_rate if delta is more than default value
        self.score_run_rate = max(delta, sfg.Achievement.SCORE_RUN_RATE)


    def update(self, passed_seconds):
        if self.current_value == self.next_value:
            return

        self.current_value += passed_seconds * self.score_run_rate
        self.current_value = min(self.current_value, self.next_value)


    def draw(self, camera, blit_pos=None):
        score = self.font.render(str(int(self.current_value)), True, self.color)
        if blit_pos is None:
            blit_pos = self.blit_pos
        camera.screen.blit(score, blit_pos)



def start_game(screen):
    bg_box.play(sfg.Music.START_GAME_KEY)

    pic = cg_image_controller.get(sfg.StartGame.PICTURE_IMAGE_KEY).convert()
    pic_rect = pic.get_rect()

    screen_centerx = sfg.Screen.SIZE[0] * 0.5
    pic_rect.centerx = screen_centerx
    pic_rect.top = sfg.StartGame.PICTURE_BLIT_Y

    clock = pygame.time.Clock()
    pic_alpha = 0 # picture fades in, alpha changes from 0 to 255
    fade_in_delta = 256 / sfg.StartGame.PICTURE_FADE_IN_TIME

    # check whether autosave data exists
    autosave = util.load_auto_save()
    if autosave is not None:
        for opt in sfg.Menu.START_GAME["options"]:
            if opt["mark"] == "load":
                opt["display"] = True

    menu = Menu(sfg.Menu.START_GAME)
    while True:
        screen.fill(pygame.Color("black"))

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed * 0.001
        if pic_alpha < 255:
            pic_alpha = int(min(pic_alpha + passed_seconds * fade_in_delta, 255))
        pic.set_alpha(pic_alpha)
        screen.blit(pic, pic_rect)

        for event in pygame.event.get():
            if pic_alpha < 255:
                continue
                # no events will be handled until the renne's picure is fully displayed
            if event.type == pygame.QUIT: 
                return {"status": cfg.GameControl.QUIT}
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    mark = menu.get_current_mark()
                    if mark == "load":
                        return {"status": cfg.GameControl.CONTINUE, "save": autosave}
                    elif mark == "start":
                        return {"status": cfg.GameControl.NEXT}
                    elif mark == "dead_mode":
                        return {"status": cfg.GameControl.DEAD_MODE}
                    elif mark == "quit":
                        return {"status": cfg.GameControl.QUIT}
                elif event.key == K_ESCAPE:
                    return {"status": cfg.GameControl.QUIT}

                menu.update(event.key)

        if pic_alpha == 255:
            menu.draw(screen)

        pygame.display.flip()



def loading_chapter_picture(screen):
    img = cg_image_controller.get(sfg.Chapter.LOADING_PICTURE_IMAGE_KEY).subsurface(
        sfg.Chapter.LOADING_PICTURE_RECT).convert()
    img_rect = img.get_rect()
    img_rect.center = sfg.Screen.SIZE[0] * 0.5, sfg.Screen.SIZE[1] * 0.45

    alpha = 0
    delta = 256 / sfg.Chapter.LOADING_PICTURE_FADE_IN_TIME
    clock = pygame.time.Clock()
    while alpha < 255:
        for event in pygame.event.get():
            # no event handle, avoiding "mouse stuck"
            pass

        screen.fill(pygame.Color("black"))
        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed * 0.001
        alpha = int(min(alpha + passed_seconds * delta, 255))
        img.set_alpha(alpha)
        screen.blit(img, img_rect)
        screen.blit(sfg.Chapter.LOADING_WORD, sfg.Chapter.LOADING_WORD_BLIT_POS)
        pygame.display.flip()



def show_the_end(screen):
    the_end_image = cg_image_controller.get(sfg.EndGame.THE_END_IMAGE_KEY).subsurface(
        sfg.EndGame.THE_END_IMAGE_RECT).convert()
    the_end_image_rect = the_end_image.get_rect()
    the_end_image_rect.center = sfg.Screen.SIZE[0] * 0.5, sfg.Screen.SIZE[1] * 0.4

    the_end_word = sfg.EndGame.THE_END_WORD
    the_end_word_rect = the_end_word.get_rect()
    the_end_word_rect.center = sfg.Screen.SIZE[0] * 0.5, sfg.Screen.SIZE[1] * 0.8

    mask_alpha = 255
    fade_in_delta = 256 / (sfg.EndGame.ENDING_FADEIN_TIME - sfg.EndGame.THE_END_SHOW_DELAY_TIME)
    delay_time = 0
    mask = sfg.Screen.DEFAULT_SURFACE
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

        screen.fill(pygame.Color("black"))
        screen.blit(the_end_image, the_end_image_rect)
        screen.blit(the_end_word, the_end_word_rect)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed * 0.001
        mask_alpha = int(max(mask_alpha - passed_seconds * fade_in_delta, 0))
        mask.fill(pygame.Color(0, 0, 0, mask_alpha))
        screen.blit(mask, (0, 0))

        pygame.display.flip()
        if mask_alpha == 0:
            delay_time += passed_seconds
            if delay_time > sfg.EndGame.THE_END_SHOW_DELAY_TIME:
                return



def show_chapter_win_screen_images(screen):
    # the chapter 0 is actually start menu
    chapters = sfg.GameMap.CHAPTERS[1:]
    for chapter in chapters:
        img = load_chapter_win_screen_image(chapter)
        if img is None:
            continue

        img_alpha = 0
        fade_in_delta = 256 / (sfg.EndGame.ENDING_FADEIN_TIME \
            - sfg.EndGame.CHAPTER_WIN_SCREEN_IMAGE_SHOW_DELAY_TIME)
        clock = pygame.time.Clock()
        img_show_delay_time = 0

        while True:
            screen.fill(pygame.Color("black"))

            time_passed = clock.tick(sfg.FPS)
            passed_seconds = time_passed * 0.001

            if img_alpha < 255:
                img_alpha = int(min(img_alpha + passed_seconds * fade_in_delta, 255))
            else:
                img_show_delay_time += passed_seconds
                if img_show_delay_time > sfg.EndGame.CHAPTER_WIN_SCREEN_IMAGE_SHOW_DELAY_TIME:
                    break

            img.set_alpha(img_alpha)
            screen.blit(img, (0, 0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    return True

            pygame.display.flip()



def end_game(screen):
    bg_box.play(sfg.Music.END_GAME_KEY, loops=0)

    quit_game = show_the_end(screen)
    if quit_game:
        return

    quit_game = show_chapter_win_screen_images(screen)
    if quit_game:
        return

    screen_centerx = sfg.Screen.SIZE[0] * 0.5

    renne_image = pygame.image.load(sfg.RENNE_IMAGE_FILENAME).convert_alpha()
    renne_image_rect = renne_image.get_rect()
    renne_image_rect.centerx = screen_centerx
    renne_image_rect.centery = sfg.EndGame.RENNE_IMAGE_BLIT_Y

    word = sfg.EndGame.BUSUNCLE_WORKS
    word_rect = word.get_rect()
    word_rect.centerx = screen_centerx
    word_rect.centery = sfg.EndGame.BUSUNCLE_WORKS_BLIT_Y

    mask_alpha = 255
    fade_in_delta = 256 / sfg.EndGame.ENDING_FADEIN_TIME
    mask = sfg.Screen.DEFAULT_SURFACE

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return

        screen.fill(pygame.Color("black"))
        screen.blit(renne_image, renne_image_rect)
        screen.blit(word, word_rect)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed * 0.001
        mask_alpha = int(max(mask_alpha - passed_seconds * fade_in_delta, 0))
        mask.fill(pygame.Color(0, 0, 0, mask_alpha))
        screen.blit(mask, (0, 0))

        pygame.display.flip()



class GameDirector(object):
    def __init__(self, chapter, hero, enemy_list):
        self.chapter = chapter
        self.win_cond = sfg.Chapter.WIN_CONDITION.get(self.chapter, sfg.Chapter.WIN_CONDITION_NONE)
        self.hero = hero
        self.enemy_list = enemy_list
        if self.win_cond == sfg.Chapter.WIN_CONDITION_BOSS_DIE:
            self.boss = None
            for em in self.enemy_list:
                if hasattr(em.setting, "IS_BOSS"):
                    self.boss = em
                    break

        self.status = cfg.GameStatus.INIT
        self.win_panel = gen_panel(battle_images, 
            sfg.GameStatus.HERO_WIN_PANEL_IMAGE_KEY, sfg.GameStatus.HERO_WIN_PANEL_RECT)
        self.lose_panel = gen_panel(battle_images, 
            sfg.GameStatus.HERO_LOSE_PANEL_IMAGE_KEY, sfg.GameStatus.HERO_LOSE_PANEL_RECT)
        self.chapter_score_icon = gen_panel(battle_images, 
            sfg.GameStatus.CHAPTER_SCORE_ICON_IMAGE_KEY, 
            sfg.GameStatus.CHAPTER_SCORE_ICON_RECT, 
            sfg.GameStatus.CHAPTER_SCORE_ICON_SCALE_SIZE)
        self.bonus_icon = gen_panel(battle_images, 
            sfg.GameStatus.BONUS_ICON_IMAGE_KEY, sfg.GameStatus.BONUS_ICON_RECT)
        self.chapter_score_line = gen_panel(battle_images, 
            sfg.GameStatus.CHAPTER_SCORE_LINE_IMAGE_KEY, 
            sfg.GameStatus.CHAPTER_SCORE_LINE_RECT, 
            sfg.GameStatus.CHAPTER_SCORE_LINE_SCALE_SIZE)
        self.numbers1 = gen_numbers(battle_images, sfg.GameStatus.NUMBER_IMAGE_KEY1, 
            sfg.GameStatus.NUMBER_RECT1, sfg.GameStatus.NUMBER_SIZE1)
        self.begin_timer = Timer()
        self.hero_status = HeroStatus(hero)
        self.achievement = Achievement(hero, enemy_list)
        self.menu = Menu(sfg.Menu.PAUSE)
        self.mask = sfg.Screen.DEFAULT_SURFACE

        bg_box.play("%s%s" % (sfg.Music.CHAPTER_KEY_PREFIX, chapter))


    def update(self, passed_seconds):
        if self.status == cfg.GameStatus.IN_PROGRESS:
            if self.hero.hp_status == cfg.HpStatus.DIE:
                # hero is dead, game over
                self.status = cfg.GameStatus.HERO_LOSE
                return

            if self.win_cond != sfg.Chapter.WIN_CONDITION_NONE and len(self.enemy_list) == 0:
                # all enemies are gone, hero win
                self.status = cfg.GameStatus.HERO_WIN
                self.achievement.cal_chapter_score()
                return 

        elif self.status == cfg.GameStatus.HERO_WIN:
            self.achievement.chapter_score.update(passed_seconds)

        if self.win_cond == sfg.Chapter.WIN_CONDITION_BOSS_DIE \
            and self.boss.hp_status == cfg.HpStatus.DIE:
            # in an chapter that boss die you win, kill all enemy when boss die
            for em in self.enemy_list:
                if em.hp > 0:
                    em.hp = 0
                    em.hp_status = cfg.HpStatus.DIE

        for em in self.enemy_list:
            if em.hp_status == cfg.HpStatus.DIE:
                can_be_removed = em.animation.dead_tick()
                if can_be_removed:
                    em.hp_status = cfg.HpStatus.VANISH
                    # kill the sprite from sprite groups containing it, but not chaning its internal status
                    em.kill()

        # achievement calculation here
        self.achievement.update(passed_seconds)


    def draw_count_down_number(self, camera, timer, persist_time):
        left_time = persist_time - timer.passed_time()
        number_to_draw = self.numbers1[int(left_time)+1]
        camera.screen.blit(number_to_draw, sfg.GameStatus.BEGIN_NUMBER_BLIT_POS)


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
                self.draw_count_down_number(camera, self.begin_timer, sfg.GameStatus.INIT_PERSIST_TIME)

        elif self.status in cfg.GameStatus.STATUS_WITH_MASK:
            self.mask.fill(sfg.Stuff.MASK_ALPHA_128)
            camera.screen.blit(self.mask, (0, 0))

            if self.status == cfg.GameStatus.HERO_WIN:
                camera.screen.blit(self.achievement.kill_icon, sfg.GameStatus.CHAPTER_KILL_ICON_BLIT_POS)
                camera.screen.blit(self.achievement.n_hit_icon, sfg.GameStatus.CHAPTER_N_HIT_ICON_BLIT_POS)
                camera.screen.blit(self.achievement.n_kill_icon, sfg.GameStatus.CHAPTER_N_KILL_ICON_BLIT_POS)
                camera.screen.blit(self.chapter_score_line, sfg.GameStatus.CHAPTER_SCORE_LINE_BLIT_POS)
                camera.screen.blit(self.chapter_score_icon, sfg.GameStatus.CHAPTER_SCORE_ICON_BLIT_POS)
                camera.screen.blit(self.win_panel, sfg.GameStatus.HERO_WIN_BLIT_POS)
                camera.screen.blit(self.bonus_icon, sfg.GameStatus.BONUS_ICON_BLIT_POS1)
                camera.screen.blit(self.bonus_icon, sfg.GameStatus.BONUS_ICON_BLIT_POS2)
                screen_draw_y_symmetric(camera, sfg.GameStatus.CHAPTER_NEXT, 
                    sfg.GameStatus.CHAPTER_NEXT_BLIT_Y)

                self.achievement.kill_score.draw(camera, sfg.GameStatus.CHAPTER_KILL_BLIT_POS)
                self.achievement.n_hit_score.draw(camera, sfg.GameStatus.CHAPTER_N_HIT_BLIT_POS)
                self.achievement.n_kill_score.draw(camera, sfg.GameStatus.CHAPTER_N_KILL_BLIT_POS)
                self.achievement.chapter_score.draw(camera)

                if bg_box.current_playing != sfg.Music.HERO_WIN_KEY:
                    bg_box.play(sfg.Music.HERO_WIN_KEY, 0)

            elif self.status == cfg.GameStatus.HERO_LOSE:
                camera.screen.blit(self.lose_panel, sfg.GameStatus.HERO_LOSE_BLIT_POS)
                screen_draw_y_symmetric(camera, sfg.GameStatus.CHAPTER_AGAIN, 
                    sfg.GameStatus.CHAPTER_AGAIN_BLIT_Y)
                if bg_box.current_playing != sfg.Music.HERO_LOSE_KEY:
                    bg_box.play(sfg.Music.HERO_LOSE_KEY, 0)
            
            elif self.status == cfg.GameStatus.PAUSE:
                self.menu.draw(camera.screen)



class HeroStatus(object):
    def __init__(self, hero):
        self.hero = hero
        self.head_images_list = self.gen_head_images_list()
        self.status_panel = gen_panel(battle_images, sfg.SpriteStatus.HERO_PANEL_IMAGE_KEY, 
            sfg.SpriteStatus.HERO_PANEL_RECT, sfg.SpriteStatus.HERO_PANEL_SCALE_SIZE)
        self.hero_hp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE).convert_alpha()
        self.hero_mp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE).convert_alpha()
        self.hero_sp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE).convert_alpha()
        self.hero_exp_bar = pygame.Surface(sfg.SpriteStatus.HERO_ALL_BAR_SIZE).convert_alpha()
        # skill icons 
        self.magic_skill_1_icon = gen_panel(effect_image_controller, 
            sfg.SpriteStatus.MAGIC_SKILL_1_ICON_IMAGE_KEY, 
            sfg.SpriteStatus.MAGIC_SKILL_1_ICON_RECT)
        self.magic_skill_2_icon = gen_panel(effect_image_controller, 
            sfg.SpriteStatus.MAGIC_SKILL_2_ICON_IMAGE_KEY, 
            sfg.SpriteStatus.MAGIC_SKILL_2_ICON_RECT)
        self.magic_skill_3_icon = gen_panel(effect_image_controller,
            sfg.SpriteStatus.MAGIC_SKILL_3_ICON_IMAGE_KEY, 
            sfg.SpriteStatus.MAGIC_SKILL_3_ICON_RECT)
        self.magic_skill_4_icon = gen_panel(effect_image_controller,
            sfg.SpriteStatus.MAGIC_SKILL_4_ICON_IMAGE_KEY,
            sfg.SpriteStatus.MAGIC_SKILL_4_ICON_RECT)
        self.skill_icon_frame = gen_panel(battle_images, sfg.SpriteStatus.SKILL_ICON_FRAME_IMAGE_KEY,
            sfg.SpriteStatus.SKILL_ICON_FRAME_RECT, sfg.SpriteStatus.SKILL_ICON_SIZE)


    def gen_head_images_list(self):
        # generate the head image in status panel for Renne
        res = []
        w, h = sfg.SpriteStatus.HERO_HEAD_SIZE
        for row in (0, 1):
            for column in (0, 1):
                res.append(battle_images.get(
                    sfg.SpriteStatus.HERO_HEAD_IMAGE_KEY).convert_alpha().subsurface(
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


    def draw_skill_icon_mask(self, camera, icon_width, blit_pos, cd, cd_left):
        # icon is suppose to be square, so width equals height, just use width is ok
        w = icon_width
        point_list = [(0.5 * w, 0), (0.5 * w, 0.5 * w)]
        size_len = w * 4
        left_ratio = float(cd_left) / cd
        if left_ratio < 0.125:
            # less than 1 / 8 of size_len
            point_list.append(((0.125 - left_ratio) * size_len, 0))
        elif left_ratio < 0.375:
            # more than 1 / 8 and less than 3 / 8
            point_list.append((0, (left_ratio - 0.125) * size_len))
            point_list.append((0, 0))
        elif left_ratio < 0.625:
            # more than 3 / 8 and less than 5 / 8
            point_list.append(((left_ratio - 0.375) * size_len, w))
            point_list.extend([(0, w), (0, 0)])
        elif left_ratio < 0.875:
            # more than 5 / 8 and less than 7 / 8
            point_list.append((w, (0.875 - left_ratio) * size_len))
            point_list.extend([(w, w), (0, w), (0, 0)])
        else:
            # more than 7 / 8
            point_list.append(((1.125 - left_ratio) * size_len, 0))
            point_list.extend([(w, 0), (w, w), (0, w), (0, 0)])
    
        sf = pygame.Surface((w, w)).convert_alpha()
        pygame.draw.polygon(sf, sfg.SpriteStatus.SKILL_CD_MASK_COLOR, point_list)
        camera.screen.blit(sf, blit_pos, special_flags=BLEND_ADD)


    def draw(self, camera):
        # panel first, other things over it
        camera.screen.blit(self.status_panel, sfg.SpriteStatus.HERO_PANEL_BLIT_POS)

        # hero's head, showing her status
        camera.screen.blit(self.get_current_head(self.hero.hp_status), sfg.SpriteStatus.HERO_HEAD_BLIT_POS)

        # hp, mp, sp words
        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_hp"], sfg.SpriteStatus.HERO_HP_TITLE_BLIT_POS)
        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_mp"], sfg.SpriteStatus.HERO_MP_TITLE_BLIT_POS)
        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_sp"], sfg.SpriteStatus.HERO_SP_TITLE_BLIT_POS)
        camera.screen.blit(sfg.SpriteStatus.WORDS["hero_exp"], sfg.SpriteStatus.HERO_EXP_TITTLE_BLIT_POS)

        # level title is not a constant, read it from hero
        level_title = sfg.SpriteStatus.LEVEL_TITLE_FONT.render("LV%s" % self.hero.level, True, 
            sfg.SpriteStatus.LEVEL_TITLE_COLOR)
        camera.screen.blit(level_title, sfg.SpriteStatus.HERO_LEVEL_BLIT_POS)

        # draw the hp bar for Renne
        self.draw_hero_bar(camera, self.hero.hp, self.hero.setting.HP, self.hero_hp_bar, 
            sfg.SpriteStatus.SPRITE_HP_COLORS[self.hero.hp_status], 
            sfg.SpriteStatus.HERO_HP_BLIT_POS)

        # draw the mp bar for Renne
        self.draw_hero_bar(camera, self.hero.mp, self.hero.setting.MP, self.hero_mp_bar,
            sfg.SpriteStatus.HERO_MP_COLOR, sfg.SpriteStatus.HERO_MP_BLIT_POS)

        # draw the sp bar for Renne
        self.draw_hero_bar(camera, self.hero.sp, self.hero.setting.SP, self.hero_sp_bar,
            sfg.SpriteStatus.HERO_SP_COLOR, sfg.SpriteStatus.HERO_SP_BLIT_POS)

        # draw the level bar for Renne
        last_exp = self.hero.setting.LEVEL_EXP[self.hero.level - 1]
        if self.hero.level < self.hero.setting.MAX_LEVEL:
            next_exp = self.hero.setting.LEVEL_EXP[self.hero.level]
            self.draw_hero_bar(camera, self.hero.exp - last_exp, next_exp - last_exp, self.hero_exp_bar,
                sfg.SpriteStatus.HERO_EXP_COLOR, sfg.SpriteStatus.HERO_EXP_BLIT_POS)
        else:
            self.draw_hero_bar(camera, 1, 1, self.hero_exp_bar,
                sfg.SpriteStatus.HERO_EXP_COLOR, sfg.SpriteStatus.HERO_EXP_BLIT_POS)

        # draw skill icons
        camera.screen.blit(self.magic_skill_1_icon, sfg.SpriteStatus.MAGIC_SKILL_1_ICON_BLIT_POS)
        camera.screen.blit(self.magic_skill_2_icon, sfg.SpriteStatus.MAGIC_SKILL_2_ICON_BLIT_POS)
        camera.screen.blit(self.magic_skill_3_icon, sfg.SpriteStatus.MAGIC_SKILL_3_ICON_BLIT_POS)
        camera.screen.blit(self.magic_skill_4_icon, sfg.SpriteStatus.MAGIC_SKILL_4_ICON_BLIT_POS)

        # draw skill icon masks, if it is in cd status
        cds = self.hero.attacker.magic_cds
        if cds["magic_skill_1"] > 0:
            self.draw_skill_icon_mask(camera, self.magic_skill_1_icon.get_width(), 
                sfg.SpriteStatus.MAGIC_SKILL_1_ICON_BLIT_POS,
                self.hero.attacker.magic_skill_1_params["cd"], cds["magic_skill_1"])
        if cds["magic_skill_2"] > 0:
            self.draw_skill_icon_mask(camera, self.magic_skill_2_icon.get_width(),
                sfg.SpriteStatus.MAGIC_SKILL_2_ICON_BLIT_POS,
                self.hero.attacker.magic_skill_2_params["cd"], cds["magic_skill_2"])
        if cds["magic_skill_3"] > 0:
            self.draw_skill_icon_mask(camera, self.magic_skill_3_icon.get_width(),
                sfg.SpriteStatus.MAGIC_SKILL_3_ICON_BLIT_POS,
                self.hero.attacker.magic_skill_3_params["cd"], cds["magic_skill_3"])
        if cds["magic_skill_4"] > 0:
            self.draw_skill_icon_mask(camera, self.magic_skill_4_icon.get_width(),
                sfg.SpriteStatus.MAGIC_SKILL_4_ICON_BLIT_POS,
                self.hero.attacker.magic_skill_4_params["cd"], cds["magic_skill_4"])

        # draw the frame of skill icons
        for blit_pos in (sfg.SpriteStatus.MAGIC_SKILL_1_ICON_BLIT_POS,
            sfg.SpriteStatus.MAGIC_SKILL_2_ICON_BLIT_POS, 
            sfg.SpriteStatus.MAGIC_SKILL_3_ICON_BLIT_POS,
            sfg.SpriteStatus.MAGIC_SKILL_4_ICON_BLIT_POS):
            camera.screen.blit(self.skill_icon_frame, blit_pos)



class Achievement(object):
    def __init__(self, hero, enemy_list):
        self.hero = hero
        self.enemy_list = enemy_list
        self.n_kill_list = []
        self.kill_time_list = []
        self.kill_icon = gen_panel(battle_images, 
            sfg.Achievement.KILL_ICON_IMAGE_KEY, sfg.Achievement.KILL_ICON_RECT)
        self.n_hit_icon = gen_panel(battle_images, 
            sfg.Achievement.N_HIT_ICON_IMAGE_KEY, sfg.Achievement.N_HIT_ICON_RECT)
        self.n_kill_icon = gen_panel(battle_images, 
            sfg.Achievement.N_KILL_ICON_IMAGE_KEY, sfg.Achievement.N_KILL_ICON_RECT)

        self.kill_score = Score(sfg.Achievement.KILL_SCORE)
        self.n_hit_score = Score(sfg.Achievement.N_HIT_SCORE)
        self.n_kill_score = Score(sfg.Achievement.N_KILL_SCORE)
        self.chapter_score = Score(sfg.GameStatus.CHAPTER_SCORE)

        self.score_panel = gen_panel(battle_images, 
            sfg.Achievement.SCORE_PANEL_IMAGE_KEY, sfg.Achievement.SCORE_PANEL_RECT,
            sfg.Achievement.SCORE_PANEL_SCALE_SIZE)


    def cal_chapter_score(self):
        # only call incr_next_value one for chapter score
        score = self.kill_score.next_value + self.n_hit_score.next_value + self.n_kill_score.next_value
        self.chapter_score.incr_next_value(score)


    def update(self, passed_seconds):
        # calculate n_hit
        if len(self.hero.attacker.hit_record) > 0:
            for record in self.hero.attacker.hit_record:
                score = sfg.Achievement.SCORE["per_hit"] * sum(range(1, record["n_hit"] + 1))
                self.n_hit_score.incr_next_value(score)

            self.hero.attacker.hit_record = []

        # calculate n_kill
        if len(self.hero.attacker.kill_record) > 0:
            for record in self.hero.attacker.kill_record:
                self.kill_score.incr_next_value(sfg.Achievement.SCORE["per_kill"])
                self.kill_time_list.append(record["time"])
                if len(self.kill_time_list) == 1:
                    self.n_kill_list.append(1)
                else:
                    if self.kill_time_list[-1] - self.kill_time_list[-2] <= sfg.Achievement.N_KILL_TIMEDELTA:
                        n_kill = self.n_kill_list[-1] + 1
                        self.n_kill_list.append(n_kill)
                        score = sfg.Achievement.SCORE["per_n_kill"] * 2 * n_kill
                        self.n_kill_score.incr_next_value(score)
                    else:
                        self.n_kill_list.append(1)

            self.hero.attacker.kill_record = []

        self.kill_score.update(passed_seconds)
        self.n_hit_score.update(passed_seconds)
        self.n_kill_score.update(passed_seconds)


    def draw(self, camera):
        camera.screen.blit(self.score_panel, sfg.Achievement.SCORE_PANEL_BLIT_POS1)
        camera.screen.blit(self.score_panel, sfg.Achievement.SCORE_PANEL_BLIT_POS2)
        camera.screen.blit(self.score_panel, sfg.Achievement.SCORE_PANEL_BLIT_POS3)
        camera.screen.blit(self.kill_icon, sfg.Achievement.KILL_ICON_BLIT_POS)
        camera.screen.blit(self.n_hit_icon, sfg.Achievement.N_HIT_ICON_BLIT_POS)
        camera.screen.blit(self.n_kill_icon, sfg.Achievement.N_KILL_ICON_BLIT_POS)
        self.kill_score.draw(camera)
        self.n_hit_score.draw(camera)
        self.n_kill_score.draw(camera)
