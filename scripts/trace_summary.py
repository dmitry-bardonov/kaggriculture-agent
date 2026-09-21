#!/usr/bin/env python3
"""Summarize declared market orders in compressed public replay agents."""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"trace_{path.parent.name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize(path: Path) -> dict:
    module = load(path)
    trace = getattr(module, "_TRACE", None)
    if not isinstance(trace, list):
        raise RuntimeError(f"{path} does not expose _TRACE")
    sells: dict[str, list[dict]] = defaultdict(list)
    order_types: Counter[str] = Counter()
    for step, action in enumerate(trace):
        for order in action.get("market", []) or []:
            if not isinstance(order, list) or not order:
                continue
            order_types[str(order[0])] += 1
            if order[0] == "SELL" and len(order) >= 3:
                sells[str(order[1])].append(
                    {"step": step, "day": step // 24, "hour": step % 24, "qty": order[2]}
                )
    return {
        "path": str(path),
        "trace_steps": len(trace),
        "order_types": dict(sorted(order_types.items())),
        "sells": dict(sorted(sells.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps([summarize(path.resolve()) for path in args.paths], indent=2))


if __name__ == "__main__":
    main()
