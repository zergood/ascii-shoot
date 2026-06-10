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

PICKUP_SPAWNS = [
    (6.5, 6.5, 'hp'), (14.5, 3.5, 'hp'), (3.5, 14.5, 'hp'),
    (20.5, 20.5, 'hp'), (10.5, 13.5, 'hp'),
    (2.5, 7.5, 'ammo'), (12.5, 2.5, 'ammo'), (21.5, 5.5, 'ammo'),
    (5.5, 20.5, 'ammo'), (17.5, 11.5, 'ammo'),
]

SHADE_UNI   = ['█', '▓', '▒', '░', '·']
SHADE_ASCII = ['#', '@', '+', ':', '.']
WALL_COLOR  = {1: 3, 2: 4, 3: 3, 4: 1}


# ---------------------------------------------------------------------------
# World  — map data + spatial queries, no curses
# ---------------------------------------------------------------------------

class World:
    """Map grid plus collision and raycasting helpers."""

    def __init__(self, grid=None):
        self.grid = grid if grid is not None else WORLD_MAP
        self.h    = len(self.grid)
        self.w    = len(self.grid[0]) if self.h else 0

    def is_wall(self, x: float, y: float) -> bool:
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.w or iy < 0 or iy >= self.h:
            return True
        return self.grid[iy][ix] != 0

    def cell_type(self, x: float, y: float) -> int:
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.w or iy < 0 or iy >= self.h:
            return 1
        return self.grid[iy][ix]

    def can_step(self, x: float, y: float, r: float = 0.28) -> bool:
        return not (self.is_wall(x + r, y) or self.is_wall(x - r, y) or
                    self.is_wall(x, y + r) or self.is_wall(x, y - r))

    def has_los(self, x1: float, y1: float,
                x2: float, y2: float) -> bool:
        """True when (x1,y1)→(x2,y2) has no wall in between."""
        ex, ey = x2 - x1, y2 - y1
        dist   = math.sqrt(ex * ex + ey * ey)
        steps  = max(4, int(dist / 0.2))
        return not any(
            self.is_wall(x1 + ex * i / steps,
                         y1 + ey * i / steps)
            for i in range(1, steps)
        )

    def cast_ray(self, px: float, py: float, view_angle: float,
                 col: int, screen_w: int):
        """DDA raycasting. Returns (dist, wall_type, side, wall_x)."""
        dx  = math.cos(view_angle)
        dy  = math.sin(view_angle)
        plx =  0.66 * dy
        ply = -0.66 * dx

        cam = 2.0 * col / max(screen_w - 1, 1) - 1.0
        rdx = dx + plx * cam
        rdy = dy + ply * cam

        mx, my = int(px), int(py)
        ddx = abs(1.0 / rdx) if rdx else 1e30
        ddy = abs(1.0 / rdy) if rdy else 1e30
        sx  = 1 if rdx >= 0 else -1
        sy  = 1 if rdy >= 0 else -1
        sdx = (mx + 1 - px) * ddx if rdx >= 0 else (px - mx) * ddx
        sdy = (my + 1 - py) * ddy if rdy >= 0 else (py - my) * ddy

        side = 0
        for _ in range(64):
            if sdx < sdy:
                sdx += ddx; mx += sx; side = 0
            else:
                sdy += ddy; my += sy; side = 1
            if 0 <= mx < self.w and 0 <= my < self.h and self.grid[my][mx]:
                wt = self.grid[my][mx]
                d  = max(0.05, (sdx - ddx) if side == 0 else (sdy - ddy))
                wx = (py + d * rdy) if side == 0 else (px + d * rdx)
                wx -= math.floor(wx)
                return d, wt, side, wx

        return 64.0, 1, 0, 0.5


