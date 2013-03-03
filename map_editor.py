import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSpritesGroup, enemy_in_one_screen
from gameobjects.vector2 import Vector2
import etc.setting as sfg
import etc.constant as cfg
import sys
from time import time
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from renderer import Camera
from base import util
import debug_tools




screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne Map Editor")


def get_map_pos_for_mouse(camera_rect, mouse_pos):
    map_pos = (mouse_pos[0] + camera_rect.topleft[0], (mouse_pos[1] + camera_rect.topleft[1]) * 2)
    return map_pos


def select_unit(map_pos_for_mouse, game_objects):
    # change mouse pos to map pos first
    for sp in game_objects:
        if sp.area.collidepoint(map_pos_for_mouse):
            return sp
    return None


def put_selected_unit(selected_unit, game_objects):
    for sp in game_objects:
        if sp is selected_unit:
            continue
        if selected_unit.area.colliderect(sp.area):
            return False
    return True


def run(chapter):
    clock = pygame.time.Clock()

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

    running = True
    key_vec = Vector2()
    selected_unit = None
    left_click_begin = None
    while running:
        key_vec.x = key_vec.y = 0.0
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                running = False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                    running = False

        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[sfg.UserKey.LEFT]:
            key_vec.x -= 1.0
        if pressed_keys[sfg.UserKey.RIGHT]:
            key_vec.x += 1.0
        if pressed_keys[sfg.UserKey.UP]:
            key_vec.y -= 1.0
        if pressed_keys[sfg.UserKey.DOWN]:
            key_vec.y += 1.0

        pressed_mouse = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0

        map_pos_for_mouse = get_map_pos_for_mouse(camera.rect, mouse_pos)

        camera.screen_move(key_vec, sfg.MapEditor.SCREEN_MOVE_SPEED, passed_seconds)

        if pressed_mouse[0]:
            if selected_unit is None:
                selected_unit = select_unit(map_pos_for_mouse, game_world.sprites())
        elif pressed_mouse[2]:
            if selected_unit and put_selected_unit(selected_unit, game_world.sprites()):
                selected_unit = None

        game_map.draw(camera)
        game_world.draw(camera)
        if selected_unit is not None:
            selected_unit.area.center = map_pos_for_mouse
            selected_unit.pos.x, selected_unit.pos.y = map_pos_for_mouse
            if isinstance(selected_unit, GameStaticObject):
                selected_unit.adjust_rect()
            debug_tools.draw_area(selected_unit, camera)

        pygame.display.flip()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "please specify the only param chapter"
        exit(-1)
    run(sys.argv[1])
