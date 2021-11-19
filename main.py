import pygame
import sys
from character import Character
from interpreter import Interpreter
from map import Map
import time
import datetime as dt

pygame.init()

# turn on for fps debugging
fps_display = True
fps_limit = 30
# notes on size:
# right side of the screen is square with 48x48 display area
# (each block is 16 pixels, because we want to fit the entire map)
# map begins on pixel 672
# writing section is 600 pixels wide on the left (offset of 36 on either side, additional 72 on the top for menu)

screen = pygame.display.set_mode((1440, 768))
clock = pygame.time.Clock()
map = Map("map")
character = Character(map)
interpreter = Interpreter(map, character)

total_frames = 0
start_time = dt.datetime.today().timestamp()

while True:
    # cap game at 30fps
    if fps_limit > 0:
        clock.tick(fps_limit)


    if fps_display:
        time_diff = dt.datetime.today().timestamp() - start_time
        total_frames += 1
        print("avg fps:",round(total_frames / time_diff,4))

    if len(pygame.event.get(eventtype=pygame.QUIT)) >= 1:
        sys.exit()

    screen.fill((0, 0, 0))
    interpreter.run(screen)
    map.run(screen)
    character.run(screen)
    pygame.display.flip()
