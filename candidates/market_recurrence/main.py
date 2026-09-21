"""Local experiment: conservative recurrence-based one-step market front-running."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


BASE = Path(__file__).resolve().parents[2] / "opponents" / "public" / "c27" / "main.py"
SPEC = importlib.util.spec_from_file_location("market_recurrence_base", BASE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load base agent: {BASE}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

PREMIUM = ("MELON", "STRAWBERRY", "MILK", "WOOL")
PERIODS = {
    "STRAWBERRY": (48, 96),
    "MILK": (48, 96),
    "WOOL": (72, 144),
}
SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

_LAST_STEP = -1
_PREV_INVENTORY = None
_PREV_TOWN = None
_PREV_ACTION = None
_PREV_FARM = None
_PREV_PRIVATE = None
_HISTORY = {item: {} for item in PREMIUM}
_TRIGGERS = []


def _town_demand(item, step, town):
    demand = 0
    if step % 4 == 0:
        for shop in (town or {}).get("unlocked_shops", []) or []:
            products = SHOPS.get(shop, ())
            if item in products:
                demand += 2 if len(products) == 1 else 1
    if step % 12 == 0:
        day = step // 24
        demand += 4 if day >= 20 else 2 if day >= 10 else 1
    return demand


def _declared_sale(action, item):
    return any(
        isinstance(order, list)
        and len(order) >= 2
        and order[0] == "SELL"
        and order[1] == item
        for order in (action or {}).get("market", []) or []
    )


def _own_successful_sale(item):
    if _PREV_FARM is None or _PREV_PRIVATE is None or _PREV_ACTION is None:
        return 0
    shed = dict(_PREV_PRIVATE.get("shed") or {})
    inventories = [dict(row or {}) for row in (_PREV_PRIVATE.get("inventories") or [])]
    positions = [
        _PREV_FARM.get("farmer", [0, 0]),
        *(_PREV_FARM.get("hands", []) or []),
    ]
    actions = [
        _PREV_ACTION.get("farmer", ["PASS"]),
        *(_PREV_ACTION.get("hands", []) or []),
    ]
    shed_tiles = {(4, 4), (5, 4), (4, 5), (5, 5)}
    for index, action in enumerate(actions[: len(positions)]):
        if not isinstance(action, list) or not action or tuple(positions[index]) not in shed_tiles:
            continue
        inventory = inventories[index] if index < len(inventories) else {}
        if action[0] == "PICKUP" and len(action) >= 3:
            picked_item = action[1]
            room = max(0, 10 - sum(max(0, int(value or 0)) for value in inventory.values()))
            quantity = min(
                max(0, int(action[2] or 0)),
                max(0, int(shed.get(picked_item, 0) or 0)),
                room,
            )
            shed[picked_item] = int(shed.get(picked_item, 0) or 0) - quantity
        elif action[0] == "DROP":
            room = max(0, 100 - sum(max(0, int(value or 0)) for value in shed.values()))
            for dropped_item, raw_quantity in inventory.items():
                quantity = min(max(0, int(raw_quantity or 0)), room)
                shed[dropped_item] = int(shed.get(dropped_item, 0) or 0) + quantity
                room -= quantity
    declared = sum(
        max(0, int(order[2] or 0))
        for order in _PREV_ACTION.get("market", []) or []
        if isinstance(order, list)
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] == item
    )
    return min(max(0, int(shed.get(item, 0) or 0)), declared)


def _observe_opponent_sales(obs, step):
    global _PREV_INVENTORY, _PREV_TOWN, _PREV_ACTION, _PREV_FARM, _PREV_PRIVATE
    current = dict(((obs.get("market") or {}).get("inventory") or {}))
    if _PREV_INVENTORY is not None and step == _LAST_STEP + 1:
        for item in PREMIUM:
            net_external = (
                int(current.get(item, 0) or 0)
                - int(_PREV_INVENTORY.get(item, 0) or 0)
                + _town_demand(item, _LAST_STEP, _PREV_TOWN)
                - _own_successful_sale(item)
            )
            if net_external > 0:
                _HISTORY[item][_LAST_STEP] = net_external
    _PREV_INVENTORY = current
    _PREV_TOWN = copy.deepcopy(obs.get("town") or {})
    player = int(obs.get("player", 0) or 0)
    _PREV_FARM = copy.deepcopy((obs.get("farms") or [])[player])
    _PREV_PRIVATE = copy.deepcopy(obs.get("private") or {})


def _predict(item, target_step):
    periods = PERIODS.get(item)
    if periods is None:
        return 0
    first, _second = periods
    recent = int(_HISTORY[item].get(target_step - first, 0) or 0)
    if recent <= 0:
        return 0
    return recent


def _front_run_recurrence(action, obs, step):
    global _TRIGGERS
    # A town purchase after this action would replenish supply before the
    # predicted next-step sale and makes the one-step shift hard to justify.
    if step % 4 == 0:
        return
    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return
    shed = (obs.get("private") or {}).get("shed") or {}
    next_step = step + 1
    if next_step >= len(MODULE._TRACE):
        return
    choices = []
    for order in MODULE._TRACE[next_step].get("market", []) or []:
        if not (
            isinstance(order, list)
            and len(order) >= 3
            and order[0] == "SELL"
            and order[1] in PREMIUM
        ):
            continue
        item = order[1]
        if _declared_sale(action, item):
            continue
        prediction = _predict(item, next_step)
        available = int(shed.get(item, 0) or 0)
        quantity = min(available, int(order[2] or 0))
        if prediction > 0 and quantity > 0:
            choices.append((prediction * quantity, item, quantity))
    if choices:
        _, item, quantity = max(choices)
        orders.append(["SELL", item, quantity])
        action["market"] = orders
        _TRIGGERS.append((step, item, quantity))


def agent(obs, config=None):
    global _LAST_STEP, _PREV_INVENTORY, _PREV_TOWN, _PREV_ACTION, _PREV_FARM, _PREV_PRIVATE, _HISTORY, _TRIGGERS
    step = int(obs.get("step", 0) or 0)
    if step == 0 or step <= _LAST_STEP:
        _PREV_INVENTORY = None
        _PREV_TOWN = None
        _PREV_ACTION = None
        _PREV_FARM = None
        _PREV_PRIVATE = None
        _HISTORY = {item: {} for item in PREMIUM}
        _TRIGGERS = []
        _LAST_STEP = -1
    _observe_opponent_sales(obs, step)
    action = MODULE.agent(obs, config)
    _front_run_recurrence(action, obs, step)
    _PREV_ACTION = copy.deepcopy(action)
    _LAST_STEP = step
    return action
