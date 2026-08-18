import re
import json
from pathlib import Path

# Check Captures directory for monsters
captures = Path('Captures')
captured_monsters = {}

for capture_dir in sorted(captures.iterdir()):
    if not capture_dir.is_dir():
        continue
    
    capture_num = capture_dir.name
    msm_json = capture_dir / 'msm_json'
    
    if not msm_json.exists():
        continue
    
    # Look for db_monster files or player data
    monster_files = sorted(msm_json.glob('*monster*.json'))
    
    # Also check for Nextstars.json
    nextstars = msm_json / 'Nextstars.json'
    
    captured_monsters[capture_num] = {
        'monster_files': [f.name for f in monster_files],
        'has_nextstars': nextstars.exists()
    }

print('📁 Captures Directory Analysis:')
print(f'   Found {len(captured_monsters)} capture directories')
print()

for capture_num in sorted(captured_monsters.keys(), key=lambda x: int(x) if x.isdigit() else 999):
    info = captured_monsters[capture_num]
    if info['monster_files']:
        print(f'   Capture {capture_num}: {len(info["monster_files"])} monster files')
        for mf in info['monster_files'][:3]:
            print(f'      - {mf}')
        if len(info['monster_files']) > 3:
            print(f'      ... and {len(info["monster_files"]) - 3} more')
    elif info['has_nextstars']:
        print(f'   Capture {capture_num}: Has Nextstars.json')
    else:
        print(f'   Capture {capture_num}: (empty)')
