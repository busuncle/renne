import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSpritesGroup, enemy_in_one_screen
import etc.setting as sfg
import etc.constant as cfg
import etc.ai_setting as ai
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from gamestatus import GameStatus
from achievement import Achievement
from musicbox import BackgroundBox
from animation import cg_image_controller, basic_image_controller
from renderer import Camera
import debug_tools
from base import util



screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
bg_box = BackgroundBox(sfg.Music.BACKGROUND_VOLUME)
pygame.display.set_caption("Renne")
pygame.display.set_icon(pygame.image.load("renne.png").convert_alpha())


COMMAND_DEBUG_MODE = False
COMMAND_DEBUG_OPTIONS = {}


def select_menu(key, menu_list, menu_index):
    # return a new menu_index that satisfies: 0 <= menu_index <= len(menu_list) - 1
    if key in (sfg.UserKey.DOWN, K_DOWN):
        return min(menu_index + 1, len(menu_list) - 1)
    elif key in (sfg.UserKey.UP, K_UP):
        return max(0, menu_index - 1)
    return menu_index


def render_menu(screen, menu_index, menu_list, menu_option_rect_setting, menu_blit_y,
        font_on, font_off, color_on, color_off):
    renne_cursor = basic_image_controller.get("head_status").subsurface(
        pygame.Rect(sfg.StartGame.RENNE_CURSOR_RECT)).convert_alpha()
    menu_option_rect = pygame.Rect(menu_option_rect_setting)
    screen_centerx = sfg.Screen.SIZE[0] / 2
    for i, menu_word in enumerate(menu_list):
        if i == menu_index:
            renne_cursor_rect = renne_cursor.get_rect()
            renne_cursor_rect.center = (screen_centerx - menu_option_rect.width / 2,
                menu_blit_y + menu_option_rect.height / 2)
            screen.blit(renne_cursor, renne_cursor_rect)

            m_font = font_on
            m_color = color_on

        else:
            m_font = font_off
            m_color = color_off

        menu = m_font.render(menu_word, True, m_color)
        menu_rect = menu.get_rect()
        menu_rect.center = (screen_centerx, menu_blit_y + menu_option_rect.height / 2)
        screen.blit(menu, menu_rect)

        menu_blit_y += menu_option_rect.height


def main(args):
    # a Renne singleton goes through the whole game
    renne = Renne(sfg.Renne, (0, 0), 0)

    if args.chapter is not None:
        # it's for debuging, only run 1 part and return immediately
        if args.chapter == 0:
            start_game(screen)
        elif args.chapter == -1:
            end_game(screen)
        else:
            enter_chapter(screen, args.chapter, renne)
        return

    i = 0
    while i < len(sfg.GameMap.CHAPTERS):
        if i == 0:
            # chapter 0 means the main menu
            status = start_game(screen)
        else:
            chapter = sfg.GameMap.CHAPTERS[i]
            loading_chapter_picture(screen)
            status = enter_chapter(screen, chapter, renne)
            # TODO: auto save here

        bg_box.stop()

        if status == cfg.GameControl.NEXT:
            i += 1
            # TODO: recover renne's status(eg. hp, sp) here
        elif status == cfg.GameControl.AGAIN:
            continue
        elif status == cfg.GameControl.MAIN:
            i = 0
        elif status == cfg.GameControl.QUIT:
            return

    end_game(screen)


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



def start_game(screen):
    bg_box.play("start_game")

    pic = cg_image_controller.get("start_game").convert()
    pic_rect = pic.get_rect()

    screen_centerx = sfg.Screen.SIZE[0] / 2
    pic_rect.centerx = screen_centerx
    pic_rect.top = sfg.StartGame.PICTURE_BLIT_Y

    clock = pygame.time.Clock()
    menu_index = 0
    pic_alpha = 0 # picture fades in, alpha changes from 0 to 255
    fade_in_delta = 256 / sfg.StartGame.PICTURE_FADE_IN_TIME

    menu_option_rect = pygame.Rect(sfg.StartGame.MENU_OPTION_RECT)
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
                        if sfg.StartGame.MENU_LIST[menu_index] == "START":
                            return cfg.GameControl.NEXT
                        elif sfg.StartGame.MENU_LIST[menu_index] == "QUIT":
                            return cfg.GameControl.QUIT
                    elif event.key == K_ESCAPE:
                        return cfg.GameControl.QUIT

                    # 0 <= menu_index <= len(menu_list) - 1
                    menu_index = select_menu(event.key, sfg.StartGame.MENU_LIST, menu_index)

            render_menu(screen, menu_index, sfg.StartGame.MENU_LIST, sfg.StartGame.MENU_OPTION_RECT,
                sfg.StartGame.MENU_BLIT_Y, sfg.StartGame.MENU_ON_FONT, sfg.StartGame.MENU_OFF_FONT,
                sfg.StartGame.MENU_ON_COLOR, sfg.StartGame.MENU_OFF_COLOR)

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
    mask = pygame.Surface(sfg.Screen.SIZE).convert_alpha()

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



