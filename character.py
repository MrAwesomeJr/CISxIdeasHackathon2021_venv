import pygame
from os import path
from pygame import freetype


class Character:
    def __init__(self, map):
        self.show_hitbox = False
        self.show_hurtbox = False

        pygame.init()

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

        self.hitbox_queue = []

        self.blocking_anim = False
        # velocity per frame (30fps)
        self.velocity = [0,0]

        # to stop processing pointless events
        self.old_velocity = 0
        self.velocity_unchanged = False
        self.collided = False

        self.total_frame = 0

        self.font = pygame.freetype.Font(path.join(".", "fonts", "Menlo.ttc"))
        self.font.size = 12
        self.font.fgcolor = (156, 170, 255)

        # initialize animations ((<x_offset>, <y_offset>),[<surface>])
        # x_offset and y_offset are relative to the top left corner of the character (the hitbox is 14x28)
        # all animations are facing right. Animations are flipped in self._render()
        self.anim_idle = self._load_char_anim((-8, 0), path.join(".", "images", "char", "idle"), (32, 32), frames = 4)
        self.anim_aerial = [(-8, 0), pygame.transform.scale(pygame.image.load(path.join(".", "images", "char", "idle", "0.png")), (32, 32))]
        self.anim_jump = self._load_char_anim((-8, 0), path.join(".", "images", "char", "jump"), (32, 32), frames = 6)
        self.anim_walk = self._load_char_anim((-8, 0), path.join(".", "images", "char", "walk"), (32, 32), frames = 7)
        self.anim_ftilt = self._load_char_anim((-8, 0), path.join(".", "images", "char", "ftilt"), (32, 32), frames = 12)
        self.anim_btilt = self._load_char_anim((-8, -3), path.join(".", "images", "char", "btilt"), (32, 32), frames = 8)
        self.anim_utilt = self._load_char_anim((-8, -3), path.join(".", "images", "char", "utilt"), (32, 32), frames = 12)
        # self.anim_fair = self._load_char_anim((-8, 0), path.join(".", "images", "char", "fair"), (32, 32), frames = 1)

    def _load_char_anim(self, offset, dir, size, frames = 1):
        anim_list = [offset]
        for frame in range(frames):
            anim_list.append(pygame.transform.scale(pygame.image.load(path.join(dir, str(frame)+".png")), size))
        return anim_list

    def run(self, screen):
        self.screen = screen
        # run one frame or freeze if game is frozen
        # freeze game if game has ended
        if self.map.done:
            self.framedata = []
            if self.map.win_frames == 0:
                self.map.win_frames = self.total_frame

        self._render(screen)
        self._tick()
        self.total_frame += 1

    def spawn(self):
        self.pos = [(self.map.spawnpoint[0] + self.map.x_block_offset) * self.map.pixel_size[0] +
                    self.map.render_offset[0] + ((self.map.pixel_size[0] - self.size[0]) / 2),
                    (self.map.spawnpoint[1] + self.map.y_block_offset + 2) * self.map.pixel_size[1] +
                    self.map.render_offset[1] - self.size[1]]

        self.grounded = True
        self.framedata = []
        self.anim_stack = []
        self.hitbox_queue = []
        self.blocking_anim = False
        self.velocity = [0,0]
        self.facing = "right"
        self.total_frame = 0
        self.collided = False
        self.velocity_unchanged = False



    def _render(self, screen):
        # idle if nothing is happening
        if len(self.anim_stack) == 0:
            self.blocking_anim = False
            if self.grounded:
                if self.velocity[0] == 0 and self.velocity[1] == 0:
                    self.push_animation(self.anim_idle)
                else:
                    self.push_animation(self.anim_walk)
            else:
                # when in the air
                self.push_animation(self.anim_aerial)

        # debugging hurtbox display
        if self.show_hurtbox:
            debug_box = pygame.Surface(self.size)
            debug_box.fill((255, 0, 0))
            screen.blit(debug_box, pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1]))

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

        # frame counter
        screen.blit(*self.font.render(str(self.total_frame)))

    def push_animation(self, anim_list, block_flag = False, facing = None):
        if facing != None:
            self.facing = facing
        # dereference original anim_list
        anim_list = anim_list[:]
        if len(self.anim_stack) == 0 or not self.blocking_anim:
            if len(self.anim_stack) == 0:
                self.blocking_anim == block_flag
            offset = anim_list[0]
            anim_list.pop(0)
            self.anim_stack = []
            for anim in anim_list:
                self.anim_stack.append((anim, offset))

    def push_hitbox(self, direction, frame):
        frame = frame * 3
        if len(self.hitbox_queue) <= frame:
            while len(self.hitbox_queue) <= frame:
                self.hitbox_queue.append("")
            self.hitbox_queue.append(direction)
        else:
            self.hitbox_queue[frame] = direction


    def _tick(self):
        # action to do in current frame
        if len(self.framedata) > 0:
            # print(self.framedata[0])
            if self.framedata[0] == "jump":
                if self.grounded:
                    self.push_animation(self.anim_jump, block_flag = True)
            elif self.framedata[0] == "endjump":
                if self.grounded:
                    self.velocity[1] = -1.8
            elif self.framedata[0] == "left":
                self.velocity[0] = -2
                if self.grounded:
                    self.push_animation(self.anim_walk, facing = "left")
            elif self.framedata[0] == "right":
                self.velocity[0] = 2
                if self.grounded:
                    self.push_animation(self.anim_walk, facing = "right")
            elif self.framedata[0] == "stop":
                self.velocity[0] = 0
            elif self.framedata[0] == "atk_left":
                if self.facing == "right":
                    self.push_hitbox("left",3)
                    self.push_animation(self.anim_btilt, facing = "right")
                elif self.facing == "left":
                    self.push_hitbox("left",7)
                    self.push_animation(self.anim_ftilt, facing = "left")
            elif self.framedata[0] == "atk_right":
                if self.facing == "right":
                    self.push_hitbox("right",7)
                    self.push_animation(self.anim_ftilt, facing = "right")
                elif self.facing == "left":
                    self.push_hitbox("right",3)
                    self.push_animation(self.anim_btilt, facing = "left")
            elif self.framedata[0] == "atk_up":
                self.push_hitbox("up",7)
                self.push_animation(self.anim_utilt)

            self.framedata.pop(0)



        # calculate physics
        if not self.grounded:
            self.velocity[1] += 0.05
        elif self.velocity[1] > 0:
            self.velocity[1] = 0
        new_pos = self.pos[:]
        new_pos[0] += self.velocity[0]
        new_pos[1] += self.velocity[1]

        if self.velocity == self.old_velocity:
            self.velocity_unchanged = True
        else:
            self.velocity_unchanged = False
        self.old_velocity = self.velocity[:]

        # prevent walking into walls
        if not self.collided or not self.velocity_unchanged:
            # test if any squares intersect
            intersect = self._block_intersect(new_pos, self.size)

            # if there is an intersection, attempt to circumvent block by not going up or down
            if intersect:
                if self.velocity[1] < 0:
                    while new_pos[1] <= self.pos[1] and intersect:
                        new_pos[1] += 0.05
                        intersect = self._block_intersect(new_pos, self.size)
                elif self.velocity[1] > 0:
                    while new_pos[1] >= self.pos[1] and intersect:
                        new_pos[1] -= 0.05
                        intersect = self._block_intersect(new_pos, self.size)

            # then attempt to not go forwards
            if intersect:
                new_pos[1] = self.pos[1] + self.velocity[1]
                if self.velocity[0] > 0:
                    while new_pos[0] >= self.pos[0] and intersect:
                        new_pos[0] -= 0.05
                        intersect = self._block_intersect(new_pos, self.size)
                elif self.velocity[0] < 0:
                    while new_pos[0] <= self.pos[0] and intersect:
                        new_pos[0] += 0.05
                        intersect = self._block_intersect(new_pos, self.size)

            # otherwise don't move.
            if not intersect:
                self.collided = False
                # test if grounded
                self.grounded = self._block_intersect([new_pos[0],new_pos[1]+1], self.size)
                self.pos = [round(self.pos[0],2),round(self.pos[1],2)]
                new_pos = [round(new_pos[0],2),round(new_pos[1],2)]
                if self.pos != new_pos:
                    self.pos = new_pos
                else:
                    self.collided = True


        # hitboxes
        attack_length = 10
        attack_width = 2
        if len(self.hitbox_queue) > 0:
            if self.hitbox_queue[0] == "up":
                hitbox_pos = [self.pos[0] + (self.size[0] - attack_width) / 2, self.pos[1] - attack_length]
                hitbox_size = [attack_width, attack_length]

                self._block_intersect(hitbox_pos, hitbox_size, block_type = 2)

                # render hitbox
                if self.show_hitbox:
                    print(hitbox_pos, hitbox_size)
                    hitbox_surface = pygame.Surface(hitbox_size)
                    hitbox_surface.fill((0, 255, 0))
                    self.screen.blit(hitbox_surface,pygame.Rect(hitbox_pos[0], hitbox_pos[1], hitbox_size[0], hitbox_size[1]))

            elif self.hitbox_queue[0] == "right":
                hitbox_pos = [self.pos[0] + self.size[0], self.pos[1] - (attack_width - self.size[1]) / 2]
                hitbox_size = [attack_length, attack_width]

                self._block_intersect(hitbox_pos, hitbox_size, block_type = 2)

                # render hitbox
                if self.show_hitbox:
                    print(hitbox_pos, hitbox_size)
                    hitbox_surface = pygame.Surface(hitbox_size)
                    hitbox_surface.fill((0, 255, 0))
                    self.screen.blit(hitbox_surface,pygame.Rect(hitbox_pos[0], hitbox_pos[1], hitbox_size[0], hitbox_size[1]))

            elif self.hitbox_queue[0] == "left":
                hitbox_pos = [self.pos[0] - attack_length, self.pos[1] - (attack_width - self.size[1]) / 2]
                hitbox_size = [attack_length, attack_width]

                self._block_intersect(hitbox_pos, hitbox_size, block_type = 2)

                # render hitbox
                if self.show_hitbox:
                    print(hitbox_pos, hitbox_size)
                    hitbox_surface = pygame.Surface(hitbox_size)
                    hitbox_surface.fill((0, 255, 0))
                    self.screen.blit(hitbox_surface,pygame.Rect(hitbox_pos[0], hitbox_pos[1], hitbox_size[0], hitbox_size[1]))


            self.hitbox_queue.pop(0)


    def _block_intersect(self, pos, size, block_type = 1):
        # if block type is 2 break the target
        player_rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        intersect = False
        for y_index in range(self.map.total_map_size[0]):
            for x_index in range(self.map.total_map_size[1]):
                if self.map.render_map[y_index][x_index] == block_type:
                    block_rect = pygame.Rect((self.map.render_offset[0] + x_index * self.map.pixel_size[0],
                                              self.map.render_offset[1] + y_index * self.map.pixel_size[1],
                                              self.map.pixel_size[0],
                                              self.map.pixel_size[1]))
                    intersect = player_rect.colliderect(block_rect)
                    if intersect:
                        if block_type == 2:
                            self.map.break_target(x_index, y_index)
                        return intersect
        return intersect
