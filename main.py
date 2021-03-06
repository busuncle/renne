# -*- coding: gbk -*-

import pygame
from pygame.locals import *
from time import time
from random import choice, gauss, randint
from gamesprites import Renne, Joshua, GameSpritesGroup, enemy_in_one_screen
from gamesprites import EnemyGroup, ENEMY_CLASS_MAPPING
from base import constant as cfg
from etc import setting as sfg
from etc import ai_setting as ai
from gameworld import GameWorld, GameMap, StaticObjectGroup, StaticObject
from gamedirector import GameDirector, Menu, bg_box, start_game, loading_chapter_picture, end_game
from renderer import Camera
import debug_tools
from base import util
import sys



screen = sfg.Screen.DEFAULT_SCREEN
pygame.display.set_caption("Renne")
pygame.display.set_icon(pygame.image.load(sfg.RENNE_IMAGE_FILENAME).convert_alpha())


COMMAND_DEBUG_MODE = False
COMMAND_DEBUG_OPTIONS = {}


util.prepare_data_related_folder()



def main(args):
    # a singleton goes through the whole game
    if sfg.CONFIG["hero"] == "renne":
        hero = Renne(sfg.Renne, (0, 0), 0)
    else:
        hero = Joshua(sfg.Joshua, (0, 0), 0)

    if args.chapter is not None:
        # it's for debuging, only run 1 part and return immediately
        if args.chapter == 0:
            start_game(screen)
        elif args.chapter == -1:
            end_game(screen)
        else:
            enter_chapter(screen, args.chapter, hero)
        return

    res = {"status": cfg.GameControl.MAIN}
    i = -1
    while True:
        if i >= len(sfg.Chapter.ALL):
            break

        status = res["status"]

        if status == cfg.GameControl.NEXT:
            i += 1
            if i < len(sfg.Chapter.ALL):
                loading_chapter_picture(screen)
                hero.recover()
                chapter = sfg.Chapter.ALL[i]
                res = enter_chapter(screen, chapter, hero)

        elif status == cfg.GameControl.SUB_CHAPTER:
            chapter = res["chapter"]
            res = enter_chapter(screen, chapter, hero)

        elif status == cfg.GameControl.AGAIN:
            hero.recover()
            res = enter_chapter(screen, res["chapter"], hero)

        elif status == cfg.GameControl.MAIN:
            hero.exp = 0
            hero.recover(level=1)
            i = -1
            res = start_game(screen)

        elif status == cfg.GameControl.QUIT:
            return

        elif status == cfg.GameControl.CONTINUE:
            i = sfg.Chapter.ALL.index(res["save"]["current_chapter"]) + 1
            if i < len(sfg.Chapter.ALL):
                loading_chapter_picture(screen)
                hero.exp = res["save"]["exp"]
                hero.recover(res["save"]["level"])
                chapter = sfg.Chapter.ALL[i]
                res = enter_chapter(screen, chapter, hero)

        elif status == cfg.GameControl.DEAD_MODE:
            loading_chapter_picture(screen)
            hero.exp = 0
            hero.recover(level=1)
            res = enter_dead_mode(screen, hero)

    end_game(screen)



