#!/usr/bin/env python3
"""Remove the incorrect structure 9 nurseries we added and add correct structure 1 nurseries."""

import sys
sys.path.insert(0, r'.')

from pathlib import Path
import msm_store
import msm_playerdata

# Configure paths
msm_store.players_dir = Path(r'E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players')

def cleanup_player(username):
    """Remove wrong nurseries and add correct ones."""
    try:
        root, player = msm_playerdata.load_player(username)
        fixed_islands = 0
        added_nurseries = 0
        
        for island in player.get('islands', []):
            structures = island.get('structures', [])
            
            # Remove structure 9 (castles we added by mistake)
            new_structures = [s for s in structures if s is None or s.get('structure') != 9]
            if len(new_structures) < len(structures):
                fixed_islands += 1
            
            # Check if island now has no nursery (structure 1)
            has_nursery = any(s for s in new_structures if s and s.get('structure') == 1)
            if not has_nursery:
                # Add a new correct nursery
                max_struct_id = 0
                for struct in new_structures:
                    if struct:
                        sid = struct.get('user_structure_id', 0)
                        if isinstance(sid, (int, float)):
                            max_struct_id = max(max_struct_id, int(sid))
                
                new_nursery = {
                    "user_structure_id": max_struct_id + 1,
                    "structure": 1,  # Correct nursery ID
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
                new_structures.append(new_nursery)
                added_nurseries += 1
            
            island['structures'] = new_structures
        
        if fixed_islands > 0 or added_nurseries > 0:
            msm_playerdata.save_player(username, root)
            return (fixed_islands, added_nurseries)
        return (0, 0)
    except Exception as e:
        print(f"Error for {username}: {e}")
        return (0, 0)

# Get all player files
players_dir = msm_store.players_dir
if not players_dir.exists():
    print(f"Players directory not found: {players_dir}")
    sys.exit(1)

player_files = list(players_dir.glob("*.json"))
print(f"Processing {len(player_files)} player files...")

total_fixed = 0
total_added = 0
fixed_players = []

for player_file in player_files:
    username = player_file.stem
    fixed, added = cleanup_player(username)
    if fixed > 0 or added > 0:
        fixed_players.append((username, fixed, added))
        total_fixed += fixed
        total_added += added

print(f"\nCompleted!")
print(f"  Players affected: {len(fixed_players)}")
print(f"  Islands fixed: {total_fixed}")
print(f"  Nurseries added: {total_added}")

if fixed_players:
    print("\nFirst 10 players fixed:")
    for username, fixed, added in fixed_players[:10]:
        print(f"  {username}: fixed {fixed} islands, added {added} nurseries")
