#!/usr/bin/env python3
"""Create an attributed deterministic local opponent from a public replay."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import textwrap
import zlib
from pathlib import Path


TEMPLATE = '''"""Public replay trajectory; local research opponent only.

Source episode: {episode_id}
Source team: {team_name}
Replay SHA-256: {replay_sha256}
"""
import base64
import copy
import json
import zlib

_TRACE = json.loads(zlib.decompress(base64.b85decode(
{payload}
)).decode("utf-8"))


def agent(obs, config=None):
    step = min(int(obs.get("step", 0) or 0), len(_TRACE) - 1)
    return copy.deepcopy(_TRACE[step])
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("replay", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--player", type=int, choices=(0, 1), required=True)
    args = parser.parse_args()

    raw = args.replay.read_bytes()
    replay = json.loads(raw)
    # Replay index 0 is the initialization state. The action chosen for
    # observation step N is stored in recorded state N+1.
    actions = [
        states[args.player].get("action") or {}
        for states in replay["steps"][1:]
    ]
    encoded = base64.b85encode(
        zlib.compress(json.dumps(actions, separators=(",", ":")).encode("utf-8"), 9)
    ).decode("ascii")
    payload = "\n".join(repr(chunk) for chunk in textwrap.wrap(encoded, 100))
    # Adjacent string literals need indentation inside the function call.
    payload = "    " + "\n    ".join(payload.splitlines())
    team_name = replay.get("info", {}).get("TeamNames", [])[args.player]
    rendered = TEMPLATE.format(
        episode_id=replay.get("info", {}).get("EpisodeId"),
        team_name=team_name,
        replay_sha256=hashlib.sha256(raw).hexdigest(),
        payload=payload,
    )
    compile(rendered, str(args.output), "exec")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"created={args.output} team={team_name} steps={len(actions)}")


if __name__ == "__main__":
    main()
