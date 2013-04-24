import os
import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
from pygame.transform import smoothscale
from base.util import ImageController
import etc.setting as sfg
import etc.constant as cfg



class GameMap(object):
    tile_images = ImageController(sfg.TILE_IMAGES[0])
    tile_images.add_from_list(sfg.TILE_IMAGES[1])
    def __init__(self, chapter, size, tiles_setting):
        self.chapter = chapter
        self.size = size
        self.map_tiles = []
        self.init_map_titles(tiles_setting)
        self.waypoints = self.load_waypoints(chapter)


    def load_waypoints(self, chapter):
        res = set()
        fp = open(os.path.join(sfg.WayPoint.DIR, "%s.txt" % chapter))
        for line in fp:
            x, y = line.strip().split("\t")
            res.add((float(x), float(y)))

        return res

    def init_map_titles(self, map_tile_setting):
        tile_cache = {}
        for y, tile_row in enumerate(map_tile_setting): 
            for x, tile_id in enumerate(tile_row):
                tile = tile_cache.get(tile_id)
                if not tile:
                    tile = self.tile_images.get(tile_id).convert_alpha()
                    tile = smoothscale(tile, (tile.get_width(), tile.get_height() / 2))
                    tile_cache[tile_id] = tile
                w, h = tile.get_width(), tile.get_height()
                self.map_tiles.append((tile, pygame.Rect(w * x, h * y, w, h)))


    def draw(self, camera):
        for tile, tile_rect in self.map_tiles:
            if tile_rect.colliderect(camera.rect):
                camera.screen.blit(tile, (tile_rect.left - camera.rect.left, tile_rect.top - camera.rect.top))



class GameStaticObject(pygame.sprite.DirtySprite):
    static_images = ImageController(sfg.STATIC_OBJECT_IMAGES[0])
    static_images.add_from_list(sfg.STATIC_OBJECT_IMAGES[1])

    def __init__(self, setting, pos):
        super(GameStaticObject, self).__init__()
        self.setting = setting
        self.pos = Vector2(pos)
        self.image = self.static_images.get(setting.IMAGE_KEY).convert_alpha().subsurface(
            Rect(setting.IMAGE_RECT)
        )
        self.rect = self.image.get_rect()
        self.adjust_rect()
        self.area = pygame.Rect(setting.AREA_RECT)
        self.area.center = pos


    def adjust_rect(self):
        self.rect.center = (self.pos[0], self.pos[1] / 2 - self.setting.POS_RECT_DELTA_Y)


    def draw(self, camera):
        camera.screen.blit(self.image, (self.rect.left - camera.rect.left, self.rect.top - camera.rect.top))



class GameStaticObjectGroup(pygame.sprite.LayeredDirty):
    def __init__(self):
        super(GameStaticObjectGroup, self).__init__()

    def draw(self, surface):
        for obj in self.sprites():
            obj.draw(surface)



class GameWorld(pygame.sprite.LayeredDirty):
    # containing all sprites in the world
    def __init__(self):
        super(GameWorld, self).__init__()
        self.static_objects = []
        self.dynamic_objects = []


    def all_objects(self):
        return self.static_objects + self.dynamic_objects


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


    def yield_objects_in_screen(self, camera):
        for obj in self.sprites():
            if obj.setting.GAME_OBJECT_TYPE == cfg.GameObject.TYPE_STATIC:
                rect = obj.rect
            else:
                # dynamic object, adjust its rect first!
                obj.adjust_rect()
                rect = obj.animation.rect

            if rect.colliderect(camera.rect):
                yield obj


    def draw2(self, camera):
        objs = sorted(self.yield_objects_in_screen(camera), key=lambda sp: sp.pos.y)
        for v in objs:
            v.draw(camera)


    def update(self):
        for i, sp in enumerate(self.dynamic_objects):
            if sp.status["hp"] == cfg.SpriteStatus.VANISH:
                self.dynamic_objects.pop(i)


    def draw(self, camera):
        # only sort dynamic objects, static object is sorted in nature and no longer change 
        # the algorithm is inspired by merge sort
        self.dynamic_objects.sort(key=lambda obj: obj.pos.y)
        dy_idx = 0
        st_idx = 0
        while dy_idx < len(self.dynamic_objects) and st_idx < len(self.static_objects):
            if self.static_objects[st_idx].pos.y <= self.dynamic_objects[dy_idx].pos.y:
                if self.static_objects[st_idx].rect.colliderect(camera.rect):
                    self.static_objects[st_idx].draw(camera)
                st_idx += 1

            else:
                self.dynamic_objects[dy_idx].adjust_rect()
                if self.dynamic_objects[dy_idx].animation.rect.colliderect(camera.rect):
                    self.dynamic_objects[dy_idx].draw(camera)
                dy_idx += 1

        while dy_idx < len(self.dynamic_objects):
            self.dynamic_objects[dy_idx].adjust_rect()
            if self.dynamic_objects[dy_idx].animation.rect.colliderect(camera.rect):
                self.dynamic_objects[dy_idx].draw(camera)
            dy_idx += 1

        while st_idx < len(self.static_objects):
            if self.static_objects[st_idx].rect.colliderect(camera.rect):
                self.static_objects[st_idx].draw(camera)
            st_idx += 1
