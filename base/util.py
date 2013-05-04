import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
import weakref
import os
from random import random
from time import time
import pprint
import imp




def happen(probability):
    # calculate whether the event will happen according the probability
    return random() < probability


def get_project_root():
    filepath = os.path.abspath(__file__)
    dirname = os.path.split(filepath)[0]
    # filepath here is $PROJECT_ROOT/base/util.py, 
    # so return the joined path except last two
    return os.path.split(dirname)[0]


def load_map_setting(chapter):
    name = "chapter_%s" % chapter
    m = imp.load_source(name, os.path.join("etc", "maps", name+".py"))

    return getattr(m, "map_setting")


def save_map_setting(chapter, map_setting):
    res = pprint.pformat(map_setting)
    with open(os.path.join("etc", "maps", "chapter_%s.py" % chapter), "w") as fp:
        fp.write("map_setting = " + res)


def parse_command_line(needed_args_list):
    # for version compatible
    # needed_args_list should be a list containing tuples with args and kwargs that parser accepts
    # e.g. [(args, kwargs), ...], args is a list containing arguments, 
    # and kwargs means keyword-args that using a dict to do the same thing
    try:
        # for python version >= 2.7
        import argparse
        parser = argparse.ArgumentParser()
        for args, kwargs in needed_args_list:
            parser.add_argument(*args, **kwargs)
        args = parser.parse_args()
        return args

    except ImportError, ex:
        import optparse
        parser = optparse.OptionParser()
        for args, kwargs in needed_args_list:
            parser.add_option(*args, **kwargs)
        options, args = parser.parse_args()
        return options


class ResourceController(object):
    def __init__(self, loader):
        self.res_mapping = {}
        # TODO: disable weakref for trouble shooting
        #self.cache = weakref.WeakValueDictionary()
        self.cache = {}
        self.loader = loader
        self.path = "res"

    def add(self, key, file):
        self.res_mapping[key] = os.path.join(self.path, file)

    def add_from_list(self, files_mapping):
        # files_mapping should be a dict likes "{name1: file1, name2: file2, ...}"
        for k, v in files_mapping.iteritems():
            self.add(k, v)

    def get(self, name):
        try:
            res = self.cache[name]
        except KeyError:
            res = self.loader(self.res_mapping[name])
            self.cache[name] = res
        return res

    def __nonzero__(self):
        return len(self.res_mapping) > 0



class MusicController(ResourceController):
    def __init__(self, music_folder="", default_loader=pygame.mixer.Sound):
        super(MusicController, self).__init__(default_loader)
        self.path = os.path.join(self.path, "music", music_folder)

    def load(self, key):
        # this function is totally for pygame.mixer.music.load
        # it loads music file as stream, it should be called every time when you want to play another music
        res = self.res_mapping[key]
        self.loader(res)



class ImageController(ResourceController):
    def __init__(self, image_folder=""):
        super(ImageController, self).__init__(pygame.image.load)
        self.path = os.path.join(self.path, "image", image_folder)



class SpriteImageController(ImageController):
    # extend for sprite image resource
    def __init__(self, image_folder=""):
        super(SpriteImageController, self).__init__(image_folder)
        self.surfaces_mapping = {}

    def make_frames(self):
        # make surface into subsurfaces
        for k in self.res_mapping:
            surface = self.get(k).convert_alpha()
            width, height = surface.get_size()
            num = height / width
            self.surfaces_mapping[k] = [surface.subsurface(
                Rect((0, i * width), (width, width))) for i in xrange(num)]

    def init_frames(self, frame_files):
        if not self:
            self.add_from_list(frame_files)
            self.make_frames()

    def get_surface(self, name):
        return self.surfaces_mapping[name]



class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_tuple(self):
        return (self.x, self.y)

    def __str__(self):
        return "(%s, %s)" % (self.x, self.y)


def point_add_delta(point, point_delta):
    # given a point p(x, y) and a delta (dx, dy), return a new point p(x + dx, y + dy) 
    # all of above params and return value should be tuple type
    return (point[0] + point_delta[0], point[1] + point_delta[1])


class LineSegment(object):
    def __init__(self, point_a, point_b):
        # point_a and point_b should be tuple type
        self.a = point_a
        self.b = point_b

    def __str__(self):
        return "(%s, %s)" % (str(self.a), str(self.b))


