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
renne_image = pygame.image.load("renne.png").convert_alpha()
pygame.display.set_icon(renne_image)

COMMAND_DEBUG_MODE = False



def main(args):
    if args.chapter is not None:
        if args.chapter == 0:
            start_game()
        elif args.chapter == -1:
            end_game()
        else:
            enter_chapter(args.chapter)
        return

    option_index_chosen = start_game()
    if option_index_chosen == sfg.START_GAME.INDEX_QUIT:
        return

    i = 0
    while i < len(sfg.GameMap.CHAPTERS):
        chapter = sfg.GameMap.CHAPTERS[i]
        loading_chapter_picture(screen)
        status = enter_chapter(chapter)
        if status == cfg.Chapter.STATUS_QUIT_GAME:
            return
        elif status == cfg.Chapter.STATUS_PASS:
            i += 1

    end_game()


def loading_chapter_picture(screen):
    screen.fill(pygame.Color("black"))
    img = cg_image_controller.get("loading_chapter").convert_alpha()
    r = img.get_rect()
    r.center = map(lambda x: x/2, sfg.Screen.SIZE)
    screen.blit(img, r)
    screen.blit(sfg.GameStatus.WORDS["loading"], sfg.GameStatus.LOADING_BLIT_POS)
    pygame.display.update()
    # a delay to show renne's picture on purpose?
    pygame.time.wait(1000)


def start_game():
    pic = cg_image_controller.get("start_game").convert_alpha()
    pic_rect = pic.get_rect()

    renne_cursor = basic_image_controller.get("head_status").subsurface(
        pygame.Rect(sfg.START_GAME.RENNE_CURSOR_RECT)).convert_alpha()

    screen_centerx = sfg.Screen.SIZE[0] / 2
    pic_rect.centerx = screen_centerx
    pic_rect.top = sfg.START_GAME.PICTURE_BLIT_Y

    clock = pygame.time.Clock()
    menu_index = 0
    pic_alpha = 255 # picture fades in, alpha changes from 255 to 0
    fade_in_delta = 256 / sfg.START_GAME.PICTURE_FADEIN_TIME

    mask = pygame.Surface((pic.get_width(), pic.get_height())).convert_alpha()

    while True:
        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0

        pic_alpha = int(max(pic_alpha - passed_seconds * fade_in_delta, 0))

        mask.fill(pygame.Color(0, 0, 0, pic_alpha))

        screen.blit(pic, pic_rect)
        screen.blit(mask, pic_rect.topleft)

        if pic_alpha == 0:
            # no events accepted until the renne's picure is fully displayed
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    exit(0)
                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        return menu_index
                    elif event.key == K_ESCAPE:
                        return sfg.START_GAME.INDEX_QUIT
                    elif event.key in (sfg.UserKey.DOWN, K_DOWN):
                        menu_index = min(len(sfg.START_GAME.MENU_LIST) - 1, menu_index + 1)
                    elif event.key in (sfg.UserKey.UP, K_UP):
                        menu_index = max(0, menu_index - 1)

            menu_y = sfg.START_GAME.MENU_BLIT_Y
            for i, menu_word in enumerate(sfg.START_GAME.MENU_LIST):
                menu_option_rect = pygame.Rect(sfg.START_GAME.MENU_OPTION_RECT)
                menu_option = pygame.Surface((menu_option_rect.width, menu_option_rect.height))

                if i == menu_index:
                    renne_cursor_rect = renne_cursor.get_rect()
                    renne_cursor_rect.centery = menu_option_rect.height / 2
                    menu_option.blit(renne_cursor, renne_cursor_rect)
                    m_size = sfg.START_GAME.MENU_ON_SIZE
                    m_color = sfg.START_GAME.MENU_ON_COLOR
                else:
                    m_size = sfg.START_GAME.MENU_OFF_SIZE
                    m_color = sfg.START_GAME.MENU_OFF_COLOR
                
                menu = pygame.font.SysFont("arial black", m_size).render(menu_word, True, m_color)
                menu_rect = menu.get_rect()
                menu_rect.center = menu_option_rect.center
                menu_option.blit(menu, menu_rect)

                menu_option_rect.centerx = screen_centerx
                menu_option_rect.centery = menu_y + menu_option_rect.height / 2
                screen.blit(menu_option, menu_option_rect)

                menu_y += menu_option_rect.height

        pygame.display.flip()



def end_game():
    screen_centerx = sfg.Screen.SIZE[0] / 2

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

        screen.blit(renne_image, renne_image_rect)

        # it *must* create a new surface everytime for rendering a good font!
        word_panel = pygame.Surface((word_rect.width, word_rect.height))
        word_panel.blit(word, (0, 0))
        screen.blit(word_panel, word_rect)


        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0
        mask_alpha = int(max(mask_alpha - passed_seconds * fade_in_delta, 0))
        mask.fill(pygame.Color(0, 0, 0, mask_alpha))
        screen.blit(mask, (0, 0))

        pygame.display.update()



def enter_chapter(chapter):
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

    running = True
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                exit(0)

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    return cfg.Chapter.STATUS_QUIT_GAME
                if event.key == K_RETURN:
                    if game_status.status == cfg.GameStatus.HERO_WIN:
                        return cfg.Chapter.STATUS_PASS
                    elif game_status.status == cfg.GameStatus.HERO_LOSE:
                        return cfg.Chapter.STATUS_AGAIN

        pressed_keys = pygame.key.get_pressed()
        renne.event_handle(pressed_keys, external_event=game_status.status)

        for enemy in filter(lambda x: enemy_in_one_screen(renne, x), enemies):
            enemy.event_handle(pressed_keys, external_event=game_status.status)

        game_map.draw(camera)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0

        renne.update(passed_seconds)
        for enemy in filter(lambda x: enemy_in_one_screen(renne, x), enemies):
            enemy.update(passed_seconds)

        game_status.update()

        camera.screen_follow(renne.pos)

        game_world.draw(camera)
        game_status.draw(camera)

        if COMMAND_DEBUG_MODE or sfg.DEBUG_MODE:
            debug_tools.all_model_display(camera, game_world, game_map)        

        pygame.display.flip()



if __name__ == "__main__":
    args = util.parse_command_line([
        (["-d", "--debug"], {"dest": "debug", "action": "store_true"}),
        (["-c", "--chapter"], {"dest": "chapter", "action": "store", "type": int}),
    ])
    COMMAND_DEBUG_MODE = args.debug is True
    main(args)

