import pathlib, sys, importlib
sys.path.insert(0, r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server')
import msm_store
importlib.reload(msm_store)

p = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players')
msm_store.players_dir = str(p)
p.mkdir(parents=True, exist_ok=True)

# Test multiple players
for username in ['Player1', 'Player2', 'Player3', 'TestUser']:
    root = msm_store.load_user_data(username)
    po = root['player_object']
    print(username + ': coins=' + str(po.get('coins')) + ', level=' + str(po.get('level')) + ', xp=' + str(po.get('xp')) + ', display_name=' + po.get('display_name'))
    
    # Verify the file was created
    player_file = p / (username + '.json')
    print('  File exists: ' + str(player_file.exists()))
