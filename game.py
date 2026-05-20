import pygame
from rng import rng
import math
from config import GAME_W, MENU_BG, POWERUP_TYPES
import audio
import renderer
from update import update as game_update, set_pygame_time
from utils import get_font

_active = True
_paused = False
_state = None
_keys = {}
_last_time = 0
_anim_loop = None
_esc_once = False
_esc_hint_timer = 0
_screen = None
_cinematic_pending = None
WAVES = [(1, 'STAGE 1'), (2, 'STAGE 2'), (3, 'STAGE 3')]


def wire_game_buttons():
    pass


def set_screen(screen):
    global _screen
    _screen = screen


def start_game(mode, p1_name, p2_name, ctrl_p1='wasd', ctrl_p2='arrows', easter=False):
    global _state, _last_time, _paused, _esc_once, _anim_loop
    audio.stop_music()
    _paused = False
    _esc_once = False
    _anim_loop = None

    game_h = 430 if mode == 2 else 440
    half_h = game_h // 2

    _state = {
        'GAME_W': GAME_W,
        'GAME_H': game_h,
        'HALF_H': half_h,
        'currentMode': mode,
        'p1Name': p1_name,
        'p2Name': p2_name,
        'score1': 0,
        'score2': 0,
        'killCount': 0,
        'wave': 1,
        'bossMusicPlayed': False,
        'ctrlSchemeP1': ctrl_p1,
        'ctrlSchemeP2': ctrl_p2,
        'easterEgg': easter,
        'shake': 0,
        'enemies': [],
        'bullets': [],
        'eBullets': [],
        'particles': [],
        'scorePopups': [],
        'gameOver': False,
        'gameBeaten': False,
        'spawnTimer': 2.0 * 0.2,
        'lastTime': 0,
        'powerups': [],
        'waveMsg': '',
        'waveMsgTimer': 0,
        'puPickupMsg': '',
        'puPickupTimer': 0,
        'loserShown': False,
        'loserShown2P': False,

        'starField': [
            {
                'x': rng.random() * GAME_W,
                'y': rng.random() * game_h,
                'spd': 20 + rng.random() * 80,
                'r': max(1, int(rng.random() * 2)),
                'a': 0.2 + rng.random() * 0.7
            } for _ in range(80)
        ],

        'players': [
            {
                'id': 0, 'zone': 0,
                'x': 70, 'y': half_h // 2 if mode == 2 else game_h // 2,
                'minX': 8, 'maxX': GAME_W - 8,
                'minY': 8, 'maxY': half_h - 8 if mode == 2 else game_h - 8,
                'lives': 3, 'dead': False,
                'color': (0, 255, 255), 'dark': (0, 51, 68),
                'invTimer': 0, 'shootCd': 0,
                'speed': 220, 'name': p1_name, 'lastDir': 1,
                'heat': 0, 'reloadTimer': 0,
                'powerup': None, 'powerupTimer': 0, 'heatMax': 15, 'shield': False
            }
        ]
    }

    if mode == 2:
        _state['players'].append({
            'id': 1, 'zone': 1,
            'x': 70, 'y': half_h + half_h // 2,
            'minX': 8, 'maxX': GAME_W - 8,
            'minY': half_h + 8, 'maxY': game_h - 8,
            'lives': 3, 'dead': False,
            'color': (255, 0, 255), 'dark': (68, 0, 51),
            'invTimer': 0, 'shootCd': 0,
            'speed': 220, 'name': p2_name, 'lastDir': 1,
            'heat': 0, 'reloadTimer': 0,
            'powerup': None, 'powerupTimer': 0, 'heatMax': 15, 'shield': False
        })

    _state['onPlayerDead'] = on_player_dead

    _last_time = 0
    audio.play_aventura_music()
    _anim_loop = True


def on_player_dead(p):
    global _cinematic_pending, _anim_loop
    if _state.get('loserShown'):
        return
    _state['loserShown'] = True
    if _state['currentMode'] == 1:
        _cinematic_pending = p
        _anim_loop = False


