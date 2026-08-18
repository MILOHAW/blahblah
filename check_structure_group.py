import json

# Check if there's any documentation in store items about categories/sections
store_data = json.load(open(r'Data\db_files\db_store_v2.json', encoding='utf-8'))
items = store_data.get('store_item_data', [])

# Get all unique group_ids
group_ids = sorted(set(i.get('group_id') for i in items))
print(f"All group IDs in store: {group_ids}")
print(f"Group 7 exists: {7 in group_ids}")

# Check island theme items to understand the structure
theme_items = [i for i in items if i.get('group_id') == 6]
if theme_items:
    print(f"\nIsland Theme item (group 6) sample:")
    print(f"  item_name: {theme_items[0].get('item_name')}")
    print(f"  item_title: {theme_items[0].get('item_title')}")
    print(f"  group_id: {theme_items[0].get('group_id')}")
    print(f"  contents: {theme_items[0].get('contents')}")
    print(f"  All keys: {sorted(theme_items[0].keys())}")
