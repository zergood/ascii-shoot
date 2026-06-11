"""tcod I/O layer — window, input, and renderer.

Replaces curses entirely. Pure game logic lives in game.py.
"""

from __future__ import annotations

import math
import os
import time

import tcod
import tcod.console
import tcod.context
import tcod.event
import tcod.tileset

import sprites as _spr

# ── Window configuration ────────────────────────────────────────────────────

COLS       = 120          # console width  (characters)
ROWS       = 45           # console height (characters)
FONT_PATH  = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONT_SIZE  = 14           # px — adjust for monitor DPI
VIEW_ROWS  = ROWS - 3     # rows reserved for the 3D view

# ── Colour palette (RGB) ────────────────────────────────────────────────────

BLACK   = (  0,   0,   0)
WHITE   = (220, 220, 220)
RED     = (220,  40,  40)
ORANGE  = (220, 140,  40)
YELLOW  = (220, 200,  60)
GREEN   = ( 60, 180,  60)
CYAN    = ( 60, 200, 210)
BLUE    = ( 40,  80, 160)
MAGENTA = (180,  60, 200)
GREY    = ( 80,  80,  80)
DKGREY  = ( 30,  30,  30)

SKY_TOP    = ( 12,  12,  35)
SKY_BOT    = ( 28,  28,  72)
FLOOR_TOP  = ( 45,  35,  20)
FLOOR_BOT  = ( 18,  14,   8)

# Muted wall colours — less saturated than before so walls don't overwhelm
WALL_FG: dict[int, tuple] = {
    1: (155, 125,  65),  # warm stone
    2: ( 50, 145,  70),  # moss green
    3: (135,  85,  50),  # brown brick
    4: (185,  55,  55),  # dark red
    5: ( 50, 175, 190),  # cyan door
}

ENEMY_COLOR: dict[str, tuple] = {
    'zombie': (235,  55,  55),
    'demon':  (210,  70, 225),
    'imp':    (245, 165,  40),
}

# Maximum render distance (walls become empty beyond this)
FAR_CLIP = 16.0

# ── Key mapping ─────────────────────────────────────────────────────────────

_K = tcod.event.KeySym

MOVE_FORWARD  = {_K.W, _K.UP}
MOVE_BACK     = {_K.S, _K.DOWN}
STRAFE_LEFT   = {_K.A}
STRAFE_RIGHT  = {_K.D}
TURN_LEFT     = {_K.LEFT}
TURN_RIGHT    = {_K.RIGHT}
FIRE          = {_K.SPACE, _K.F}
USE           = {_K.E}
PAUSE         = {_K.P}
QUIT          = {_K.Q, _K.ESCAPE}
WEAPON_KEYS   = {_K.N1: 0, _K.N2: 1, _K.N3: 2}


def _lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    """Linear interpolate between two RGB tuples."""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _dim(color: tuple, factor: float) -> tuple:
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


# ── Renderer ─────────────────────────────────────────────────────────────────

