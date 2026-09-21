#!/usr/bin/env python3
"""Run one local game and summarize declared premium-product sale timing."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import uuid
from collections import defaultdict
from pathlib import Path

from kaggle_environments import make

from tournament import EXPECTED_ENGINE


PREMIUM = {"MELON", "STRAWBERRY", "MILK", "WOOL"}


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("replay_" + uuid.uuid4().hex, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    import kaggle_environments

    if kaggle_environments.__version__ != EXPECTED_ENGINE:
        raise RuntimeError(f"Expected engine {EXPECTED_ENGINE}")
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": args.seed},
        debug=False,
    )
    modules = [load_module(args.left.resolve()), load_module(args.right.resolve())]
    env.run([module.agent for module in modules])
    sales: list[dict[str, list[dict]]] = [defaultdict(list), defaultdict(list)]
    for recorded_step, states in enumerate(env.steps[:-1]):
        for player, state in enumerate(states):
            action = state.action if isinstance(state.action, dict) else {}
            for order in action.get("market", []) or []:
                if (
                    isinstance(order, list)
                    and len(order) >= 3
                    and order[0] == "SELL"
                    and order[1] in PREMIUM
                ):
                    sales[player][order[1]].append(
                        {
                            "step": recorded_step,
                            "day": recorded_step // 24,
                            "hour": recorded_step % 24,
                            "qty": int(order[2]),
                        }
                    )
    print(
        json.dumps(
            {
                "seed": args.seed,
                "rewards": [state.reward for state in env.steps[-1]],
                "sales": None if args.summary_only else [dict(sorted(player.items())) for player in sales],
                "debug": [
                    {
                        "history": {
                            item: len(rows)
                            for item, rows in getattr(module, "_HISTORY", {}).items()
                        },
                        "triggers": getattr(module, "_TRIGGERS", None),
                    }
                    for module in modules
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
