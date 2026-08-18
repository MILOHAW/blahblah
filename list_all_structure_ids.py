import json

# Load all structure files and collect structure IDs
all_ids = set()
for chunk in range(1, 7):
    if chunk == 1:
        fname = 'db_structure.json'
    else:
        fname = f'db_structure_{chunk}.json'
    
    try:
        data = json.load(open(f'Data/db_files/{fname}'))
        structs = data.get('structures_data', [])
        for s in structs:
            sid = s.get('structure_id')
            if sid:
                all_ids.add(sid)
    except:
        pass

all_ids = sorted(list(all_ids))
print(f"Total unique structure IDs: {len(all_ids)}")
print(f"Range: {min(all_ids) if all_ids else 'none'} to {max(all_ids) if all_ids else 'none'}")
print(f"\nAll structure IDs: {all_ids}")

# Check what structure_ids are > 200 (usually decorative structures)
high_ids = [x for x in all_ids if x > 200]
print(f"\nHigh structure IDs (>200, likely decorative): {high_ids}")
