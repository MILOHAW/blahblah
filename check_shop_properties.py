import json

store_data = json.load(open(r'Data\db_files\db_store_v2.json', encoding='utf-8'))
items = store_data.get('store_item_data', [])

# Check our castle item
castle_item = next((i for i in items if i.get('item_name') == 'castle.structure'), None)

if castle_item:
    print("Current castle item properties:")
    for key in sorted(castle_item.keys()):
        print(f"  {key}: {castle_item[key]}")

# Find a structure item from the bundles to see what properties they have
print("\n\nSample bundle with structure:")
bundle = next((i for i in items if i.get('contents') and any(c.get('type') == 'STRUCTURE' for c in i.get('contents', []))), None)
if bundle:
    for key in sorted(bundle.keys()):
        print(f"  {key}: {bundle[key]}")
