import json
import glob

for filepath in sorted(glob.glob('Data/db_files/db_monster*.json')):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Handle malformed JSON by finding last valid close bracket
            last_close = content.rfind('}]')
            if last_close > 0:
                truncated = content[:last_close+2]
                data = json.loads(truncated)
                items = data.get('monsters_data', [])
                
                for item in items:
                    cls = item.get('class', '')
                    if 'DIPSTER' in cls:
                        monster_id = item.get('monster_id')
                        name = item.get('common_name')
                        market = item.get('view_in_market')
                        print('{}: ID={} {} [{}] market={}'.format(filepath, monster_id, name, cls, market))
    except Exception as e:
        pass
