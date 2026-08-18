import sys, json
sys.path.insert(0, r'E:\Next-Private-Server-main\My Singing Monsters Server')
from msm_playerdata import load_player
import msm_monsters

root, player = load_player('Nextstars')
for island in player.get('islands', []):
    eggs = island.get('eggs') or []
    for egg in eggs:
        if not egg:
            continue
        user_egg_id = egg.get('user_egg_id')
        print('TRYING egg', user_egg_id, 'monster', egg.get('monster'), 'island', island.get('user_island_id'))
        try:
            resp = msm_monsters.viewed_egg('Nextstars', {'user_egg_id': user_egg_id})
            print('OK', resp)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print('FAILED for egg', user_egg_id)
            raise
