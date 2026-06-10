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
# Enemy sprite builder
# ---------------------------------------------------------------------------

def enemy_char(kind: str, ry: float, frame: int, state: str) -> str | None:
    """Return the ASCII character at relative height *ry* (0=top, 1=bottom).

    Returns None for transparent rows (below the sprite).
    *frame* is 0 or 1 for the walk animation tick.
    *state* is the enemy state string ('patrol', 'chase', 'dead').
    """
    legs = ('\\' if frame else '/') if state == 'chase' else '|'

    if kind == 'demon':
        if   ry < 0.10: return 'W'   # wide horns
        elif ry < 0.22: return 'O'
        elif ry < 0.27: return '}'
        elif ry < 0.65: return 'D'
        elif ry < 0.80: return legs
        else:           return None

    elif kind == 'imp':
        if   ry < 0.08: return '^'   # pointy head
        elif ry < 0.20: return 'O'
        elif ry < 0.25: return '~'
        elif ry < 0.65: return 'I'
        elif ry < 0.80: return legs
        else:           return None

    else:  # zombie (default)
        if   ry < 0.18: return 'O'
        elif ry < 0.22: return '-'
        elif ry < 0.65: return 'Z'
        elif ry < 0.80: return legs
        else:           return None
