from time import time
import pygame
from pygame.locals import *
from pygame.transform import smoothscale, scale2x
from animation import cg_image_controller, basic_image_controller
from musicbox import BackgroundBox
from base.util import ImageController
import etc.setting as sfg
import etc.constant as cfg
from base.util import Timer



bg_box = BackgroundBox(sfg.Music.BACKGROUND_VOLUME)

battle_images = ImageController(sfg.BATTLE_IMAGES[0])
battle_images.add_from_list(sfg.BATTLE_IMAGES[1])



def screen_draw_y_symmetric(camera, blit_surface, y):
    # given y, draw the surface to screen that it's y-axis symmetric
    r = blit_surface.get_rect()
    r.centerx = camera.size[0] / 2
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
        self.options = menu_setting["options"]
        self.option_rect = pygame.Rect(menu_setting["option_rect"])
        self.blit_y = menu_setting["blit_y"]
        self.font_on = menu_setting["font_on"]
        self.font_off = menu_setting["font_off"]
        self.color_on = menu_setting["color_on"]
        self.color_off = menu_setting["color_off"]
        self.renne_cursor = basic_image_controller.get("head_status").subsurface(
            pygame.Rect(sfg.Menu.RENNE_CURSOR_RECT)).convert_alpha()


    def current_menu(self):
        return self.options[self.index]


    def update(self, key):
        # 0 <= menu_index <= len(menu_list) - 1
        if key in (sfg.UserKey.DOWN, K_DOWN):
            self.index = min(self.index + 1, len(self.options) - 1)
        elif key in (sfg.UserKey.UP, K_UP):
            self.index = max(0, self.index - 1)


    def draw(self, screen):
        menu_blit_y = self.blit_y
        screen_centerx = sfg.Screen.SIZE[0] / 2
        for i, menu_word in enumerate(self.options):
            if i == self.index:
                renne_cursor_rect = self.renne_cursor.get_rect()
                renne_cursor_rect.center = (screen_centerx - self.option_rect.width / 2,
                    menu_blit_y + self.option_rect.height / 2)
                screen.blit(self.renne_cursor, renne_cursor_rect)

                m_font = self.font_on
                m_color = self.color_on

            else:
                m_font = self.font_off
                m_color = self.color_off

            menu = m_font.render(menu_word, True, m_color)
            menu_rect = menu.get_rect()
            menu_rect.center = (screen_centerx, menu_blit_y + self.option_rect.height / 2)
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
    bg_box.play("start_game")

    pic = cg_image_controller.get("start_game").convert()
    pic_rect = pic.get_rect()

    screen_centerx = sfg.Screen.SIZE[0] / 2
    pic_rect.centerx = screen_centerx
    pic_rect.top = sfg.StartGame.PICTURE_BLIT_Y

    clock = pygame.time.Clock()
    pic_alpha = 0 # picture fades in, alpha changes from 0 to 255
    fade_in_delta = 256 / sfg.StartGame.PICTURE_FADE_IN_TIME

    menu = Menu(sfg.Menu.START_GAME)
    while True:
        screen.fill(pygame.Color("black"))

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0
        pic_alpha = int(min(pic_alpha + passed_seconds * fade_in_delta, 255))
        pic.set_alpha(pic_alpha)
        screen.blit(pic, pic_rect)

        if pic_alpha >= 255:
            # no events accepted until the renne's picure is fully displayed
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    return cfg.GameControl.QUIT
                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        if menu.current_menu() == "START":
                            return cfg.GameControl.NEXT
                        elif menu.current_menu() == "QUIT":
                            return cfg.GameControl.QUIT
                    elif event.key == K_ESCAPE:
                        return cfg.GameControl.QUIT

                    menu.update(event.key)

            menu.draw(screen)

        pygame.display.flip()



def loading_chapter_picture(screen):
    img = cg_image_controller.get("loading_chapter").convert()
    img_rect = img.get_rect()
    img_rect.center = map(lambda x: x/2, sfg.Screen.SIZE)

    alpha = 0
    delta = 256 / sfg.Chapter.LOADING_PICTURE_FADE_IN_TIME
    clock = pygame.time.Clock()
    while alpha < 255:
        screen.fill(pygame.Color("black"))
        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0
        alpha = int(min(alpha + passed_seconds * delta, 255))
        img.set_alpha(alpha)
        screen.blit(img, img_rect)
        screen.blit(sfg.Chapter.LOADING_WORD, sfg.Chapter.LOADING_WORD_BLIT_POS)
        pygame.display.flip()



def end_game(screen):
    bg_box.play("end_game")

    screen_centerx = sfg.Screen.SIZE[0] / 2

    renne_image = pygame.image.load("renne.png").convert_alpha()
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
                exit(0)
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    exit(0)

        screen.fill(pygame.Color("black"))
        screen.blit(renne_image, renne_image_rect)
        screen.blit(word, word_rect)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0
        mask_alpha = int(max(mask_alpha - passed_seconds * fade_in_delta, 0))
        mask.fill(pygame.Color(0, 0, 0, mask_alpha))
        screen.blit(mask, (0, 0))

        pygame.display.flip()



