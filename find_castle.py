import json
import glob
files = glob.glob(r'Data\db_files\db_structure*.json')
for f in sorted(files):
    data = json.load(open(f))
    for s in data.get('structures_data', []):
        if 'castle' in str(s).lower():
            print(f"{f}: ID={s.get('structure_id')}, name={s.get('name')}, structure_name={s.get('structure_name')}")
