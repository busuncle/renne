import os
import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSpritesGroup
from gameobjects.vector2 import Vector2
import etc.setting as sfg
import etc.constant as cfg
import sys
from time import time
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from renderer import Camera
from base import util
import debug_tools



PROJECT_ROOT = util.get_project_root()
assert os.path.basename(PROJECT_ROOT) == "renne"

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


def change_map_setting(map_setting, game_world):
    res = {"hero": None, "monsters": [], "static_objects": []}
    for sp in game_world.sprites():
        x, y = map(int, sp.pos)
        if issubclass(sp.setting, sfg.StaticObject):
            res["static_objects"].append([sp.setting.ID, [x, y]])
        elif issubclass(sp.setting, sfg.GameRole):
            direct = sp.direction
            if isinstance(sp, Renne):
                res["hero"] = [[x, y], direct]
            else:
                res["monsters"].append([sp.setting.ID, [x, y], direct])

    map_setting.update(res)


def set_selected_unit_follow_mouse(map_pos_for_mouse, selected_unit):
    selected_unit.area.center = map_pos_for_mouse
    selected_unit.pos.x, selected_unit.pos.y = map_pos_for_mouse
    if isinstance(selected_unit, GameStaticObject):
        selected_unit.adjust_rect()


def change_mouse_select(selected_unit, game_world):
    # None -> Enemy -> GameStaticObject -> None ... change in this circle
    new_selected = None
    if isinstance(selected_unit, Renne):
        # Renne is not under this loop, do nothing and return it immediately
        return selected_unit

    if selected_unit is None:
        new_selected = Enemy(sfg.SPRITE_SETTING_MAPPING[1], (-1000, -1000), 0)
        game_world.add(new_selected)
    elif isinstance(selected_unit, Enemy):
        game_world.remove(selected_unit)
        new_selected = GameStaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[1], (-1000, -1000))
        game_world.add(new_selected)
    elif isinstance(selected_unit, GameStaticObject):
        game_world.remove(selected_unit)
        new_selected = None

    return new_selected



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
    renne = Renne(sfg.Renne, *map_setting["hero"])

    # load monsters
    monster_init = map_setting["monsters"]
    for monster_id, pos, direct in monster_init:
        monster = Enemy(sfg.SPRITE_SETTING_MAPPING[monster_id], pos, direct)

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
    while running:
        mouse_pos = pygame.mouse.get_pos()
        map_pos_for_mouse = get_map_pos_for_mouse(camera.rect, mouse_pos)

        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                running = False

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

                if event.key == K_q:
                    selected_unit = change_mouse_select(selected_unit, game_world)

                if pygame.key.get_mods() & KMOD_CTRL and event.key == K_s:
                    # ctrl+s to save map setting
                    change_map_setting(map_setting, game_world)
                    util.save_map_setting(chapter, map_setting)
                    print "save %s map setting" % chapter

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    # left click
                    if selected_unit is None:
                        # pick up "this" unit if the mouse is over it
                        selected_unit = select_unit(map_pos_for_mouse, game_world.sprites())
                    else:
                        # put down the current selected unit if no "collision" happen
                        if put_selected_unit(selected_unit, game_world.sprites()):
                            selected_unit = None


        pressed_keys = pygame.key.get_pressed()
        key_vec.x = key_vec.y = 0.0
        if pressed_keys[K_LEFT]:
           key_vec.x -= 1.0
        if pressed_keys[K_RIGHT]:
            key_vec.x += 1.0
        if pressed_keys[K_UP]:
            key_vec.y -= 1.0
        if pressed_keys[K_DOWN]:
            key_vec.y += 1.0

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed / 1000.0

        camera.screen_move(key_vec, sfg.MapEditor.SCREEN_MOVE_SPEED, passed_seconds)

        game_map.draw(camera)
        game_world.draw(camera)

        if selected_unit is not None:
            set_selected_unit_follow_mouse(map_pos_for_mouse, selected_unit)
            debug_tools.draw_area(selected_unit, camera)

        pygame.display.flip()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "please specify the only param chapter"
        exit(-1)
    run(sys.argv[1])
