import json
with open(r'My Singing Monsters Server/SFS2X/extensions/MSM/players/Nextstars.json') as f:
    data = json.load(f)
    
player = data.get('player_object', {})
islands = player.get('islands', [])

print('Total islands:', len(islands))
for i, island in enumerate(islands):
    eggs = island.get('eggs', [])
    monsters = island.get('monsters', [])
    print(f'\nIsland {i} (type {island.get("island_type")}, id {island.get("user_island_id")}):')
    print(f'  Eggs: {len(eggs)}')
    for egg in eggs[:5]:
        print(f'    - egg_id={egg.get("user_egg_id")}, monster={egg.get("monster")}')
    print(f'  Monsters: {len(monsters)}')
