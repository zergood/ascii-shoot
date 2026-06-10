#!/usr/bin/env python3
"""ASCII FPS — Doom-style raycasting shooter in the terminal."""

import math
import time
import random
import sys
import sprites as _spr

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

# Re-export shading palettes so existing importers (tests) still work
SHADE_UNI   = _spr.SHADE_UNI
SHADE_ASCII = _spr.SHADE_ASCII
WALL_COLOR  = {1: 3, 2: 4, 3: 3, 4: 1}

WEAPONS = [
    # idx 0 — Pistol
    {'name': 'Pistol',  'cd': 0.25, 'dmg': (12, 28), 'spread': 0.45,
     'ammo_type': 'bullet', 'cost': 1, 'pellets': 1},
    # idx 1 — Shotgun
    {'name': 'Shotgun', 'cd': 0.70, 'dmg': (6,  14), 'spread': 0.85,
     'ammo_type': 'shell',  'cost': 1, 'pellets': 5},
    # idx 2 — Rifle
    {'name': 'Rifle',   'cd': 0.12, 'dmg': (25, 40), 'spread': 0.22,
     'ammo_type': 'bullet', 'cost': 1, 'pellets': 1},
]


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
        self.x       = 2.5
        self.y       = 2.5
        self.angle   = 0.0
        self.health  = 100
        self.ammo    = {'bullet': 50, 'shell': 15}
        self.weapon  = 0   # index into WEAPONS
        self.score   = 0
        self.combo   = 0
        self.combo_t = 0.0

    @property
    def current_ammo(self) -> int:
        return self.ammo.get(WEAPONS[self.weapon]['ammo_type'], 0)


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
# Game  — coordinator, no curses code
# ---------------------------------------------------------------------------

