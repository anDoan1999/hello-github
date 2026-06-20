# Super Mario MVP - Python + Pygame

A Mario-style 2D side-scrolling platformer built with Python and Pygame.

## Quick Start

```bash
cd mario_game
uv run python main.py
```

## Controls

| Key | Action |
|---|---|
| `← →` or `A D` | Move left/right |
| `SPACE` | Jump (hold for higher jump) |
| `ESC` | Back to menu / Quit |

## Features

### Core Gameplay
- **Movement**: Left/right with acceleration and friction physics
- **Jumping**: Variable height (hold SPACE longer = jump higher)
- **Collision**: Separate horizontal/vertical collision detection

### Player System
- **Small → Big**: Eat a mushroom to grow (survives one extra hit)
- **Invincibility Stars**: Temporary invincibility with visual flash
- **Lives**: 3 lives, earn extra life every 100 coins
- **Death Animation**: Pop-up and fall off screen

### Enemies
- **Goomba**: Patrols left/right, can be stomped from above
- **Piranha Plant**: Emerges from pipes on a timer, damages on contact

### Items
- **Coins**: Collect 100 for an extra life (+200 points each)
- **Mushroom**: Grow bigger, survive one hit (+1000 points)
- **Star**: Temporary invincibility (+1000 points)

### Level Elements
- **Brick Blocks**: Break when hit from below while big
- **Question Blocks**: Hit from below to release coins/items
- **Pipes**: Solid obstacles, some contain Piranha Plants
- **Gaps**: Fall into them = lose a life
- **Flagpole**: Reach it to complete the level

### Visual Polish
- Animated coin rotation (3D spin effect)
- Player running/jumping animations
- Cloud parallax scrolling background
- Score popups on enemy stomps and item collection
- HUD with coins, lives, score, and countdown timer

## Project Structure

```
mario_game/
├── main.py          # Game loop, camera, HUD, state machine
├── settings.py      # All constants (physics, colors, tile definitions)
├── sprites.py       # All game entities (player, enemies, items, blocks)
├── levels.py        # Level map data and loading logic
└── README.md        # This file
```

## Architecture

- **Settings**: All constants centralized for easy tuning
- **Sprites**: OOP design with per-entity update/draw methods
- **Levels**: Tile-map based, character arrays define layout
- **Camera**: Smooth horizontal follow with boundary clamping
- **State Machine**: menu → playing → level_complete / game_over

## Level Design

The single level (200 tiles wide) features:
- Flat intro area with first Goomba encounter
- Pipe section with Piranha Plants
- Elevated platform section with brick/question blocks
- Gap challenge section
- Final pipe gauntlet before the flagpole

## Physics Tuning

Key parameters in `settings.py`:
- `GRAVITY = 0.6` — how fast you fall
- `PLAYER_JUMP_FORCE = -12` — jump height
- `PLAYER_ACC = 0.5` — acceleration
- `PLAYER_FRICTION = -0.12` — deceleration
- `PLAYER_MAX_SPEED_X = 5` — top speed

## Future Enhancements (Not in MVP)

- Sound effects and music
- Sprite sheet graphics (replace colored rectangles)
- Multiple levels/worlds
- Fire flower power-up
- Underground/secret areas
- Auto-running mode
- Kingdom building system