class GameStatus(object):
    def __init__(self, chapter, hero, enemy_list):
        self.chapter = chapter
        self.hero = hero
        self.enemy_list = enemy_list
        self.status = cfg.GameStatus.INIT
        self.win_panel = gen_panel(battle_images, "status2", sfg.GameStatus.HERO_WIN_PANEL_RECT)
        self.lose_panel = gen_panel(battle_images, "status2", sfg.GameStatus.HERO_LOSE_PANEL_RECT)
        self.chapter_score_icon = gen_panel(battle_images, "status2", 
            sfg.GameStatus.CHAPTER_SCORE_ICON_RECT, sfg.GameStatus.CHAPTER_SCORE_ICON_SCALE_SIZE)
        self.bonus_icon = gen_panel(battle_images, "status6", sfg.GameStatus.BONUS_ICON_RECT)
        self.chapter_score_line = gen_panel(battle_images, "status3", 
            sfg.GameStatus.CHAPTER_SCORE_LINE_RECT, sfg.GameStatus.CHAPTER_SCORE_LINE_SCALE_SIZE)
        self.numbers1 = gen_numbers(battle_images, "status4", 
            sfg.GameStatus.NUMBER_RECT1, sfg.GameStatus.NUMBER_SIZE1)
        self.begin_timer = Timer()
        self.hero_status = HeroStatus(hero)
        self.achievement = Achievement(hero, enemy_list)
        self.menu = Menu(sfg.Menu.PAUSE)
        self.mask = sfg.Screen.DEFAULT_SURFACE

        bg_box.play("chapter_%s" % chapter)


    def update(self, passed_seconds):
        if self.status == cfg.GameStatus.IN_PROGRESS:
            if self.hero.status["hp"] == cfg.SpriteStatus.DIE:
                # hero is dead, game over
                self.status = cfg.GameStatus.HERO_LOSE
                return

            if len(self.enemy_list) == 0:
                # all enemies are gone, hero win
                self.status = cfg.GameStatus.HERO_WIN
                # only call incr_next_value one for chapter score
                score = self.achievement.kill_score.current_value \
                    + self.achievement.n_hit_score.current_value \
                    + self.achievement.n_kill_score.current_value
                self.achievement.chapter_score.incr_next_value(score)
                return 

        elif self.status == cfg.GameStatus.HERO_WIN:
            self.achievement.chapter_score.update(passed_seconds)

        remove_list = []
        for em in self.enemy_list:
            if em.status["hp"] == cfg.SpriteStatus.DIE:
                can_be_removed = em.animation.death_tick()
                if can_be_removed:
                    remove_list.append(em)

        for em in remove_list:
            self.enemy_list.remove(em)

        # achievement calculation here
        self.achievement.update(passed_seconds)


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

        elif self.status != cfg.GameStatus.IN_PROGRESS:
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

                if bg_box.current_playing != "hero_win":
                    bg_box.play("hero_win", 0)

            elif self.status == cfg.GameStatus.HERO_LOSE:
                camera.screen.blit(self.lose_panel, sfg.GameStatus.HERO_LOSE_BLIT_POS)
                screen_draw_y_symmetric(camera, sfg.GameStatus.CHAPTER_AGAIN, 
                    sfg.GameStatus.CHAPTER_AGAIN_BLIT_Y)
                if bg_box.current_playing != "hero_lose":
                    bg_box.play("hero_lose", 0)
            
            elif self.status == cfg.GameStatus.PAUSE:
                self.menu.draw(camera.screen)



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
        self.n_kill_list = []
        self.kill_time_list = []
        self.kill_icon = gen_panel(battle_images, "status5", sfg.Achievement.KILL_ICON_RECT)
        self.n_hit_icon = gen_panel(battle_images, "status5", sfg.Achievement.N_HIT_ICON_RECT)
        self.n_kill_icon = gen_panel(battle_images, "status5", sfg.Achievement.N_KILL_ICON_RECT)
        self.numbers2 = gen_numbers(battle_images, "icon1", sfg.GameStatus.NUMBER_RECT2, sfg.GameStatus.NUMBER_SIZE2)

        self.kill_score = Score(sfg.Achievement.KILL_SCORE)
        self.n_hit_score = Score(sfg.Achievement.N_HIT_SCORE)
        self.n_kill_score = Score(sfg.Achievement.N_KILL_SCORE)
        self.chapter_score = Score(sfg.GameStatus.CHAPTER_SCORE)

        self.score_panel = gen_panel(battle_images, "status", sfg.Achievement.SCORE_PANEL_RECT,
            sfg.Achievement.SCORE_PANEL_SCALE_SIZE)


    def update(self, passed_seconds):
        # calculate n_hit
        if len(self.hero.attacker.hit_record) > 0:
            for record in self.hero.attacker.hit_record:
                score = sfg.Achievement.SCORE["per_hit"] * sum(range(1, record["n_hit"] + 1))
                self.n_hit_score.incr_next_value(score)
                print "%s hit!" % record["n_hit"]

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
                        print "%s kill!" % self.n_kill_list[-1]
                        score = sfg.Achievement.SCORE["per_n_kill"] * pow(2, n_kill)
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
