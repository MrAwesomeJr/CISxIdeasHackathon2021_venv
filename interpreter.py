import pygame
from os import path
from pygame import freetype
from string import ascii_lowercase
from string import digits


class Interpreter:
    def __init__(self, map, character):
        self.map = map
        self.character = character

        self.code = ""

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

        self.error_display = ""

        self._reset()

        self.backspace_held = False
        self.backspace_startup = 0

        self.cursor_display = True
        self.cursor_display_timer = 0


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
        if self.cursor_display:
            code_segments[-1] += "|"
        self.cursor_display_timer += 1
        if self.cursor_display_timer >= 10:
            self.cursor_display_timer = 0
            self.cursor_display = not self.cursor_display

        for segment_index in range(len(code_segments)):
            font_surface, font_rect = self.font.render(str(code_segments[segment_index]))
            font_rect = font_rect.move(64, segment_index * 16 + 72)
            screen.blit(font_surface, font_rect)


        # render error message
        self.display_error(screen, update_error = False)


    def _reset(self):
        self.character.spawn()
        self.map.reset_map()
        self.map.done = False

    def _get_input(self):
        # no mouse input yet for text, only keyboard
        # backspace and enter and text

        key_down_events = pygame.event.get(eventtype=pygame.KEYDOWN)
        key_up_events = pygame.event.get(eventtype=pygame.KEYUP)

        for key_event in key_down_events:
            if key_event.key == pygame.K_SPACE:
                self.code += " "
            if key_event.key == pygame.K_RETURN:
                self.code += "\n"

            if key_event.key == pygame.K_BACKSPACE:
                if len(self.code) >= 2 and self.code[-2:] == "\n":
                    self.code = self.code[:-2]
                elif len(self.code) >= 1:
                    self.code = self.code[:-1]
                self.backspace_held = True

            for char in ascii_lowercase:
                if key_event.key == pygame.key.key_code(char):
                    self.code += char.upper()

            for digit in digits:
                if key_event.key == pygame.key.key_code(digit):
                    self.code += digit

        for key_event in key_up_events:
            if key_event.key == pygame.K_BACKSPACE:
                self.backspace_held = False
                self.backspace_startup = 0

        # special (and lazy) backspace key repeat
        if self.backspace_held:
            if self.backspace_startup < 4:
                self.backspace_startup += 1
            else:
                if len(self.code) >= 2 and self.code[-2:] == "\n":
                    self.code = self.code[:-2]
                elif len(self.code) >= 1:
                    self.code = self.code[:-1]

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
                        self._reset()
                        self.interpret()
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

    def display_error(self, screen, error = "", update_error = True):
        if update_error:
            self.error_display = error

        font_surface, font_rect = self.font.render(self.error_display)
        font_rect = font_rect.move(52, 16)
        screen.blit(font_surface, font_rect)

    def interpret(self):
        # input for interpreter:
        # STOP
        # JUMP
        # MOVE <LEFT|RIGHT>
        # ATTACK <UP|LEFT|RIGHT>
        # WAIT <frames>
        lines = self.code.split("\n")
        framedata = []
        current_action = ""
        for line in lines:
            words = line.split(" ")
            if len(words) >= 1:
                if words[0] == "STOP":
                    framedata.append("stop")
                elif words[0] == "JUMP":
                    framedata.append("jump")
                    for i in range(12):
                        framedata.append("")
                    framedata.append("endjump")
                    for i in range(4):
                        framedata.append("")
                elif len(words) >= 2:
                    if words[0] == "MOVE":
                        if words[1] == "LEFT":
                            framedata.append("left")
                        elif words[1] == "RIGHT":
                            framedata.append("right")
                    if words[0] == "ATTACK":
                        if words[1] == "LEFT":
                            framedata.append("atk_left")
                        elif words[1] == "RIGHT":
                            framedata.append("atk_right")
                        elif words[1] == "UP":
                            framedata.append("atk_up")
                    if words[0] == "WAIT":
                        try:
                            for i in range(int(words[1])):
                                framedata.append("")
                        except TypeError:
                            pass
        self.character.framedata = framedata[:]




    # stuff written by yu, thanks yu but idk how to use any of this so i'm gonna rewrite it
#     def interpret(self, line):
#         if line != "":
#             args = line.split(' ')
#             if len(args) < 1: return
#             if args[0] not in self.cmds:
#                 raise CodingException()
#             callback = self.cmds[args[0]]
#             try:
#                 callback(args[1:])
#             except TypeError: # probably argcount mismatch
#                 raise CodingException('Invalid arguments')
#             except ValueError: # probably type conversion error
#                 raise CodingException('Argument type invalid')
#
#     def parse(self, code):
#         for n,line in enumerate(code.split(' ')):
#             try:
#                 self.interpret(line)
#             except CodingException as e:
#                 self.error_display = 'Error at line {}: {}'.format(n, e.args[0])
#                 return
#
# class CodingException(Exception):
#     pass