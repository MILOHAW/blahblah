#!/usr/bin/env python3
import json

# Check live database
try:
    with open('db_monster.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_monsters = data.get('monsters_data', [])
    print(f"Total monsters in db_monster.json: {len(all_monsters)}")
    
    # Look for any Q* pattern
    q_monsters = [m for m in all_monsters if any('Q' in str(n) for n in m.get('names', []))]
    print(f"\nMonsters with 'Q' in their names: {len(q_monsters)}")
    
    for m in q_monsters[:10]:
        print(f"  ID {m.get('monster_id')}: {m.get('common_name')} - view_in_market: {m.get('view_in_market')} - names: {m.get('names')}")
    
    if not q_monsters:
        print("\nNo Q-series monsters found. Showing first few monsters:")
        for m in all_monsters[:5]:
            print(f"  ID {m.get('monster_id')}: {m.get('common_name')} - names: {m.get('names')}")

except Exception as e:
    print(f"Error: {e}")
