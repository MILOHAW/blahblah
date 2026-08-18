import json

store_data = json.load(open(r'Data\db_files\db_store_v2.json'))

# Find all store_item_data and group them by group_id
groups = {}
for item in store_data.get('store_item_data', []):
    gid = item.get('group_id', 'unknown')
    if gid not in groups:
        groups[gid] = []
    groups[gid].append(item)

print("All groups:")
for gid in sorted(groups.keys(), key=lambda x: (isinstance(x, int), x)):
    items = groups[gid]
    print(f"\nGroup {gid}: {len(items)} items")
    for item in items[:3]:  # Show first 3 items in each group
        print(f"  - {item.get('item_name')} (enabled={item.get('enabled')}, price={item.get('price')} {item.get('currency')})")

# Show the castle specifically
castle_items = [i for i in store_data.get('store_item_data', []) if 'castle' in str(i).lower()]
if castle_items:
    print("\n\nCastle Item Details:")
    import pprint
    pprint.pprint(castle_items[0])
