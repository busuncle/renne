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


def all_model_display(camera, game_world):
    for sp in game_world.sprites():
        draw_area(sp, camera)
        draw_pos(sp, camera)
