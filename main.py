import pygame
from pygame.locals import *
from time import time
from gamesprites import Renne, GameSpritesGroup, enemy_in_one_screen, ENEMY_CLASS_MAPPING, Ambush
from base import constant as cfg
from etc import setting as sfg
from etc import ai_setting as ai
from gameworld import GameWorld, GameMap, StaticObjectGroup, StaticObject
from gamedirector import GameDirector, Menu, bg_box, start_game, loading_chapter_picture, end_game
from renderer import Camera
import debug_tools
from base import util
import sys



renne_dirlock = util.DirLock("renne_running.lock")
if not renne_dirlock.lock():
    print "renne is already running"
    sys.exit(0)


screen = sfg.Screen.DEFAULT_SCREEN
pygame.display.set_caption("Renne")
pygame.display.set_icon(pygame.image.load(sfg.RENNE_IMAGE_FILENAME).convert_alpha())


COMMAND_DEBUG_MODE = False
COMMAND_DEBUG_OPTIONS = {}


util.prepare_data_related_folder()



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
            res = start_game(screen)
        else:
            chapter = sfg.GameMap.CHAPTERS[i]
            loading_chapter_picture(screen)
            res = enter_chapter(screen, chapter, renne)

        bg_box.stop()

        status = res["status"]
        if status == cfg.GameControl.NEXT:
            i += 1
            renne.recover()
        elif status == cfg.GameControl.AGAIN:
            renne.recover()
        elif status == cfg.GameControl.MAIN:
            i = 0
        elif status == cfg.GameControl.QUIT:
            return
        elif status == cfg.GameControl.CONTINUE:
            i = res["current_chapter"] + 1

    end_game(screen)



