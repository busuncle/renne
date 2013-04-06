import argparse
import os
import pygame
from pygame.locals import *
import etc.setting as sfg


screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
pygame.display.set_caption("Renne Image See")

def run(filepath):
    clock = pygame.time.Clock()
    img = pygame.image.load(filepath).convert_alpha()
    img_rect = img.get_rect()
    words_blit_pos = img_rect.bottomleft
    while True:
        ev = pygame.event.wait()
        if ev.type == KEYDOWN:
            if ev.key == K_ESCAPE:
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
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file-path", dest="filepath", action="store")
    args = parser.parse_args()
    if args.filepath is None:
        print "please specify the param filepath, using -f or --file-path option"
        exit(-1)
    run(args.filepath)
