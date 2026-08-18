#!/usr/bin/env python3
"""
Clear all monsters from all player islands in all save files.
"""

import json
from pathlib import Path

def clear_all_monsters():
    """Remove all monsters from all islands in all player saves."""
    players_dir = Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players")
    
    player_files = sorted(players_dir.glob("*.json"))
    
    print(f"Processing {len(player_files)} player files...")
    
    total_cleared = 0
    
    for player_file in player_files:
        try:
            with open(player_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            player_obj = data.get("player_object", {})
            islands = player_obj.get("islands", [])
            
            cleared_count = 0
            for island in islands:
                if isinstance(island, dict) and "monsters" in island:
                    if len(island.get("monsters", [])) > 0:
                        cleared_count += len(island["monsters"])
                        island["monsters"] = []
            
            if cleared_count > 0:
                with open(player_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                total_cleared += cleared_count
                print(f"  {player_file.name}: cleared {cleared_count} monsters")
        
        except Exception as e:
            print(f"  ERROR processing {player_file.name}: {e}")
    
    print(f"\nCompleted!")
    print(f"  Total monsters cleared: {total_cleared}")

if __name__ == "__main__":
    clear_all_monsters()
