import pygame
import sys
import random
import math
import os
from config import *
import audio
import renderer
from game import start_game, game_loop, handle_key, is_game_running, is_paused, pause_game, resume_game, stop_game, get_state, get_font, set_screen, do_game_over, get_cinematic_pending, cinematic_done
from leaderboard import load_board, add_score, save_settings, load_settings, get_ctrl_scheme, set_ctrl_scheme, get_ctrl_p2, set_ctrl_p2
from cinematic import CrashCinematic

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

NATIVE_W = GAME_W
NATIVE_H = SCREEN_H

display_info = pygame.display.Info()
best_scale_w = max(1, display_info.current_w // NATIVE_W)
best_scale_h = max(1, display_info.current_h // NATIVE_H)
initial_scale = min(best_scale_w, best_scale_h, 3)

WIN_W = NATIVE_W * initial_scale
WIN_H = NATIVE_H * initial_scale
window = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
pygame.display.set_caption("STAR FORCE 8-BIT")
native = pygame.Surface((NATIVE_W, NATIVE_H))
_fullscreen = False
clock = pygame.time.Clock()
set_screen(native)
renderer.load_assets()
audio.load_volumes()

# ── Joystick ──
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    try:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
    except Exception:
        joystick = None

settings_dict = load_settings()
ctrl_scheme = settings_dict['p1']
ctrl_scheme_p2 = settings_dict['p2']

STATE = 'menu'
pending_mode = 1
p1_name = 'P1'
p2_name = 'P2'
menu_cursor = 0
name_input = ''
name_input2 = ''
input_active = 0
cinematic = None
loser_banner = None
loser_banner_timer = 0
game_over_state = None

def native_coords(x, y):
    w, h = window.get_size()
    return x * NATIVE_W // w, y * NATIVE_H // h

# ── Menu stars ──
menu_stars = [{'x': random.random() * NATIVE_W, 'y': random.random() * NATIVE_H,
               'spd': 10 + random.random() * 40, 'r': 1 + int(random.random() * 2),
               'a': 0.15 + random.random() * 0.6} for _ in range(60)]

def play_select():
    try:
        sr = 22050
        n = int(sr * 0.06)
        buf = bytearray(n * 2)
        for i in range(n):
            t_val = 0.12 if (i / sr * 880) % 1 < 0.5 else -0.12
            val = int(max(-32768, min(32767, t_val * 32767)))
            buf[i*2:(i+1)*2] = val.to_bytes(2, 'little', signed=True)
        s = pygame.mixer.Sound(buffer=bytes(buf))
        s.set_volume(audio.sfx_volume)
        s.play()
    except Exception:
        pass

def play_hover():
    try:
        sr = 22050
        n = int(sr * 0.03)
        buf = bytearray(n * 2)
        for i in range(n):
            t_val = 0.06 if (i / sr * 440) % 1 < 0.5 else -0.06
            val = int(max(-32768, min(32767, t_val * 32767)))
            buf[i*2:(i+1)*2] = val.to_bytes(2, 'little', signed=True)
        s = pygame.mixer.Sound(buffer=bytes(buf))
        s.set_volume(audio.sfx_volume * 0.5)
        s.play()
    except Exception:
        pass

def draw_text(surf, text, pos, size=20, color=(240, 160, 0), align='topleft'):
    font = get_font(size)
    for ox, oy in [(1, 0), (0, 1), (1, 1)]:
        sh = font.render(text, True, (0, 0, 0))
        sr = sh.get_rect()
        if align == 'center':
            sr.center = (pos[0] + ox, pos[1] + oy)
        elif align == 'right':
            sr.topright = (pos[0] + ox, pos[1] + oy)
        else:
            sr.topleft = (pos[0] + ox, pos[1] + oy)
        surf.blit(sh, sr)
    img = font.render(text, True, color)
    r = img.get_rect()
    if align == 'center':
        r.center = pos
    elif align == 'right':
        r.topright = pos
    else:
        r.topleft = pos
    surf.blit(img, r)

def draw_text_centered(surf, text, y, size=20, color=(240, 160, 0)):
    font = get_font(size)
    img = font.render(text, True, color)
    r = img.get_rect(center=(NATIVE_W // 2, y))
    for ox, oy in [(1, 0), (0, 1), (1, 1)]:
        sh = font.render(text, True, (0, 0, 0))
        sr = sh.get_rect(center=(NATIVE_W // 2 + ox, y + oy))
        surf.blit(sh, sr)
    surf.blit(img, r)

def draw_pixel_box(surf, rect, border_color=(122, 72, 0), inner_color=(0, 0, 0)):
    bx, by, bw, bh = rect
    pygame.draw.rect(surf, border_color, (bx - 4, by - 4, bw + 8, bh + 8))
    inner = (max(0, border_color[0] - 30), max(0, border_color[1] - 30), max(0, border_color[2] - 30))
    pygame.draw.rect(surf, inner, (bx - 3, by - 3, bw + 6, bh + 6))
    pygame.draw.rect(surf, inner_color, (bx - 2, by - 2, bw + 4, bh + 4))
    pygame.draw.rect(surf, inner_color, (bx, by, bw, bh))

def render_starfield(surf, stars, dt):
    for s in stars:
        s['x'] -= s['spd'] * dt
        if s['x'] < -4:
            s['x'] = NATIVE_W + 4
            s['y'] = random.random() * NATIVE_H
        a = int(s['a'] * 255)
        star = pygame.Surface((s['r'], s['r']), pygame.SRCALPHA)
        star.fill((255, 255, 255, a))
        surf.blit(star, (int(s['x']), int(s['y'])))

# ── Menu ──
_last_hover = -1
def render_menu(dt):
    global _last_hover
    native.fill(MENU_BG)
    render_starfield(native, menu_stars, dt)

    draw_text_centered(native, 'STAR FORCE', 50, 48, (240, 160, 0))
    draw_text_centered(native, '8-BIT', 92, 16, (204, 0, 255))

    board = load_board()
    bx, by = NATIVE_W // 2 - 170, 112
    draw_pixel_box(native, (bx, by, 340, 165), inner_color=(8, 0, 8))
    draw_text_centered(native, '\u2605 MEJORES 5 PUNTUACIONES \u2605', by + 16, 10, (240, 160, 0))
    if not board:
        draw_text_centered(native, '\u2014 SIN PUNTUACIONES \u2014', by + 80, 8, (51, 51, 51))
    else:
        medals = ['\u2605', '2', '3', '4', '5']
        for i, entry in enumerate(board):
            ry = by + 36 + i * 22
            mc = (255, 215, 0) if i == 0 else (85, 85, 85)
            draw_text(native, medals[i], (bx + 10, ry), 8, mc)
            draw_text(native, entry['name'], (bx + 38, ry), 8, (240, 160, 0))
            draw_text(native, str(entry['score']).zfill(5), (bx + 260, ry), 8, (0, 255, 255))

    items = ['1 JUGADOR', '2 JUGADORES', 'C\u00d3MO JUGAR', 'AJUSTES']
    iy = 302
    mx, my = pygame.mouse.get_pos()
    mx, my = native_coords(mx, my)
    hovered = -1
    for i, item in enumerate(items):
        bw2, bh2 = 290, 36
        bx2 = NATIVE_W // 2 - bw2 // 2
        r = pygame.Rect(bx2, iy + i * 42, bw2, bh2)
        is_hover = r.collidepoint(mx, my) or menu_cursor == i
        if is_hover:
            hovered = i
        if is_hover:
            bright = min(255, 240 + int(math.sin(pygame.time.get_ticks() * 0.004) * 15))
            pygame.draw.rect(native, (bright, 160, 0), (bx2, iy + i * 42, bw2, bh2))
            draw_text(native, '\u25b6', (bx2 + 10, iy + i * 42 + 11), 12, (0, 0, 0))
            draw_text_centered(native, item, iy + i * 42 + 20, 12, (0, 0, 0))
        else:
            draw_pixel_box(native, (bx2, iy + i * 42, bw2, bh2), inner_color=(0, 0, 0))
            draw_text_centered(native, item, iy + i * 42 + 20, 12, (240, 160, 0))
    if hovered != _last_hover and hovered >= 0:
        play_hover()
    _last_hover = hovered

_HOVER_CACHE = {}
def draw_interactive_text(surf, text, rect, size=12, color=(240, 160, 0), active=False):
    key = (text, rect.x, rect.y, rect.w, rect.h)
    if active:
        bright = min(255, 240 + int(math.sin(pygame.time.get_ticks() * 0.004) * 15))
        c = (bright, 160, 0)
        pygame.draw.rect(surf, c, rect)
        draw_text_centered(surf, text, rect.centery + size // 3, size, (0, 0, 0))
        return True
    else:
        draw_pixel_box(surf, (rect.x, rect.y, rect.w, rect.h), inner_color=(0, 0, 0))
        draw_text_centered(surf, text, rect.centery + size // 3, size, color)
        return False

def render_how_to_play():
    native.fill(MENU_BG)
    draw_text_centered(native, 'C\u00d3MO JUGAR', 40, 22, (240, 160, 0))
    lines = [
        ('1P: W A S D mover  |  BLOQ MAYUS disparar', (0, 255, 255)),
        ('2P: P1:\u2191\u2193\u2190\u2192+SHIFT  |  P2:WASD+CTRL', (255, 0, 255)),
        ('', (100, 100, 100)),
        ('Wave 1 \u2192 15 kills', (240, 160, 0)),
        ('Wave 2 \u2192 15 kills', (240, 160, 0)),
        ('Wave 3+ \u2192 boss incoming +1 vida', (240, 160, 0)),
        ('', (100, 100, 100)),
        ('S=100pts  M=200pts  B=350pts', (85, 85, 85)),
        ('', (100, 100, 100)),
        ('2P: el que muere primero ve su avion', (255, 102, 102)),
        ('estrellarse en las torres!', (255, 102, 102)),
        ('', (100, 100, 100)),
        ('\u2500\u2500\u2500  MANDO XBOX  \u2500\u2500\u2500', (240, 160, 0)),
        ('Stick/DPad mover  |  A disparar', (85, 85, 85)),
        ('Start = Pausa  |  B = Volver', (85, 85, 85)),
    ]
    y = 78
    for text, col in lines:
        if text:
            draw_text_centered(native, text, y, 8, col)
        y += 20
    draw_text_centered(native, '\u25c0 VOLVER', NATIVE_H - 40, 12, (240, 160, 0))

def render_name_entry():
    native.fill(MENU_BG)
    draw_text_centered(native, 'INGRESA TU NOMBRE', 50, 22, (240, 160, 0))
    draw_text_centered(native, '\u25c6 DATOS DEL JUGADOR \u25c6', 80, 8, (102, 102, 102))
    draw_text_centered(native, 'JUGADOR 1', 125, 10, (0, 255, 255))
    i1x, i1y = NATIVE_W // 2 - 110, 145
    bc = (240, 160, 0) if input_active == 0 else (122, 72, 0)
    draw_pixel_box(native, (i1x, i1y, 220, 36), border_color=bc, inner_color=(17, 17, 17))
    blink = '_' if (pygame.time.get_ticks() // 500) % 2 == 0 and input_active == 0 else ' '
    draw_text_centered(native, name_input + blink, 163, 12, (240, 160, 0))
    if pending_mode == 2:
        draw_text_centered(native, 'JUGADOR 2', 205, 10, (255, 0, 255))
        i2x, i2y = NATIVE_W // 2 - 110, 225
        bc2 = (240, 160, 0) if input_active == 1 else (122, 72, 0)
        draw_pixel_box(native, (i2x, i2y, 220, 36), border_color=bc2, inner_color=(17, 17, 17))
        blink2 = '_' if (pygame.time.get_ticks() // 500) % 2 == 0 and input_active == 1 else ' '
        draw_text_centered(native, name_input2 + blink2, 243, 12, (240, 160, 0))
    btn_y = 285 if pending_mode == 2 else 225
    bw_btn = 200
    bx_btn = NATIVE_W // 2 - bw_btn // 2
    draw_pixel_box(native, (bx_btn, btn_y, bw_btn, 36), border_color=(0, 255, 136), inner_color=(0, 0, 0))
    draw_text_centered(native, '\u25b6 INICIAR!', btn_y + 20, 10, (0, 255, 136))
    draw_pixel_box(native, (bx_btn, btn_y + 44, bw_btn, 36), inner_color=(0, 0, 0))
    draw_text_centered(native, '\u25c0 VOLVER', btn_y + 64, 10, (240, 160, 0))

settings_music_vol = int(audio.get_music_volume() * 100)
settings_sfx_vol = int(audio.get_sfx_volume() * 100)
settings_ctrl_p1 = get_ctrl_scheme()
settings_ctrl_p2 = get_ctrl_p2()
def render_settings():
    global settings_music_vol, settings_sfx_vol, settings_ctrl_p1, settings_ctrl_p2
    native.fill(MENU_BG)
    draw_text_centered(native, 'AJUSTES', 40, 22, (240, 160, 0))

    sl_w = 240
    sl_x = NATIVE_W // 2 - sl_w // 2

    draw_text_centered(native, '\U0001f3b5 MUSICA', 85, 10, (240, 160, 0))
    pygame.draw.rect(native, (34, 34, 34), (sl_x, 102, sl_w, 10))
    fill_w = int(sl_w * settings_music_vol / 100)
    pygame.draw.rect(native, (240, 160, 0), (sl_x, 102, fill_w, 10))
    draw_text_centered(native, str(settings_music_vol), 118, 10, (240, 160, 0))

    draw_text_centered(native, '\U0001f50a EFECTOS', 145, 10, (240, 160, 0))
    pygame.draw.rect(native, (34, 34, 34), (sl_x, 162, sl_w, 10))
    fill_w2 = int(sl_w * settings_sfx_vol / 100)
    pygame.draw.rect(native, (240, 160, 0), (sl_x, 162, fill_w2, 10))
    draw_text_centered(native, str(settings_sfx_vol), 178, 10, (240, 160, 0))

    ctrl_items = ['W A S D + BLOQ MAYUS', '\u2191 \u2193 \u2190 \u2192 + SHIFT']

    draw_text_centered(native, '\u2500 CONTROLES JUGADOR 1 \u2500', 218, 10, (0, 255, 255))
    for i, item in enumerate(ctrl_items):
        ciw, cih = 260, 32
        cix = NATIVE_W // 2 - ciw // 2
        ci_y = 238
        active = (settings_ctrl_p1 == 'wasd' and i == 0) or (settings_ctrl_p1 == 'arrows' and i == 1)
        if active:
            bright = min(255, 240 + int(math.sin(pygame.time.get_ticks() * 0.004) * 15))
            pygame.draw.rect(native, (bright, 160, 0), (cix, ci_y + i * 38, ciw, cih))
            draw_text_centered(native, item, ci_y + i * 38 + 18, 9, (0, 0, 0))
        else:
            draw_pixel_box(native, (cix, ci_y + i * 38, ciw, cih), inner_color=(0, 0, 0))
            draw_text_centered(native, item, ci_y + i * 38 + 18, 9, (240, 160, 0))

    draw_text_centered(native, '\u2500 CONTROLES JUGADOR 2 \u2500', 324, 10, (255, 0, 255))
    for i, item in enumerate(ctrl_items):
        ciw, cih = 260, 32
        cix = NATIVE_W // 2 - ciw // 2
        ci_y = 344
        active = (settings_ctrl_p2 == 'wasd' and i == 0) or (settings_ctrl_p2 == 'arrows' and i == 1)
        if active:
            bright = min(255, 240 + int(math.sin(pygame.time.get_ticks() * 0.004) * 15))
            pygame.draw.rect(native, (bright, 160, 0), (cix, ci_y + i * 38, ciw, cih))
            draw_text_centered(native, item, ci_y + i * 38 + 18, 9, (0, 0, 0))
        else:
            draw_pixel_box(native, (cix, ci_y + i * 38, ciw, cih), inner_color=(0, 0, 0))
            draw_text_centered(native, item, ci_y + i * 38 + 18, 9, (240, 160, 0))

    draw_text_centered(native, '\u25c0 VOLVER', NATIVE_H - 40, 12, (240, 160, 0))

def render_pause():
    overlay = pygame.Surface((NATIVE_W, NATIVE_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 217))
    native.blit(overlay, (0, 0))
    blink = (pygame.time.get_ticks() // 800) % 2 == 0
    if blink:
        draw_text_centered(native, '\u23f8 PAUSA', NATIVE_H // 2 - 50, 36, (240, 160, 0))
    draw_text_centered(native, 'PRESIONA ESC PARA CONTINUAR', NATIVE_H // 2 - 10, 8, (85, 85, 85))
    bw2 = 200
    bx2 = NATIVE_W // 2 - bw2 // 2
    draw_pixel_box(native, (bx2, NATIVE_H // 2 + 25, bw2, 36), border_color=(0, 255, 136), inner_color=(0, 0, 0))
    draw_text_centered(native, '\u25b6 CONTINUAR', NATIVE_H // 2 + 43, 8, (0, 255, 136))
    draw_pixel_box(native, (bx2, NATIVE_H // 2 + 69, bw2, 36), inner_color=(0, 0, 0))
    draw_text_centered(native, '\u2302 MENU', NATIVE_H // 2 + 87, 8, (240, 160, 0))

def render_game_over():
    s = game_over_state or get_state()
    if not s:
        return
    overlay = pygame.Surface((NATIVE_W, NATIVE_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 235))
    native.blit(overlay, (0, 0))
    draw_text_centered(native, 'FIN DEL JUEGO', NATIVE_H // 2 - 85, 30, (255, 51, 51))
    sub_t = 'MISI\u00d3N FALLIDA' if s['currentMode'] == 1 else '\u2014 RESULTADO FINAL \u2014'
    draw_text_centered(native, sub_t, NATIVE_H // 2 - 55, 8, (102, 102, 102))
    draw_text_centered(native, s['p1Name'] + ': ' + str(s['score1']).zfill(5), NATIVE_H // 2 - 30, 10, (0, 255, 255))
    if s['currentMode'] == 1:
        draw_text_centered(native, 'KILLS ' + str(s['killCount']), NATIVE_H // 2 - 10, 8, (85, 85, 85))
    if s['currentMode'] == 2:
        draw_text_centered(native, s['p2Name'] + ': ' + str(s['score2']).zfill(5), NATIVE_H // 2 - 10, 10, (255, 0, 255))
    if s['currentMode'] == 1:
        wt = '\U0001f3c6 ' + s['p1Name'] + ' PUNTUACI\u00d3N: ' + str(s['score1']).zfill(5)
    else:
        if s['score1'] > s['score2']:
            wt = '\u2605 \u00a1' + s['p1Name'] + ' GANA! \u2605'
        elif s['score2'] > s['score1']:
            wt = '\u2605 \u00a1' + s['p2Name'] + ' GANA! \u2605'
        else:
            wt = '\u25c6 EMPATE \u25c6'
    draw_text_centered(native, wt, NATIVE_H // 2 + 15, 10, (240, 160, 0))
    bw2 = 200
    bx2 = NATIVE_W // 2 - bw2 // 2
    draw_pixel_box(native, (bx2, NATIVE_H // 2 + 50, bw2, 36), border_color=(0, 255, 136), inner_color=(0, 0, 0))
    draw_text_centered(native, '\u25b6 REINTENTAR', NATIVE_H // 2 + 68, 8, (0, 255, 136))
    draw_pixel_box(native, (bx2, NATIVE_H // 2 + 94, bw2, 36), inner_color=(0, 0, 0))
    draw_text_centered(native, '\u2302 MENU', NATIVE_H // 2 + 112, 8, (240, 160, 0))


def start_game_now():
    global p1_name, p2_name, STATE, cinematic, game_over_state
    p1 = (name_input.strip() or 'P1').upper()[:8]
    p2 = (name_input2.strip() or 'P2').upper()[:8]
    p1_name = p1
    p2_name = p2
    easter = 'CHESTER' in (p1, p2)
    start_game(pending_mode, p1, p2, ctrl_scheme, ctrl_scheme_p2, easter)
    STATE = 'playing'
    cinematic = None
    game_over_state = None


def check_mouse_click(mx, my):
    global STATE, menu_cursor, pending_mode, input_active, name_input, name_input2, p1_name, p2_name, ctrl_scheme, ctrl_scheme_p2
    global settings_music_vol, settings_sfx_vol, cinematic, game_over_state, loser_banner, loser_banner_timer
    if STATE == 'menu':
        for i in range(4):
            r = pygame.Rect(NATIVE_W // 2 - 145, 302 + i * 42, 290, 36)
            if r.collidepoint(mx, my):
                play_select()
                menu_cursor = i
                if i == 0:
                    pending_mode = 1; STATE = 'name_entry'; name_input = ''; name_input2 = ''; input_active = 0
                elif i == 1:
                    pending_mode = 2; STATE = 'name_entry'; name_input = ''; name_input2 = ''; input_active = 0
                elif i == 2:
                    STATE = 'how_to_play'
                elif i == 3:
                    STATE = 'settings'
                return
    elif STATE == 'how_to_play':
        if NATIVE_H - 55 <= my <= NATIVE_H - 25:
            play_select(); STATE = 'menu'
    elif STATE == 'settings':
        sl_w, sl_x = 240, NATIVE_W // 2 - 120
        if pygame.Rect(sl_x, 95, sl_w, 30).collidepoint(mx, my):
            val = int((mx - sl_x) / sl_w * 100); val = max(0, min(100, val))
            settings_music_vol = val; audio.set_music_volume(val / 100)
        if pygame.Rect(sl_x, 155, sl_w, 30).collidepoint(mx, my):
            val = int((mx - sl_x) / sl_w * 100); val = max(0, min(100, val))
            settings_sfx_vol = val; audio.set_sfx_volume(val / 100)
        # P1 controls
        for i in range(2):
            if pygame.Rect(NATIVE_W // 2 - 130, 238 + i * 38, 260, 32).collidepoint(mx, my):
                settings_ctrl_p1 = 'wasd' if i == 0 else 'arrows'
                set_ctrl_scheme(settings_ctrl_p1); save_settings(); ctrl_scheme = settings_ctrl_p1
        # P2 controls
        for i in range(2):
            if pygame.Rect(NATIVE_W // 2 - 130, 344 + i * 38, 260, 32).collidepoint(mx, my):
                settings_ctrl_p2 = 'wasd' if i == 0 else 'arrows'
                set_ctrl_p2(settings_ctrl_p2); save_settings(); ctrl_scheme_p2 = settings_ctrl_p2
        if NATIVE_H - 55 <= my <= NATIVE_H - 25:
            play_select(); STATE = 'menu'
    elif STATE == 'name_entry':
        if pygame.Rect(NATIVE_W // 2 - 110, 145, 220, 36).collidepoint(mx, my):
            input_active = 0
        if pending_mode == 2 and pygame.Rect(NATIVE_W // 2 - 110, 225, 220, 36).collidepoint(mx, my):
            input_active = 1
        btn_y = 285 if pending_mode == 2 else 225
        if pygame.Rect(NATIVE_W // 2 - 100, btn_y, 200, 36).collidepoint(mx, my):
            play_select(); start_game_now()
        if pygame.Rect(NATIVE_W // 2 - 100, btn_y + 44, 200, 36).collidepoint(mx, my):
            play_select(); STATE = 'menu'
    elif STATE == 'paused':
        if pygame.Rect(NATIVE_W // 2 - 100, NATIVE_H // 2 + 25, 200, 36).collidepoint(mx, my):
            resume_game(); STATE = 'playing'
        if pygame.Rect(NATIVE_W // 2 - 100, NATIVE_H // 2 + 69, 200, 36).collidepoint(mx, my):
            play_select(); stop_game(); audio.play_menu_music(); STATE = 'menu'; game_over_state = None
    elif STATE == 'game_over':
        if pygame.Rect(NATIVE_W // 2 - 100, NATIVE_H // 2 + 50, 200, 36).collidepoint(mx, my):
            play_select(); start_game_now()
        if pygame.Rect(NATIVE_W // 2 - 100, NATIVE_H // 2 + 94, 200, 36).collidepoint(mx, my):
            play_select(); audio.play_menu_music(); STATE = 'menu'; game_over_state = None


# ── Controller state ──
_btn_prev = {}
_btn_cooldown = {}

def _btn_edge(btn, val):
    key = (id(joystick), btn)
    prev = _btn_prev.get(key, False)
    _btn_prev[key] = val
    return val and not prev

def _btn_wait(btn, ms=200):
    key = (id(joystick), btn)
    now = pygame.time.get_ticks()
    last = _btn_cooldown.get(key, 0)
    if now - last < ms:
        return False
    _btn_cooldown[key] = now
    return True

_axis_u_prev = False
_axis_d_prev = False

def handle_controller():
    global _btn_b_held, STATE, menu_cursor, pending_mode, name_input, name_input2, input_active, ctrl_scheme
    global settings_music_vol, settings_sfx_vol, game_over_state, _axis_u_prev, _axis_d_prev
    if not joystick:
        return
    try:
        pygame.event.pump()
        axis_x = joystick.get_axis(0)
        axis_y = joystick.get_axis(1)
        hat = joystick.get_hat(0)

        a_btn = joystick.get_button(0)
        b_btn = joystick.get_button(1)
        start_btn = joystick.get_button(7)

        dpad_l = hat[0] < -0.5 or axis_x < -0.5
        dpad_r = hat[0] > 0.5 or axis_x > 0.5
        dpad_u = hat[1] > 0.5 or axis_y < -0.5
        dpad_d = hat[1] < -0.5 or axis_y > 0.5

        # In-game controls — controller only controls P1
        if STATE == 'playing':
            if _btn_edge(7, start_btn):
                handle_key(pygame.K_ESCAPE, True)
                handle_key(pygame.K_ESCAPE, False)
            if ctrl_scheme == 'wasd':
                handle_key(pygame.K_w, dpad_u)
                handle_key(pygame.K_s, dpad_d)
                handle_key(pygame.K_a, dpad_l)
                handle_key(pygame.K_d, dpad_r)
                handle_key(pygame.K_CAPSLOCK, a_btn)
            else:
                handle_key(pygame.K_UP, dpad_u)
                handle_key(pygame.K_DOWN, dpad_d)
                handle_key(pygame.K_LEFT, dpad_l)
                handle_key(pygame.K_RIGHT, dpad_r)
                handle_key(pygame.K_LSHIFT, a_btn)

        elif STATE == 'paused':
            if _btn_edge(7, start_btn) or _btn_edge(0, a_btn):
                resume_game()
                STATE = 'playing'

        if STATE in ('menu', 'how_to_play', 'settings'):
            if (dpad_u or axis_y < -0.5) and not _axis_u_prev:
                if menu_cursor > 0:
                    menu_cursor -= 1
                    play_hover()
            if (dpad_d or axis_y > 0.5) and not _axis_d_prev:
                if STATE == 'menu' and menu_cursor < 3:
                    menu_cursor += 1
                    play_hover()
            _axis_u_prev = dpad_u or axis_y < -0.5
            _axis_d_prev = dpad_d or axis_y > 0.5

            if _btn_edge(0, a_btn):
                play_select()
                if STATE == 'menu':
                    if menu_cursor == 0:
                        pending_mode = 1; STATE = 'name_entry'; name_input = ''; name_input2 = ''; input_active = 0
                    elif menu_cursor == 1:
                        pending_mode = 2; STATE = 'name_entry'; name_input = ''; name_input2 = ''; input_active = 0
                    elif menu_cursor == 2:
                        STATE = 'how_to_play'
                    elif menu_cursor == 3:
                        STATE = 'settings'
                elif STATE == 'how_to_play':
                    STATE = 'menu'
                elif STATE == 'settings':
                    STATE = 'menu'

            if _btn_edge(1, b_btn):
                if STATE in ('how_to_play', 'settings'):
                    play_select(); STATE = 'menu'

        elif STATE == 'game_over':
            if _btn_edge(0, a_btn):
                play_select(); start_game_now()
            if _btn_edge(1, b_btn):
                play_select(); audio.play_menu_music(); STATE = 'menu'; game_over_state = None
            if _btn_edge(7, start_btn):
                play_select(); start_game_now()
    except Exception:
        pass


running = True
audio.play_menu_music()

while running:
    dt = clock.tick(60) / 1000.0

    handle_controller()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = native_coords(event.pos[0], event.pos[1])
            check_mouse_click(mx, my)

        if event.type == pygame.KEYDOWN:
            if STATE == 'menu':
                if event.key == pygame.K_UP:
                    menu_cursor = (menu_cursor - 1) % 4; play_hover()
                elif event.key == pygame.K_DOWN:
                    menu_cursor = (menu_cursor + 1) % 4; play_hover()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    play_select()
                    if menu_cursor == 0:
                        pending_mode = 1; STATE = 'name_entry'; name_input = ''; name_input2 = ''; input_active = 0
                    elif menu_cursor == 1:
                        pending_mode = 2; STATE = 'name_entry'; name_input = ''; name_input2 = ''; input_active = 0
                    elif menu_cursor == 2:
                        STATE = 'how_to_play'
                    elif menu_cursor == 3:
                        STATE = 'settings'

            elif STATE == 'how_to_play':
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    play_select(); STATE = 'menu'

            elif STATE == 'settings':
                if event.key == pygame.K_ESCAPE:
                    play_select(); STATE = 'menu'

            elif STATE == 'name_entry':
                if event.key == pygame.K_TAB and pending_mode == 2:
                    input_active = 1 - input_active
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    play_select(); start_game_now()
                elif event.key == pygame.K_ESCAPE:
                    play_select(); STATE = 'menu'
                elif event.key == pygame.K_BACKSPACE:
                    if input_active == 0: name_input = name_input[:-1]
                    else: name_input2 = name_input2[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        ch = event.unicode.upper()
                        if input_active == 0 and len(name_input) < 8:
                            name_input += ch
                        elif input_active == 1 and len(name_input2) < 8:
                            name_input2 += ch

            elif STATE == 'playing':
                if event.key == pygame.K_ESCAPE:
                    handle_key(pygame.K_ESCAPE, True)
                    if is_paused():
                        STATE = 'paused'
                else:
                    handle_key(event.key, True)

            elif STATE == 'paused':
                if event.key == pygame.K_ESCAPE:
                    resume_game(); STATE = 'playing'

            elif STATE == 'game_over':
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    play_select(); start_game_now()
                elif event.key == pygame.K_ESCAPE:
                    play_select(); audio.play_menu_music(); STATE = 'menu'; game_over_state = None

            if event.key == pygame.K_F11:
                _fullscreen = not _fullscreen
                if _fullscreen:
                    win_w = display_info.current_w
                    win_h = display_info.current_h
                    window = pygame.display.set_mode((win_w, win_h), pygame.FULLSCREEN)
                else:
                    window = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)

        if event.type == pygame.KEYUP:
            if STATE in ('playing', 'paused'):
                handle_key(event.key, False)

        if event.type == pygame.VIDEORESIZE and not _fullscreen:
            WIN_W, WIN_H = event.w, event.h
            window = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)

    # ═══ RENDER ═══
    if STATE == 'menu':
        render_menu(dt)
    elif STATE == 'how_to_play':
        render_how_to_play()
    elif STATE == 'name_entry':
        render_name_entry()
    elif STATE == 'settings':
        render_settings()
    elif STATE == 'playing':
        s = get_state()
        if cinematic:
            cinematic.update(dt)
            if cinematic.done:
                cinematic = None
                cinematic_done()
        elif get_cinematic_pending() and s:
            p = get_cinematic_pending()
            cinematic = CrashCinematic(native, p['color'], p['name'], s['GAME_H'], lambda: None)
            cinematic_done()
        else:
            if s:
                if s['currentMode'] == 2 and s.get('loserShown') and not loser_banner:
                    dead_p = next((p_ for p_ in s['players'] if p_['dead']), None)
                    if dead_p:
                        loser_banner = dead_p
                        loser_banner_timer = 3.5
                if s.get('gameOver'):
                    STATE = 'game_over'
                    do_game_over()
                    game_over_state = s
                    add_score(s['p1Name'], s['score1'])
                    if s['currentMode'] == 2:
                        add_score(s['p2Name'], s['score2'])
                else:
                    game_loop()

        if loser_banner:
            if loser_banner_timer > 0:
                loser_banner_timer -= dt
                if 'loser_title' not in loser_banner:
                    loser_banner['loser_title'] = random.choice(LOSER_TITLES)
                title = loser_banner['loser_title']
                draw_text_centered(native, '\u2620 ' + title + ' \u2620', NATIVE_H // 3 - 10, 12, (255, 51, 51))
                draw_text_centered(native, loser_banner['name'] + ' HA SIDO ELIMINADO', NATIVE_H // 3 + 15, 8, (255, 170, 0))
                s2 = get_state()
                if s2:
                    living = [p_ for p_ in s2['players'] if not p_['dead']]
                    if living:
                        draw_text_centered(native, '\u00a1' + living[0]['name'] + ' sigue luchando!', NATIVE_H // 3 + 35, 7, (136, 136, 136))
            if loser_banner_timer <= 0:
                loser_banner = None

    elif STATE == 'paused':
        if is_game_running():
            game_loop()
        render_pause()
    elif STATE == 'game_over':
        render_game_over()

    # Scale and present
    cur_w, cur_h = window.get_size()
    scaled = pygame.transform.scale(native, (cur_w, cur_h))
    window.blit(scaled, (0, 0))
    pygame.display.flip()

pygame.quit()
sys.exit()
