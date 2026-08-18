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
username = 'NewFreshPlayer'

# Use load_user_data which calls _ensure_missing_player_save
root = msm_store.load_user_data(username)
po = root['player_object']

print('Display name:', po.get('display_name'))
print('Total islands:', len(po.get('islands', [])))
print('Player premium:', po.get('premium'))
print('Player coins:', po.get('coins'))
print()

print('Island details:')
for idx, island in enumerate(po.get('islands', [])):
    print(f"  Island {idx + 1}:")
    print(f"    user_island_id={island.get('user_island_id')}, type={island.get('type')}")
    print(f"    unlocked_themes count: {len(island.get('unlocked_themes', []))}")
    if len(island.get('unlocked_themes', [])) > 0:
        print(f"    first 5 theme IDs: {island.get('unlocked_themes', [])[:5]}")
