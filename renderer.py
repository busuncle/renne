import etc.setting as sfg
import pygame
from pygame.locals import HWSURFACE, DOUBLEBUF



class Camera(object):
    def __init__(self, screen, map_size, size=sfg.Screen.SIZE, inner_size=sfg.Screen.INNER_SIZE):
        self.screen = screen
        self.map_size = map_size
        self.size = size
        self.x_min = size[0] / 2
        self.x_max = map_size[0] - size[0] / 2
        self.y_min = size[1] / 2 
        self.y_max = map_size[1] / 2 - size[1] / 2
        self.inner_size = inner_size
        self.dx_max = inner_size[0] / 2
        self.dy_max = inner_size[1] / 2
        self.rect = pygame.Rect((0, 0), size)

    
    def set_rect(self, hero_pos):
        # set rect according the position of hero
        hero_screen_x, hero_screen_y = hero_pos[0], hero_pos[1] / 2
        # delta between hero_screen_x(y) and screen center
        dx, dy = hero_screen_x - self.rect.centerx, hero_screen_y - self.rect.centery
        if abs(dx) > self.dx_max:
            new_x = hero_screen_x - self.dx_max if dx > 0 else hero_screen_x + self.dx_max
            new_x = min(max(self.x_min, new_x), self.x_max)
            self.rect.centerx = new_x
        if abs(dy) > self.dy_max:
            new_y = hero_screen_y - self.dy_max if dy > 0 else hero_screen_y + self.dy_max
            new_y = min(max(self.y_min, new_y), self.y_max)
            self.rect.centery = new_y

