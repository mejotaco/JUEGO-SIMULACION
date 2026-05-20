import pygame
import random
import math
from config import LOSER_TITLES
from utils import get_font_safe

def random_loser_title():
    return random.choice(LOSER_TITLES)

class CrashCinematic:
    def __init__(self, screen, player_color, player_name, game_h, on_done):
        self.screen = screen
        self.player_color = player_color
        self.player_name = player_name
        self.game_h = game_h
        self.on_done = on_done
        self.W = 700
        self.t = 0.0
        self.duration = 4.5
        self.exploded = False
        self.exp_particles = []
        self.debris = []
        self.smoke_trails = []
        self.done = False

        self.ship_start_x = 60
        self.ship_start_y = game_h * 0.35
        self.tower1_x = 480
        self.tower2_x = 540
        self.tower_w = 44
        self.tower_top_h = 70
        self.tower_body_h = 280
        self.tower_top_y = game_h - self.tower_body_h - self.tower_top_h
        self.impact_x = self.tower1_x + self.tower_w // 2
        self.impact_y = self.tower_top_y + 30

        self.dark = (0, 51, 68) if player_color == (0, 255, 255) else (68, 0, 51)

        self.bg_stars = []
        for _ in range(60):
            self.bg_stars.append({
                'x': random.random() * self.W,
                'y': random.random() * (game_h * 0.55),
                'r': max(1, int(random.random() * 2)),
                'a': 0.2 + random.random() * 0.6
            })

        self.loser_shown_title = None
        self.second_explosion_timer = None

    def spawn_explosion(self, x, y, count, max_r, max_spd):
        colors = [(255, 68, 0), (255, 170, 0), (255, 255, 0), (255, 102, 0), (255, 255, 255)]
        for _ in range(count):
            a = random.random() * math.pi * 2
            spd = 20 + random.random() * max_spd
            life = 0.6 + random.random() * 1.2
            self.exp_particles.append({
                'x': x, 'y': y,
                'vx': math.cos(a) * spd,
                'vy': math.sin(a) * spd - random.random() * 30,
                'r': 3 + int(random.random() * max_r),
                'life': life, 'maxLife': life,
                'color': random.choice(colors)
            })

    def spawn_debris(self, x, y):
        colors = [(136, 136, 136), (170, 170, 170), (255, 102, 0), (204, 204, 204)]
        for _ in range(20):
            a = -math.pi / 2 + (random.random() - 0.5) * math.pi * 1.2
            spd = 40 + random.random() * 120
            self.debris.append({
                'x': x, 'y': y,
                'vx': math.cos(a) * spd,
                'vy': math.sin(a) * spd,
                'w': 4 + int(random.random() * 10),
                'h': 4 + int(random.random() * 10),
                'rot': random.random() * math.pi,
                'rotSpd': (random.random() - 0.5) * 6,
                'life': 2 + random.random() * 2,
                'color': random.choice(colors)
            })

    def draw_tower(self, x):
        body_y = self.game_h - self.tower_body_h
        pygame.draw.rect(self.screen, (85, 85, 85), (x, body_y, self.tower_w, self.tower_body_h))
        for row in range(8):
            for col in range(3):
                wx = x + 5 + col * 12
                wy = body_y + 10 + row * 28
                c = (255, 238, 136) if random.random() < 0.15 else (34, 34, 34)
                pygame.draw.rect(self.screen, c, (wx, wy, 8, 10))
        pygame.draw.rect(self.screen, (102, 102, 102), (x + self.tower_w // 2 - 4, self.tower_top_y, 8, self.tower_top_h))
        pygame.draw.rect(self.screen, (136, 136, 136), (x + self.tower_w // 2 - 2, self.tower_top_y - 20, 4, 22))
        pygame.draw.rect(self.screen, (102, 102, 102), (x - 4, self.tower_top_y, self.tower_w + 8, 18))
        glow = pygame.Surface((6, self.tower_body_h), pygame.SRCALPHA)
        glow.fill((150, 220, 255, 38))
        self.screen.blit(glow, (x + 2, body_y))

    def update(self, dt):
        if self.done:
            return
        self.t += dt

        self.screen.fill((0, 0, 8))

        gradient = pygame.Surface((self.W, int(self.game_h * 0.6)))
        for i in range(int(self.game_h * 0.6)):
            ratio = i / (self.game_h * 0.6)
            b = int(24 - ratio * 24)
            gradient.set_at((0, i), (0, 0, b))
        gradient = pygame.transform.scale(gradient, (self.W, int(self.game_h * 0.6)))
        self.screen.blit(gradient, (0, 0))

        for s in self.bg_stars:
            a = int(s['a'] * 255)
            star = pygame.Surface((s['r'], s['r']), pygame.SRCALPHA)
            star.fill((255, 255, 255, a))
            self.screen.blit(star, (int(s['x']), int(s['y'])))

        pygame.draw.circle(self.screen, (221, 238, 255), (600, 60), 28)
        pygame.draw.circle(self.screen, (0, 0, 24), (615, 55), 22)

        pygame.draw.rect(self.screen, (17, 17, 17), (0, self.game_h - self.tower_body_h, self.W, self.tower_body_h))
        glow_g = pygame.Surface((self.W, 35), pygame.SRCALPHA)
        glow_g.fill((255, 180, 60, 20))
        self.screen.blit(glow_g, (0, self.game_h - self.tower_body_h - 30))

        bgs = [(50, 120, 40, 200), (140, 90, 35, 230), (230, 110, 38, 210),
               (620, 100, 36, 220), (660, 80, 32, 240)]
        for bxi, _, bwi, bhi in bgs:
            pygame.draw.rect(self.screen, (26, 26, 26), (bxi, self.game_h - bhi, bwi, bhi))
            for rr in range(bhi // 16):
                for cc in range(bwi // 12):
                    col2 = (85, 68, 0) if random.random() < 0.3 else (26, 26, 10)
                    pygame.draw.rect(self.screen, col2, (bxi + 3 + cc * 12, self.game_h - bhi + 4 + rr * 16, 7, 8))

        self.draw_tower(self.tower1_x)
        self.draw_tower(self.tower2_x)

        progress = min(self.t / 2.2, 1)
        ship_x = self.ship_start_x + (self.impact_x - 40 - self.ship_start_x) * progress
        ship_y = self.ship_start_y * (1 - progress) + self.impact_y * progress + math.sin(progress * math.pi) * (-30)
        wobble = (progress - 0.7) / 0.3 * math.sin(self.t * 25) * 4 if progress > 0.7 else 0

        if not self.exploded:
            if self.t < 2.2 and random.random() < 0.6:
                self.smoke_trails.append({
                    'x': ship_x - 10, 'y': ship_y + wobble,
                    'vx': -15 - random.random() * 10,
                    'vy': (random.random() - 0.5) * 8,
                    'r': 3 + random.random() * 4,
                    'life': 0.8 + random.random() * 0.4,
                    'base': 80 + int(random.random() * 40)
                })
            new_smoke = []
            for s in self.smoke_trails:
                s['x'] += s['vx'] * dt
                s['y'] += s['vy'] * dt
                s['life'] -= dt
                s['r'] += dt * 3
                if s['life'] > 0:
                    a2 = int(max(0, s['life'] * 0.5) * 255)
                    smoke = pygame.Surface((int(s['r']) * 2, int(s['r']) * 2), pygame.SRCALPHA)
                    pygame.draw.circle(smoke, (s['base'], s['base'], s['base'], a2), (int(s['r']), int(s['r'])), int(s['r']))
                    self.screen.blit(smoke, (int(s['x']) - int(s['r']), int(s['y']) - int(s['r'])))
                    new_smoke.append(s)
            self.smoke_trails = new_smoke

            if self.t < 2.2:
                angle = ((ship_y + wobble - self.ship_start_y) / (self.impact_y - self.ship_start_y)) * 0.3 + math.sin(self.t * 2) * 0.05
                surf = pygame.Surface((100, 80), pygame.SRCALPHA)
                self._draw_cinematic_ship(surf)
                rot_surf = pygame.transform.rotate(surf, -angle * 57.3)
                r = rot_surf.get_rect(center=(int(ship_x), int(ship_y + wobble)))
                self.screen.blit(rot_surf, r)
            else:
                self.exploded = True
                self.spawn_explosion(self.impact_x, self.impact_y, 60, 12, 200)
                self.spawn_debris(self.impact_x, self.impact_y)
                self.second_explosion_timer = 0.2

        if self.second_explosion_timer is not None:
            self.second_explosion_timer -= dt
            if self.second_explosion_timer <= 0:
                self.spawn_explosion(self.tower2_x + self.tower_w // 2, self.tower_top_y + 20, 40, 10, 150)
                self.second_explosion_timer = None

        new_particles = []
        for p in self.exp_particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 60 * dt
            p['life'] -= dt
            if p['life'] > 0:
                alpha = max(0, p['life'] / p['maxLife'])
                sz2 = max(1, int(p['r'] * alpha))
                s2 = pygame.Surface((sz2, sz2), pygame.SRCALPHA)
                s2.set_alpha(int(alpha * 255))
                s2.fill(p['color'])
                self.screen.blit(s2, (int(p['x']), int(p['y'])))
                new_particles.append(p)
        self.exp_particles = new_particles

        new_debris = []
        for d in self.debris:
            d['x'] += d['vx'] * dt
            d['y'] += d['vy'] * dt
            d['vy'] += 80 * dt
            d['rot'] += d['rotSpd'] * dt
            d['life'] -= dt
            if d['life'] > 0:
                alpha = max(0, min(1, d['life'] * 0.5))
                surf2 = pygame.Surface((d['w'], d['h']))
                surf2.set_alpha(int(alpha * 255))
                surf2.fill(d['color'])
                rot_surf2 = pygame.transform.rotate(surf2, d['rot'] * 57.3)
                r2 = rot_surf2.get_rect(center=(int(d['x']), int(d['y'])))
                self.screen.blit(rot_surf2, r2)
                new_debris.append(d)
        self.debris = new_debris

        if self.exploded and self.t < 2.5:
            flash_a = max(0, (2.5 - self.t) / 0.3) * 0.7
            flash = pygame.Surface((self.W, self.game_h), pygame.SRCALPHA)
            flash.fill((255, 200, 100, int(flash_a * 255)))
            self.screen.blit(flash, (0, 0))

        if self.exploded:
            fire_a = min(1, (self.t - 2.2) * 2) * 0.5
            fire1 = pygame.Surface((self.tower_w + 40, 120), pygame.SRCALPHA)
            fire1.fill((255, 80, 0, int(fire_a * 0.3 * 255)))
            self.screen.blit(fire1, (self.tower1_x - 20, self.tower_top_y - 40))
            fire2 = pygame.Surface((self.tower_w + 20, 80), pygame.SRCALPHA)
            fire2.fill((255, 180, 0, int(fire_a * 0.2 * 255)))
            self.screen.blit(fire2, (self.tower2_x - 10, self.tower_top_y - 20))

        if self.t > 2.6:
            text_a = min(1, (self.t - 2.6) * 2)
            if not self.loser_shown_title:
                self.loser_shown_title = random_loser_title()
            font_big = get_font_safe(11)
            font_small = get_font_safe(8)
            title = self.loser_shown_title
            txt1 = font_big.render('\u2620 ' + title + ' \u2620', True, (255, 51, 51))
            txt1.set_alpha(int(text_a * 255))
            r1 = txt1.get_rect(center=(self.W // 2, int(self.game_h * 0.25)))
            self.screen.blit(txt1, r1)
            txt2 = font_small.render(self.player_name + ' HA SIDO ELIMINADO', True, (255, 170, 0))
            txt2.set_alpha(int(text_a * 255))
            r2 = txt2.get_rect(center=(self.W // 2, int(self.game_h * 0.25) + 30))
            self.screen.blit(txt2, r2)

        if self.t > 3.5:
            alpha = min(1, (self.t - 3.5) * 3)
            font = get_font_safe(7)
            txt = font.render('VOLVIENDO AL JUEGO...', True, (136, 136, 136))
            txt.set_alpha(int(alpha * 255))
            r = txt.get_rect(center=(self.W // 2, self.game_h - 20))
            self.screen.blit(txt, r)

        if self.t >= self.duration:
            self.done = True
            self.on_done()

    def _draw_cinematic_ship(self, surf):
        import renderer
        sheet = renderer.player_sheet
        if sheet:
            frame = int(pygame.time.get_ticks() / 180) % 2
            fw, fh = 48, 32
            spr = sheet.subsurface(frame * fw, 0, fw, fh)
            cx2, cy2 = 50, 40
            surf.blit(spr, (cx2 - fw // 2, cy2 - fh // 2))
        else:
            cx, cy = 50, 40
            frame = int(pygame.time.get_ticks() / 90) % 3
            flames = [(255, 170, 0), (255, 102, 0), (255, 255, 0)]
            color = self.player_color
            dark = self.dark
            pygame.draw.rect(surf, flames[frame], (cx - 22, cy - 3, 10, 6))
            pygame.draw.rect(surf, (255, 255, 255) if frame == 1 else (255, 204, 0), (cx - 28, cy - 1, 8, 2))
            pygame.draw.rect(surf, dark, (cx - 10, cy - 14, 18, 6))
            pygame.draw.rect(surf, dark, (cx - 10, cy + 8, 18, 6))
            pygame.draw.rect(surf, color, (cx - 8, cy - 12, 14, 4))
            pygame.draw.rect(surf, color, (cx - 8, cy + 8, 14, 4))
            pygame.draw.rect(surf, color, (cx - 14, cy - 7, 36, 14))
            pygame.draw.rect(surf, color, (cx + 22, cy - 5, 6, 10))
            pygame.draw.rect(surf, color, (cx + 28, cy - 3, 6, 6))
            pygame.draw.rect(surf, color, (cx + 32, cy - 1, 6, 2))
            pygame.draw.rect(surf, (255, 255, 255), (cx + 2, cy - 5, 12, 10))
            pygame.draw.rect(surf, (170, 255, 255), (cx + 4, cy - 3, 8, 6))
            pygame.draw.rect(surf, (0, 119, 153), (cx + 6, cy - 1, 4, 2))
            pygame.draw.rect(surf, dark, (cx - 14, cy - 7, 36, 2))
            pygame.draw.rect(surf, dark, (cx - 14, cy + 5, 36, 2))
