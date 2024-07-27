from Data.const import *
from Data.object import Synthesizer
import numpy as np


class Player:
    pos = ((WIDTH - size) / 2, (HEIGHT - size) / 2)  # 窗口坐标
    color = (255, 255, 255)
    font_p = pg.font.Font(font_path, round(size_p))
    sw = 300 * scale
    sh = 450 / scale / 1.5

    def __init__(self, pos, mode):
        self.x, self.y = pos[0], pos[1] + pw
        self.on = int(self.x // chunk_size[0])
        self.x0 = int(self.x // 1)
        self.y0 = int(self.y // 1)
        self.v_x = 0
        self.v_y = 0
        self.dir = 0
        self.max_speed = 8
        self.max_fall_v = -60
        self.a = 50
        self.err = 0.01 * self.a
        self.a_x = 0
        self.max_height = 1.5
        self.start_v = (2 * g * self.max_height) ** 0.5
        self.flying = False

        self.name = '我'
        self.knap = Knapsack()
        self.syner = Synthesizer((self.knap.istart[0] + self.sw, self.knap.kstart + self.sh), 2)
        self.mouse = None
        self.opening = []
        self.mode = mode  # 生存模式 0, 创造模式 1
        self.distance = 3 if self.mode == 0 else 5
        self.hp = Health(100) if self.mode == 0 else Health(0)
        self.camera = Camera(self.x, self.y)

    def __handle(arr):
        p1 = True if arr[0] == None else arr[0].penetrable
        p2 = True if arr[1] == None else arr[1].penetrable
        return not (p1 and p2)

    def collide(self, world, dx, dy):
        sx = self.x0 - self.x
        sy = self.y0 - self.y
        coll = world.get_blocks((self.x - 1, self.y + 1), (self.x + 2, self.y - 2))
        self.land = Player.__handle(coll[1:3, -2]) if self.y == self.y0 else Player.__handle(coll[1:3, -1])
        if Player.__handle(coll[0, 1:3]) and self.v_x < 0 and dx < sx:
            self.v_x = 0
            dx = sx
            self.a_x = 0 if self.dir == 0 else self.a_x
        elif Player.__handle(coll[-1, 1:3]) and self.v_x > 0 and dx > sx - pw + 2:
            self.v_x = 0
            dx = sx - pw + 2
            self.a_x = 0 if self.dir == 0 else self.a_x
        if self.land and self.v_y < 0 and dy < sy + pw - 1:
            self.hp.add(min(self.v_y + self.start_v * 2, 0) * 3.8)
            self.flying = False
            self.v_y = 0
            dy = sy + pw - 1
        elif Player.__handle(coll[1:3, 0]) and self.v_y > 0 and dy > sy + 1:
            self.v_y = 0
            dy = sy + 1
        return dx, dy

    def get_pos(self):
        return self.x, self.y

    def update(self, world):
        self.v_x += self.a_x * dt
        if self.v_x >= self.max_speed:
            self.v_x = self.max_speed
        elif self.v_x <= -self.max_speed:
            self.v_x = -self.max_speed
        if self.dir == 0 and -self.err <= self.v_x <= self.err:
            self.v_x = 0
            self.a_x = 0
        dx, dy = self.collide(world, self.v_x * dt, self.v_y * dt)
        if not self.land and not self.flying:
            self.v_y -= g * dt
            if self.v_y <= self.max_fall_v:
                self.v_y = self.max_fall_v
        self.x += dx
        self.y += dy
        self.x0 = int(self.x // 1)
        self.y0 = int(self.y // 1)
        self.on = int(self.x // chunk_size[0])
        self.knap.update()
        self.camera.update(self.x, self.y)

    def excavate(self, world, pos):
        x, y = self.camera.screen_to_world(pos)
        if -self.distance <= x - self.x0 <= self.distance + 2 and abs(y - self.y0) <= self.distance:
            item, locking, drop = world.destroy((x, y))
            self.knap.add(item)
            for i in locking:
                self.knap.add(i)
            self.knap.add(drop)

    def interact(self, world, pos):
        x, y = self.camera.screen_to_world(pos)
        try:
            block = world.get_blocks((x, y), (x, y))[0, 0]
            block.use(self.knap)
            self.opening.append(block)
        except AttributeError:
            hold = self.knap.get_hold()
            if -self.distance <= x - self.x0 <= self.distance + 2 and abs(y - self.y0) <= self.distance and (
                    not 0 <= x - self.x0 <= 2 or not -1 <= y - self.y0 <= 1) and hold != None:
                items = world.create(hold, (x, y))
                self.knap.add(items)

    def move(self, dir):
        self.v_x = 0 if self.dir == -dir else self.v_x
        self.a_x = dir * self.a
        self.dir = dir

    def stop(self, dir):
        if self.dir == dir:
            self.dir = 0
            if self.v_x != 0:
                self.a_x = -dir * self.a

    def fly(self, dir):
        if self.mode == 1:
            self.v_y = dir * self.max_speed
            self.flying = True

    def stop_fly(self, dir):
        if self.mode == 1 and dir * self.v_y >= 0:
            self.v_y = 0

    def jump(self):
        if self.land:
            self.v_y = self.start_v

    def click(self, pos, button):
        if self.knap.out_knap(pos):
            self.mouse = None
        else:
            if button == 1:
                mode = 'all'
            elif button == 3:
                if self.mouse == None:
                    mode = 'half'
                else:
                    mode = 'one'
            if self.knap.in_edge(pos):
                self.mouse = self.knap.click(pos, self.mouse, mode)
            elif self.syner.in_edge(pos):
                self.mouse = self.syner.click(pos, self.mouse, mode)
            self.syner.match()
            for i in self.opening:
                if i.in_edge(pos):
                    self.mouse = i.click(pos, self.mouse, mode)
                i.match()

    def open(self):
        self.knap.open()
        self.syner.open() if self.knap.opening else self.syner.close(self.knap)
        self.knap.add(self.mouse) if not self.knap.opening else None
        self.mouse = None
        for i in self.opening:
            i.close(self.knap)
        self.opening = []

    def reset(self):
        self.knap.add(self.mouse)
        self.knap.add(self.mouse) if not self.knap.opening else None
        self.mouse = None
        self.knap.close()
        self.syner.close(self.knap)
        for i in self.opening:
            i.close(self.knap)
        self.opening = []
        self.v_x = 0
        self.a_x = 0
        self.dir = 0
        self.v_y = 0

    def set_acceleration(self, accel):
        self.a = accel

    def set_max_speed(self, speed):
        self.max_speed = speed

    def set_max_height(self, height):
        self.max_height = height

    def draw(self, screen):
        draw_word(screen, self.name, color, self.pos, self.font_p)
        draw_word(screen, f'({self.x0},{self.y0})', color, (10, 10))

        self.knap.draw(screen)
        self.syner.draw(screen)
        if not self.knap.opening:
            self.hp.draw(screen, self.knap.width, self.knap.iheight)
        for i in self.opening:
            i.draw_ui(screen)
        x, y = pg.mouse.get_pos()
        self.mouse.draw(screen, x - 25 * scale, y - 20 * scale) if self.mouse != None else None


class Health:
    sp = 8 * scale
    color = (255, 0, 0)

    def __init__(self, max):
        self.health = max
        self.max = max

    def add(self, amount):
        if self.max > 0:
            self.health = min(self.health + amount, self.max)

    def set(self, amount):
        self.health = amount

    def reset(self):
        self.health = self.max

    def set_max(self, amount):
        self.max = amount

    def dead(self):
        return self.health <= 0 if self.max > 0 else False

    def draw(self, screen, width, height):
        if self.max > 0:
            pg.draw.rect(screen, 'red',
                         (int((WIDTH - width) / 2), HEIGHT - height - self.sp - 12,
                          int(self.health / self.max * width), self.sp))


class Knapsack:
    edge = (10, 3)
    width = edge[0] * per
    height = edge[1] * per
    rect_w = round(4 * scale)
    line_w = round(2 * scale)

    iheight = per + rect_w * 2
    istart = (int((WIDTH - width) / 2), HEIGHT - iheight + rect_w - 10)

    kstart = rect_w
    kheight = HEIGHT - kstart - per - rect_w - 10
    kstarty = istart[1] - (edge[1] + 1) * per

    surface = pg.Surface((per, per), pg.SRCALPHA)
    surface.fill((255, 215, 0, 70))

    def __init__(self):
        self.knap = np.full((self.edge[0], self.edge[1] + 1), None, dtype=object)
        self.indice = 0
        self.opening = False

    def open(self):
        self.opening = not self.opening

    def in_edge(self, pos):
        x, y = pos[0] - self.istart[0], pos[1] - self.kstarty
        return 0 <= x <= self.width and 0 <= y <= self.height + per * 2

    def click(self, pos, on, mode='all'):
        x, y = pos[0] - self.istart[0], pos[1] - self.kstarty
        x = int(x // per)
        y = int(y // per)
        if y != self.edge[1]:
            y = self.edge[1] if y == self.edge[1] + 1 else y
            items = self.knap[x, y]
            if on == None:
                if items != None:
                    return items.apart(mode)
            else:
                if items == None:
                    self.knap[x, y] = on.apart(mode)
                else:
                    self.knap[x, y], on = items.add(on.apart('all'))
        return on

    def close(self):
        self.opening = False

    def add(self, items, ij=None):
        if items != None:
            if ij == None:
                hold = self.get_hold()
                if (hold != items and hold != None) or (hold == items and (hold.full() if hold != None else False)):
                    cases = self.knap.copy()
                    cases[np.vectorize(lambda x: x.full() if x != None else False)(self.knap)] = None
                    indice = np.where(cases == items)
                    if len(indice[0]) == 0:
                        indice = np.where(self.knap[:, self.edge[1]] == None)
                        if len(indice[0]) == 0:
                            indice = np.where(self.knap == None)
                            if len(indice[0]) == 0:
                                return
                            else:
                                ij = (indice[0][0], indice[1][0])
                        else:
                            ij = (indice[0][0], self.edge[1])
                    else:
                        ij = (indice[0][0], indice[1][0])
                else:
                    ij = (self.indice, self.edge[1])
                if (old := self.knap[ij[0], ij[1]]) == None:
                    self.knap[ij[0], ij[1]] = items
                else:
                    old.add(items)
                    self.add(items)
            else:
                if (old := self.knap[ij[0], ij[1]]) == items:
                    old.add(items)
                else:
                    self.knap[ij[0], ij[1]] = items

    def update(self):
        self.knap = np.where(self.knap == None, None, self.knap)

    def get_hold(self):
        return self.knap[self.indice, self.edge[1]]

    def out_knap(self, pos):
        x, y = pos
        return not (0 <= x - self.istart[0] <= self.width and 0 <= y - self.kstart <= HEIGHT - self.kstart - 10)

    def set_indice(self, pos):
        self.indice = 9 if pos == 0 else pos - 1

    def move_indice(self, dir):
        if not self.opening:
            self.indice += dir
            match self.indice:
                case -1:
                    self.indice = 9
                case 10:
                    self.indice = 0

    def draw_knap(self, screen):
        pg.draw.rect(screen, knapcolor,
                     (self.istart[0] - self.rect_w, self.kstart, self.width + self.rect_w * 2,
                      self.kheight))
        pg.draw.rect(screen, backcolor,
                     (self.istart[0], self.kstarty, self.width, self.height))
        for i in range(self.edge[0]):
            for j in range(self.edge[1]):
                x = self.istart[0] + i * per
                pg.draw.rect(screen, knapcolor,
                             (x, self.istart[1] - (j + 2) * per, per, per),
                             self.line_w)
                if (items := self.knap[i, j]) != None:
                    items.draw(screen, x, self.istart[1] - (self.edge[1] - j + 1) * per)

    def draw(self, screen):
        pg.draw.rect(screen, knapcolor,
                     (self.istart[0] - self.rect_w, self.istart[1] - self.rect_w, self.width + self.rect_w * 2,
                      self.iheight),
                     self.rect_w)
        pg.draw.rect(screen, backcolor,
                     (self.istart[0], self.istart[1], self.width, per))
        for i in range(self.edge[0]):
            pg.draw.rect(screen, knapcolor,
                         (self.istart[0] + i * per, self.istart[1], per, per),
                         self.line_w)
            if (items := self.knap[i, self.edge[1]]) != None:
                items.draw(screen, self.istart[0] + i * per, self.istart[1])

        if self.opening:
            self.draw_knap(screen)
        else:
            screen.blit(self.surface, (self.istart[0] + self.indice * per, self.kstarty + (self.edge[1] + 1) * per))


class Camera:
    rect = (45, 25)
    offset = (-(rect[0] // 2), rect[1] // 2)
    c1 = (WIDTH - rect[0] * size) / 2
    c2 = (HEIGHT - rect[1] * size) / 2

    def __init__(self, x, y, scaled=1.0):
        self.x = x + self.offset[0]
        self.y = y + self.offset[1]
        self.scaled = scaled

    def get_pos(self):
        return self.x, self.y

    def scale(self, scaled):
        self.scaled = scaled

    def screen_to_world(self, pos):
        x = (pos[0] - self.c1) / size + self.x
        y = -(pos[1] - self.c2) / size + self.y
        return x, y

    def world_to_screen(self, pos):
        x = (pos[0] - self.x) * size + self.c1
        y = -(pos[1] - self.y) * size + self.c2
        return x, y

    def update(self, x, y):
        self.x = x + self.offset[0]
        self.y = y + self.offset[1]
