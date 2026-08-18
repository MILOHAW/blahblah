import sys
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import pathlib
import importlib

import msm_handlers
import msm_store

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
msm_store.players_dir = str(p)
p.mkdir(parents=True, exist_ok=True)

# Create a test player
root = msm_store.load_user_data('TestDisplayName')
print('Initial display_name:', root['player_object'].get('display_name'))

# Call the handler
handler = msm_handlers.GAMEPLAY_HANDLERS['gs_set_displayname']
result = handler('TestDisplayName', {'displayname': 'NewDisplayName'})
print('Handler result:', result)

# Verify the change was saved
root = msm_store.load_user_data('TestDisplayName')
print('Saved display_name:', root['player_object'].get('display_name'))
