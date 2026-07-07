#!/usr/bin/env python3
"""Unit tests for game.py — no curses required."""

import math
import random
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from game import (World, Player, Enemy, Projectile, WEAPONS, WORLD_MAP,
                  MAP_W, MAP_H, generate_map, WAVE_MAX)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class TestWorld(unittest.TestCase):

    def setUp(self):
        self.w = World()

    # -- is_wall --

    def test_outer_border_is_wall(self):
        self.assertTrue(self.w.is_wall(0.5, 0.5))    # top-left corner cell
        self.assertTrue(self.w.is_wall(0.5, MAP_H - 1 + 0.5))
        self.assertTrue(self.w.is_wall(MAP_W - 1 + 0.5, 0.5))

    def test_interior_empty_cell(self):
        self.assertFalse(self.w.is_wall(1.5, 1.5))
        self.assertFalse(self.w.is_wall(12.0, 12.0))

    def test_out_of_bounds_is_wall(self):
        self.assertTrue(self.w.is_wall(-1.0,  0.0))
        self.assertTrue(self.w.is_wall( 0.0, -1.0))
        self.assertTrue(self.w.is_wall(float(MAP_W), 0.0))
        self.assertTrue(self.w.is_wall(0.0, float(MAP_H)))

    def test_float_truncation_empty(self):
        # (1.99, 1.99) → cell (1,1) = 0 in WORLD_MAP
        self.assertFalse(self.w.is_wall(1.99, 1.99))

    def test_float_truncation_wall(self):
        # (0.01, 0.01) → cell (0,0) = 1
        self.assertTrue(self.w.is_wall(0.01, 0.01))

    def test_custom_grid(self):
        grid = [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]
        w = World(grid)
        self.assertTrue(w.is_wall(0.5, 0.5))
        self.assertFalse(w.is_wall(1.5, 1.5))
        self.assertEqual(w.w, 3)
        self.assertEqual(w.h, 3)

    # -- cell_type --

    def test_cell_type_wall(self):
        self.assertEqual(self.w.cell_type(0.5, 0.5), 1)

    def test_cell_type_empty(self):
        self.assertEqual(self.w.cell_type(1.5, 1.5), 0)

    def test_cell_type_oob(self):
        self.assertEqual(self.w.cell_type(-1.0, 0.0), 1)

    # -- can_step --

    def test_can_step_open_area(self):
        # Row 2 is fully open from x=1..22; r=0.28 won't touch any wall here
        self.assertTrue(self.w.can_step(5.0, 2.0))

    def test_cannot_step_near_west_wall(self):
        # x=0.2 means the left radius touches the wall at x=0
        self.assertFalse(self.w.can_step(0.2, 2.0))

    def test_can_step_custom_radius(self):
        # With tiny radius, can step very close to wall
        self.assertTrue(self.w.can_step(1.05, 1.5, r=0.01))

    # -- has_los --

    def test_los_open_corridor(self):
        self.assertTrue(self.w.has_los(2.0, 2.0, 4.0, 2.0))

    def test_los_blocked_by_outer_wall(self):
        # Point inside vs point outside (negative x)
        self.assertFalse(self.w.has_los(2.0, 2.0, -1.0, 2.0))

    def test_los_blocked_by_inner_wall(self):
        # Use a controlled grid with a wall in the middle
        grid = [
            [1, 1, 1, 1, 1],
            [1, 0, 1, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        w = World(grid)
        # (1,1) → (3,1) has cell (2,1)=1 between them
        self.assertFalse(w.has_los(1.5, 1.5, 3.5, 1.5))

    def test_los_same_point(self):
        self.assertTrue(self.w.has_los(5.0, 5.0, 5.0, 5.0))

    # -- cast_ray --

    def test_cast_ray_returns_four_tuple(self):
        result = self.w.cast_ray(2.5, 2.5, 0.0, 60, 120)
        self.assertEqual(len(result), 4)

    def test_cast_ray_dist_positive(self):
        for angle in [0, math.pi / 4, math.pi / 2, math.pi, 3 * math.pi / 2]:
            dist, _, _, _ = self.w.cast_ray(2.5, 2.5, angle, 60, 120)
            self.assertGreater(dist, 0.0)

    def test_cast_ray_always_hits_wall(self):
        # Inside a bounded map, every ray must hit a wall
        for col in range(0, 120, 10):
            dist, wtype, _, _ = self.w.cast_ray(2.5, 2.5, 0.0, col, 120)
            self.assertLess(dist, 64.0)
            self.assertGreater(wtype, 0)

    def test_cast_ray_wall_x_in_range(self):
        for col in range(0, 120, 15):
            for angle in [0, math.pi / 3, math.pi / 2]:
                _, _, _, wx = self.w.cast_ray(2.5, 2.5, angle, col, 120)
                self.assertGreaterEqual(wx, 0.0)
                self.assertLess(wx, 1.0)

    def test_cast_ray_side_is_0_or_1(self):
        for col in range(0, 120, 20):
            _, _, side, _ = self.w.cast_ray(2.5, 2.5, 0.0, col, 120)
            self.assertIn(side, (0, 1))

    def test_cast_ray_facing_east_short_dist(self):
        # Player at (2.5, 1.5) facing east — open corridor until east wall
        dist, _, _, _ = self.w.cast_ray(2.5, 1.5, 0.0, 60, 120)
        self.assertLess(dist, 25.0)   # must hit something before far clip
        self.assertGreater(dist, 0.0)


# ---------------------------------------------------------------------------
# Projectile
# ---------------------------------------------------------------------------

class TestProjectile(unittest.TestCase):

    def setUp(self):
        self.world = World()

    def _open_world(self):
        return World([[0] * 10 for _ in range(10)])

    def test_projectile_moves(self):
        p   = Player()
        p.x, p.y = 5.0, 5.0
        proj = Projectile(2.0, 5.0, Projectile.SPEED, 0.0, 10)
        proj.update(0.5, p, self.world)   # moves east 3.5 u
        self.assertGreater(proj.x, 2.0)

    def test_hits_player(self):
        p = Player()
        p.x, p.y = 3.0, 5.0
        proj = Projectile(2.0, 5.0, Projectile.SPEED, 0.0, 10)
        dmg = proj.update(1.0, p, self.world)   # will reach player
        self.assertGreater(dmg, 0)
        self.assertFalse(proj.alive)

    def test_blocked_by_wall(self):
        p = Player()
        p.x, p.y = 5.0, 5.0
        # fire into outer wall (east wall at x≈24)
        proj = Projectile(20.0, 2.0, Projectile.SPEED, 0.0, 10)
        for _ in range(30):
            proj.update(0.1, p, self.world)
        self.assertFalse(proj.alive)

    def test_miss_does_no_damage(self):
        p = Player()
        p.x, p.y = 2.5, 2.5
        proj = Projectile(5.0, 2.5, Projectile.SPEED, 0.0, 10)  # heading away
        dmg = proj.update(0.1, p, self.world)
        self.assertEqual(dmg, 0)

    def test_imp_stats(self):
        e = Enemy(5.0, 5.0, 'imp')
        self.assertEqual(e.char, 'I')
        self.assertTrue(e.ranged)
        self.assertEqual(e.health, 20)

    def test_imp_shoots_when_chasing(self):
        world = World()
        p = Player()
        p.x, p.y = 7.0, 2.0
        imp = Enemy(5.0, 2.0, 'imp')
        imp.state   = 'chase'
        imp.shot_cd = 0.0
        projs: list = []
        imp.update(0.1, p, world, 1000.0, projs)
        self.assertEqual(len(projs), 1)
        self.assertIsInstance(projs[0], Projectile)


# ---------------------------------------------------------------------------
# Doors
# ---------------------------------------------------------------------------

class TestDoors(unittest.TestCase):

    def setUp(self):
        self.world = World([
            [1, 1, 1],
            [1, 5, 1],
            [1, 1, 1],
        ])

    def test_closed_door_is_wall(self):
        self.assertTrue(self.world.is_wall(1.5, 1.5))

    def test_open_door_passable(self):
        self.world.toggle_door(1, 1)
        self.assertFalse(self.world.is_wall(1.5, 1.5))

    def test_toggle_twice_closes(self):
        self.world.toggle_door(1, 1)
        self.world.toggle_door(1, 1)
        self.assertTrue(self.world.is_wall(1.5, 1.5))

    def test_can_step_through_open_door(self):
        self.world.toggle_door(1, 1)
        self.assertTrue(self.world.can_step(1.5, 1.5, r=0.1))

    def test_cannot_step_through_closed_door(self):
        self.assertFalse(self.world.can_step(1.5, 1.5, r=0.1))

    def test_cell_type_returns_5_for_door(self):
        self.assertEqual(self.world.cell_type(1.5, 1.5), 5)

    def test_open_doors_independent_per_world(self):
        w2 = World(self.world.grid)
        self.world.toggle_door(1, 1)
        # w2 shares grid data but has its own _open_doors
        self.assertTrue(w2.is_wall(1.5, 1.5))


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

class TestPlayer(unittest.TestCase):

    def test_initial_values(self):
        p = Player()
        self.assertAlmostEqual(p.x, 2.5)
        self.assertAlmostEqual(p.y, 2.5)
        self.assertAlmostEqual(p.angle, 0.0)
        self.assertEqual(p.health, 100)
        self.assertIsInstance(p.ammo, dict)
        self.assertIn('bullet', p.ammo)
        self.assertIn('shell', p.ammo)
        self.assertEqual(p.ammo['bullet'], 50)
        self.assertEqual(p.ammo['shell'], 15)
        self.assertEqual(p.weapon, 0)
        self.assertEqual(p.score, 0)

    def test_current_ammo_pistol(self):
        p = Player()
        p.weapon = 0   # pistol uses bullet
        self.assertEqual(p.current_ammo, p.ammo['bullet'])

    def test_current_ammo_shotgun(self):
        p = Player()
        p.weapon = 1   # shotgun uses shell
        self.assertEqual(p.current_ammo, p.ammo['shell'])

    def test_weapons_list_structure(self):
        for w in WEAPONS:
            self.assertIn('name',      w)
            self.assertIn('cd',        w)
            self.assertIn('dmg',       w)
            self.assertIn('ammo_type', w)
            self.assertIn('pellets',   w)
            self.assertGreater(w['pellets'], 0)

    def test_two_players_independent(self):
        p1, p2 = Player(), Player()
        p1.health = 50
        self.assertEqual(p2.health, 100)


# ---------------------------------------------------------------------------
# Enemy
# ---------------------------------------------------------------------------

class TestEnemy(unittest.TestCase):

    def setUp(self):
        self.world = World()

    def test_zombie_stats(self):
        e = Enemy(5.0, 5.0, 'zombie')
        self.assertEqual(e.health, 30)
        self.assertEqual(e.char, 'Z')
        self.assertEqual(e.cpair, 1)
        self.assertEqual(e.state, 'patrol')

    def test_demon_stats(self):
        e = Enemy(5.0, 5.0, 'demon')
        self.assertEqual(e.health, 60)
        self.assertEqual(e.char, 'D')
        self.assertEqual(e.cpair, 7)

    def test_dead_returns_zero_damage(self):
        e = Enemy(5.0, 5.0)
        e.state = 'dead'
        p = Player()
        dmg = e.update(0.5, p, self.world, 1000.0)
        self.assertEqual(dmg, 0)

    def test_dead_does_not_move(self):
        e = Enemy(5.0, 5.0)
        e.state = 'dead'
        p = Player()
        e.update(1.0, p, self.world, 1000.0)
        self.assertAlmostEqual(e.x, 5.0)
        self.assertAlmostEqual(e.y, 5.0)

    def test_los_triggers_chase(self):
        # Both in open area of row 2, close together
        e = Enemy(5.0, 2.0)
        p = Player()
        p.x, p.y = 5.0, 2.5
        e.update(0.1, p, self.world, 1000.0)
        self.assertEqual(e.state, 'chase')

    def test_wall_blocks_los(self):
        # Controlled grid: wall separates enemy from player
        grid = [
            [1, 1, 1, 1, 1],
            [1, 0, 1, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        w = World(grid)
        e = Enemy(1.5, 1.5, 'zombie')
        p = Player()
        p.x, p.y = 3.5, 1.5
        e.update(0.1, p, w, 1000.0)
        self.assertEqual(e.state, 'patrol')  # wall blocks LOS

    def test_chase_moves_toward_player(self):
        e = Enemy(10.0, 2.0)
        e.state = 'chase'
        p = Player()
        p.x, p.y = 8.0, 2.0   # player is to the west
        old_x = e.x
        e.update(0.5, p, self.world, 1000.0)
        self.assertLess(e.x, old_x)   # moved west

    def test_attack_when_adjacent(self):
        e = Enemy(2.6, 2.5)
        e.state = 'chase'
        e.last_attack = 0.0
        p = Player()
        p.x, p.y = 2.5, 2.5   # dist ≈ 0.1 < 0.9
        # First adjacent update starts the 0.35s windup (no damage yet)…
        dmg = e.update(0.1, p, self.world, 1000.0)
        self.assertEqual(dmg, 0)
        self.assertGreater(e.windup_t, 0)
        # …and after the windup elapses the hit lands.
        dmg = e.update(0.1, p, self.world, 1000.5)
        zombie_max = Enemy.KINDS['zombie']['dmg'][1]
        zombie_min = Enemy.KINDS['zombie']['dmg'][0]
        self.assertGreaterEqual(dmg, zombie_min)
        self.assertLessEqual(dmg, zombie_max)

    def test_windup_cancelled_when_player_escapes(self):
        e = Enemy(2.6, 2.5)
        e.state = 'chase'
        e.last_attack = 0.0
        p = Player()
        p.x, p.y = 2.5, 2.5
        e.update(0.1, p, self.world, 1000.0)   # windup starts
        p.x = 5.5                              # player runs away
        dmg = e.update(0.1, p, self.world, 1000.5)
        self.assertEqual(dmg, 0)
        self.assertEqual(e.windup_t, 0.0)

    def test_attack_cooldown_respected(self):
        e = Enemy(2.6, 2.5)
        e.state = 'chase'
        e.last_attack = 999.5   # attacked 0.5s ago; cooldown = 1.0s
        p = Player()
        p.x, p.y = 2.5, 2.5
        dmg = e.update(0.1, p, self.world, 1000.0)
        self.assertEqual(dmg, 0)

    def test_patrol_timer_resets_direction(self):
        e = Enemy(12.0, 12.0)
        e.patrol_timer = 0.001  # about to expire
        old_vx, old_vy = e.patrol_vx, e.patrol_vy
        p = Player()
        p.x, p.y = 20.0, 20.0  # far away, no LOS
        e.update(0.1, p, self.world, 1000.0)
        # After timer reset, direction may change
        # We just check it's a float and enemy didn't crash
        self.assertIsInstance(e.patrol_vx, float)


# ---------------------------------------------------------------------------
# Pickup collection (logic extracted for testing)
# ---------------------------------------------------------------------------

def _collect(player, pickups):
    """Mirror of Game.update() pickup logic."""
    remaining = []
    for pk in pickups:
        dist = math.sqrt((pk[0] - player.x) ** 2 + (pk[1] - player.y) ** 2)
        if dist < 0.75:
            if pk[2] == 'hp':
                gained = min(25, 100 - player.health)
                player.health += gained
            else:
                gained = min(15, 99 - player.ammo['bullet'])
                player.ammo['bullet'] += gained
        else:
            remaining.append(pk)
    return remaining


class TestPickups(unittest.TestCase):

    def test_collect_hp_pickup(self):
        p = Player()
        p.health = 70
        rem = _collect(p, [(2.5, 2.5, 'hp')])
        self.assertEqual(rem, [])
        self.assertEqual(p.health, 95)  # 70 + min(25, 30)

    def test_collect_ammo_pickup(self):
        p = Player()
        p.ammo['bullet'] = 30
        _collect(p, [(2.5, 2.5, 'ammo')])
        self.assertEqual(p.ammo['bullet'], 45)

    def test_no_collect_far_pickup(self):
        p = Player()
        rem = _collect(p, [(20.0, 20.0, 'hp')])
        self.assertEqual(len(rem), 1)
        self.assertEqual(p.health, 100)

    def test_hp_capped_at_100(self):
        p = Player()
        p.health = 99
        _collect(p, [(2.5, 2.5, 'hp')])
        self.assertLessEqual(p.health, 100)

    def test_ammo_capped_at_99(self):
        p = Player()
        p.ammo['bullet'] = 90
        _collect(p, [(2.5, 2.5, 'ammo')])
        self.assertLessEqual(p.ammo['bullet'], 99)

    def test_multiple_pickups_only_near_collected(self):
        p = Player()
        p.x, p.y = 2.5, 2.5
        pickups = [(2.5, 2.5, 'hp'), (15.0, 15.0, 'ammo')]
        rem = _collect(p, pickups)
        self.assertEqual(len(rem), 1)
        self.assertEqual(rem[0][2], 'ammo')


# ---------------------------------------------------------------------------
# Hitscan shooting (logic extracted for testing)
# ---------------------------------------------------------------------------

def _hitscan(player, enemies, world):
    """Mirror of Game._shoot() target selection."""
    rdx = math.cos(player.angle)
    rdy = math.sin(player.angle)
    best_e, best_d = None, 22.0
    for e in enemies:
        if e.state == 'dead':
            continue
        ex, ey = e.x - player.x, e.y - player.y
        dist   = math.sqrt(ex * ex + ey * ey)
        if dist < 0.3:
            continue
        dot  = ex * rdx + ey * rdy
        perp = abs(ex * rdy - ey * rdx)
        if dot <= 0 or perp > 0.45 or dot >= best_d:
            continue
        if world.has_los(player.x, player.y, e.x, e.y):
            best_e, best_d = e, dot
    return best_e, best_d


class TestHitscan(unittest.TestCase):

    def setUp(self):
        self.world = World()

    def test_hit_enemy_directly_ahead(self):
        p = Player()
        p.x, p.y, p.angle = 2.5, 2.5, 0.0   # facing east
        e = Enemy(5.0, 2.5)
        best, _ = _hitscan(p, [e], self.world)
        self.assertIs(best, e)

    def test_miss_enemy_behind(self):
        p = Player()
        p.x, p.y, p.angle = 5.0, 2.5, 0.0   # facing east
        e = Enemy(2.5, 2.5)                   # enemy is west
        best, _ = _hitscan(p, [e], self.world)
        self.assertIsNone(best)

    def test_miss_enemy_perpendicular(self):
        p = Player()
        p.x, p.y, p.angle = 2.5, 2.5, 0.0   # facing east
        e = Enemy(2.5, 8.0)                   # due north
        best, _ = _hitscan(p, [e], self.world)
        self.assertIsNone(best)

    def test_skip_dead_enemy(self):
        p = Player()
        p.x, p.y, p.angle = 2.5, 2.5, 0.0
        e = Enemy(5.0, 2.5)
        e.state = 'dead'
        best, _ = _hitscan(p, [e], self.world)
        self.assertIsNone(best)

    def test_nearest_enemy_wins(self):
        p = Player()
        p.x, p.y, p.angle = 2.5, 2.5, 0.0
        near = Enemy(4.0, 2.5)
        far  = Enemy(8.0, 2.5)
        best, _ = _hitscan(p, [near, far], self.world)
        self.assertIs(best, near)

    def test_wall_blocks_shot(self):
        # Controlled grid: wall between player and enemy
        grid = [
            [1, 1, 1, 1, 1, 1],
            [1, 0, 1, 0, 0, 1],
            [1, 1, 1, 1, 1, 1],
        ]
        w = World(grid)
        p = Player()
        p.x, p.y, p.angle = 1.5, 1.5, 0.0   # facing east (angle=0)
        e = Enemy(3.5, 1.5)
        best, _ = _hitscan(p, [e], w)
        self.assertIsNone(best)


# ---------------------------------------------------------------------------
# Procedural map generation
# ---------------------------------------------------------------------------

class TestMapGen(unittest.TestCase):

    def _gen(self, wave: int = 1, seed: int = 42):
        return generate_map(wave, random.Random(seed))

    def test_returns_four_items(self):
        result = self._gen()
        self.assertEqual(len(result), 4)

    def test_grid_outer_border_is_solid(self):
        grid, _, _, _ = self._gen()
        H, W = len(grid), len(grid[0])
        for x in range(W):
            self.assertNotEqual(grid[0][x],   0, f'top border open x={x}')
            self.assertNotEqual(grid[H-1][x], 0, f'bottom border open x={x}')
        for y in range(H):
            self.assertNotEqual(grid[y][0],   0, f'left border open y={y}')
            self.assertNotEqual(grid[y][W-1], 0, f'right border open y={y}')

    def test_player_start_in_open_cell(self):
        grid, (px, py), _, _ = self._gen()
        self.assertEqual(grid[int(py)][int(px)], 0)

    def test_has_enemies(self):
        _, _, enemies, _ = self._gen()
        self.assertGreater(len(enemies), 0)

    def test_enemy_spawns_on_open_cell(self):
        grid, _, enemies, _ = self._gen()
        for ex, ey, kind in enemies:
            self.assertEqual(grid[int(ey)][int(ex)], 0,
                             f'{kind} spawned on wall at ({ex},{ey})')

    def test_wave5_more_enemies_than_wave1(self):
        _, _, e1, _ = generate_map(1, random.Random(42))
        _, _, e5, _ = generate_map(5, random.Random(42))
        self.assertGreater(len(e5), len(e1))

    def test_has_pickups(self):
        _, _, _, pickups = self._gen()
        self.assertGreater(len(pickups), 0)

    def test_world_queries_work_on_generated_grid(self):
        grid, (px, py), _, _ = self._gen()
        w = World(grid)
        self.assertFalse(w.is_wall(px, py))
        self.assertTrue(w.is_wall(0.5, 0.5))

    def test_wave_max_constant(self):
        self.assertGreaterEqual(WAVE_MAX, 3)

    def test_different_seeds_differ(self):
        g1, _, _, _ = generate_map(1, random.Random(1))
        g2, _, _, _ = generate_map(1, random.Random(999))
        # Grids won't be identical (though theoretically possible; vanishingly unlikely)
        self.assertNotEqual(g1, g2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
