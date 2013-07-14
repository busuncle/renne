import os
import sys
import weakref
import pygame
import animation
from pygame import transform
from pygame.locals import *
from random import randint
from etc import setting as sfg
from base import util


screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)


bomb_images = animation.effect_image_controller.get(
    sfg.Effect.BOMB_IMAGE_KEY).convert_alpha().subsurface(sfg.Effect.BOMB_RECT)
bombs = [bomb_images.subsurface((i * 64, 0, 64, 64)) for i in xrange(3)]

bomb_images2 = animation.effect_image_controller.get(
    sfg.Effect.BOMB2_IMAGE_KEY).convert_alpha()
bombs2 = [
    bomb_images2.subsurface((0, 0, 128, 128)),
    bomb_images2.subsurface((128, 0, 128, 128)),
    bomb_images2.subsurface((0, 128, 128, 128)),
    bomb_images2.subsurface((128, 128, 128, 128)),
]


def run():

    t = 0
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

        screen.fill(pygame.Color("black"))

        time_passed = clock.tick(sfg.FPS)
        time_passed_seconds = time_passed / 200.0

        t += time_passed_seconds

        t %= len(bombs)
        screen.blit(bombs[int(t)], (100, 100))
        #t %= len(bombs2)
        #screen.blit(bombs2[int(t)], (100, 100))

        pygame.display.update()



if __name__ == "__main__":
    run()
