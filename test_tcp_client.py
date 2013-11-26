import socket
import pygame
from pygame.locals import *


pygame.init()
pygame.display.set_mode([400, 300])

FPS = 60

address = ("127.0.0.1", 2012)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(address)
s.setblocking(0)


def run():
    clock = pygame.time.Clock()
    data = {}
    while True:
        data.clear()
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

        pressed_keys = pygame.key.get_pressed()
        for k in (K_a, K_d, K_w, K_s):
            if pressed_keys[k]:
                data[k] = 1

        if len(data) > 0:
            try:
                s.send(repr(data))
            except socket.error, ex:
                pass

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    run()
