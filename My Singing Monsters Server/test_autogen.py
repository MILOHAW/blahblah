import sys
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import pathlib
import msm_store
import msm_handlers

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
p.mkdir(parents=True, exist_ok=True)
msm_store.players_dir = str(p)

# Simulate a fresh login for a new user
username = 'FreshUser'
print('Before login - file exists:', (p / (username + '.json')).exists())

# Call ensure_player_save (what happens during login)
msm_handlers.ensure_player_save(username)

print('After login - file exists:', (p / (username + '.json')).exists())

# Verify the save
root = msm_store.load_user_data(username)
po = root['player_object']
print('Auto-generated account:', username)
print('  display_name:', po.get('display_name'))
print('  coins:', po.get('coins'))
print('  level:', po.get('level'))
print('  islands:', len(po.get('islands', [])))
