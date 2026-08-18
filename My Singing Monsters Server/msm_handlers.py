import json
import logging
import os
import time
from pathlib import Path

import msm_box
import msm_cardalbum
import msm_islands
import msm_monsters
import msm_rewards
import msm_rewardtracks
import msm_structures
import msm_synthesis
from msm_playerdata import (
    add_actual_currencies,
    coerce_wire_types,
    create_player_properties,
    find_monster_with_island,
    load_player,
)
from msm_protocol import SFSLong
from msm_store import load_db_json, load_user_data, normalize_db_payload, save_user_data
logger = logging.getLogger("msm.handlers")
DEFAULT_USERNAME = "New_Player"
LEGACY_DEFAULT_USERNAMES = {"Nextstars", "Next Private Server", "Default"}

# The save copied for a first-time login. Kept separate from DEFAULT_USERNAME so the template can
# be swapped for a clean starter save without changing who the fallback account is.
NEW_PLAYER_TEMPLATE = os.environ.get("MSM_NEW_PLAYER_TEMPLATE", DEFAULT_USERNAME)


def current_username(session):
    """The account this connection is logged in as, or the default before USER_LOGIN arrives."""
    if isinstance(session, dict):
        name = session.get("username")
        if name:
            return str(name)
    return DEFAULT_USERNAME


def _session_capture_dir():
    # Check environment variable first
    env_path = os.environ.get("MSM_SESSION_DIR")
    if env_path:
        env_candidate = Path(env_path)
        if env_candidate.exists():
            return env_candidate
    
    # Auto-detect session_* directories in script location and parent
    script_dir = Path(__file__).parent.absolute()
    search_dirs = [script_dir, script_dir.parent]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        # Find all session_* directories, return the most recent one
        session_dirs = sorted(
            [d for d in search_dir.iterdir() if d.is_dir() and d.name.startswith("session_")],
            key=lambda p: p.name,
            reverse=True
        )
        if session_dirs:
            return session_dirs[0]
    
    return None


