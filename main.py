import sys, pygame
from map import Map
from character import Character
pygame.init()

size = (width, height) = (1440, 768)
# notes on size:
# right side of the screen is square with 48x48 display area (each block is 16 pixels, because we want to fit the entire map)
# map begins on pixel 672
# writing section is 600 pixels wide on the left

screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
map = Map("map")
character = Character(map)


while True:
    # cap game at 30fps
    clock.tick(30)

    if len(pygame.event.get(eventtype=pygame.QUIT)) >= 1:
        sys.exit()

    screen.fill((0,0,0))
    map.run(screen)
    pygame.display.flip()