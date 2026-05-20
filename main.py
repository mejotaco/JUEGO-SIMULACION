import pygame
import sys
import random
import math
import os
from config import *
import audio
import renderer
from game import start_game, game_loop, handle_key, is_game_running, is_paused, pause_game, resume_game, stop_game, get_state, get_font, set_screen, do_game_over, get_cinematic_pending, cinematic_done
from leaderboard import load_board, add_score, save_settings, load_settings, get_ctrl_scheme, set_ctrl_scheme
from cinematic import CrashCinematic

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

SCREEN = pygame.display.set_mode((GAME_W, SCREEN_H))
pygame.display.set_caption("STAR FORCE 8-BIT")
clock = pygame.time.Clock()
set_screen(SCREEN)
renderer.load_assets()
audio.load_volumes()

ctrl_scheme = load_settings()

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

SEL = pygame.USEREVENT + 1

def play_select():
    try:
        sr = 22050
        n = int(sr * 0.08)
        buf = bytearray(n * 2)
        for i in range(n):
            t_val = 0.15 if (i / sr * 660) % 1 < 0.5 else -0.15
            val = int(max(-32768, min(32767, t_val * 32767)))
            buf[i*2:(i+1)*2] = val.to_bytes(2, 'little', signed=True)
        s = pygame.mixer.Sound(buffer=bytes(buf))
        s.set_volume(audio.sfx_volume)
        s.play()
    except Exception:
        pass

def draw_text(surf, text, pos, size=20, color=(240, 160, 0), align='topleft'):
    img = get_font(size).render(text, True, color)
    r = img.get_rect()
    if align == 'center':
        r.center = pos
    elif align == 'right':
        r.topright = pos
    else:
        r.topleft = pos
    surf.blit(img, r)

