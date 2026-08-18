import sys
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import pathlib
import msm_store
import msm_handlers

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
p.mkdir(parents=True, exist_ok=True)
msm_store.players_dir = str(p)

username = 'AllIslandsUnlocked'
root = msm_store.load_user_data(username)
po = root['player_object']

print('Starting active island:', po.get('active_island'))

# Test switching to each island
for idx, island in enumerate(po.get('islands', [])):
    island_id = island.get('user_island_id')
    result = msm_handlers.handle_gs_change_island(username, {'user_island_id': island_id})
    print(f"Switch to Island {idx + 1} (type {island.get('type')}): success={result.get('success')}")
    
    # Verify active island was updated
    root = msm_store.load_user_data(username)
    po = root['player_object']
    print(f"  Active island after switch: {po.get('active_island')}")
