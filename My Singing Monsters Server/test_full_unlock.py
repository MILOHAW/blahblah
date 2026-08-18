import sys
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import pathlib
import importlib
import msm_store

# Force reload
importlib.reload(msm_store)

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
p.mkdir(parents=True, exist_ok=True)
msm_store.players_dir = str(p)

# Test creating a new player
username = 'FullUnlockedTest'

# Use _ensure_missing_player_save which calls _create_default_player_root
root = msm_store._ensure_missing_player_save(username)
po = root['player_object']

print('Display name:', po.get('display_name'))
print('Total islands:', len(po.get('islands', [])))
print('Player unlocked_themes count:', len(po.get('unlocked_themes', [])))
print('Player available_themes count:', len(po.get('available_themes', [])))
print()

print('Island details with unlocks:')
for idx, island in enumerate(po.get('islands', [])):
    print(f"  Island {idx + 1}:")
    print(f"    type={island.get('type')}, user_island_id={island.get('user_island_id')}")
    print(f"    unlocked_themes={len(island.get('unlocked_themes', []))} items")
    print(f"    available_themes={len(island.get('available_themes', []))} items")
    print(f"    owned_themes={len(island.get('owned_themes', []))} items")
