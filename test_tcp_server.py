import socket
import select
import pygame
from pygame.locals import *

FPS = 60

pygame.init()
screen = pygame.display.set_mode([800, 600])




def run():
    img = pygame.image.load("renne.png").convert_alpha()
    address = ("127.0.0.1", 2012)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(address)
    s.listen(1)

    already_accept = False
    x, y = 0, 0
    clock = pygame.time.Clock()
    conn = None
    while True:
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return conn
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return conn

        if not already_accept:
            rlist, wlist, elist = select.select([s], [], [], 0)
            if len(rlist) > 0 and rlist[0] == s:
                already_accept = True
                conn, address = s.accept()
                conn.setblocking(0)
                print "connect by %s:%s" % address

        data = None
        if already_accept:
            try:
                data = conn.recv(1024*1024)
            except socket.error, ex:
                pass

        if data:
            data = eval(data)
            for k in data:
                if k == K_a:
                    x -= 1
                elif k == K_d:
                    x += 1
                elif k == K_w:
                    y -= 1
                elif k == K_s:
                    y += 1

        screen.fill(pygame.Color("black"))
        screen.blit(img, (x, y))
        pygame.display.update()
        clock.tick(FPS)



if __name__ == "__main__":
    conn = run()
    conn.close()
    pygame.quit()

