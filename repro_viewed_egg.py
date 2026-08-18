import sys
sys.path.insert(0, r'E:\Next-Private-Server-main\My Singing Monsters Server')
from msm_monsters import viewed_egg
from msm_playerdata import load_player, get_active_island_id

root, player = load_player('Nextstars')
print('active island', get_active_island_id(player))
for island in player.get('islands', []):
    eggs = island.get('eggs') or []
    if eggs:
        print('island', island.get('user_island_id'), 'egg_count', len(eggs))
        for e in eggs[:3]:
            print('  egg', e)
        break
else:
    print('NO EGGS FOUND')
