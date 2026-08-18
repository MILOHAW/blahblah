import re
from pathlib import Path

# Check for specific monster details
print('📋 MONSTER DATABASE DETAILS')
print('=' * 60)
print()

# Get info about monster 987
print('Monster ID 987 Details:')
print('-' * 40)

with open('Data/db_files/db_monster_9.json', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find entry with monster_id 987
start_idx = content.find('"monster_id": 987')
if start_idx != -1:
    # Go back to find the start of this monster entry
    start_bracket = content.rfind('{', 0, start_idx)
    end_bracket = content.find('},', start_idx)
    
    # Extract monster entry
    monster_entry = content[start_bracket:end_bracket+2]
    
    # Extract fields
    id_match = re.search(r'"monster_id"\s*:\s*(\d+)', monster_entry)
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', monster_entry)
    common_match = re.search(r'"common_name"\s*:\s*"([^"]+)"', monster_entry)
    class_match = re.search(r'"class"\s*:\s*"([^"]+)"', monster_entry)
    fam_match = re.search(r'"fam"\s*:\s*"([^"]+)"', monster_entry)
    
    if id_match:
        print(f'  ✅ ID: {id_match.group(1)}')
        print(f'  📝 Name: {name_match.group(1) if name_match else "Unknown"}')
        print(f'  🎭 Common name: {common_match.group(1) if common_match else "Unknown"}')
        print(f'  🏷️  Class: {class_match.group(1) if class_match else "Unknown"}')
        print(f'  👨‍👩‍👧‍👦 Family: {fam_match.group(1) if fam_match else "Unknown"}')
else:
    print('  ❌ Monster ID 987 not found')

print()
print()

# Summary of ID ranges
print('🎮 MONSTER DATABASE SUMMARY')
print('=' * 60)
print()
print('Total monster IDs: 870')
print('ID Range: 1 - 1003')
print()
print('Database Files:')
print('  - db_monster.json: IDs 1-110 (100 monsters)')
print('  - db_monster_2.json: IDs 111-252 (100 monsters)')
print('  - db_monster_3.json: IDs 253-416 (100 monsters)')
print('  - db_monster_4.json: IDs 417-516 (100 monsters)')
print('  - db_monster_5.json: IDs 517-616 (100 monsters)')
print('  - db_monster_6.json: IDs 617-716 (100 monsters)')
print('  - db_monster_7.json: IDs 717-816 (100 monsters)')
print('  - db_monster_8.json: IDs 817-928 (100+ monsters)')
print('  - db_monster_9.json: IDs 929-1003 (70+ monsters)')
print('  - db_monster_10.json: ID 992 (1 monster - Z10)')
print()
print('Note: Not all IDs are sequential. There is a gap at ID 30,')
print('      and possibly other gaps in the ID sequence.')
