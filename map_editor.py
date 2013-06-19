import os
import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSprite, GameSpritesGroup, Ambush
from gameobjects.vector2 import Vector2
from gameworld import GameWorld, GameMap, StaticObjectGroup, StaticObject
from renderer import Camera
from base import util
import debug_tools
from base import constant as cfg
from etc import setting as sfg



DEBUG_DRAW = {
    "pos": False,
    "area": False,
    "waypoints": False,
}


def save_waypoints(chapter, waypoints):
    filename = "%s.txt" % chapter
    fp = open(os.path.join(sfg.WayPoint.DIR, filename), "w")
    for wp in waypoints:
        fp.write("%s\t%s\n" % wp)
    fp.close()



def gen_chapter_waypoints(chapter, map_setting):
    bounding_box = pygame.Rect(sfg.WayPoint.BOUNDING_BOX_RECT)
    blocks = []
    waypoints = set()

    for static_obj_init in map_setting["static_objects"]:
        t, p = static_obj_init["id"], static_obj_init["pos"]
        static_obj_setting = sfg.STATIC_OBJECT_SETTING_MAPPING[t]
        if not static_obj_setting.IS_BLOCK:
            continue

        pos = Vector2(p)
        rect = pygame.Rect(static_obj_setting.AREA_RECT)
        rect.center = pos
        blocks.append(rect)

    for x in xrange(0, map_setting["size"][0], sfg.WayPoint.STEP_WIDTH):
        for y in xrange(0, map_setting["size"][1], sfg.WayPoint.STEP_WIDTH):
            fx, fy = map(float, (x, y))
            bounding_box.center = (fx, fy)
            if bounding_box.collidelist(blocks) == -1:
                waypoints.add((fx, fy))

    return waypoints



def get_map_pos_for_mouse(camera_rect, mouse_pos):
    map_pos = (mouse_pos[0] + camera_rect.topleft[0], (mouse_pos[1] + camera_rect.topleft[1]) * 2)
    return map_pos


def select_unit(map_pos_for_mouse, game_world):
    # objects in game_world first
    for sp in game_world.yield_all_objects():
        if sp.area.collidepoint(map_pos_for_mouse):
            game_world.remove_object(sp)
            return sp

    # than check whether select a ambush
    for ambush in game_world.ambush_list:
        if ambush.surround_area.collidepoint(map_pos_for_mouse):
            # remove all references to sprites
            ambush.empty()
            game_world.ambush_list.remove(ambush)
            return ambush

    return None


def put_down_selected_object(selected_object, game_world):
    if selected_object is None:
        return True

    for sp in game_world.yield_all_objects():
        if selected_object.area.colliderect(sp.area):
            return False

    for ambush in game_world.ambush_list:
        if selected_object.area.colliderect(ambush.surround_area):
            # we don't let object be put in a existed ambush, for simpleness
            return False

    game_world.add_object(selected_object)
    return True


def put_down_ambush(ambush, game_world):
    if ambush is None:
        return True

    # at least one sprite collide with it, return True
    for sp in game_world.dynamic_objects:
        if isinstance(sp, Renne):
            continue

        if ambush.surround_area.colliderect(sp.area):
            ambush.add(sp)

    if len(ambush.sprites()) == 0:
        return False

    game_world.ambush_list.append(ambush)
    return True


def change_map_setting(map_setting, game_world):
    res = {"hero": None, "monsters": [], "static_objects": []}
    for sp in game_world.static_objects:
        x, y = map(int, sp.pos)
        res["static_objects"].append({"id": sp.setting.ID, "pos": (x, y)})

    for sp in game_world.dynamic_objects:
        x, y = map(int, sp.pos)
        if isinstance(sp, Renne):
            res["hero"] = {"pos": (x, y), "direction": sp.direction}
        else:
            res["monsters"].append({"id": sp.setting.ID, "pos": (x, y), "direction": sp.direction})

    map_setting.update(res)



def set_selected_object_follow_mouse(map_pos_for_mouse, selected_object):
    selected_object.area.center = map_pos_for_mouse
    selected_object.pos.x, selected_object.pos.y = map_pos_for_mouse
    selected_object.adjust_rect()



def set_ambush_follow_mouse(map_pos_for_mouse, ambush):
    ambush.pos = map_pos_for_mouse
    ambush.adjust_model()
        


