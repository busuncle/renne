import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSpritesGroup, enemy_in_one_screen
import etc.setting as sfg
import etc.constant as cfg
import etc.ai_setting as ai
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from gamestatus import GameStatus, Menu, bg_box, start_game, loading_chapter_picture, end_game
from renderer import Camera
import debug_tools
from base import util



screen = sfg.Screen.DEFAULT_SCREEN
pygame.display.set_caption("Renne")
pygame.display.set_icon(pygame.image.load("renne.png").convert_alpha())


COMMAND_DEBUG_MODE = False
COMMAND_DEBUG_OPTIONS = {}



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



def enter_chapter(screen, chapter, renne):
    map_setting = util.load_map_setting(chapter)

    camera = Camera(screen, map_size=map_setting["size"])
    game_world = GameWorld()
    allsprites = GameSpritesGroup()
    enemies = GameSpritesGroup()
    static_objects = GameStaticObjectGroup()
    game_map = GameMap(chapter, map_setting["size"], map_setting["tiles"])

    # load hero
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

    if COMMAND_DEBUG_MODE:
        # skip the init status in command debug mode
        game_status.status = cfg.GameStatus.IN_PROGRESS

    clock = pygame.time.Clock()
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
                        game_status.menu.index = 0
                    elif game_status.status == cfg.GameStatus.PAUSE:
                        game_status.status = cfg.GameStatus.IN_PROGRESS
                        bg_box.unpause()

                if event.key == K_RETURN:
                    if game_status.status == cfg.GameStatus.HERO_WIN:
                        return cfg.GameControl.NEXT
                    elif game_status.status == cfg.GameStatus.HERO_LOSE:
                        return cfg.GameControl.AGAIN
                    elif game_status.status == cfg.GameStatus.PAUSE:
                        if game_status.menu.current_menu() == "CONTINUE":
                            game_status.status = cfg.GameStatus.IN_PROGRESS
                            bg_box.unpause()
                        elif game_status.menu.current_menu() == "MAIN":
                            return cfg.GameControl.MAIN
                        elif game_status.menu.current_menu() == "QUIT":
                            return cfg.GameControl.QUIT

                if game_status.status == cfg.GameStatus.PAUSE:
                    game_status.menu.update(event.key)

        pressed_keys = pygame.key.get_pressed()
        renne.event_handle(pressed_keys, external_event=game_status.status)

        for enemy in enemies:
            if enemy_in_one_screen(renne, enemy):
                enemy.event_handle(pressed_keys, external_event=game_status.status)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0

        # update renne, enemies, game_status in sequence
        renne.update(passed_seconds, external_event=game_status.status)
        for enemy in enemies:
            if enemy_in_one_screen(renne, enemy):
                enemy.update(passed_seconds, external_event=game_status.status)

        game_status.update(passed_seconds)

        camera.screen_follow(renne.pos)

        game_map.draw(camera)
        game_world.draw(camera)
        game_status.draw(camera)

        if COMMAND_DEBUG_MODE or sfg.DEBUG_MODE:
            debug_tools.run_debug_by_option_list(COMMAND_DEBUG_OPTIONS,
                camera, game_world, game_map, clock)

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

