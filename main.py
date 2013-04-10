import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSpritesGroup, enemy_in_one_screen
import etc.setting as sfg
import etc.constant as cfg
import etc.ai_setting as ai
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from gamestatus import GameStatus
from animation import cg_image_controller, basic_image_controller
from renderer import Camera
import debug_tools
from base import util



screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne")
pygame.display.set_icon(pygame.image.load("renne.png").convert_alpha())


COMMAND_DEBUG_MODE = False


def select_menu(key, menu_list, menu_index):
    # return a new menu_index that satisfies: 0 <= menu_index <= len(menu_list) - 1
    if key in (sfg.UserKey.DOWN, K_DOWN):
        return min(menu_index + 1, len(menu_list) - 1)
    elif key in (sfg.UserKey.UP, K_UP):
        return max(0, menu_index - 1)
    return menu_index


def render_menu(screen, menu_index, menu_list, menu_option_rect_setting, menu_blit_y,
        size_on, size_off, color_on, color_off):
    renne_cursor = basic_image_controller.get("head_status").subsurface(
        pygame.Rect(sfg.START_GAME.RENNE_CURSOR_RECT)).convert_alpha()
    menu_option_rect = pygame.Rect(menu_option_rect_setting)
    screen_centerx = sfg.Screen.SIZE[0] / 2
    for i, menu_word in enumerate(menu_list):
        if i == menu_index:
            renne_cursor_rect = renne_cursor.get_rect()
            renne_cursor_rect.center = (screen_centerx - menu_option_rect.width / 2,
                menu_blit_y + menu_option_rect.height / 2)
            screen.blit(renne_cursor, renne_cursor_rect)

            m_size = size_on
            m_color = color_on

        else:
            m_size = size_off
            m_color = color_off

        menu = pygame.font.SysFont("arial black", m_size).render(menu_word, True, m_color)
        menu_rect = menu.get_rect()
        menu_rect.center = (screen_centerx, menu_blit_y + menu_option_rect.height / 2)
        screen.blit(menu, menu_rect)

        menu_blit_y += menu_option_rect.height


def main(args):
    if args.chapter is not None:
        if args.chapter == 0:
            start_game(screen)
        elif args.chapter == -1:
            end_game(screen)
        else:
            enter_chapter(screen, args.chapter)
        return

    i = 0
    while i < len(sfg.GameMap.CHAPTERS):
        if i == 0:
            # chapter 0 means the main menu
            status = start_game(screen)
        else:
            chapter = sfg.GameMap.CHAPTERS[i]
            loading_chapter_picture(screen)
            status = enter_chapter(screen, chapter)

        if status == cfg.GameControl.NEXT:
            i += 1
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
    pic = cg_image_controller.get("start_game").convert()
    pic_rect = pic.get_rect()

    screen_centerx = sfg.Screen.SIZE[0] / 2
    pic_rect.centerx = screen_centerx
    pic_rect.top = sfg.START_GAME.PICTURE_BLIT_Y

    clock = pygame.time.Clock()
    menu_index = 0
    pic_alpha = 0 # picture fades in, alpha changes from 0 to 255
    fade_in_delta = 256 / sfg.START_GAME.PICTURE_FADE_IN_TIME

    menu_option_rect = pygame.Rect(sfg.START_GAME.MENU_OPTION_RECT)
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
                        if sfg.START_GAME.MENU_LIST[menu_index] == "START":
                            return cfg.GameControl.NEXT
                        elif sfg.START_GAME.MENU_LIST[menu_index] == "QUIT":
                            return cfg.GameControl.QUIT
                    elif event.key == K_ESCAPE:
                        return cfg.GameControl.QUIT

                    # 0 <= menu_index <= len(menu_list) - 1
                    menu_index = select_menu(event.key, sfg.START_GAME.MENU_LIST, menu_index)

            render_menu(screen, menu_index, sfg.START_GAME.MENU_LIST, sfg.START_GAME.MENU_OPTION_RECT,
                sfg.START_GAME.MENU_BLIT_Y, sfg.START_GAME.MENU_ON_SIZE, sfg.START_GAME.MENU_OFF_SIZE,
                sfg.START_GAME.MENU_ON_COLOR, sfg.START_GAME.MENU_OFF_COLOR)

        pygame.display.flip()



