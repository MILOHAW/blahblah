import re
from pathlib import Path

# Find all gaps in the monster ID sequence
pattern = r'"monster_id"\s*:\s*(\d+)'

all_ids = set()
db_files = sorted([f for f in Path('Data/db_files').glob('db_monster*.json')])

for db_file in db_files:
    try:
        with open(str(db_file), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        matches = re.findall(pattern, content)
        file_ids = set(int(m) for m in matches)
        all_ids.update(file_ids)
    except Exception as e:
        pass

sorted_ids = sorted(all_ids)

print('🔍 MONSTER ID SEQUENCE ANALYSIS')
print('=' * 60)
print()

# Find gaps
gaps = []
for i in range(len(sorted_ids)-1):
    if sorted_ids[i+1] - sorted_ids[i] > 1:
        gap_range = (sorted_ids[i], sorted_ids[i+1])
        gap_size = sorted_ids[i+1] - sorted_ids[i] - 1
        gaps.append((gap_range, gap_size))

print(f'Total IDs: {len(sorted_ids)}')
print(f'Range: {min(sorted_ids)} - {max(sorted_ids)}')
print(f'Number of gaps: {len(gaps)}')
print()

if gaps:
    print('Gaps in ID sequence:')
    print('-' * 60)
    for gap_range, gap_size in gaps:
        print(f'  IDs {gap_range[0]+1:4d}-{gap_range[1]-1:4d} ({gap_size} missing) | Between {gap_range[0]} and {gap_range[1]}')
print()
print()

# Check specific ID ranges for special handling
print('⭐ SPECIAL MONSTER ID RANGES')
print('=' * 60)
print()

# Check for class-based groupings
class_checks = {}
db_file = Path('Data/db_files/db_monster_9.json')

with open(str(db_file), 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find all classes in the 987-1003 range
for mid in range(980, 1004):
    pattern_id = f'"monster_id": {mid}'
    if pattern_id in content:
        # Extract class
        start_idx = content.find(pattern_id)
        if start_idx != -1:
            # Look for class field nearby
            section = content[max(0, start_idx-200):start_idx+500]
            class_match = re.search(r'"class"\s*:\s*"([^"]+)"', section)
            if class_match:
                class_name = class_match.group(1)
                if class_name not in class_checks:
                    class_checks[class_name] = []
                class_checks[class_name].append(mid)

if class_checks:
    print('Monster classes in ID range 980-1003:')
    print('-' * 60)
    for cls, ids in sorted(class_checks.items()):
        print(f'  {cls}: IDs {min(ids)}-{max(ids)} ({len(ids)} monsters)')
