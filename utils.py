import math
import os

FONT_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'PressStart2P-Regular.ttf')

def pad(n):
    return str(max(0, round(n))).zfill(5)

def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

def clamp(v, a, b):
    return max(a, min(b, v))

def get_font(size):
    import pygame
    return pygame.font.Font(FONT_PATH, size)

def get_font_safe(size):
    import pygame
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.Font(None, size * 2)
