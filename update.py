import math
import random
from config import ETYPES, POWERUP_TYPES

def update(dt, state, keys):
    state['shake'] = max(0, state.get('shake', 0) - dt * 2.5)

    for p in state['players']:
        if p['dead']:
            continue
        p['invTimer'] = max(0, p['invTimer'] - dt)
        p['shootCd'] = max(0, p['shootCd'] - dt)
        p['reloadTimer'] = max(0, p.get('reloadTimer', 0) - dt)
        p['heat'] = max(0, p.get('heat', 0) - dt * 3)

        ctrl_p = 'ctrlSchemeP1' if p['id'] == 0 else 'ctrlSchemeP2'
        p_wasd = state.get(ctrl_p, 'wasd' if p['id'] == 0 else 'arrows') == 'wasd'
        up = keys.get('w') if p_wasd else keys.get('up')
        dn = keys.get('s') if p_wasd else keys.get('down')
        lt = keys.get('a') if p_wasd else keys.get('left')
        rt = keys.get('d') if p_wasd else keys.get('right')
        sh = keys.get('capslock') if p_wasd else keys.get('shift')
        if p['id'] != 0:
            sh = sh or keys.get('ctrl')

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
            shoot_cd = 0.1 if p.get('powerup') == 'rapid_fire' else 0.25
            if p.get('powerup') == 'spread':
                for ang in [-0.15, 0, 0.15]:
                    cv, sv = math.cos(ang), math.sin(ang)
                    state['bullets'].append({
                        'x': p['x'] + (26 if p['lastDir'] > 0 else -18), 'y': p['y'],
                        'owner': p['id'], 'color': p['color'],
                        'w': 18, 'h': 5, 'dead': False,
                        'vx': 540 * p['lastDir'] * cv,
                        'vy': 540 * sv
                    })
            else:
                state['bullets'].append({
                    'x': p['x'] + (26 if p['lastDir'] > 0 else -18), 'y': p['y'],
                    'owner': p['id'], 'color': p['color'],
                    'w': 18, 'h': 5, 'dead': False,
                    'vx': 540 * p['lastDir']
                })
            import audio
            audio.play_disparo()
            p['shootCd'] = shoot_cd
            p['heat'] = p.get('heat', 0) + 2
            if p['heat'] >= p.get('heatMax', 15):
                p['heat'] = 0
                p['reloadTimer'] = 2.0

    if state.get('easterEgg'):
        for p in state['players']:
            if 'easterTimer' not in p:
                p['easterTimer'] = 3.5
            elif p['easterTimer'] > 0:
                p['easterTimer'] -= dt

    for b in state['bullets']:
        b['x'] += b['vx'] * dt
        b['y'] += b.get('vy', 0) * dt
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
        wave_factor = {1: 0.025, 2: 0.03, 3: 0.035, 4: 0.04, 5: 0.045}.get(state['wave'], 0.05)
        state['spawnTimer'] = max(0.3, 2.0 - state['killCount'] * wave_factor)

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
        rage = state.get('wave3RageTimer', 0) > 0
        if e['shootCd'] <= 0 and random.random() < 0.35:
            if tgt:
                if e['tier'] == 0:
                    state['eBullets'].append({
                        'x': e['x'] - 14, 'y': e['y'],
                        'vx': -220, 'vy': 0,
                        'w': 11, 'h': 5, 'dead': False, 'zone': e['zone']
                    })
                    if rage:
                        state['eBullets'].append({
                            'x': e['x'] - 14, 'y': e['y'],
                            'vx': -220 * 0.866, 'vy': -220 * 0.5,
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
                    if rage:
                        angle = random.choice([-1, 1])
                        rad = math.radians(30 * angle)
                        cv, sv = math.cos(rad), math.sin(rad)
                        bvx = dx / d * 195
                        bvy = dy / d * 195
                        state['eBullets'].append({
                            'x': e['x'] - 14, 'y': e['y'],
                            'vx': bvx * cv - bvy * sv,
                            'vy': bvx * sv + bvy * cv,
                            'w': 11, 'h': 5, 'dead': False, 'zone': e['zone']
                        })
                else:
                    state['eBullets'].append({
                        'x': e['x'] - 14, 'y': e['y'],
                        'vx': -180, 'vy': 0,
                        'wave': True, 'waveOffset': random.random() * 100,
                        'w': 14, 'h': 6, 'dead': False, 'zone': e['zone']
                    })
                    if rage:
                        state['eBullets'].append({
                            'x': e['x'] - 14, 'y': e['y'],
                            'vx': -180 * 0.866, 'vy': -180 * 0.5,
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
                    import audio as _a
                    _a.play_explosion()
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

                    if random.random() < 0.12 + e.get('tier', 0) * 0.06:
                        ptype = random.choice(['rapid_fire', 'heat_up', 'shield', 'spread'])
                        state['powerups'].append({
                            'x': e['x'], 'y': e['y'],
                            'type': ptype,
                            'vx': -40, 'vy': 20 + random.random() * 20,
                            'life': 8.0,
                            'w': 16, 'h': 16,
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
                if p.get('shield'):
                    p['shield'] = False
                    p['powerup'] = None
                    p['powerupTimer'] = 0
                    boom(p['x'], p['y'], (0, 200, 255), state)
                else:
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

    for pu in state['powerups']:
        pu['x'] += pu['vx'] * dt
        pu['y'] += pu['vy'] * dt
        pu['vy'] += 60 * dt
        pu['life'] -= dt
        for pp in state['players']:
            if pp['dead']:
                continue
            mx, my = 8, 8
            if overlap(pu['x'] - mx, pu['y'] - my, mx * 2, my * 2,
                       pp['x'] - 20, pp['y'] - 11, 40, 22):
                pu['life'] = -1
                if pu['type'] == 'rapid_fire':
                    pp['powerup'] = 'rapid_fire'
                    pp['powerupTimer'] = 6.0
                elif pu['type'] == 'spread':
                    pp['powerup'] = 'spread'
                    pp['powerupTimer'] = 6.0
                elif pu['type'] == 'heat_up':
                    pp['powerup'] = 'heat_up'
                    pp['powerupTimer'] = 12.0
                    pp['heatMax'] = 25
                elif pu['type'] == 'shield':
                    pp['shield'] = True
                    pp['powerup'] = 'shield'
                    pp['powerupTimer'] = 999
                state['puPickupMsg'] = '+' + POWERUP_TYPES.get(pu['type'], {}).get('label', pu['type'])
                state['puPickupTimer'] = 2.0
                break
    state['powerups'] = [pu for pu in state['powerups'] if pu['life'] > 0]

    for p in state['players']:
        if p.get('powerupTimer', 0) > 0:
            p['powerupTimer'] -= dt
            if p['powerupTimer'] <= 0:
                if p.get('powerup') == 'heat_up':
                    p['heatMax'] = 15
                elif p.get('powerup') == 'shield':
                    p['shield'] = False
                p['powerup'] = None
                p['powerupTimer'] = 0

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
                if p.get('shield'):
                    p['shield'] = False
                    p['powerup'] = None
                    p['powerupTimer'] = 0
                    boom(e['x'], e['y'], (0, 200, 255), state)
                else:
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
    elif state['killCount'] < 50:
        state['wave'] = 3
    elif state['killCount'] < 80:
        state['wave'] = 4
    else:
        state['wave'] = 5 + (state['killCount'] - 80) // 40

    if state['wave'] != prevWave:
        if state['wave'] == 2:
            state['waveMsg'] = '\u2605 WAVE 2 \u2605 +1 \u2665'
            state['waveMsgTimer'] = 2.0
            for p in state['players']:
                if not p['dead']:
                    p['lives'] += 1
        elif state['wave'] == 3:
            state['waveMsg'] = '\u2605 WAVE 3 \u2605 +1 \u2665'
            state['waveMsgTimer'] = 2.0
            for p in state['players']:
                if not p['dead']:
                    p['lives'] += 1
        elif state['wave'] == 4:
            state['waveMsg'] = '\u2605 WAVE 4 \u2605 +1 \u2665'
            state['waveMsgTimer'] = 2.0
            for p in state['players']:
                if not p['dead']:
                    p['lives'] += 1
        elif state['wave'] == 5 and not state.get('bossMusicPlayed'):
            state['bossMusicPlayed'] = True
            import audio
            audio.play_boss_music()
            state['waveMsg'] = '\u2605 WAVE 5 \u2605 BOSS INCOMING \u2605 +1 \u2665'
            state['waveMsgTimer'] = 3.0
            state['wave3RageTimer'] = 10.0
            for p in state['players']:
                if not p['dead']:
                    p['lives'] += 1
        elif state['wave'] > 5:
            state['waveMsg'] = '\u2605 WAVE {} \u2605 +1 \u2665'.format(state['wave'])
            state['waveMsgTimer'] = 2.0
            for p in state['players']:
                if not p['dead']:
                    p['lives'] += 1

    # Boss beaten → show GANASTE once
    if (state.get('bossMusicPlayed') and
        state.get('wave3RageTimer', 0) <= 0 and
        not state.get('gameBeaten') and
        state.get('wave', 1) >= 5):
        state['gameBeaten'] = True
        state['waveMsg'] = '\u2605\u2605 GANASTE \u2605\u2605'
        state['waveMsgTimer'] = 3.0

    state['waveMsgTimer'] = max(0, state.get('waveMsgTimer', 0) - dt)
    state['puPickupTimer'] = max(0, state.get('puPickupTimer', 0) - dt)
    state['wave3RageTimer'] = max(0, state.get('wave3RageTimer', 0) - dt)

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
    wave = state.get('wave', 1)
    max_enemies = {1: 6, 2: 8, 3: 11, 4: 15, 5: 18}.get(wave, 20)
    if len(state['enemies']) >= max_enemies:
        return
    roll = random.random()
    if state['killCount'] < 15:
        idx = 0
    elif state['killCount'] < 30:
        idx = 0 if roll < 0.5 else 1
    elif state['killCount'] < 50:
        idx = 0 if roll < 0.33 else (1 if roll < 0.66 else 2)
    elif state['killCount'] < 80:
        idx = 0 if roll < 0.2 else (1 if roll < 0.5 else 2)
    else:
        idx = 0 if roll < 0.1 else (1 if roll < 0.3 else 2)

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
