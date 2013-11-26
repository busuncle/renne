import socket
import pygame
from pygame.locals import *

FPS = 60

address = ("127.0.0.1", 2012)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(address)
s.listen(1)
conn, address = s.accept()
conn.setblocking(0)
print "connect by %s:%s" % address


pygame.init()
screen = pygame.display.set_mode([800, 600])

def run():
    img = pygame.image.load("renne.png").convert_alpha()

    x, y = 0, 0
    clock = pygame.time.Clock()
    while True:
        data = None
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return

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
    try:
        run()
    except Exception, ex:
        print ex
    finally:
        conn.close()

    pygame.quit()

