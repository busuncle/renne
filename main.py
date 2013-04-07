import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSpritesGroup, enemy_in_one_screen
import etc.setting as sfg
import etc.constant as cfg
import etc.ai_setting as ai
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from gamestatus import GameStatus
from animation import cg_image_controller
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
        enter_chapter(args.chapter)
        return

    start_game()
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
    img = cg_image_controller.get(2).convert_alpha()
    r = img.get_rect()
    r.center = map(lambda x: x/2, sfg.Screen.SIZE)
    screen.blit(img, r)
    screen.blit(sfg.GameStatus.WORDS["loading"], sfg.GameStatus.LOADING_BLIT_POS)
    pygame.display.update()
    # a delay to show renne's picture on purpose?
    pygame.time.wait(1000)


def start_game():
    pic = cg_image_controller.get(1).convert_alpha()
    r = pic.get_rect()
    screen_centerx = sfg.Screen.SIZE[0] / 2
    r.centerx = screen_centerx
    r.top = sfg.START_GAME.PICTURE_BLIT_Y
    mask = pygame.Surface((pic.get_width(), pic.get_height())).convert_alpha()

    clock = pygame.time.Clock()
    menu_index = 0
    menu_option_rect = pygame.Rect(sfg.START_GAME.MENU_OPTION_RECT)
    menu_option = pygame.Surface((menu_option_rect.width, menu_option_rect.height))
    pic_alpha = 255 # picture fades in, alpha changes from 255 to 0
    fade_in_delta = 256 / sfg.START_GAME.PICTURE_FADEIN_TIME
    while True:
        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0

        pic_alpha = max(pic_alpha - passed_seconds * fade_in_delta, 0)
        mask.fill(pygame.Color(0, 0, 0, pic_alpha))
        pic.blit(mask, (0, 0))

        screen.blit(pic, r)

        if pic_alpha == 0:
            # no event accepted when fading in the picture
            ev = pygame.event.wait()
            if ev.type == KEYDOWN:
                if ev.key == K_RETURN:
                    break
                elif ev.key == K_ESCAPE:
                    exit(0)
                elif ev.key == K_DOWN:
                    menu_index = min(len(sfg.START_GAME.MENU_LIST) - 1, menu_index + 1)
                elif ev.key == K_UP:
                    menu_index = max(0, menu_index - 1)

            menu_y = sfg.START_GAME.MENU_BLIT_Y
            for i, menu_word in enumerate(sfg.START_GAME):
                if i == menu_index:
                    m_size = sfg.START_GAME.MENU_ON_SIZE
                    m_color = sfg.START_GAME.MENU_ON_COLOR
                else:
                    m_size = sfg.START_GAME.MENU_OFF_SIZE
                    m_color = sfg.START_GAME.MENU_OFF_COLOR

                menu_option_rect.centerx = screen_centerx
                menu_option_rect.centery = menu_y + menu_option_rect.height / 2
                menu = pygame.font.SysFont("arial", m_size).render(menu_word, True, m_color)
                menu_rect = menu.get_rect()
                menu_rect.center = menu_option_rect.center
                menu_option.blit(menu, menu_rect)
                screen.blit(menu_option, menu_option_rect)

                meny_y += menu_option_rect.height

        pygame.display.update()



def end_game():
    r = renne_image.get_rect()
    r.center = map(lambda x: x/2, sfg.Screen.SIZE)
    screen.blit(renne_image, r)
    word = sfg.GameStatus.WORDS["busuncle_works"]
    r = word.get_rect()
    r.center = (sfg.Screen.SIZE[0]/2, sfg.Screen.SIZE[1] * 0.61)
    screen.blit(word, r)
    pygame.display.update()
    clock = pygame.time.Clock()
    while True:
        ev = pygame.event.wait()
        if ev.type == KEYDOWN:
            if ev.key == K_ESCAPE:
                exit(0)

        clock.tick(sfg.FPS)



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
        (["-c", "--chapter"], {"dest": "chapter", "action": "store"}),
    ])
    COMMAND_DEBUG_MODE = args.debug is True
    main(args)

