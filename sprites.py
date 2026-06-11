"""ASCII art data — shading tables, gun frames, enemy body layouts."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Wall / floor shading palettes
# ---------------------------------------------------------------------------

SHADE_UNI   = ['█', '▓', '▒', '░', '·']
SHADE_ASCII = ['@', '#', '8', 'x', '*', ',', ':', '.']

# ---------------------------------------------------------------------------
# Width helpers
# ---------------------------------------------------------------------------

def _fit(rows: list[str], w: int) -> list[str]:
    """Pad (or truncate) every row to exactly *w* characters."""
    return [(r + ' ' * w)[:w] for r in rows]

# ---------------------------------------------------------------------------
# Gun sprites  (GUN_H rows × GUN_W chars each)
# ---------------------------------------------------------------------------

GUN_W = 40
GUN_H = 15

GUN_SPRITES = [

    # ── 0  Pistol ─────────────────────────────────────────────────────────
    _fit([
        '',
        '               .----------.              ',
        '  ____________/            \\____________ ',
        ' /  [        P I S T O L        ]       \\',
        '|    |__________________________________|',
        '|    |__________________________________| ',
        ' \\             |          |            / ',
        '               |  [grip]  |              ',
        '              /|__________|\\             ',
        '             / /|        |\\ \\            ',
        '            (__/|  [=M=] |\\__)           ',
        '               |        |                ',
        '               |________|                ',
        '',
        '',
    ], GUN_W),

    # ── 1  Shotgun ────────────────────────────────────────────────────────
    _fit([
        '',
        '  ======================================',
        ' /======================================\\',
        '|========================================|',
        '|========================================|',
        '|====================|                   ',
        '|====================|                   ',
        '                     |___________        ',
        '                    /             \\      ',
        '                   ( [o]       [o] )     ',
        '                    \\    [===]    /      ',
        '                     \\_____________/     ',
        '',
        '',
        '',
    ], GUN_W),

    # ── 2  Rifle ──────────────────────────────────────────────────────────
    _fit([
        '   _____________________________________  ',
        '  /_____________________________________| ',
        ' |_____________________________________|  ',
        ' |====[ R  I  F  L  E ]====|            ',
        ' |_____________________________________|  ',
        '           |===================|          ',
        '           |                   |          ',
        '           |    [  scope  ]    |          ',
        '           |___________________|          ',
        '/                                       \\ ',
        '|_______________________________________|  ',
        '\\                                       / ',
        '',
        '',
        '',
    ], GUN_W),
]

# ---------------------------------------------------------------------------
# Muzzle-flash frames  (GUN_W chars, 3 animation frames)
# ---------------------------------------------------------------------------

GUN_FLASH = _fit([
    '              \\\\*+*+*+*//              ',
    '               \\*+*+*+*/               ',
    '                *+*+*+*                ',
], GUN_W)

# ---------------------------------------------------------------------------
# Enemy 2-D sprites
#   ENEMY_SPRITES_2D[kind] = [frame_0_rows, frame_1_rows]
#   All rows in one sprite must have the same length (ENEMY_W).
#   Space = transparent.
# ---------------------------------------------------------------------------

ENEMY_W = 21      # width of all enemy sprite rows

ENEMY_SPRITES_2D: dict[str, list[list[str]]] = {

    # ── Zombie ────────────────────────────────────────────────────────────
    'zombie': [
        # frame 0 — standing
        _fit([
            '      /~~~~~\\      ',
            '     | . . . |     ',
            '     |   ^   |     ',
            '     | ----- |     ',
            '      \\_____/      ',
            '       |ZZZ|       ',
            '  /----+ZZZ+----\\  ',
            ' /     |ZZZ|     \\ ',
            '|      |ZZZ|      |',
            '|      |===|      |',
            ' \\     |   |     / ',
            '  \\    |   |    /  ',
            '   \\   | | |   /   ',
            '    \\  |/ \\|  /    ',
            '       |   |       ',
            '      /|   |\\      ',
            '     / |   | \\     ',
            '    /  |___|  \\    ',
        ], ENEMY_W),
        # frame 1 — walking
        _fit([
            '      /~~~~~\\      ',
            '     | . . . |     ',
            '     |   ^   |     ',
            '     | ----- |     ',
            '      \\_____/      ',
            '       |ZZZ|       ',
            '  /----+ZZZ+----\\  ',
            ' /     |ZZZ|     \\ ',
            '|      |ZZZ|      |',
            '|      |===|      |',
            ' \\     |   |     / ',
            '  \\    |   |    /  ',
            '   \\   | | |   /   ',
            '    \\  |   |  /    ',
            '       |   |       ',
            '      /|   | \\     ',
            '     / |   |  \\    ',
            '    /  |___|   \\   ',
        ], ENEMY_W),
    ],

    # ── Demon ─────────────────────────────────────────────────────────────
    'demon': [
        # frame 0 — standing
        _fit([
            ' /\\         /\\     ',
            '/  \\_______/  \\    ',
            '   | [D] [D] |     ',
            '   |   ===   |     ',
            '   |  /---\\  |     ',
            '    \\_______/      ',
            '   /{D_D_D_D}\\     ',
            '  |{DDDDDDDDD}|    ',
            '  |{DDDDDDDDD}|    ',
            '  |{_________}|    ',
            '  {|         |}    ',
            ' //|         |\\\\   ',
            '// |         | \\\\  ',
            '/  |         |  \\  ',
            '   |    |    |     ',
            '   |   / \\   |     ',
            '   |  /   \\  |     ',
            '   |_/     \\_|     ',
        ], ENEMY_W),
        # frame 1 — walking
        _fit([
            ' /\\         /\\     ',
            '/  \\_______/  \\    ',
            '   | [D] [D] |     ',
            '   |   ===   |     ',
            '   |  /---\\  |     ',
            '    \\_______/      ',
            '   /{D_D_D_D}\\     ',
            '  |{DDDDDDDDD}|    ',
            '  |{DDDDDDDDD}|    ',
            '  |{_________}|    ',
            '  {|         |}    ',
            '  /|         |\\\\   ',
            ' /  |       |  \\   ',
            '/   |_______|   \\  ',
            '    |       |       ',
            '   /|       |\\      ',
            '  / |       | \\     ',
            ' /  |_______|  \\    ',
        ], ENEMY_W),
    ],

    # ── Imp ───────────────────────────────────────────────────────────────
    'imp': [
        # frame 0 — hovering
        _fit([
            '  ^  [^.^]  ^      ',
            '  |   (o.o)  |     ',
            ' /|  |-_-_-| |\\    ',
            '/ |   \\___/  | \\   ',
            '  |   ~I~I~  |     ',
            ' /| --{I_I}--| \\   ',
            '/ |   |I_I|  |  \\  ',
            '  |   |___|  |     ',
            '  |  /|| ||\\  |    ',
            '  | /  |_|  \\ |    ',
        ], ENEMY_W),
        # frame 1 — lunging
        _fit([
            '    [^.^]          ',
            '    (o.o) -->      ',
            '   |-_-_-|  -->    ',
            '    \\___/   -->    ',
            '    ~I~I~          ',
            '  --{I_I}--        ',
            '    |I_I|          ',
            '    |___|          ',
            '   /|  |\\  -->     ',
            '  / |  |   -->     ',
        ], ENEMY_W),
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
            elif ws[0] != ENEMY_W:
                errors.append(f'{kind} frame {fnum}: width={ws[0]} (need {ENEMY_W})')

    if errors:
        raise AssertionError('Sprite width errors:\n' + '\n'.join(errors))


_validate()