def end_game(screen):
    screen_centerx = sfg.Screen.SIZE[0] / 2

    renne_image = pygame.image.load("renne.png").convert_alpha()
    renne_image_rect = renne_image.get_rect()
    renne_image_rect.centerx = screen_centerx
    renne_image_rect.centery = sfg.END_GAME.RENNE_IMAGE_BLIT_Y

    word = sfg.END_GAME.BUSUNCLE_WORKS
    word_rect = word.get_rect()
    word_rect.centerx = screen_centerx
    word_rect.centery = sfg.END_GAME.BUSUNCLE_WORKS_BLIT_Y

    mask_alpha = 255
    fade_in_delta = 256 / sfg.END_GAME.ENDING_FADEIN_TIME
    mask = pygame.Surface(sfg.Screen.SIZE).convert_alpha()

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
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



def enter_chapter(screen, chapter):
    clock = pygame.time.Clock()
    map_setting = util.load_map_setting(chapter)

    camera = Camera(screen, map_size=map_setting["size"])
    game_world = GameWorld()
    allsprites = GameSpritesGroup()
    enemies = GameSpritesGroup()
    static_objects = GameStaticObjectGroup()
    game_map = GameMap(chapter, map_setting["size"], map_setting["tiles"])

    # load hero
    renne = Renne(sfg.Renne, *map_setting["hero"])
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

    menu_index = 0
    running = True
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                exit(0)

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    #return cfg.GameControl.QUIT
                    if game_status.status == cfg.GameStatus.IN_PROGRESS:
                        game_status.status = cfg.GameStatus.PAUSE
                        menu_index = 0
                    elif game_status.status == cfg.GameStatus.PAUSE:
                        game_status.status = cfg.GameStatus.IN_PROGRESS

                if event.key == K_RETURN:
                    if game_status.status == cfg.GameStatus.HERO_WIN:
                        return cfg.GameControl.NEXT
                    elif game_status.status == cfg.GameStatus.HERO_LOSE:
                        return cfg.GameControl.AGAIN
                    elif game_status.status == cfg.GameStatus.PAUSE:
                        if sfg.Chapter.PAUSE_MENU_LIST[menu_index] == "CONTINUE":
                            game_status.status = cfg.GameStatus.IN_PROGRESS
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

        renne.update(passed_seconds, external_event=game_status.status)
        for enemy in filter(lambda x: enemy_in_one_screen(renne, x), enemies):
            enemy.update(passed_seconds, external_event=game_status.status)

        game_status.update()

        camera.screen_follow(renne.pos)

        game_world.draw(camera)
        game_status.draw(camera)

        if COMMAND_DEBUG_MODE or sfg.DEBUG_MODE:
            debug_tools.all_model_display(camera, game_world, game_map)        

        if game_status.status == cfg.GameStatus.PAUSE:
            mask = pygame.Surface(sfg.Screen.SIZE).convert_alpha()
            mask.fill(pygame.Color(0, 0, 0, 128))
            screen.blit(mask, (0, 0))

            # draw the pause menu
            render_menu(screen, menu_index, sfg.Chapter.PAUSE_MENU_LIST, sfg.Chapter.PAUSE_MENU_OPTION_RECT,
                sfg.Chapter.PAUSE_MENU_BLIT_Y, sfg.Chapter.PAUSE_MENU_ON_SIZE, sfg.Chapter.PAUSE_MENU_OFF_SIZE,
                sfg.Chapter.PAUSE_MENU_ON_COLOR, sfg.Chapter.PAUSE_MENU_OFF_COLOR)


        pygame.display.flip()



if __name__ == "__main__":
    args = util.parse_command_line([
        (["-d", "--debug"], {"dest": "debug", "action": "store_true"}),
        (["-c", "--chapter"], {"dest": "chapter", "action": "store", "type": int}),
    ])
    COMMAND_DEBUG_MODE = args.debug is True
    main(args)

