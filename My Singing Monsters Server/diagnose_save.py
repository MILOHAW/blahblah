#!/usr/bin/env python3
"""Find why the client crashes at 97% by comparing a save against a real-server capture.

97% is where the client parses player data. A crash there almost always means a record carries a
field the real server never sends, or a value of the wrong shape. This compares every monster,
structure, egg and island in a save against a genuine capture and reports the differences.

    python diagnose_save.py <save.json> [reference_gs_player_capture.json]

Reference defaults to Captures/15/msm_json/177_gs_player.json (705 monsters, 1111 structures).
Nothing is modified; this only reads.
"""
import json
import sys
from collections import Counter
from pathlib import Path

INT32_MAX = 2147483647


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    # Saves are {"player_object": ...}; captures are {"cmd","len","payload":{"player_object":...}}
    if isinstance(data, dict) and "payload" in data and isinstance(data["payload"], dict):
        data = data["payload"]
    if isinstance(data, dict) and "player_object" in data:
        return data["player_object"]
    return data


def collect(po, kind):
    out = []
    for island in (po.get("islands") or []):
        if isinstance(island, dict):
            out.extend(r for r in (island.get(kind) or []) if isinstance(r, dict))
    return out


def fieldset(records):
    c = Counter()
    for r in records:
        c.update(r.keys())
    return c


def report(kind, mine, ref):
    print("\n=== %s: %d in save, %d in reference ===" % (kind, len(mine), len(ref)))
    if not mine:
        print("    (none in the save - nothing to compare)")
        return []
    mine_f, ref_f = fieldset(mine), fieldset(ref)
    foreign = sorted(f for f in mine_f if f not in ref_f)
    missing = sorted(f for f in ref_f if f not in mine_f and ref_f[f] == len(ref))

    problems = []
    if foreign:
        print("    FIELDS THE REAL SERVER NEVER SENDS (prime suspects):")
        for f in foreign:
            sample = next((r[f] for r in mine if f in r), None)
            print("        %-28s on %-4d records   e.g. %r" % (f, mine_f[f], str(sample)[:60]))
            problems.append("%s.%s" % (kind, f))
    else:
        print("    no foreign fields")

    if missing:
        print("    ALWAYS PRESENT IN REAL DATA BUT MISSING HERE:")
        for f in missing:
            print("        %s" % f)
            problems.append("%s.-%s" % (kind, f))

    # values that will not survive the wire
    big = []
    for r in mine:
        for k, v in r.items():
            if isinstance(v, bool):
                continue
            if isinstance(v, int) and abs(v) > INT32_MAX and k in ref_f:
                refvals = [x.get(k) for x in ref if isinstance(x.get(k), int)]
                if refvals and max(abs(x) for x in refvals) <= INT32_MAX:
                    big.append((k, v))
    if big:
        print("    VALUES TOO LARGE FOR A 32-BIT FIELD:")
        for k, v in Counter(big).most_common(8):
            print("        %-28s %s" % (k[0], k[1]))
            problems.append("%s.%s(too-large)" % (kind, k[0]))

    # Type mismatches. Compare per record, not per field: if most records are fine and only a
    # handful are wrong, comparing whole sets hides the bad ones behind the good ones.
    for f in sorted(set(mine_f) & set(ref_f)):
        rt = {type(r[f]).__name__ for r in ref if f in r and r[f] is not None}
        if not rt:
            continue
        # int/float are interchangeable on the wire; str is not.
        if rt <= {"int", "float"}:
            rt = {"int", "float"}
        bad = Counter(type(r[f]).__name__ for r in mine
                      if f in r and r[f] is not None and type(r[f]).__name__ not in rt)
        if bad:
            for tname, n in bad.most_common(3):
                sample = next((r[f] for r in mine
                               if f in r and type(r[f]).__name__ == tname), None)
                print("    TYPE MISMATCH: %-22s %d records are %s, real data is %s  e.g. %r"
                      % (f, n, tname, sorted(rt), str(sample)[:40]))
            problems.append("%s.%s(type)" % (kind, f))
    return problems


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    save_path = Path(sys.argv[1])
    ref_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        "Captures/15/msm_json/177_gs_player.json")
    if not ref_path.exists():
        print("reference capture not found: %s" % ref_path)
        return 2

    mine, ref = load(save_path), load(ref_path)
    print("save     : %s" % save_path)
    print("reference: %s" % ref_path)
    print("islands  : %d in save, %d in reference" % (
        len(mine.get("islands") or []), len(ref.get("islands") or [])))

    problems = []
    for kind in ("monsters", "structures", "eggs"):
        problems += report(kind, collect(mine, kind), collect(ref, kind))

    # island-level fields matter too: the client reads these before the contents
    isl_mine = [i for i in (mine.get("islands") or []) if isinstance(i, dict)]
    isl_ref = [i for i in (ref.get("islands") or []) if isinstance(i, dict)]
    problems += report("island fields", isl_mine, isl_ref)

    print("\n" + "=" * 60)
    if problems:
        print("SUSPECTS (%d):" % len(problems))
        for p in problems:
            print("   " + p)
        print("\nStrip the foreign fields before sending, or stop writing them.")
    else:
        print("No differences found against the reference.")
        print("If it still crashes, send the server log from the crash instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
