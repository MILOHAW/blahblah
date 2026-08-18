import json
import glob

# Check what castles look like
data = json.load(open(r'Data\db_files\db_structure.json'))
castles = [s for s in data.get('structures_data', []) if s.get('structure_id') in [1, 2, 138, 186, 203, 206, 301]]
for castle in castles[:3]:
    print(f"ID={castle.get('structure_id')}, name={castle.get('name')}")
    print(f"  cost={castle.get('cost')}, currency={castle.get('currency')}, category={castle.get('category')}")
    print(f"  requires_island={castle.get('requires_island')}")
    print()

# Check what's in the store
store_data = json.load(open(r'Data\db_files\db_store_v2.json'))
store_items = store_data.get('store_item_data', [])
structure_items = [i for i in store_items if 'structure' in str(i).lower()]
print(f"Total structures in store: {len(structure_items)}")
if structure_items:
    print(f"Sample: {structure_items[0]}")
