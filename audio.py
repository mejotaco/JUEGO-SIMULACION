import pygame
import os

ASSETS = os.path.join(os.path.dirname(__file__), 'assets')

music_volume = 0.3
sfx_volume = 0.3

def load_volumes():
    global music_volume, sfx_volume
    try:
        with open(os.path.join(ASSETS, 'volumes.txt'), 'r') as f:
            lines = f.read().splitlines()
            if len(lines) >= 2:
                music_volume = max(0, min(1, float(lines[0])))
                sfx_volume = max(0, min(1, float(lines[1])))
    except (FileNotFoundError, ValueError):
        pass

def save_volumes():
    try:
        with open(os.path.join(ASSETS, 'volumes.txt'), 'w') as f:
            f.write(str(music_volume) + '\n' + str(sfx_volume))
    except Exception:
        pass

def set_music_volume(v):
    global music_volume
    music_volume = max(0, min(1, v))
    try:
        pygame.mixer.music.set_volume(music_volume)
    except Exception:
        pass
    save_volumes()

def set_sfx_volume(v):
    global sfx_volume
    sfx_volume = max(0, min(1, v))
    save_volumes()

def get_music_volume():
    return music_volume

def get_sfx_volume():
    return sfx_volume

# ── SFX ──
sfx_cache = {}
def _load_sfx(name):
    path = os.path.join(ASSETS, 'sfx', name)
    if name not in sfx_cache:
        try:
            sfx_cache[name] = pygame.mixer.Sound(path)
        except Exception:
            sfx_cache[name] = None
    return sfx_cache[name]

def play_disparo():
    s = _load_sfx('disparo.wav')
    if s:
        s.set_volume(sfx_volume)
        s.play()

def play_hit():
    s = _load_sfx('hit.wav')
    if s:
        s.set_volume(sfx_volume)
        s.play()

# ── Music ──
def stop_music():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception:
        pass

def play_music(name):
    stop_music()
    path = os.path.join(ASSETS, 'music', name)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)
    except Exception:
        pass

def play_menu_music():
    play_music('menu.mp3')

def play_aventura_music():
    play_music('aventura.mp3')

def play_boss_music():
    play_music('boss.mp3')
