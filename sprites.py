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

    # ── 0  Pistol — first-person, held two-handed, barrel into screen ──────
    _fit([
        '',
        '',
        '',
        '                  ___',
        '                 /@@@\\',
        '                 |@@@|',
        '                 |@@@|',
        '                /@@@@@\\',
        '           __  |@@@@@@@|  __',
        '          /##\\_/@@@@@@@\\_/##\\',
        '         |####/#########\\####|',
        '        /####|###########|####\\',
        '        |####|###########|####|',
        '       /#####|###########|#####\\',
        '       |#####|###########|#####|',
    ], GUN_W),

    # ── 1  Shotgun — wide double barrel, pump grip ─────────────────────────
    _fit([
        '',
        '               (@)(@)',
        '               /@@@@\\',
        '              /@@@@@@\\',
        '              |@@@@@@|',
        '             /@@@@@@@@\\',
        '             |@======@|',
        '            /@@@@@@@@@@\\',
        '        __  |@@@@@@@@@@|  __',
        '       /##\\_/@@@@@@@@@@\\_/##\\',
        '      |####/############\\####|',
        '      |###|##############|###|',
        '     /####|##############|####\\',
        '     |####|##############|####|',
        '    /#####|##############|#####\\',
    ], GUN_W),

    # ── 2  Rifle — slim muzzle, vented rail, stock in hands ────────────────
    _fit([
        '                   _',
        '                  (@)',
        '                 /@@@\\',
        '                 |@@@|',
        '                /@@@@@\\',
        '                |@@@@@|',
        '               /@=====@\\',
        '               |@@@@@@@|',
        '          __  /@@@@@@@@@\\  __',
        '         /##\\_|@@@@@@@@@|_/##\\',
        '        |####/###########\\####|',
        '        |###|#############|###|',
        '       /####|#############|####\\',
        '       |####|#############|####|',
        '      /#####|#############|#####\\',
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

    # ── Zombie  (21 wide × 14 rows) ──────────────────────────────────────
    'zombie': [
        # frame 0 — standing
        _fit([
            '    .~~~~~~~~~.    ',  # head top
            '   |(O)     (O)|   ',  # big eyes
            '   | ~~~ ^ ~~~ |   ',  # mouth + nose
            '    \_________/    ',  # chin/jaw
            '   /ZZZZZZZZZZZ\   ',  # upper body
            '  |ZZZZZZZZZZZZZ|  ',  # body
            '  |ZZ[=======]ZZ|  ',  # belt
            '  |ZZZZZZZZZZZZZ|  ',  # lower body
            '   \ZZZZZZZZZZZ/   ',  # hips
            '    |ZZZ| |ZZZ|    ',  # upper legs
            '    |ZZZ| |ZZZ|    ',  # mid legs
            '    |ZZZ| |ZZZ|    ',  # lower legs
            '   /|ZZZ| |ZZZ|\   ',  # feet spread
            ' [ZZZZ]   [ZZZZ]   ',  # flat feet
        ], ENEMY_W),
        # frame 1 — walking (shifted legs)
        _fit([
            '    .~~~~~~~~~.    ',  # head top
            '   |(O)     (O)|   ',  # big eyes
            '   | ~~~ ^ ~~~ |   ',  # mouth + nose
            '    \_________/    ',  # chin/jaw
            '   /ZZZZZZZZZZZ\   ',  # upper body
            '  |ZZZZZZZZZZZZZ|  ',  # body
            '  |ZZ[=======]ZZ|  ',  # belt
            '  |ZZZZZZZZZZZZZ|  ',  # lower body
            '   \ZZZZZZZZZZZ/   ',  # hips
            '    |ZZZ| |ZZZ|    ',  # upper legs
            '   /|ZZZ| |ZZZ|    ',  # stride L forward
            '  / |ZZZ| |ZZZ|\   ',  # stride
            ' /  |ZZZ| |ZZZ| \  ',  # feet spread
            '[ZZZZ]     [ZZZZ]  ',  # flat feet shifted
        ], ENEMY_W),
    ],

    # ── Demon  (21 wide × 15 rows) ───────────────────────────────────────
    'demon': [
        # frame 0 — standing
        _fit([
            '  /\         /\    ',  # horns
            ' /  \_______/  \   ',  # horn base + head
            '| [D]  ###  [D] |  ',  # big [D] eyes
            '| ##/=====\## |    ',  # fanged mouth
            ' \_____________/   ',  # jaw
            '  /{DDDDDDDDD}\    ',  # neck + chest
            ' |{DDDDDDDDDDD}|   ',  # upper body
            '|{DDDDDDDDDDDDD}|  ',  # wide mid body
            ' |{DDDDDDDDDDD}|   ',  # lower body
            '  \{DDDDDDDDD}/    ',  # hips
            '  |{DD}| |{DD}|    ',  # upper legs
            '  |{DD}| |{DD}|    ',  # mid legs
            ' /|{DD}| |{DD}|\   ',  # lower legs
            '/  |___|   |___|   ',  # ankles
            '[__]         [__]  ',  # clawed feet
        ], ENEMY_W),
        # frame 1 — stomping
        _fit([
            '  /\         /\    ',  # horns
            ' /  \_______/  \   ',  # horn base + head
            '| [D]  ###  [D] |  ',  # big [D] eyes
            '| ##/=====\## |    ',  # fanged mouth
            ' \_____________/   ',  # jaw
            '  /{DDDDDDDDD}\    ',  # neck + chest
            ' |{DDDDDDDDDDD}|   ',  # upper body
            '|{DDDDDDDDDDDDD}|  ',  # wide mid body
            ' |{DDDDDDDDDDD}|   ',  # lower body
            '  \{DDDDDDDDD}/    ',  # hips
            '  |{DD}| |{DD}|    ',  # upper legs
            ' /|{DD}| |{DD}|    ',  # stomp L raised
            '/  |{DD}| |{DD}|\  ',  # stomp
            '   |___|   |___|   ',  # ankles
            ' [__]       [__]   ',  # feet shifted
        ], ENEMY_W),
    ],

    # ── Imp  (21 wide × 12 rows) ─────────────────────────────────────────
    'imp': [
        # frame 0 — hovering
        _fit([
            '   *   [^.^]  *    ',  # antenna + head
            '  ===  (o.o) ===   ',  # eyes + wing roots
            ' =====  ^-^  ===== ',  # brow + wings
            '======={I_I}=======',  # full wings + body
            '  ====  |I|  ====  ',  # wing taper + body
            '    |   |I|   |    ',  # body
            '    |   |I|   |    ',  # lower body
            '    |  /| |\  |    ',  # legs spread
            '    | / | | \ |    ',  # legs
            '   /|/  | |  \|\   ',  # lower legs + feet
            '  / |   | |   | \  ',  # feet spread
            ' *  |   |_|   | *  ',  # tail tips
        ], ENEMY_W),
        # frame 1 — lunging
        _fit([
            '     [^.^]  *      ',  # head shifted
            ' === (o.o) ==>     ',  # eyes + lunge arrow
            '==== ^-^   ==>     ',  # wings + lunge
            '===={I_I}  ==>     ',  # body + lunge
            '  == |I|   ==>     ',  # wing taper
            '     |I|           ',  # body
            '     |I|           ',  # lower body
            '    /| |\  ==>     ',  # legs lunging
            '   / | | \ ==>     ',  # legs
            '  /  | |  \ ==>    ',  # lower legs
            ' /   | |   \       ',  # feet
            '*    |_|    *      ',  # tail tips
        ], ENEMY_W),
    ],
}


# Per-row silhouette spans: (kind, frame) -> [(first_col, last_col), ...]
# Used to fill the enemy body solid between its leftmost and rightmost chars.
_SPANS: dict[tuple[str, int], list[tuple[int, int]]] = {}

def _row_spans(rows: list[str]) -> list[tuple[int, int]]:
    spans = []
    for r in rows:
        stripped = r.strip()
        if not stripped:
            spans.append((-1, -1))
        else:
            first = len(r) - len(r.lstrip())
            last  = len(r.rstrip()) - 1
            spans.append((first, last))
    return spans

for _kind, _frames in ENEMY_SPRITES_2D.items():
    for _fnum, _rows in enumerate(_frames):
        _SPANS[(_kind, _fnum)] = _row_spans(_rows)


def enemy_cell(kind: str, ry: float, rx: float,
               frame: int, state: str) -> tuple[str, bool]:
    """Sample the enemy sprite at normalised (ry, rx) ∈ [0,1]².

    Returns (char, inside):
      inside=False → cell is outside the body silhouette (fully transparent)
      inside=True  → cell belongs to the body; char may be ' ' (plain body
                     fill) or a detail character (eyes, belt, claws…).
    """
    key    = kind if kind in ENEMY_SPRITES_2D else 'zombie'
    f      = (frame % 2) if state == 'chase' else 0
    rows   = ENEMY_SPRITES_2D[key][f]

    row_idx = min(int(ry * len(rows)), len(rows) - 1)
    row_str = rows[row_idx]
    col_idx = min(int(rx * len(row_str)), len(row_str) - 1)

    first, last = _SPANS[(key, f)][row_idx]
    if first < 0 or col_idx < first or col_idx > last:
        return ' ', False
    return row_str[col_idx], True


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
