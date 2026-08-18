import sys
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import pathlib
import msm_store
import msm_handlers
import msm_islands

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
p.mkdir(parents=True, exist_ok=True)
msm_store.players_dir = str(p)

# Create a test player
username = 'IslandSwitchTest'
root = msm_store.load_user_data(username)

print('Initial islands:', len(root['player_object'].get('islands', [])))
print('First island user_island_id:', root['player_object']['islands'][0].get('user_island_id'))

# Buy an island
result = msm_islands.buy_island(username, {'island_id': 2})
print('Buy result - success:', result.get('success'))

# Reload the player
root = msm_store.load_user_data(username)
islands = root['player_object'].get('islands', [])
print('After buy - islands:', len(islands))

# Try to switch to the second island
if len(islands) > 1:
    second_island_id = islands[1].get('user_island_id')
    print('Second island user_island_id:', second_island_id, 'type:', type(second_island_id))
    
    # Simulate the change_island command
    change_result = msm_handlers.handle_gs_change_island(username, {'user_island_id': second_island_id})
    print('Change island result - success:', change_result.get('success'))
    print('Change island result - message:', change_result.get('message'))
    
    # Verify active island was updated
    root = msm_store.load_user_data(username)
    print('Active island after switch:', root['player_object'].get('active_island'))
