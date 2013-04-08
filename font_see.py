import os
import pygame
from pygame.locals import *
import etc.setting as sfg
from base import util


screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne Font See")


def run(string, name="arial black", size=64, color=pygame.Color("white")):
    if string is None:
        string = "abcABC"

    font = pygame.font.SysFont(name, size).render(string, True, color)

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

        screen.fill(pygame.Color("black"))
        screen.blit(font, (0, 0))
        pygame.display.update()

        clock.tick(sfg.FPS)


if __name__ == "__main__":
    args = util.parse_command_line([
        (["-s", "--string"], {"dest": "string", "action": "store"}),
    ])
    run(args.string)
