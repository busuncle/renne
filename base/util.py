import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
import weakref
import os
import json
import pprint




def get_project_root():
    filepath = os.path.abspath(__file__)
    dirname = os.path.split(filepath)[0]
    # filepath here is $PROJECT_ROOT/base/util.py, 
    # so return the joined path except last two
    return os.path.split(dirname)[0]


def load_map_setting(chapter):
    def convert(input):
        if isinstance(input, dict):
            return {convert(k): convert(v) for k, v in input.iteritems()}
        elif isinstance(input, list):
            return [convert(v) for v in input]
        elif isinstance(input, unicode):
            return input.encode("utf-8")
        else:
            return input

    project_root = get_project_root()
    with open(os.path.join(project_root, "etc", "maps", "%s.js" % chapter)) as fp:
        res = json.load(fp, object_hook=convert)

    return res


def save_map_setting(chapter, map_setting):
    project_root = get_project_root()
    res = pprint.pformat(map_setting)
    with open(os.path.join(project_root, "etc", "maps", "%s.js" % chapter), "w") as fp:
        fp.write(res)


class ResourceController(object):
    def __init__(self, loader):
        self.res_mapping = {}
        self.cache = weakref.WeakValueDictionary()
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
    res = load_map_setting(1)
    print res["size"]
