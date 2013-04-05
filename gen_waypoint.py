import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
import etc.setting as sfg
import etc.constant as cfg
import os
from base import util

pygame.init()

WAYPOINTS_DIR = sfg.WayPoint.DIR
bounding_box = pygame.Rect(sfg.WayPoint.BOUNDING_BOX_RECT)


def gen_chapter_waypoints(chapter):
    blocks = []
    waypoints = []

    map_setting = util.load_map_setting(chapter)
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
                waypoints.append((fx, fy))


    filename = "%s.txt" % chapter
    fp = open(os.path.join(WAYPOINTS_DIR, filename), "w")
    for wp in waypoints:
        fp.write("%s\t%s\n" % wp)

    print "generate waypoints %s success" % filename

    fp.close()



if __name__ == "__main__":
    for chapter in sfg.GameMap.CHAPTERS:
        gen_chapter_waypoints(chapter)

    print "finish all waypoints"
