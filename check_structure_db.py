import json

# Load structure database
structures = json.load(open(r'Data\db_files\db_structure.json'))
struct_data = structures.get('structure_data', [])

# Find structure ID 7
castle_structs = [s for s in struct_data if s.get('structure_id') == 7]
print("Structures with ID 7:")
for s in castle_structs:
    print(f"  Name: {s.get('structure_name')}")
    print(f"  Buildable: {s.get('buildable')}")
    print(f"  Image ID: {s.get('image_id')}")
    print(f"  Price: {s.get('price')}")
    print(f"  Currency: {s.get('currency')}")

# Show all structure IDs 
print(f"\nTotal structures: {len(struct_data)}")
print(f"Structure ID range: {min(s.get('structure_id', 0) for s in struct_data)} to {max(s.get('structure_id', 0) for s in struct_data)}")

# Check if there are duplicates
ids = [s.get('structure_id') for s in struct_data]
dups = [x for x in set(ids) if ids.count(x) > 1]
if dups:
    print(f"Duplicate structure IDs: {dups}")
