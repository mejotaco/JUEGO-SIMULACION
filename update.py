import math
import random
from config import ETYPES

def update(dt, state, keys):
    state['shake'] = max(0, state.get('shake', 0) - dt * 2.5)

    for p in state['players']:
        if p['dead']:
            continue
        p['invTimer'] = max(0, p['invTimer'] - dt)
        p['shootCd'] = max(0, p['shootCd'] - dt)
        p['reloadTimer'] = max(0, p.get('reloadTimer', 0) - dt)
        p['heat'] = max(0, p.get('heat', 0) - dt * 3)

        useWASD = state['currentMode'] == 1 and state.get('ctrlScheme', 'wasd') == 'wasd'
        up = p['id'] == 0 and (keys.get('w') if useWASD else keys.get('up')) or (p['id'] != 0 and keys.get('w'))
        dn = p['id'] == 0 and (keys.get('s') if useWASD else keys.get('down')) or (p['id'] != 0 and keys.get('s'))
        lt = p['id'] == 0 and (keys.get('a') if useWASD else keys.get('left')) or (p['id'] != 0 and keys.get('a'))
        rt = p['id'] == 0 and (keys.get('d') if useWASD else keys.get('right')) or (p['id'] != 0 and keys.get('d'))
        sh = p['id'] == 0 and (keys.get('capslock') if useWASD else keys.get('shift')) or (p['id'] != 0 and keys.get('ctrl'))

        if up:
            p['y'] = max(p['minY'] + 12, p['y'] - p['speed'] * dt)
        if dn:
            p['y'] = min(p['maxY'] - 12, p['y'] + p['speed'] * dt)
        if lt:
            p['x'] = max(p['minX'] + 20, p['x'] - p['speed'] * dt)
            p['lastDir'] = -1
        if rt:
            p['x'] = min(p['maxX'] - 20, p['x'] + p['speed'] * dt)
            p['lastDir'] = 1

        if sh and p['shootCd'] <= 0 and not p.get('reloadTimer'):
            state['bullets'].append({
                'x': p['x'] + (26 if p['lastDir'] > 0 else -18), 'y': p['y'],
                'owner': p['id'], 'color': p['color'],
                'w': 18, 'h': 5, 'dead': False,
                'vx': 540 * p['lastDir']
            })
            import audio
            audio.play_disparo()
            p['shootCd'] = 0.25
            p['heat'] = p.get('heat', 0) + 2
            if p['heat'] >= 15:
                p['heat'] = 0
                p['reloadTimer'] = 2.0

    for b in state['bullets']:
        b['x'] += b['vx'] * dt
        if b['x'] > state['GAME_W'] + 30 or b['x'] < -30:
            b['dead'] = True
        if state['currentMode'] == 2:
            if b['owner'] == 0 and b['y'] > state['HALF_H']:
                b['dead'] = True
            if b['owner'] == 1 and b['y'] < state['HALF_H']:
                b['dead'] = True

    state['spawnTimer'] -= dt
    if state['spawnTimer'] <= 0:
        spawnEnemy(state)
        state['spawnTimer'] = max(0.5, 2.0 - state['killCount'] * 0.025)

    for e in state['enemies']:
        e['x'] -= e['spd'] * dt

        tgt = next((p for p in state['players'] if not p['dead'] and p.get('zone') == e['zone']), None)
        if tgt:
            dy = tgt['y'] - e['y']
            e['y'] += (1 if dy > 0 else -1 if dy < 0 else 0) * e['spd'] * (state.get('wave', 1)) * 0.12 * dt

        if e.get('tier') in (1, 2):
            e['y'] += math.sin(pygame_time() * 0.001 * e['wobF'] * 100 + e['wOff']) * e['wAmp']

        e['y'] = clamp(e['y'], e['minY'], e['maxY'])
        e['shootCd'] -= dt
        if e['shootCd'] <= 0 and random.random() < 0.35:
            if tgt:
                if e['tier'] == 0:
                    state['eBullets'].append({
                        'x': e['x'] - 14, 'y': e['y'],
                        'vx': -220, 'vy': 0,
                        'w': 11, 'h': 5, 'dead': False, 'zone': e['zone']
                    })
                elif e['tier'] == 1:
                    dx = tgt['x'] - e['x']
                    dy = tgt['y'] - e['y']
                    d = math.sqrt(dx * dx + dy * dy) or 1
                    state['eBullets'].append({
                        'x': e['x'] - 14, 'y': e['y'],
                        'vx': dx / d * 195, 'vy': dy / d * 195,
                        'w': 11, 'h': 5, 'dead': False, 'zone': e['zone']
                    })
                else:
                    state['eBullets'].append({
                        'x': e['x'] - 14, 'y': e['y'],
                        'vx': -180, 'vy': 0,
                        'wave': True, 'waveOffset': random.random() * 100,
                        'w': 14, 'h': 6, 'dead': False, 'zone': e['zone']
                    })
            e['shootCd'] = 1.3 + random.random() * 1.5

    state['enemies'] = [e for e in state['enemies'] if e['x'] > -60]

    for b in state['eBullets']:
        b['x'] += b['vx'] * dt
        b['y'] += b['vy'] * dt
        if b.get('wave'):
            b['y'] += math.sin(pygame_time() * 0.01 + b['waveOffset']) * 2.5
        if b['x'] < -40 or b['x'] > state['GAME_W'] + 40 or b['y'] < -40 or b['y'] > state['GAME_H'] + 40:
            b['dead'] = True
        if state['currentMode'] == 2:
            if b.get('zone') == 0 and b['y'] > state['HALF_H']:
                b['dead'] = True
            if b.get('zone') == 1 and b['y'] < state['HALF_H']:
                b['dead'] = True

    for b in state['bullets']:
        if b['dead']:
            continue
        for e in state['enemies']:
            if e['dead']:
                continue
            if state['currentMode'] == 2:
                bz = 'top' if b['owner'] == 0 else 'bottom'
                ez = 'top' if e['y'] < state['HALF_H'] else 'bottom'
                if bz != ez:
                    continue
            if overlap(b['x'], b['y'] - b['h'] / 2, b['w'], b['h'],
                       e['x'] - e['w'] / 2, e['y'] - e['h'] / 2, e['w'], e['h']):
                e['hp'] -= 1
                b['dead'] = True
                if e['hp'] <= 0:
                    e['dead'] = True
                    state['killCount'] += 1
                    boom(e['x'], e['y'], e['col'], state)
                    if b['owner'] == 0:
                        state['score1'] += e['pts']
                    else:
                        state['score2'] += e['pts']
                    state['scorePopups'].append({
                        'x': e['x'], 'y': e['y'] - 10,
                        'text': '+' + str(e['pts']),
                        'color': (0, 255, 255) if b['owner'] == 0 else (255, 0, 255),
                        'life': 1.1, 'vy': -35
                    })

    state['bullets'] = [b for b in state['bullets'] if not b['dead']]
    state['enemies'] = [e for e in state['enemies'] if not e['dead']]

    for b in state['eBullets']:
        if b['dead']:
            continue
        for p in state['players']:
            if p['dead'] or p['invTimer'] > 0:
                continue
            if state['currentMode'] == 2 and b.get('zone') != p.get('zone'):
                continue
            if overlap(b['x'], b['y'] - b['h'] / 2, b['w'], b['h'],
                       p['x'] - 20, p['y'] - 11, 40, 22):
                b['dead'] = True
                import audio
                audio.play_hit()
                state['shake'] = 1.0
                p['lives'] -= 1
                p['invTimer'] = 2.0
                boom(p['x'], p['y'], p['color'], state)
                if p['lives'] <= 0:
                    p['dead'] = True
                    state.get('onPlayerDead', lambda x: None)(p)

    state['eBullets'] = [b for b in state['eBullets'] if not b['dead']]

    for e in state['enemies']:
        if e['dead']:
            continue
        for p in state['players']:
            if p['dead'] or p['invTimer'] > 0:
                continue
            if state['currentMode'] == 2 and e.get('zone') != p.get('zone'):
                continue
            if overlap(e['x'] - e['w'] / 2, e['y'] - e['h'] / 2, e['w'], e['h'],
                       p['x'] - 20, p['y'] - 11, 40, 22):
                e['dead'] = True
                p['lives'] -= 1
                p['invTimer'] = 2.0
                boom(e['x'], e['y'], e['col'], state)
                if p['lives'] <= 0:
                    p['dead'] = True
                    state.get('onPlayerDead', lambda x: None)(p)

    state['enemies'] = [e for e in state['enemies'] if not e['dead']]

    for p in state['particles']:
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt
        p['life'] -= dt
    state['particles'] = [p for p in state['particles'] if p['life'] > 0]

    for s in state['scorePopups']:
        s['y'] += s['vy'] * dt
        s['life'] -= dt
    state['scorePopups'] = [s for s in state['scorePopups'] if s['life'] > 0]

    prevWave = state.get('wave', 1)
    if state['killCount'] < 15:
        state['wave'] = 1
    elif state['killCount'] < 30:
        state['wave'] = 2
    else:
        state['wave'] = 3

    if state['wave'] != prevWave and state['wave'] == 3 and not state.get('bossMusicPlayed'):
        state['bossMusicPlayed'] = True
        import audio
        audio.play_boss_music()
        state['waveMsg'] = '\u2605 BOSS INCOMING \u2605 +1 \u2665'
        state['waveMsgTimer'] = 2.0
        for p in state['players']:
            if not p['dead']:
                p['lives'] += 1

    if state['wave'] != prevWave and state['wave'] == 2:
        state['waveMsg'] = '\u2605 WAVE 2 \u2605 +1 \u2665'
        state['waveMsgTimer'] = 2.0
        for p in state['players']:
            if not p['dead']:
                p['lives'] += 1

    state['waveMsgTimer'] = max(0, state.get('waveMsgTimer', 0) - dt)

    alive = [p for p in state['players'] if not p['dead']]
    if len(alive) == 0:
        state['gameOver'] = True


