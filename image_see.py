import os
import pygame
from pygame.locals import *
import etc.setting as sfg
from base import util


screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne Image See")

def run(filepath):
    img = pygame.image.load(filepath).convert_alpha()
    img_rect = img.get_rect()
    words_blit_pos = img_rect.bottomleft

    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

        screen.fill(pygame.Color("black")) 
        screen.blit(img, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] > img_rect.right or mouse_pos[1] > img_rect.bottom:
            words = "outside the image"
        else:
            words = "(%s, %s)" % tuple(map(int, mouse_pos))
        info = pygame.font.SysFont("arial", 32).render(words, True, pygame.Color("white"))
        screen.blit(info, words_blit_pos)

        pygame.display.update()

        clock.tick(sfg.FPS)




if __name__ == "__main__":
    args = util.parse_command_line([
        (["-f", "--file-path"], {"dest": "filepath", "action": "store"}),
    ])
    if args.filepath is None:
        print "please specify the param filepath, using -f or --file-path option"
        exit(-1)
    run(args.filepath)
