#!/usr/bin/env python3
"""
Generate Accounts.json entries for all 480 player accounts.
"""

import json
import hashlib
from pathlib import Path

def hash_password(password):
    """Hash password for Accounts.json."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_accounts_file():
    """Create Accounts.json with entries for all 480 players."""
    
    players_dir = Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players")
    accounts_file = Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\Accounts.json")
    
    print(f"Reading player files from {players_dir}...")
    
    # Get all player JSON files
    player_files = sorted(players_dir.glob("*.json"))
    player_files = [f for f in player_files if f.name != "Nextstars.json"]
    
    print(f"Found {len(player_files)} player files")
    
    # Create accounts list
    accounts = []
    
    for i, player_file in enumerate(player_files):
        username = player_file.stem  # filename without .json
        password = "password"  # Default password for all test accounts
        user_id = f"00000{i:06d}"
        
        account = {
            "username": username,
            "email": f"{username}@local.test",
            "password": hash_password(password),
            "user_id": user_id,
            "user_game_id": username,
            "steam_id": f"7656{i:014d}"
        }
        
        accounts.append(account)
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(player_files)} accounts...")
    
    print(f"\nWriting {len(accounts)} accounts to {accounts_file}...")
    
    with open(accounts_file, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)
    
    print(f"Done! Created {len(accounts)} account entries")
    print(f"\nAll accounts use password: 'password'")
    print(f"You can now log in with any username like: {accounts[0]['username']}")

if __name__ == "__main__":
    create_accounts_file()
