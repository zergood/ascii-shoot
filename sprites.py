"""ASCII art data — shading tables, gun frames, enemy body layouts.

No game logic here; import this module in the renderer.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Wall / floor shading palettes
# ---------------------------------------------------------------------------

SHADE_UNI   = ['█', '▓', '▒', '░', '·']
SHADE_ASCII = ['#', '@', '+', ':', '.']

# ---------------------------------------------------------------------------
# Gun sprites — indexed by weapon index (0=Pistol 1=Shotgun 2=Rifle)
# Each entry is three rows of exactly 9 characters, centred at cx-4.
# ---------------------------------------------------------------------------

GUN_SPRITES = [
    # Pistol
    ['   ___   ',
     '  /---\\  ',
     '   |_|   '],
    # Shotgun
    [' ======= ',
     '/=======\\',
     '|=======|'],
    # Rifle
    ['  _____  ',
     ' /-----\\=',
     ' \\_____/ '],
]

# Muzzle-flash animation frames (3 rows of 9 chars, same width as gun)
GUN_FLASH = [
    '  *!*!*  ',
    '   *!*   ',
    '    !    ',
]

# ---------------------------------------------------------------------------
# Enemy sprites — 2-D ASCII art
# ---------------------------------------------------------------------------
# Structure: dict[kind] = [frame_0_rows, frame_1_rows]
# Each frame is a list of equal-length strings (left→right, top→bottom).
# Space = transparent (pixel not drawn).
# Frame 0 is used when patrolling; frames 0/1 alternate when chasing.
#
# You can edit the art here and it immediately shows in-game.
# All rows inside one sprite must have the same length.

ENEMY_SPRITES_2D: dict[str, list[list[str]]] = {

    'zombie': [
        # ── frame 0  (patrol / still) ──
        [' O ',    #  head
         '_Z_',    #  arms out
         ' | ',    #  waist
         '/|\\'],  #  legs  →  /|\
        # ── frame 1  (walking step) ──
        [' O ',
         '_Z_',
         ' | ',
         '/ \\'],  #  legs  →  / \
    ],

    'demon': [
        # ── frame 0 ──
        ['\\V/',   #  wings / horns  →  \V/
         ' O ',    #  head
         '{D}',    #  wide body
         ' | ',    #  waist
         '/|\\'],  #  legs
        # ── frame 1 ──
        ['\\V/',
         ' O ',
         '{D}',
         ' | ',
         '\\ /'],  #  legs step  →  \ /
    ],

    'imp': [
        # ── frame 0 ──
        ['^.^',    #  spiky head / eyes
         ' O ',    #  face
         '~I~',    #  squiggly body
         ' | ',    #  waist
         '/|\\'],  #  legs
        # ── frame 1 ──
        ['^.^',
         ' O ',
         '~I~',
         ' | ',
         '/ \\'],  #  legs step
    ],
}


def enemy_char(kind: str, ry: float, rx: float,
               frame: int, state: str) -> str | None:
    """Return the sprite character at position (ry, rx) ∈ [0, 1]².

    ry  — vertical fraction  (0 = top,  1 = bottom)
    rx  — horizontal fraction (0 = left, 1 = right)
    Returns None for transparent cells (out-of-bounds or space character).
    """
    frames = ENEMY_SPRITES_2D.get(kind, ENEMY_SPRITES_2D['zombie'])
    f      = (frame % 2) if state == 'chase' else 0
    rows   = frames[f]

    row_idx = int(ry * len(rows))
    if row_idx >= len(rows):
        return None                         # below sprite → transparent

    row_str = rows[row_idx]
    col_idx = min(int(rx * len(row_str)), len(row_str) - 1)
    ch      = row_str[col_idx]
    return None if ch == ' ' else ch        # space → transparent
