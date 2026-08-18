import json

with open(r'E:\Next-Private-Server-main\Captures\1\msm_json\69_gs_player.json') as f:
    data = json.load(f)
    player_obj = data['payload']['player_object']
    result = {'player_object': player_obj}
    with open(r'E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players\Nextstars.json', 'w') as out:
        json.dump(result, out, indent=2)
    print('Successfully updated Nextstars.json with captured data')
    print('Player now has:')
    print('  coins:', player_obj.get('coins'))
    print('  diamonds:', player_obj.get('diamonds'))
    print('  level:', player_obj.get('level'))
    print('  islands:', len(player_obj.get('islands', [])))
