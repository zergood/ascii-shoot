# ASCII SHOOT

A Doom-style raycasting FPS in the terminal, built with [tcod](https://python-tcod.readthedocs.io/).

```
   _   ___  ___ ___ ___   ___ _  _ ___   ___ _____
  /_\ / __|/ __|_ _|_ _| / __| || | _ \ / _ \_   _|
 / _ \\__ \ (__ | | | |  \__ \ __ |   /| (_) || |
/_/ \_\___/\___|___|___| |___/_||_|_|_\ \___/ |_|
```

## Requirements

- Python 3.10+
- A desktop environment (tcod opens an SDL window)

## Install

```bash
pip install -r requirements.txt
```

On Linux you may also need the SDL3 system library:

```bash
# Debian / Ubuntu
sudo apt-get install libsdl2-dev

# Fedora
sudo dnf install SDL2-devel
```

## Run

```bash
python game.py
```

## Controls

| Key | Action |
|-----|--------|
| W / ↑ | Move forward |
| S / ↓ | Move back |
| A | Strafe left |
| D | Strafe right |
| ← → | Turn |
| Space / F | Fire |
| E | Use door |
| 1 / 2 / 3 | Switch weapon (Pistol / Shotgun / Rifle) |
| P | Pause |
| Q / Esc | Quit |

## Weapons

| # | Name | Ammo | Notes |
|---|------|------|-------|
| 1 | Pistol | Bullet | Fast, accurate |
| 2 | Shotgun | Shell | 5 pellets, wide spread |
| 3 | Rifle | Bullet | High damage, tight spread |

## Enemies

| Enemy | Behaviour |
|-------|-----------|
| Zombie | Chases and melees |
| Demon | Chases and melees, more HP |
| Imp | Keeps distance, fires projectiles |

## Scoring

- Kill: **150 pts × combo multiplier**
- Combo resets after 3 s of no kills
- Highscores saved to `highscore.txt`

## Tests

```bash
SDL_VIDEODRIVER=offscreen python -m unittest test_game -v
```
