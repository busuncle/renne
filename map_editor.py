import os
import pygame
from pygame.locals import *
from gamesprites import Renne, Enemy, GameSpritesGroup
from gameobjects.vector2 import Vector2
from gameworld import GameWorld, GameMap, GameStaticObjectGroup, GameStaticObject
from renderer import Camera
from base import util
import debug_tools
from base import constant as cfg
from etc import setting as sfg



PROJECT_ROOT = util.get_project_root()
assert os.path.basename(PROJECT_ROOT) == "renne"

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

    print "generate waypoints %s success" % filename

    fp.close()


def gen_chapter_waypoints(chapter, map_setting):
    bounding_box = pygame.Rect(sfg.WayPoint.BOUNDING_BOX_RECT)
    blocks = []
    waypoints = set()

    for t, p in map_setting["static_objects"]:
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
    # change mouse pos to map pos first
    for sp in game_world.all_objects():
        if sp.area.collidepoint(map_pos_for_mouse):
            return sp
    return None


def put_selected_object(selected_object, game_world):
    if selected_object is None:
        return True
    for sp in game_world.all_objects():
        if sp is selected_object:
            continue
        if selected_object.area.colliderect(sp.area):
            return False
    return True


def change_map_setting(map_setting, game_world):
    res = {"hero": None, "monsters": [], "static_objects": []}
    for sp in game_world.static_objects:
        x, y = map(int, sp.pos)
        res["static_objects"].append([sp.setting.ID, [x, y]])

    for sp in game_world.dynamic_objects:
        x, y = map(int, sp.pos)
        if isinstance(sp, Renne):
            res["hero"] = [[x, y], sp.direction]
        else:
            res["monsters"].append([sp.setting.ID, [x, y], sp.direction])

    map_setting.update(res)


def set_selected_object_follow_mouse(map_pos_for_mouse, selected_object):
    selected_object.area.center = map_pos_for_mouse
    selected_object.pos.x, selected_object.pos.y = map_pos_for_mouse
    selected_object.adjust_rect()
        


def mouse_object_toggle(selected_object, game_world):
    # None -> Enemy -> GameStaticObject -> None ... change in this circle
    new_selected = None
    if isinstance(selected_object, Renne):
        # Renne is not under this loop, do nothing and return it immediately
        return selected_object

    if selected_object is None:
        new_selected = Enemy(sfg.SPRITE_SETTING_MAPPING[1], (-1000, -1000), 0)
        game_world.add_object(new_selected)
    elif isinstance(selected_object, Enemy):
        game_world.remove_object(selected_object)
        new_selected = GameStaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[1], (-1000, -1000))
        game_world.add_object(new_selected)
    elif isinstance(selected_object, GameStaticObject):
        game_world.remove_object(selected_object)
        new_selected = None

    return new_selected


def selected_object_toggle(selected_object, game_world):
    if selected_object is None or isinstance(selected_object, Renne):
        # Renne and None are not in toggle loop
        return selected_object

    game_world.remove_object(selected_object)
    if isinstance(selected_object, Enemy):
        new_object_id = (selected_object.setting.ID + 1) % (len(sfg.SPRITE_SETTING_LIST) + 1) or 1
        new_object = Enemy(sfg.SPRITE_SETTING_MAPPING[new_object_id], (-1000, -1000), 0)
    elif isinstance(selected_object, GameStaticObject):
        new_object_id = (selected_object.setting.ID + 1) % (len(sfg.STATIC_OBJECT_SETTING_LIST) + 1) or 1
        new_object = GameStaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[new_object_id], (-1000, -1000))
    game_world.add_object(new_object)
        
    return new_object


def create_new_instance(selected_object):
    if isinstance(selected_object, Enemy):
        return Enemy(sfg.SPRITE_SETTING_MAPPING[selected_object.setting.ID], 
            selected_object.pos.as_tuple(), 0)
    elif isinstance(selected_object, GameStaticObject):
        return GameStaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[selected_object.setting.ID],
            selected_object.pos.as_tuple())
    raise Exception("invalid object to create")


def turn_sprite_direction(selected_object):
    if isinstance(selected_object, Renne) or isinstance(selected_object, Enemy):
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
    renne = Renne(sfg.Renne, *map_setting["hero"])
    game_world.add_object(renne)

    # load monsters
    monster_init = map_setting.get("monsters", [])
    for monster_id, pos, direct in monster_init:
        monster = Enemy(sfg.SPRITE_SETTING_MAPPING[monster_id], pos, direct)
        game_world.add_object(monster)

    # load static objects
    chapter_static_objects = map_setting.get("static_objects", [])
    for t, p in chapter_static_objects:
        static_obj = GameStaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[t], p)
        game_world.add_object(static_obj)


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
                    if put_selected_object(selected_object, game_world):
                        selected_object = None

                if event.key == K_q:
                    selected_object = mouse_object_toggle(selected_object, game_world)

                if event.key == K_w:
                    selected_object = selected_object_toggle(selected_object, game_world)

                if event.key == K_e:
                    if selected_object is not None:
                        game_world.remove_object(selected_object)
                        selected_object = None

                if event.key == K_t:
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

                if key_mods & KMOD_ALT:
                    if event.key == K_p:
                        DEBUG_DRAW["pos"] = not DEBUG_DRAW["pos"]
                    if event.key == K_a:
                        DEBUG_DRAW["area"] = not DEBUG_DRAW["area"]
                    if event.key == K_z:
                        DEBUG_DRAW["waypoints"] = not DEBUG_DRAW["waypoints"]

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    # left click
                    if selected_object is None:
                        # pick up "this" unit if the mouse is over it
                        selected_object = select_unit(map_pos_for_mouse, game_world)
                    else:
                        # put down the current selected unit if no "collision" happen
                        if put_selected_object(selected_object, game_world):
                            if pygame.key.get_mods() & KMOD_CTRL:
                                selected_object = create_new_instance(selected_object)
                                game_world.add_object(selected_object)
                            else:
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
        passed_seconds = time_passed / 1000.0

        camera.screen_move(key_vec, sfg.MapEditor.SCREEN_MOVE_SPEED, passed_seconds)
        if selected_object is not None:
            set_selected_object_follow_mouse(map_pos_for_mouse, selected_object)

        game_map.draw(camera)

        for sp in sorted(game_world.all_objects(), key=lambda sp: sp.pos.y):
            if sp.setting.GAME_OBJECT_TYPE == cfg.GameObject.TYPE_DYNAMIC:
                # select current image for corresponding direction
                sp.adjust_rect()
                image = sp.animation.sprite_image_contoller.get_surface(cfg.SpriteAction.STAND)[sp.direction]
                rect = sp.animation.rect
                shd_image = sp.animation.shadow_image
                shd_rect = sp.animation.shadow_rect 
                camera.screen.blit(shd_image, (shd_rect.x - camera.rect.x, shd_rect.y - camera.rect.y))
                camera.screen.blit(image, (rect.x - camera.rect.x, rect.y - camera.rect.y))
                if sp.setting.ROLE == cfg.SpriteRole.ENEMY:
                    sp.animation.draw_hp_bar(camera)
            else:
                image = sp.image
                rect = sp.rect
                camera.screen.blit(image, (rect.x - camera.rect.x, rect.y - camera.rect.y))


        if selected_object is not None:
            selected_object_name = sfg.Font.ARIAL_32.render(
                selected_object.setting.NAME, True, pygame.Color("black"))
            camera.screen.blit(selected_object_name, (5, 5))

        # debug drawings
        for sp in game_world.all_objects():
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
