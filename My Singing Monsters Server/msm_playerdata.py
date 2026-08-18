import os
import struct

from msm_protocol import SFSFloat, SFSLong
from msm_store import load_user_data, save_user_data

DEBUG_MAX_NUMERIC_VALUE = 99_999_999


def _debug_currency_override_enabled():
    return True


def _decode_double_bits(value):
    if isinstance(value, dict) and '__double_bits' in value:
        bits_value = value.get('__double_bits')
        if isinstance(bits_value, str):
            bits_value = bits_value.strip()
            if bits_value.lower().startswith('0x'):
                bits_value = bits_value[2:]
            try:
                bits = int(bits_value, 16)
                return struct.unpack('>d', struct.pack('>Q', bits))[0]
            except (ValueError, TypeError):
                return value
        if isinstance(bits_value, (int, float)):
            try:
                return struct.unpack('>d', struct.pack('>Q', int(bits_value)))[0]
            except Exception:
                return value
    if isinstance(value, list) and len(value) == 8:
        try:
            return struct.unpack('>d', bytes(v & 0xFF for v in value))[0]
        except Exception:
            return value
    return value


def _convert_double_bit_values(value):
    if isinstance(value, dict):
        converted = {}
        for key, item in value.items():
            converted[key] = _convert_double_bit_values(item)
        if '__double_bits' in converted:
            return _decode_double_bits(converted)
        return converted
    if isinstance(value, list):
        return [_convert_double_bit_values(item) for item in value]
    return value


