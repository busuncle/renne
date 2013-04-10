import os
import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
from pygame.transform import smoothscale
from base.util import ImageController
import etc.setting as sfg



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
        self.is_block = setting.IS_BLOCK
        self.is_view_block = setting.IS_VIEW_BLOCK
        self.image = self.static_images.get(setting.IMAGE_KEY).convert_alpha().subsurface(
            Rect(setting.IMAGE_RECT)
        )
        self.rect = self.image.get_rect()
        self.adjust_rect()
        self.area = pygame.Rect(setting.AREA_RECT)
        self.area.center = pos


    def adjust_rect(self):
        self.rect.center = (self.pos[0], self.pos[1] / 2 + self.setting.IMAGE_POS_DELTA_Y)


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


    def yield_objects_in_screen(self, camera):
        for obj in self.sprites():
            if hasattr(obj, "rect"):
                rect = obj.rect
            else:
                rect = obj.animation.rect

            if rect.colliderect(camera.rect):
                yield obj


    def draw(self, camera):
        #objs = sorted(self.sprites(), key=lambda sp: sp.pos.y)
        objs = sorted(self.yield_objects_in_screen(camera), key=lambda sp: sp.pos.y)
        for v in objs:
            v.draw(camera)


