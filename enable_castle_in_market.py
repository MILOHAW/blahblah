import json

# Load structures
data = json.load(open('Data/db_files/db_structure.json', encoding='utf-8'))
structs = data.get('structures_data', [])

# Find and update castle (structure 7)
updated = False
for s in structs:
    if s.get('structure_id') == 7:
        if s.get('view_in_market') == 0:
            s['view_in_market'] = 1
            print(f"✓ Updated castle structure_id=7:")
            print(f"  view_in_market: 0 → 1")
            updated = True
        else:
            print(f"Castle already has view_in_market={s.get('view_in_market')}")
        break

if updated:
    # Save back
    with open('Data/db_files/db_structure.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print("\n✓ Saved db_structure.json")
else:
    print("No update needed")
