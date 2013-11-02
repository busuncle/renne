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


current_selected_object_ids = {
    cfg.GameObject.TYPE_STATIC: None,
    cfg.GameObject.TYPE_DYNAMIC: None,
}



def gen_chapter_waypoints(map_setting):
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
            # remove it from ambush if it's in one of it
            for ambush in game_world.ambush_list:
                if sp in ambush:
                    ambush.remove(sp)
                    break
            return sp

    # than check whether select a ambush
    for ambush in game_world.ambush_list:
        if ambush.surround_area.collidepoint(map_pos_for_mouse):
            # remove all references to sprites
            ambush.empty()
            game_world.ambush_list.remove(ambush)
            return ambush

    return None



def object_can_be_shift(selected_object):
    return isinstance(selected_object, GameSprite) or isinstance(selected_object, StaticObject)



def put_down_selected_object(selected_object, game_world):
    if selected_object is None:
        return True

    for sp in game_world.yield_all_objects():
        if selected_object.area.colliderect(sp.area):
            return False

    if isinstance(selected_object, GameSprite):
        # put sprite into ambush if it's *only* in one ambush
        first_collide_ambush_index = None
        for i, ambush in enumerate(game_world.ambush_list):
            if selected_object.area.colliderect(ambush.surround_area):
                if first_collide_ambush_index is not None:
                    # already in one ambush, we don't let it be in two or more ambush
                    return False
                else:
                    first_collide_ambush_index = i

        if first_collide_ambush_index is not None:
            game_world.ambush_list[first_collide_ambush_index].add(selected_object)

    game_world.add_object(selected_object)
    return True


def put_down_ambush(ambush, game_world):
    if ambush is None:
        return True

    for other_ambush in game_world.ambush_list:
        # ambush can not overlap each other, for simpleness
        if ambush.surround_area.colliderect(other_ambush.surround_area):
            return False

    for sp in game_world.dynamic_objects:
        if isinstance(sp, Renne):
            continue

        if ambush.surround_area.colliderect(sp.area):
            # check whether this sprite is already in other ambush,
            # we don't let one sprite in two or more ambush in the same time
            can_add_to_ambush = True
            for other_ambush in game_world.ambush_list:
                if sp in other_ambush:
                    can_add_to_ambush = False
                    break

            if can_add_to_ambush:
                ambush.add(sp)

    game_world.ambush_list.append(ambush)
    return True



def change_map_setting(map_setting, game_world, game_map):
    res = {"hero": None, "monsters": [], "static_objects": [], "ambush_list": [], "waypoints": []}
    for sp in game_world.static_objects:
        x, y = map(int, sp.pos)
        res["static_objects"].append({"id": sp.setting.ID, "pos": (x, y)})

    # sprite in ambush will not be set into monster list
    monster_ignore_list = set()
    for ambush in game_world.ambush_list:
        am_sp_list = []
        for sp in ambush:
            x, y = map(int, sp.pos)
            am_sp_list.append({"id": sp.setting.ID, "pos": (x, y), "direction": sp.direction})
            monster_ignore_list.add(sp)

        res["ambush_list"].append({"ambush": {"pos": ambush.pos, "type": ambush.appear_type},
            "monsters": am_sp_list})

    for sp in game_world.dynamic_objects:
        if sp in monster_ignore_list:
            continue

        x, y = map(int, sp.pos)
        if isinstance(sp, Renne):
            res["hero"] = {"pos": (x, y), "direction": sp.direction}
        else:
            res["monsters"].append({"id": sp.setting.ID, "pos": (x, y), "direction": sp.direction})

    # a good chance for generating waypoints when saving the map setting
    game_map.waypoints = gen_chapter_waypoints(map_setting)
    for wp in game_map.waypoints:
        res["waypoints"].append(wp)

    map_setting.update(res)



def set_selected_object_follow_mouse(map_pos_for_mouse, selected_object):
    selected_object.area.center = map_pos_for_mouse
    selected_object.pos.x, selected_object.pos.y = map_pos_for_mouse
    selected_object.adjust_rect()



def set_ambush_follow_mouse(map_pos_for_mouse, ambush):
    ambush.pos = map_pos_for_mouse
    ambush.adjust_model()
        


def mouse_ambush_toggle(selected_object):
    if isinstance(selected_object, Renne):
        # Renne is not under this loop, do nothing and return it immediately
        return selected_object

    ambush = Ambush((-1000, -1000), sfg.Ambush.SURROUND_AREA_WIDTH,
        sfg.Ambush.ENTER_AREA_WIDTH, cfg.Ambush.APPEAR_TYPE_TOP_DOWN)
    return ambush