def draw_text_centered(surf, text, y, size=20, color=(240, 160, 0)):
    img = get_font(size).render(text, True, color)
    r = img.get_rect(center=(GAME_W // 2, y))
    surf.blit(img, r)

def draw_pixel_box(surf, rect, border_color=(122, 72, 0), inner_color=(0, 0, 0)):
    bx, by, bw, bh = rect
    pygame.draw.rect(surf, border_color, (bx - 4, by - 4, bw + 8, bh + 8))
    pygame.draw.rect(surf, border_color, (bx - 3, by - 3, bw + 6, bh + 6))
    pygame.draw.rect(surf, inner_color, (bx - 2, by - 2, bw + 4, bh + 4))
    pygame.draw.rect(surf, inner_color, (bx, by, bw, bh))

def draw_text_with_shadow(surf, text, y, size=48, color=(240, 160, 0)):
    font = get_font(size)
    for ox, oy in [(3, 0), (0, 3), (3, 3)]:
        sh = font.render(text, True, (122, 72, 0))
        r = sh.get_rect(center=(GAME_W // 2 + ox, y + oy))
        surf.blit(sh, r)
    hl = font.render(text, True, (255, 208, 96))
    r = hl.get_rect(center=(GAME_W // 2 - 1, y - 1))
    surf.blit(hl, r)
    img = font.render(text, True, color)
    r = img.get_rect(center=(GAME_W // 2, y))
    surf.blit(img, r)

# ── Menu ──
def render_menu():
    SCREEN.fill(MENU_BG)
    txt1 = get_font(48).render('STAR FORCE', True, (240, 160, 0))
    r1 = txt1.get_rect(center=(GAME_W // 2, 55))
    for ox, oy in [(3, 0), (0, 3), (3, 3)]:
        sh = get_font(48).render('STAR FORCE', True, (122, 72, 0))
        sr = sh.get_rect(center=(GAME_W // 2 + ox, 55 + oy))
        SCREEN.blit(sh, sr)
    hl = get_font(48).render('STAR FORCE', True, (255, 208, 96))
    hr = hl.get_rect(center=(GAME_W // 2 - 1, 54))
    SCREEN.blit(hl, hr)
    SCREEN.blit(txt1, r1)
    draw_text_centered(SCREEN, '8-BIT', 95, 16, (204, 0, 255))

    board = load_board()
    bx, by = GAME_W // 2 - 170, 115
    draw_pixel_box(SCREEN, (bx, by, 340, 165), inner_color=(8, 0, 8))
    draw_text_centered(SCREEN, '\u2605 MEJORES 5 PUNTUACIONES \u2605', by + 16, 10, (240, 160, 0))
    if not board:
        draw_text_centered(SCREEN, '\u2014 SIN PUNTUACIONES \u2014', by + 80, 8, (51, 51, 51))
    else:
        medals = ['\u2605', '2', '3', '4', '5']
        for i, entry in enumerate(board):
            ry = by + 38 + i * 22
            mc = (255, 215, 0) if i == 0 else (85, 85, 85)
            draw_text(SCREEN, medals[i], (bx + 10, ry), 8, mc)
            draw_text(SCREEN, entry['name'], (bx + 40, ry), 8, (240, 160, 0))
            draw_text(SCREEN, str(entry['score']).zfill(5), (bx + 260, ry), 8, (0, 255, 255))

    items = ['1 JUGADOR', '2 JUGADORES', 'C\u00d3MO JUGAR', 'AJUSTES']
    iy = 305
    for i, item in enumerate(items):
        bw2, bh2 = 290, 36
        bx2 = GAME_W // 2 - bw2 // 2
        if menu_cursor == i:
            pygame.draw.rect(SCREEN, (240, 160, 0), (bx2, iy + i * 42, bw2, bh2))
            draw_text(SCREEN, '\u25b6', (bx2 + 10, iy + i * 42 + 11), 12, (0, 0, 0))
            draw_text_centered(SCREEN, item, iy + i * 42 + 20, 12, (0, 0, 0))
        else:
            draw_pixel_box(SCREEN, (bx2, iy + i * 42, bw2, bh2), inner_color=(0, 0, 0))
            draw_text_centered(SCREEN, item, iy + i * 42 + 20, 12, (240, 160, 0))

# ── How to play ──
def render_how_to_play():
    SCREEN.fill(MENU_BG)
    draw_text_centered(SCREEN, 'C\u00d3MO JUGAR', 40, 22, (240, 160, 0))
    lines = [
        ('1P: W A S D mover  |  BLOQ MAYUS disparar', (0, 255, 255)),
        ('2P: P1:\u2191\u2193\u2190\u2192+SHIFT  |  P2:WASD+CTRL', (255, 0, 255)),
        ('', (100, 100, 100)),
        ('Wave 1 \u2192 15 kills', (240, 160, 0)),
        ('Wave 2 \u2192 15 kills', (240, 160, 0)),
        ('Wave 3 \u2192 boss incoming +1 vida', (240, 160, 0)),
        ('', (100, 100, 100)),
        ('S=100pts  M=200pts  B=350pts', (85, 85, 85)),
        ('', (100, 100, 100)),
        ('2P: el que muere primero ve su avion', (255, 102, 102)),
        ('estrellarse en las torres!', (255, 102, 102)),
    ]
    y = 80
    for text, col in lines:
        if text:
            draw_text_centered(SCREEN, text, y, 8, col)
        y += 22
    draw_text_centered(SCREEN, '\u25c0 VOLVER', SCREEN_H - 45, 12, (240, 160, 0))

# ── Name entry ──
def render_name_entry():
    SCREEN.fill(MENU_BG)
    draw_text_centered(SCREEN, 'INGRESA TU NOMBRE', 50, 22, (240, 160, 0))
    draw_text_centered(SCREEN, '\u25c6 DATOS DEL JUGADOR \u25c6', 80, 8, (102, 102, 102))
    draw_text_centered(SCREEN, 'JUGADOR 1', 125, 10, (0, 255, 255))
    i1x, i1y = GAME_W // 2 - 110, 145
    bc = (240, 160, 0) if input_active == 0 else (122, 72, 0)
    draw_pixel_box(SCREEN, (i1x, i1y, 220, 36), border_color=bc, inner_color=(17, 17, 17))
    blink = '_' if (pygame.time.get_ticks() // 500) % 2 == 0 and input_active == 0 else ' '
    draw_text_centered(SCREEN, name_input + blink, 163, 12, (240, 160, 0))
    if pending_mode == 2:
        draw_text_centered(SCREEN, 'JUGADOR 2', 205, 10, (255, 0, 255))
        i2x, i2y = GAME_W // 2 - 110, 225
        bc2 = (240, 160, 0) if input_active == 1 else (122, 72, 0)
        draw_pixel_box(SCREEN, (i2x, i2y, 220, 36), border_color=bc2, inner_color=(17, 17, 17))
        blink2 = '_' if (pygame.time.get_ticks() // 500) % 2 == 0 and input_active == 1 else ' '
        draw_text_centered(SCREEN, name_input2 + blink2, 243, 12, (240, 160, 0))
    btn_y = 285 if pending_mode == 2 else 225
    bw_btn = 200
    bx_btn = GAME_W // 2 - bw_btn // 2
    draw_pixel_box(SCREEN, (bx_btn, btn_y, bw_btn, 36), border_color=(0, 255, 136), inner_color=(0, 0, 0))
    draw_text_centered(SCREEN, '\u25b6 INICIAR!', btn_y + 20, 10, (0, 255, 136))
    draw_pixel_box(SCREEN, (bx_btn, btn_y + 44, bw_btn, 36), inner_color=(0, 0, 0))
    draw_text_centered(SCREEN, '\u25c0 VOLVER', btn_y + 64, 10, (240, 160, 0))

# ── Settings ──
settings_music_vol = int(audio.get_music_volume() * 100)
settings_sfx_vol = int(audio.get_sfx_volume() * 100)
settings_ctrl = load_settings()

def render_settings():
    global settings_music_vol, settings_sfx_vol, settings_ctrl
    SCREEN.fill(MENU_BG)
    draw_text_centered(SCREEN, 'AJUSTES', 40, 22, (240, 160, 0))

    draw_text_centered(SCREEN, '\U0001f3b5 MUSICA', 90, 10, (240, 160, 0))
    sl_w = 240
    sl_x = GAME_W // 2 - sl_w // 2
    pygame.draw.rect(SCREEN, (34, 34, 34), (sl_x, 105, sl_w, 8))
    fill_w = int(sl_w * settings_music_vol / 100)
    pygame.draw.rect(SCREEN, (240, 160, 0), (sl_x, 105, fill_w, 8))
    draw_text_centered(SCREEN, str(settings_music_vol), 120, 10, (240, 160, 0))

    draw_text_centered(SCREEN, '\U0001f50a EFECTOS', 150, 10, (240, 160, 0))
    pygame.draw.rect(SCREEN, (34, 34, 34), (sl_x, 165, sl_w, 8))
    fill_w2 = int(sl_w * settings_sfx_vol / 100)
    pygame.draw.rect(SCREEN, (240, 160, 0), (sl_x, 165, fill_w2, 8))
    draw_text_centered(SCREEN, str(settings_sfx_vol), 180, 10, (240, 160, 0))

    draw_text_centered(SCREEN, '\u2500 CONTROLES 1 JUGADOR \u2500', 220, 10, (240, 160, 0))

    ctrl_items = ['W A S D + BLOQ MAYUS', '\u2191 \u2193 \u2190 \u2192 + SHIFT']
    ci_y = 245
    for i, item in enumerate(ctrl_items):
        ciw, cih = 280, 36
        cix = GAME_W // 2 - ciw // 2
        active = (settings_ctrl == 'wasd' and i == 0) or (settings_ctrl == 'arrows' and i == 1)
        if active:
            pygame.draw.rect(SCREEN, (240, 160, 0), (cix, ci_y + i * 42, ciw, cih))
            draw_text_centered(SCREEN, item, ci_y + i * 42 + 20, 10, (0, 0, 0))
        else:
            draw_pixel_box(SCREEN, (cix, ci_y + i * 42, ciw, cih), inner_color=(0, 0, 0))
            draw_text_centered(SCREEN, item, ci_y + i * 42 + 20, 10, (240, 160, 0))

    draw_text_centered(SCREEN, '\u25c0 VOLVER', SCREEN_H - 45, 12, (240, 160, 0))

# ── Pause ──
def render_pause():
    overlay = pygame.Surface((GAME_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 217))
    SCREEN.blit(overlay, (0, 0))
    blink = (pygame.time.get_ticks() // 800) % 2 == 0
    if blink:
        draw_text_centered(SCREEN, '\u23f8 PAUSA', SCREEN_H // 2 - 50, 36, (240, 160, 0))
    draw_text_centered(SCREEN, 'PRESIONA ESC PARA CONTINUAR', SCREEN_H // 2 - 10, 8, (85, 85, 85))
    bw2 = 200
    bx2 = GAME_W // 2 - bw2 // 2
    draw_pixel_box(SCREEN, (bx2, SCREEN_H // 2 + 25, bw2, 36), border_color=(0, 255, 136), inner_color=(0, 0, 0))
    draw_text_centered(SCREEN, '\u25b6 CONTINUAR', SCREEN_H // 2 + 43, 8, (0, 255, 136))
    draw_pixel_box(SCREEN, (bx2, SCREEN_H // 2 + 69, bw2, 36), inner_color=(0, 0, 0))
    draw_text_centered(SCREEN, '\u2302 MENU', SCREEN_H // 2 + 87, 8, (240, 160, 0))

# ── Game Over ──
def render_game_over():
    s = get_state()
    if not s:
        return
    overlay = pygame.Surface((GAME_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 235))
    SCREEN.blit(overlay, (0, 0))
    draw_text_centered(SCREEN, 'FIN DEL JUEGO', SCREEN_H // 2 - 85, 30, (255, 51, 51))
    sub_t = 'MISI\u00d3N FALLIDA' if s['currentMode'] == 1 else '\u2014 RESULTADO FINAL \u2014'
    draw_text_centered(SCREEN, sub_t, SCREEN_H // 2 - 55, 8, (102, 102, 102))
    draw_text_centered(SCREEN, s['p1Name'] + ': ' + str(s['score1']).zfill(5), SCREEN_H // 2 - 30, 10, (0, 255, 255))
    if s['currentMode'] == 1:
        kt = 'KILLS ' + str(s['killCount'])
        draw_text_centered(SCREEN, kt, SCREEN_H // 2 - 10, 8, (85, 85, 85))
    if s['currentMode'] == 2:
        draw_text_centered(SCREEN, s['p2Name'] + ': ' + str(s['score2']).zfill(5), SCREEN_H // 2 - 10, 10, (255, 0, 255))
    if s['currentMode'] == 1:
        wt = '\U0001f3c6 ' + s['p1Name'] + ' PUNTUACI\u00d3N: ' + str(s['score1']).zfill(5)
    else:
        if s['score1'] > s['score2']:
            wt = '\u2605 \u00a1' + s['p1Name'] + ' GANA! \u2605'
        elif s['score2'] > s['score1']:
            wt = '\u2605 \u00a1' + s['p2Name'] + ' GANA! \u2605'
        else:
            wt = '\u25c6 EMPATE \u25c6'
    draw_text_centered(SCREEN, wt, SCREEN_H // 2 + 15, 10, (240, 160, 0))
    bw2 = 200
    bx2 = GAME_W // 2 - bw2 // 2
    draw_pixel_box(SCREEN, (bx2, SCREEN_H // 2 + 50, bw2, 36), border_color=(0, 255, 136), inner_color=(0, 0, 0))
    draw_text_centered(SCREEN, '\u25b6 REINTENTAR', SCREEN_H // 2 + 68, 8, (0, 255, 136))
    draw_pixel_box(SCREEN, (bx2, SCREEN_H // 2 + 94, bw2, 36), inner_color=(0, 0, 0))
    draw_text_centered(SCREEN, '\u2302 MENU', SCREEN_H // 2 + 112, 8, (240, 160, 0))

def start_game_now():
    global p1_name, p2_name, STATE, cinematic
    p1 = (name_input.strip() or 'P1').upper()[:8]
    p2 = (name_input2.strip() or 'P2').upper()[:8]
    p1_name = p1
    p2_name = p2
    start_game(pending_mode, p1, p2, ctrl_scheme)
    STATE = 'playing'
    cinematic = None

button_rects = {}

def check_mouse_click(mx, my):
    global STATE, menu_cursor, pending_mode, input_active, name_input, name_input2, p1_name, p2_name, ctrl_scheme, settings_music_vol, settings_sfx_vol, cinematic, game_over_state, loser_banner, loser_banner_timer
    if STATE == 'menu':
        for i in range(4):
            r = pygame.Rect(GAME_W // 2 - 145, 305 + i * 42, 290, 36)
            if r.collidepoint(mx, my):
                play_select()
                menu_cursor = i
                if i == 0:
                    pending_mode = 1
                    STATE = 'name_entry'
                    name_input = ''
                    name_input2 = ''
                    input_active = 0
                elif i == 1:
                    pending_mode = 2
                    STATE = 'name_entry'
                    name_input = ''
                    name_input2 = ''
                    input_active = 0
                elif i == 2:
                    STATE = 'how_to_play'
                elif i == 3:
                    STATE = 'settings'
                return
    elif STATE == 'how_to_play':
        if SCREEN_H - 60 <= my <= SCREEN_H - 30:
            play_select()
            STATE = 'menu'
    elif STATE == 'settings':
        sl_w = 240
        sl_x = GAME_W // 2 - sl_w // 2
        music_bar = pygame.Rect(sl_x, 95, sl_w, 30)
        if music_bar.collidepoint(mx, my):
            val = int((mx - sl_x) / sl_w * 100)
            val = max(0, min(100, val))
            settings_music_vol = val
            audio.set_music_volume(val / 100)
        sfx_bar = pygame.Rect(sl_x, 155, sl_w, 30)
        if sfx_bar.collidepoint(mx, my):
            val = int((mx - sfx_bar.x) / sl_w * 100)
            val = max(0, min(100, val))
            settings_sfx_vol = val
            audio.set_sfx_volume(val / 100)
        ci_y = 245
        ciw = 280
        cix = GAME_W // 2 - ciw // 2
        for i in range(2):
            r = pygame.Rect(cix, ci_y + i * 42, ciw, 36)
            if r.collidepoint(mx, my):
                settings_ctrl = 'wasd' if i == 0 else 'arrows'
                set_ctrl_scheme(settings_ctrl)
                save_settings()
        if SCREEN_H - 60 <= my <= SCREEN_H - 30:
            play_select()
            STATE = 'menu'
    elif STATE == 'name_entry':
        if pygame.Rect(GAME_W // 2 - 110, 145, 220, 36).collidepoint(mx, my):
            input_active = 0
        if pending_mode == 2 and pygame.Rect(GAME_W // 2 - 110, 225, 220, 36).collidepoint(mx, my):
            input_active = 1
        btn_y = 285 if pending_mode == 2 else 225
        if pygame.Rect(GAME_W // 2 - 100, btn_y, 200, 36).collidepoint(mx, my):
            play_select()
            start_game_now()
        if pygame.Rect(GAME_W // 2 - 100, btn_y + 44, 200, 36).collidepoint(mx, my):
            play_select()
            STATE = 'menu'
    elif STATE == 'paused':
        if pygame.Rect(GAME_W // 2 - 100, SCREEN_H // 2 + 25, 200, 36).collidepoint(mx, my):
            resume_game()
            STATE = 'playing'
        if pygame.Rect(GAME_W // 2 - 100, SCREEN_H // 2 + 69, 200, 36).collidepoint(mx, my):
            play_select()
            stop_game()
            audio.play_menu_music()
            STATE = 'menu'
    elif STATE == 'game_over':
        if pygame.Rect(GAME_W // 2 - 100, SCREEN_H // 2 + 50, 200, 36).collidepoint(mx, my):
            play_select()
            start_game_now()
        if pygame.Rect(GAME_W // 2 - 100, SCREEN_H // 2 + 94, 200, 36).collidepoint(mx, my):
            play_select()
            audio.play_menu_music()
            STATE = 'menu'

running = True
audio.play_menu_music()

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if STATE == 'menu':
                if event.key == pygame.K_UP:
                    menu_cursor = (menu_cursor - 1) % 4
                    play_select()
                elif event.key == pygame.K_DOWN:
                    menu_cursor = (menu_cursor + 1) % 4
                    play_select()
                elif event.key == pygame.K_RETURN:
                    play_select()
                    if menu_cursor == 0:
                        pending_mode = 1
                        STATE = 'name_entry'
                        name_input = ''
                        name_input2 = ''
                        input_active = 0
                    elif menu_cursor == 1:
                        pending_mode = 2
                        STATE = 'name_entry'
                        name_input = ''
                        name_input2 = ''
                        input_active = 0
                    elif menu_cursor == 2:
                        STATE = 'how_to_play'
                    elif menu_cursor == 3:
                        STATE = 'settings'

            elif STATE == 'how_to_play':
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    play_select()
                    STATE = 'menu'

            elif STATE == 'settings':
                sl_w = 240
                sl_x = GAME_W // 2 - sl_w // 2
                if event.key == pygame.K_LEFT:
                    if pygame.Rect(sl_x, 100, sl_w, 20).collidepoint(pygame.mouse.get_pos()):
                        pass
                    settings_music_vol = max(0, settings_music_vol - 5)
                    audio.set_music_volume(settings_music_vol / 100)
                elif event.key == pygame.K_RIGHT:
                    settings_music_vol = min(100, settings_music_vol + 5)
                    audio.set_music_volume(settings_music_vol / 100)
                elif event.key == pygame.K_ESCAPE:
                    play_select()
                    STATE = 'menu'

            elif STATE == 'name_entry':
                if event.key == pygame.K_TAB and pending_mode == 2:
                    input_active = 1 - input_active
                elif event.key == pygame.K_RETURN:
                    play_select()
                    start_game_now()
                elif event.key == pygame.K_ESCAPE:
                    play_select()
                    STATE = 'menu'
                elif event.key == pygame.K_BACKSPACE:
                    if input_active == 0:
                        name_input = name_input[:-1]
                    else:
                        name_input2 = name_input2[:-1]
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
                    resume_game()
                    STATE = 'playing'
            elif STATE == 'game_over':
                if event.key == pygame.K_RETURN:
                    play_select()
                    start_game_now()
                elif event.key == pygame.K_ESCAPE:
                    play_select()
                    audio.play_menu_music()
                    STATE = 'menu'

        if event.type == pygame.KEYUP:
            if STATE == 'playing' or STATE == 'paused':
                handle_key(event.key, False)

        if event.type == pygame.MOUSEBUTTONDOWN:
            check_mouse_click(event.pos[0], event.pos[1])

    # ── Render ──
    if STATE == 'menu':
        render_menu()
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
            cinematic = CrashCinematic(SCREEN, p['color'], p['name'], s['GAME_H'],
                lambda: None)
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
                draw_text_centered(SCREEN, '\u2620 ' + title + ' \u2620', SCREEN_H // 3 - 10, 12, (255, 51, 51))
                draw_text_centered(SCREEN, loser_banner['name'] + ' HA SIDO ELIMINADO', SCREEN_H // 3 + 15, 8, (255, 170, 0))
                s2 = get_state()
                if s2:
                    living = [p_ for p_ in s2['players'] if not p_['dead']]
                    if living:
                        draw_text_centered(SCREEN, '\u00a1' + living[0]['name'] + ' sigue luchando!', SCREEN_H // 3 + 35, 7, (136, 136, 136))
            if loser_banner_timer <= 0:
                loser_banner = None

    elif STATE == 'paused':
        if is_game_running():
            game_loop()
        render_pause()
    elif STATE == 'game_over':
        if not game_over_state:
            s = get_state()
            if s:
                game_over_state = s
        render_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit()
