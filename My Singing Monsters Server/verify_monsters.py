import json
with open(r'E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players\Nextstars.json') as f:
    data = json.load(f)
player = data['player_object']
islands = player.get('islands', [])
total_monsters = sum(len(island.get('monsters', [])) for island in islands)
print(f"Total islands: {len(islands)}")
print(f"Total monsters across all islands: {total_monsters}")
print("\nFirst 5 islands:")
for i, island in enumerate(islands[:5]):
    print(f"  Island {i+1}: {len(island.get('monsters', []))} monsters")
