import os
import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
from pygame.transform import smoothscale
from base.util import ImageController
from base import constant as cfg
from etc import setting as sfg



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


    def update(self):
        for i, sp in enumerate(self.dynamic_objects):
            if sp.status["hp"] == cfg.SpriteStatus.VANISH:
                self.dynamic_objects.pop(i)


    def draw(self, camera):
        # only sort dynamic objects, static object is sorted in nature and no longer change 
        # the algorithm is inspired by merge sort
        self.dynamic_objects.sort(key=lambda obj: obj.pos.y)

        # draw shawdow first
        for sp in self.dynamic_objects:
            # adjust_rect by the way
            sp.adjust_rect()
            sp.animation.draw_shadow(camera)
            if sp.setting.ATTACKTYPE in cfg.SpriteAttackType.HAS_MAGIC_SKILLS:
                for magic in sp.attacker.magic_list:
                    for msp in magic.magic_sprites:
                        msp.draw_shadow(camera)

        dy_idx = 0
        st_idx = 0
        while dy_idx < len(self.dynamic_objects) and st_idx < len(self.static_objects):
            if self.static_objects[st_idx].pos.y <= self.dynamic_objects[dy_idx].pos.y:
                if self.static_objects[st_idx].rect.colliderect(camera.rect):
                    self.static_objects[st_idx].draw(camera)
                st_idx += 1

            else:
                if self.dynamic_objects[dy_idx].animation.rect.colliderect(camera.rect):
                    self.dynamic_objects[dy_idx].draw(camera)
                dy_idx += 1

        while dy_idx < len(self.dynamic_objects):
            if self.dynamic_objects[dy_idx].animation.rect.colliderect(camera.rect):
                self.dynamic_objects[dy_idx].draw(camera)
            dy_idx += 1

        while st_idx < len(self.static_objects):
            if self.static_objects[st_idx].rect.colliderect(camera.rect):
                self.static_objects[st_idx].draw(camera)
            st_idx += 1