class Game:

    def __init__(self, renderer, input_handler):
        self.world   = World()
        self.player  = Player()
        self.enemies = [Enemy(x, y, k) for x, y, k in ENEMY_SPAWNS]
        self.pickups = list(PICKUP_SPAWNS)
        self.corpses  = []
        self.messages = []
        self.running  = True
        self.won      = False

        # Visual-effect timers — written by game logic, read by Renderer
        self.flash       = 0.0
        self.shoot_cd    = 0.0
        self.dmg_flash   = 0.0
        self.recoil      = 0.0
        self.hit_shake   = 0.0
        self._is_moving  = False
        self._walk_timer = 0.0

        self.renderer      = renderer
        self._input_handler = input_handler
        self.last_t        = time.time()

    def _msg(self, text: str):
        self.messages.append((text, time.time() + 2.5))

    # ---- Input -------------------------------------------------------------

    def _input(self, dt: float):
        import engine as _eng
        keys, quit_req = self._input_handler.process_events()

        if quit_req:
            self.running = False
            return

        p   = self.player
        spd = 3.8 * dt
        rot = 2.2 * dt
        dx  = math.cos(p.angle)
        dy  = math.sin(p.angle)

        if keys & _eng.MOVE_FORWARD:
            nx, ny = p.x + dx * spd, p.y + dy * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if keys & _eng.MOVE_BACK:
            nx, ny = p.x - dx * spd, p.y - dy * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if keys & _eng.STRAFE_LEFT:
            nx, ny = p.x - dy * spd, p.y + dx * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if keys & _eng.STRAFE_RIGHT:
            nx, ny = p.x + dy * spd, p.y - dx * spd
            if self.world.can_step(nx, p.y): p.x = nx
            if self.world.can_step(p.x, ny): p.y = ny

        if keys & _eng.TURN_LEFT:  p.angle += rot
        if keys & _eng.TURN_RIGHT: p.angle -= rot

        self._is_moving = bool(keys & (_eng.MOVE_FORWARD | _eng.MOVE_BACK
                                       | _eng.STRAFE_LEFT | _eng.STRAFE_RIGHT))

        if keys & _eng.FIRE:
            self._shoot()

        for sym, idx in _eng.WEAPON_KEYS.items():
            if sym in keys:
                p.weapon = idx

    # ---- Shooting ----------------------------------------------------------

    def _shoot(self):
        if self.shoot_cd > 0:
            return
        p    = self.player
        wdef = WEAPONS[p.weapon]
        atype = wdef['ammo_type']

        if p.ammo.get(atype, 0) <= 0:
            self._msg(f"-- NO {wdef['name'].upper()} AMMO --")
            return

        p.ammo[atype] -= wdef['cost']
        self.shoot_cd  = wdef['cd']
        self.flash     = 0.12
        self.recoil    = 0.05

        hit_any = False
        for _ in range(wdef['pellets']):
            off = random.uniform(-wdef['spread'] * 0.10,
                                  wdef['spread'] * 0.10)
            rdx = math.cos(p.angle + off)
            rdy = math.sin(p.angle + off)
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
                if dot <= 0 or perp > wdef['spread'] or dot >= best_d:
                    continue
                if self.world.has_los(p.x, p.y, e.x, e.y):
                    best_e, best_d = e, dot

            if best_e is None or best_e.state == 'dead':
                continue

            dmg = random.randint(*wdef['dmg'])
            best_e.health -= dmg
            best_e.state   = 'chase'
            hit_any = True

            if best_e.health <= 0:
                best_e.state = 'dead'
                p.score     += 150
                self.corpses.append((best_e.x, best_e.y))
                self._msg(f"KILL! +150pts  [{best_d:.1f}m]")
            else:
                self._msg(f"HIT {best_e.char}  -{dmg}hp  [{best_d:.1f}m]")

        if not hit_any:
            self._msg("MISSED!")

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
                    gained = min(15, 99 - self.player.ammo['bullet'])
                    self.player.ammo['bullet'] += gained
                    self._msg(f"+{gained} AMMO")
            else:
                remaining.append(pk)
        self.pickups = remaining

    # ---- Main loop ---------------------------------------------------------

    def run(self, ctx):
        """Run the game loop. *ctx* is the tcod Context for presenting frames."""
        import engine as _eng
        target = 1.0 / 35.0
        while self.running:
            now = time.time()
            dt  = min(now - self.last_t, 0.05)
            self.last_t = now
            self._input(dt)
            self.update(dt, now)
            self.renderer.render(self, now)
            ctx.present(self.renderer.con)
            wait = target - (time.time() - now)
            if wait > 0:
                time.sleep(wait)


# ---------------------------------------------------------------------------
# Highscores helper
# ---------------------------------------------------------------------------

import os as _os

_SCORE_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                             'highscore.txt')

def load_scores() -> list[int]:
    try:
        with open(_SCORE_FILE) as f:
            return [int(l.strip()) for l in f if l.strip().isdigit()][:10]
    except Exception:
        return []

def save_score(score: int) -> None:
    scores = sorted(load_scores() + [score], reverse=True)[:10]
    try:
        with open(_SCORE_FILE, 'w') as f:
            f.write('\n'.join(str(s) for s in scores))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import engine as _eng

    with _eng.make_context() as ctx:
        console  = _eng.make_console()
        renderer = _eng.Renderer(console)
        inp      = _eng.InputHandler()

        while True:
            action = renderer.menu_screen(ctx)
            if action == 'quit':
                break
            if action == 'scores':
                scores = load_scores()
                # reuse end_screen with a dummy won=True game for display
                # (simplest approach — just show scores via end_screen)
                class _Stub:
                    won = True
                    player = type('P', (), {'score': 0})()
                    enemies = []
                _stub = _Stub()
                renderer.end_screen(_stub, ctx, scores)
                continue

            # --- Play ---
            game = Game(renderer, inp)
            game.run(ctx)
            save_score(game.player.score)
            renderer.end_screen(game, ctx, load_scores())
            inp.clear()


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
