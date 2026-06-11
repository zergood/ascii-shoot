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
    [1,0,0,0,0,0,0,0,0,5,0,0,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,3,0,0,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,3,3,3,3,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,2,2,5,2,0,0,0,0,0,0,4,4,5,4,0,0,0,0,1],
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
    (18.5, 18.5, 'zombie'), (8.5, 18.5, 'demon'), (12.5, 12.5, 'imp'),
    (20.5, 4.5, 'imp'),    (4.5, 20.5, 'demon'), (7.5, 7.5, 'zombie'),
    (17.5, 14.5, 'imp'),
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

WAVE_MAX   = 5
MAP_GEN_W  = 32
MAP_GEN_H  = 24


def generate_map(wave: int, rng: random.Random):
    """Procedurally generate a level for the given wave number.

    Returns (grid, player_start_xy, enemy_spawns, pickup_spawns).
    """
    W, H = MAP_GEN_W, MAP_GEN_H
    grid = [[1] * W for _ in range(H)]
    rooms: list[tuple[int, int, int, int]] = []

    # Place up to 10 non-overlapping rooms (with 2-cell padding)
    for _ in range(100):
        if len(rooms) >= 10:
            break
        rw = rng.randint(4, 8)
        rh = rng.randint(3, 6)
        rx = rng.randint(2, W - rw - 2)
        ry = rng.randint(2, H - rh - 2)
        ok = all(
            rx + rw + 2 <= orx or orx + orw + 2 <= rx or
            ry + rh + 2 <= ory or ory + orh + 2 <= ry
            for orx, ory, orw, orh in rooms
        )
        if ok:
            rooms.append((rx, ry, rw, rh))

    if not rooms:
        rooms = [(3, 3, 6, 5)]

    # Paint room-border cells with wall-type variants before carving interiors
    wtypes = [rng.choice([1, 2, 3, 4]) for _ in rooms]
    for i, (rx, ry, rw, rh) in enumerate(rooms):
        wt = wtypes[i]
        for y in range(max(1, ry - 1), min(H - 1, ry + rh + 1)):
            for x in range(max(1, rx - 1), min(W - 1, rx + rw + 1)):
                if grid[y][x] == 1:
                    grid[y][x] = wt

    # Carve room interiors
    for rx, ry, rw, rh in rooms:
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y][x] = 0

    def _ctr(r: tuple) -> tuple[int, int]:
        return r[0] + r[2] // 2, r[1] + r[3] // 2

    def _carve(x1: int, y1: int, x2: int, y2: int) -> None:
        """Carve an L-shaped corridor, never touching the outer border."""
        if rng.random() < 0.5:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 1 <= y1 <= H - 2 and 1 <= x <= W - 2:
                    grid[y1][x] = 0
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 1 <= y <= H - 2 and 1 <= x2 <= W - 2:
                    grid[y][x2] = 0
        else:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 1 <= y <= H - 2 and 1 <= x1 <= W - 2:
                    grid[y][x1] = 0
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 1 <= y2 <= H - 2 and 1 <= x <= W - 2:
                    grid[y2][x] = 0

    # Connect rooms in a chain, then add some extra loop connections
    for i in range(len(rooms) - 1):
        ax, ay = _ctr(rooms[i])
        bx, by = _ctr(rooms[i + 1])
        _carve(ax, ay, bx, by)

    if len(rooms) >= 2:
        for _ in range(max(1, len(rooms) // 3)):
            i, j = rng.sample(range(len(rooms)), 2)
            ax, ay = _ctr(rooms[i])
            bx, by = _ctr(rooms[j])
            _carve(ax, ay, bx, by)

    # Add doors at natural chokepoints (wall cell flanked by open cells)
    door_limit = 3 + wave // 2
    cands: list[tuple[int, int]] = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if grid[y][x] == 0:
                continue
            if ((grid[y][x - 1] == 0 and grid[y][x + 1] == 0) or
                    (grid[y - 1][x] == 0 and grid[y + 1][x] == 0)):
                cands.append((x, y))
    rng.shuffle(cands)
    for x, y in cands[:door_limit]:
        grid[y][x] = 5

    # ── Spawn points ────────────────────────────────────────────────────────
    rx0, ry0, rw0, rh0 = rooms[0]
    psx = rx0 + rw0 / 2.0
    psy = ry0 + rh0 / 2.0

    kinds = (['zombie'] * (2 + wave) +
             ['demon']  * max(0, wave - 1) +
             ['imp']    * max(0, wave - 2))
    rng.shuffle(kinds)

    # Prefer cells far from player; fall back to any open cell if needed
    all_open = [
        (x + 0.5, y + 0.5)
        for y in range(1, H - 1)
        for x in range(1, W - 1)
        if grid[y][x] == 0
    ]
    far_pts = sorted(
        all_open,
        key=lambda p: -((p[0] - psx) ** 2 + (p[1] - psy) ** 2)
    )
    # Only use cells beyond 5.5 units; if insufficient, use sorted list anyway
    truly_far = [p for p in far_pts
                 if math.sqrt((p[0] - psx) ** 2 + (p[1] - psy) ** 2) > 5.5]
    spawn_pool = truly_far if len(truly_far) >= len(kinds) else far_pts
    rng.shuffle(spawn_pool)

    enemy_spawns = [
        (spawn_pool[i][0], spawn_pool[i][1], k)
        for i, k in enumerate(kinds)
        if i < len(spawn_pool)
    ]

    used = set(spawn_pool[:len(enemy_spawns)])
    pick_pts = [p for p in all_open if p not in used]
    rng.shuffle(pick_pts)
    n_picks = 6 + wave // 2
    pickup_spawns = [
        (pick_pts[i][0], pick_pts[i][1], 'hp' if i % 2 == 0 else 'ammo')
        for i in range(min(n_picks, len(pick_pts)))
    ]

    return grid, (psx, psy), enemy_spawns, pickup_spawns


# ---------------------------------------------------------------------------
# World  — map data + spatial queries, no curses
# ---------------------------------------------------------------------------

class World:
    """Map grid plus collision and raycasting helpers."""

    def __init__(self, grid=None):
        self.grid        = grid if grid is not None else WORLD_MAP
        self.h           = len(self.grid)
        self.w           = len(self.grid[0]) if self.h else 0
        self._open_doors: set[tuple[int, int]] = set()

    def toggle_door(self, x: int, y: int) -> None:
        key = (x, y)
        if key in self._open_doors:
            self._open_doors.discard(key)
        else:
            self._open_doors.add(key)

    def is_wall(self, x: float, y: float) -> bool:
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.w or iy < 0 or iy >= self.h:
            return True
        cell = self.grid[iy][ix]
        if cell == 5:
            return (ix, iy) not in self._open_doors
        return cell != 0

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
# Projectile
# ---------------------------------------------------------------------------

class Projectile:
    SPEED = 7.0   # world-units per second

    def __init__(self, x: float, y: float, dx: float, dy: float, dmg: int):
        self.x     = x
        self.y     = y
        self.dx    = dx   # already scaled by SPEED
        self.dy    = dy
        self.dmg   = dmg
        self.alive = True

    def update(self, dt: float, player, world: World) -> int:
        """Move, using sub-steps so fast projectiles can't skip past targets."""
        if not self.alive:
            return 0
        sub = max(1, int((abs(self.dx) + abs(self.dy)) * dt / 0.25 + 1))
        sdt = dt / sub
        for _ in range(sub):
            self.x += self.dx * sdt
            self.y += self.dy * sdt
            if world.is_wall(self.x, self.y):
                self.alive = False
                return 0
            if math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2) < 0.5:
                self.alive = False
                return self.dmg
        return 0


# ---------------------------------------------------------------------------
# Game objects  — no curses
# ---------------------------------------------------------------------------

class Player:
    def __init__(self, x: float = 2.5, y: float = 2.5):
        self.x       = x
        self.y       = y
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
        'zombie': dict(hp=30, speed=1.4, dmg=(4, 12),  char='Z', ranged=False),
        'demon':  dict(hp=60, speed=0.9, dmg=(8, 20),  char='D', ranged=False),
        'imp':    dict(hp=20, speed=1.8, dmg=(5, 12),  char='I', ranged=True),
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
        self.ranged       = k['ranged']
        self.cpair        = 1 if kind == 'zombie' else 7
        self.state        = 'patrol'
        self.last_attack  = 0.0
        self.shot_cd      = 0.0
        self.patrol_vx    = random.uniform(-0.6, 0.6)
        self.patrol_vy    = random.uniform(-0.6, 0.6)
        self.patrol_timer = random.uniform(1.0, 3.0)

    def update(self, dt: float, player, world: World, now: float,
               projectiles: list | None = None) -> int:
        """Update AI. Returns melee damage this frame (0 if none).
        Ranged enemies append Projectile objects to *projectiles* if provided."""
        if self.state == 'dead':
            return 0

        ex   = player.x - self.x
        ey   = player.y - self.y
        dist = math.sqrt(ex * ex + ey * ey)

        if dist < 11.0 and self.state == 'patrol':
            if world.has_los(self.x, self.y, player.x, player.y):
                self.state = 'chase'

        if self.state == 'chase':
            if self.ranged:
                # Imp: keep 4-8u range; shoot a fireball every 2.5s
                if dist > 6.0:
                    mv = self.speed * dt / dist
                    nx, ny = self.x + ex * mv, self.y + ey * mv
                    if not world.is_wall(nx, self.y): self.x = nx
                    if not world.is_wall(self.x, ny): self.y = ny
                elif dist < 3.5:
                    mv = self.speed * dt / dist
                    nx, ny = self.x - ex * mv, self.y - ey * mv
                    if not world.is_wall(nx, self.y): self.x = nx
                    if not world.is_wall(self.x, ny): self.y = ny
                self.shot_cd = max(0.0, self.shot_cd - dt)
                if (self.shot_cd <= 0 and dist < 12.0
                        and world.has_los(self.x, self.y, player.x, player.y)
                        and projectiles is not None):
                    self.shot_cd = 2.5
                    self.last_attack = now
                    spd = Projectile.SPEED
                    projectiles.append(Projectile(
                        self.x, self.y,
                        (ex / dist) * spd, (ey / dist) * spd,
                        random.randint(*self.dmg),
                    ))
            else:
                if dist > 0.9:
                    mv = self.speed * dt / dist
                    nx, ny = self.x + ex * mv, self.y + ey * mv
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

    def __init__(self, renderer, input_handler,
                 wave: int = 1,
                 grid=None,
                 player_start=None,
                 enemy_spawns=None,
                 pickup_spawns=None):
        self.wave    = wave
        self.world   = World(grid)
        ps = player_start or (2.5, 2.5)
        self.player  = Player(ps[0], ps[1])
        self.enemies = [Enemy(x, y, k) for x, y, k in (enemy_spawns or ENEMY_SPAWNS)]
        self.pickups = list(pickup_spawns or PICKUP_SPAWNS)
        self.projectiles: list[Projectile] = []
        self.corpses     = []
        self.messages    = []
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
        self.paused      = False

        self.renderer      = renderer
        self._input_handler = input_handler
        self.last_t        = time.time()
        self.start_t       = time.time()

    def _msg(self, text: str):
        self.messages.append((text, time.time() + 2.5))

    # ---- Input -------------------------------------------------------------

    def _input(self, dt: float):
        import engine as _eng
        keys, quit_req = self._input_handler.process_events()

        if quit_req:
            self.running = False
            return

        if self._input_handler.just_pressed(_eng.PAUSE):
            self.paused = not self.paused

        if self.paused:
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

        if self._input_handler.just_pressed(_eng.USE):
            self._use_door()

        for sym, idx in _eng.WEAPON_KEYS.items():
            if sym in keys:
                p.weapon = idx

    # ---- Door interaction --------------------------------------------------

    def _use_door(self):
        p    = self.player
        dx_  = math.cos(p.angle)
        dy_  = math.sin(p.angle)
        for reach in (1.0, 1.5):
            door_ix = int(p.x + dx_ * reach)
            door_iy = int(p.y + dy_ * reach)
            if self.world.cell_type(door_ix, door_iy) == 5:
                self.world.toggle_door(door_ix, door_iy)
                opened = (door_ix, door_iy) in self.world._open_doors
                self._msg('[E] Door ' + ('opened' if opened else 'closed'))
                return

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
                p.combo     += 1
                p.combo_t    = time.time() + 3.0
                bonus        = 150 * max(1, p.combo)
                p.score     += bonus
                self.corpses.append((best_e.x, best_e.y))
                if p.combo > 1:
                    self._msg(f"x{p.combo} COMBO! +{bonus}pts [{best_d:.1f}m]")
                else:
                    self._msg(f"KILL! +{bonus}pts  [{best_d:.1f}m]")
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
        p = self.player
        if p.combo > 0 and p.combo_t > 0 and now > p.combo_t:
            p.combo = 0
        if p.health <= 0:
            self.running = False
            return

        # Update projectiles
        proj_dmg = 0
        surviving = []
        for proj in self.projectiles:
            d = proj.update(dt, self.player, self.world)
            if d:
                proj_dmg += d
            if proj.alive:
                surviving.append(proj)
        self.projectiles = surviving
        if proj_dmg:
            self.player.health -= proj_dmg
            self.dmg_flash      = 0.55
            self.hit_shake      = 0.06
            self._msg(f"IMP HIT! -{proj_dmg}hp")
            if self.player.health <= 0:
                self.running = False

        alive = [e for e in self.enemies if e.state != 'dead']
        if not alive:
            self.won     = True
            self.running = False
            return

        for e in alive:
            dmg = e.update(dt, self.player, self.world, now, self.projectiles)
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
        target = 1.0 / 35.0
        while self.running:
            now = time.time()
            dt  = min(now - self.last_t, 0.05)
            self.last_t = now
            self._input(dt)
            if not self.paused:
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
                renderer.scores_screen(ctx, load_scores())
                continue

            # ── Wave run ────────────────────────────────────────────────────
            rng          = random.Random()
            carry_score  = 0
            carry_ammo   = {'bullet': 50, 'shell': 15}
            carry_weapon = 0
            carry_health = 100

            for wave in range(1, WAVE_MAX + 1):
                grid, pstart, espawns, pspawns = generate_map(wave, rng)

                inp.clear()
                game = Game(renderer, inp, wave=wave, grid=grid,
                            player_start=pstart, enemy_spawns=espawns,
                            pickup_spawns=pspawns)
                game.player.score  = carry_score
                game.player.ammo   = dict(carry_ammo)
                game.player.weapon = carry_weapon
                game.player.health = carry_health

                game.run(ctx)
                save_score(game.player.score)

                if not game.won:
                    renderer.end_screen(game, ctx, load_scores())
                    break

                # Wave cleared — carry state + refill bonus
                carry_score  = game.player.score
                carry_ammo   = dict(game.player.ammo)
                carry_ammo['bullet'] = min(99, carry_ammo.get('bullet', 0) + 20)
                carry_ammo['shell']  = min(30, carry_ammo.get('shell',  0) + 5)
                carry_weapon = game.player.weapon
                carry_health = min(100, game.player.health + 30)

                if wave < WAVE_MAX:
                    renderer.wave_clear_screen(ctx, wave, wave + 1)
                else:
                    renderer.end_screen(game, ctx, load_scores())

            inp.clear()


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