def enter_chapter(screen, chapter, renne):
    map_setting = util.load_map_setting(chapter)

    camera = Camera(screen, map_size=map_setting["size"])
    game_world = GameWorld()
    allsprites = GameSpritesGroup()
    enemies = GameSpritesGroup()
    static_objects = StaticObjectGroup()
    game_map = GameMap(chapter, map_setting)

    # load hero
    renne.place(map_setting["hero"]["pos"], map_setting["hero"]["direction"])
    renne.activate(allsprites, enemies, static_objects, game_map)

    # load monsters
    monster_init_list = map_setting["monsters"]
    for monster_init in monster_init_list:
        monster_id, pos, direct = monster_init["id"], monster_init["pos"], monster_init["direction"]
        monster_setting = sfg.SPRITE_SETTING_MAPPING[monster_id]
        EnemyClass = ENEMY_CLASS_MAPPING[monster_id]
        monster = EnemyClass(monster_setting, pos, direct)
        monster_ai_setting = ai.AI_MAPPING[monster_id]
        monster.activate(monster_ai_setting, allsprites, renne, static_objects, game_map)

        enemies.add(monster)

    # load ambush
    game_world.ambush_list = []
    ambush_init_list = map_setting.get("ambush_list", [])
    for ambush_init in ambush_init_list:
        # only add monsters to ambush, when hero enter ambush, add it to enemy group
        ambush = Ambush(ambush_init["ambush"]["pos"], sfg.Ambush.SURROUND_AREA_WIDTH,
            sfg.Ambush.ENTER_AREA_WIDTH, ambush_init["ambush"]["type"])

        for monster_init in ambush_init["monsters"]:
            monster_id, pos, direct = monster_init["id"], monster_init["pos"], monster_init["direction"]
            monster_setting = sfg.SPRITE_SETTING_MAPPING[monster_id]
            EnemyClass = ENEMY_CLASS_MAPPING[monster_id]
            monster = EnemyClass(monster_setting, pos, direct)
            ambush.add(monster)

        ambush.init_sprite_status()
        game_world.ambush_list.append(ambush)

    # load static objects
    chapter_static_objects = map_setting["static_objects"]
    for static_obj_init in chapter_static_objects:
        t, p = static_obj_init["id"], static_obj_init["pos"]
        static_obj = StaticObject(sfg.STATIC_OBJECT_SETTING_MAPPING[t], p)
        static_objects.add(static_obj)

    allsprites.add(renne)
    allsprites.add(enemies)

    game_world.batch_add(allsprites)
    game_world.batch_add(static_objects)

    game_director = GameDirector(chapter, renne, enemies)

    if COMMAND_DEBUG_MODE:
        # skip the init status in command debug mode
        game_director.status = cfg.GameStatus.IN_PROGRESS

    clock = pygame.time.Clock()
    running = True
    last_direct_key_up = None
    one_pressed_keys = dict((k, {"pressed": False, "cd": 0}) for k in sfg.UserKey.ONE_PRESSED_KEYS)
    while running:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return {"status": cfg.GameControl.QUIT}

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if game_director.status == cfg.GameStatus.IN_PROGRESS:
                        game_director.status = cfg.GameStatus.PAUSE
                        bg_box.pause()
                        game_director.menu.index = 0
                    elif game_director.status == cfg.GameStatus.PAUSE:
                        game_director.status = cfg.GameStatus.IN_PROGRESS
                        bg_box.unpause()

                if event.key == K_RETURN:
                    if game_director.status == cfg.GameStatus.HERO_WIN:
                        util.save_chapter_win_screen_image(chapter, camera.screen)
                        dat = util.load_auto_save() or {}
                        dat["current_chapter"] = chapter
                        dat.setdefault("chapter_detail", {})
                        dat["chapter_detail"].setdefault(chapter, {})
                        dat["chapter_detail"][chapter]["total_score"] \
                            = game_director.achievement.chapter_score.next_value
                        util.auto_save(dat)
                        return {"status": cfg.GameControl.NEXT}
                    elif game_director.status == cfg.GameStatus.HERO_LOSE:
                        return {"status": cfg.GameControl.AGAIN}
                    elif game_director.status == cfg.GameStatus.PAUSE:
                        if game_director.menu.current_menu() == "CONTINUE":
                            game_director.status = cfg.GameStatus.IN_PROGRESS
                            bg_box.unpause()
                        elif game_director.menu.current_menu() == "MAIN":
                            return {"status": cfg.GameControl.MAIN}
                        elif game_director.menu.current_menu() == "QUIT":
                            return {"status": cfg.GameControl.QUIT}

                if event.key in sfg.UserKey.DIRECTION_KEYS:
                    if last_direct_key_up is not None:
                        if event.key == last_direct_key_up[0] \
                            and time() - last_direct_key_up[1] < sfg.UserKey.RUN_THRESHOLD \
                            and not renne.locked():
                            # adhoc for special key event
                            renne.action = cfg.HeroAction.RUN

                if event.key in one_pressed_keys and one_pressed_keys[event.key]["cd"] == 0:
                    one_pressed_keys[event.key]["pressed"] = True
                    one_pressed_keys[event.key]["cd"] = 0.22

                if game_director.status == cfg.GameStatus.PAUSE:
                    game_director.menu.update(event.key)

            if event.type == KEYUP:
                if event.key in sfg.UserKey.DIRECTION_KEYS:
                    last_direct_key_up = (event.key, time())

        pressed_keys = pygame.key.get_pressed()
        renne.event_handle(pressed_keys, one_pressed_keys, external_event=game_director.status)

        for enemy in enemies:
            if enemy_in_one_screen(renne, enemy):
                enemy.event_handle(pressed_keys, external_event=game_director.status)

        time_passed = clock.tick(sfg.FPS)
        passed_seconds = time_passed * 0.001

        for k in one_pressed_keys:
            one_pressed_keys[k]["pressed"] = False
            one_pressed_keys[k]["cd"] = max(one_pressed_keys[k]["cd"] - passed_seconds, 0)

        # update renne, enemies, game_director in sequence
        renne.update(passed_seconds, external_event=game_director.status)
        for enemy in enemies:
            if enemy_in_one_screen(renne, enemy):
                enemy.update(passed_seconds, external_event=game_director.status)

        if game_director.status != cfg.GameStatus.PAUSE:
            game_world.update(passed_seconds)

        # check ambush status, only one ambush can be enter in one time
        if game_director.status == cfg.GameStatus.ENTER_AMBUSH:
            game_world.active_ambush.update(passed_seconds)
            if game_world.active_ambush.status == cfg.Ambush.STATUS_FINISH:
                game_director.status = cfg.GameStatus.IN_PROGRESS
                game_world.ambush_list.remove(game_world.active_ambush)
                game_world.active_ambush = None
        else:
            for ambush in game_world.ambush_list:
                if ambush.enter(renne):
                    renne.set_emotion(cfg.SpriteEmotion.ALERT)
                    # only one ambush is active
                    game_director.status = cfg.GameStatus.ENTER_AMBUSH
                    game_world.active_ambush = ambush
                    for monster in ambush:
                        monster_ai_setting = ai.AI_MAPPING[monster.setting.ID]
                        monster.activate(monster_ai_setting, allsprites, 
                            renne, static_objects, game_map)
                        # monster in ambush will be in offence state, target at hero right now!
                        monster.brain.set_target(renne)
                        monster.brain.set_active_state(cfg.SpriteState.CHASE)
                        enemies.add(monster)

                    allsprites.add(enemies)
                    game_world.batch_add(ambush)
                    break

        game_director.update(passed_seconds)

        camera.screen_follow(renne.pos)

        # 3 layers from bottom to top: floor -> sprites in the playground -> game info(player hp, ep etc)
        game_map.draw(camera)
        game_world.draw(camera)
        game_director.draw(camera)

        if COMMAND_DEBUG_MODE or sfg.DEBUG_MODE:
            debug_tools.run_debug_by_option_list(COMMAND_DEBUG_OPTIONS,
                camera, game_world, game_map, clock)
            if COMMAND_DEBUG_OPTIONS["god"]:
                renne.hp = renne.setting.HP
                renne.mp = renne.setting.MP
                renne.sp = renne.setting.SP
                renne.attacker.refresh_skill()

        pygame.display.flip()



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

