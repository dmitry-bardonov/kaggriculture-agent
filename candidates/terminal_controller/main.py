"""Local experiment: switch c27 to its observation-driven terminal policy earlier."""
from __future__ import annotations

import importlib.util
from pathlib import Path


TERMINAL_START = 714
BASE = Path(__file__).resolve().parents[2] / "opponents" / "public" / "c27" / "main.py"
SPEC = importlib.util.spec_from_file_location("terminal_controller_base", BASE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load base agent: {BASE}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def agent(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    if step >= TERMINAL_START:
        return MODULE._terminal_action(obs)
    return MODULE.agent(obs, config)