def game_loop():
    global _last_time, _anim_loop, _paused, _esc_once, _esc_hint_timer
    if _paused or not _anim_loop or _state is None:
        return
    now = pygame.time.get_ticks()
    if not _last_time:
        _last_time = now
    dt = min((now - _last_time) / 1000.0, 0.05)
    _last_time = now

    set_pygame_time(now)

    pressed = pygame.key.get_pressed()
    game_keys = {}
    p = _state['players'][0]
    ctrl_p1 = _state.get('ctrlSchemeP1', 'wasd')
    if ctrl_p1 == 'wasd':
        game_keys['w'] = pressed[pygame.K_w] or _keys.get(pygame.K_w, False)
        game_keys['s'] = pressed[pygame.K_s] or _keys.get(pygame.K_s, False)
        game_keys['a'] = pressed[pygame.K_a] or _keys.get(pygame.K_a, False)
        game_keys['d'] = pressed[pygame.K_d] or _keys.get(pygame.K_d, False)
        game_keys['capslock'] = pressed[pygame.K_CAPSLOCK] or _keys.get(pygame.K_CAPSLOCK, False)
        game_keys['up'] = False
        game_keys['down'] = False
        game_keys['left'] = False
        game_keys['right'] = False
        game_keys['shift'] = False
    else:
        game_keys['up'] = pressed[pygame.K_UP] or _keys.get(pygame.K_UP, False)
        game_keys['down'] = pressed[pygame.K_DOWN] or _keys.get(pygame.K_DOWN, False)
        game_keys['left'] = pressed[pygame.K_LEFT] or _keys.get(pygame.K_LEFT, False)
        game_keys['right'] = pressed[pygame.K_RIGHT] or _keys.get(pygame.K_RIGHT, False)
        game_keys['shift'] = pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT] or _keys.get(pygame.K_LSHIFT, False) or _keys.get(pygame.K_RSHIFT, False)
        game_keys['w'] = False
        game_keys['s'] = False
        game_keys['a'] = False
        game_keys['d'] = False
        game_keys['capslock'] = False

    if _state['currentMode'] == 2:
        ctrl_p2 = _state.get('ctrlSchemeP2', 'arrows')
        if ctrl_p2 == 'wasd':
            game_keys['w'] = game_keys['w'] or pressed[pygame.K_w] or _keys.get(pygame.K_w, False)
            game_keys['s'] = game_keys['s'] or pressed[pygame.K_s] or _keys.get(pygame.K_s, False)
            game_keys['a'] = game_keys['a'] or pressed[pygame.K_a] or _keys.get(pygame.K_a, False)
            game_keys['d'] = game_keys['d'] or pressed[pygame.K_d] or _keys.get(pygame.K_d, False)
            game_keys['ctrl'] = game_keys.get('ctrl', False) or pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL] or _keys.get(pygame.K_LCTRL, False) or _keys.get(pygame.K_RCTRL, False)
        else:
            game_keys['up'] = game_keys['up'] or pressed[pygame.K_UP] or _keys.get(pygame.K_UP, False)
            game_keys['down'] = game_keys['down'] or pressed[pygame.K_DOWN] or _keys.get(pygame.K_DOWN, False)
            game_keys['left'] = game_keys['left'] or pressed[pygame.K_LEFT] or _keys.get(pygame.K_LEFT, False)
            game_keys['right'] = game_keys['right'] or pressed[pygame.K_RIGHT] or _keys.get(pygame.K_RIGHT, False)
            game_keys['ctrl'] = game_keys.get('ctrl', False) or pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL] or _keys.get(pygame.K_LCTRL, False) or _keys.get(pygame.K_RCTRL, False)

    game_update(dt, _state, game_keys)

    renderer.render(_screen, _state, get_font)

    if _state.get('waveMsgTimer', 0) > 0:
        msg = _state.get('waveMsg', '')
        if msg:
            sf = get_font(9)
            txt = sf.render(msg, True, (255, 204, 0))
            tr = txt.get_rect(center=(GAME_W // 2, 55))
            _screen.blit(txt, tr)

    if _state.get('puPickupTimer', 0) > 0:
        msg = _state.get('puPickupMsg', '')
        if msg:
            pf = get_font(14)
            shadow = pf.render(msg, True, (0, 0, 0))
            main = pf.render(msg, True, (255, 255, 255))
            cx, cy = GAME_W // 2, 80
            for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                sr = shadow.get_rect(center=(cx + dx, cy + dy))
                _screen.blit(shadow, sr)
            mr = main.get_rect(center=(cx, cy))
            _screen.blit(main, mr)

    hud_y = -5
    font = get_font(10)
    hp = font.render(p['name'], True, (136, 136, 136))
    _screen.blit(hp, (6, hud_y))
    line1 = '\u2665' + str(p['lives']) + '  ' + str(_state['score1']).zfill(5)
    l1 = font.render(line1, True, (0, 255, 255))
    _screen.blit(l1, (6, hud_y + 12))

    if _state['currentMode'] == 2:
        p2 = _state['players'][1]
        hp2 = font.render(p2['name'], True, (136, 136, 136))
        _screen.blit(hp2, (6, hud_y + 28))
        line2 = '\u2665' + str(p2['lives']) + '  ' + str(_state['score2']).zfill(5)
        l2 = font.render(line2, True, (255, 0, 255))
        _screen.blit(l2, (6, hud_y + 40))

    wave_text = 'WAVE ' + str(_state.get('wave', 1))
    wt = font.render(wave_text, True, (240, 160, 0))
    _screen.blit(wt, (GAME_W - 100, hud_y + 12))

    kill_text = str(_state['killCount'])
    kt = font.render(kill_text, True, (240, 160, 0))
    _screen.blit(kt, (GAME_W - 100, hud_y + 26))

    active_pu = None
    for pp in _state['players']:
        if not pp['dead'] and pp.get('powerup'):
            active_pu = pp['powerup']
            break
    if active_pu:
        pu_info = POWERUP_TYPES.get(active_pu, {})
        pu_font = get_font(8)
        pu_label = pu_info.get('label', active_pu)
        pu_col = pu_info.get('color', (255, 255, 255))
        pu_surf = pu_font.render('[' + pu_label + ']', True, pu_col)
        _screen.blit(pu_surf, (GAME_W - 100, hud_y + 40))

    reloading = any(not p['dead'] and p.get('reloadTimer', 0) > 0 for p in _state['players'])
    if reloading:
        rt = font.render('RELOADING...', True, (255, 204, 0))
        _screen.blit(rt, (8, max(_state['GAME_H'] - 30, 0)))

    if _esc_once and _esc_hint_timer > 0:
        _esc_hint_timer -= dt
        hint = get_font(8).render('\u25c0 ESC de nuevo para pausar \u25b6', True, (240, 160, 0))
        hr = hint.get_rect(center=(GAME_W // 2, _state['GAME_H'] - 15))
        _screen.blit(hint, hr)
        if _esc_hint_timer <= 0:
            _esc_once = False

    if _state.get('gameOver'):
        do_game_over()


def is_game_active():
    return _active


def get_state():
    return _state


def handle_key(key_code, down):
    global _esc_once, _esc_hint_timer, _paused
    _keys[key_code] = down
    if down and key_code == pygame.K_ESCAPE and _state and _anim_loop:
        if _paused:
            resume_game()
            return
        if _esc_once:
            _esc_once = False
            _esc_hint_timer = 0
            pause_game()
        else:
            _esc_once = True
            _esc_hint_timer = 2.0


def pause_game():
    global _paused
    if _paused or _state is None or _state.get('gameOver'):
        return
    _paused = True


def resume_game():
    global _paused, _last_time
    if not _paused:
        return
    _paused = False
    _last_time = 0


def cinematic_done():
    global _cinematic_pending, _anim_loop, _last_time
    _cinematic_pending = None
    _anim_loop = True
    _last_time = 0


def get_cinematic_pending():
    return _cinematic_pending


def stop_game():
    global _anim_loop, _paused, _cinematic_pending
    _anim_loop = False
    _paused = False
    _cinematic_pending = None


def is_paused():
    return _paused


def is_game_running():
    return _anim_loop or _paused


def set_paused(v):
    global _paused
    _paused = v


def do_game_over():
    global _anim_loop
    _anim_loop = False
    audio.stop_music()
    _state['gameOver'] = True
