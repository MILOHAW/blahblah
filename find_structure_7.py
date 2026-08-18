import json

# Load all structure files and find structure 7
for chunk in range(1, 7):
    if chunk == 1:
        fname = 'db_structure.json'
    else:
        fname = f'db_structure_{chunk}.json'
    
    try:
        data = json.load(open(f'Data/db_files/{fname}'))
        structs = data.get('structures_data', [])
        for s in structs:
            if s.get('structure_id') == 7:
                print(f"Structure 7 found in {fname}:")
                print(f"  Name: {s.get('name')}")
                print(f"  Description: {s.get('description')}")
                print(f"  Type: {s.get('structure_type')}")
                print(f"  Image: {s.get('image_id')}")
                print(f"  Graphic: {s.get('graphic', {}).get('file')}")
                print(f"  view_in_market: {s.get('view_in_market')}")
                print(f"  Cost: {s.get('cost_coins')} coins")
                print(f"  Level: {s.get('level')}")
                break
    except:
        pass
