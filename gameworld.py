import os
import weakref
import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
from pygame.transform import smoothscale
from base.util import ImageController, Blink
from animation import get_shadow_image
from base import constant as cfg
from etc import setting as sfg



class GameMap(object):
    tile_images = ImageController(sfg.TILE_IMAGES[0])
    tile_images.add_from_list(sfg.TILE_IMAGES[1])
    def __init__(self, chapter, size, tiles_setting):
        self.chapter = chapter
        self.size = size
        #self.map_tiles = weakref.WeakValueDictionary()
        self.map_tiles = {}
        self.waypoints = self.load_waypoints(chapter)
        self.init_map_titles(tiles_setting)


    def load_waypoints(self, chapter):
        res = set()
        waypoints_file = os.path.join(sfg.WayPoint.DIR, "%s.txt" % chapter)
        if os.path.exists(waypoints_file):
            fp = open(waypoints_file)
            for line in fp:
                x, y = line.strip().split("\t")
                res.add((float(x), float(y)))
            fp.close()

        return res


    def init_map_titles(self, map_tile_setting):
        tile_cache = weakref.WeakValueDictionary()
        for y, tile_row in enumerate(map_tile_setting): 
            for x, tile_id in enumerate(tile_row):
                tile = tile_cache.get(tile_id)
                if not tile:
                    tile = self.tile_images.get(tile_id).convert_alpha()
                    tile = smoothscale(tile, (tile.get_width(), tile.get_height() / 2))
                    tile_cache[tile_id] = tile
                w, h = tile.get_width(), tile.get_height()
                self.map_tiles[(w * x, h * y)] = tile


    def draw(self, camera):
        for (x, y), tile in self.map_tiles.iteritems():
            if x + sfg.GameMap.TILE_SIZE < camera.rect.x or x > camera.rect.x + camera.rect.width \
                or y + sfg.GameMap.TILE_SIZE < camera.rect.y or y > camera.rect.y + camera.rect.height:
                    continue

            camera.screen.blit(tile, (x - camera.rect.x, y - camera.rect.y))



class StaticObject(pygame.sprite.DirtySprite):
    static_images = ImageController(sfg.STATIC_OBJECT_IMAGES[0])
    static_images.add_from_list(sfg.STATIC_OBJECT_IMAGES[1])

    def __init__(self, setting, pos):
        super(StaticObject, self).__init__()
        self.setting = setting
        self.pos = Vector2(pos)
        self.image = self.static_images.get(setting.IMAGE_KEY).convert_alpha().subsurface(
            Rect(setting.IMAGE_RECT)
        )
        self.rect = self.image.get_rect()
        self.adjust_rect()
        self.area = pygame.Rect(setting.AREA_RECT)
        self.area.center = pos
        self.status = cfg.StaticObject.STATUS_NORMAL
        if self.setting.IS_ELIMINABLE:
            # the object is eliminable, we should make it blink-blink look!
            self.image_mix = None
            self.shadow_image = get_shadow_image(setting.SHADOW_INDEX)
            self.shadow_rect_delta_y = setting.SHADOW_RECT_DELTA_Y
            self.blink = Blink(sfg.Effect.BLINK_RATE2, sfg.Effect.BLINK_DEPTH_SECTION2)


    def adjust_rect(self):
        self.rect.center = (self.pos[0], self.pos[1] * 0.5 - self.setting.POS_RECT_DELTA_Y)


    def update(self, passed_seconds):
        if self.setting.IS_ELIMINABLE:
            self.image_mix = self.blink.make(self.image, passed_seconds)


    def draw_shadow(self, camera):
        shd_rect = self.shadow_image.get_rect()
        shd_rect.center = self.area.center
        camera.screen.blit(self.shadow_image,
            (shd_rect.x - camera.rect.x, shd_rect.y * 0.5 - camera.rect.y - self.shadow_rect_delta_y))


    def draw(self, camera):
        if not self.rect.colliderect(camera.rect):
            return

        if self.setting.IS_ELIMINABLE and self.image_mix is not None:
            camera.screen.blit(self.image_mix,
                (self.rect.left - camera.rect.left, self.rect.top - camera.rect.top))
        else:
            camera.screen.blit(self.image, 
                (self.rect.left - camera.rect.left, self.rect.top - camera.rect.top))



class StaticObjectGroup(pygame.sprite.LayeredDirty):
    def __init__(self):
        super(StaticObjectGroup, self).__init__()

    def draw(self, surface):
        for obj in self.sprites():
            obj.draw(surface)



