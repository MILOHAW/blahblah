#!/usr/bin/env python3
"""One-shot checker for the NPS server: finds the 97% crash cause and makes the setup safe.

Run it by double-clicking CHECK_AND_FIX.bat. It:

  1. locates the server (the folder holding Config.json)
  2. reports whether the save fix is installed
  3. finds every player save and flags any that are capture frames rather than saves
  4. moves stale session_* snapshot folders aside so nothing can restore from them
  5. compares each save's records against a real capture and reports what does not belong
  6. writes REPORT.txt next to itself

Nothing is deleted. Files are only ever moved, and every move is listed in the report.
"""
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

INT32_MAX = 2147483647
LOG = []


def say(line=""):
    print(line)
    LOG.append(line)


def head(title):
    say()
    say("=" * 68)
    say(title)
    say("=" * 68)


def read_json(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def find_base(start):
    """The server folder is the one containing Config.json."""
    start = Path(start).resolve()
    for d in [start, *start.parents]:
        if (d / "Config.json").exists():
            return d
    for d in [start, *start.parents]:
        if not d.exists():
            continue
        for sub in d.iterdir():
            if sub.is_dir() and (sub / "Config.json").exists():
                return sub.resolve()
    return None


def classify(path):
    """Is this a player save, a raw capture frame, or something else?"""
    try:
        d = read_json(path)
    except Exception as exc:
        return "unreadable", None, str(exc)
    if isinstance(d, dict) and isinstance(d.get("player_object"), dict):
        return "save", d["player_object"], ""
    if isinstance(d, dict) and "payload" in d and "cmd" in d:
        po = d.get("payload", {}).get("player_object")
        return "capture-frame", po if isinstance(po, dict) else None, ""
    return "unknown", None, ""


def counts(po):
    isl = po.get("islands") or []
    m = sum(len(i.get("monsters") or []) for i in isl if isinstance(i, dict))
    s = sum(len(i.get("structures") or []) for i in isl if isinstance(i, dict))
    e = sum(len(i.get("eggs") or []) for i in isl if isinstance(i, dict))
    return len(isl), m, s, e


def best_reference(base):
    """The capture with the most content is the most useful comparison."""
    best = None
    for root in {base, base.parent}:
        for p in root.glob("**/*gs_player*.json"):
            try:
                d = read_json(p)
            except Exception:
                continue
            po = d.get("payload", {}).get("player_object") if isinstance(d, dict) else None
            if not isinstance(po, dict):
                continue
            _, m, s, _ = counts(po)
            if m and (best is None or m > best[0]):
                best = (m, s, p, po)
    return best


def unbits(value):
    """Captures store floats as {"__double_bits": "0x3ff0000000000000"}; that IS a number.

    Comparing raw types without this reported every 'volume' and 'scale' as a type mismatch
    (dict vs float), which was a false alarm.
    """
    if isinstance(value, dict) and len(value) == 1:
        for key in ("__double_bits", "__float_bits"):
            if key in value:
                try:
                    import struct
                    raw = str(value[key])[2:]
                    if key == "__double_bits":
                        return struct.unpack(">d", bytes.fromhex(raw.rjust(16, "0")))[0]
                    return struct.unpack(">f", bytes.fromhex(raw.rjust(8, "0")[-8:]))[0]
                except Exception:
                    return 0.0
    return value


def collect(po, kind):
    out = []
    for island in (po.get("islands") or []):
        if isinstance(island, dict):
            out.extend(r for r in (island.get(kind) or []) if isinstance(r, dict))
    return out


def compare(kind, mine, ref):
    if not mine:
        say("   %-11s none in this save" % kind)
        return []
    mine_f, ref_f = Counter(), Counter()
    for r in mine:
        mine_f.update(r.keys())
    for r in ref:
        ref_f.update(r.keys())

    problems = []
    say("   %-11s %d records" % (kind, len(mine)))

    for f in sorted(f for f in mine_f if f not in ref_f):
        sample = next((r[f] for r in mine if f in r), None)
        say("       FOREIGN FIELD  %-24s on %-4d records  e.g. %r"
            % (f, mine_f[f], str(sample)[:40]))
        problems.append("%s.%s" % (kind, f))

    for r in mine:
        stop = False
        for k, v in list(r.items()):
            if isinstance(v, bool) or not isinstance(v, int):
                continue
            if abs(v) > INT32_MAX and k in ref_f:
                rv = [x.get(k) for x in ref if isinstance(x.get(k), int)]
                if rv and max(abs(x) for x in rv) <= INT32_MAX:
                    say("       TOO LARGE      %-24s = %s" % (k, v))
                    problems.append("%s.%s(too-large)" % (kind, k))
                    stop = True
                    break
        if stop:
            break

    # Fields the real server sends on (nearly) every record but this save lacks. A record missing
    # something the client expects is just as fatal as one carrying junk.
    for f in sorted(ref_f):
        if ref_f[f] < len(ref) * 0.95:
            continue
        missing = sum(1 for r in mine if f not in r)
        if missing:
            say("       MISSING FIELD  %-24s absent on %d of %d records (real data always has it)"
                % (f, missing, len(mine)))
            problems.append("%s.-%s" % (kind, f))

    for f in sorted(set(mine_f) & set(ref_f)):
        rt = {type(unbits(r[f])).__name__ for r in ref if f in r and r[f] is not None}
        if not rt:
            continue
        if rt <= {"int", "float"}:
            rt = {"int", "float"}
        bad = Counter(type(unbits(r[f])).__name__ for r in mine
                      if f in r and r[f] is not None and type(unbits(r[f])).__name__ not in rt)
        for tname, n in bad.most_common(2):
            say("       WRONG TYPE     %-24s %d records are %s, real data is %s"
                % (f, n, tname, sorted(rt)))
            problems.append("%s.%s(type)" % (kind, f))

    if not problems:
        say("       looks fine")

    # With only a handful of records, print them in full: that is usually enough to spot the
    # problem by eye without needing the whole save file.
    if 0 < len(mine) <= 10:
        say("       full contents of these %d record(s):" % len(mine))
        for r in mine[:5]:
            say("         " + json.dumps(r, sort_keys=True)[:900])
        example = next((r for r in ref), None)
        if example is not None:
            say("       for comparison, a real one:")
            say("         " + json.dumps(example, sort_keys=True)[:900])
    return problems


def main():
    here = Path(__file__).resolve().parent
    say("NPS server check - %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    say("running from: %s" % here)

    base = find_base(here)
    if base is None:
        head("COULD NOT FIND THE SERVER")
        say("No Config.json found near this script.")
        say("Put CHECK_AND_FIX.bat inside the server folder (or beside it) and run it again.")
        return 2
    say("server folder: %s" % base)

    # ------------------------------------------------------------ 1. is the fix installed?
    head("1. IS THE SAVE FIX INSTALLED?")
    checks = [
        ("msm_handlers.py", "per-account saving", "def current_username"),
        ("msm_store.py", "atomic save writes", "_save_lock"),
        ("bridge_core.py", "no snapshot restore on disconnect", "save left intact"),
    ]
    installed = 0
    for fname, label, marker in checks:
        try:
            ok = marker in (base / fname).read_text(encoding="utf-8", errors="replace")
        except OSError:
            ok = False
        say("   [%s] %-34s (%s)" % ("OK " if ok else "NO ", label, fname))
        installed += bool(ok)
    if installed < len(checks):
        say()
        say("   -> The fix is NOT fully installed. Copy the three files from the")
        say("      ServerData_SaveFix zip (patched folder) into:")
        say("      %s" % base)

    # ------------------------------------------------------------ 2. player saves
    head("2. PLAYER SAVES")
    players = base / "SFS2X" / "extensions" / "MSM" / "players"
    say("saves folder: %s" % players)
    moved = []
    save_files = []
    if not players.exists():
        say("   MISSING - the server has nowhere to store saves.")
    else:
        for p in sorted(players.glob("*.json")):
            kind, po, err = classify(p)
            size = p.stat().st_size / 1024.0
            if kind == "save" and po is not None:
                i, m, s, e = counts(po)
                say("   [save]  %-24s %7.0f KB  islands=%-3d monsters=%-4d structures=%-4d eggs=%d"
                    % (p.name, size, i, m, s, e))
                save_files.append((p, po))
                continue
            say("   [%s] %-24s %7.0f KB  %s" % (kind, p.name, size, err))
            quarantine = players.parent / "not_saves"
            quarantine.mkdir(exist_ok=True)
            dest = quarantine / p.name
            shutil.move(str(p), str(dest))
            moved.append((p, dest))
            say("       ^ NOT a player save. This is a classic cause of the 97% crash: the")
            say("         server loads it, player_object is missing, and the client dies.")
            say("         MOVED to %s" % dest)

    # ------------------------------------------------------------ 3. session snapshots
    head("3. STALE SESSION SNAPSHOTS")
    found_session = False
    for root in {base, base.parent}:
        for d in sorted(root.glob("session_*")):
            if not d.is_dir():
                continue
            found_session = True
            dest = d.with_name("_disabled_" + d.name)
            if dest.exists():
                say("   already disabled: %s" % dest.name)
                continue
            shutil.move(str(d), str(dest))
            moved.append((d, dest))
            say("   %s" % d)
            say("      Holds a frozen copy of the save. The old code restored from it on every")
            say("      disconnect, throwing away the session. Renamed to %s" % dest.name)
    if not found_session:
        say("   none found - good")

    # ------------------------------------------------------------ 4. compare with real data
    head("4. DOES THE SAVE CONTENT LOOK LIKE REAL SERVER DATA?")
    ref = best_reference(base)
    if ref is None:
        say("   No reference capture found nearby - skipping this check.")
    elif not save_files:
        say("   No readable saves to check.")
    else:
        m, s, refpath, refpo = ref
        say("reference: %s" % refpath.name)
        say("           %d monsters, %d structures - a genuine official-server capture" % (m, s))
        all_problems = []
        for p, po in save_files:
            say()
            say("   --- %s ---" % p.name)
            i, mm, ss, _ = counts(po)
            if mm == 0 and ss == 0:
                say("   %d islands, but nothing on them." % i)
                say("   If he has been playing, progress is not reaching disk - send the server log.")
            for kind in ("monsters", "structures", "eggs"):
                all_problems += compare(kind, collect(po, kind), collect(refpo, kind))
        if all_problems:
            say()
            say("   SUSPECTS: %s" % ", ".join(sorted(set(all_problems))))
            say("   A name with a minus in front means the field is MISSING and should be added;")
            say("   anything else means it should not be sent. Send this report back.")

    # ------------------------------------------------------------ summary
    head("WHAT WAS CHANGED")
    if moved:
        for src, dst in moved:
            say("   moved: %s" % src)
            say("       -> %s" % dst)
        say()
        say("   Nothing was deleted. Move them back to undo.")
    else:
        say("   nothing needed moving")

    head("NEXT STEP")
    say("   Start the server, log in, and see if it still crashes at 97 percent.")
    say("   If it does, send REPORT.txt (next to this script) plus the server log.")
    return 0


if __name__ == "__main__":
    code = 0
    try:
        code = main()
    except Exception:
        import traceback
        say()
        say("the checker itself hit an error:")
        for line in traceback.format_exc().splitlines():
            say("   " + line)
        code = 3
    try:
        out = Path(__file__).resolve().parent / "REPORT.txt"
        out.write_text("\n".join(LOG), encoding="utf-8")
        print("\nreport written to %s" % out)
    except Exception as exc:
        print("could not write REPORT.txt: %s" % exc)
    sys.exit(code)
