import json
import os

HERE = os.path.dirname(__file__)
BOARD_PATH = os.path.join(HERE, 'assets', 'leaderboard.json')
SETTINGS_PATH = os.path.join(HERE, 'assets', 'settings.json')

def load_board():
    try:
        with open(BOARD_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_board(b):
    try:
        with open(BOARD_PATH, 'w') as f:
            json.dump(b, f)
    except Exception:
        pass

def add_score(name, score):
    b = load_board()
    b.append({'name': name.upper()[:8], 'score': score})
    b.sort(key=lambda x: -x['score'])
    b[:] = b[:5]
    save_board(b)

def load_settings():
    try:
        with open(SETTINGS_PATH, 'r') as f:
            d = json.load(f)
            return d.get('ctrlScheme', 'wasd')
    except (FileNotFoundError, json.JSONDecodeError):
        return 'wasd'

def save_settings():
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump({'ctrlScheme': get_ctrl_scheme()}, f)
    except Exception:
        pass

_ctrl_scheme = 'wasd'

def set_ctrl_scheme(s):
    global _ctrl_scheme
    _ctrl_scheme = s

def get_ctrl_scheme():
    return _ctrl_scheme
