import pygame
from os import path
from pygame import freetype
from string import ascii_lowercase
from string import digits
from character import Character


class Interpreter:
    def __init__(self, map, character):
        self.map = map
        self.character = character

        self.code = ""

        self.framedata = []

        self.pressed_play = False
        self.pressed_stop = False

        pygame.init()

        # import animations
        self.anim_play = [pygame.image.load(path.join(".", "images", "play", "unpress.png")),
                          pygame.image.load(path.join(".", "images", "play", "press.png"))]
        self.anim_stop = [pygame.image.load(path.join(".", "images", "stop", "unpress.png")),
                          pygame.image.load(path.join(".", "images", "stop", "press.png"))]

        self.font = pygame.freetype.Font(path.join(".", "fonts", "Menlo.ttc"))
        self.font.size = 12
        self.font.fgcolor = (156, 170, 255)


        self.cmds = {
            'MOVE': self.cmd_move,
            'WAIT': self.cmd_wait}

        self._reset()

    def run(self, screen):
        self._get_input()
        self._render(screen)

    def _render(self, screen):
        # render the border behind the background
        border = pygame.Surface((672, 768))
        border.fill((8, 0, 26))
        screen.blit(border,pygame.Rect(0, 0, 672, 768))

        background = pygame.Surface((600,660))
        background.fill((46, 42, 54))
        screen.blit(background,pygame.Rect(36, 72, 600, 660))

        # render buttons
        if self.pressed_play:
            screen.blit(self.anim_play[1], pygame.Rect(548, 16, 32, 32))
        else:
            screen.blit(self.anim_play[0], pygame.Rect(548, 16, 32, 32))

        if self.pressed_stop:
            screen.blit(self.anim_stop[1], pygame.Rect(596, 16, 32, 32))
        else:
            screen.blit(self.anim_stop[0], pygame.Rect(596, 16, 32, 32))


        # render line numbers
        for line_number in range(40):
            font_surface, font_rect = self.font.render(str(line_number))
            font_rect = font_rect.move(48, line_number * 16 + 72)
            screen.blit(font_surface, font_rect)

        code_segments = self.code.split("\n")
        for segment_index in range(len(code_segments)):
            font_surface, font_rect = self.font.render(str(code_segments[segment_index]))
            font_rect = font_rect.move(64, segment_index * 16 + 72)
            screen.blit(font_surface, font_rect)


    def _reset(self):
        self.character.spawn()
        self.character.freeze = True
        self.map.reset_map()

    def _get_input(self):
        # no mouse input yet for text, only keyboard
        # backspace and enter and text
        # input for interpreter:
        # move <left|right>
        # stop
        # jump
        # attack <up|down|left|right|stop>

        key_events = pygame.event.get(eventtype=pygame.KEYDOWN)

        for key_event in key_events:
            if key_event.key == pygame.K_SPACE:
                self.code += " "
            if key_event.key == pygame.K_RETURN:
                self.code += "\n"

            if key_event.key == pygame.K_BACKSPACE:
                if len(self.code) >= 2 and self.code[-2:] == "\n":
                    self.code = self.code[:-2]
                elif len(self.code) >= 1:
                    self.code = self.code[:-1]

            for char in ascii_lowercase:
                if key_event.key == pygame.key.key_code(char):
                    self.code += char.upper()

            for digit in digits:
                if key_event.key == pygame.key.key_code(digit):
                    self.code += digit

        # check for button presses
        mouse_down_events = pygame.event.get(eventtype=pygame.MOUSEBUTTONDOWN)
        mouse_up_events = pygame.event.get(eventtype=pygame.MOUSEBUTTONUP)

        for mouse_event in mouse_down_events:
            if mouse_event.button == 1:
                if 16 <= mouse_event.pos[1] <= 48:
                    if 548 <= mouse_event.pos[0] <= 580:
                        self.pressed_play = True
                    elif 596 <= mouse_event.pos[0] <= 628:
                        self.pressed_stop = True

        for mouse_event in mouse_up_events:
            if mouse_event.button == 1:
                self.pressed_stop = False
                self.pressed_play = False
                if 16 <= mouse_event.pos[1] <= 48:
                    if 548 <= mouse_event.pos[0] <= 580:
                        self.parse(self.code)
                    elif 596 <= mouse_event.pos[0] <= 628:
                        self._reset()


    def cmd_move(self, direction):
        if direction == "RIGHT":
            self.character.push_animation(self.character.anim_walk, facing = "right")
            self.character.velocity[0] = 2
        elif direction == "LEFT":
            self.character.push_animation(self.character.anim_walk, facing = "left")
            self.character.velocity[0] = 2

    def cmd_wait(self, time):
        time = int(time) # if this fails, interpret() will catch it

    def display_error(self, error):
        if error == None:
            self.error_display = ""
        else:
            font_surface, font_rect = self.font.render(error_display)
            font_rect = font_rect.move(52, 16)
            screen.blit(font_surface, font_rect)



    # stuff written by yu, thanks yu
    def interpret(self, line):
        if line != "":
            args = line.split(' ')
            if len(args) < 1: return
            if args[0] not in self.cmds:
                raise CodingException()
            callback = self.cmds[args[0]]
            try:
                callback(args[1:])
            except TypeError: # probably argcount mismatch
                raise CodingException('Invalid arguments')
            except ValueError: # probably type conversion error
                raise CodingException('Argument type invalid')

    def parse(self, code):
        for n,line in enumerate(code.split(' ')):
            try:
                self.interpret(line)
            except CodingException as e:
                self.error_display = 'Error at line {}: {}'.format(n, e.args[0])
                return

class CodingException(Exception):
    pass