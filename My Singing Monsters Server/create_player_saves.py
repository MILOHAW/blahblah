#!/usr/bin/env python3
"""
Generate 480 player save files with random names for local multiplayer testing.
"""

import json
import random
import string
from pathlib import Path

# Random name generation words
FIRST_NAMES = [
    "Alex", "Bailey", "Casey", "Dakota", "Evan", "Flynn", "Gray", "Hunter",
    "Indigo", "Jordan", "Kass", "Levi", "Morgan", "Noel", "Owen", "Parker",
    "Quinn", "Riley", "Sky", "Taylor", "Utah", "Vale", "Wiley", "Xavier",
    "Yara", "Zane", "Ash", "Blake", "Cade", "Dale", "Eden", "Forest",
    "Gale", "Harbor", "Iris", "Jamie", "Kit", "Lake", "Moss", "Nova",
    "Ocean", "Piper", "Raven", "Sage", "Storm", "Unity", "Vale", "Winter",
    "Xander", "York", "Zen"
]

LAST_NAMES = [
    "Storm", "Wave", "Peak", "Stone", "Stream", "Wind", "Frost", "Blaze",
    "Root", "Vine", "Branch", "Leaf", "Flower", "Star", "Moon", "Sun",
    "Cloud", "Rain", "Snow", "Thunder", "Lightning", "Fire", "Water", "Earth",
    "Sky", "Ocean", "Forest", "Mountain", "Valley", "Desert", "Meadow", "Lake",
    "River", "Creek", "Hill", "Ridge", "Canyon", "Mesa", "Prairie", "Tundra",
    "Plateau", "Slope", "Peak", "Summit", "Base", "Trail", "Path", "Road"
]

def generate_random_name():
    """Generate a random player name."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"{first}{last}{suffix}"

def create_player_saves(count=480):
    """Create count number of player save files with random names."""
    players_dir = Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players")
    template_file = players_dir / "Nextstars.json"
    
    if not template_file.exists():
        print(f"ERROR: Template file not found: {template_file}")
        return False
    
    print(f"Loading template from {template_file}...")
    with open(template_file, "r", encoding="utf-8") as f:
        template = json.load(f)
    
    print(f"Creating {count} player save files in {players_dir}...")
    
    generated_names = set()
    created = 0
    failed = 0
    
    for i in range(count):
        # Generate unique name
        while True:
            name = generate_random_name()
            if name not in generated_names:
                generated_names.add(name)
                break
        
        # Create player file
        player_path = players_dir / f"{name}.json"
        
        try:
            with open(player_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2)
            created += 1
            
            if (i + 1) % 50 == 0:
                print(f"  Created {i + 1}/{count} files...")
        
        except Exception as e:
            print(f"  ERROR creating {name}: {e}")
            failed += 1
    
    print(f"\nCompleted!")
    print(f"  Successfully created: {created}/{count}")
    print(f"  Failed: {failed}/{count}")
    
    return failed == 0

if __name__ == "__main__":
    success = create_player_saves(480)
    exit(0 if success else 1)