def _load_captured_session_frames():
    session_dir = _session_capture_dir()
    if session_dir is None:
        return []
    responses_dir = session_dir / "responses"
    if not responses_dir.exists():
        return []

    frames = []
    for path in sorted(responses_dir.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        command = data.get("cmd")
        payload = data.get("payload")
        if not command or command in {"CID", "USER_LOGIN", "alive"}:
            continue
        if not isinstance(payload, dict):
            continue
        frames.append((str(command), dict(payload)))
    return frames


def _load_captured_session_command(command):
    for captured_cmd, payload in _load_captured_session_frames():
        if captured_cmd == command:
            return payload
    return None
def _normalize_island_id(value):
    """Extract integer value from SFSLong or other types."""
    if value is None:
        return None
    # Try as SFSLong first (has .value attribute)
    if hasattr(value, 'value'):
        try:
            return int(value.value)
        except (ValueError, TypeError, AttributeError):
            pass
    # Try direct int conversion
    try:
        return int(value)
    except (ValueError, TypeError):
        pass
    return value


def _find_island(islands, user_island_id):
    target_id = _normalize_island_id(user_island_id)
    if target_id is None:
        return None
    
    for island in islands:
        if not isinstance(island, dict):
            continue
        island_id = _normalize_island_id(island.get("user_island_id"))
        if island_id == target_id:
            return island
    return None


def _remove_all_trees(player_obj):
    """Remove all monsters, eggs, trees, and structures from all islands and set island type to 10."""
    islands = player_obj.get("islands", []) or []
    cleared_islands = 0
    for island in islands:
        if not isinstance(island, dict):
            continue
        island["structures"] = []
        island["monsters"] = []
        island["eggs"] = []
        for key in ("trees", "rocks", "decorations", "obstacles"):
            if key in island:
                island[key] = []
        island["island_type"] = 10
        island["type"] = 10
        island["num_monsters"] = 0
        cleared_islands += 1
    logger.info("Removed all monsters, eggs, structures, and trees from %d islands and set island_type=10", cleared_islands)
    return cleared_islands


def _rewrite_session_snapshot(username, root):
    session_dir = _session_capture_dir()
    if session_dir is None:
        return None
    snapshot_path = session_dir / "Nextstars.json"
    if not snapshot_path.parent.exists():
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with snapshot_path.open("w", encoding="utf-8") as fh:
        json.dump(root, fh, indent=2, ensure_ascii=False)
    logger.info("Wrote empty logout snapshot for %s to %s", username, snapshot_path)
    return snapshot_path


def _session_nextstars_snapshot_path():
    session_dir = _session_capture_dir()
    if session_dir is not None:
        snapshot_path = session_dir / "Nextstars.json"
        if snapshot_path.exists():
            return snapshot_path
    return None


def handle_gs_change_island(username, params):
    user_island_id = params.get("user_island_id")
    if user_island_id is None:
        return None
    
    root = load_user_data(username)
    player_object = root.get("player_object")
    
    # Set active island regardless of whether it's found
    if player_object is not None:
        target_id = _normalize_island_id(user_island_id)
        player_object["active_island"] = target_id if isinstance(target_id, int) else user_island_id
        save_user_data(username, root)
    
    result = {
        "success": True, 
        "user_island_id": SFSLong(user_island_id) if isinstance(user_island_id, int) else user_island_id,
    }
    return result
def handle_gs_player(username, params):
    # Ensure the player has a save file, creating one if needed
    ensure_player_save(username)
    
    root, player_object = load_player(username)
    player_object["premium"] = 99_999_999
    player_object["has_premium"] = True
    player_object["is_premium"] = True
    for island in player_object.get("islands") or []:
        msm_monsters.grant_full_book(island)
        msm_monsters.backfill_titansoul_state(island)
        msm_structures.backfill_awakener_structures(island)
        msm_islands.backfill_island_type(island)
        msm_box.repair_broken_box_eggs(island)
        msm_synthesis.repair_glitched_synthesis(island)
    msm_islands.migrate_legacy_mirror_ids(player_object)
    save_user_data(username, root)
    return {"player_object": coerce_wire_types(player_object)}

def handle_gs_set_displayname(username, params):
    new_displayname = params.get("displayname") or params.get("display_name") or ""
    if not new_displayname or len(new_displayname.strip()) == 0:
        return {"success": False, "message": "Invalid display name"}
    
    root = load_user_data(username)
    player_object = root.get("player_object")
    if player_object is not None:
        player_object["display_name"] = str(new_displayname)[:32]
        save_user_data(username, root)
    return {"success": True, "display_name": player_object.get("display_name") if player_object else new_displayname}

def _simple(fn):
    def handler(username, params):
        return fn(username, params)
    return handler
def _with_structure_update(command, fn, always=False):
    def handler(username, params):
        result, update = fn(username, params)
        frames = [(command, result)]
        if update or always:
            frames.append(("gs_update_structure", update))
        return frames
    return handler
def _discard_structure_update(fn):
    def handler(username, params):
        result, _update = fn(username, params)
        return result
    return handler
def _with_monster_update(command, fn):
    def handler(username, params):
        result, update = fn(username, params)
        frames = [(command, result)]
        if update:
            frames.append(("gs_update_monster", update))
        return frames
    return handler
def _with_monster_update_first(command, fn):
    def handler(username, params):
        result, update = fn(username, params)
        frames = []
        if update:
            frames.append(("gs_update_monster", update))
        frames.append((command, result))
        return frames
    return handler
def _mega_monster_handler(username, params):
    logger.info("gs_mega_monster_message params: %r", params)
    result, update = msm_monsters.biggify_monster(username, params)
    logger.info("gs_mega_monster_message result: %r update: %r", result, update)
    frames = []
    if update:
        frames.append(("gs_update_monster", update))
    frames.append(("gs_mega_monster_message", result))
    return frames
def _generic_success(extra_array_keys=()):
    def handler(username, params):
        result = {"success": True}
        for key in extra_array_keys:
            result[key] = []
        return result
    return handler
def _finish_breeding(force_complete):
    def handler(username, params):
        return msm_monsters.finish_breeding(username, params, force_complete)
    return handler
def _teleport_monster(send_home):
    def handler(username, params):
        root, player_object = load_player(username)
        source_island_id = params.get("user_island_id") or player_object.get("active_island", 0) or 0
        source_island = _find_island(player_object.get("islands") or [], source_island_id)
        happy_effects = []
        if source_island is not None:
            for monster in source_island.get("monsters") or []:
                if monster is not None and monster.get("user_monster_id"):
                    happy_effects.append({
                        "user_monster_id": SFSLong(monster.get("user_monster_id", 0)),
                        "happiness": monster.get("happiness", 0) or 0,
                    })
        result = msm_monsters.move_battle_monster(username, params, send_home)
        if not result.get("success"):
            return result
        return [
            ("gs_send_monster_home" if send_home else "battle_teleport", result),
            ("gs_multi_update_monster", {"success": True, "monster_happy_effects": happy_effects}),
        ]
    return handler
def _send_to_magical_nexus_handler(username, params):
    logger.info("gs_send_to_magical_nexus params: %r", params)
    monster_id = (params.get("user_monster_id") or params.get("monster_id")
                  or params.get("source_user_monster_id") or params.get("id") or 0)
    root, player_object = load_player(username)
    source_island, monster = None, None
    for island in player_object.get("islands") or []:
        if island is None:
            continue
        for candidate in island.get("monsters") or []:
            if candidate is not None and candidate.get("user_monster_id") == monster_id:
                source_island, monster = island, candidate
                break
        if monster is not None:
            break
    result, nursery = msm_monsters.send_to_magical_nexus(username, params)
    if not result.get("success"):
        return result
    update_entry = {"user_monster_id": SFSLong(monster_id), "happiness": 0, "last_collection": SFSLong(int(time.time() * 1000))}
    if monster is not None:
        update_entry["happiness"] = monster.get("happiness", 0) or 0
    return [
        ("gs_send_to_magical_nexus", result),
        ("gs_multi_update_monster", {
            "success": True, "user_monster_id": SFSLong(monster_id),
            "update_monster_list": [update_entry],
        }),
    ]
def _buy_egg_handler(username, params):
    logger.info("gs_buy_egg params: %r", params)
    quantity = params.get("quantity") or 100  # Default to 100 if not specified
    quantity = min(max(1, int(quantity)), 999)  # Clamp to 1-999
    
    if quantity == 1:
        return msm_monsters.buy_egg(username, params)[0]
    
    # Bulk purchase
    results = []
    eggs_purchased = 0
    for i in range(quantity):
        result, update = msm_monsters.buy_egg(username, params)
        if not result.get("success"):
            logger.info("_buy_egg_handler: stopped at purchase %d/%d", i, quantity)
            break
        eggs_purchased += 1
        results.append(result)
    
    if eggs_purchased == 0:
        return results[0] if results else {"success": False, "error": "failed_to_purchase"}
    
    # Merge results
    if eggs_purchased == 1:
        return results[0]
    
    # For multiple purchases, return aggregated result
    final_result = {
        "success": True,
        "eggs_purchased": eggs_purchased,
        "properties": results[-1].get("properties", {}),
        "eggs": [r.get("user_egg") for r in results if r.get("user_egg")],
    }
    logger.info("_buy_egg_handler: successfully purchased %d eggs", eggs_purchased)
    return final_result
def _costume_action(command):
    def handler(username, params):
        return msm_monsters.costume_action(username, params, command)
    return handler
def _collect_monster(command):
    def handler(username, params):
        outcome = msm_monsters.collect_monster(username, params)
        if isinstance(outcome, tuple):
            result, update_bundle = outcome
            frames = [(command, result)]
            for update in update_bundle.get("monster_updates", []):
                frames.append(("gs_update_monster", update))
            return frames
        return outcome
    return handler
def _hatch_egg_handler(username, params):
    import os
    try:
        result, monster_update = msm_monsters.hatch_egg(username, params)
    except Exception as e:
        # Log the actual exception instead of silently catching it
        logger.exception("hatch_egg failed with exception: %s", type(e).__name__)
        # Return a proper error instead of fake success
        result = {"success": False, "error": str(e), "user_egg_id": params.get("user_egg_id")}
        monster_update = None
    
    frames = [("gs_hatch_egg", result)]
    if monster_update:
        frames.append(("gs_update_monster", monster_update))
    
    # Auto-awaken box monsters after hatching (can be disabled with AUTO_AWAKEN_BOX=0)
    auto_awaken = os.environ.get("AUTO_AWAKEN_BOX", "1") != "0"
    logger.info("_hatch_egg_handler: AUTO_AWAKEN_BOX=%s, result.success=%s", auto_awaken, result.get("success"))
    
    if auto_awaken and result.get("success"):
        monster_data = result.get("monster", {})
        logger.info("_hatch_egg_handler: monster_data type=%s, keys=%s", type(monster_data), list(monster_data.keys()) if isinstance(monster_data, dict) else "N/A")

        if isinstance(monster_data, dict):
            from msm_box import is_box_monster_entity
            from msm_gamedata import get_monster_definition
            monster_id = monster_data.get("monster", 0)
            logger.info("_hatch_egg_handler: monster_id=%s, checking if box monster", monster_id)

            definition = get_monster_definition(monster_id)
            logger.info("_hatch_egg_handler: definition found=%s", definition is not None)

            is_box = is_box_monster_entity(definition)
            logger.info("_hatch_egg_handler: is_box_monster_entity=%s", is_box)

            if is_box:
                # Automatically activate the box monster and force the client to refresh the
                # monster state via the standard gs_update_monster frame.
                user_monster_id = monster_data.get("user_monster_id", 0)
                if hasattr(user_monster_id, 'value'):
                    user_monster_id = user_monster_id.value
                user_monster_id = int(user_monster_id) if user_monster_id else 0

                logger.info("_hatch_egg_handler: auto-awakening box monster %d, user_monster_id=%d", monster_id, user_monster_id)
                if user_monster_id:
                    activate_result, activate_update = msm_box.box_activate_monster(username, {"user_monster_id": user_monster_id})
                    logger.info("_hatch_egg_handler: activation result=%s", activate_result.get("success"))
                    if activate_result.get("success") and activate_update:
                        frames.append(("gs_update_monster", activate_update))
                        
                        # Mute then unmute to trigger animation
                        mute_result, mute_update = msm_monsters.mute_monster(username, {"user_monster_id": user_monster_id, "muted": 1})
                        if mute_result.get("success") and mute_update:
                            frames.append(("gs_update_monster", mute_update))
                        
                        unmute_result, unmute_update = msm_monsters.mute_monster(username, {"user_monster_id": user_monster_id, "muted": 0})
                        if unmute_result.get("success") and unmute_update:
                            frames.append(("gs_update_monster", unmute_update))

    return frames
def _viewed_egg_handler(username, params):
    result, sold_update = msm_monsters.viewed_egg(username, params)
    frames = []
    if sold_update:
        frames.append(("gs_update_sold_monsters", sold_update))
    frames.append(("gs_viewed_egg", result))
    return frames
def _sell_monster_handler(username, params):
    result, sold_update = msm_monsters.sell_monster(username, params)
    frames = []
    if sold_update:
        frames.append(("gs_update_sold_monsters", sold_update))
    frames.append(("gs_sell_monster", result))
    return frames
def _facebook_help_instances_stub(username, params):
    return {"success": True, "egg_results": [], "breeding_results": [], "count": 0}
def _battle_claim_versus_rewards(username, params):
    root = load_user_data(username)
    player_object = root.get("player_object") or {}
    tier = params.get("tier", 1) or 1
    campaign_id = params.get("campaign_id", 1000) or 1000
    reward = {"coins": 500 * tier, "food": 200 * tier}
    for key, amount in reward.items():
        player_object[key] = (player_object.get(key, 0) or 0) + amount
        player_object[f"{key}_actual"] = player_object[key]
    save_user_data(username, root)
    result = {
        "success": True, "tier": tier, "campaign_id": campaign_id,
        "claimed_on": SFSLong(int(time.time() * 1000)),
        "season_rewards": reward,
        "properties": create_player_properties(player_object),
    }
    add_actual_currencies(result, player_object)
    return result
def _battle_set_music(username, params):
    return {"success": True, "currently_playing": params.get("track", params.get("currently_playing", 0)) or 0, "muted": bool(params.get("muted", False))}
def _client_keep_alive(username, params):
    return {}
def _metric_event(username, params):
    return {"event": params.get("event", "")}
def _collect_rewards_stub(username, params):
    return {"success": False, "notificationOnFail": False}
_STATIC_ALIAS_RESPONSES = {
    "gs_daily_login_reward_seen": "gs_update_island_tutorials",
    "gs_news_seen": "gs_update_island_tutorials",
    "gs_generic_success": "gs_update_island_tutorials",
    "gs_update_island_tutorials": "gs_update_island_tutorials",
}
GAMEPLAY_HANDLERS = {
    "gs_change_island": handle_gs_change_island,
    "gs_player": handle_gs_player,
    "gs_set_displayname": handle_gs_set_displayname,
    "gs_buy_island": _simple(msm_islands.buy_island),
    "update_island_mode": _simple(msm_islands.update_island_mode),
    "gs_save_island_warp_speed": _simple(msm_islands.set_warp_island),
    "gs_mute_island": _simple(msm_islands.mute_island),
    "gs_buy_structure": _simple(msm_structures.buy_structure),
    "gs_move_structure": _with_structure_update("gs_move_structure", msm_structures.move_structure, always=True),
    "move_structure": _with_structure_update("move_structure", msm_structures.move_structure, always=True),
    "gs_update_structure_position": _with_structure_update("gs_update_structure_position", msm_structures.move_structure, always=True),
    "gs_sell_structure": _simple(msm_structures.sell_structure),
    "gs_remove_obstacle": _simple(msm_structures.sell_structure),
    "gs_clear_obstacle": _simple(msm_structures.sell_structure),
    "gs_buy_remove_obstacle": _simple(msm_structures.sell_structure),
    "gs_remove_island_obstacle": _simple(msm_structures.sell_structure),
    "gs_flip_structure": _with_structure_update("gs_flip_structure", msm_structures.flip_structure, always=True),
    "gs_mute_structure": _with_structure_update("gs_mute_structure", msm_structures.mute_structure),
    "gs_start_upgrade_structure": _with_structure_update("gs_start_upgrade_structure", msm_structures.start_upgrade_structure),
    "gs_upgrade_structure": _with_structure_update("gs_upgrade_structure", msm_structures.start_upgrade_structure),
    "gs_finish_upgrade_structure": _simple(msm_structures.finish_upgrade_structure),
    "gs_speed_up_upgrade_structure": _with_structure_update("gs_speed_up_upgrade_structure", msm_structures.speed_up_upgrade_structure),
    "gs_speedup_upgrade_structure": _with_structure_update("gs_speedup_upgrade_structure", msm_structures.speed_up_upgrade_structure),
    "gs_speed_up_upgrade_structure_video": _with_structure_update("gs_speed_up_upgrade_structure_video", msm_structures.speed_up_upgrade_structure),
    "gs_speedup_upgrade_structure_video": _with_structure_update("gs_speedup_upgrade_structure_video", msm_structures.speed_up_upgrade_structure),
    "gs_start_fuguing": _with_structure_update("gs_start_fuguing", msm_structures.start_fuguing),
    "gs_finish_fuguing": _with_structure_update("gs_finish_fuguing", msm_structures.finish_fuguing),
    "gs_speed_up_fuguing": _with_structure_update("gs_speed_up_fuguing", msm_structures.speed_up_fuguing),
    "gs_speedup_fuguing": _with_structure_update("gs_speedup_fuguing", msm_structures.speed_up_fuguing),
    "gs_collect_structure": _with_structure_update("gs_collect_structure", msm_structures.collect_structure),
    "gs_collect_from_mine": _with_structure_update("gs_collect_from_mine", msm_structures.collect_mine),
    "gs_check_in_structure": _simple(msm_structures.store_structure),
    "gs_store_structure": _simple(msm_structures.store_structure),
    "gs_store_decoration": _simple(msm_structures.store_structure),
    "gs_pack_in_structure": _simple(msm_structures.store_structure),
    "gs_pack_in_decoration": _simple(msm_structures.store_structure),
    "gs_move_structure_to_storage": _simple(msm_structures.store_structure),
    "gs_check_out_structure": _simple(msm_structures.unstore_structure),
    "gs_unstore_structure": _simple(msm_structures.unstore_structure),
    "gs_unstore_decoration": _simple(msm_structures.unstore_structure),
    "gs_pack_out_structure": _simple(msm_structures.unstore_structure),
    "gs_pack_out_decoration": _simple(msm_structures.unstore_structure),
    "gs_move_structure_from_storage": _simple(msm_structures.unstore_structure),
    "gs_start_baking": _simple(msm_structures.start_baking),
    "gs_speed_up_baking": _simple(msm_structures.speed_up_baking),
    "gs_speedup_baking": _simple(msm_structures.speed_up_baking),
    "gs_finish_baking": _simple(msm_structures.finish_baking),
    "gs_move_monster": _with_monster_update("gs_move_monster", msm_monsters.move_monster),
    "move_monster": _with_monster_update("move_monster", msm_monsters.move_monster),
    "gs_update_monster_position": _with_monster_update("gs_update_monster_position", msm_monsters.move_monster),
    "gs_flip_monster": _with_monster_update("gs_flip_monster", msm_monsters.flip_monster),
    "gs_mute_monster": _with_monster_update("gs_mute_monster", msm_monsters.mute_monster),
    "gs_add_soul_link": _with_monster_update_first("gs_add_soul_link", msm_monsters.add_soul_link),
    "gs_remove_soul_link": _with_monster_update_first("gs_remove_soul_link", msm_monsters.remove_soul_link),
    "gs_toggle_titansoul_fx": _with_monster_update_first("gs_toggle_titansoul_fx", msm_monsters.toggle_titansoul_fx),
    "gs_mega_monster_message": _mega_monster_handler,
    "gs_biggify_monster": _mega_monster_handler,
    "gs_bigify_monster": _mega_monster_handler,
    "gs_bigfy_monster": _mega_monster_handler,
    "gs_mega_monster": _mega_monster_handler,
    "gs_feed_monster": _with_monster_update("gs_feed_monster", msm_monsters.feed_monster),
    "gs_sell_monster": _sell_monster_handler,
    "gs_name_monster": _simple(msm_monsters.name_monster),
    "gs_collect_monster": _collect_monster("gs_collect_monster"),
    "gs_collect_multi_monster": _collect_monster("gs_collect_multi_monster"),
    "gs_buy_egg": _buy_egg_handler,
    "gs_hatch_egg": _hatch_egg_handler,
    "gs_sell_egg": _discard_structure_update(msm_monsters.sell_egg),
    "gs_speed_up_hatching": _discard_structure_update(msm_monsters.speed_up_hatching),
    "gs_viewed_egg": _viewed_egg_handler,
    "gs_claim_hatched_egg": _simple(msm_monsters.claim_hatched_egg),
    "gs_breed_monsters": _simple(msm_monsters.breed_monsters),
    "gs_finish_breeding": _finish_breeding(True),
    "gs_finish_breed_monsters": _finish_breeding(True),
    "gs_finish_breeding_monsters": _finish_breeding(True),
    "gs_finish_breeding_video": _finish_breeding(True),
    "gs_speed_up_breeding": _with_structure_update("gs_speed_up_breeding", msm_monsters.speed_up_breeding),
    "gs_speed_up_breeding_video": _with_structure_update("gs_speed_up_breeding_video", msm_monsters.speed_up_breeding),
    "gs_speedup_breeding": _with_structure_update("gs_speedup_breeding", msm_monsters.speed_up_breeding),
    "gs_speedup_breeding_video": _with_structure_update("gs_speedup_breeding_video", msm_monsters.speed_up_breeding),
    "gs_speedup_breed_monsters": _with_structure_update("gs_speedup_breed_monsters", msm_monsters.speed_up_breeding),
    "gs_speedup_breeding_monsters": _with_structure_update("gs_speedup_breeding_monsters", msm_monsters.speed_up_breeding),
    "gs_cancel_breeding": _simple(msm_monsters.cancel_breeding),
    "gs_remove_breeding": _simple(msm_monsters.cancel_breeding),
    "gs_check_in_monster": _simple(msm_monsters.store_monster),
    "gs_store_monster": _simple(msm_monsters.store_monster),
    "gs_move_monster_to_hotel": _simple(msm_monsters.store_monster),
    "gs_unstore_monster": _simple(msm_monsters.unstore_monster),
    "gs_check_out_monster": _simple(msm_monsters.unstore_monster),
    "gs_move_monster_from_hotel": _simple(msm_monsters.unstore_monster),
    "battle_teleport": _teleport_monster(False),
    "gs_teleport_monster": _teleport_monster(False),
    "gs_teleport": _teleport_monster(False),
    "gs_transpose_monster": _teleport_monster(False),
    "gs_move_monster_to_island": _teleport_monster(False),
    "gs_send_monster_home": _teleport_monster(True),
    "gs_send_to_magical_nexus": _send_to_magical_nexus_handler,
    "gs_send_bonus_for_looking_up_friend_id": _generic_success(),
    "gs_buy_island_skin": _simple(msm_islands.buy_island_skin),
    "gs_activate_island_theme": _simple(msm_islands.activate_island_theme),
    "gs_set_active_island_theme": _simple(msm_islands.activate_island_theme),
    "gs_equip_island_skin": _simple(msm_islands.activate_island_theme),
    "gs_mute_castle": _simple(msm_islands.mute_castle),
    "gs_get_island_boosts": _simple(msm_islands.get_island_boosts),
    "gs_island_boosts": _simple(msm_islands.get_island_boosts),
    "gs_get_island_boost": _simple(msm_islands.get_island_boosts),
    "gs_save_happiness_warnings_status": _generic_success(),
    "gs_collect_daily_reward": _generic_success(["rewards"]),
    "gs_collect_flip_level": _simple(msm_rewards.collect_flip_level),
    "gs_collect_flip_mini_game": _simple(msm_rewards.collect_flip_mini_game),
    "gs_collect_scratch_off": _simple(msm_rewards.collect_scratch_off),
    "gs_create_clubbox": _generic_success(),
    "gs_daily_login_buyback": _generic_success(["rewards"]),
    "gs_delete_mail": _generic_success(),
    "gs_finish_dish_harmonizing": _with_structure_update("gs_finish_dish_harmonizing", msm_structures.finish_dish_harmonizing, always=True),
    "gs_flip_minigame_cost": _simple(msm_rewards.flip_minigame_cost),
    "gs_friend_request_manage": _generic_success(),
    "gs_get_code": _generic_success(),
    "gs_get_friend_visit_data": _generic_success(["friend_data", "islands"]),
    "gs_get_friends": _generic_success(["friends"]),
    "gs_get_island_rank": _simple(msm_islands.get_island_rank),
    "gs_get_messages": _generic_success(["messages"]),
    "gs_get_random_tribes": _generic_success(["tribes"]),
    "gs_get_ranked_island_data": _generic_success(["islands"]),
    "gs_get_top10_island_data": _generic_success(["islands"]),
    "gs_get_torchgifts": _generic_success(["torchgifts"]),
    "gs_handle_facebook_help_instances": _facebook_help_instances_stub,
    "battle_claim_versus_rewards": _battle_claim_versus_rewards,
    "battle_set_music": _battle_set_music,
    "client_keep_alive": _client_keep_alive,
    "metric_event": _metric_event,
    "gs_get_tribal_island_data": _generic_success(["tribe", "members"]),
    "gs_hype_game": _generic_success(),
    "gs_incubate_dish_harmonizer_egg": _generic_success(["egg"]),
    "gs_leave_tribe_request": _generic_success(),
    "gs_light_torch": _generic_success(),
    "gs_place_on_gold_island": _simple(msm_monsters.place_on_gold_island),
    "gs_play_scratch_off": _simple(msm_rewards.play_scratch_off),
    "gs_purchase_scratch_off": _simple(msm_rewards.play_scratch_off),
    "gs_player_has_scratch_off": _simple(msm_rewards.player_has_scratch_off),
    "gs_get_prize_wheel": _simple(msm_rewards.get_prize_wheel),
    "gs_spin_prize_wheel": _simple(msm_rewards.spin_prize_wheel),
    "gs_collect_prize_wheel": _simple(msm_rewards.collect_prize_wheel),
    "gs_get_memory_game_numbers": _simple(msm_rewards.get_memory_game_numbers),
    "gs_player_save_profile": _generic_success(),
    "gs_process_event_cleanup": _generic_success(),
    "gs_box_add_egg": _simple(msm_box.box_monster_command),
    "gs_box_add_monster": _simple(msm_box.box_monster_command),
    "gs_box_monster": _simple(msm_box.box_monster_command),
    "gs_box_purchase_fill": _with_monster_update("gs_box_purchase_fill", msm_box.box_purchase_fill),
    "gs_box_activate_monster": _with_monster_update("gs_box_activate_monster", msm_box.box_activate_monster),
    "gs_activate_box_monster": _with_monster_update("gs_activate_box_monster", msm_box.wake_wubbox),
    "gs_wake_wubbox": _with_monster_update("gs_wake_wubbox", msm_box.wake_wubbox),
    "gs_attempt_early_box_activate": _with_monster_update("gs_attempt_early_box_activate", msm_box.box_purchase_fill),
    "gs_purchase_evolve_unlock": _simple(msm_box.purchase_evolve_unlock),
    "gs_purchase_flip_mini_game": _simple(msm_rewards.purchase_flip_mini_game),
    "gs_rate_island": _generic_success(),
    "gs_refresh_tribe_requests": _generic_success(["requests"]),
    "gs_remove_friend": _generic_success(),
    "gs_save_composer_track": _generic_success(),
    "gs_set_last_timed_theme": _simple(msm_islands.set_last_timed_theme),
    "gs_speedup_dish_harmonizing": _with_structure_update("gs_speedup_dish_harmonizing", msm_structures.speed_up_dish_harmonizing, always=True),
    "gs_start_dish_harmonizing": _with_structure_update("gs_start_dish_harmonizing", msm_structures.start_dish_harmonizing, always=True),
    "gs_tribal_feed_monster": _generic_success(["rewards"]),
    "gs_start_synthesizing": _simple(msm_synthesis.start_synthesizing),
    "gs_speedup_synthesizing": _simple(msm_synthesis.speedup_synthesizing),
    "gs_collect_synthesizing_success": _simple(msm_synthesis.collect_synthesizing),
    "gs_collect_synthesizing_failure": _simple(msm_synthesis.collect_synthesizing),
    "gs_collect_synthesizing": _simple(msm_synthesis.collect_synthesizing),
    "gs_finish_synthesizing": _simple(msm_synthesis.collect_synthesizing),
    "gs_start_attuning": _simple(msm_synthesis.start_attuning),
    "gs_finish_attuning": _simple(msm_synthesis.finish_attuning),
    "gs_speedup_attuning": _simple(msm_synthesis.speedup_attuning),
    "gs_update_reattune_monster": _simple(msm_synthesis.update_reattune_monster),
    "gs_collect_reattune_monster": _simple(msm_synthesis.collect_reattune_monster),
    "gs_viewed_reattuned_monster": _simple(msm_synthesis.collect_reattune_monster),
    "purchase_costume": _costume_action("purchase_costume"),
    "equip_costume": _costume_action("equip_costume"),
    "gs_update_owned_costumes": _simple(msm_monsters.update_owned_costumes),
    "gs_update_properties": _generic_success(),
    "gs_update_sold_monsters": _generic_success(),
    "gs_update_titansoul_rewards": _generic_success(["rewards"]),
    "update_viewed_campaigns": _generic_success(),
    "gs_update_viewed_cards": _generic_success(["viewed_cards", "card_ids"]),
    "gs_open_card_packs": _simple(msm_cardalbum.open_card_packs),
    "gs_buy_card_album_store_item": _simple(msm_cardalbum.buy_card_album_store_item),
    "gs_buy_tile": _simple(msm_structures.buy_tile),
    "gs_save_paintstate": _simple(msm_structures.save_paintstate),
    "update_awakener": _simple(msm_structures.update_awakener),
    "gs_collect_card_album_rewards": _simple(msm_cardalbum.collect_card_album_rewards),
    "gs_collect_card_album_page_rewards": _simple(msm_cardalbum.collect_card_album_page_rewards),
    "card_album_reward_collect": _simple(msm_cardalbum.collect_card_album_rewards),
    "card_album_page_reward_collect": _simple(msm_cardalbum.collect_card_album_page_rewards),
    "gs_collect_rewards": _simple(msm_rewardtracks.collect_rewards),
    "gs_multi_neighbors": _generic_success(["neighbors"]),
    "gs_viewed_cruc_unlock": _generic_success(),
}
def resolve_login_username(params):
    """Which account is this? Falls back to the canonical default only if the client sent nothing."""
    for key in ("user_game_id", "username", "user_id", "bbb_id", "u"):
        if (params or {}).get(key):
            username = str((params or {}).get(key)).strip()
            if not username:
                return DEFAULT_USERNAME
            if username in LEGACY_DEFAULT_USERNAMES:
                return DEFAULT_USERNAME
            return username
    return DEFAULT_USERNAME


def ensure_player_save(username):
    """Create a fresh canonical account save for any missing player.

    The legacy Nextstars template path is intentionally not used anymore. It carried the old
    27-island, locked state and caused new players to inherit a stale account shape. Every missing
    account now starts from the canonical default save in msm_store.
    """
    from msm_store import _create_default_player_root, _player_file

    target = _player_file(username)
    if target.exists():
        return False

    root = _create_default_player_root(username)
    target.parent.mkdir(parents=True, exist_ok=True)
    save_user_data(username, root)
    logger.info("ensure_player_save: created a fresh canonical save for %s", username)
    return True


def handle_login(params, session=None):
    # Check if we have a client IP in the session; if so, use IP-based account mapping
    username = None
    
    if isinstance(session, dict) and "client_ip" in session:
        client_ip = session["client_ip"]
        try:
            from msm_store import get_username_for_ip
            username = get_username_for_ip(client_ip)
            logger.info(f"IP-based login: {client_ip} -> {username}")
        except Exception as e:
            logger.warning(f"Failed to resolve IP-based username for {client_ip}: {e}")
    
    # Fall back to normal username resolution if IP mapping failed or no IP provided
    if not username:
        username = resolve_login_username(params)
    
    if isinstance(session, dict):
        # Remember who this connection belongs to; every later command uses it.
        session["username"] = username
    try:
        ensure_player_save(username)
    except Exception:
        logger.exception("could not prepare a save for %s", username)
    # NOTE: this used to call _remove_all_trees() and save immediately, which erased every
    # monster, egg, structure and decoration on every island on each login. That is the main
    # reason nothing appeared to save.
    frames = [("USER_LOGIN", {"data": {}, "success": True, "user": username})]
    frames.extend(login_bootstrap_frames())
    return frames

def login_bootstrap_frames():
    frames = []
    game_settings = load_db_json("game_settings")
    if game_settings is not None:
        frames.append(("game_settings", dict(game_settings)))
    gs_initialized = load_db_json("gs_initialized")
    if gs_initialized is not None:
        frames.append(("gs_initialized", normalize_db_payload("gs_initialized", dict(gs_initialized))))

    frames.append(("gs_display_generic_message", {"force_logout": False, "msg": "Welcome to ZewicMsM Online"}))

    seen = {command for command, _ in frames}
    for command, payload in _load_captured_session_frames():
        if command in seen:
            continue
        frames.append((command, normalize_db_payload(command, dict(payload))))
    return frames

def clear_structures_now():
    """Clear the active runtime state and persist the empty snapshot back to disk."""
    username = DEFAULT_USERNAME
    try:
        root, player_object = load_player(username)
        _remove_all_trees(player_object)
        save_user_data(username, root)
        _rewrite_session_snapshot(username, root)
        logger.info("clear_structures_now: cleared runtime state and rewrote Nextstars snapshot for %s", username)
        return True
    except Exception:
        logger.exception("clear_structures_now failed for %s", username)
        return False


def restore_nextstars_player_data(username=None):
    """Restore the live Nextstars save from the captured session snapshot at the configured path."""
    username = username or DEFAULT_USERNAME
    snapshot_path = _session_nextstars_snapshot_path()
    try:
        if snapshot_path is not None and snapshot_path.exists():
            with snapshot_path.open("r", encoding="utf-8") as fh:
                restored_root = json.load(fh)
            if isinstance(restored_root, dict):
                from msm_store import _player_file
                target_path = _player_file(username)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with target_path.open("w", encoding="utf-8") as fh:
                    json.dump(restored_root, fh, indent=2, ensure_ascii=False)
                logger.info("restore_nextstars_player_data: overwrote %s with snapshot from %s", target_path, snapshot_path)
                return True

        root, player_object = load_player(username)
        _remove_all_trees(player_object)
        save_user_data(username, root)
        _rewrite_session_snapshot(username, root)
        logger.info("restore_nextstars_player_data: rewrote Nextstars from runtime state for %s", username)
        return True
    except Exception:
        logger.exception("restore_nextstars_player_data failed for %s", username)
        return False


def handle_logout(params, session=None):
    """Log out without touching the save.

    This used to call restore_nextstars_player_data(), which overwrote the live save with an old
    snapshot -- throwing away everything the player had just done. Handlers already persist after
    each action, so logging out needs to do nothing at all.
    """
    username = (session or {}).get("username") or (params or {}).get("username") or DEFAULT_USERNAME
    logger.info("logout: %s (save left as-is)", username)
    return [("USER_LOGOUT", {"success": True})]

def handle_command(command, params, session=None):
    """Dispatch one client frame.

    `session` is the per-connection state owned by the websocket loop. It carries the logged-in
    username, which is what makes each account read and write its OWN save; previously every
    handler ran as DEFAULT_USERNAME, so all 480 accounts shared Nextstars.json.
    """
    if command == "alive":
        return []
    if command == "USER_LOGIN":
        return handle_login(params, session)
    if command == "USER_LOGOUT":
        return handle_logout(params, session)
    aliased_command = _STATIC_ALIAS_RESPONSES.get(command)
    if aliased_command is not None:
        data = load_db_json(aliased_command)
        if data is None:
            logger.info("no captured response for %s (via %s)", command, aliased_command)
            return []
        return [(aliased_command, normalize_db_payload(aliased_command, dict(data)))]
    handler = GAMEPLAY_HANDLERS.get(command)
    if handler is not None:
        try:
            result = handler(current_username(session), params)
        except Exception:
            logger.exception("handler for %s raised", command)
            return []
        if result is None:
            logger.info("handler for %s had nothing to answer", command)
            return []
        if isinstance(result, list):
            return result
        return [(command, result)]
    data = load_db_json(command)
    if data is None:
        session_data = _load_captured_session_command(command)
        if session_data is not None:
            logger.info("using captured session response for %s", command)
            data = session_data
        else:
            logger.info("no captured response for %s", command)
            if "cruc" in command.lower() or "card" in command.lower():
                return [(command, {"success": True})]
            return []
    frames = [(command, normalize_db_payload(command, dict(data)))]
    for i in range(2, 10):
        chained = load_db_json(f"{command}_{i}")
        if chained is None:
            break
        frames.append((command, normalize_db_payload(command, dict(chained))))
    return frames
