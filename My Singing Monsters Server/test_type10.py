import sys
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import pathlib
import importlib
import msm_store
import msm_handlers

# Force reload to get the updated code
importlib.reload(msm_store)
importlib.reload(msm_handlers)

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
p.mkdir(parents=True, exist_ok=True)
msm_store.players_dir = str(p)

# Test with a fresh player - use ensure_player_save to trigger creation
username = 'Type10Test'
msm_handlers.ensure_player_save(username)

# Now load it
root = msm_store.load_user_data(username)
po = root['player_object']

print('Display name:', po.get('display_name'))
print('Total islands:', len(po.get('islands', [])))
print('Active island ID:', po.get('active_island'))
print()
print('Island details:')
for idx, island in enumerate(po.get('islands', [])):
    print(f"  Island {idx + 1}: type={island.get('type')}, user_island_id={island.get('user_island_id')}, name={island.get('name')}")
