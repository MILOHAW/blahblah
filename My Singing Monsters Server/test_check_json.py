import json
import pathlib

# Check what's actually in the NewFreshPlayer.json file
player_file = pathlib.Path(r'd:\ZewicMsMPc\ServerData\My Singing Monsters Server\SFS2X\extensions\MSM\players\NewFreshPlayer.json')

if player_file.exists():
    with open(player_file, 'r') as f:
        data = json.load(f)
    
    po = data.get('player_object', {})
    print('Display name from JSON:', po.get('display_name'))
    print('Username from JSON:', po.get('username'))
    print('Total islands:', len(po.get('islands', [])))
else:
    print('File does not exist')