class GameWorld(pygame.sprite.LayeredDirty):
    # containing all sprites in the world
    def __init__(self):
        super(GameWorld, self).__init__()
        self.static_objects = []
        self.dynamic_objects = []


    def yield_all_objects(self):
        # use a generator instead of list operator +
        for obj in self.static_objects:
            yield obj
        for obj in self.dynamic_objects:
            yield obj


    def add_object(self, game_object):
        if game_object.setting.GAME_OBJECT_TYPE == cfg.GameObject.TYPE_DYNAMIC:
            self.dynamic_objects.append(game_object)
        else:
            self.static_objects.append(game_object)


    def remove_object(self, game_object):
        if game_object.setting.GAME_OBJECT_TYPE == cfg.GameObject.TYPE_DYNAMIC:
            self.dynamic_objects.remove(game_object)
        else:
            self.static_objects.remove(game_object)


    def batch_add(self, game_objects):
        for obj in game_objects:
            self.add_object(obj)

        self.dynamic_objects.sort(key=lambda obj: obj.pos.y)
        self.static_objects.sort(key=lambda obj: obj.pos.y)


    def update(self, passed_seconds):
        for i, obj in enumerate(self.static_objects):
            if obj.setting.IS_ELIMINABLE:
                obj.update(passed_seconds)
            if obj.status == cfg.StaticObject.STATUS_VANISH:
                self.static_objects.pop(i)

        for i, sp in enumerate(self.dynamic_objects):
            if sp.status["hp"] == cfg.SpriteStatus.VANISH:
                self.dynamic_objects.pop(i)

            if sp.setting.ID in sfg.SPRITES_WITH_MAGIC_SKILL:
                for i, magic in enumerate(sp.attacker.magic_list):
                    if magic.status == cfg.Magic.STATUS_VANISH:
                        sp.attacker.magic_list.pop(i)
                    else:
                        # for every magic, do some status update 
                        # and damage calculation among all the sprites 
                        magic.update(passed_seconds)

                # adhoc code for leon's hell claw tips
                if sp.setting.ID == sfg.LeonHardt.ID and sp.attacker.method == "hell_claw" \
                    and sp.attacker.current_magic is not None:
                    sp.attacker.update_hell_claw_tips(passed_seconds)

            if sp.setting.ID in sfg.SPRITES_WITH_AMMO:
                sp.attacker.update_ammo(passed_seconds)


    def draw(self, camera):
        movings = []
        movings.extend(self.dynamic_objects)

        # draw shawdow first
        for sp in self.dynamic_objects:
            # adjust_rect by the way
            sp.adjust_rect()
            sp.animation.draw_shadow(camera)
            if sp.setting.ID in sfg.SPRITES_WITH_MAGIC_SKILL:
                for magic in sp.attacker.magic_list:
                    # magic sprite is dynamic objects too, put them into movings
                    movings.extend(magic.magic_sprites)
                    for msp in magic.magic_sprites:
                        msp.draw_shadow(camera)

                # adhoc code for leon's hell claw tips
                if sp.setting.ID == sfg.LeonHardt.ID and sp.attacker.method == "hell_claw" \
                    and sp.attacker.current_magic is not None:
                    sp.attacker.draw_hell_claw_tips(camera)

            if sp.setting.ID in sfg.SPRITES_WITH_AMMO:
                movings.extend(sp.attacker.ammo_list)
                #for ammo in sp.attacker.ammo_list:
                #    ammo.draw_shadow(camera)
                

        for obj in self.static_objects:
            if obj.setting.IS_ELIMINABLE:
                obj.draw_shadow(camera)

        # only sort dynamic objects, static object is sorted in nature and no longer change 
        # the algorithm is inspired by merge sort
        movings.sort(key=lambda obj: obj.pos.y)

        dy_idx = 0
        st_idx = 0
        while dy_idx < len(movings) and st_idx < len(self.static_objects):
            if self.static_objects[st_idx].pos.y <= movings[dy_idx].pos.y:
                if self.static_objects[st_idx].rect.colliderect(camera.rect):
                    self.static_objects[st_idx].draw(camera)
                st_idx += 1

            else:
                movings[dy_idx].draw(camera)
                dy_idx += 1

        while dy_idx < len(movings):
            movings[dy_idx].draw(camera)
            dy_idx += 1

        while st_idx < len(self.static_objects):
            if self.static_objects[st_idx].rect.colliderect(camera.rect):
                self.static_objects[st_idx].draw(camera)
            st_idx += 1
