from Data.const import *
from datetime import datetime
import random as rd
import json
import shutil
import os


class Button:
    def __init__(self, name, option, pos, scale=1.0):
        self.name = name
        self.option = option
        self.l = [len(i) for i in option]
        self.length = len(option)
        self.x, self.y = pos
        self.indice = 0
        self.h2width = 80 * scale
        self.hwidth = self.h2width * self.length
        self.width = self.hwidth * 2
        self.height = 40 * scale
        self.hwidth = self.width / 2

        self.sp = 6 * scale
        self.size = self.height - self.sp * 2
        self.font = pg.font.Font(font_path, round(self.size))
        self.ocolor = [color] * self.length
        self.ocolor[0] = backcolor

    def click(self, pos):
        x, y = pos[0] - self.x - self.hwidth, pos[1] - self.y
        if 0 <= x <= self.hwidth and 0 <= y < self.height:
            self.ocolor[self.indice] = color
            self.indice = int(x // self.h2width)
            self.ocolor[self.indice] = backcolor

    def get_width(self):
        return self.width

    def get_choice(self):
        return self.indice

    def move_to(self, pos):
        self.x, self.y = pos

    def draw(self, screen):
        pg.draw.rect(screen, color, (self.x - 2, self.y - 2, self.width, self.height), 2)
        pg.draw.line(screen, color, (self.x + self.hwidth, self.y), (self.x + self.hwidth, self.y + self.height - 4), 1)
        draw_word(screen, self.name, color,
                  (self.x + self.hwidth / 2 - self.size * len(self.name) / 2, self.y + self.sp),
                  self.font)
        pg.draw.rect(screen, color, (
            self.x + self.hwidth + self.h2width * self.indice, self.y - 2, self.h2width, self.height))
        for i in range(self.length):
            draw_word(screen, self.option[i], self.ocolor[i],
                      (self.x + self.hwidth + self.h2width * (i + 0.5) - self.size * self.l[i] / 2, self.y + self.sp),
                      self.font)


class TextInput:
    def __init__(self, name, pos, max, char=True, no_click_text=''):
        self.name = name + ':'
        self.text = ''
        self.x, self.y = pos
        self.max = max
        self.char = char
        self.width = size * (max + 2) if char else size * max / 1.5
        self.nwidth = size * (len(name) + 1)
        self.sp = 10 * scale
        self.height = size + self.sp * 2
        self.on_click = False
        self.no_click_text = no_click_text
        self.ncolor = (127, 127, 127)

    def click(self, pos):
        x, y = pos[0] - self.x - self.nwidth, pos[1] - self.y
        self.on_click = 0 <= x <= self.width and 0 <= y <= self.height

    def input(self, text):
        if self.on_click:
            if self.char:
                for i in text:
                    if len(self.text) < self.max:
                        if i not in [' ', '/', '\\', '*', '?', '\"', '|', ':', '<', '>']:
                            self.text += i
            else:
                for i in text:
                    if len(self.text) < self.max:
                        if i in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or (i == '-' and self.empty()):
                            self.text += i

    def remove(self):
        if self.on_click:
            self.text = self.text[:-1]

    def empty(self):
        return self.text == ''

    def move_to(self, pos):
        self.x, self.y = pos

    def get_width(self):
        return self.width + self.nwidth + 2

    def draw(self, screen):
        draw_word(screen, self.name, color, (self.x, self.y + self.sp))
        pg.draw.rect(screen, color, (self.x + self.nwidth - 2, self.y - 2, self.width, self.height), 2)
        text = self.text + '_' if self.on_click else self.text
        if text == '':
            draw_word(screen, self.no_click_text, self.ncolor, (self.x + self.nwidth + self.sp, self.y + self.sp))
        draw_word(screen, text, color, (self.x + self.nwidth + self.sp, self.y + self.sp))


class UI:
    def __init__(self, options):
        self.options = options
        self.length = len(self.options)
        self.indice = 0

    def move_indice(self, dir):
        self.indice += dir
        if self.indice == -1:
            self.indice = self.length - 1
        elif self.indice == self.length:
            self.indice = 0

    def get_width(self, n):
        return font.render(self.options[n], True, color).get_width()


class Home(UI):
    sp = size + 30 * scale
    width = (WIDTH - tw) / 2
    height = HEIGHT - th
    start_y = height + th * 26 / 33 - sp * 3 + 30 * scale

    def __init__(self):
        super().__init__(['开始游戏', '设置', '退出'])
        self.ostart = (WIDTH - self.get_width(0)) / 2 + 25 * scale

    def draw(self, screen):
        screen.blit(title, (self.width, self.height))
        for i in range(self.length):
            draw_word(screen, self.options[i], color, (self.ostart, self.start_y + self.sp * i))
        draw_word(screen, '我', color, (self.ostart - size - 10, self.start_y + self.sp * self.indice))


class Worlds(UI):
    start = 250 * scale
    bstart = start - 13
    width = WIDTH - start * 2
    sp = 30 * scale
    oh = 100 * scale
    uh = 240 * scale
    start_y = HEIGHT - uh + oh + 30
    dis = 200 * scale
    dh = 50 * scale
    twidth = font.render('2024-07-13 18:03:33', True, color).get_width()
    surface = pg.Surface((width + 20, size + sp), pg.SRCALPHA)
    surface.fill((255, 215, 0, 70))

    def __init__(self):
        super().__init__(['进入世界', '删除世界', '创造世界', '返回'])
        try:
            worlds = os.listdir(save_path)
        except FileNotFoundError:
            os.mkdir(save_path)
            self.__init__()
        else:
            modes, types, seeds = [], [], []
            for i in worlds:
                with open(os.path.join(save_path, i, 'data.json'), 'r') as file:
                    data = json.load(file)
                modes.append(data['mode'])
                types.append(data['type'])
                seeds.append(data['seed'])
            times = [str(datetime.fromtimestamp(round(os.path.getmtime(os.path.join(save_path, i, 'player.pkl')))))
                     for i in worlds]
            self.worlds = sorted(zip(worlds, types, modes, seeds, times), key=lambda x: x[4], reverse=True)
            self.n = len(self.worlds)
            self.world = None
            self.ocolor = [nocolor, nocolor, color, color]

    def click(self, pos):
        x, y = pos
        if 0 <= x - self.start <= self.width and 0 <= y - self.oh <= self.start_y:
            if (n := int((y - self.oh) // (size + self.sp))) <= self.n - 1:
                self.world = None if self.world == n else n

    def delete(self):
        if self.world != None:
            shutil.rmtree(os.path.join(save_path, self.get_world()[0]))
            self.worlds.pop(self.world)
            self.n -= 1
            self.world = None

    def get_world(self):
        return self.worlds[self.world]

    def draw(self, screen):
        draw_word(screen, '世界', color, (WIDTH / 2 - size, self.dh))
        pg.draw.rect(screen, color, (self.bstart, self.oh, WIDTH - (self.start - 10) * 2, HEIGHT - self.uh), 3)
        for i in range(self.n):
            y = self.oh + 17 + (size + self.sp) * i
            x = WIDTH - self.start - self.twidth
            draw_word(screen, self.worlds[i][0], color, (self.start, y))
            draw_word(screen, self.worlds[i][4], color, (x, y))
            mode = '生存' if self.worlds[i][2] == 0 else '创造'
            type = '随机' if self.worlds[i][1] == 0 else '平坦'
            draw_word(screen, mode, color, (x - size * 3, y))
            draw_word(screen, type, color, (x - size * 6, y))
        if self.world == None:
            self.ocolor[0:2] = nocolor, nocolor
        else:
            y1 = self.oh + 17 + (size + self.sp) * self.world - self.sp / 2
            y2 = y1 + size + self.sp
            pg.draw.line(screen, color, (self.bstart, y1), (self.start + self.width + 3, y1), 2)
            pg.draw.line(screen, color, (self.bstart, y2), (self.start + self.width + 3, y2), 2)
            screen.blit(self.surface, (self.bstart, y1))
            self.ocolor[0:2] = color, color

        for i in range(self.length):
            draw_word(screen, self.options[i], self.ocolor[i],
                      (WIDTH / 2 + size * 2.5 + self.dis * (i - 2), self.start_y))
        draw_word(screen, '我', color,
                  (WIDTH / 2 + size * 2.5 + self.dis * (self.indice - 2) - size - 10, self.start_y))


class Create(UI):
    max = 12
    dis = 150 * scale
    bwidth = size * (max + 2) * scale
    sp = 10 * scale
    bheight = size + sp * 2
    start_y = 200 * scale
    space = 90 * scale
    height = start_y + space * 4

    def __init__(self):
        super().__init__(['生成世界', '返回'])
        self.name = TextInput('世界名称', (0, 0), self.max)
        self.seed = TextInput('世界种子', (0, 0), 21, False, '随机')
        self.type = Button('地形', ['随机', '平坦'], (0, 0), scale)
        self.mode = Button('模式', ['生存', '创造'], (0, 0), scale)
        self.name.move_to(((WIDTH - self.name.get_width()) / 2, self.start_y))
        self.seed.move_to((self.name.x, self.start_y + self.space))
        self.type.move_to(((WIDTH - self.type.get_width()) / 2, self.start_y + self.space * 2))
        self.mode.move_to((self.type.x, self.start_y + self.space * 3))
        self.ocolor = [nocolor, color]

    def click(self, pos):
        self.name.click(pos)
        self.seed.click(pos)
        self.type.click(pos)
        self.mode.click(pos)
        pg.key.start_text_input() if self.name.on_click or self.seed.on_click else pg.key.stop_text_input()

    def world_data(self):
        seed = rd.randint(-int('9' * 20), int('9' * 21)) if self.seed.empty() else int(self.seed.text)
        return self.name.text, seed, self.type.get_choice(), self.mode.get_choice()

    def input(self, text):
        self.name.input(text)
        self.seed.input(text)

    def remove(self):
        self.name.remove()
        self.seed.remove()

    def draw(self, screen):
        self.ocolor[0] = nocolor if self.name.empty() else color
        self.name.draw(screen)
        self.seed.draw(screen)
        self.type.draw(screen)
        self.mode.draw(screen)
        for i in range(self.length):
            draw_word(screen, self.options[i], self.ocolor[i], (WIDTH / 2 + self.dis * (i * 2 - 1) - size, self.height))
        draw_word(screen, '我', color,
                  (WIDTH / 2 - self.dis + (self.dis * self.indice - size) * 2 - 10,
                   self.height))


class Dead(UI):
    tsize = 200 * scale
    tfont = pg.font.Font(font_path, round(tsize))
    height = 180 * scale
    start_y = 480 * scale
    dis = 150 * scale

    def __init__(self):
        super().__init__(['复活', '退出'])

    def draw(self, screen):
        draw_word(screen, '你死了', color, ((WIDTH - self.tsize * 3) / 2, self.height), self.tfont)
        for i in range(self.length):
            draw_word(screen, self.options[i], color, (WIDTH / 2 + self.dis * (i * 2 - 1) - size, self.start_y))
        draw_word(screen,'我', color,
                  (WIDTH / 2 - self.dis + (self.dis * self.indice - size) * 2 - 10,self.start_y))