def _normalize_numeric_value(value, default=0):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, dict):
        value = _decode_double_bits(value)
    if isinstance(value, list):
        value = _decode_double_bits(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return int(float(stripped))
        except ValueError:
            try:
                return int(stripped, 0)
            except ValueError:
                return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return default


def _debug_value_for_key(key, value=0):
    if _debug_currency_override_enabled():
        if key == 'level':
            return 100
        if key in {'coins', 'diamonds', 'food', 'ethereal_currency', 'keys', 'relics', 'egg_wildcards', 'clubbox_tokens', 'starpower', 'xp', 'premium'}:
            return DEBUG_MAX_NUMERIC_VALUE
        if key in {'daily_bonus_amount', 'daily_relic_purchase_count', 'relic_diamond_cost', 'earned_starpower', 'speed_up_credit', 'battle_xp', 'battle_level', 'medals'}:
            return DEBUG_MAX_NUMERIC_VALUE
    return _normalize_numeric_value(value, 0)


_WIRE_LONG_KEYS = {
    "user_structure_id", "user_island_id", "user_monster_id", "user_egg_id", "user_breeding_id",
    "user_baking_id", "user_box_monster_id", "underlingUid", "underling_id", "user_underling_id",
    "selectedUnderlingUid", "parent_monster", "parent_user_monster_id", "parent_island",
    "parent_user_island_id", "active_island", "last_user_monster_id", "last_user_egg_id",
    "last_user_island_id", "last_collection", "last_collected", "last_fed", "date_created",
    "building_completed", "obj_end", "finishing_time", "complete_on", "seconds_remaining",
    "time_remaining", "started_at", "finished_at", "user", "chief", "last_login", "hatches_on", "laid_on",
    "bakery", "bbb_id", "c", "clubbox_tokens", "clubbox_tokens_actual", "coins_actual",
    "currencyScratchTime", "diamonds_actual", "egg_wildcards", "egg_wildcards_actual", "end_date",
    "entity_id", "ethereal_currency_actual", "event_start_time", "flipGameTime", "food_actual",
    "friend_gift", "keys", "keys_actual", "last_collect_all", "last_fb_post_reward", "last_feeding",
    "last_speed_up", "last_speed_up_breeding", "last_speed_up_nursery", "monsterScratchTime",
    "nextDailyLogin", "next_collect", "next_relic_reset", "prev_rank", "recipient_bbbid", "relics",
    "relics_actual", "s", "schedule_started_on", "seed", "speed_up_credit", "starpower",
    "starpower_actual", "start_date", "started_on", "time_of_next_gift", "total_starpower_collected",
    "user_achievement_id", "user_monster_1", "user_monster_2", "user_structure", "user_torch_id",
    "user_track_id", "premium",
}
_WIRE_FLOAT_KEYS = {
    "scale", "volume", "warp_speed", "coin_production_mod", "nursery_speed_mod", "total_points",
}


def _force_runtime_island_types(value, island_type=10):
    if isinstance(value, dict):
        island_like = any(key in value for key in ("island_id", "user_island_id", "islands", "islands_data", "island", "active_island"))
        if island_like or "island_type" in value:
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


def coerce_wire_types(value):
    value = _convert_double_bit_values(value)
    value = _force_runtime_island_types(value, 10)
    if isinstance(value, dict):
        for key, sub in list(value.items()):
            if isinstance(sub, dict) or isinstance(sub, list):
                value[key] = coerce_wire_types(sub)
            elif key in _WIRE_LONG_KEYS and isinstance(sub, int) and not isinstance(sub, bool):
                value[key] = SFSLong(sub)
            elif key in _WIRE_FLOAT_KEYS and isinstance(sub, (int, float)) and not isinstance(sub, bool):
                value[key] = SFSFloat(sub)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            value[i] = coerce_wire_types(item)
    return value

PROPERTY_ALIASES = [
    ("coins", "coins_actual"), ("diamonds", "diamonds_actual"), ("food", "food_actual"),
    ("ethereal_currency", "ethereal_currency_actual"), ("keys", "keys_actual"),
    ("relics", "relics_actual"), ("egg_wildcards", "egg_wildcards_actual"),
    ("clubbox_tokens", "clubbox_tokens_actual"), ("starpower", "starpower_actual"),
]

def _clamp_i32(value):
    return _normalize_numeric_value(value, 0)


def force_island_types(player_object, island_type=10):
    if not isinstance(player_object, dict):
        return
    for island in player_object.get("islands") or []:
        if not isinstance(island, dict):
            continue
        island["island_type"] = island_type
        island["type"] = island_type
    return player_object


def load_player(username):
    root = load_user_data(username)
    player_object = root.get("player_object") or {}
    force_island_types(player_object, 10)
    return root, player_object


def _ensure_account_premium_and_unlocked(player_object):
    if not isinstance(player_object, dict):
        return
    player_object["premium"] = 99_999_999
    player_object["has_premium"] = True
    player_object["is_premium"] = True
    player_object["premium_status"] = "premium"

    try:
        from msm_islands import ALL_THEME_IDS
    except Exception:
        ALL_THEME_IDS = list(range(1, 101))

    theme_ids = list(ALL_THEME_IDS)
    player_object["owned_island_themes"] = theme_ids
    player_object["owned_themes"] = theme_ids
    player_object["unlocked_themes"] = theme_ids
    player_object["available_themes"] = theme_ids
    player_object.setdefault("active_island_themes", [])

    for island in player_object.get("islands") or []:
        if island is None:
            continue
        island["owned_themes"] = theme_ids
        island["unlocked_themes"] = theme_ids
        island["available_themes"] = theme_ids
        island["themes"] = theme_ids
        island["island_themes"] = theme_ids

    from msm_gamedata import all_monster_ids, monster_ids_allowed_on_island
    from msm_monsters import island_type_of, MAGICAL_NEXUS_ISLAND_TYPE, grant_full_book, repair_book_of_monsters_counts
    for island in player_object.get("islands") or []:
        if island is None:
            continue
        grant_full_book(island)
        island_type = island_type_of(island) or 1
        known_ids = set(island.get("book_monster_ids") or [])
        if island_type == MAGICAL_NEXUS_ISLAND_TYPE:
            known_ids.update(all_monster_ids())
        else:
            known_ids.update(monster_ids_allowed_on_island(island_type))
        island["book_monster_ids"] = sorted(known_ids)
        repair_book_of_monsters_counts(island)


def save_player(username, root):
    player_object = root.get("player_object")
    if player_object:
        force_island_types(player_object, 10)
        _ensure_account_premium_and_unlocked(player_object)
    save_user_data(username, root)


def get_active_island_id(player_object):
    return player_object.get("active_island", 0)


def find_island(player_object, island_id):
    for island in player_object.get("islands") or []:
        if island is not None and island.get("user_island_id") == island_id:
            return island
    return None


def island_type_of(island):
    if not island:
        return 0
    return island.get("island_type", island.get("type", island.get("island", 0))) or 0


def find_structure(island, structure_id):
    if island is None:
        return None
    for structure in island.get("structures") or []:
        if structure is not None and structure.get("user_structure_id") == structure_id:
            return structure
    return None


def find_monster(island, monster_id):
    if island is None:
        return None
    for monster in island.get("monsters") or []:
        if monster is not None and monster.get("user_monster_id") == monster_id:
            return monster
    return None


def find_island_by_structure(player_object, structure_id):
    for island in player_object.get("islands") or []:
        structure = find_structure(island, structure_id)
        if structure is not None:
            return island, structure
    return None, None


def find_monster_with_island(player_object, monster_id, preferred_island=None):
    if preferred_island is not None:
        monster = find_monster(preferred_island, monster_id)
        if monster is not None:
            return preferred_island, monster
    for island in player_object.get("islands") or []:
        monster = find_monster(island, monster_id)
        if monster is not None:
            return island, monster
    return None, None


_DAILY_RESET_HOUR_UTC = 15


def next_daily_reset_timestamp(now_ms=None):
    import time as _time
    now_ms = now_ms if now_ms is not None else int(_time.time() * 1000)
    day_ms = 86400000
    today_start = (now_ms // day_ms) * day_ms
    reset = today_start + _DAILY_RESET_HOUR_UTC * 3600000
    if reset <= now_ms:
        reset += day_ms
    return reset


def create_player_properties(player_object):
    properties = []
    for source_key, actual_key in PROPERTY_ALIASES:
        value = _debug_value_for_key(source_key, player_object.get(source_key, 0))
        if actual_key in _WIRE_LONG_KEYS and isinstance(value, int):
            value = SFSLong(value)
        properties.append({actual_key: value})
    xp = _debug_value_for_key('xp', player_object.get('xp', 0))
    level = _debug_value_for_key('level', player_object.get('level', 0))
    properties.append({"xp": SFSLong(xp) if isinstance(xp, int) else xp})
    properties.append({"level": level})
    properties.append({"daily_bonus_type": player_object.get("daily_bonus_type") or "none"})
    daily_bonus_amount = _debug_value_for_key('daily_bonus_amount', player_object.get('daily_bonus_amount', 0))
    properties.append({"daily_bonus_amount": SFSLong(daily_bonus_amount) if isinstance(daily_bonus_amount, int) else daily_bonus_amount})
    properties.append({"has_free_ad_scratch": bool(player_object.get("has_free_ad_scratch", True))})
    daily_relic_purchase_count = _debug_value_for_key('daily_relic_purchase_count', player_object.get('daily_relic_purchase_count', 0))
    relic_diamond_cost = _debug_value_for_key('relic_diamond_cost', player_object.get('relic_diamond_cost', 1))
    properties.append({"daily_relic_purchase_count": SFSLong(daily_relic_purchase_count) if isinstance(daily_relic_purchase_count, int) else daily_relic_purchase_count})
    properties.append({"relic_diamond_cost": SFSLong(relic_diamond_cost) if isinstance(relic_diamond_cost, int) else relic_diamond_cost})
    properties.append({"next_relic_reset": SFSLong(next_daily_reset_timestamp())})
    premium = _debug_value_for_key('premium', player_object.get('premium', 0))
    properties.append({"premium": premium})
    earned_starpower = _debug_value_for_key('earned_starpower', player_object.get('earned_starpower', 0))
    speed_up_credit = _debug_value_for_key('speed_up_credit', player_object.get('speed_up_credit', 0))
    battle_xp = _debug_value_for_key('battle_xp', player_object.get('battle_xp', 0))
    battle_level = _debug_value_for_key('battle_level', player_object.get('battle_level', 0))
    medals = _debug_value_for_key('medals', player_object.get('medals', 0))
    properties.append({"earned_starpower": SFSLong(earned_starpower) if isinstance(earned_starpower, int) else earned_starpower})
    properties.append({"speed_up_credit": SFSLong(speed_up_credit) if isinstance(speed_up_credit, int) else speed_up_credit})
    properties.append({"battle_xp": SFSLong(battle_xp) if isinstance(battle_xp, int) else battle_xp})
    properties.append({"battle_level": SFSLong(battle_level) if isinstance(battle_level, int) else battle_level})
    properties.append({"medals": SFSLong(medals) if isinstance(medals, int) else medals})
    return properties


def add_actual_currencies(result, player_object):
    for source_key, actual_key in PROPERTY_ALIASES:
        result[actual_key] = _debug_value_for_key(source_key, player_object.get(source_key, 0))


_CURRENCY_KEY_ALIASES = {actual: source for source, actual in PROPERTY_ALIASES}
_CURRENCY_KEY_ALIASES.update({source: source for source, _ in PROPERTY_ALIASES})


def charge_entity_cost(player_object, currency_key, cost=None, *, allow_negative=False):
    """Subtract a currency cost from a player object.

    Supports both the newer explicit (player_object, currency_key, cost) style and
    the older compatibility style (player_object, definition) used by the game
    handlers when they pass a monster or structure definition dict.
    """
    if not isinstance(player_object, dict):
        return False

    if currency_key is None:
        return True

    def _resolve_cost_and_currency(defn):
        if not isinstance(defn, dict):
            return None, 0

        for source_key, actual_key in PROPERTY_ALIASES:
            for field_name in (source_key, f"cost_{source_key}", f"{source_key}_cost", actual_key, f"cost_{actual_key}", f"{actual_key}_cost"):
                if field_name in defn:
                    value = defn.get(field_name)
                    if value is not None:
                        return source_key, _normalize_numeric_value(value, 0)

        for field_name in ("cost", "cost_coins", "coins_cost", "cost_currency"):
            if field_name in defn:
                value = defn.get(field_name)
                if isinstance(value, dict):
                    for candidate_key, candidate_value in value.items():
                        if candidate_key in {"coins", "diamonds", "food", "ethereal_currency", "keys", "relics", "egg_wildcards", "clubbox_tokens", "starpower", "premium"}:
                            return candidate_key, _normalize_numeric_value(candidate_value, 0)
                if value is not None:
                    return "coins", _normalize_numeric_value(value, 0)

        for field_name in ("coins", "diamonds", "food", "ethereal_currency", "keys", "relics", "egg_wildcards", "clubbox_tokens", "starpower", "premium"):
            if field_name in defn:
                return field_name, _normalize_numeric_value(defn.get(field_name), 0)

        return None, 0

    if isinstance(currency_key, dict) and cost is None:
        resolved_currency, resolved_cost = _resolve_cost_and_currency(currency_key)
        if resolved_currency is None:
            return True
        source_key = resolved_currency
        norm_cost = resolved_cost
    else:
        source_key = _CURRENCY_KEY_ALIASES.get(str(currency_key), str(currency_key))
        norm_cost = _normalize_numeric_value(cost, 0) if cost is not None else 0

    if norm_cost == 0:
        return True

    current = _normalize_numeric_value(player_object.get(source_key, 0), 0)
    if norm_cost < 0:
        player_object[source_key] = current - norm_cost
    else:
        if current < norm_cost and not allow_negative:
            return False
        player_object[source_key] = current - norm_cost

    for source_name, actual_name in PROPERTY_ALIASES:
        if source_name == source_key:
            player_object[actual_name] = player_object.get(source_key, 0)
            break

    return True


def action_result(success, id_key, id_value, with_properties=False):
    result = {"success": bool(success), id_key: SFSLong(id_value)}
    if with_properties:
        result["properties"] = []
    return result