def cross_product(vec_a, vec_b):
    """
    cross product for 2D vector
    """

    return vec_a.x * vec_b.y - vec_b.x * vec_a.y


def dot_mul(vec_a, vec_b):
    """
    dot multiplication for 2D vector
    """

    return vec_a.x * vec_b.x + vec_a.y * vec_b.y


def line_segment_intersect(line_a, line_b):
    """
    return True if line_a intersect with line_b else False
    params should be LineSegment object
    """

    p1 = line_a.a
    p2 = line_a.b
    p3 = line_b.a
    p4 = line_b.b

    vec_a = Vector2.from_points(p3, p1)
    vec_b = Vector2.from_points(p3, p4)
    d1 = cross_product(vec_a, vec_b)

    vec_a = Vector2.from_points(p3, p2)
    vec_b = Vector2.from_points(p3, p4)
    d2 = cross_product(vec_a, vec_b)

    vec_a = Vector2.from_points(p1, p3)
    vec_b = Vector2.from_points(p1, p2)
    d3 = cross_product(vec_a, vec_b)

    vec_a = Vector2.from_points(p1, p4)
    vec_b = Vector2.from_points(p1, p2)
    d4 = cross_product(vec_a, vec_b)

    # normal intersect
    if d1 * d2 < 0 and d3 * d4 < 0:
        return True

    def on_segment(pi, pj, pk):
        # pi, pj, pk have to be a tuple as (x, y)
        return min(pi[0], pj[0]) <= pk[0] <= max(pi[0], pj[0]) \
            and min(pi[1], pj[1]) <= pk[1] <= max(pi[1], pj[1])

    # abnormal intersect test
    if d1 == 0 and on_segment(p3, p4, p1):
        return True

    if d2 == 0 and on_segment(p3, p4, p2):
        return True

    if d3 == 0 and on_segment(p1, p2, p3):
        return True

    if d4 == 0 and on_segment(p1, p2, p4):
        return True

    return False


def line_segment_intersect_with_rect(line_seg, rect):
    # check whether a line intersect with any side of a rect
    # line is a LineSegment object, rect is a Rect object
    v_lines = map(lambda seg:LineSegment(*seg),
        [(rect.topleft, rect.topright), (rect.topleft, rect.bottomleft), 
        (rect.bottomleft, rect.bottomright), (rect.topright, rect.bottomright)])

    for v in v_lines:
        if line_segment_intersect(line_seg, v):
            return True

    return False


def cos_for_vec(v1, v2):
    # return the cosine value of the 2 vector using cosine law
    # the 2 params should be objects of Vector2
    return dot_mul(v1, v2) / (v1.get_length() * v2.get_length())


def manhattan_distance(p1, p2):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)



class Timer(object):
    def __init__(self, time_len=None):
        self.begin_time = None
        self.current_time = None
        self.time_len = time_len


    def begin(self, time_len=None):
        # set begin time, when you run a stopwatch, you must call this
        # optionally, you may set another time_len
        self.begin_time = time()
        if time_len is not None:
            self.time_len = time_len


    def is_begin(self):
        return self.begin_time is not None


    def tick(self):
        self.current_time = time()


    def passed_time(self):
        return self.current_time - self.begin_time


    def exceed(self):
        self.current_time = time()
        if self.current_time - self.begin_time > self.time_len:
            return True
        return False


    def clear(self):
        self.begin_time = None
        self.current_time = None
        self.time_len = None



def test_geometry():
    p1 = Point(2, 3)
    p2 = Point(2, 5)
    p3 = Point(1, 4)
    p4 = Point(3, 6)
    
    l1 = LineSegment(p1, p2)
    l2 = LineSegment(p3, p4)

    from gameobjects.vector2 import Vector2
    v = Vector2(1, 0)
    for p in [(0, 2), (1, 0), (-1, 0), (10, 10), (1, -1), (-1, 1), (0, -1), (-1, -1)]:
        v2 = Vector2(p)
        cosine = dot_mul(v, v2) / (v.get_length() * v2.get_length())
        print v, v2, cosine



if __name__ == "__main__":
    res = parse_command_line([
        (["-d", "--debug"], {"dest": "debug", "action": "store_true"}),
        (["-f", "--file-path"], {"dest": "filepath", "action": "store"}),
    ])
    print res.debug
    print res.filepath
