import copy

import pygame
from os import path


class Character:
    def __init__(self, map):
        self.map = map
        # character is calculated using the top left corner as (0,0), following pygame standards
        self.pos = [0,0]
        self.size = [14,28]

        self.grounded = True

        # list of inputs per frame that is read frame by frame and executed
        self.framedata = []

        self.facing = "right"

        # contains a list of things to animate.
        self.anim_stack = []
        # animate once every 3 frames (except jumpsquat, which needs to be animated every frame)
        self.anim_counter = 0

        self.blocking_anim = False
        # velocity per frame (30fps)
        self.velocity = [0,0]

        # stop the game from updating physics or running code
        self.freeze = True

        pygame.init()

        # initialize animations ((<x_offset>, <y_offset>),[<surface>])
        # x_offset and y_offset are relative to the top left corner of the character (the hitbox is 14x28)
        # all animations are facing right. Animations are flipped in self._render()
        self.anim_idle = self._load_char_anim((-8, 0), path.join(".", "images", "char", "idle"), (32, 32), frames = 4)
        # self.anim_aerial = [(0, 0), pygame.transform.scale(pygame.image.load(path.join(dir, str(frame)+".png")), (0, 0))]
        # self.anim_jump = self._load_char_anim((-8, 0), path.join(".", "images", "char", "jump"), (32, 32), frames = 1)
        # self.anim_walk = self._load_char_anim((-8, 0), path.join(".", "images", "char", "walk"), (32, 32), frames = 1)
        # self.anim_ftilt = self._load_char_anim((-8, 0), path.join(".", "images", "char", "ftilt"), (32, 32), frames = 1)
        # self.anim_btilt = self._load_char_anim((-8, 0), path.join(".", "images", "char", "btilt"), (32, 32), frames = 1)
        self.anim_utilt = self._load_char_anim((-8, -3), path.join(".", "images", "char", "utilt"), (32, 32), frames = 12)
        # self.anim_fair = self._load_char_anim((-8, 0), path.join(".", "images", "char", "fair"), (32, 32), frames = 1)

    def _load_char_anim(self, offset, dir, size, frames = 1):
        anim_list = [offset]
        for frame in range(frames):
            anim_list.append(pygame.transform.scale(pygame.image.load(path.join(dir, str(frame)+".png")), size))

        return anim_list

    def run(self, screen):
        # run one frame or freeze if game is frozen
        # freeze game if game has ended
        if self.map.done:
            self.freeze = True

        if not self.freeze:
            self._tick()

        self._render(screen)

    def spawn(self):
        self.pos = ((self.map.spawnpoint[0] + self.map.x_block_offset) * self.map.pixel_size[0] +
                    self.map.render_offset[0] + ((self.map.pixel_size[0] - self.size[0]) / 2),
                    (self.map.spawnpoint[1] + self.map.y_block_offset + 2) * self.map.pixel_size[1] +
                    self.map.render_offset[1] - self.size[1])

        self.grounded = True
        self.framedata = []
        self.anim_stack = []
        self.blocking_anim = False
        self.velocity = [0,0]
        self.freeze = True



    def _render(self, screen):
        # idle if nothing is happening
        if len(self.anim_stack) >= 0:
            if self.grounded:
                if self.velocity[0] == 0:
                    self.push_animation(self.anim_idle)
                else:
                    self.push_animation(self.anim_walk)
            else:
                # when in the air
                self.push_animation(self.anim_aerial)


        if self.facing == "left":
            screen.blit(pygame.transform.flip(self.anim_stack[0][0], True, False),
                        pygame.Rect(self.pos[0] + self.anim_stack[0][1][0],
                                    self.pos[1] + self.anim_stack[0][1][1],
                                    self.size[0], self.size[1]))
        else:
            screen.blit(self.anim_stack[0][0],
                        pygame.Rect(self.pos[0] + self.anim_stack[0][1][0],
                                    self.pos[1] + self.anim_stack[0][1][1],
                                    self.size[0], self.size[1]))

        if self.anim_counter < 2:
            self.anim_counter += 1
        else:
            self.anim_stack.pop(0)
            self.anim_counter = 0

    def push_animation(self, anim_list, block_flag = False, facing = None):
        if facing != None:
            self.facing = facing
        # dereference original anim_list
        anim_list = anim_list[:]
        if len(self.anim_stack) == 0 or self.blocking_anim == False:
            if len(self.anim_stack) == 0:
                self.blocking_anim == block_flag
            offset = anim_list[0]
            anim_list.pop(0)
            for anim in anim_list:
                self.anim_stack.append((anim, offset))

    def _tick(self):
        new_pos = self.pos
        new_pos[0] += self.velocity[0]
        new_pos[1] += self.velocity[1]

        # find the block your new_pos is in
        pos_block = [0,0]


        # prevent walking into walls

        # check sword location and targets