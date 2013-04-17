import pygame
import etc.setting as sfg



def draw_area(camera, sprite):
    r = pygame.Rect(0, 0, sprite.area.width, sprite.area.height / 2)
    r.center = (sprite.pos.x, sprite.pos.y/2)
    r.top -= camera.rect.top
    r.left -= camera.rect.left
    pygame.draw.rect(camera.screen, pygame.Color("red"), r, 1)


def draw_pos(camera, sprite):
    pos = "(%s, %s)" % tuple(map(int, sprite.pos))
    info = sfg.Font.ARIAL_16.render(pos, True, pygame.Color("red"))
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
    if fps < 50:
        font = sfg.Font.ARIAL_BOLD_16
        color = pygame.Color("pink")
    else:
        font = sfg.Font.ARIAL_16
        color = pygame.Color("red")

    w = "%s fps" % fps
    info = font.render(w, True, color)
    r = info.get_rect()
    r.right = camera.rect.right - 5
    r.centery = camera.rect.centery
    camera.screen.blit(info, (r.left - camera.rect.left, r.top - camera.rect.top))



def run_debug_by_option_list(option_list, camera, game_world, game_map, clock):
    if option_list["waypoints"]:
        draw_waypoins(camera, game_map.waypoints)
    if option_list["fps"]:
        draw_fps(camera, clock)
    if option_list["area"]:
        for sp in game_world.sprites():
            draw_area(camera, sp)
    if option_list["pos"]:
        for sp in game_world.sprites():
            draw_pos(camera, sp)
        