def enter_chapter(screen, chapter, hero):
    map_setting = util.load_map_setting(chapter)

    camera = Camera(screen, map_size=map_setting["size"])
    game_map = GameMap(chapter, map_setting)
    static_objects = StaticObjectGroup()
    allsprites = GameSpritesGroup()
    enemies = EnemyGroup(map_setting["monsters"], allsprites, hero, static_objects, game_map)
    game_world = GameWorld()

    # load hero
    hero.place(map_setting["hero"]["pos"], map_setting["hero"]["direction"])
    hero.activate(allsprites, enemies, static_objects, game_map)

    # load ambush
    game_world.init_ambush_list(map_setting.get("ambush_list", []))

    # load static objects
    chapter_static_objects = map_setting["static_objects"]
    for static_obj_init in chapter_static_objects:
        t, p = static_obj_init["id"], static_obj_init["pos"]
        static_obj = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[t], p)
        static_objects.add(static_obj)

    allsprites.add(hero)
    allsprites.add(enemies)

    game_world.batch_add(allsprites)
    game_world.batch_add(static_objects)

    game_director = GameDirector(chapter, hero, enemies)

    if COMMAND_DEBUG_MODE:
        # skip the init status in command debug mode
        game_director.status = cfg.GameStatus.IN_PROGRESS

    clock = pygame.time.Clock()
    running = True

    battle_keys= {}
    for k in sfg.UserKey.ONE_PRESSED_KEYS:
        battle_keys[k] = {"pressed": False, "cd": 0, "full_cd": sfg.UserKey.ONE_PRESSED_KEY_CD}
    for k in sfg.UserKey.CONTINUE_PRESSED_KEYS:
        battle_keys[k] = {"pressed": False}
    battle_keys["last_direct_key_up"] = {"key": None, "time": None}

    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return {"status": cfg.GameControl.QUIT}

            if event.type == KEYDOWN:
                if event.key == sfg.UserKey.PAUSE:
                    if game_director.status == cfg.GameStatus.IN_PROGRESS:
                        game_director.status = cfg.GameStatus.PAUSE
                        bg_box.pause()
                        game_director.menu.index = 0
                    elif game_director.status == cfg.GameStatus.PAUSE:
                        game_director.status = cfg.GameStatus.IN_PROGRESS
                        bg_box.unpause()

                if event.key == sfg.UserKey.OK:
                    if game_director.status == cfg.GameStatus.HERO_WIN:
                        util.save_chapter_win_screen_image(chapter, camera.screen)
                        dat = util.load_auto_save() or {}
                        dat["current_chapter"] = chapter
                        dat["level"] = hero.level
                        dat["exp"] = hero.exp
                        util.auto_save(dat)
                        return {"status": cfg.GameControl.NEXT}
                    elif game_director.status == cfg.GameStatus.HERO_LOSE:
                        return {"status": cfg.GameControl.AGAIN, "chapter": chapter}
                    elif game_director.status == cfg.GameStatus.PAUSE:
                        mark = game_director.menu.get_current_mark()
                        if mark == "continue":
                            game_director.status = cfg.GameStatus.IN_PROGRESS
                            bg_box.unpause()
                        elif mark == "main":
                            return {"status": cfg.GameControl.MAIN}
                        elif mark == "quit":
                            return {"status": cfg.GameControl.QUIT}

                if event.key in sfg.UserKey.ONE_PRESSED_KEYS and battle_keys[event.key]["cd"] == 0:
                    battle_keys[event.key]["pressed"] = True
                    battle_keys[event.key]["cd"] = battle_keys[event.key]["full_cd"]

                if game_director.status == cfg.GameStatus.PAUSE:
                    game_director.menu.update(event.key)

            if event.type == KEYUP:
                if event.key in sfg.UserKey.DIRECTION_KEYS:
                    battle_keys["last_direct_key_up"]["key"] = event.key
                    battle_keys["last_direct_key_up"]["time"] = time()

        pressed_keys = pygame.key.get_pressed()
        for k in sfg.UserKey.CONTINUE_PRESSED_KEYS:
            battle_keys[k]["pressed"] = pressed_keys[k]

        hero.event_handle(battle_keys, external_event=game_director.status)
        for enemy in enemies:
            if enemy_in_one_screen(hero, enemy):
                enemy.event_handle(external_event=game_director.status)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed * 0.001

        for k in sfg.UserKey.ONE_PRESSED_KEYS:
            battle_keys[k]["pressed"] = False
            battle_keys[k]["cd"] = max(battle_keys[k]["cd"] - passed_seconds, 0)
        for k in sfg.UserKey.CONTINUE_PRESSED_KEYS:
            battle_keys[k]["pressed"] = False

        # update hero, enemies, game_director in sequence
        hero.update(passed_seconds, external_event=game_director.status)
        for enemy in enemies:
            if enemy_in_one_screen(hero, enemy):
                enemy.update(passed_seconds, external_event=game_director.status)

        game_world.update(passed_seconds, game_director.status)
        game_world.update_ambush(passed_seconds, game_director, hero, allsprites, enemies,
            static_objects, game_map)

        game_director.update(passed_seconds)

        camera.screen_follow(hero.pos)

        # 3 layers from bottom to top: floor -> sprites in the playground -> game info(player hp, ep etc)
        game_map.draw(camera)
        game_world.draw(camera)
        game_director.draw(camera)

        if COMMAND_DEBUG_MODE or sfg.DEBUG_MODE:
            debug_tools.run_debug_by_option_list(COMMAND_DEBUG_OPTIONS,
                camera, game_world, game_map, clock)
            if COMMAND_DEBUG_OPTIONS["god"]:
                hero.hp = hero.setting.HP
                hero.mp = hero.setting.MP
                hero.sp = hero.setting.SP
                hero.hp_status = hero.cal_sprite_status(hero.hp, hero.setting.HP)
                hero.attacker.refresh_skill()

        pygame.display.update()



