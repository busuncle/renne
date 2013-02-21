import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
import etc.setting as sfg
import etc.constant as cfg
import os

pygame.init()

WAYPOINTS_DIR = sfg.WayPoint.DIR
bounding_box = pygame.Rect(sfg.WayPoint.BOUNDING_BOX_RECT)



if __name__ == "__main__":
    for n, static_objs_desc in sfg.GameMap.STATIC_OBJECTS.iteritems():
        blocks = []
        waypoints = []

        for t, p in static_objs_desc:
            static_obj_setting = sfg.STATIC_OBJECT_SETTING_MAPPING[t]
            if not static_obj_setting.IS_BLOCK:
                continue

            pos = Vector2(p)
            rect = pygame.Rect(static_obj_setting.AREA_RECT)
            rect.center = pos
            blocks.append(rect)


        for x in xrange(0, sfg.GameMap.SIZE[n][0], sfg.WayPoint.STEP_WIDTH):
            for y in xrange(0, sfg.GameMap.SIZE[n][1], sfg.WayPoint.STEP_WIDTH):
                fx, fy = map(float, (x, y))
                bounding_box.center = (fx, fy)
                if bounding_box.collidelist(blocks) == -1:
                    waypoints.append((fx, fy))


        filename = "%s.txt" % n
        fp = open(os.path.join(WAYPOINTS_DIR, filename), "w")
        for wp in waypoints:
            fp.write("%s\t%s\n" % wp)

        print "%s success" % filename

        fp.close()

    print "finish all waypoints"
