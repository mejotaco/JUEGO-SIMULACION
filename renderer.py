import pygame
import os
import math
import random
from config import WHITE, P1_COLOR, P1_DARK, P2_COLOR, P2_DARK, POWERUP_TYPES

ASSETS = os.path.join(os.path.dirname(__file__), 'assets')

player_sheet = None
helicopter_sheet = None
bg_image = None
enemy_sprites = [None, None, None]

def load_assets():
    global player_sheet, helicopter_sheet, bg_image, enemy_sprites
    try:
        player_sheet = pygame.image.load(os.path.join(ASSETS, 'ships', 'player001_sheet.png')).convert_alpha()
    except Exception:
        player_sheet = None
    try:
        helicopter_sheet = pygame.image.load(os.path.join(ASSETS, 'enemies', 'helicopter_sheet.png')).convert_alpha()
    except Exception:
        helicopter_sheet = None
    try:
        bg_image = pygame.image.load(os.path.join(ASSETS, 'backgrounds', 'space_bg.png')).convert()
    except Exception:
        bg_image = None

    root = os.path.dirname(__file__)
    names = ['enemigo1.png', 'enemigo2.png', 'enemigo3.png']
    for i, name in enumerate(names):
        try:
            img = pygame.image.load(os.path.join(root, name)).convert_alpha()
            enemy_sprites[i] = img
        except Exception:
            enemy_sprites[i] = None

PLAYER_FW = 48
PLAYER_FH = 32
HELI_FW = 48
HELI_FH = 32
BG_W = 512

_bg_scaled = {}

