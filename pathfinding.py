import pygame
from heapq import heappush, heappop
import os
from gameobjects.vector2 import Vector2
import etc.constant as cfg
import etc.setting as sfg



class Node(object):
    def __init__(self, coord, g, parent):
        # coord should be a tuple like a coordinate, eg: (1, 2)
        self._x, self._y = coord
        self._g = g
        self._parent = parent

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def g(self):
        return self._g

    @property
    def parent(self):
        return self._parent

    @property
    def coord(self):
        return (self._x, self._y)


class OpenList(object):
    def __init__(self):
        # saving (f, (x, y)), a priority queue order by f ascending
        self._heap = [] 
        # saving "(x, y): node" mapping, for quick lookup
        self._dict = {}
        
    def add_node(self, f, node):
        heappush(self._heap, (f, node.coord))
        self._dict[node.coord] = node

    def get_node(self, coord):
        return self._dict.get(coord, None)

    def pop_node(self):
        f, coord = heappop(self._heap)
        node = self._dict.get(coord, None)
        if node:
            # a trick for efficiency of lookup, that making self._heap not sync with self._dict, 
            # but it works without any problems
            del self._dict[coord]

        return coord, node

    def __len__(self):
        return len(self._heap)


class Astar(object):

    # an empirical value for limiting the size of close list
    MAX_SEARCHING_STEP = 100

    directs = {
        (-1.0, 0.0): 1.0,
        (-1.0, -1.0): 1.4,
        (0.0, -1.0): 1.0,
        (1.0, -1.0): 1.4,
        (1.0, 0.0): 1.0,
        (1.0, 1.0): 1.4,
        (0.0, 1.0): 1.0,
        (-1.0, 1.0): 1.4,
    }

    all_waypoints = {}

    def __init__(self, sprite):
        self.sprite = sprite
        self.chapter = sprite.game_map.chapter
        self.waypoints = self.all_waypoints.get(self.chapter)
        if self.waypoints is None:
            # lazy loading waypoints
            self.waypoints = self.load_waypoints(self.chapter)
            self.all_waypoints[self.chapter] = self.waypoints


    def load_waypoints(self, chapter):
        res = set()
        fp = open(os.path.join(sfg.WayPoint.DIR, "%s.txt" % chapter))
        for line in fp:
            x, y = line.strip().split("\t")
            res.add((float(x), float(y)))

        return res


    def gen_path(self, cur_node):
        path = [cur_node.coord, ]
        next_parent = cur_node.parent
        while next_parent is not None:
            path.append(next_parent.coord)
            next_parent = next_parent.parent

        return path[:-1] if len(path) > 1 else path


    def get_start_node(self, pos):
        # try 4 corners first
        x0, y0 = map(lambda v: v - v % sfg.WayPoint.STEP_WIDTH, pos.as_tuple())
        node = self.try_nearby_waypoints(x0, y0, 2)
        if node is None:
            # try a bigger area, i think it will return a valid node anyhow
            x0, y0 = map(lambda v: v - v % (sfg.WayPoint.STEP_WIDTH * 2), pos.as_tuple())
            node = self.try_nearby_waypoints(x0, y0, 4)
        return node


    def try_nearby_waypoints(self, x0, y0, steps):
        for i in xrange(0, steps):
            for j in xrange(0, steps):
                x = x0 + sfg.WayPoint.STEP_WIDTH * i
                y = y0 + sfg.WayPoint.STEP_WIDTH * j
                if (x, y) in self.waypoints:
                    return Node((x, y), 0, None)
        return None


    def find(self, target_coord, reach_delta):
        # target_coord should be a tuple like (x, y), representing the target coordinate on the map

        sp = self.sprite

        start = self.get_start_node(sp.pos)
        if start is None:
            return None

        target = Node(target_coord, 0, None)

        open_list = OpenList()
        close_list = set()

        open_list.add_node(0, start)

        direct_vec = Vector2()

        while len(open_list) > 0:
            (cur_x, cur_y), cur_node = open_list.pop_node()
            if (cur_x, cur_y) in close_list:
                continue

            close_list.add((cur_x, cur_y))

            if len(close_list) > self.MAX_SEARCHING_STEP:
                # pruning, reaching the max search step, return the most likely path
                # avoiding the exhaust of cpu
                print "impossible: %s" % len(close_list)
                path = self.gen_path(cur_node)
                return path

            # using manhattan distance to judge whether reaching the target for a non-grid map
            # a value little equal than a reach_delta is regarded as reaching the target
            if abs(cur_x - target.x) + abs(cur_y - target.y) < reach_delta:
                path = self.gen_path(cur_node)
                print "astar close list length: %s" % len(close_list)
                return path

            for vec, cost in self.directs.iteritems():
                direct_vec.x, direct_vec.y = vec
                direct_vec *= sfg.WayPoint.STEP_WIDTH
                next_x, next_y = cur_x + direct_vec.x, cur_y + direct_vec.y

                if not (0 <= next_x <= sp.game_map.size[0]) \
                    or not (0 <= next_y <= sp.game_map.size[1]):
                    continue

                if (next_x, next_y) in close_list:
                    continue

                if (next_x, next_y) not in self.waypoints:
                    continue

                next_g = cur_node.g + cost * sfg.WayPoint.STEP_WIDTH
                # manhattan distance
                next_h = abs(next_x - target.x) + abs(next_y - target.y)

                # astar heuristic search formula
                next_f = next_g + next_h
                old_node = open_list.get_node((next_x, next_y))
                if old_node:
                    if next_g < old_node.g:
                        # update value g and f, change its parent node
                        next_node = Node((next_x, next_y), next_g, cur_node)
                        open_list.add_node(next_f, next_node)

                else:
                    next_node = Node((next_x, next_y), next_g, cur_node)
                    open_list.add_node(next_f, next_node)

        return None
