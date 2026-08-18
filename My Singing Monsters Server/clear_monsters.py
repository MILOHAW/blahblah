import json

with open(r'E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players\Nextstars.json') as f:
    data = json.load(f)

# Remove monsters from all islands
player_obj = data['player_object']
islands = player_obj.get('islands', [])
for island in islands:
    island['monsters'] = []

# Save the updated data
with open(r'E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players\Nextstars.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f'Cleared monsters from {len(islands)} islands')
for i, island in enumerate(islands):
    print(f'  Island {i+1}: {island.get("name")} - monsters: {len(island.get("monsters", []))}')
