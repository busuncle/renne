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
        ix -= camera.rect.left
        iy -= camera.rect.top
        pygame.draw.circle(camera.screen, pygame.Color("red"), (ix, iy), 2)



def draw_fps(camera, clock):
    fps = int(clock.get_fps())
    w = "%s fps" % fps
    info = pygame.font.SysFont("arial", 16).render(w, True, pygame.Color("red"))
    r = info.get_rect()
    r.right = camera.rect.right - 5
    r.centery = camera.rect.centery
    camera.screen.blit(info, (r.left - camera.rect.left, r.top - camera.rect.top))



def run_debug_by_option_list(option_list, camera, game_world, game_map, clock):
    if "z" in option_list:
        draw_waypoins(camera, game_map.waypoints)
    if "f" in option_list:
        draw_fps(camera, clock)
    if "a" in option_list or "p" in option_list:
        for sp in game_world.sprites():
            if "a" in option_list:
                draw_area(camera, sp)
            if "p" in option_list:
                draw_pos(camera, sp)
        
