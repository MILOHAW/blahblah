#!/usr/bin/env python3
"""
Directly unlock all books for all players by modifying JSON files.
"""

import json
from pathlib import Path

def get_all_monster_ids():
    """Get all possible monster IDs from the database."""
    try:
        db_path = Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\db_files\db_monsters.json")
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                monster_ids = []
                for monster in data.get("monster_data", []):
                    mid = monster.get("id")
                    if mid:
                        monster_ids.append(mid)
                return set(monster_ids)
    except Exception as e:
        print(f"Warning: Could not load monster database: {e}")
    return set()

def unlock_all_books_direct():
    """Unlock all monster books for all players by direct JSON manipulation."""
    players_dir = Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players")
    
    player_files = sorted(players_dir.glob("*.json"))
    
    print(f"Processing {len(player_files)} player files...")
    
    all_monster_ids = get_all_monster_ids()
    print(f"Found {len(all_monster_ids)} total monsters in database")
    
    total_unlocked = 0
    successful = 0
    
    for player_file in player_files:
        try:
            with open(player_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            player_object = data.get("player_object", {})
            islands = player_object.get("islands", [])
            
            unlocked_count = 0
            for island in islands:
                if isinstance(island, dict):
                    # Determine which monsters should be unlocked for this island
                    island_type = island.get("island_type") or island.get("type") or 1
                    
                    # For now, unlock all monsters for all islands
                    current_book = set(island.get("book_monster_ids") or [])
                    current_book.update(all_monster_ids)
                    island["book_monster_ids"] = sorted(current_book)
                    
                    # Update counts
                    island["numUniqueCommonsCollectedOnBookOfMonstersIsland"] = max(len([m for m in current_book if m <= 100]), island.get("numUniqueCommonsCollectedOnBookOfMonstersIsland", 0))
                    island["numUniqueRaresCollectedOnBookOfMonstersIsland"] = max(len([m for m in current_book if 100 < m <= 200]), island.get("numUniqueRaresCollectedOnBookOfMonstersIsland", 0))
                    island["numUniqueEpicsCollectedOnBookOfMonstersIsland"] = max(len([m for m in current_book if 200 < m]), island.get("numUniqueEpicsCollectedOnBookOfMonstersIsland", 0))
                    
                    unlocked_count += 1
                    total_unlocked += 1
            
            if unlocked_count > 0:
                with open(player_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                successful += 1
                print(f"  {player_file.name}: unlocked {unlocked_count} island(s)")
        
        except Exception as e:
            print(f"  ERROR processing {player_file.name}: {e}")
    
    print(f"\nCompleted!")
    print(f"  Successfully updated: {successful} players")
    print(f"  Total islands unlocked: {total_unlocked}")

if __name__ == "__main__":
    unlock_all_books_direct()