def mouse_object_toggle(selected_object, object_type):
    if isinstance(selected_object, Renne):
        # Renne is not under this loop, do nothing and return it immediately
        return selected_object

    new_selected = None
    if object_type == cfg.GameObject.TYPE_STATIC:
        new_selected = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[1], (-1000, -1000))
    elif object_type == cfg.GameObject.TYPE_DYNAMIC:
        new_selected = Enemy(sfg.SPRITE_SETTING_MAPPING[1], (-1000, -1000), 0)

    return new_selected


def mouse_ambush_toggle(selected_object):
    if isinstance(selected_object, Renne):
        # Renne is not under this loop, do nothing and return it immediately
        return selected_object

    ambush = Ambush((-1000, -1000), sfg.Ambush.SURROUND_AREA_WIDTH,
        sfg.Ambush.ENTER_AREA_WIDTH, cfg.Ambush.APPEAR_TYPE_TOP_DOWN)
    return ambush



def selected_object_toggle(selected_object):
    if selected_object is None or isinstance(selected_object, Renne):
        # Renne and None are not in toggle loop
        return selected_object

    if isinstance(selected_object, Enemy):
        new_object_id = (selected_object.setting.ID + 1) % (len(sfg.SPRITE_SETTING_LIST) + 1) or 1
        new_object = Enemy(sfg.SPRITE_SETTING_MAPPING[new_object_id], (-1000, -1000), 0)
    elif isinstance(selected_object, StaticObject):
        new_object_id = (selected_object.setting.ID + 1) % (len(sfg.STATIC_OBJECT_SETTING_LIST) + 1) or 1
        new_object = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[new_object_id], (-1000, -1000))
        
    return new_object


def create_new_instance(selected_object):
    if isinstance(selected_object, Enemy):
        return Enemy(sfg.SPRITE_SETTING_MAPPING[selected_object.setting.ID], 
            selected_object.pos.as_tuple(), 0)
    elif isinstance(selected_object, StaticObject):
        return StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[selected_object.setting.ID],
            selected_object.pos.as_tuple())
    raise Exception("invalid object to create")


def turn_sprite_direction(selected_object):
    selected_object.direction = (selected_object.direction + 1) % len(cfg.Direction.ALL)
    return selected_object


