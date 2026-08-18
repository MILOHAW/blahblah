#!/usr/bin/env python3
"""
Unlock all books (monster collections) for all players on all islands.
"""

import json
from pathlib import Path
from msm_monsters import grant_full_book
from msm_store import load_user_data, save_user_data

def unlock_all_books():
    """Unlock all monster books for all players on all islands."""
    players_dir = Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players")
    
    player_files = sorted(players_dir.glob("*.json"))
    
    print(f"Processing {len(player_files)} player files...")
    
    total_unlocked = 0
    
    for player_file in player_files:
        try:
            username = player_file.stem
            root = load_user_data(username)
            player_object = root.get("player_object", {})
            islands = player_object.get("islands", [])
            
            for island in islands:
                if isinstance(island, dict):
                    # Grant full book to this island
                    grant_full_book(island)
                    total_unlocked += 1
            
            if islands:
                save_user_data(username, root)
                print(f"  {player_file.name}: unlocked {len(islands)} island book(s)")
        
        except Exception as e:
            print(f"  ERROR processing {player_file.name}: {e}")
    
    print(f"\nCompleted!")
    print(f"  Total island books unlocked: {total_unlocked}")

if __name__ == "__main__":
    unlock_all_books()
