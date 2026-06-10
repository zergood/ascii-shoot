#!/usr/bin/env python3
"""ASCII FPS — Doom-style raycasting shooter in the terminal."""

import curses
import math
import time
import random
import sys

# ---------------------------------------------------------------------------
# Level data
# ---------------------------------------------------------------------------

MAP_W = 24
MAP_H = 24

# 0=empty, 1-4=wall types (different colors)
WORLD_MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0,0,1],
    [1,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,2,0,0,1],
    [1,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,2,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0,0,1],
    [1,0,0,0,0,0,0,0,0,3,3,3,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,3,0,0,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,3,0,0,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,3,3,3,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,2,2,2,2,0,0,0,0,0,0,4,4,4,4,0,0,0,0,1],
    [1,0,0,0,0,2,0,0,2,0,0,0,0,0,0,4,0,0,4,0,0,0,0,1],
    [1,0,0,0,0,2,0,0,2,0,0,0,0,0,0,4,0,0,4,0,0,0,0,1],
    [1,0,0,0,0,2,2,2,2,0,0,0,0,0,0,4,4,4,4,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,4,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

ENEMY_SPAWNS = [
    (5.5, 10.5, 'zombie'), (10.5, 5.5, 'zombie'), (15.5, 8.5, 'demon'),
    (18.5, 18.5, 'zombie'), (8.5, 18.5, 'demon'), (12.5, 12.5, 'zombie'),
    (20.5, 4.5, 'zombie'), (4.5, 20.5, 'demon'), (7.5, 7.5, 'zombie'),
    (17.5, 14.5, 'demon'),
]

# Shade chars ordered near→far
SHADE_UNI   = ['█', '▓', '▒', '░', '·']
SHADE_ASCII = ['#', '@', '+', ':', '.']

# Wall type → color pair index
WALL_COLOR = {1: 3, 2: 4, 3: 3, 4: 1}

# ---------------------------------------------------------------------------
# Game objects
# ---------------------------------------------------------------------------

class Player:
    def __init__(self):
        self.x      = 2.5
        self.y      = 2.5
        self.angle  = 0.0
        self.health = 100
        self.ammo   = 50
        self.score  = 0


class Enemy:
    KINDS = {
        'zombie': dict(hp=30, speed=1.4, dmg=(4, 12), char='Z'),
        'demon':  dict(hp=60, speed=0.9, dmg=(8, 20), char='D'),
    }

    def __init__(self, x, y, kind='zombie'):
        k = self.KINDS[kind]
        self.x            = float(x)
        self.y            = float(y)
        self.kind         = kind
        self.health       = k['hp']
        self.speed        = k['speed']
        self.dmg          = k['dmg']
        self.char         = k['char']
        self.state        = 'patrol'     # patrol | chase | dead
        self.last_attack  = 0.0
        self.patrol_vx    = random.uniform(-0.6, 0.6)
        self.patrol_vy    = random.uniform(-0.6, 0.6)
        self.patrol_timer = random.uniform(1.0, 3.0)


# ---------------------------------------------------------------------------
# Core game
# ---------------------------------------------------------------------------

class Game:
    def __init__(self, stdscr):
        self.scr      = stdscr
        self.player   = Player()
        self.enemies  = [Enemy(x, y, k) for x, y, k in ENEMY_SPAWNS]
        self.messages = []    # list of (text, expire_float)
        self.last_t   = time.time()
        self.flash     = 0.0   # muzzle flash timer
        self.shoot_cd  = 0.0
        self.dmg_flash = 0.0   # red border on hit
        self.running  = True
        self.won      = False
        self._unicode = True
        self._setup()

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def _setup(self):
        curses.curs_set(0)
        curses.noecho()
        self.scr.nodelay(True)
        self.scr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED,     -1)   # danger / enemy
        curses.init_pair(2, curses.COLOR_WHITE,   -1)   # bright wall
        curses.init_pair(3, curses.COLOR_YELLOW,  -1)   # mid wall / HUD
        curses.init_pair(4, curses.COLOR_GREEN,   -1)   # far wall / ok
        curses.init_pair(5, curses.COLOR_CYAN,    -1)   # ceiling
        curses.init_pair(6, curses.COLOR_BLUE,    -1)   # floor
        curses.init_pair(7, curses.COLOR_MAGENTA, -1)   # flash / alert
        # Unicode probe
        try:
            self.scr.addstr(0, 0, '█')
            self.scr.erase()
        except Exception:
            self._unicode = False

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _wall(self, x, y) -> bool:
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= MAP_W or iy < 0 or iy >= MAP_H:
            return True
        return WORLD_MAP[iy][ix] != 0

    def _can_step(self, x, y, r=0.28) -> bool:
        return not (self._wall(x + r, y) or self._wall(x - r, y) or
                    self._wall(x, y + r) or self._wall(x, y - r))

    def _msg(self, text: str):
        self.messages.append((text, time.time() + 2.5))

    # -----------------------------------------------------------------------
    # Input
    # -----------------------------------------------------------------------

    def _input(self, dt: float):
        keys: set[int] = set()
        while True:
            k = self.scr.getch()
            if k == -1:
                break
            keys.add(k)

        if ord('q') in keys or 27 in keys:
            self.running = False
            return

        p = self.player
        spd = 3.8 * dt
        rot = 2.2 * dt

        dx = math.cos(p.angle)
        dy = math.sin(p.angle)

        if ord('w') in keys or curses.KEY_UP in keys:
            nx, ny = p.x + dx * spd, p.y + dy * spd
            if self._can_step(nx, p.y): p.x = nx
            if self._can_step(p.x, ny): p.y = ny

        if ord('s') in keys or curses.KEY_DOWN in keys:
            nx, ny = p.x - dx * spd, p.y - dy * spd
            if self._can_step(nx, p.y): p.x = nx
            if self._can_step(p.x, ny): p.y = ny

        if ord('a') in keys:
            nx, ny = p.x - dy * spd, p.y + dx * spd
            if self._can_step(nx, p.y): p.x = nx
            if self._can_step(p.x, ny): p.y = ny

        if ord('d') in keys:
            nx, ny = p.x + dy * spd, p.y - dx * spd
            if self._can_step(nx, p.y): p.x = nx
            if self._can_step(p.x, ny): p.y = ny

        if curses.KEY_LEFT  in keys: p.angle += rot
        if curses.KEY_RIGHT in keys: p.angle -= rot

        if ord(' ') in keys or ord('f') in keys:
            self._shoot()

    # -----------------------------------------------------------------------
    # Shooting
    # -----------------------------------------------------------------------

    def _shoot(self):
        if self.shoot_cd > 0:
            return
        p = self.player
        if p.ammo <= 0:
            self._msg("-- NO AMMO --")
            return

        p.ammo   -= 1
        self.shoot_cd = 0.25
        self.flash    = 0.12

        rdx = math.cos(p.angle)
        rdy = math.sin(p.angle)

        best_e, best_d = None, 22.0

        for e in self.enemies:
            if e.state == 'dead':
                continue
            ex, ey = e.x - p.x, e.y - p.y
            dist = math.sqrt(ex*ex + ey*ey)
            if dist < 0.3:
                continue
            dot  = ex * rdx + ey * rdy          # forward distance
            perp = abs(ex * rdy - ey * rdx)     # lateral offset
            if dot <= 0 or perp > 0.45 or dot >= best_d:
                continue
            # LOS: step along ray
            steps = max(4, int(dot / 0.2))
            blocked = any(
                self._wall(p.x + rdx * i * dot / steps,
                           p.y + rdy * i * dot / steps)
                for i in range(1, steps)
            )
            if not blocked:
                best_e, best_d = e, dot

        if best_e is None:
            self._msg("MISSED!")
            return

        dmg = random.randint(12, 28)
        best_e.health -= dmg
        best_e.state   = 'chase'
        if best_e.health <= 0:
            best_e.state  = 'dead'
            p.score       += 150
            self._msg(f"KILL! +150pts  [{best_d:.1f}m]")
        else:
            self._msg(f"HIT {best_e.char}  -{dmg}hp  [{best_d:.1f}m]")

    # -----------------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------------

    def update(self, dt: float):
        now = time.time()
        self.shoot_cd  = max(0.0, self.shoot_cd  - dt)
        self.flash     = max(0.0, self.flash     - dt)
        self.dmg_flash = max(0.0, self.dmg_flash - dt)
        self.messages  = [(m, t) for m, t in self.messages if t > now]

        alive = [e for e in self.enemies if e.state != 'dead']
        if not alive:
            self.won = self.running = False
            return

        p = self.player

        for e in alive:
            ex, ey = p.x - e.x, p.y - e.y
            dist = math.sqrt(ex*ex + ey*ey)

            # LOS → switch to chase
            if dist < 11.0 and e.state == 'patrol':
                steps = max(4, int(dist / 0.25))
                has_los = not any(
                    self._wall(e.x + ex * i / steps,
                               e.y + ey * i / steps)
                    for i in range(1, steps)
                )
                if has_los:
                    e.state = 'chase'

            if e.state == 'chase':
                if dist > 0.9:
                    mv = e.speed * dt / dist
                    nx, ny = e.x + ex * mv, e.y + ey * mv
                    if not self._wall(nx, e.y): e.x = nx
                    if not self._wall(e.x, ny): e.y = ny
                elif now - e.last_attack > 1.0:
                    dmg = random.randint(*e.dmg)
                    p.health       -= dmg
                    e.last_attack   = now
                    self.dmg_flash  = 0.55
                    self._msg(f"OUCH! -{dmg}hp")
                    if p.health <= 0:
                        self.running = False

            else:  # patrol
                e.patrol_timer -= dt
                if e.patrol_timer <= 0:
                    e.patrol_timer = random.uniform(1.0, 3.0)
                    e.patrol_vx    = random.uniform(-0.6, 0.6)
                    e.patrol_vy    = random.uniform(-0.6, 0.6)
                nx = max(1.0, min(MAP_W - 2.0, e.x + e.patrol_vx * dt))
                ny = max(1.0, min(MAP_H - 2.0, e.y + e.patrol_vy * dt))
                if not self._wall(nx, e.y): e.x = nx
                if not self._wall(e.x, ny): e.y = ny

    # -----------------------------------------------------------------------
    # Raycasting (DDA)
    # -----------------------------------------------------------------------

    def _cast(self, col: int, w: int):
        """Return (perp_dist, wall_type, side) for screen column `col`."""
        p   = self.player
        dx  = math.cos(p.angle)
        dy  = math.sin(p.angle)
        # Camera plane perpendicular to view direction, scaled for ~66° FOV
        px  =  0.66 * dy
        py  = -0.66 * dx

        cam  = 2.0 * col / max(w - 1, 1) - 1.0
        rdx  = dx + px * cam
        rdy  = dy + py * cam

        mx, my = int(p.x), int(p.y)

        ddx = abs(1.0 / rdx) if rdx else 1e30
        ddy = abs(1.0 / rdy) if rdy else 1e30
        sx  = 1  if rdx >= 0 else -1
        sy  = 1  if rdy >= 0 else -1
        sdx = (mx + 1 - p.x) * ddx if rdx >= 0 else (p.x - mx) * ddx
        sdy = (my + 1 - p.y) * ddy if rdy >= 0 else (p.y - my) * ddy

        side = 0
        for _ in range(64):
            if sdx < sdy:
                sdx += ddx; mx += sx; side = 0
            else:
                sdy += ddy; my += sy; side = 1
            if 0 <= mx < MAP_W and 0 <= my < MAP_H and WORLD_MAP[my][mx]:
                wt = WORLD_MAP[my][mx]
                d  = (sdx - ddx) if side == 0 else (sdy - ddy)
                return max(0.05, d), wt, side

        return 64.0, 1, 0

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------

    def render(self):
        scr = self.scr
        h, w = scr.getmaxyx()
        if h < 12 or w < 40:
            try:
                scr.addstr(0, 0, "Terminal too small (need 40×12)")
            except curses.error:
                pass
            return

        scr.erase()

        view_h = h - 3        # rows reserved for HUD
        half_h = view_h // 2
        shade  = SHADE_UNI if self._unicode else SHADE_ASCII
        dot    = '·' if self._unicode else '.'

        # Ceiling & floor
        for row in range(half_h):
            try: scr.addstr(row, 0, dot * (w - 1), curses.color_pair(5))
            except curses.error: pass
        for row in range(half_h, view_h):
            try: scr.addstr(row, 0, dot * (w - 1), curses.color_pair(6))
            except curses.error: pass

        z_buf = [999.0] * w

        # Walls
        for col in range(w - 1):
            dist, wtype, side = self._cast(col, w)
            z_buf[col] = dist

            wh  = min(int(view_h / dist), view_h)
            top = max(0,      half_h - wh // 2)
            bot = min(view_h, half_h + wh // 2)

            si  = min(int(dist / 2.8), len(shade) - 1)
            ch  = shade[si]
            cp  = WALL_COLOR.get(wtype, 3)
            if side == 1:
                cp = max(1, cp - 1)     # darker N/S faces
            attr = curses.color_pair(cp) | (curses.A_BOLD if dist < 2.5 else 0)

            for row in range(top, bot):
                try: scr.addstr(row, col, ch, attr)
                except curses.error: pass

        # Enemy sprites
        self._draw_enemies(z_buf, w, view_h, half_h)

        # Crosshair
        cy, cx = view_h // 2, w // 2
        xcol = curses.color_pair(7) | curses.A_BOLD if self.flash > 0 \
               else curses.color_pair(2)
        try:
            scr.addstr(cy,     cx - 1, '-+-', xcol)
            scr.addstr(cy - 1, cx,     '|',   xcol)
            scr.addstr(cy + 1, cx,     '|',   xcol)
        except curses.error:
            pass

        self._draw_gun(view_h, w)
        self._draw_minimap(w)
        self._draw_hud(h, w, view_h)
        self._draw_damage_border(view_h, w)

        # Combat messages (top-left, skip minimap area)
        for i, (msg, _) in enumerate(self.messages[-3:]):
            try:
                scr.addstr(1 + i, 1, msg[:38], curses.color_pair(7) | curses.A_BOLD)
            except curses.error:
                pass

        scr.refresh()

    def _draw_enemies(self, z_buf, w, view_h, half_h):
        p   = self.player
        dx  = math.cos(p.angle);  dy = math.sin(p.angle)
        px  =  0.66 * dy;         py = -0.66 * dx
        # inv of camera matrix  (det is always 0.66)
        inv = 1.0 / (px * dy - dx * py)

        visible = []
        for e in self.enemies:
            if e.state == 'dead':
                continue
            ex, ey  = e.x - p.x, e.y - p.y
            tx  = inv * ( dy * ex - dx * ey)   # strafe offset
            tz  = inv * (-py * ex + px * ey)   # depth (must be > 0)
            if tz <= 0.1:
                continue
            sx  = int((w / 2) * (1.0 + tx / tz))
            sh  = min(abs(int(view_h / tz)), view_h)
            visible.append((tz, e, sx, sh))

        for depth, e, sx, sh in sorted(visible, key=lambda v: -v[0]):
            sw  = max(1, sh // 2)
            top = half_h - sh // 2
            for cx_off in range(-sw // 2, sw // 2 + 1):
                col = sx + cx_off
                if col < 0 or col >= w - 1 or z_buf[col] <= depth:
                    continue
                for row_off in range(sh):
                    row = top + row_off
                    if row < 0 or row >= view_h:
                        continue
                    ry = row_off / sh
                    if   ry < 0.18: ch = 'O'
                    elif ry < 0.22: ch = '-'
                    elif ry < 0.65: ch = e.char
                    elif ry < 0.80: ch = '|'
                    else:           continue
                    try:
                        self.scr.addstr(row, col, ch,
                            curses.color_pair(1) | curses.A_BOLD)
                    except curses.error:
                        pass

    def _draw_minimap(self, w):
        size  = 13
        ox    = w - size - 2
        oy    = 0
        scale = size / MAP_W

        for my in range(size):
            for mx in range(size):
                gx = min(MAP_W - 1, int(mx / scale))
                gy = min(MAP_H - 1, int(my / scale))
                ch    = '#' if WORLD_MAP[gy][gx] else ' '
                color = curses.color_pair(3) if WORLD_MAP[gy][gx] else 0
                try: self.scr.addstr(oy + my, ox + mx, ch, color)
                except curses.error: pass

        # Player dot + direction indicator
        ppx = int(self.player.x * scale)
        ppy = int(self.player.y * scale)
        if 0 <= ppx < size and 0 <= ppy < size:
            try:
                self.scr.addstr(oy + ppy, ox + ppx, '@',
                    curses.color_pair(4) | curses.A_BOLD)
            except curses.error:
                pass

        # Two look-ahead dots showing direction
        dot_ch = '·' if self._unicode else '.'
        for step in (2.0, 3.5):
            fx = int((self.player.x + math.cos(self.player.angle) * step) * scale)
            fy = int((self.player.y + math.sin(self.player.angle) * step) * scale)
            if 0 <= fx < size and 0 <= fy < size and (fx != ppx or fy != ppy):
                try:
                    self.scr.addstr(oy + fy, ox + fx, dot_ch,
                        curses.color_pair(4) | curses.A_BOLD)
                except curses.error:
                    pass

        # Enemy dots
        for e in self.enemies:
            if e.state == 'dead':
                continue
            ex = int(e.x * scale)
            ey = int(e.y * scale)
            if 0 <= ex < size and 0 <= ey < size:
                try:
                    self.scr.addstr(oy + ey, ox + ex, '!',
                        curses.color_pair(1))
                except curses.error:
                    pass

    def _draw_gun(self, view_h, w):
        """Draw weapon sprite at bottom-centre of the 3D view."""
        cx = w // 2
        firing = self.flash > 0
        col = curses.color_pair(3) | curses.A_BOLD

        if firing:
            # Muzzle flash above barrel
            flashes = [' *!*!* ', '  *!*  ', '   !   ']
            fi = int((0.12 - self.flash) / 0.04) % len(flashes)
            try:
                self.scr.addstr(view_h - 5, cx - 3,
                    flashes[fi], curses.color_pair(7) | curses.A_BOLD)
            except curses.error:
                pass
            gun_lines = ['  ___  ', ' /===\\ ', '[=====]']
            base_row  = view_h - 4
        else:
            gun_lines = ['  ___  ', ' /===\\ ', '[=====]']
            base_row  = view_h - 3

        for i, line in enumerate(gun_lines):
            try:
                self.scr.addstr(base_row + i, cx - 3, line, col)
            except curses.error:
                pass

    def _draw_damage_border(self, view_h, w):
        """Flash red border on the sides and top/bottom when player is hit."""
        if self.dmg_flash <= 0:
            return
        t      = self.dmg_flash / 0.55   # 1.0 → 0.0
        cols   = max(1, int(t * 5))
        rows   = max(1, int(t * 3))
        side   = '▌' if self._unicode else '|'
        top_c  = '▄' if self._unicode else '-'
        bot_c  = '▀' if self._unicode else '-'
        attr   = curses.color_pair(1) | curses.A_BOLD

        for row in range(view_h):
            for c in range(cols):
                try:
                    self.scr.addstr(row, c,             side, attr)
                    self.scr.addstr(row, w - 2 - c,     side, attr)
                except curses.error:
                    pass

        strip = top_c * (w - 1) if self._unicode else top_c * (w - 1)
        for r in range(rows):
            try:
                self.scr.addstr(r,              0, strip[:w-1], attr)
                self.scr.addstr(view_h - 1 - r, 0, strip[:w-1], attr)
            except curses.error:
                pass

    def _draw_hud(self, h, w, view_h):
        p       = self.player
        y       = view_h
        hp_pct  = max(0, p.health) / 100.0
        bw      = 12
        filled  = int(hp_pct * bw)
        if self._unicode:
            bar = '█' * filled + '░' * (bw - filled)
        else:
            bar = '#' * filled + '-' * (bw - filled)

        hp_col  = curses.color_pair(1) if hp_pct < 0.3 else curses.color_pair(4)
        sep     = '─' * (w - 1) if self._unicode else '-' * (w - 1)
        alive   = sum(1 for e in self.enemies if e.state != 'dead')

        try:
            self.scr.addstr(y,     0,  sep, curses.color_pair(3))
            self.scr.addstr(y + 1, 1,
                f'HP[{bar}]{p.health:3d}', hp_col | curses.A_BOLD)
            self.scr.addstr(y + 1, 22, f'AMMO:{p.ammo:3d}',
                curses.color_pair(3) | curses.A_BOLD)
            self.scr.addstr(y + 1, 32, f'SCORE:{p.score}',
                curses.color_pair(4) | curses.A_BOLD)
            self.scr.addstr(y + 2, 1,
                f'ENEMIES:{alive:2d}/{len(self.enemies)}',
                curses.color_pair(1))
            self.scr.addstr(y + 2, 18,
                'W/S:fwd/back  A/D:strafe  ←→:turn  SPC:fire  Q:quit',
                curses.color_pair(6))
        except curses.error:
            pass

    # -----------------------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------------------

    def run(self):
        self.last_t = time.time()
        target      = 1.0 / 35.0

        while self.running:
            now = time.time()
            dt  = min(now - self.last_t, 0.05)
            self.last_t = now

            self._input(dt)
            self.update(dt)
            self.render()

            wait = target - (time.time() - now)
            if wait > 0:
                time.sleep(wait)

        self._end_screen()

    def _end_screen(self):
        scr = self.scr
        h, w = scr.getmaxyx()
        scr.erase()

        if self.won:
            title = "  YOU WIN!  "
            color = curses.color_pair(4) | curses.A_BOLD
        else:
            title = "  GAME OVER  "
            color = curses.color_pair(1) | curses.A_BOLD

        lines = [
            title,
            f"Final score: {self.player.score}",
            f"Kills: {sum(1 for e in self.enemies if e.state == 'dead')}"
              f"/{len(self.enemies)}",
            "",
            "Press any key to exit...",
        ]
        cy = h // 2 - len(lines) // 2
        for i, line in enumerate(lines):
            try:
                scr.addstr(cy + i, w // 2 - len(line) // 2, line, color)
            except curses.error:
                pass

        scr.refresh()
        scr.nodelay(False)
        scr.getch()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(stdscr):
    Game(stdscr).run()


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
