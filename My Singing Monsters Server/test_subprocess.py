import sys
import subprocess

# Run in a completely fresh process
code = '''
import sys
sys.path.insert(0, r"d:\\ZewicMsMPc\\ServerData\\My Singing Monsters Server")
import msm_store
import pathlib

p = pathlib.Path(r"d:\\ZewicMsMPc\\ServerData\\My Singing Monsters Server\\SFS2X\\extensions\\MSM\\players")
p.mkdir(parents=True, exist_ok=True)
msm_store.players_dir = str(p)

root = msm_store.load_user_data("TestFresh")
po = root["player_object"]

print("Display name:", po.get("display_name"))
print("Username:", po.get("username"))
print("Total islands:", len(po.get("islands", [])))

import json
with open(r"d:\\ZewicMsMPc\\ServerData\\My Singing Monsters Server\\SFS2X\\extensions\\MSM\\players\\TestFresh.json") as f:
    saved = json.load(f)
    saved_po = saved["player_object"]
    print()
    print("From JSON file:")
    print("  Display name:", saved_po.get("display_name"))
    print("  Username:", saved_po.get("username"))
'''

result = subprocess.run([r"C:\Python314\python.exe", "-c", code], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