class Renderer:
    """Draws game state onto a tcod Console each frame."""

    def __init__(self, console: tcod.console.Console):
        self.con = console

    # ---- Main entry --------------------------------------------------------

    def render(self, game, now: float) -> None:
        con     = self.con
        w, h    = COLS, ROWS
        view_h  = VIEW_ROWS
        half_h  = view_h // 2

        import random
        shake = (random.uniform(-game.hit_shake, game.hit_shake)
                 if game.hit_shake > 0.005 else 0.0)
        view_angle = game.player.angle + game.recoil + shake

        con.clear()
        self._draw_sky_floor(game.player, view_angle, view_h, half_h, w)
        z_buf = [999.0] * w
        self._draw_walls(game.world, game.player, view_angle, view_h, half_h, w, z_buf)
        self._draw_live_enemies(game, z_buf, view_angle, view_h, half_h, w, now)
        self._draw_floor_objects(game, z_buf, view_angle, view_h, half_h, w)
        self._draw_projectiles(game, z_buf, view_angle, view_h, half_h, w)
        self._draw_crosshair(game.flash, view_h, w)
        self._draw_gun(game, view_h, w)
        self._draw_minimap(game, w)
        self._draw_hud(game, h, w, view_h)
        self._draw_damage_border(game.dmg_flash, view_h, w)
        self._draw_messages(game.messages)
        if game.paused:
            self._draw_pause_overlay(view_h, w)

    # ---- Sky / floor --------------------------------------------------------

    def _draw_sky_floor(self, player, view_angle: float,
                        view_h: int, half_h: int, w: int) -> None:
        con = self.con

        # ── Ceiling: clean gradient, no characters ──────────────────────────
        for row in range(half_h):
            t  = row / max(half_h - 1, 1)
            bg = _lerp_color(SKY_TOP, SKY_BOT, t)
            for col in range(w):
                con.print(col, row, ' ', bg=bg)

        # ── Floor: perspective-correct tile casting ──────────────────────────
        # Camera vectors (same as wall raycaster)
        dx  = math.cos(view_angle);  dy  = math.sin(view_angle)
        px  =  0.66 * dy;            py  = -0.66 * dx
        rlx = dx - px;               rly = dy - py   # leftmost ray
        rrx = dx + px;               rry = dy + py   # rightmost ray

        for row in range(half_h, view_h):
            p_row = row - half_h + 0.5          # rows below horizon (≥ 0.5)
            row_dist = half_h / p_row           # world distance to this row

            step_x = row_dist * (rrx - rlx) / w
            step_y = row_dist * (rry - rly) / w
            fx = player.x + row_dist * rlx
            fy = player.y + row_dist * rly

            fog = max(0.12, 1.0 - row_dist / 10.0)
            t   = (row - half_h) / max(view_h - half_h - 1, 1)
            bg  = _lerp_color(FLOOR_TOP, FLOOR_BOT, t)

            for col in range(w):
                tx = fx - math.floor(fx)        # fractional tile position
                ty = fy - math.floor(fy)

                at_edge = tx < 0.06 or tx > 0.94 or ty < 0.06 or ty > 0.94
                if at_edge:
                    ch = '+'
                    fg = _dim(FLOOR_TOP, fog * 0.9)
                else:
                    ch = '·'
                    fg = _dim(FLOOR_TOP, fog * 0.45)

                try:
                    con.print(col, row, ch, fg=fg, bg=bg)
                except Exception:
                    pass

                fx += step_x
                fy += step_y

    # ---- Walls --------------------------------------------------------------

    def _draw_walls(self, world, player, view_angle,
                    view_h, half_h, w, z_buf) -> None:
        for col in range(w):
            dist, wtype, side, wall_x = world.cast_ray(
                player.x, player.y, view_angle, col, w)

            z_buf[col] = dist

            # 4-tier character by distance (Javidx9 style)
            if   dist <= FAR_CLIP / 4:  ch = '█'
            elif dist <= FAR_CLIP / 3:  ch = '▓'
            elif dist <= FAR_CLIP / 2:  ch = '▒'
            elif dist <= FAR_CLIP:      ch = '░'
            else:                       ch = ' '

            # Tile boundary: thin vertical seam where tile faces meet
            boundary = (wall_x < 0.04 or wall_x > 0.96)
            if boundary:
                ch = '│'

            base_fg = WALL_FG.get(wtype, WALL_FG[1])

            # N/S faces slightly dimmer (directional shading)
            if side == 1:
                base_fg = _dim(base_fg, 0.60)

            if boundary:
                base_fg = _dim(base_fg, 0.40)

            # Linear fog: full bright at dist=0, dim at dist=FAR_CLIP
            fog = max(0.20, 1.0 - dist / FAR_CLIP)
            fg  = _dim(base_fg, fog)

            wh  = min(int(view_h / max(dist, 0.05)), view_h)
            top = max(0,      half_h - wh // 2)
            bot = min(view_h, half_h + wh // 2)

            for row in range(top, bot):
                try:
                    self.con.print(col, row, ch, fg=fg, bg=BLACK)
                except Exception:
                    pass

    # ---- Live enemy sprites ------------------------------------------------

    def _draw_live_enemies(self, game, z_buf, view_angle,
                           view_h, half_h, w, now) -> None:
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
            fog  = max(0.4, 1.0 - depth / 14.0)
            fg   = _dim(ENEMY_COLOR.get(e.kind, WHITE), fog)
            sw_range = max(sw - 1, 1)

            for cx_off in range(-sw // 2, sw // 2 + 1):
                col = sx + cx_off
                if col < 0 or col >= w or z_buf[col] <= depth:
                    continue
                rx = max(0.0, min(1.0, (cx_off + sw // 2) / sw_range))
                for row_off in range(sh):
                    row = top + row_off
                    if row < 0 or row >= view_h:
                        continue
                    ch = _spr.enemy_char(
                        e.kind, row_off / sh, rx, frame, e.state)
                    if ch is None:
                        continue
                    try:
                        self.con.print(col, row, ch, fg=fg)
                    except Exception:
                        pass

    # ---- Floor objects (corpses + pickups) ---------------------------------

    def _draw_floor_objects(self, game, z_buf, view_angle,
                            view_h, half_h, w) -> None:
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
            [(cx, cy, '%', RED)   for cx, cy in game.corpses] +
            [(px2, py2,
              '+' if k == 'hp' else '*',
              GREEN if k == 'hp' else YELLOW)
             for px2, py2, k in game.pickups]
        )
        for ox, oy, fch, fcolor in objs:
            tx, tz = _proj(ox, oy)
            if tz <= 0.1:
                continue
            sx  = int((w / 2) * (1.0 + tx / tz))
            sh  = min(abs(int(view_h / tz)), view_h)
            row = min(view_h - 1, half_h + sh // 3)
            if 0 <= sx < w and z_buf[sx] > tz:
                try:
                    self.con.print(sx, row, fch, fg=fcolor)
                except Exception:
                    pass

    # ---- Projectiles -------------------------------------------------------

    def _draw_projectiles(self, game, z_buf, view_angle,
                          view_h, half_h, w) -> None:
        p   = game.player
        dx  = math.cos(view_angle);  dy = math.sin(view_angle)
        px  =  0.66 * dy;            py = -0.66 * dx
        inv = 1.0 / (px * dy - dx * py)

        for proj in game.projectiles:
            if not proj.alive:
                continue
            ex, ey = proj.x - p.x, proj.y - p.y
            tx = inv * ( dy * ex - dx * ey)
            tz = inv * (-py * ex + px * ey)
            if tz <= 0.1:
                continue
            sx = int((w / 2) * (1.0 + tx / tz))
            sy = half_h   # eye level
            if 0 <= sx < w and 0 <= sy < view_h and z_buf[sx] > tz:
                fog = max(0.4, 1.0 - tz / 14.0)
                try:
                    self.con.print(sx, sy, '*', fg=_dim(ORANGE, fog))
                except Exception:
                    pass

    # ---- Crosshair ---------------------------------------------------------

    def _draw_crosshair(self, flash: float, view_h: int, w: int) -> None:
        cy, cx = view_h // 2, w // 2
        color  = MAGENTA if flash > 0 else WHITE
        try:
            self.con.print(cx - 1, cy,     '-+-', fg=color)
            self.con.print(cx,     cy - 1, '|',   fg=color)
            self.con.print(cx,     cy + 1, '|',   fg=color)
        except Exception:
            pass

    # ---- Gun sprite --------------------------------------------------------

    def _draw_gun(self, game, view_h: int, w: int) -> None:
        cx     = w // 2
        firing = game.flash > 0

        bob = 0
        if game._is_moving and not firing:
            bob = round(math.sin(game._walk_timer * 8.0) * 1.3)

        gun_lines = _spr.GUN_SPRITES[game.player.weapon]
        if firing:
            fi = int((0.12 - game.flash) / 0.04) % len(_spr.GUN_FLASH)
            try:
                self.con.print(cx - 4, view_h - 5,
                               _spr.GUN_FLASH[fi], fg=MAGENTA)
            except Exception:
                pass
            base_row = view_h - 4
        else:
            base_row = view_h - 3

        base_row += bob
        for i, line in enumerate(gun_lines):
            try:
                self.con.print(cx - 4, base_row + i, line, fg=YELLOW)
            except Exception:
                pass

    # ---- Minimap -----------------------------------------------------------

    def _draw_minimap(self, game, w: int) -> None:
        world = game.world
        size  = 13
        ox    = w - size - 2
        oy    = 0
        mw, mh = world.w, world.h
        scale = size / max(mw, mh)

        for my in range(size):
            for mx in range(size):
                gx = min(mw - 1, int(mx / scale))
                gy = min(mh - 1, int(my / scale))
                cell = world.grid[gy][gx]
                if cell:
                    if cell == 5:
                        is_open = (gx, gy) in world._open_doors
                        ch = '/' if is_open else '+'
                        fg = GREEN if is_open else CYAN
                    else:
                        ch, fg = '#', YELLOW
                    try:
                        self.con.print(ox + mx, oy + my, ch, fg=fg)
                    except Exception:
                        pass

        for px2, py2, kind in game.pickups:
            mx = int(px2 * scale);  my = int(py2 * scale)
            if 0 <= mx < size and 0 <= my < size:
                fg = GREEN if kind == 'hp' else YELLOW
                try:
                    self.con.print(ox + mx, oy + my,
                                   '+' if kind == 'hp' else '*', fg=fg)
                except Exception:
                    pass

        for cx2, cy2 in game.corpses:
            mx = int(cx2 * scale);  my = int(cy2 * scale)
            if 0 <= mx < size and 0 <= my < size:
                try:
                    self.con.print(ox + mx, oy + my, 'x', fg=RED)
                except Exception:
                    pass

        for e in game.enemies:
            if e.state == 'dead':
                continue
            ex = int(e.x * scale);  ey = int(e.y * scale)
            if 0 <= ex < size and 0 <= ey < size:
                try:
                    self.con.print(ox + ex, oy + ey, '!', fg=RED)
                except Exception:
                    pass

        ppx = int(game.player.x * scale)
        ppy = int(game.player.y * scale)
        if 0 <= ppx < size and 0 <= ppy < size:
            try:
                self.con.print(ox + ppx, oy + ppy, '@', fg=GREEN)
            except Exception:
                pass

        # FOV dots
        fov_half = math.atan(0.66)
        for dist in (2.0, 3.5):
            for ao in (-fov_half, fov_half):
                fx = int((game.player.x +
                          math.cos(game.player.angle + ao) * dist) * scale)
                fy = int((game.player.y +
                          math.sin(game.player.angle + ao) * dist) * scale)
                if 0 <= fx < size and 0 <= fy < size:
                    try:
                        self.con.print(ox + fx, oy + fy, '.', fg=CYAN)
                    except Exception:
                        pass

    # ---- HUD ---------------------------------------------------------------

    def _draw_hud(self, game, h: int, w: int, view_h: int) -> None:
        from game import WEAPONS, WAVE_MAX
        p      = game.player
        y      = view_h
        hp_pct = max(0, p.health) / 100.0
        bw     = 14
        filled = int(hp_pct * bw)
        bar    = '█' * filled + '░' * (bw - filled)
        hp_fg  = (RED    if hp_pct < 0.3 else
                  ORANGE if hp_pct < 0.6 else GREEN)

        wdef      = WEAPONS[p.weapon]
        wname     = f'[{p.weapon+1}]{wdef["name"]}'
        bullets   = p.ammo.get('bullet', 0)
        shells    = p.ammo.get('shell',  0)
        alive     = sum(1 for e in game.enemies if e.state != 'dead')
        wave_num  = getattr(game, 'wave', 1)
        sep       = '═' * (w - 1)

        combo_str = f'  x{p.combo} COMBO!' if p.combo > 1 else ''
        pause_str = '  [PAUSED]'           if game.paused  else ''
        wave_str  = f'WAVE {wave_num}/{WAVE_MAX}'

        try:
            self.con.print(0,  y,     sep[:w-1],                  fg=YELLOW)
            self.con.print(1,  y + 1, f'HP[{bar}]{p.health:3d}',  fg=hp_fg)
            self.con.print(23, y + 1, wname,                       fg=YELLOW)
            self.con.print(35, y + 1, f'SCORE:{p.score}',          fg=GREEN)
            if combo_str:
                self.con.print(54, y + 1, combo_str,               fg=MAGENTA)
            if pause_str:
                self.con.print(70, y + 1, pause_str,               fg=CYAN)
            self.con.print(w - len(wave_str) - 2, y + 1,
                           wave_str,                               fg=CYAN)
            self.con.print(1,  y + 2,
                           f'BULLET:{bullets:3d}  SHELL:{shells:2d}',
                           fg=YELLOW)
            self.con.print(25, y + 2,
                           f'ENEMIES:{alive:2d}/{len(game.enemies)}',
                           fg=RED)
            controls = 'WASD:move ←→:turn SPC:fire 1-3:weapon P:pause Q:quit'
            self.con.print(42, y + 2, controls[:w - 43], fg=BLUE)
        except Exception:
            pass

    # ---- Pause overlay -----------------------------------------------------

    def _draw_pause_overlay(self, view_h: int, w: int) -> None:
        cx   = w // 2
        cy   = view_h // 2
        lines = [
            '╔════════════════╗',
            '║    P A U S E D ║',
            '║  P  to resume  ║',
            '╚════════════════╝',
        ]
        bw = len(lines[0])
        bx = cx - bw // 2
        by = cy - len(lines) // 2
        for i, line in enumerate(lines):
            try:
                self.con.print(bx, by + i, line, fg=CYAN, bg=BLACK)
            except Exception:
                pass

    # ---- Damage border -----------------------------------------------------

    def _draw_damage_border(self, dmg_flash: float,
                            view_h: int, w: int) -> None:
        if dmg_flash <= 0:
            return
        t    = dmg_flash / 0.55
        cols = max(1, int(t * 5))
        rows = max(1, int(t * 3))
        for row in range(view_h):
            for c in range(cols):
                try:
                    self.con.print(c,         row, '▌', fg=RED)
                    self.con.print(w - 2 - c, row, '▌', fg=RED)
                except Exception:
                    pass
        for r in range(rows):
            try:
                self.con.print(0, r,              '▄' * (w - 1), fg=RED)
                self.con.print(0, view_h - 1 - r, '▄' * (w - 1), fg=RED)
            except Exception:
                pass

    # ---- Messages ----------------------------------------------------------

    def _draw_messages(self, messages) -> None:
        for i, (msg, _) in enumerate(messages[-3:]):
            try:
                self.con.print(1, 1 + i, msg[:38], fg=MAGENTA)
            except Exception:
                pass

    # ---- Menu / end screens ------------------------------------------------

    def menu_screen(self, ctx: tcod.context.Context) -> str:
        """Show the main menu. Returns 'play', 'scores', or 'quit'."""
        options  = ['NEW GAME', 'HIGHSCORES', 'QUIT']
        results  = ['play', 'scores', 'quit']
        selected = 0
        title = [
            r"   _   ___  ___ ___ ___   ___ _  _ ___   ___ _____",
            r"  /_\ / __|/ __|_ _|_ _| / __| || | _ \ / _ \_   _|",
            r" / _ \\__ \ (__ | | | |  \__ \ __ |   /| (_) || |  ",
            r"/_/ \_\___/\___|___|___| |___/_||_|_|_\ \___/ |_|  ",
        ]
        tagline = 'A  D O O M - S T Y L E  A S C I I  S H O O T E R'
        blink   = True
        blink_t = time.time()

        while True:
            now = time.time()
            if now - blink_t >= 0.5:
                blink   = not blink
                blink_t = now

            self.con.clear()
            cw = COLS // 2

            for i, line in enumerate(title):
                try:
                    self.con.print(max(0, cw - len(line) // 2),
                                   ROWS // 2 - 10 + i, line, fg=YELLOW)
                except Exception:
                    pass
            try:
                self.con.print(cw - len(tagline) // 2,
                               ROWS // 2 - 5, tagline, fg=ORANGE)
            except Exception:
                pass

            for i, opt in enumerate(options):
                is_sel = (i == selected)
                fg     = MAGENTA if is_sel else WHITE
                marker = ('▶ ' if blink else '  ') if is_sel else '  '
                try:
                    self.con.print(cw - 10, ROWS // 2 - 1 + i * 2,
                                   f'{marker}{opt}', fg=fg)
                except Exception:
                    pass

            try:
                self.con.print(1, ROWS - 2,
                               '↑↓ W S : navigate    ENTER SPACE : select',
                               fg=GREY)
            except Exception:
                pass

            ctx.present(self.con)

            for event in tcod.event.wait(timeout=0.5):
                if isinstance(event, tcod.event.Quit):
                    return 'quit'
                if isinstance(event, tcod.event.KeyDown):
                    if event.sym in (tcod.event.KeySym.UP,
                                     tcod.event.KeySym.W):
                        selected = (selected - 1) % len(options)
                    elif event.sym in (tcod.event.KeySym.DOWN,
                                       tcod.event.KeySym.S):
                        selected = (selected + 1) % len(options)
                    elif event.sym in (tcod.event.KeySym.RETURN,
                                       tcod.event.KeySym.SPACE,
                                       tcod.event.KeySym.KP_ENTER):
                        return results[selected]
                    elif event.sym == tcod.event.KeySym.Q:
                        return 'quit'
                    elif event.sym == tcod.event.KeySym.N:
                        return 'play'

    def scores_screen(self, ctx: tcod.context.Context,
                      scores: list[int]) -> None:
        """Dedicated highscore table. Any key returns to menu."""
        medals = ['★', '☆', '○', '·', '·', '·', '·', '·', '·', '·']
        self.con.clear()
        cw = COLS // 2

        header = '╔══════════════════════╗'
        footer = '╚══════════════════════╝'
        try:
            self.con.print(cw - len(header) // 2,
                           ROWS // 2 - 8, header, fg=YELLOW)
            self.con.print(cw - 9, ROWS // 2 - 7,
                           '║    HALL  OF  FAME    ║', fg=YELLOW)
            self.con.print(cw - len(header) // 2,
                           ROWS // 2 - 6, '╠══════════════════════╣', fg=YELLOW)
        except Exception:
            pass

        if scores:
            for i, s in enumerate(scores[:10]):
                medal = medals[i]
                line  = f'║  {medal} {i+1:2d}.  {s:>8d}       ║'
                fg    = (YELLOW  if i == 0 else
                         GREY    if i == 1 else
                         ORANGE  if i == 2 else WHITE)
                try:
                    self.con.print(cw - len(header) // 2,
                                   ROWS // 2 - 5 + i, line, fg=fg)
                except Exception:
                    pass
            row_after = ROWS // 2 - 5 + len(scores[:10])
        else:
            try:
                self.con.print(cw - 8, ROWS // 2 - 4,
                               '║    No scores yet.    ║', fg=GREY)
            except Exception:
                pass
            row_after = ROWS // 2 - 3

        try:
            self.con.print(cw - len(footer) // 2,
                           row_after, footer, fg=YELLOW)
            self.con.print(cw - 11, row_after + 2,
                           'Press any key to return…', fg=GREY)
        except Exception:
            pass

        ctx.present(self.con)
        for event in tcod.event.wait():
            if isinstance(event, (tcod.event.KeyDown, tcod.event.Quit)):
                return

    def wave_clear_screen(self, ctx: tcod.context.Context,
                          wave_num: int = 1,
                          next_wave: int | None = None) -> None:
        """Brief between-wave flash. Auto-advances after 2 s or any key."""
        next_str = (f'  Preparing wave {next_wave}…'
                    if next_wave else '  Preparing final wave…')
        lines = [
            '╔══════════════════════════════╗',
            '║                              ║',
            f'║   ★  W A V E  {wave_num}  C L E A R  ★  ║',
            '║                              ║',
            '║   All enemies defeated!      ║',
            next_str[:32].ljust(30).join(['║  ', '  ║']),
            '║                              ║',
            '╚══════════════════════════════╝',
        ]
        cw  = COLS // 2
        bw  = max(len(l) for l in lines)
        bx  = cw - bw // 2
        cy  = ROWS // 2 - len(lines) // 2
        deadline = time.time() + 2.5

        while time.time() < deadline:
            self.con.clear()
            for i, line in enumerate(lines):
                try:
                    self.con.print(bx, cy + i, line, fg=GREEN)
                except Exception:
                    pass
            try:
                self.con.print(cw - 12, cy + len(lines) + 1,
                               'Press any key to continue…', fg=GREY)
            except Exception:
                pass
            ctx.present(self.con)
            for event in tcod.event.wait(timeout=0.1):
                if isinstance(event, (tcod.event.KeyDown, tcod.event.Quit)):
                    return

    def end_screen(self, game, ctx: tcod.context.Context,
                   scores: list[int]) -> None:
        """Show game-over / win screen with stats and highscores."""
        from game import WAVE_MAX
        self.con.clear()
        is_win    = game.won
        title     = '  YOU  WIN!  ' if is_win else '  GAME  OVER  '
        title_fg  = GREEN if is_win else RED
        kills     = sum(1 for e in game.enemies if e.state == 'dead')
        total     = len(game.enemies)
        elapsed   = int(time.time() - getattr(game, 'start_t', time.time()))
        mins, sec = divmod(elapsed, 60)
        wave_num  = getattr(game, 'wave', 1)
        is_new    = bool(scores and game.player.score == scores[0]
                        and game.player.score > 0)

        stats = [
            f'  Score   : {game.player.score}',
            f'  Wave    : {wave_num} / {WAVE_MAX}',
            f'  Kills   : {kills} / {total}',
            f'  Time    : {mins:02d}:{sec:02d}',
        ]
        top   = ['', '  TOP SCORES:', '  ─────────────'] + [
            f'  {i+1:2d}.  {s}' for i, s in enumerate(scores[:5])
        ] + ['', '  Press any key…']

        box_w    = 34
        cw       = COLS // 2
        bx       = cw - box_w // 2
        by       = ROWS // 2 - 9
        top_line = '╔' + '═' * (box_w - 2) + '╗'
        bot_line = '╚' + '═' * (box_w - 2) + '╝'
        mid_sep  = '╠' + '═' * (box_w - 2) + '╣'

        def _row(text: str, fg=WHITE) -> None:
            nonlocal by
            inner = text[:box_w - 4].ljust(box_w - 4)
            try:
                self.con.print(bx, by, f'║ {inner} ║', fg=fg)
            except Exception:
                pass
            by += 1

        def _line(ch: str, fg=YELLOW) -> None:
            nonlocal by
            try:
                self.con.print(bx, by, ch, fg=fg)
            except Exception:
                pass
            by += 1

        by_start = by
        try:
            self.con.print(bx, by, top_line, fg=YELLOW)
        except Exception:
            pass
        by += 1

        _row(title.center(box_w - 4), fg=title_fg)
        if is_new:
            _row('★  NEW  HIGH  SCORE  ★'.center(box_w - 4), fg=YELLOW)

        _line(mid_sep)

        for s in stats:
            _row(s, fg=WHITE)

        _line(mid_sep)

        for s in top:
            _row(s, fg=CYAN if s.strip().startswith(('1.', '1 ')) else WHITE)

        try:
            self.con.print(bx, by, bot_line, fg=YELLOW)
        except Exception:
            pass

        ctx.present(self.con)
        for event in tcod.event.wait():
            if isinstance(event, (tcod.event.KeyDown, tcod.event.Quit)):
                return


# ── Input handler ───────────────────────────────────────────────────────────

class InputHandler:
    """Translates tcod events into a held-key set for Game._input()."""

    def __init__(self) -> None:
        self._held: set[tcod.event.KeySym] = set()
        self._just: set[tcod.event.KeySym] = set()

    def process_events(self) -> tuple[set, bool]:
        """Poll events; return (held_keys, quit_requested)."""
        self._just.clear()
        quit_req = False
        for event in tcod.event.get():
            if isinstance(event, tcod.event.Quit):
                quit_req = True
            elif isinstance(event, tcod.event.KeyDown):
                if not event.repeat:
                    self._just.add(event.sym)
                self._held.add(event.sym)
                if event.sym in QUIT:
                    quit_req = True
            elif isinstance(event, tcod.event.KeyUp):
                self._held.discard(event.sym)
        return frozenset(self._held), quit_req

    def just_pressed(self, key: tcod.event.KeySym) -> bool:
        return key in self._just

    def clear(self) -> None:
        self._held.clear()
        self._just.clear()


# ── Context factory ─────────────────────────────────────────────────────────

def make_context(title: str = 'ASCII SHOOT') -> tcod.context.Context:
    tileset = tcod.tileset.load_truetype_font(FONT_PATH, FONT_SIZE, FONT_SIZE)
    return tcod.context.new(
        columns=COLS,
        rows=ROWS,
        tileset=tileset,
        title=title,
        vsync=True,
    )


def make_console() -> tcod.console.Console:
    return tcod.console.Console(COLS, ROWS, order='C')
