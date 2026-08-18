import json

store_data = json.load(open(r'Data\db_files\db_store_v2.json', encoding='utf-8'))
items = store_data.get('store_item_data', [])

# Find the castle item
castle_item = next((i for i in items if i.get('item_name') == 'castle.structure'), None)

if castle_item:
    # Update to use group 7 (structures section)
    castle_item['group_id'] = 7
    # Ensure enabled is 1
    castle_item['enabled'] = 1
    # Remove contents and add direct structure properties (like island themes)
    castle_item['structure_id'] = 7
    # Keep it as a direct purchase, not a bundle
    del castle_item['contents']
    
    # Save
    with open(r'Data\db_files\db_store_v2.json', 'w', encoding='utf-8') as f:
        json.dump(store_data, f, ensure_ascii=False, separators=(',', ': '))
    
    print("Updated castle item:")
    print(f"  group_id: 7 (structures)")
    print(f"  structure_id: 7 (CASTLE_01)")
    print(f"  enabled: 1")
    print(f"  Removed 'contents' - now direct structure purchase")