def render(screen, state, get_font):
    GAME_W = state['GAME_W']
    GAME_H = state['GAME_H']
    HALF_H = state['HALF_H']
    mode = state['currentMode']
    eb = state['eBullets']
    pb = state['bullets']
    en = state['enemies']
    pl = state['players']
    pt = state['particles']
    sp = state['scorePopups']

    screen.fill((0, 0, 0))

    shake = state.get('shake', 0)
    shake_dx = 0
    shake_dy = 0
    if shake > 0:
        power = shake * 22
        shake_dx = int((1 if random.random() > 0.5 else -1) * power)
        shake_dy = int((1 if random.random() > 0.5 else -1) * power)

    if bg_image:
        full_h = screen.get_height()
        if 'full_h' not in _bg_scaled or _bg_scaled.get('_h') != full_h:
            _bg_scaled['full_h'] = pygame.transform.scale(bg_image, (BG_W, full_h))
            _bg_scaled['_h'] = full_h
        bg = _bg_scaled['full_h']
        scroll = int(pygame.time.get_ticks() * 0.05) % BG_W
        x = -scroll
        while x < GAME_W:
            screen.blit(bg, (x + shake_dx, shake_dy))
            x += BG_W
    else:
        for s in state.get('starField', []):
            a = int(s['a'] * 255)
            star = pygame.Surface((s['r'], s['r']), pygame.SRCALPHA)
            star.fill((255, 255, 255, a))
            screen.blit(star, (int(s['x']) + shake_dx, int(s['y']) + shake_dy))

    if mode == 2:
        for x in range(0, GAME_W, 14):
            div = pygame.Surface((8, 2), pygame.SRCALPHA)
            div.fill((240, 160, 0, 51))
            screen.blit(div, (x + shake_dx, HALF_H - 1 + shake_dy))
        for p in pl:
            if p['dead']:
                zy = 0 if p['id'] == 0 else HALF_H
                overlay = pygame.Surface((GAME_W, HALF_H), pygame.SRCALPHA)
                overlay.fill((60, 0, 0, 89))
                screen.blit(overlay, (shake_dx, zy + shake_dy))
                txt = get_font(9).render('ELIMINATED', True, (255, 51, 51))
                txt.set_alpha(68)
                tr = txt.get_rect(center=(GAME_W // 2 + shake_dx, zy + HALF_H // 2 + shake_dy))
                screen.blit(txt, tr)

    for b in eb:
        bx, by = int(b['x'] - b['w'] / 2) + shake_dx, int(b['y'] - b['h'] / 2) + shake_dy
        pygame.draw.rect(screen, (255, 136, 0), (bx, by, b['w'], b['h']))
        pygame.draw.rect(screen, (255, 221, 0), (bx + 2, by + 1, b['w'] - 5, b['h'] - 2))

    for b in pb:
        if b['dead']:
            continue
        bx, by = int(b['x']) + shake_dx, int(b['y'] - b['h'] / 2) + shake_dy
        pygame.draw.rect(screen, b['color'], (bx, by, b['w'], b['h']))
        pygame.draw.rect(screen, WHITE, (bx + 3, by + 1, b['w'] - 8, b['h'] - 2))

    for e in en:
        if not e['dead']:
            draw_enemy(screen, e, shake_dx, shake_dy)

    for pu in state.get('powerups', []):
        draw_powerup(screen, pu, shake_dx, shake_dy)

    for p in pl:
        if p['dead']:
            continue
        if p['invTimer'] > 0 and int(p['invTimer'] * 10) % 2 == 0:
            continue
        draw_player(screen, p, shake_dx, shake_dy, get_font)

    for p in pt:
        alpha = max(0, min(1, p['life'] * 2.8))
        sz = max(2, int(p['r']))
        s = pygame.Surface((sz, sz), pygame.SRCALPHA)
        s.set_alpha(int(alpha * 255))
        s.fill(p['color'])
        screen.blit(s, (int(p['x']) + shake_dx, int(p['y']) + shake_dy))

    score_font = get_font(10)
    for s in sp:
        alpha = max(0, min(1, s['life'] * 1.2))
        txt = score_font.render(s['text'], True, s['color'])
        txt.set_alpha(int(alpha * 255))
        tr = txt.get_rect(center=(int(s['x']) + shake_dx, int(s['y']) + shake_dy))
        screen.blit(txt, tr)

def draw_player(screen, p, shake_dx=0, shake_dy=0, get_font=None):
    if p.get('easterTimer', 0) > 0:
        bob = math.sin(pygame.time.get_ticks() * 0.008) * 3
        bx = int(p['x'] - PLAYER_FW / 2) + shake_dx
        by = int(p['y'] - PLAYER_FH / 2) + shake_dy + int(bob)
        if player_sheet:
            frame = int(pygame.time.get_ticks() / 180) % 2
            spr = player_sheet.subsurface(frame * PLAYER_FW, 0, PLAYER_FW, PLAYER_FH)
            screen.blit(spr, (bx, by))
        else:
            draw_pixel_ship_fallback(screen, p, shake_dx, shake_dy)
        if get_font:
            bubble = 'PONGANOS 10 PROFE!'
            f = get_font(9)
            tw, th = f.size(bubble)
            pad_b = 6
            bw, bh = tw + pad_b * 2 + 2, th + pad_b * 2
            bub_x = int(p['x']) + shake_dx - bw // 2
            bub_y = by - bh - 6
            pygame.draw.rect(screen, (255, 255, 255), (bub_x, bub_y, bw, bh))
            pygame.draw.rect(screen, (0, 0, 0), (bub_x, bub_y, bw, bh), 2)
            tx = bub_x + pad_b + 1
            ty = bub_y + pad_b
            txt = f.render(bubble, True, (0, 0, 0))
            screen.blit(txt, (tx, ty))
    elif player_sheet:
        frame = int(pygame.time.get_ticks() / 180) % 2
        spr = player_sheet.subsurface(frame * PLAYER_FW, 0, PLAYER_FW, PLAYER_FH)
        screen.blit(spr, (int(p['x'] - PLAYER_FW / 2) + shake_dx, int(p['y'] - PLAYER_FH / 2) + shake_dy))
    else:
        draw_pixel_ship_fallback(screen, p, shake_dx, shake_dy)

def draw_enemy(screen, e, shake_dx=0, shake_dy=0):
    if e.get('tier') == 1 and helicopter_sheet:
        frame = int(pygame.time.get_ticks() / 140) % 2
        x, y = int(e['x']), int(e['y'])
        spr = helicopter_sheet.subsurface(frame * HELI_FW, 0, HELI_FW, HELI_FH)
        screen.blit(spr, (x - HELI_FW // 2 + shake_dx, y - HELI_FH // 2 + shake_dy))
        bw = 32
        pygame.draw.rect(screen, (34, 34, 34), (x - bw // 2 + shake_dx, y + 22 + shake_dy, bw, 4))
        ratio = e['hp'] / e['maxHp']
        pygame.draw.rect(screen, (255, 204, 0), (x - bw // 2 + shake_dx, y + 22 + shake_dy, max(1, int(bw * ratio)), 4))
    elif e.get('tier') == 2:
        x, y = int(e['x']), int(e['y'])
        idx = e.get('spriteIdx', 0)
        spr = enemy_sprites[idx]
        if spr:
            scaled = pygame.transform.scale(spr, (e['w'], e['h']))
            screen.blit(scaled, (x - e['w'] // 2 + shake_dx, y - e['h'] // 2 + shake_dy))
        else:
            draw_pixel_enemy_fallback(screen, e, shake_dx, shake_dy)
        bw = e['w'] - 8
        ratio = e['hp'] / e['maxHp']
        pygame.draw.rect(screen, (34, 34, 34), (x - bw // 2 + shake_dx, y + e['h'] // 2 + 3 + shake_dy, bw, 4))
        hp_color = (0, 255, 102) if ratio > 0.6 else (255, 204, 0) if ratio > 0.3 else (255, 51, 0)
        pygame.draw.rect(screen, hp_color, (x - bw // 2 + shake_dx, y + e['h'] // 2 + 3 + shake_dy, max(1, int(bw * ratio)), 4))
    else:
        draw_pixel_enemy_fallback(screen, e, shake_dx, shake_dy)

def draw_pixel_ship_fallback(screen, p, shake_dx=0, shake_dy=0):
    x, y = int(p['x']) + shake_dx, int(p['y']) + shake_dy
    frame = int(pygame.time.get_ticks() / 90) % 3
    flames = [(255, 170, 0), (255, 102, 0), (255, 255, 0)]
    pygame.draw.rect(screen, flames[frame], (x - 22, y - 3, 10, 6))
    pygame.draw.rect(screen, WHITE if frame == 1 else (255, 204, 0), (x - 28, y - 1, 8, 2))
    pygame.draw.rect(screen, p['dark'], (x - 10, y - 14, 18, 6))
    pygame.draw.rect(screen, p['dark'], (x - 10, y + 8, 18, 6))
    pygame.draw.rect(screen, p['color'], (x - 8, y - 12, 14, 4))
    pygame.draw.rect(screen, p['color'], (x - 8, y + 8, 14, 4))
    pygame.draw.rect(screen, p['color'], (x - 14, y - 7, 36, 14))
    pygame.draw.rect(screen, p['color'], (x + 22, y - 5, 6, 10))
    pygame.draw.rect(screen, p['color'], (x + 28, y - 3, 6, 6))
    pygame.draw.rect(screen, p['color'], (x + 32, y - 1, 6, 2))
    pygame.draw.rect(screen, WHITE, (x + 2, y - 5, 12, 10))
    pygame.draw.rect(screen, (170, 255, 255), (x + 4, y - 3, 8, 6))
    pygame.draw.rect(screen, (0, 119, 153), (x + 6, y - 1, 4, 2))
    pygame.draw.rect(screen, p['dark'], (x - 14, y - 7, 36, 2))
    pygame.draw.rect(screen, p['dark'], (x - 14, y + 5, 36, 2))

def draw_pixel_enemy_fallback(screen, e, shake_dx=0, shake_dy=0):
    x, y = int(e['x']) + shake_dx, int(e['y']) + shake_dy
    hw, hh = int(e['w'] / 2), int(e['h'] / 2)
    pygame.draw.rect(screen, e['dark'], (x - hw, y - hh, e['w'], e['h']))
    pygame.draw.rect(screen, e['col'], (x - hw + 3, y - hh + 3, e['w'] - 6, e['h'] - 6))
    pygame.draw.rect(screen, e['dark'], (x - hw, y - 3, 6, 6))
    pygame.draw.rect(screen, WHITE, (x - 5, y - 5, 10, 10))
    pygame.draw.rect(screen, (255, 0, 0), (x - 3, y - 3, 6, 6))
    pygame.draw.rect(screen, (102, 0, 0), (x - 1, y - 1, 2, 2))
    if e['maxHp'] > 1:
        bw = e['w'] - 8
        ratio = e['hp'] / e['maxHp']
        pygame.draw.rect(screen, (34, 34, 34), (x - bw // 2, y + hh + 3, bw, 4))
        hp_color = (0, 255, 102) if ratio > 0.6 else (255, 204, 0) if ratio > 0.3 else (255, 51, 0)
        pygame.draw.rect(screen, hp_color, (x - bw // 2, y + hh + 3, max(1, int(bw * ratio)), 4))

def draw_powerup(screen, pu, shake_dx=0, shake_dy=0):
    x = int(pu['x']) + shake_dx
    y = int(pu['y']) + shake_dy + int(math.sin(pygame.time.get_ticks() * 0.006) * 3)
    info = POWERUP_TYPES.get(pu['type'], {})
    col = info.get('color', (255, 255, 255))
    pygame.draw.rect(screen, (255, 255, 255), (x - 9, y - 9, 18, 18))
    pygame.draw.rect(screen, col, (x - 7, y - 7, 14, 14))
    glow = int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 100 + 155)
    pygame.draw.rect(screen, (glow, glow, glow), (x - 4, y - 4, 8, 8))
