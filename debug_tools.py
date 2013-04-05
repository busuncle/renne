import pygame



def draw_area(camera, sprite):
    r = pygame.Rect(0, 0, sprite.area.width, sprite.area.height / 2)
    r.center = (sprite.pos.x, sprite.pos.y/2)
    r.top -= camera.rect.top
    r.left -= camera.rect.left
    pygame.draw.rect(camera.screen, pygame.Color("red"), r, 1)


def draw_pos(camera, sprite):
    pos = "(%s, %s)" % tuple(map(int, sprite.pos))
    info = pygame.font.SysFont("arial", 16).render(pos, True, pygame.Color("red"))
    r = pygame.Rect(0, 0, 100, 20)
    r.center = (sprite.pos.x, sprite.pos.y/2)
    r.top -= camera.rect.top
    r.left -= camera.rect.left
    camera.screen.blit(info, r)


def draw_waypoins(camera, waypoints):
    for x, y in waypoints:
        ix, iy = map(int, (x, y/2))
        pygame.draw.circle(camera.screen, pygame.Color("red"), (ix, iy), 2)


def all_model_display(camera, game_world, game_map):
    draw_waypoins(camera, game_map.waypoints)
    for sp in game_world.sprites():
        #draw_area(camera, sp)
        #draw_pos(camera, sp)
        pass

