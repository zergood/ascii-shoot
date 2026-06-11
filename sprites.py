"""ASCII art data — shading tables, gun frames, enemy body layouts."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Wall / floor shading palettes
# ---------------------------------------------------------------------------

SHADE_UNI   = ['█', '▓', '▒', '░', '·']
SHADE_ASCII = ['#', '@', '+', ':', '.']

# ---------------------------------------------------------------------------
# Gun sprites  (GUN_H rows × GUN_W chars each)
# Renderer centres them at  cx - GUN_W // 2
# ---------------------------------------------------------------------------

GUN_W = 23
GUN_H = 10

GUN_SPRITES = [
    # ── 0  Pistol ─────────────────────────────────────────────────────────
    [
        '                       ',   # 23
        '          .------.     ',   # 23
        '   _______|      |___  ',   # 23
        '  | [   PISTOL   ]  |  ',   # 23
        '  |_________________|  ',   # 23
        '          |     |      ',   # 23
        '          |     |      ',   # 23
        '         /       \\     ',   # 23
        '        / /|   |\\ \\    ',   # 23
        '       (___| |___)     ',   # 23
    ],
    # ── 1  Shotgun ────────────────────────────────────────────────────────
    [
        '                       ',   # 23
        '  ===================  ',   # 23
        ' /=================== \\',   # 23
        '|=====================|',   # 23
        '|=====================|',   # 23
        '|===========|          ',   # 23
        '             |______   ',   # 23
        '            /        \\ ',   # 23
        '           (   [  ]   )',   # 23
        '            \\_______/  ',   # 23
    ],
    # ── 2  Rifle ──────────────────────────────────────────────────────────
    [
        '  ___________________  ',   # 23
        ' /___________________| ',   # 23
        '|___________________|  ',   # 23
        '|===[ RIFLE ]===|      ',   # 23
        '|___________________|  ',   # 23
        '     |===========|     ',   # 23
        '     |           |     ',   # 23
        '     |___________|     ',   # 23
        '/                     \\',   # 23
        '(_____________________)',    # 23
    ],
]


# ---------------------------------------------------------------------------
# Muzzle-flash frames  (GUN_W chars each, 3 animation frames)
# ---------------------------------------------------------------------------

GUN_FLASH = [
    '       \\*+*+*/         ',   # 23
    '        *+*+*          ',   # 23
    '         *+*           ',   # 23
]

# ---------------------------------------------------------------------------
# Enemy 2-D sprites
#   ENEMY_SPRITES_2D[kind] = [frame_0_rows, frame_1_rows]
#   All rows in one sprite must have the same length.
#   Space = transparent.
# ---------------------------------------------------------------------------

ENEMY_SPRITES_2D: dict[str, list[list[str]]] = {

    # ── Zombie ───────────────────────────────────────────────────────────
    'zombie': [
        # frame 0 — standing
        [
            '   /---\\   ',   # 11
            '  | o o |  ',   # 11
            '  |  ^  |  ',   # 11
            '  | --- |  ',   # 11
            '   \\___/   ',   # 11
            '   |ZZZ|   ',   # 11
            ' --[ZZZ]-- ',   # 11
            '   |ZZZ|   ',   # 11
            '   |___|   ',   # 11
            '  /|   |\\  ',   # 11
            ' / |   | \\ ',   # 11
            '/  |___|  \\',   # 11
        ],
        # frame 1 — walking
        [
            '   /---\\   ',
            '  | o o |  ',
            '  |  ^  |  ',
            '  | --- |  ',
            '   \\___/   ',
            '   |ZZZ|   ',
            ' --[ZZZ]-- ',
            '   |ZZZ|   ',
            '   |___|   ',
            '  /  |  \\  ',   # 11
            ' /   |   \\ ',   # 11
            '/    |    \\',   # 11
        ],
    ],

    # ── Demon ────────────────────────────────────────────────────────────
    'demon': [
        # frame 0 — standing
        [
            ' /\\     /\\ ',   # 11
            '/  \\___/  \\',   # 11
            '  | D D |  ',   # 11
            '  | === |  ',   # 11
            '  |\\___/|  ',   # 11
            ' /{D_D_D}\\ ',   # 11
            '|{D_D_D_D}|',   # 11
            '|{_______}|',   # 11
            ' {|     |} ',   # 11
            ' //|   |\\\\ ',   # 11
            '// |   | \\\\',   # 11
            '/  |   |  \\',   # 11
            '   |___|   ',   # 11
        ],
        # frame 1 — walking
        [
            ' /\\     /\\ ',
            '/  \\___/  \\',
            '  | D D |  ',
            '  | === |  ',
            '  |\\___/|  ',
            ' /{D_D_D}\\ ',
            '|{D_D_D_D}|',
            '|{_______}|',
            ' {|     |} ',
            '   /|   |\\ ',   # 11
            '  / |   | \\',   # 11
            ' /  |___|  ',   # 11
            '    |      ',   # 11
        ],
    ],

    # ── Imp ──────────────────────────────────────────────────────────────
    'imp': [
        # frame 0 — hovering
        [
            '  [^.^]    ',   # 11
            '   (o.o)   ',   # 11
            '  |-_-_-|  ',   # 11
            '   \\___/   ',   # 11
            '   ~I~I~   ',   # 11
            ' --{I_I}-- ',   # 11
            '   |I_I|   ',   # 11
            '   |___|   ',   # 11
            '  /|| ||\\  ',   # 11
            ' /  |_|  \\ ',   # 11
        ],
        # frame 1 — lunging
        [
            '  [^.^]    ',
            '   (o.o)   ',
            '  |-_-_-|  ',
            '   \\___/   ',
            '   ~I~I~   ',
            ' --{I_I}-- ',
            '   |I_I|   ',
            '   |___|   ',
            '  /|  |\\   ',   # 11
            ' /  |  |   ',   # 11
        ],
    ],
}


def enemy_char(kind: str, ry: float, rx: float,
               frame: int, state: str) -> str | None:
    """Return the sprite character at normalised position (ry, rx) ∈ [0,1]².

    ry  — vertical fraction   (0 = top,  1 = bottom)
    rx  — horizontal fraction (0 = left, 1 = right)
    Returns None for transparent / out-of-bounds cells.
    """
    frames = ENEMY_SPRITES_2D.get(kind, ENEMY_SPRITES_2D['zombie'])
    f      = (frame % 2) if state == 'chase' else 0
    rows   = frames[f]

    row_idx = int(ry * len(rows))
    if row_idx >= len(rows):
        return None

    row_str = rows[row_idx]
    col_idx = min(int(rx * len(row_str)), len(row_str) - 1)
    ch      = row_str[col_idx]
    return None if ch == ' ' else ch


# ---------------------------------------------------------------------------
# Width validation — runs once at import time.
# ---------------------------------------------------------------------------

def _validate() -> None:
    errors: list[str] = []

    for i, lines in enumerate(GUN_SPRITES):
        widths = [len(l) for l in lines]
        if len(set(widths)) != 1 or widths[0] != GUN_W:
            errors.append(f'GUN_SPRITES[{i}]: widths={widths} (need all {GUN_W})')

    for i, line in enumerate(GUN_FLASH):
        if len(line) != GUN_W:
            errors.append(f'GUN_FLASH[{i}]: len={len(line)} (need {GUN_W})')

    for kind, (f0, f1) in ENEMY_SPRITES_2D.items():
        for fnum, rows in enumerate((f0, f1)):
            ws = [len(r) for r in rows]
            if len(set(ws)) != 1:
                errors.append(f'{kind} frame {fnum}: unequal widths {ws}')

    if errors:
        raise AssertionError('Sprite width errors:\n' + '\n'.join(errors))


_validate()
