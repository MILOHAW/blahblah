#!/usr/bin/env python3
"""Add nursery structures to all player islands."""

import sys
sys.path.insert(0, r'.')

from pathlib import Path
import json
import msm_store
import msm_playerdata
import msm_gamedata

# Configure paths
msm_store.players_dir = Path(r'E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players')

def get_nursery_structure_id():
    """Get the structure ID for nursery."""
    return 1  # Basic nursery (structure ID 1)

def add_nurseries_to_player(username):
    """Add a nursery to each island if it doesn't have one."""
    try:
        root, player = msm_playerdata.load_player(username)
        islands = player.get('islands', [])
        
        nurseries_added = 0
        for island in islands:
            structures = island.get('structures', [])
            
            # Check if island already has a nursery
            has_nursery = any(s for s in structures if s and s.get("structure") == 1)
            
            if not has_nursery:
                # Create a new nursery structure
                max_struct_id = 0
                for struct in structures:
                    if struct:
                        sid = struct.get('user_structure_id', 0)
                        if isinstance(sid, (int, float)):
                            max_struct_id = max(max_struct_id, int(sid))
                
                new_nursery = {
                    "user_structure_id": max_struct_id + 1,
                    "structure": 1,  # Nursery ID (structure ID 1)
                    "level": 1,
                    "pos_x": 10,
                    "pos_y": 10,
                    "col": 10,
                    "row": 10,
                    "flip": 0,
                    "building_completed": int(__import__('time').time() * 1000),
                    "occupied": False,
                    "has_egg": False,
                    "viewed": True,
                }
                
                island.get('structures', []).append(new_nursery)
                nurseries_added += 1
        
        if nurseries_added > 0:
            msm_playerdata.save_player(username, root)
            return nurseries_added
        return 0
    except Exception as e:
        print(f"Error for {username}: {e}")
        return 0

# Get all player files
players_dir = msm_store.players_dir
if not players_dir.exists():
    print(f"Players directory not found: {players_dir}")
    sys.exit(1)

player_files = list(players_dir.glob("*.json"))
print(f"Processing {len(player_files)} player files...")

total_added = 0
for player_file in player_files:
    username = player_file.stem
    added = add_nurseries_to_player(username)
    if added > 0:
        print(f"  {username}: added {added} nursery/nurseries")
        total_added += added

print(f"\nCompleted!")
print(f"  Total nurseries added: {total_added}")
