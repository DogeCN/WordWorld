import pygame as pg
import win32api

pg.init()

# 获取屏幕信息
info = pg.display.Info()
# 获取屏幕宽度
WIDTH = info.current_w
# 获取屏幕高度
HEIGHT = info.current_h
# 计算缩放比例，取最小值
scale = (WIDTH / 1360 + HEIGHT / 768) / 2
# 计算字体大小
size = 28 * scale
per = size * scale * 2
size_p = size * 1.4
pw = size_p / size
# 设置字体颜色
color = (255, 255, 255)
nocolor = (127, 127, 127)
# 设置背景颜色
backcolor = (0, 0, 0)
knapcolor = (200, 200, 200)
# 设置字体
font_path = 'Data/resource/Zpix-beta-3.0.2.ttf'
save_path = 'Save'
block_path = ['Data/json/blocks/chinese.json', 'Data/json/blocks/symbol.json']
real_path = 'Data/json/recipes/real'
font = pg.font.Font(font_path, round(size))
title = pg.transform.scale(pg.image.load('Data/resource/title.png'), (WIDTH, HEIGHT - 108))
tw = title.get_width()
th = title.get_height()
# 设置区块大小
chunk_size = (48, 128)
# 表示世界中区块的编号范围
edgechunk = (-20, 19)
# 设置x轴边界
edgex = (-960, 959)
# 设置y轴边界
edgey = (-63, 64)
# 获取屏幕刷新率
fps = win32api.EnumDisplaySettings(None, 0).DisplayFrequency
# 计算刷新时间
dt = 1 / fps

g = 55

p = [0.9, 0.1]


def draw_word(screen, text, color, pos, font=font):
    t = font.render(text, True, color)
    screen.blit(t, pos)
