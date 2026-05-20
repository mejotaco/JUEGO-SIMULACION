SCREEN_W = 700
SCREEN_H = 520
GAME_W = 700
FPS = 60

WHITE = (255, 255, 255)

ETYPES = [
    {'w': 26, 'h': 18, 'maxHp': 1, 'pts': 100, 'col': (255, 68, 68),   'dark': (102, 0, 0),    'spdMul': 1.0, 'wobF': 0, 'wAmp': 0, 'sCD': 2.2, 'tier': 0},
    {'w': 32, 'h': 24, 'maxHp': 2, 'pts': 200, 'col': (255, 136, 0),   'dark': (119, 51, 0),   'spdMul': 0.7, 'wobF': 0.08, 'wAmp': 2.8, 'sCD': 1.8, 'tier': 1},
    {'w': 40, 'h': 30, 'maxHp': 3, 'pts': 350, 'col': (204, 0, 255),   'dark': (85, 0, 136),   'spdMul': 0.5, 'wobF': 0.018, 'wAmp': 12, 'sCD': 1.5, 'tier': 2},
]

LOSER_TITLES = [
    '\u00a1PERDEDOR!', 'FIN DEL JUEGO', 'HAS MUERTO \U0001F480', 'PROBLEMA DE HABILIDAD', '\u00a1MUY LENTO!',
    '\u00a1ELIMINADO!', '\u00a1DESTRUIDO!', '\u00a1NOS VEMOS!', '\u00a1ADIOS!', '\u00a1TE LIMPIARON!',
    '\u00a1NOOB ALERTA!', 'L + RATIO', 'VE A TOCAR PASTO', 'PEOR PILOTO', 'MUERTE F\u00c1CIL', '\u00a1ELIMINADO!',
]

P1_COLOR = (0, 255, 255)
P1_DARK = (0, 51, 68)
P2_COLOR = (255, 0, 255)
P2_DARK = (68, 0, 51)
HUD_COLOR = (240, 160, 0)

POWERUP_TYPES = {
    'rapid_fire': {'color': (255, 255, 0), 'label': 'RAPIDO', 'desc': 'Disparo Rapido'},
    'heat_up':    {'color': (255, 120, 0), 'label': 'CALOR+', 'desc': '+10 Disparos'},
    'shield':     {'color': (0, 200, 255), 'label': 'ESCUDO', 'desc': 'Escudo 1 Hit'},
    'spread':     {'color': (0, 255, 100), 'label': 'SPREAD', 'desc': 'Triple Disparo'},
}

MENU_BG = (10, 0, 16)
GAME_BG = (0, 0, 0)
