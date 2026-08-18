import json
path = r'E:\Next-Private-Server-main\Captures\1\msm_json\69_gs_player.json'
with open(path) as f:
    data = json.load(f)
player = data.get('player_object', {})
islands = player.get('islands', [])
print(f"Player username: {player.get('username')}")
print(f"Player level: {player.get('level')}")
print(f"Number of islands: {len(islands)}")
if islands:
    total_monsters = sum(len(island.get('monsters', [])) for island in islands)
    print(f"Total monsters across islands: {total_monsters}")
