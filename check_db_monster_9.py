import json
with open(r'Data/db_files/db_monster_9.json') as f:
    data = json.load(f)
    
# Check structure
print("Keys in db_monster_9.json:", list(data.keys()))
print("Number of entries:", len(data.get("monsters_data", [])) if "monsters_data" in data else "N/A")

# Check if monster 987 is in there
monsters = data.get("monsters_data", [])
for m in monsters:
    if m.get("monster_id") == 987:
        print(f"\nFound monster 987!")
        print(f"  Name: {m.get('name')}")
        print(f"  Class: {m.get('fam')}")
        break
else:
    print("\nMonster 987 NOT found in monsters_data")
    
# Show some IDs that ARE there
ids_in_file = sorted([m.get("monster_id") for m in monsters if m.get("monster_id")])
print(f"\nMonster IDs in db_monster_9.json: {ids_in_file[:20]}")
print(f"...to... {ids_in_file[-20:]}")

if 987 in ids_in_file:
    print("\nWait, 987 IS there!")
