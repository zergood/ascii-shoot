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
# Enemy sprites — static band tables
# ---------------------------------------------------------------------------
# Each entry is (ry_max, char).
# ry_max: the band covers [previous ry_max, ry_max).
# char:   str for a fixed character, tuple (patrol_ch, chase_frame0, chase_frame1)
#         for the animated legs row.
# Rows after the last band are transparent (None).

_LEGS = ('|', '/', '\\')   # (patrol, chase_frame0, chase_frame1)

ENEMY_SPRITES: dict[str, list[tuple]] = {
    'zombie': [
        (0.18, 'O'),   # head
        (0.22, '-'),   # neck
        (0.65, 'Z'),   # body
        (0.80, _LEGS), # legs
    ],
    'demon': [
        (0.10, 'W'),   # horns
        (0.22, 'O'),   # head
        (0.27, '}'),   # chest
        (0.65, 'D'),   # body
        (0.80, _LEGS), # legs
    ],
    'imp': [
        (0.08, '^'),   # spike
        (0.20, 'O'),   # head
        (0.25, '~'),   # neck
        (0.65, 'I'),   # body
        (0.80, _LEGS), # legs
    ],
}


def enemy_char(kind: str, ry: float, frame: int, state: str) -> str | None:
    """Look up the sprite character for *kind* at vertical fraction *ry*.

    *frame* (0 or 1) and *state* only affect the animated legs band.
    Returns None for transparent (below-sprite) rows.
    """
    for ry_max, ch in ENEMY_SPRITES.get(kind, ENEMY_SPRITES['zombie']):
        if ry < ry_max:
            if isinstance(ch, tuple):
                patrol_ch, f0, f1 = ch
                return (f1 if frame else f0) if state == 'chase' else patrol_ch
            return ch
    return None