def enter_dead_mode(screen, hero):

    # pre_loading sprite
    for mnstr_id in sfg.COMMON_MONSTER_ID_LIST:
        mnstr_sfg = sfg.SPRITE_SETTING_MAPPING[mnstr_id]
        mnstr = ENEMY_CLASS_MAPPING[mnstr_id](mnstr_sfg, (0, 0), cfg.Direction.SOUTH)

    map_setting = util.load_map_setting(sfg.DeadMode.MAP_CHAPTER)

    camera = Camera(screen, map_size=map_setting["size"])
    game_map = GameMap(sfg.DeadMode.MAP_CHAPTER, map_setting)
    static_objects = StaticObjectGroup()
    allsprites = GameSpritesGroup()
    enemies = EnemyGroup(map_setting["monsters"], allsprites, hero, static_objects, game_map)
    game_world = GameWorld()

    # load hero
    hero.place(map_setting["hero"]["pos"], map_setting["hero"]["direction"])
    hero.activate(allsprites, enemies, static_objects, game_map)

    # load static objects
    chapter_static_objects = map_setting["static_objects"]
    for static_obj_init in chapter_static_objects:
        t, p = static_obj_init["id"], static_obj_init["pos"]
        static_obj = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[t], p)
        static_objects.add(static_obj)

    allsprites.add(hero)
    allsprites.add(enemies)

    game_world.batch_add(allsprites)
    game_world.batch_add(static_objects)

    game_director = GameDirector(sfg.DeadMode.MAP_CHAPTER, hero, enemies)

    add_enemy_timer = util.Timer(sfg.DeadMode.ADD_ENEMY_TIME_DELTA)
    enemy_add_num = sfg.DeadMode.ENEMY_ADD_INIT_NUM
    enemy_add_delta = sfg.DeadMode.ENEMY_ADD_DELTA
    current_round = 1

    clock = pygame.time.Clock()
    running = True

    battle_keys= {}
    for k in sfg.UserKey.ONE_PRESSED_KEYS:
        battle_keys[k] = {"pressed": False, "cd": 0, "full_cd": sfg.UserKey.ONE_PRESSED_KEY_CD}
    for k in sfg.UserKey.CONTINUE_PRESSED_KEYS:
        battle_keys[k] = {"pressed": False}
    battle_keys["last_direct_key_up"] = {"key": None, "time": None}

    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return {"status": cfg.GameControl.QUIT}

            if event.type == KEYDOWN:
                if event.key == sfg.UserKey.PAUSE:
                    if game_director.status == cfg.GameStatus.IN_PROGRESS:
                        game_director.status = cfg.GameStatus.PAUSE
                        bg_box.pause()
                        game_director.menu.index = 0
                    elif game_director.status == cfg.GameStatus.PAUSE:
                        game_director.status = cfg.GameStatus.IN_PROGRESS
                        bg_box.unpause()

                if event.key == sfg.UserKey.OK:
                    if game_director.status == cfg.GameStatus.HERO_WIN:
                        pass
                    elif game_director.status == cfg.GameStatus.HERO_LOSE:
                        return {"status": cfg.GameControl.DEAD_MODE}
                    elif game_director.status == cfg.GameStatus.PAUSE:
                        mark = game_director.menu.get_current_mark()
                        if mark == "continue":
                            game_director.status = cfg.GameStatus.IN_PROGRESS
                            bg_box.unpause()
                        elif mark == "main":
                            return {"status": cfg.GameControl.MAIN}
                        elif mark == "quit":
                            return {"status": cfg.GameControl.QUIT}

                if event.key in sfg.UserKey.ONE_PRESSED_KEYS and battle_keys[event.key]["cd"] == 0:
                    battle_keys[event.key]["pressed"] = True
                    battle_keys[event.key]["cd"] = battle_keys[event.key]["full_cd"]

                if game_director.status == cfg.GameStatus.PAUSE:
                    game_director.menu.update(event.key)

            if event.type == KEYUP:
                if event.key in sfg.UserKey.DIRECTION_KEYS:
                    battle_keys["last_direct_key_up"]["key"] = event.key
                    battle_keys["last_direct_key_up"]["time"] = time()

        pressed_keys = pygame.key.get_pressed()
        for k in sfg.UserKey.CONTINUE_PRESSED_KEYS:
            battle_keys[k]["pressed"] = pressed_keys[k]

        hero.event_handle(battle_keys, external_event=game_director.status)
        for enemy in enemies:
            if enemy_in_one_screen(hero, enemy):
                enemy.event_handle(external_event=game_director.status)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed * 0.001

        for k in sfg.UserKey.ONE_PRESSED_KEYS:
            battle_keys[k]["pressed"] = False
            battle_keys[k]["cd"] = max(battle_keys[k]["cd"] - passed_seconds, 0)
        for k in sfg.UserKey.CONTINUE_PRESSED_KEYS:
            battle_keys[k]["pressed"] = False

        # update hero, enemies, game_director in sequence
        hero.update(passed_seconds, external_event=game_director.status)
        for enemy in enemies:
            if enemy_in_one_screen(hero, enemy):
                enemy.update(passed_seconds, external_event=game_director.status)

        game_world.update(passed_seconds, game_director.status)

        game_director.update(passed_seconds)

        # judge enenmy nums
        if len(enemies) == 0:
            if add_enemy_timer.is_begin():
                if add_enemy_timer.exceed():
                    add_enemy_timer.clear()
                    hero.set_emotion(cfg.SpriteEmotion.ALERT)
                    for _a_useless_var in xrange(enemy_add_num):
                        monster_id = choice(sfg.COMMON_MONSTER_ID_LIST)
                        monster_setting = sfg.SPRITE_SETTING_MAPPING[monster_id]
                        monster = ENEMY_CLASS_MAPPING[monster_id](monster_setting, 
                            (randint(int(game_map.size[0] * 0.3), int(game_map.size[0] * 0.7)),
                                randint(int(game_map.size[1] * 0.3), int(game_map.size[1] * 0.7))),
                            choice(cfg.Direction.ALL))
                        monster_ai_setting = ai.AI_MAPPING[monster_id]
                        monster.activate(monster_ai_setting, allsprites, hero, static_objects, game_map)
                        monster.brain.set_target(hero)
                        monster.brain.set_active_state(cfg.SpriteState.CHASE)
                        enemies.add(monster)
                        game_world.add_object(monster)

                    allsprites.add(enemies)

                    enemy_add_num = min(enemy_add_num + enemy_add_delta, sfg.DeadMode.ENEMY_ADD_MAX)

            else:
                add_enemy_timer.begin()
                current_round += 1
                
                new_foods = []
                for _is_a_useless_var in xrange(3):
                    food = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[
                        choice(sfg.FOOD_ID_LIST)], 
                        (randint(int(game_map.size[0] * 0.2), int(game_map.size[0] * 0.5)),
                            randint(int(game_map.size[1] * 0.3), int(game_map.size[1] * 0.6)))
                    )
                    new_foods.append(food)
                    static_objects.add(food)

                game_world.batch_add(new_foods)


        camera.screen_follow(hero.pos)

        # 3 layers from bottom to top: floor -> sprites in the playground -> game info(player hp, ep etc)
        game_map.draw(camera)
        game_world.draw(camera)
        game_director.draw(camera)

        # say how many enemies left
        enemy_left_info = sfg.Font.MSYH_32.render(u"ʣ���������%s" % len(enemies), True, pygame.Color("white"))
        screen.blit(enemy_left_info, sfg.DeadMode.ENEMY_LEFT_INFO_BLIT_POS)

        # say current round
        current_round_info = sfg.Font.MSYH_32.render(u"��%s��" % current_round, True, pygame.Color("white"))
        screen.blit(current_round_info, sfg.DeadMode.CURRENT_ROUND_INFO_BLIT_POS)

        if len(enemies) == 0 and add_enemy_timer.is_begin() and (not add_enemy_timer.exceed()):
            game_director.draw_count_down_number(camera, add_enemy_timer, sfg.DeadMode.ADD_ENEMY_TIME_DELTA)

        if COMMAND_DEBUG_MODE or sfg.DEBUG_MODE:
            debug_tools.run_debug_by_option_list(COMMAND_DEBUG_OPTIONS,
                camera, game_world, game_map, clock)
            if COMMAND_DEBUG_OPTIONS["god"]:
                hero.hp = hero.setting.HP
                hero.mp = hero.setting.MP
                hero.sp = hero.setting.SP
                hero.hp_status = hero.cal_sprite_status(hero.hp, hero.setting.HP)
                hero.attacker.refresh_skill()

        pygame.display.update()


if __name__ == "__main__":
    args = util.parse_command_line([
        (["-d", "--debug"], {"dest": "debug", "action": "store_true"}),
        (["-c", "--chapter"], {"dest": "chapter", "action": "store"}),
        (["--fps"], {"dest": "fps", "action": "store_true"}),
        (["--waypoints"], {"dest": "waypoints", "action": "store_true"}),
        (["--area"], {"dest": "area", "action": "store_true"}),
        (["--pos"], {"dest": "pos", "action": "store_true"}),
        (["--mute"], {"dest": "mute", "action": "store_true"}),
        (["--god"], {"dest": "god", "action": "store_true"}),
    ])
    COMMAND_DEBUG_MODE = args.debug is True
    COMMAND_DEBUG_OPTIONS["waypoints"] = args.waypoints
    COMMAND_DEBUG_OPTIONS["fps"] = args.fps
    COMMAND_DEBUG_OPTIONS["area"] = args.area
    COMMAND_DEBUG_OPTIONS["pos"] = args.pos
    COMMAND_DEBUG_OPTIONS["god"] = args.god
    if args.mute:
        sfg.Music.BACKGROUND_VOLUME = 0
        sfg.Music.SOUND_VOLUME = 0

    main(args)
    pygame.quit()

