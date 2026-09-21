"""Local experiment: infer opponent cargo and front-run its trip to the shed."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


BASE = Path(__file__).resolve().parents[2] / "opponents" / "public" / "c27" / "main.py"
SPEC = importlib.util.spec_from_file_location("logistics_front_run_base", BASE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load base agent: {BASE}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

PREMIUM = ("MELON", "STRAWBERRY", "MILK", "WOOL")
PRODUCT = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}
HORIZON = 8
SKIP_TOWN_STEPS = False
CARGO_MULTIPLIER = 100

_LAST_STEP = -1
_PREV_OPPONENT = None
_CARGO = []
_TRIGGERS = []
_AUTO_SHED = {}
_AUTO_SHED_STEP = -1


def _positions(farm):
    return [farm.get("farmer", [0, 0]), *(farm.get("hands", []) or [])]


def _shed_tiles(size):
    half = size // 2
    return {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}


def _item_and_yield(tile):
    if not isinstance(tile, dict):
        return None, 0
    quantity = max(0, int(tile.get("yield_units", 0) or 0))
    if quantity <= 0:
        return None, 0
    if tile.get("kind") == "PLANT":
        return tile.get("crop"), quantity
    animal = tile.get("animal")
    return PRODUCT.get(animal), quantity


def _tile(farm, position):
    x, y = map(int, position)
    tiles = farm.get("tiles") or []
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
        return tiles[y][x]
    return None


def _observe_cargo(opponent, step):
    global _PREV_OPPONENT, _CARGO, _AUTO_SHED, _AUTO_SHED_STEP
    current_positions = _positions(opponent)
    if _PREV_OPPONENT is None or step != _LAST_STEP + 1 or step % 24 == 0:
        if _PREV_OPPONENT is not None and step == _LAST_STEP + 1 and step % 24 == 0:
            _AUTO_SHED = {}
            for cargo in _CARGO:
                for item, quantity in cargo.items():
                    _AUTO_SHED[item] = int(_AUTO_SHED.get(item, 0) or 0) + int(quantity or 0)
            _AUTO_SHED_STEP = step
        else:
            _AUTO_SHED = {}
            _AUTO_SHED_STEP = -1
        _CARGO = [{} for _ in current_positions]
        _PREV_OPPONENT = copy.deepcopy(opponent)
        return

    previous_positions = _positions(_PREV_OPPONENT)
    size = len(opponent.get("tiles") or [])
    sheds = _shed_tiles(size)
    if len(_CARGO) < len(current_positions):
        _CARGO.extend({} for _ in range(len(current_positions) - len(_CARGO)))

    for index in range(min(len(previous_positions), len(current_positions))):
        previous_position = tuple(previous_positions[index])
        current_position = tuple(current_positions[index])
        # A loaded actor that began the previous action at the shed could DROP
        # before the market phase, so its private cargo is no longer trackable.
        if previous_position in sheds and _CARGO[index]:
            _CARGO[index] = {}

        item, previous_yield = _item_and_yield(_tile(_PREV_OPPONENT, previous_position))
        current_item, current_yield = _item_and_yield(_tile(opponent, current_position))
        harvested = (
            item in PREMIUM
            and previous_yield > 0
            and current_position == previous_position
            and (current_item != item or current_yield < previous_yield)
        )
        if harvested:
            quantity = previous_yield - current_yield if current_item == item else previous_yield
            _CARGO[index][item] = int(_CARGO[index].get(item, 0) or 0) + quantity

    _CARGO = _CARGO[: len(current_positions)]
    _PREV_OPPONENT = copy.deepcopy(opponent)


def _declared_sale(action, item):
    return any(
        isinstance(order, list)
        and len(order) >= 2
        and order[0] == "SELL"
        and order[1] == item
        for order in action.get("market", []) or []
    )


def _planned_quantity(item, start, stop):
    total = 0
    for future in range(start, min(stop, len(MODULE._TRACE))):
        for order in MODULE._TRACE[future].get("market", []) or []:
            if (
                isinstance(order, list)
                and len(order) >= 3
                and order[0] == "SELL"
                and order[1] == item
            ):
                total += max(0, int(order[2] or 0))
    return total


def _front_run(action, obs, opponent, step):
    global _TRIGGERS
    # Town consumption after this action replenishes supply before the cargo
    # arrives, weakening both prediction value and denial value.
    if SKIP_TOWN_STEPS and step % 4 == 0:
        return
    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return
    size = len(opponent.get("tiles") or [])
    sheds = _shed_tiles(size)
    positions = _positions(opponent)
    risks = []
    if _AUTO_SHED_STEP == step:
        for item, quantity in _AUTO_SHED.items():
            if item in PREMIUM and quantity > 0:
                risks.append((float(quantity), item, int(quantity), HORIZON))
    for index, cargo in enumerate(_CARGO[: len(positions)]):
        if not cargo:
            continue
        x, y = map(int, positions[index])
        distance = min(abs(x - sx) + abs(y - sy) for sx, sy in sheds)
        if not 1 <= distance <= HORIZON:
            continue
        for item, quantity in cargo.items():
            if item in PREMIUM and quantity > 0:
                risks.append((quantity / distance, item, int(quantity), distance))
    if not risks:
        return

    shed = (obs.get("private") or {}).get("shed") or {}
    choices = []
    for risk, item, opponent_quantity, distance in risks:
        if _declared_sale(action, item):
            continue
        planned = _planned_quantity(item, step + 1, step + distance + 1)
        quantity = min(
            max(0, int(shed.get(item, 0) or 0)),
            planned,
            opponent_quantity * CARGO_MULTIPLIER,
        )
        if quantity > 0:
            choices.append((risk * quantity, item, quantity, distance))
    if choices:
        _, item, quantity, distance = max(choices)
        orders.append(["SELL", item, quantity])
        action["market"] = orders
        _TRIGGERS.append((step, item, quantity, distance))


def agent(obs, config=None):
    global _LAST_STEP, _PREV_OPPONENT, _CARGO, _TRIGGERS, _AUTO_SHED, _AUTO_SHED_STEP
    step = int(obs.get("step", 0) or 0)
    if step == 0 or step <= _LAST_STEP:
        _LAST_STEP = -1
        _PREV_OPPONENT = None
        _CARGO = []
        _TRIGGERS = []
        _AUTO_SHED = {}
        _AUTO_SHED_STEP = -1
    player = int(obs.get("player", 0) or 0)
    opponent = (obs.get("farms") or [])[1 - player]
    _observe_cargo(opponent, step)
    action = MODULE.agent(obs, config)
    _front_run(action, obs, opponent, step)
    _LAST_STEP = step
    return action
