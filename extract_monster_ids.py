import re
import os
from pathlib import Path

# Extract monster IDs using regex from db_monster files
all_ids = set()
pattern = r'"monster_id"\s*:\s*(\d+)'

db_dir = Path('Data/db_files')
db_files = sorted([f for f in db_dir.glob('db_monster*.json')])
print(f'Scanning {len(db_files)} monster database files...')
print()

for db_file in db_files:
    try:
        with open(str(db_file), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        matches = re.findall(pattern, content)
        file_ids = set(int(m) for m in matches)
        all_ids.update(file_ids)
        
        if file_ids:
            print(f'{db_file.name}: {len(file_ids)} monsters (IDs: {min(file_ids)}-{max(file_ids)})')
        else:
            print(f'{db_file.name}: No monsters found')
    except Exception as e:
        print(f'{db_file.name}: Error - {e}')

print()
print('📊 SUMMARY:')
print(f'   Total unique monster IDs: {len(all_ids)}')
if all_ids:
    sorted_ids = sorted(all_ids)
    print(f'   ID range: {min(all_ids)} - {max(all_ids)}')
    print(f'   First 30 IDs: {sorted_ids[:30]}')
    print(f'   Last 30 IDs: {sorted_ids[-30:]}')
    
    # Check for 987
    if 987 in all_ids:
        print(f'\n✅ Monster ID 987 EXISTS in database')
    else:
        print(f'\n❌ Monster ID 987 NOT found in database')