def boom(x, y, color, state):
    for _ in range(18):
        a = random.random() * math.pi * 2
        spd = 15 + random.random() * 120
        state['particles'].append({
            'x': x, 'y': y,
            'vx': math.cos(a) * spd, 'vy': math.sin(a) * spd,
            'r': 2 + random.random() * 5,
            'life': 0.3 + random.random() * 0.5,
            'color': color
        })


def spawnEnemy(state):
    roll = random.random()
    if state['killCount'] < 15:
        idx = 0
    elif state['killCount'] < 30:
        idx = 0 if roll < 0.5 else 1
    else:
        idx = 0 if roll < 0.33 else (1 if roll < 0.66 else 2)

    t = ETYPES[idx]
    baseSpd = 35 + min(state['killCount'], 60) * 0.8

    if state['currentMode'] == 2:
        alive = [p for p in state['players'] if not p['dead']]
        src = alive[int(random.random() * len(alive))] if alive else state['players'][0]
        zone = src.get('zone', 0)
        minY = src['minY'] + t['h'] / 2
        maxY = src['maxY'] - t['h'] / 2
    else:
        minY = t['h'] / 2 + 8
        maxY = state['GAME_H'] - t['h'] / 2 - 8
        zone = 0

    minY = max(t['h'] / 2 + 4, minY)
    maxY = min(state['GAME_H'] - t['h'] / 2 - 4, maxY)
    if minY >= maxY:
        maxY = minY + 10

    tier_val = 0 if idx == 0 else (1 if idx == 1 else 2)
    state['enemies'].append({
        'x': state['GAME_W'] + t['w'] / 2 + 10,
        'y': minY + random.random() * (maxY - minY),
        'w': t['w'], 'h': t['h'],
        'hp': t['maxHp'], 'maxHp': t['maxHp'],
        'pts': t['pts'], 'col': t['col'], 'dark': t['dark'],
        'spd': baseSpd * t['spdMul'],
        'wobF': t['wobF'], 'wAmp': t['wAmp'],
        'wOff': random.random() * 100,
        'shootCd': t['sCD'] + random.random(),
        'tier': tier_val,
        'dead': False, 'minY': minY, 'maxY': maxY, 'zone': zone,
        'spriteIdx': random.randint(0, 2) if tier_val == 2 else 0
    })


def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


_pg_time = 0

def set_pygame_time(t):
    global _pg_time
    _pg_time = t

def pygame_time():
    return _pg_time
