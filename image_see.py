import os
import pygame
from pygame import transform
from pygame.locals import *
from random import randint
import etc.setting as sfg
from base import util

"""
check image
"""


screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne Image See")

def run(args):
    img = pygame.image.load(args.filepath).convert_alpha()
    #img = img.subsurface((294, 720, 68, 74))
    img_rect = img.get_rect()
    words_blit_pos = img_rect.bottomleft
    background_color = args.background_color or "black"
    #mask = pygame.Surface((256, 256)).convert_alpha()

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

        screen.fill(pygame.Color(background_color))
        mask = img.copy()
        mask.fill(pygame.Color(32, 32, 32), special_flags=BLEND_ADD)
        #img.set_alpha(128)
        #screen.blit(img, (0, 0))
        screen.blit(mask, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] > img_rect.right or mouse_pos[1] > img_rect.bottom:
            words = "outside the image"
        else:
            words = "(%s, %s)" % tuple(map(int, mouse_pos))
        info = sfg.Font.ARIAL_32.render(words, True, pygame.Color("white"))
        screen.blit(info, words_blit_pos)

        pygame.display.update()

        clock.tick(sfg.FPS)




if __name__ == "__main__":
    args = util.parse_command_line([
        (["-f", "--file-path"], {"dest": "filepath", "action": "store"}),
        (["-b", "--background-color"], {"dest": "background_color", "action": "store"}),
    ])
    if args.filepath is None:
        print "please specify the param filepath, using -f or --file-path option"
        exit(-1)
    run(args)
