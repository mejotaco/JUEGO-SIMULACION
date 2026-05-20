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
            return {
                'p1': d.get('ctrlSchemeP1', 'wasd'),
                'p2': d.get('ctrlSchemeP2', 'arrows')
            }
    except (FileNotFoundError, json.JSONDecodeError):
        return {'p1': 'wasd', 'p2': 'arrows'}

def save_settings():
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump({'ctrlSchemeP1': _ctrl_p1, 'ctrlSchemeP2': _ctrl_p2}, f)
    except Exception:
        pass

_ctrl_p1 = 'wasd'
_ctrl_p2 = 'arrows'

def set_ctrl_scheme(s):
    global _ctrl_p1
    _ctrl_p1 = s

def get_ctrl_scheme():
    return _ctrl_p1

def set_ctrl_p2(s):
    global _ctrl_p2
    _ctrl_p2 = s

def get_ctrl_p2():
    return _ctrl_p2
