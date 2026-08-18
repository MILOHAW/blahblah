with open(r'My Singing Monsters Server\msm_monsters.py') as f:
    lines = f.readlines()
    for i, line in enumerate(lines, 1):
        if '_mark_monster_viewed_in_sold' in line or '_mark_monster_sold' in line or '_mark_monster_reacquired' in line:
            if 'def ' in line:
                print(f"Line {i}: {line.strip()}")
