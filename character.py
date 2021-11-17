import pygame
class Character:
    def __init__(self, map):
        self.map = map
        pygame.init()
        # character is calculated using the top left corner as (0,0), following pygame standards
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

        self.grounded = True
        # accepted states: idle, move_left, move_right, jump. Used to animate character
        self.char_state = "stop"
        self.velocity = [0,0]

    def render_character(self):
        pass