def enter_chapter(screen, chapter, renne):
    bg_box.play("chapter_%s" % chapter)
    clock = pygame.time.Clock()
    map_setting = util.load_map_setting(chapter)

    camera = Camera(screen, map_size=map_setting["size"])
    game_world = GameWorld()
    allsprites = GameSpritesGroup()
    enemies = GameSpritesGroup()
    static_objects = GameStaticObjectGroup()
    game_map = GameMap(chapter, map_setting["size"], map_setting["tiles"])

    # load hero
    #renne = Renne(sfg.Renne, *map_setting["hero"])
    renne.place(*map_setting["hero"])
    renne.activate(allsprites, enemies, static_objects, game_map)

    # load monsters
    monster_init = map_setting["monsters"]
    for monster_id, pos, direct in monster_init:
        monster = Enemy(sfg.SPRITE_SETTING_MAPPING[monster_id], pos, direct)
        monster.activate(ai.NormalAI, allsprites, renne, static_objects, game_map)

        enemies.add(monster)

    # load static objects
    chapter_static_objects = map_setting["static_objects"]
    for t, p in chapter_static_objects:
        static_obj = GameStaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[t], p)
        static_objects.add(static_obj)

    allsprites.add(renne)
    allsprites.add(enemies)

    game_world.add(allsprites)
    game_world.add(static_objects)

    game_status = GameStatus(chapter, renne, enemies)
    game_achievement = Achievement(renne, enemies)

    menu_index = 0
    running = True
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                exit(0)

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if game_status.status == cfg.GameStatus.IN_PROGRESS:
                        game_status.status = cfg.GameStatus.PAUSE
                        bg_box.pause()
                        menu_index = 0
                    elif game_status.status == cfg.GameStatus.PAUSE:
                        game_status.status = cfg.GameStatus.IN_PROGRESS
                        bg_box.unpause()

                if event.key == K_RETURN:
                    if game_status.status == cfg.GameStatus.HERO_WIN:
                        return cfg.GameControl.NEXT
                    elif game_status.status == cfg.GameStatus.HERO_LOSE:
                        return cfg.GameControl.AGAIN
                    elif game_status.status == cfg.GameStatus.PAUSE:
                        if sfg.Chapter.PAUSE_MENU_LIST[menu_index] == "CONTINUE":
                            game_status.status = cfg.GameStatus.IN_PROGRESS
                            bg_box.unpause()
                        elif sfg.Chapter.PAUSE_MENU_LIST[menu_index] == "MAIN":
                            return cfg.GameControl.MAIN
                        elif sfg.Chapter.PAUSE_MENU_LIST[menu_index] == "QUIT":
                            return cfg.GameControl.QUIT

                if game_status.status == cfg.GameStatus.PAUSE:
                    menu_index = select_menu(event.key, sfg.Chapter.PAUSE_MENU_LIST, menu_index)

        pressed_keys = pygame.key.get_pressed()
        renne.event_handle(pressed_keys, external_event=game_status.status)

        for enemy in filter(lambda x: enemy_in_one_screen(renne, x), enemies):
            enemy.event_handle(pressed_keys, external_event=game_status.status)

        game_map.draw(camera)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0

        # update renne, enemies, game_status, game_achievement in sequence
        renne.update(passed_seconds, external_event=game_status.status)
        for enemy in enemies:
            if enemy_in_one_screen(renne, enemy):
                enemy.update(passed_seconds, external_event=game_status.status)

        game_status.update()
        game_achievement.update()

        camera.screen_follow(renne.pos)

        game_world.draw(camera)
        game_status.draw(camera)

        if COMMAND_DEBUG_MODE or sfg.DEBUG_MODE:
            debug_tools.run_debug_by_option_list(COMMAND_DEBUG_OPTIONS,
                camera, game_world, game_map, clock)

        if game_status.status == cfg.GameStatus.PAUSE:
            mask = pygame.Surface(sfg.Screen.SIZE).convert_alpha()
            mask.fill(pygame.Color(0, 0, 0, 128))
            screen.blit(mask, (0, 0))

            # draw the pause menu
            render_menu(screen, menu_index, sfg.Chapter.PAUSE_MENU_LIST, sfg.Chapter.PAUSE_MENU_OPTION_RECT,
                sfg.Chapter.PAUSE_MENU_BLIT_Y, sfg.Chapter.PAUSE_MENU_ON_FONT, sfg.Chapter.PAUSE_MENU_OFF_FONT,
                sfg.Chapter.PAUSE_MENU_ON_COLOR, sfg.Chapter.PAUSE_MENU_OFF_COLOR)

        elif game_status.status == cfg.GameStatus.HERO_WIN:
            if bg_box.current_playing != "hero_win":
                bg_box.stop()
                # TODO: may play some other background music here
        elif game_status.status == cfg.GameStatus.HERO_LOSE:
            if bg_box.current_playing != "hero_lose":
                bg_box.stop()
                # TODO: may play some other background music here


        pygame.display.flip()



if __name__ == "__main__":
    args = util.parse_command_line([
        (["-d", "--debug"], {"dest": "debug", "action": "store_true"}),
        (["-c", "--chapter"], {"dest": "chapter", "action": "store", "type": int}),
        (["--fps"], {"dest": "fps", "action": "store_true"}),
        (["--waypoints"], {"dest": "waypoints", "action": "store_true"}),
        (["--area"], {"dest": "area", "action": "store_true"}),
        (["--pos"], {"dest": "pos", "action": "store_true"}),
    ])
    COMMAND_DEBUG_MODE = args.debug is True
    COMMAND_DEBUG_OPTIONS["waypoints"] = args.waypoints
    COMMAND_DEBUG_OPTIONS["fps"] = args.fps
    COMMAND_DEBUG_OPTIONS["area"] = args.area
    COMMAND_DEBUG_OPTIONS["pos"] = args.pos

    main(args)