def run(chapter):
    clock = pygame.time.Clock()

    map_setting = util.load_map_setting(chapter)

    screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
    pygame.display.set_caption("Renne Map Editor")
    camera = Camera(screen, map_size=map_setting["size"])
    game_world = GameWorld()
    game_map = GameMap(chapter, map_setting["size"], map_setting["tiles"])

    # load hero
    renne = Renne(sfg.Renne, map_setting["hero"]["pos"], map_setting["hero"]["direction"])
    game_world.add_object(renne)

    # load monsters
    monster_init_list = map_setting.get("monsters", [])
    for monster_init in monster_init_list:
        monster_id, pos, direct = monster_init["id"], monster_init["pos"], monster_init["direction"]
        monster = Enemy(sfg.SPRITE_SETTING_MAPPING[monster_id], pos, direct)
        game_world.add_object(monster)

    # load static objects
    chapter_static_objects = map_setting.get("static_objects", [])
    for static_obj_init in chapter_static_objects:
        t, p = static_obj_init["id"], static_obj_init["pos"]
        static_obj = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[t], p)
        game_world.add_object(static_obj)

    # hack an attrbute ambush into game_world for easy saving
    game_world.ambush_list = []


    running = True
    key_vec = Vector2()
    selected_object = None
    while running:
        mouse_pos = pygame.mouse.get_pos()
        map_pos_for_mouse = get_map_pos_for_mouse(camera.rect, mouse_pos)

        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                running = False

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if (isinstance(selected_object, GameSprite) or \
                        isinstance(selected_object, StaticObject)) \
                        and put_down_selected_object(selected_object, game_world):
                        selected_object = None
                    elif isinstance(selected_object, Ambush) \
                        and put_down_ambush(selected_object, game_world):
                        selected_object = None

                if event.key == K_w:
                    if isinstance(selected_object, GameSprite):
                        selected_object = selected_object_toggle(selected_object)

                if event.key == K_e:
                    selected_object = None

                if event.key == K_t:
                    if isinstance(selected_object, GameSprite):
                        selected_object = turn_sprite_direction(selected_object)

                key_mods = pygame.key.get_mods()
                if key_mods & KMOD_CTRL and event.key == K_s:
                    # ctrl+s to save map setting
                    change_map_setting(map_setting, game_world)
                    util.save_map_setting(chapter, map_setting)
                    print "save chapter %s map setting" % chapter
                    # a good chance for generating waypoints when saving the map setting
                    game_map.waypoints = gen_chapter_waypoints(chapter, map_setting)
                    save_waypoints(chapter, game_map.waypoints)
                    print "generate chapter %s waypoints success" % chapter

                if key_mods & KMOD_ALT:
                    if event.key == K_1:
                        # alt+1 toggle static object
                        selected_object = mouse_object_toggle(selected_object, 
                            cfg.GameObject.TYPE_STATIC)
                    elif event.key == K_2:
                        # alt+2 toggle enemy
                        selected_object = mouse_object_toggle(selected_object,
                            cfg.GameObject.TYPE_DYNAMIC)
                    elif event.key == K_3:
                        # alt+3 toggle ambush
                        selected_object = mouse_ambush_toggle(selected_object)

                    # debug draw switch
                    elif event.key == K_p:
                        DEBUG_DRAW["pos"] = not DEBUG_DRAW["pos"]
                    elif event.key == K_a:
                        DEBUG_DRAW["area"] = not DEBUG_DRAW["area"]
                    elif event.key == K_z:
                        DEBUG_DRAW["waypoints"] = not DEBUG_DRAW["waypoints"]

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    # left click
                    if selected_object is None:
                        # pick up "this" unit if the mouse is over it
                        selected_object = select_unit(map_pos_for_mouse, game_world)
                    else:
                        # put down the current selected unit if no "collision" happen
                        if (isinstance(selected_object, GameSprite) or \
                            isinstance(selected_object, StaticObject)) \
                            and put_down_selected_object(selected_object, game_world):
                            if pygame.key.get_mods() & KMOD_CTRL:
                                selected_object = create_new_instance(selected_object)
                            else:
                                selected_object = None

                        elif isinstance(selected_object, Ambush) \
                            and put_down_ambush(selected_object, game_world):
                            selected_object = None


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
        passed_seconds = time_passed * 0.001

        camera.screen_move(key_vec, sfg.MapEditor.SCREEN_MOVE_SPEED, passed_seconds)
        if selected_object is not None:
            if isinstance(selected_object, GameSprite) \
                or isinstance(selected_object, StaticObject):
                set_selected_object_follow_mouse(map_pos_for_mouse, selected_object)
            elif isinstance(selected_object, Ambush):
                set_ambush_follow_mouse(selected_object)

        game_map.draw(camera)

        for sp in sorted(game_world.yield_all_objects(), key=lambda sp: sp.pos.y):
            if sp.setting.GAME_OBJECT_TYPE == cfg.GameObject.TYPE_DYNAMIC:
                sp.adjust_rect()
                # select current image for corresponding direction
                sp.animation.image = sp.animation.sprite_image_contoller.get_surface(
                    cfg.SpriteAction.STAND)[sp.direction]
                sp.animation.draw_shadow(camera)

            sp.draw(camera)

        if selected_object is not None:
            if isinstance(selected_object, GameSprite) \
                or isinstance(selected_object, StaticObject):
                # render selected_object
                selected_object_name = sfg.Font.ARIAL_32.render(
                    selected_object.setting.NAME, True, pygame.Color("black"))
                camera.screen.blit(selected_object_name, (5, 5))
                selected_object.draw(camera)


        # debug drawings
        for sp in game_world.yield_all_objects():
            if DEBUG_DRAW["pos"]:
                debug_tools.draw_pos(camera, sp)
            if DEBUG_DRAW["area"]:
                debug_tools.draw_area(camera, sp)

        if DEBUG_DRAW["waypoints"]:
            debug_tools.draw_waypoins(camera, game_map.waypoints)

        pygame.display.flip()


if __name__ == "__main__":
    args = util.parse_command_line([
        (["-c", "--chapter"], {"dest": "chapter", "action": "store"}),
    ])
    if args.chapter is None:
        print "please specify the param chapter, using -c or --chapter option"
        exit(-1)
    run(args.chapter)
