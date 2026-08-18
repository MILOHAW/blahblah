import sys
sys.path.insert(0, r'My Singing Monsters Server')
from msm_gamedata import get_monster_definition, all_monster_ids

print("Checking monster definitions...")
print(f"Total monsters loaded: {len(all_monster_ids())}")
print(f"Monster 987 definition exists: {get_monster_definition(987) is not None}")
print(f"Monster 1002 definition exists: {get_monster_definition(1002) is not None}")
print(f"Monster 5 definition exists: {get_monster_definition(5) is not None}")

# Check if monster_id 987 is in the loaded list
all_ids = all_monster_ids()
if 987 in all_ids:
    print("Monster 987 IS in the loaded list")
else:
    print("Monster 987 is NOT in the loaded list")
    
if 1002 in all_ids:
    print("Monster 1002 IS in the loaded list")
else:
    print("Monster 1002 is NOT in the loaded list")

# Show first 20 loaded IDs
print(f"\nFirst 20 monster IDs: {sorted(all_ids)[:20]}")
print(f"Last 20 monster IDs: {sorted(all_ids)[-20:]}")
