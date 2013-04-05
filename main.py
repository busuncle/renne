import argparse
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
pygame.display.set_icon(pygame.image.load("renne.png").convert_alpha())

COMMAND_DEBUG_MODE = False


def main(args):
    if args.chapter is not None:
        enter_chapter(args.chapter)
        return

    opening_cg()
    for chapter in sfg.GameMap.CHAPTERS:
        img = cg_image_controller.get(2).convert_alpha()
        r = img.get_rect()
        r.center = map(lambda x: x/2, sfg.Screen.SIZE)
        screen.blit(img, r)
        screen.blit(sfg.GameStatus.WORDS["loading"], sfg.GameStatus.LOADING_BLIT_POS)
        pygame.display.update()
        pygame.time.wait(1000)
        enter_chapter(chapter)


def opening_cg():
    opening = cg_image_controller.get(1).convert_alpha()
    r = opening.get_rect()
    r.center = map(lambda x: x/2, sfg.Screen.SIZE)
    screen.blit(opening, r)
    screen.blit(sfg.GameStatus.WORDS["continue"], sfg.GameStatus.CONTINUE_BLIT_POS)
    pygame.display.update()
    clock = pygame.time.Clock()
    while True:
        ev = pygame.event.wait()
        if ev.type == KEYDOWN:
            if ev.key == K_RETURN:
                screen.fill(pygame.Color("black"))
                break
            elif ev.key == K_ESCAPE:
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
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                exit(0)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", dest="debug", action="store_true")
    parser.add_argument("-c", "--chapter", dest="chapter", action="store")
    args = parser.parse_args()
    COMMAND_DEBUG_MODE = args.debug
    main(args)

