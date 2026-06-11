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

    # ── Zombie (21 wide, 20 rows) ─────────────────────────────────────────
    'zombie': [
        # frame 0 — standing
        _fit([
            '     /~~~~~~~\\     ',  # row 0  head top
            '    |  O   O  |    ',  # row 1  eyes
            '    |    ^    |    ',  # row 2  nose
            '    |  ~~~~~  |    ',  # row 3  mouth
            '    |_________|    ',  # row 4  chin
            '     \\       /     ',  # row 5  neck
            '  /--+-------+--\\ ',  # row 6  shoulders
            ' /   |Z Z Z Z|   \\',  # row 7  shirt ZZZ
            '|    |Z Z Z Z|    |',  # row 8  shirt ZZZ
            '|    |Z Z Z Z|    |',  # row 9  shirt ZZZ
            '|    |=======|    |',  # row 10 belt
            ' \\   |       |   /',  # row 11 hips
            '  \\  |       |  / ',  # row 12 upper legs
            '     | |   | |     ',  # row 13 legs split
            '     | |   | |     ',  # row 14 legs
            '     | |   | |     ',  # row 15 legs
            '    /| |   | |\\   ',  # row 16 calves
            '   / | |   | | \\  ',  # row 17 calves
            '  /  |_|   |_|  \\ ',  # row 18 feet
            ' [___]       [___] ',  # row 19 feet flat
        ], ENEMY_W),
        # frame 1 — walking
        _fit([
            '     /~~~~~~~\\     ',  # row 0  head top
            '    |  O   O  |    ',  # row 1  eyes
            '    |    ^    |    ',  # row 2  nose
            '    |  ~~~~~  |    ',  # row 3  mouth
            '    |_________|    ',  # row 4  chin
            '     \\       /     ',  # row 5  neck
            '  /--+-------+--\\ ',  # row 6  shoulders
            ' /   |Z Z Z Z|   \\',  # row 7  shirt ZZZ
            '|    |Z Z Z Z|    |',  # row 8  shirt ZZZ
            '|    |Z Z Z Z|    |',  # row 9  shirt ZZZ
            '|    |=======|    |',  # row 10 belt
            ' \\   |       |   /',  # row 11 hips
            '  \\  |       |  / ',  # row 12 upper legs
            '     | |   | |     ',  # row 13 legs split
            '     | |   | |     ',  # row 14 legs
            '    /| |   | |     ',  # row 15 stride L
            '   / | |   | |\\   ',  # row 16 stride L
            '  /  | |   | | \\  ',  # row 17 stride R
            ' /   |_|   |_|  \\ ',  # row 18 feet
            '[___]         [___]',  # row 19 feet flat
        ], ENEMY_W),
    ],

    # ── Demon (21 wide, 22 rows) ───────────────────────────────────────────
    'demon': [
        # frame 0 — standing
        _fit([
            '  /\\         /\\    ',  # row 0  horns
            ' /  \\       /  \\   ',  # row 1  horns
            '/    \\_____/    \\  ',  # row 2  horn base / head top
            '|  D D D D D D  |  ',  # row 3  head fill
            '|  [D]     [D]  |  ',  # row 4  eyes
            '|   D  ===  D   |  ',  # row 5  nose bridge
            '|   /D-----D\\   |  ',  # row 6  fanged mouth
            ' \\_D_________D_/   ',  # row 7  jaw
            '  /{D_D_D_D_D}\\   ',  # row 8  neck / chest top
            ' |{D D D D D D}|  ',  # row 9  chest
            '/|{D D D D D D}|\\ ',  # row 10 wide arms
            '|{D_D_D_D_D_D_D}| ',  # row 11 mid body
            '\\|{D D D D D D}|/ ',  # row 12 wide arms
            ' |{D_D_D_D_D_D}|  ',  # row 13 lower body
            '  |D D D D D D|   ',  # row 14 hips
            '  |  |D D|  |     ',  # row 15 upper legs
            '  | /|   |\ |     ',  # row 16 legs
            '  |/ |   | \|     ',  # row 17 legs
            '  /  |   |  \     ',  # row 18 calves
            ' /   |   |   \    ',  # row 19 calves
            '/    |___|    \   ',  # row 20 ankles
            '[____]   [____]   ',  # row 21 clawed feet
        ], ENEMY_W),
        # frame 1 — stomping
        _fit([
            '  /\\         /\\    ',  # row 0  horns
            ' /  \\       /  \\   ',  # row 1  horns
            '/    \\_____/    \\  ',  # row 2  horn base
            '|  D D D D D D  |  ',  # row 3  head fill
            '|  [D]     [D]  |  ',  # row 4  eyes
            '|   D  ===  D   |  ',  # row 5  nose bridge
            '|   /D-----D\\   |  ',  # row 6  fanged mouth
            ' \\_D_________D_/   ',  # row 7  jaw
            '  /{D_D_D_D_D}\\   ',  # row 8  chest top
            ' |{D D D D D D}|  ',  # row 9  chest
            '/|{D D D D D D}|\\ ',  # row 10 wide arms
            '|{D_D_D_D_D_D_D}| ',  # row 11 mid body
            '\\|{D D D D D D}|/ ',  # row 12 wide arms
            ' |{D_D_D_D_D_D}|  ',  # row 13 lower body
            '  |D D D D D D|   ',  # row 14 hips
            '  |  |D D|  |     ',  # row 15 upper legs
            '  | /|   |  |     ',  # row 16 stomp L raised
            ' /|/ |   |  |     ',  # row 17 stomp L raised
            '/   |   |  |     ',  # row 18 stomp L
            '    /   |   |\    ',  # row 19 stomp R
            '   /    |___|  \  ',  # row 20 ankles
            '  [____]   [____] ',  # row 21 clawed feet
        ], ENEMY_W),
    ],

    # ── Imp (21 wide, 18 rows) ─────────────────────────────────────────────
    'imp': [
        # frame 0 — hovering
        _fit([
            '    *  [^.^]  *    ',  # row 0  antenna + head
            '   /|  (o.o)  |\   ',  # row 1  eyes
            '  / |  |-_-|  | \  ',  # row 2  face markings
            ' =--+--\___/--+--= ',  # row 3  wings out
            '=====  ~I~I~  =====',  # row 4  wings full + body
            ' =--+--{I_I}--+--= ',  # row 5  wings + midsection
            '  \ |  |I_I|  | /  ',  # row 6  body
            '   \|  |_I_|  |/   ',  # row 7  lower body
            '    |  /| |\  |    ',  # row 8  legs spread
            '    | / | | \ |    ',  # row 9  legs
            '    |/  | |  \|    ',  # row 10 legs lower
            '    /   | |   \    ',  # row 11 feet spread
            '   /    |_|    \   ',  # row 12 feet
            '  *      |      *  ',  # row 13 tail tip
            '         |         ',  # row 14 tail
            '        /|\        ',  # row 15 tail spread
            '       * | *       ',  # row 16 tail tips
            '         *         ',  # row 17 bottom tip
        ], ENEMY_W),
        # frame 1 — lunging
        _fit([
            '  *    [^.^]       ',  # row 0  antenna + head
            ' /|    (o.o) -->   ',  # row 1  eyes + lunge
            '/  |   |-_-| -->   ',  # row 2  face + lunge
            '=--+---\___/ -->   ',  # row 3  wing + body
            '====   ~I~I~  -->  ',  # row 4  wings + body
            '=--+---{I_I}--     ',  # row 5  midsection
            '  \ |  |I_I|       ',  # row 6  body
            '   \|  |_I_|       ',  # row 7  lower body
            '   /   /| |\ -->   ',  # row 8  legs lunging
            '  /   / | | \ -->  ',  # row 9  legs
            ' /   /  | |  \     ',  # row 10 legs lower
            '/    |  |_|   \    ',  # row 11 feet spread
            '     |   |    |\   ',  # row 12 feet
            '     *   |    | *  ',  # row 13 tail
            '         |         ',  # row 14 tail
            '        /|\        ',  # row 15 tail spread
            '       * | *       ',  # row 16 tail tips
            '         *         ',  # row 17 bottom tip
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
