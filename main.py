import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
from gamesprites import Renne, Enemy, GameSpritesGroup, enemy_in_one_screen
import etc.setting as sfg
import etc.constant as cfg
import os
import json
import math
import random
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from gamestatus import GameStatus
from renderer import Camera
import debug_tools
import util



screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne")
pygame.display.set_icon(pygame.image.load("renne.png").convert_alpha())




def main():
    clock = pygame.time.Clock()

    chapter = 1
    map_setting = util.load_map_setting(chapter)

    camera = Camera(screen, map_size=map_setting["size"])
    game_world = GameWorld()
    allsprites = GameSpritesGroup()
    enemies = GameSpritesGroup()
    static_objects = GameStaticObjectGroup()
    game_map = GameMap(chapter, map_setting["size"], map_setting["tiles"])

    # load hero
    hero_init = map_setting["hero"]
    renne = Renne(hero_init[0], hero_init[1], allsprites, enemies, static_objects, game_map)

    # load monsters
    monster_init = map_setting["monsters"]
    for monster_id, pos, direct in monster_init:
        monster = Enemy(sfg.SPRITE_SETTING_MAPPING[monster_id], pos, direct, allsprites, 
            renne, static_objects, game_map)

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
                running = False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

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

        camera.set_rect(renne.pos)

        game_world.draw(camera)
        game_status.draw(camera)

        if sfg.DEBUG_MODE:
            debug_tools.all_model_display(camera, game_world)        

        pygame.display.flip()


if __name__ == "__main__":
    main()
