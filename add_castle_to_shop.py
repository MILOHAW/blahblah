import json

# Load the store
store_path = r'Data\db_files\db_store_v2.json'
store_data = json.load(open(store_path, encoding='utf-8'))
items = store_data.get('store_item_data', [])

# Find the highest storeitem_id
max_id = max((i.get('storeitem_id', 0) for i in items), default=0)
next_id = max_id + 1

# Create a castle store item
castle_item = {
    "storeitem_id": next_id,
    "item_name": "castle.structure",
    "item_title": "CASTLE_TITLE",
    "item_desc": "CASTLE_DESC",
    "price": 5000000,
    "currency": "coins",
    "currency_id": 1,
    "group_id": 8,  # New group for structures
    "sheet_id": "currency.bin",
    "image_id": "castle_01",
    "consumable": 1,
    "amount": 1,
    "unlock_level": 0,
    "enabled": 1,
    "exclude": 0,
    "max": -1,
    "min_server_version": "0.0",
    "most_popular_priority": 0,
    "best_value_priority": 0,
    "ios_platform_id": "com.bbb.mysingingmonsters.castle.coins",
    "android_platform_id": "",
    "last_changed": 1786647600000,
    "contents": [
        {
            "type": "STRUCTURE",
            "id": 301,
            "debug": "castle_composer"
        }
    ]
}

items.append(castle_item)
store_data['store_item_data'] = items

# Save the updated store
with open(store_path, 'w', encoding='utf-8') as f:
    json.dump(store_data, f, ensure_ascii=False, separators=(',', ': '))

print(f"Added castle to shop!")
print(f"  Item ID: {next_id}")
print(f"  Price: 5,000,000 coins")
print(f"  Structure: CASTLE_COMPOSER (ID 301)")
