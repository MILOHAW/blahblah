import json
p = r'D:\ZewicMsMPc\Data\db_files\db_monster_9.json.new'
d = json.load(open(p, 'r', encoding='utf-8'))
items = d.get('monsters_data') or []
ids = [x.get('monster_id') for x in items if isinstance(x, dict) and 'monster_id' in x]
print('count', len(items), 'max', max(ids) if ids else -1)
for x in items:
    mid = x.get('monster_id')
    if isinstance(mid, int) and 960 <= mid <= 1040:
        print(mid, x.get('name'), x.get('common_name'), x.get('class'))