# ---------------------------------------------------------------------------
# Game objects  — no curses
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
        self.cpair        = 1 if kind == 'zombie' else 7
        self.state        = 'patrol'
        self.last_attack  = 0.0
        self.patrol_vx    = random.uniform(-0.6, 0.6)
        self.patrol_vy    = random.uniform(-0.6, 0.6)
        self.patrol_timer = random.uniform(1.0, 3.0)

    def update(self, dt: float, player, world: World, now: float) -> int:
        """Update AI. Returns damage dealt this frame (0 if none)."""
        if self.state == 'dead':
            return 0

        ex   = player.x - self.x
        ey   = player.y - self.y
        dist = math.sqrt(ex * ex + ey * ey)

        if dist < 11.0 and self.state == 'patrol':
            if world.has_los(self.x, self.y, player.x, player.y):
                self.state = 'chase'

        if self.state == 'chase':
            if dist > 0.9:
                mv = self.speed * dt / dist
                nx = self.x + ex * mv
                ny = self.y + ey * mv
                if not world.is_wall(nx, self.y): self.x = nx
                if not world.is_wall(self.x, ny): self.y = ny
            elif now - self.last_attack > 1.0:
                self.last_attack = now
                return random.randint(*self.dmg)
        else:  # patrol
            self.patrol_timer -= dt
            if self.patrol_timer <= 0:
                self.patrol_timer = random.uniform(1.0, 3.0)
                self.patrol_vx    = random.uniform(-0.6, 0.6)
                self.patrol_vy    = random.uniform(-0.6, 0.6)
            nx = max(1.0, min(world.w - 2.0, self.x + self.patrol_vx * dt))
            ny = max(1.0, min(world.h - 2.0, self.y + self.patrol_vy * dt))
            if not world.is_wall(nx, self.y): self.x = nx
            if not world.is_wall(self.x, ny): self.y = ny

        return 0


# ---------------------------------------------------------------------------
# Renderer  — owns the curses screen, reads game state, never writes it
# ---------------------------------------------------------------------------

