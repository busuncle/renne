import pygame



def draw_area(sprite, camera):
    r = pygame.Rect(0, 0, sprite.area.width, sprite.area.height / 2)
    r.center = (sprite.pos.x, sprite.pos.y/2)
    r.top -= camera.rect.top
    r.left -= camera.rect.left
    pygame.draw.rect(camera.screen, pygame.Color("red"), r, 1)


def draw_pos(sprite, camera):
    pos = "(%s, %s)" % tuple(map(int, sprite.pos))
    info = pygame.font.SysFont("arial", 16).render(pos, True, pygame.Color("red"))
    r = pygame.Rect(0, 0, 100, 20)
    r.center = (sprite.pos.x, sprite.pos.y/2)
    r.top -= camera.rect.top
    r.left -= camera.rect.left
    camera.screen.blit(info, r)


def draw_waypoins(camera, waypoints):
    for x, y in waypoints:
        pygame.draw.circle(camera.screen, pygame.Color("red"), (x, y/2), 2)


def all_model_display(camera, game_world):
    draw_waypoins(camera, game_world.waypoints)
    for sp in game_world.sprites():
        #draw_area(sp, camera)
        draw_pos(sp, camera)

