import sys
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import pathlib
import importlib
import msm_handlers
import msm_store

# Force reload to get the updated code
importlib.reload(msm_handlers)
importlib.reload(msm_store)

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
p.mkdir(parents=True, exist_ok=True)
msm_store.players_dir = str(p)

# Test gs_player handler on a brand new user (no save file)
username = 'FreshPlayer'

# Delete any existing save
import os
player_file = p / f'{username}.json'
if player_file.exists():
    os.remove(player_file)

print(f'Player save exists before gs_player: {player_file.exists()}')

# Call gs_player handler (this should create the save)
try:
    result = msm_handlers.handle_gs_player(username, {})
    print(f'Player save exists after gs_player: {player_file.exists()}')
    print('gs_player handler result keys:', list(result.keys()))
    po = result.get('player_object', {})
    print('Islands:', len(po.get('islands', [])))
    print('Coins:', po.get('coins'))
    print('Premium:', po.get('premium'))
    print('SUCCESS!')
except Exception as e:
    print(f'ERROR: {e}')