class Renderer:

    def __init__(self, scr, quality: str = 'normal'):
        self.scr     = scr
        self.quality = quality
        self._unicode = True
        self._low    = False   # computed in setup()
        self._hires  = False   # computed in setup()
        self.shade   = SHADE_ASCII
        self._hb     = {}      # (fg_color, bg_color) → pair index

    def setup(self):
        curses.curs_set(0)
        curses.noecho()
        self.scr.nodelay(True)
        self.scr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED,     -1)
        curses.init_pair(2, curses.COLOR_WHITE,   -1)
        curses.init_pair(3, curses.COLOR_YELLOW,  -1)
        curses.init_pair(4, curses.COLOR_GREEN,   -1)
        curses.init_pair(5, curses.COLOR_CYAN,    -1)
        curses.init_pair(6, curses.COLOR_BLUE,    -1)
        curses.init_pair(7, curses.COLOR_MAGENTA, -1)
        try:
            self.scr.addstr(0, 0, '█')
            self.scr.erase()
        except Exception:
            self._unicode = False
        # Pre-compute quality flags once
        self._low   = self.quality == 'low'
        self._hires = self.quality == 'high' and self._unicode
        self.shade  = SHADE_ASCII if self._low or not self._unicode else SHADE_UNI
        if self._hires:
            n = 10
            for fg in [curses.COLOR_WHITE,  curses.COLOR_YELLOW,
                       curses.COLOR_GREEN,  curses.COLOR_RED]:
                for bg in [curses.COLOR_CYAN, curses.COLOR_BLUE]:
                    curses.init_pair(n, fg, bg)
                    self._hb[(fg, bg)] = n
                    n += 1

    # ---- Main render entry -------------------------------------------------

    def render(self, game, now: float):
        scr = self.scr
        h, w = scr.getmaxyx()
        if h < 12 or w < 40:
            try: scr.addstr(0, 0, "Terminal too small (need 40×12)")
            except curses.error: pass
            return

        scr.erase()
        view_h = h - 3
        half_h = view_h // 2

        shake_off  = (random.uniform(-game.hit_shake, game.hit_shake)
                      if game.hit_shake > 0.005 else 0.0)
        view_angle = game.player.angle + game.recoil + shake_off

        self._draw_sky_floor(scr, view_h, half_h, w)

        z_buf = [999.0] * w
        self._draw_floor_casting(scr, game.player.x, game.player.y,
                                 view_angle, view_h, half_h, w)
        self._draw_walls(scr, game.world, game.player,
                         view_angle, view_h, half_h, w, z_buf)
        self._draw_live_enemies(scr, game, z_buf, view_angle,
                                view_h, half_h, w, now)
        self._draw_floor_objects(scr, game, z_buf, view_angle,
                                 view_h, half_h, w)
        self._draw_crosshair(scr, game.flash, view_h, w)
        self._draw_gun(scr, game, view_h, w)
        self._draw_minimap(scr, game, w)
        self._draw_hud(scr, game, h, w, view_h)
        self._draw_damage_border(scr, game.dmg_flash, view_h, w)
        self._draw_messages(scr, game.messages)
        scr.refresh()

    # ---- Sky / floor background --------------------------------------------

    def _draw_sky_floor(self, scr, view_h, half_h, w):
        if self._hires:
            ceil_g  = [' ', ' ', '·', '░']
            floor_g = ['▒', '░', '·', ' ']
            for row in range(half_h):
                idx = min(3, int(row / max(1, half_h) * 4))
                try: scr.addstr(row, 0, ceil_g[idx] * (w - 1),
                                curses.color_pair(5))
                except curses.error: pass
            for row in range(half_h, view_h):
                idx = min(3, int((row - half_h) /
                                 max(1, view_h - half_h) * 4))
                try: scr.addstr(row, 0, floor_g[idx] * (w - 1),
                                curses.color_pair(6))
                except curses.error: pass
        else:
            ceil_ch = '·' if self._unicode and not self._low else ' '
            for row in range(half_h):
                try: scr.addstr(row, 0, ceil_ch * (w - 1),
                                curses.color_pair(5))
                except curses.error: pass
            for row in range(half_h, view_h):
                try: scr.addstr(row, 0, ' ' * (w - 1),
                                curses.color_pair(6))
                except curses.error: pass

    # ---- Floor casting (perspective grid) ----------------------------------

    def _draw_floor_casting(self, scr, px, py, view_angle,
                            view_h, half_h, w):
        if self._low or not self._unicode:
            return
        dx  = math.cos(view_angle);  dy  = math.sin(view_angle)
        plx =  0.66 * dy;            ply = -0.66 * dx
        rl_x = dx - plx;  rl_y = dy - ply
        rr_x = dx + plx;  rr_y = dy + ply
        inv_w  = 1.0 / max(w - 2, 1)
        stride = 1 if self._hires else 2
        fattr  = curses.color_pair(6) | curses.A_BOLD
        for row in range(half_h + 1, view_h):
            rd  = (view_h * 0.5) / (row - half_h)
            fx  = px + rd * rl_x;  fy  = py + rd * rl_y
            fsx = rd * (rr_x - rl_x) * inv_w
            fsy = rd * (rr_y - rl_y) * inv_w
            thr = max(0.05, 0.14 - rd * 0.01)
            cx  = fx;  cy = fy
            for col in range(0, w - 1, stride):
                frx = cx - math.floor(cx)
                fry = cy - math.floor(cy)
                if (frx < thr or frx > 1.0 - thr or
                        fry < thr or fry > 1.0 - thr):
                    try: scr.addstr(row, col, '·', fattr)
                    except curses.error: pass
                cx += fsx * stride
                cy += fsy * stride

    # ---- Walls -------------------------------------------------------------

    def _draw_walls(self, scr, world, player, view_angle,
                    view_h, half_h, w, z_buf):
        shade    = self.shade
        ray_step = 4 if self._low else 1
        _CP_TO_CLR = {1: curses.COLOR_RED,   2: curses.COLOR_WHITE,
                      3: curses.COLOR_YELLOW, 4: curses.COLOR_GREEN}

        for col in range(0, w - 1, ray_step):
            dist, wtype, side, wall_x = world.cast_ray(
                player.x, player.y, view_angle, col, w)

            wh  = min(int(view_h / dist), view_h)
            top = max(0,      half_h - wh // 2)
            bot = min(view_h, half_h + wh // 2)

            si  = min(int(dist / 2.8), len(shade) - 1)
            ch  = shade[si]
            cp  = WALL_COLOR.get(wtype, 3)
            if side == 1:
                cp = max(1, cp - 1)

            fog  = not self._low and dist > 7.0
            attr = (curses.color_pair(cp)
                    | (curses.A_BOLD if dist < 2.5 else
                       curses.A_DIM  if fog else 0))

            wall_h = max(1, bot - top)
            for c in range(col, min(col + ray_step, w - 1)):
                z_buf[c] = dist
                for row in range(top, bot):
                    if not self._low and self._unicode:
                        row_f    = (row - top) / wall_h
                        brick_r  = int(row_f * 3)
                        offset   = 0.5 if brick_r % 2 else 0.0
                        mortar_x = ((wall_x + offset) * 2) % 1.0
                        mortar_y = (row_f * 3) % 1.0
                        is_mortar = (mortar_y < 0.10 or
                                     mortar_x < 0.07 or mortar_x > 0.93)
                        tex = shade[min(len(shade)-1, si+1)] if is_mortar else ch
                    else:
                        tex = ch
                    try: scr.addstr(row, c, tex, attr)
                    except curses.error: pass

            if self._hires:
                wh_f  = min(view_h / dist, view_h * 2.0)
                top_f = half_h - wh_f / 2
                bot_f = half_h + wh_f / 2
                top_i, bot_i   = int(top_f), int(bot_f)
                top_fr, bot_fr = top_f - top_i, bot_f - bot_i
                wc = _CP_TO_CLR.get(cp, curses.COLOR_YELLOW)
                if 0 <= top_i < view_h and top_fr > 0.5:
                    p = self._hb.get((wc, curses.COLOR_CYAN), 5)
                    try: scr.addstr(top_i, col, '▄', curses.color_pair(p))
                    except curses.error: pass
                if 0 <= bot_i < view_h and 0 < bot_fr < 0.5:
                    p = self._hb.get((wc, curses.COLOR_BLUE), 6)
                    try: scr.addstr(bot_i, col, '▀', curses.color_pair(p))
                    except curses.error: pass

    # ---- Live enemy sprites ------------------------------------------------

    def _draw_live_enemies(self, scr, game, z_buf, view_angle,
                           view_h, half_h, w, now):
        p     = game.player
        frame = int(now * 5) % 2
        dx    = math.cos(view_angle);  dy = math.sin(view_angle)
        px    =  0.66 * dy;            py = -0.66 * dx
        inv   = 1.0 / (px * dy - dx * py)

        def _proj(ox, oy):
            ex, ey = ox - p.x, oy - p.y
            tx = inv * ( dy * ex - dx * ey)
            tz = inv * (-py * ex + px * ey)
            return tx, tz

        visible = []
        for e in game.enemies:
            if e.state == 'dead':
                continue
            tx, tz = _proj(e.x, e.y)
            if tz <= 0.1:
                continue
            sx = int((w / 2) * (1.0 + tx / tz))
            sh = min(abs(int(view_h / tz)), view_h)
            visible.append((tz, e, sx, sh))

        max_sw = max(1, w // 8)
        for depth, e, sx, sh in sorted(visible, key=lambda v: -v[0]):
            sw   = min(max(1, sh // 2), max_sw)
            top  = half_h - sh // 2
            attr = curses.color_pair(e.cpair) | curses.A_BOLD
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
                    elif ry < 0.80:
                        ch = ('\\' if frame else '/') if e.state == 'chase' else '|'
                    else:           continue
                    try: scr.addstr(row, col, ch, attr)
                    except curses.error: pass

    # ---- Floor objects (corpses + pickups) ---------------------------------

    def _draw_floor_objects(self, scr, game, z_buf, view_angle,
                            view_h, half_h, w):
        p   = game.player
        dx  = math.cos(view_angle);  dy = math.sin(view_angle)
        px  =  0.66 * dy;            py = -0.66 * dx
        inv = 1.0 / (px * dy - dx * py)

        def _proj(ox, oy):
            ex, ey = ox - p.x, oy - p.y
            tx = inv * ( dy * ex - dx * ey)
            tz = inv * (-py * ex + px * ey)
            return tx, tz

        objs = (
            [(cx, cy, '%', curses.color_pair(1))
             for cx, cy in game.corpses] +
            [(px2, py2, '+' if k == 'hp' else '*',
              curses.color_pair(4) if k == 'hp' else curses.color_pair(3))
             for px2, py2, k in game.pickups]
        )
        for ox, oy, fch, fattr in objs:
            tx, tz = _proj(ox, oy)
            if tz <= 0.1:
                continue
            sx  = int((w / 2) * (1.0 + tx / tz))
            sh  = min(abs(int(view_h / tz)), view_h)
            row = min(view_h - 1, half_h + sh // 3)
            if 0 <= sx < w - 1 and z_buf[sx] > tz:
                try: scr.addstr(row, sx, fch, fattr | curses.A_BOLD)
                except curses.error: pass

    # ---- Crosshair ---------------------------------------------------------

    def _draw_crosshair(self, scr, flash, view_h, w):
        cy, cx = view_h // 2, w // 2
        xcol = (curses.color_pair(7) | curses.A_BOLD
                if flash > 0 else curses.color_pair(2))
        try:
            scr.addstr(cy,     cx - 1, '-+-', xcol)
            scr.addstr(cy - 1, cx,     '|',   xcol)
            scr.addstr(cy + 1, cx,     '|',   xcol)
        except curses.error:
            pass

    # ---- Gun sprite --------------------------------------------------------

    def _draw_gun(self, scr, game, view_h, w):
        if self._low:
            return
        cx     = w // 2
        firing = game.flash > 0
        col    = curses.color_pair(3) | curses.A_BOLD

        bob = 0
        if game._is_moving and not firing:
            bob = round(math.sin(game._walk_timer * 8.0) * 1.3)

        gun_lines = ['  ___  ', ' /===\\ ', '[=====]']
        if firing:
            flashes  = [' *!*!* ', '  *!*  ', '   !   ']
            fi = int((0.12 - game.flash) / 0.04) % len(flashes)
            try: scr.addstr(view_h - 5, cx - 3,
                            flashes[fi], curses.color_pair(7) | curses.A_BOLD)
            except curses.error: pass
            base_row = view_h - 4
        else:
            base_row = view_h - 3

        base_row += bob
        for i, line in enumerate(gun_lines):
            try: scr.addstr(base_row + i, cx - 3, line, col)
            except curses.error: pass

    # ---- Minimap -----------------------------------------------------------

    def _draw_minimap(self, scr, game, w):
        size  = 13
        ox    = w - size - 2
        oy    = 0
        scale = size / MAP_W

        for my in range(size):
            for mx in range(size):
                gx = min(MAP_W - 1, int(mx / scale))
                gy = min(MAP_H - 1, int(my / scale))
                ch    = '#' if game.world.grid[gy][gx] else ' '
                color = curses.color_pair(3) if game.world.grid[gy][gx] else 0
                try: scr.addstr(oy + my, ox + mx, ch, color)
                except curses.error: pass

        for px2, py2, kind in game.pickups:
            mx = int(px2 * scale);  my = int(py2 * scale)
            if 0 <= mx < size and 0 <= my < size:
                ch    = '+' if kind == 'hp' else '*'
                color = (curses.color_pair(4) if kind == 'hp'
                         else curses.color_pair(3))
                try: scr.addstr(oy + my, ox + mx, ch, color)
                except curses.error: pass

        for cx2, cy2 in game.corpses:
            mx = int(cx2 * scale);  my = int(cy2 * scale)
            if 0 <= mx < size and 0 <= my < size:
                try: scr.addstr(oy + my, ox + mx, 'x', curses.color_pair(1))
                except curses.error: pass

        ppx = int(game.player.x * scale)
        ppy = int(game.player.y * scale)
        if 0 <= ppx < size and 0 <= ppy < size:
            try: scr.addstr(oy + ppy, ox + ppx, '@',
                            curses.color_pair(4) | curses.A_BOLD)
            except curses.error: pass

        fov_half = math.atan(0.66)
        dot_ch   = '·' if self._unicode else '.'
        for dist in (2.0, 3.5, 5.0):
            for ao in (-fov_half, fov_half):
                fx = int((game.player.x +
                          math.cos(game.player.angle + ao) * dist) * scale)
                fy = int((game.player.y +
                          math.sin(game.player.angle + ao) * dist) * scale)
                if 0 <= fx < size and 0 <= fy < size:
                    try: scr.addstr(oy + fy, ox + fx, '.', curses.color_pair(5))
                    except curses.error: pass
        for dist in (1.5, 2.5, 3.5):
            fx = int((game.player.x +
                      math.cos(game.player.angle) * dist) * scale)
            fy = int((game.player.y +
                      math.sin(game.player.angle) * dist) * scale)
            if 0 <= fx < size and 0 <= fy < size and (fx != ppx or fy != ppy):
                try: scr.addstr(oy + fy, ox + fx, dot_ch,
                                curses.color_pair(4) | curses.A_BOLD)
                except curses.error: pass

        for e in game.enemies:
            if e.state == 'dead':
                continue
            ex = int(e.x * scale);  ey = int(e.y * scale)
            if 0 <= ex < size and 0 <= ey < size:
                try: scr.addstr(oy + ey, ox + ex, '!', curses.color_pair(1))
                except curses.error: pass

    # ---- HUD ---------------------------------------------------------------

    def _draw_hud(self, scr, game, h, w, view_h):
        p      = game.player
        y      = view_h
        hp_pct = max(0, p.health) / 100.0
        bw     = 12
        filled = int(hp_pct * bw)
        bar    = ('█' * filled + '░' * (bw - filled) if self._unicode
                  else '#' * filled + '-' * (bw - filled))
        hp_col = curses.color_pair(1) if hp_pct < 0.3 else curses.color_pair(4)
        sep    = '─' * (w - 1) if self._unicode else '-' * (w - 1)
        alive  = sum(1 for e in game.enemies if e.state != 'dead')
        try:
            scr.addstr(y,     0,  sep, curses.color_pair(3))
            scr.addstr(y + 1, 1,  f'HP[{bar}]{p.health:3d}',
                       hp_col | curses.A_BOLD)
            scr.addstr(y + 1, 22, f'AMMO:{p.ammo:3d}',
                       curses.color_pair(3) | curses.A_BOLD)
            scr.addstr(y + 1, 32, f'SCORE:{p.score}',
                       curses.color_pair(4) | curses.A_BOLD)
            scr.addstr(y + 2, 1,  f'ENEMIES:{alive:2d}/{len(game.enemies)}',
                       curses.color_pair(1))
            scr.addstr(y + 2, 18,
                       'W/S:fwd/back  A/D:strafe  ←→:turn  SPC:fire  Q:quit',
                       curses.color_pair(6))
        except curses.error:
            pass

    # ---- Damage border -----------------------------------------------------

    def _draw_damage_border(self, scr, dmg_flash, view_h, w):
        if dmg_flash <= 0:
            return
        t    = dmg_flash / 0.55
        cols = max(1, int(t * 5))
        rows = max(1, int(t * 3))
        side = '▌' if self._unicode else '|'
        top_c = '▄' if self._unicode else '-'
        attr  = curses.color_pair(1) | curses.A_BOLD
        for row in range(view_h):
            for c in range(cols):
                try:
                    scr.addstr(row, c,         side, attr)
                    scr.addstr(row, w - 2 - c, side, attr)
                except curses.error: pass
        strip = top_c * (w - 1)
        for r in range(rows):
            try:
                scr.addstr(r,              0, strip[:w-1], attr)
                scr.addstr(view_h - 1 - r, 0, strip[:w-1], attr)
            except curses.error: pass

    # ---- Messages ----------------------------------------------------------

    def _draw_messages(self, scr, messages):
        for i, (msg, _) in enumerate(messages[-3:]):
            try: scr.addstr(1 + i, 1, msg[:38],
                            curses.color_pair(7) | curses.A_BOLD)
            except curses.error: pass

    # ---- End screen --------------------------------------------------------

    def end_screen(self, game):
        scr = self.scr
        h, w = scr.getmaxyx()
        scr.erase()
        if game.won:
            title = "  YOU WIN!  "
            color = curses.color_pair(4) | curses.A_BOLD
        else:
            title = "  GAME OVER  "
            color = curses.color_pair(1) | curses.A_BOLD
        lines = [
            title,
            f"Final score: {game.player.score}",
            (f"Kills: {sum(1 for e in game.enemies if e.state == 'dead')}"
             f"/{len(game.enemies)}"),
            "",
            "Press any key to exit...",
        ]
        cy = h // 2 - len(lines) // 2
        for i, line in enumerate(lines):
            try: scr.addstr(cy + i, w // 2 - len(line) // 2, line, color)
            except curses.error: pass
        scr.refresh()
        scr.nodelay(False)
        scr.getch()


# ---------------------------------------------------------------------------
# Game  — coordinator, no curses code
# ---------------------------------------------------------------------------

class Game:

    def __init__(self, stdscr, quality: str = 'normal'):
        self.world   = World()
        self.player  = Player()
        self.enemies = [Enemy(x, y, k) for x, y, k in ENEMY_SPAWNS]
        self.pickups = list(PICKUP_SPAWNS)
        self.corpses = []
        self.messages = []
        self.running  = True
        self.won      = False

        # Visual-effect timers — written by game logic, read by Renderer
        self.flash      = 0.0
        self.shoot_cd   = 0.0
        self.dmg_flash  = 0.0
        self.recoil     = 0.0
        self.hit_shake  = 0.0
        self._is_moving  = False
        self._walk_timer = 0.0

        self.renderer = Renderer(stdscr, quality)
        self.renderer.setup()
        self.last_t   = time.time()

    def _msg(self, text: str):
        self.messages.append((text, time.time() + 2.5))

    # ---- Input -------------------------------------------------------------

    def _input(self, dt: float):
        keys: set[int] = set()
        while True:
            k = self.renderer.scr.getch()
            if k == -1:
                break
            keys.add(k)

        if ord('q') in keys or 27 in keys:
            self.running = False
            return

        p   = self.player
        spd = 3.8 * dt
        rot = 2.2 * dt
        dx  = math.cos(p.angle)
        dy  = math.sin(p.angle)

        if ord('w') in keys or curses.KEY_UP in keys:
            nx, ny = p.x + dx * spd, p.y + dy * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if ord('s') in keys or curses.KEY_DOWN in keys:
            nx, ny = p.x - dx * spd, p.y - dy * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if ord('a') in keys:
            nx, ny = p.x - dy * spd, p.y + dx * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if ord('d') in keys:
            nx, ny = p.x + dy * spd, p.y - dx * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if curses.KEY_LEFT  in keys: p.angle += rot
        if curses.KEY_RIGHT in keys: p.angle -= rot

        self._is_moving = any(k in keys for k in (
            ord('w'), ord('s'), ord('a'), ord('d'),
            curses.KEY_UP, curses.KEY_DOWN,
        ))

        if ord(' ') in keys or ord('f') in keys:
            self._shoot()

    # ---- Shooting ----------------------------------------------------------

    def _shoot(self):
        if self.shoot_cd > 0:
            return
        p = self.player
        if p.ammo <= 0:
            self._msg("-- NO AMMO --")
            return

        p.ammo       -= 1
        self.shoot_cd = 0.25
        self.flash    = 0.12
        self.recoil   = 0.05

        rdx = math.cos(p.angle)
        rdy = math.sin(p.angle)
        best_e, best_d = None, 22.0

        for e in self.enemies:
            if e.state == 'dead':
                continue
            ex, ey = e.x - p.x, e.y - p.y
            dist   = math.sqrt(ex * ex + ey * ey)
            if dist < 0.3:
                continue
            dot  = ex * rdx + ey * rdy
            perp = abs(ex * rdy - ey * rdx)
            if dot <= 0 or perp > 0.45 or dot >= best_d:
                continue
            if self.world.has_los(p.x, p.y, e.x, e.y):
                best_e, best_d = e, dot

        if best_e is None:
            self._msg("MISSED!")
            return

        dmg = random.randint(12, 28)
        best_e.health -= dmg
        best_e.state   = 'chase'
        if best_e.health <= 0:
            best_e.state = 'dead'
            p.score     += 150
            self.corpses.append((best_e.x, best_e.y))
            self._msg(f"KILL! +150pts  [{best_d:.1f}m]")
        else:
            self._msg(f"HIT {best_e.char}  -{dmg}hp  [{best_d:.1f}m]")

    # ---- Update ------------------------------------------------------------

    def update(self, dt: float, now: float):
        self.shoot_cd  = max(0.0, self.shoot_cd  - dt)
        self.flash     = max(0.0, self.flash     - dt)
        self.dmg_flash = max(0.0, self.dmg_flash - dt)
        self.hit_shake = max(0.0, self.hit_shake - dt * 4.0)
        self.recoil   *= max(0.0, 1.0 - 14.0 * dt)
        if self.recoil < 0.001:
            self.recoil = 0.0
        if self._is_moving:
            self._walk_timer += dt
        self.messages = [(m, t) for m, t in self.messages if t > now]

        alive = [e for e in self.enemies if e.state != 'dead']
        if not alive:
            self.won = self.running = False
            return

        for e in alive:
            dmg = e.update(dt, self.player, self.world, now)
            if dmg:
                self.player.health -= dmg
                self.dmg_flash      = 0.55
                self.hit_shake      = 0.06
                self._msg(f"OUCH! -{dmg}hp")
                if self.player.health <= 0:
                    self.running = False

        remaining = []
        for pk in self.pickups:
            dist = math.sqrt((pk[0] - self.player.x) ** 2 +
                             (pk[1] - self.player.y) ** 2)
            if dist < 0.75:
                if pk[2] == 'hp':
                    gained = min(25, 100 - self.player.health)
                    self.player.health += gained
                    self._msg(f"+{gained} HEALTH")
                else:
                    gained = min(15, 99 - self.player.ammo)
                    self.player.ammo += gained
                    self._msg(f"+{gained} AMMO")
            else:
                remaining.append(pk)
        self.pickups = remaining

    # ---- Main loop ---------------------------------------------------------

    def run(self):
        target = 1.0 / 35.0
        while self.running:
            now = time.time()
            dt  = min(now - self.last_t, 0.05)
            self.last_t = now
            self._input(dt)
            self.update(dt, now)
            self.renderer.render(self, now)
            wait = target - (time.time() - now)
            if wait > 0:
                time.sleep(wait)
        self.renderer.end_screen(self)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(stdscr):
    quality = 'normal'
    for arg in sys.argv[1:]:
        if arg in ('-l', '--low'):    quality = 'low'
        elif arg in ('-H', '--high'): quality = 'high'
    Game(stdscr, quality).run()


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