def selected_object_shift(selected_object, object_type=None):
    if isinstance(selected_object, Renne):
        # Renne is not under this loop, do nothing and return it immediately
        return selected_object
    
    if object_type == cfg.GameObject.TYPE_STATIC:
        current_id = current_selected_object_ids[cfg.GameObject.TYPE_STATIC]
        if current_id is None:
            current_id = 1
            new_object = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[current_id], 
                (-1000, -1000))
        else:
            if isinstance(selected_object, StaticObject):
                current_id = (current_id + 1) % (len(sfg.STATIC_OBJECT_SETTING_LIST) + 1) or 1
            new_object = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[current_id], (-1000, -1000))
        current_selected_object_ids[cfg.GameObject.TYPE_STATIC] = current_id

    elif object_type == cfg.GameObject.TYPE_DYNAMIC:
        current_id = current_selected_object_ids[cfg.GameObject.TYPE_DYNAMIC]
        if current_id is None:
            current_id = 1
            new_object = Enemy(sfg.SPRITE_SETTING_MAPPING[current_id], (-1000, -1000), 0)
        else:
            if isinstance(selected_object, GameSprite):
                current_id = (current_id + 1) % (len(sfg.SPRITE_SETTING_LIST) + 1) or 1
            new_object = Enemy(sfg.SPRITE_SETTING_MAPPING[current_id], (-1000, -1000), 0)
        current_selected_object_ids[cfg.GameObject.TYPE_DYNAMIC] = current_id

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
    game_map = GameMap(chapter, map_setting)

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
    # some monsters is in ambush list
    ambush_init_list = map_setting.get("ambush_list", [])
    for ambush_init in ambush_init_list:
        ambush = Ambush(ambush_init["ambush"]["pos"], sfg.Ambush.SURROUND_AREA_WIDTH,
            sfg.Ambush.ENTER_AREA_WIDTH, ambush_init["ambush"]["type"])
        for monster_init in ambush_init["monsters"]:
            monster_id, pos, direct = monster_init["id"], monster_init["pos"], monster_init["direction"]
            monster = Enemy(sfg.SPRITE_SETTING_MAPPING[monster_id], pos, direct)
            game_world.add_object(monster)
            ambush.add(monster)
        game_world.ambush_list.append(ambush)

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
                    if object_can_be_shift(selected_object) \
                        and put_down_selected_object(selected_object, game_world):
                        selected_object = None
                    elif isinstance(selected_object, Ambush) \
                        and put_down_ambush(selected_object, game_world):
                        selected_object = None

                if event.key == sfg.MapEditor.KEY_STATIC_OBJECT:
                    # static object
                    selected_object = selected_object_shift(selected_object, cfg.GameObject.TYPE_STATIC)
                elif event.key == sfg.MapEditor.KEY_ENEMY:
                    # enemy
                    selected_object = selected_object_shift(selected_object, cfg.GameObject.TYPE_DYNAMIC)
                elif event.key == sfg.MapEditor.KEY_AMBUSH:
                    # ambush
                    selected_object = mouse_ambush_toggle(selected_object)

                if event.key == sfg.MapEditor.KEY_ERASE_SELECTED_OBJECT:
                    selected_object = None

                if event.key == sfg.MapEditor.KEY_TURN_DIRECTION:
                    if isinstance(selected_object, GameSprite):
                        selected_object = turn_sprite_direction(selected_object)

                key_mods = pygame.key.get_mods()
                if key_mods & KMOD_CTRL and event.key == sfg.MapEditor.KEY_CTRL_SAVE:
                    # ctrl+s to save map setting
                    change_map_setting(map_setting, game_world, game_map)
                    util.save_map_setting(chapter, map_setting)
                    print "save chapter %s map setting" % chapter

                if key_mods & KMOD_ALT:

                    # debug draw switch
                    if event.key == sfg.MapEditor.KEY_ALT_SWITCH_POS:
                        DEBUG_DRAW["pos"] = not DEBUG_DRAW["pos"]
                    elif event.key == sfg.MapEditor.KEY_ALT_SWITCH_AREA:
                        DEBUG_DRAW["area"] = not DEBUG_DRAW["area"]
                    elif event.key == sfg.MapEditor.KEY_ALT_SWITCH_WAYPOINT:
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
                set_ambush_follow_mouse(map_pos_for_mouse, selected_object)

        game_map.draw(camera)

        # draw ambush before all objects, because they are "close" to the floor
        for ambush in game_world.ambush_list:
            ambush.draw(camera)

        for sp in sorted(game_world.yield_all_objects(), key=lambda sp: sp.pos.y):
            if sp.setting.GAME_OBJECT_TYPE == cfg.GameObject.TYPE_DYNAMIC:
                sp.animation.adjust_rect()
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
                if isinstance(selected_object, GameSprite):
                    selected_object.animation.draw_shadow(camera)
                    selected_object.animation.image = selected_object.animation.sprite_image_contoller.get_surface(
                        cfg.SpriteAction.STAND)[selected_object.direction]
                selected_object.draw(camera)
            
            elif isinstance(selected_object, Ambush):
                camera.screen.blit(sfg.Font.ARIAL_32.render("Ambush", True, pygame.Color("black")), (5, 5))
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
        pygame.quit()

    run(args.chapter)
    pygame.quit()
