import os
import pygame
from pygame.locals import *
import etc.setting as sfg
from base import util


screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne Sound Listen")


def run(args):
    background = pygame.mixer.music.load(args.background)
    effect = pygame.mixer.Sound(args.effect)

    pygame.mixer.music.play()
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

            if event.type == KEYDOWN and event.key == K_j:
                effect.play()

        pygame.display.update()

        clock.tick(sfg.FPS)



if __name__ == "__main__":
    args = util.parse_command_line([
        (["-b", "--background"], {"dest": "background", "action": "store"}),
        (["-e", "--effect"], {"dest": "effect", "action": "store"}),
    ])
    if args.background is None:
        print "please specify the param background, using -b or --background option"
        exit(-1)
    if args.effect is None:
        print "please specify the param effect, using -e or --effect option"
    run(args)
