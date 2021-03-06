import pygame
from pygame.locals import *
from pygame.transform import laplacian
from base import util
from etc import setting as sfg


"""
check animation
"""

screen = pygame.display.set_mode(sfg.Screen.SIZE, HWSURFACE|DOUBLEBUF)
CONTROL = {
    "stop": False,
}


def run(args):

    image = pygame.image.load(args.filepath).convert_alpha()
    background_color = args.background_color or "black"
    bg = pygame.Surface((256, 256))
    animate_size = image.get_rect()

    clock = pygame.time.Clock()


    direction = 0
    frame_speed = 8
    frame_no = 0
    frame_add = 0.0
    running = True
    if image.get_rect().height %  (8 * 256) == 0:
        has_direction = True
        frame_no_max = image.get_rect().height / 8 / 256
        print "frame_no_max: %s" % frame_no_max
    else:
        has_direction = False
        frame_no_max = image.get_rect().height / 256
        print "only one direction, frame_no_max: %s" % frame_no_max

    while running:
        for event in pygame.event.get(): # User did something
            if event.type == pygame.QUIT: # If user clicked close
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_t:
                    direction = (direction + 1) % 8
                elif event.key == K_UP:
                    frame_speed += 1
                elif event.key == K_DOWN:
                    frame_speed = max(0, frame_speed - 1)
                elif event.key == K_s:
                    CONTROL["stop"] = not CONTROL["stop"]
                elif event.key == K_a:
                    if CONTROL["stop"]:
                        frame_add -= 1
                elif event.key == K_d:
                    if CONTROL["stop"]:
                        frame_add += 1

        screen.fill(pygame.Color(background_color))

        time_passed = clock.tick(60)
        time_passed_seconds = time_passed / 1000.0

        if not CONTROL["stop"]:
            frame_add += time_passed_seconds * frame_speed

        frame_add %= frame_no_max

        if has_direction:
            frame_no = direction + int(frame_add) * 8
        else:
            frame_no = int(frame_add)

        blit_image = image.subsurface(pygame.Rect(
            (0, frame_no * animate_size.width, animate_size.width, animate_size.width)
        ))

        if args.laplacian:
            lap_sf = laplacian(blit_image)
            screen.blit(lap_sf, (0, 0))
            pygame.draw.rect(screen, pygame.Color("blue"), blit_image.get_bounding_rect(), 1)
        else:
            screen.blit(blit_image, (0, 0))

        frame_add_info = sfg.Font.ARIAL_32.render("frame add: %s" % int(frame_add), True, pygame.Color("white"))
        screen.blit(frame_add_info, (0, 256))

        pygame.display.update()


if __name__ == "__main__":
    args = util.parse_command_line([
        (["-f", "--file-path"], {"dest": "filepath", "action": "store"}),
        (["-b", "--background-color"], {"dest": "background_color", "action": "store"}),
        (["-l", "--laplacian"], {"dest": "laplacian", "action": "store_true"}),
    ])
    if args.filepath is None:
        print "please specify the param filepath, using -f or --file-path option"
        pygame.quit()

    run(args)
    pygame.quit()
