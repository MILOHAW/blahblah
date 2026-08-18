#!/usr/bin/env python3
"""Test IP-based account creation."""

import json
import sys
from pathlib import Path

# Add the server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from msm_store import get_username_for_ip, _load_ip_mapping, _ip_mapping_path

def test_ip_mapping():
    print("Testing IP-based account creation...")
    
    # Test 1: Create accounts for different IPs
    test_ips = [
        "192.168.1.100",
        "192.168.1.101", 
        "192.168.1.102",
        "10.0.0.1"
    ]
    
    usernames = {}
    for ip in test_ips:
        username = get_username_for_ip(ip)
        usernames[ip] = username
        print(f"✓ IP {ip} -> {username}")
    
    # Test 2: Verify same IP returns same username
    print("\nVerifying IP consistency...")
    for ip, expected_username in usernames.items():
        username = get_username_for_ip(ip)
        if username == expected_username:
            print(f"✓ IP {ip} consistently returns {username}")
        else:
            print(f"✗ IP {ip} returned {username}, expected {expected_username}")
    
    # Test 3: Check the mapping file
    print("\nChecking ip_accounts.json...")
    mapping = _load_ip_mapping()
    print(f"Total mappings: {len(mapping)}")
    for ip, username in mapping.items():
        print(f"  {ip} -> {username}")
    
    print("\n✓ All IP mapping tests completed!")

if __name__ == "__main__":
    test_ip_mapping()
