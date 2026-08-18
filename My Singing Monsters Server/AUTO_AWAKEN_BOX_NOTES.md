# Auto-Awaken Box Monsters Feature

## Overview
When a box monster (Wubbox, Wublin, etc.) hatches, it can now automatically awaken without requiring the player to manually trigger `gs_box_activate_monster`.

## Implementation
Modified `msm_monsters.py` in the `hatch_egg()` function to check for the `AUTO_AWAKEN_BOX` environment variable.

### How It Works
1. When an egg hatches via `gs_hatch_egg`, the game checks if it's a box monster
2. If the `AUTO_AWAKEN_BOX=1` environment variable is set, the box monster automatically enters the awakened state
3. This skips the need for players to manually call `gs_box_activate_monster` after hatching

### Enabling Auto-Awaken
Set the environment variable in your `.env` file or system environment:
```
AUTO_AWAKEN_BOX=1
```

### Related Settings
- `AUTO_WAKE_BOXES=1` - Makes box monsters spawn already awake (legacy behavior)
- `AUTO_AWAKEN_BOX=1` - Automatically awakens box monsters immediately upon hatching
- Amber Island (island_type=22) - Always awakens box monsters immediately regardless of settings

### Behavior Comparison
| Setting | Hatch State | Awaken Automatically |
|---------|------------|---------------------|
| Default | Dormant (stone) | No, requires player action |
| AUTO_AWAKEN_BOX=1 | Awakened | Yes, automatic |
| AUTO_WAKE_BOXES=1 | Awakened | Yes (legacy) |
| Amber Island | Awakened | Yes (always) |

### Files Modified
- `msm_monsters.py` - Updated `hatch_egg()` function to check for `AUTO_AWAKEN_BOX` environment variable
