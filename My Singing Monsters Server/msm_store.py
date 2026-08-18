import copy
import json
import logging
import os
import threading
import time
from pathlib import Path

from msm_protocol import SFSLong

logger = logging.getLogger(__name__)


db_dir = None
players_dir = None

_db_cache = {}



_UNCACHED_DB_NAMES = {"gs_timed_events"}


def _candidate_db_dirs():
    seen = set()
    candidates = []

    def add(path):
        if path is None:
            return
        resolved = Path(path).resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        candidates.append(resolved)

    workspace_root = Path(__file__).resolve().parent.parent
    add(workspace_root / "Data" / "db_files")
    add(workspace_root / "My Singing Monsters Server" / "db_files")
    add(workspace_root / "My Singing Monsters Server" / "SFS2X" / "extensions" / "MSM" / "db_files")
    add(Path(r"E:\Next-Private-Server-main\Data\db_files"))
    add(Path(r"D:\Next-Private-Server-main\Data\db_files"))
    add(db_dir if db_dir is not None else Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\db_files"))
    add(Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\db_files"))
    add(Path(r"D:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\db_files"))
    add(Path(r"D:\Next-Private-Server-main\My Singing Monsters Server\db_files"))
    add(Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\db_files"))
    return candidates


def _load_json_file(path):
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def _load_json_with_backup_fallback(path):
    candidates = [path]
    alternate_new = path.parent / f"{path.name}.new"
    if alternate_new.exists():
        candidates.append(alternate_new)
    backup_candidates = sorted(path.parent.glob(f"{path.name}.bak_*"))
    for backup in backup_candidates:
        candidates.append(backup)

    for candidate in candidates:
        try:
            return _load_json_file(candidate)
        except Exception:
            continue

    raise FileNotFoundError(f"no valid JSON payload found for {path}")


def load_db_json(name):
    if name in _db_cache:
        return _db_cache[name]

    for directory in _candidate_db_dirs():
        path = directory / f"{name}.json"
        if not path.exists():
            continue
        try:
            data = _load_json_with_backup_fallback(path)
        except Exception:
            if name in _UNCACHED_DB_NAMES:
                return None
            _db_cache[name] = None
            return None
        if name not in _UNCACHED_DB_NAMES:
            _db_cache[name] = data
        return data

    if name in _UNCACHED_DB_NAMES:
        return None
    _db_cache[name] = None
    return None


def _force_runtime_island_types(value, island_type=10):
    if isinstance(value, dict):
        if "island_type" in value and value.get("island_type") != island_type:
            value["island_type"] = island_type
        if "type" in value and value.get("type") != island_type:
            value["type"] = island_type
        for key, item in list(value.items()):
            if isinstance(item, (dict, list)):
                value[key] = _force_runtime_island_types(item, island_type)
        return value
    if isinstance(value, list):
        return [_force_runtime_island_types(item, island_type) for item in value]
    return value


def _force_db_island_catalog(data, island_type=10):
    if not isinstance(data, (dict, list)):
        return data
    if isinstance(data, dict):
        if "islands_data" in data or "island_id" in data or "island_type" in data:
            return _force_runtime_island_types(data, island_type)
        for key, item in list(data.items()):
            if isinstance(item, (dict, list)):
                data[key] = _force_db_island_catalog(item, island_type)
        return data
    return [_force_db_island_catalog(item, island_type) for item in data]


def load_db_json(name):
    name_key = str(name)
    if name_key in _db_cache:
        cached = _db_cache[name_key]
        if name_key.lower() == "db_island_v2" or name_key.lower().startswith("db_island"):
            rewritten = _force_db_island_catalog(cached, 10)
            if rewritten is not cached:
                _db_cache[name_key] = rewritten
            return rewritten
        return cached

    for directory in _candidate_db_dirs():
        path = directory / f"{name}.json"
        if not path.exists():
            continue
        try:
            data = _load_json_with_backup_fallback(path)
        except Exception:
            if name in _UNCACHED_DB_NAMES:
                return None
            _db_cache[name] = None
            return None
        if name not in _UNCACHED_DB_NAMES:
            if name.lower() == "db_island_v2" or name.lower().startswith("db_island"):
                data = _force_db_island_catalog(data, 10)
            _db_cache[name] = data
        return data

    if name in _UNCACHED_DB_NAMES:
        return None
    _db_cache[name] = None
    return None


def normalize_db_payload(command, payload):
    payload = _force_db_island_catalog(payload, 10)
    now_ms = SFSLong(int(time.time() * 1000))
    payload.setdefault("server_time", now_ms)
    payload.setdefault("last_updated", now_ms)
    if command.startswith("gs_"):
        payload.setdefault("success", True)
    return payload


def _candidate_players_dirs():
    seen = set()
    candidates = []

    def add(path):
        if path is None:
            return
        resolved = Path(path).resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        candidates.append(resolved)

    workspace_root = Path(__file__).resolve().parent.parent
    add(workspace_root / "My Singing Monsters Server" / "SFS2X" / "extensions" / "MSM" / "players")
    add(workspace_root / "My Singing Monsters Server" / "players")
    add(players_dir if players_dir is not None else Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players"))
    add(Path(r"E:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players"))
    add(Path(r"D:\Next-Private-Server-main\My Singing Monsters Server\SFS2X\extensions\MSM\players"))
    add(Path(r"E:\Next-Private-Server-main\Captures"))
    add(Path(r"D:\Next-Private-Server-main\My Singing Monsters Server\players"))
    return candidates


def _player_file(username):
    if players_dir is None:
        raise RuntimeError("msm_store.players_dir not configured")
    return Path(players_dir) / f"{username}.json"


def _iter_player_file_candidates(path):
    path = Path(path)
    candidates = [path]
    if path.exists():
        candidates.append(path.with_name(f"{path.name}.new"))
        candidates.extend(sorted(path.parent.glob(f"{path.name}.bak_*")))
    else:
        candidates.append(path.with_name(f"{path.name}.new"))
    seen = set()
    ordered = []
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(candidate)
    return ordered


def _read_player_json(path):
    last_error = None
    for candidate in _iter_player_file_candidates(path):
        if not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8-sig") as fh:
                return json.load(fh)
        except Exception as exc:  # pragma: no cover - defensive; exercised by the recovery tests.
            last_error = exc
    if last_error is not None:
        raise last_error
    raise FileNotFoundError(f"no player data for {path.name!r} in {path.parent}")


def _backup_player_file(path):
    path = Path(path)
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.bak_{int(time.time() * 1000)}")
    try:
        with path.open("rb") as src, backup.open("wb") as dst:
            dst.write(src.read())
        return backup
    except Exception:
        return None


def _template_player_file_candidates():
    candidates = []

    def add(path):
        if path is None:
            return
        candidate = Path(path)
        if candidate not in candidates:
            candidates.append(candidate)

    if players_dir is not None:
        add(Path(players_dir) / "Nextstars.json")
        add(Path(players_dir) / "Nextstars (2).json")
        add(Path(players_dir) / "IslandTestUser.json")

    for directory in _candidate_players_dirs():
        add(directory / "Nextstars.json")
        add(directory / "Nextstars (2).json")
        add(directory / "IslandTestUser.json")

    return candidates


def _create_starter_islands(username, base_island_id=None):
    """Create starter islands: one for each main island type (1-31), all type 10, all unlocked and ready to use."""
    if base_island_id is None:
        base_island_id = int(time.time() * 1000) % 1000000000 + 100000000
    
    islands = []
    now_ms = int(time.time() * 1000)
    
    # Create islands for all main types (1-31, excluding 30)
    main_types = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,]
    
    for idx, island_type in enumerate(main_types):
        user_island_id = base_island_id + idx
        island = {
            "num_torches": 0,
            "type": 10,
            "last_baked": [],
            "tiles": {},
            "baking": [],
            "costumes_owned": "[]",
            "user_island_id": user_island_id,
            "light_torch_flag": False,
            "monsters_sold": "[]",
            "torches": [],
            "likes": 0,
            "eggs": [],
            "island": island_type,
            "date_created": now_ms,
            "warp_speed": {"__double_bits": "0x3ff0000000000000"},
            "structures": [],
            "dislikes": 0,
            "monsters": [],
            "fuzer": [],
            "last_player_level": 1,
            "name": f"Island {island_type}",
            "costume_data": {"costumes": []},
            "user": 0,
            "breeding": [],
            "island_type": 10,
            "book_monster_ids": [],
            "owned_themes": list(range(1, 101)),
            "unlocked_themes": list(range(1, 101)),
            "available_themes": list(range(1, 101)),
            "themes": list(range(1, 101)),
            "island_themes": list(range(1, 101)),
            "owned": True,
            "unlocked": True,
            "locked": False,
            "island_unlocked": True,
            "island_owned": True,
        }
        islands.append(island)
    
    return islands, base_island_id


def _create_default_player_root(username):
    islands, base_island_id = _create_starter_islands(username)
    active_island_id = base_island_id
    
    return {
        "player_object": {
            "display_name": "made by Zewic",
            "username": "New_Player",
            "coins": 99_999_999,
            "diamonds": 99_999_999,
            "food": 99_999_999,
            "ethereal_currency": 99_999_999,
            "keys": 99_999_999,
            "relics": 99_999_999,
            "egg_wildcards": 99_999_999,
            "clubbox_tokens": 99_999_999,
            "starpower": 99_999_999,
            "coins_actual": 99_999_999,
            "diamonds_actual": 99_999_999,
            "food_actual": 99_999_999,
            "ethereal_currency_actual": 99_999_999,
            "keys_actual": 99_999_999,
            "relics_actual": 99_999_999,
            "egg_wildcards_actual": 99_999_999,
            "clubbox_tokens_actual": 99_999_999,
            "starpower_actual": 99_999_999,
            "premium": 99_999_999,
            "has_premium": True,
            "is_premium": True,
            "premium_status": "premium",
            "achievements": [],
            "active_island": active_island_id,
            "islands": islands,
            "user_id": 0,
            "xp": 999999,
            "level": 99,
            "owned_island_themes": list(range(1, 101)),
            "owned_themes": list(range(1, 101)),
            "unlocked_themes": list(range(1, 101)),
            "available_themes": list(range(1, 101)),
            "active_island_themes": [],
            "owned_islands": list(range(1, 101)),
            "unlocked_islands": list(range(1, 101)),
            "all_islands_unlocked": True,
        }
    }


def _ensure_missing_player_save(username):
    path = _player_file(username)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Always generate fresh player saves with 6 unlocked islands
    # Skip old templates to avoid loading legacy saves with 27 islands
    root = _create_default_player_root(username)
    save_user_data(username, root)
    return root


def _normalize_player_account(root):
    if not isinstance(root, dict):
        return root
    player_object = root.get("player_object")
    if not isinstance(player_object, dict):
        return root

    islands = player_object.get("islands")
    # Allow 6, 30, or 27 islands (legacy); reset if invalid
    should_reset_islands = (
        not isinstance(islands, list)
        or len(islands) not in (6, 27, 30)
        or any(not isinstance(island, dict) for island in islands)
    )
    if should_reset_islands:
        default_root = _create_default_player_root(player_object.get("username") or "New_Player")
        player_object["islands"] = default_root["player_object"]["islands"]
        player_object["active_island"] = default_root["player_object"]["active_island"]
        player_object["display_name"] = default_root["player_object"]["display_name"]
        player_object["username"] = default_root["player_object"]["username"]

    player_object["premium"] = 99_999_999
    player_object["has_premium"] = True
    player_object["is_premium"] = True
    player_object["premium_status"] = "premium"

    for key in [
        "coins", "diamonds", "food", "ethereal_currency", "keys", "relics",
        "egg_wildcards", "clubbox_tokens", "starpower", "premium",
        "coins_actual", "diamonds_actual", "food_actual", "ethereal_currency_actual",
        "keys_actual", "relics_actual", "egg_wildcards_actual", "clubbox_tokens_actual",
        "starpower_actual",
    ]:
        player_object[key] = 99_999_999

    try:
        from msm_islands import ALL_THEME_IDS
    except Exception:
        ALL_THEME_IDS = list(range(1, 101))

    theme_ids = list(ALL_THEME_IDS)
    player_object["owned_island_themes"] = theme_ids
    player_object["owned_themes"] = theme_ids
    player_object["unlocked_themes"] = theme_ids
    player_object["available_themes"] = theme_ids
    player_object["owned_islands"] = list(range(1, 101))
    player_object["unlocked_islands"] = list(range(1, 101))
    player_object["all_islands_unlocked"] = True
    player_object.setdefault("active_island_themes", [])
    for island in player_object.get("islands") or []:
        if not isinstance(island, dict):
            continue
        island["owned_themes"] = theme_ids
        island["unlocked_themes"] = theme_ids
        island["available_themes"] = theme_ids
        island["themes"] = theme_ids
        island["island_themes"] = theme_ids
        island["owned"] = True
        island["unlocked"] = True
        island["locked"] = False
        island["island_unlocked"] = True
        island["island_owned"] = True
        if not island.get("name"):
            island["name"] = f"Island {island.get('island') or island.get('type') or 1}"

    try:
        from msm_gamedata import all_monster_ids, monster_ids_allowed_on_island
        from msm_monsters import MAGICAL_NEXUS_ISLAND_TYPE, grant_full_book, island_type_of, repair_book_of_monsters_counts
    except Exception:
        return root

    for island in player_object.get("islands") or []:
        if not isinstance(island, dict):
            continue
        grant_full_book(island)
        island["book_value"] = 3334

    return root


def load_user_data(username):
    for directory in _candidate_players_dirs():
        path = directory / f"{username}.json"
        try:
            data = _read_player_json(path)
            before = json.dumps(copy.deepcopy(data), sort_keys=True, ensure_ascii=False, default=str)
            normalized = _normalize_player_account(data)
            after = json.dumps(copy.deepcopy(normalized), sort_keys=True, ensure_ascii=False, default=str)
            if before != after:
                save_user_data(username, normalized)
            return normalized
        except FileNotFoundError:
            continue
        except Exception:
            continue

    try:
        generated = _normalize_player_account(_ensure_missing_player_save(username))
        save_user_data(username, generated)
        return generated
    except Exception:
        raise FileNotFoundError(f"no player data for {username!r} in any of {[str(d) for d in _candidate_players_dirs()]}") from None


# One lock per save file. With hundreds of accounts on one server, two handlers writing the same
# player at the same time could interleave and leave a truncated, unparseable save.
_save_locks = {}
_save_locks_guard = threading.Lock()


def _save_lock(username):
    with _save_locks_guard:
        lock = _save_locks.get(username)
        if lock is None:
            lock = _save_locks[username] = threading.Lock()
        return lock


def save_user_data(username, root):
    """Write a player save atomically.

    The previous version wrote straight into the live file, so a crash, a full disk, or a second
    write landing mid-way left a half-written save that load_user_data could no longer parse --
    which looks exactly like "my data did not save". Writing to a temp file and renaming makes the
    swap atomic: readers see either the old save or the new one, never a partial one.
    """
    root = _normalize_player_account(root)
    path = _player_file(username)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Save the previous version to a timestamped .bak so the next JSON decode failure can be
    # repaired without losing the most recent working data.
    tmp = path.with_name("%s.%d.%d.tmp" % (path.name, os.getpid(), threading.get_ident()))
    with _save_lock(str(username)):
        try:
            if path.exists():
                _backup_player_file(path)
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(root, fh, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            last = None
            for attempt in range(10):
                try:
                    os.replace(tmp, path)
                    return
                except PermissionError as exc:
                    last = exc
                    time.sleep(0.05 * (attempt + 1))
            raise last
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass


# IP-to-Username mapping management
_ip_mapping_path = Path(__file__).resolve().parent / "ip_accounts.json"
_ip_mapping_lock = threading.Lock()


def _load_ip_mapping():
    """Load the IP-to-username mapping from disk."""
    if not _ip_mapping_path.exists():
        return {}
    try:
        with _ip_mapping_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_ip_mapping(mapping):
    """Save the IP-to-username mapping to disk."""
    try:
        with _ip_mapping_path.open("w", encoding="utf-8") as fh:
            json.dump(mapping, fh, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to save IP mapping: {e}")


def _generate_new_username():
    """Generate a unique new username for a new IP."""
    mapping = _load_ip_mapping()
    counter = 1
    while True:
        username = f"Player_{counter}"
        # Check if this username already exists in the mapping
        if username not in mapping.values():
            # Also check if the player file doesn't exist
            for directory in _candidate_players_dirs():
                if not (directory / f"{username}.json").exists():
                    return username
        counter += 1


def get_username_for_ip(client_ip):
    """Get or create a username for the given client IP."""
    if not client_ip or client_ip == "":
        return "New_Player"  # Fallback for unknown IPs
    
    with _ip_mapping_lock:
        mapping = _load_ip_mapping()
        
        # If this IP already has an account, return it
        if client_ip in mapping:
            return mapping[client_ip]
        
        # Generate a new unique username for this IP
        new_username = _generate_new_username()
        
        # Save the mapping
        mapping[client_ip] = new_username
        _save_ip_mapping(mapping)
        
        logger.info(f"Created new account for IP {client_ip}: {new_username}")
        return new_username
