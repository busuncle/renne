import os
import pygame
from pygame.locals import *
from base import util
from etc import setting as sfg


screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne Sound Listen")


def run(args):
    background = pygame.mixer.music.load(args.background)
    effect = pygame.mixer.Sound(args.effect)

    pygame.mixer.music.play(-1)
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

            if event.type == KEYDOWN and event.key == K_j:
                effect.play()

            if event.type == KEYDOWN and event.key == K_SPACE:
                pygame.mixer.music.stop()

        pygame.display.update()

        clock.tick(sfg.FPS)



if __name__ == "__main__":
    args = util.parse_command_line([
        (["-b", "--background"], {"dest": "background", "action": "store"}),
        (["-e", "--effect"], {"dest": "effect", "action": "store"}),
    ])

    if args.background is None:
        print "please specify the param background, using -b or --background option"
        pygame.quit()

    if args.effect is None:
        print "please specify the param effect, using -e or --effect option"
        pygame.quit()

    run(args)
    pygame.quit()
