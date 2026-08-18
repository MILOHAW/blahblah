import json

store_data = json.load(open(r'Data\db_files\db_store_v2.json', encoding='utf-8'))
items = store_data.get('store_item_data', [])

# Group items by group_id and show what's in each group
groups = {}
for item in items:
    group = item.get('group_id')
    if group not in groups:
        groups[group] = []
    groups[group].append(item.get('item_name'))

print("Store groups:")
for group_id in sorted(groups.keys()):
    print(f"\nGroup {group_id} ({len(groups[group_id])} items):")
    for name in groups[group_id][:3]:  # Show first 3
        print(f"  - {name}")
    if len(groups[group_id]) > 3:
        print(f"  ... and {len(groups[group_id]) - 3} more")

# Check if any items have view_in_market flag
has_view_flag = any('view_in_market' in item for item in items)
print(f"\n\nAny items have 'view_in_market' flag: {has_view_flag}")

# Check first few items for all their properties
print("\n\nFirst 2 items (full properties):")
for item in items[:2]:
    print(f"\n{item.get('item_name')}:")
    for key in sorted(item.keys()):
        val = item[key]
        if isinstance(val, list):
            print(f"  {key}: {len(val)} items")
        else:
            print(f"  {key}: {val}")
