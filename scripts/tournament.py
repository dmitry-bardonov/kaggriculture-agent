#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path


EXPECTED_ENGINE = "1.32.2"


@dataclass(frozen=True)
class Game:
    opponent: str
    opponent_path: str
    seed: int
    candidate_seat: int


@dataclass
class Result:
    opponent: str
    seed: int
    candidate_seat: int
    candidate_reward: float | None
    opponent_reward: float | None
    candidate_status: str
    opponent_status: str
    outcome: str
    error: str | None = None


def load_agent(path: str):
    module_name = "agent_" + uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {path}")
    module = importlib.util.module_from_spec(spec)
    module_dir = str(Path(path).resolve().parent)
    sys.path.insert(0, module_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(module_dir)
    agent = getattr(module, "agent", None)
    if not callable(agent):
        raise RuntimeError(f"{path} has no callable agent")
    return agent


def play(candidate_path: str, game: Game) -> Result:
    try:
        import kaggle_environments
        from kaggle_environments import make

        if kaggle_environments.__version__ != EXPECTED_ENGINE:
            raise RuntimeError(
                f"Expected kaggle-environments {EXPECTED_ENGINE}, "
                f"got {kaggle_environments.__version__}"
            )
        candidate = load_agent(candidate_path)
        opponent = load_agent(game.opponent_path)
        lineup = [candidate, opponent]
        if game.candidate_seat == 1:
            lineup.reverse()
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": game.seed},
            debug=False,
        )
        env.run(lineup)
        final = env.steps[-1]
        candidate_state = final[game.candidate_seat]
        opponent_state = final[1 - game.candidate_seat]
        candidate_reward = candidate_state.reward
        opponent_reward = opponent_state.reward
        statuses_ok = (
            candidate_state.status == "DONE" and opponent_state.status == "DONE"
        )
        if not statuses_ok:
            outcome = "error"
        elif candidate_reward > opponent_reward:
            outcome = "win"
        elif candidate_reward < opponent_reward:
            outcome = "loss"
        else:
            outcome = "tie"
        return Result(
            opponent=game.opponent,
            seed=game.seed,
            candidate_seat=game.candidate_seat,
            candidate_reward=candidate_reward,
            opponent_reward=opponent_reward,
            candidate_status=candidate_state.status,
            opponent_status=opponent_state.status,
            outcome=outcome,
        )
    except Exception as exc:
        return Result(
            opponent=game.opponent,
            seed=game.seed,
            candidate_seat=game.candidate_seat,
            candidate_reward=None,
            opponent_reward=None,
            candidate_status="ERROR",
            opponent_status="UNKNOWN",
            outcome="error",
            error=f"{type(exc).__name__}: {exc}",
        )


def parse_seeds(value: str) -> list[int]:
    if ":" in value:
        start, stop = value.split(":", 1)
        seeds = list(range(int(start), int(stop)))
    else:
        seeds = [int(part) for part in value.split(",") if part.strip()]
    if not seeds:
        raise argparse.ArgumentTypeError("At least one seed is required")
    return seeds


def parse_opponent(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Use NAME=PATH")
    name, path = value.split("=", 1)
    return name, str(Path(path).resolve())


def score_rate(rows: list[Result]) -> float:
    if not rows:
        return 0.0
    return (
        sum(row.outcome == "win" for row in rows)
        + 0.5 * sum(row.outcome == "tie" for row in rows)
    ) / len(rows)


def wilson_lower(successes: float, total: int, z: float = 1.96) -> float:
    if total == 0:
        return 0.0
    p = successes / total
    denominator = 1 + z * z / total
    center = p + z * z / (2 * total)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return (center - spread) / denominator


def summarize(rows: list[Result]) -> list[dict]:
    summaries = []
    for opponent in sorted({row.opponent for row in rows}):
        group = [row for row in rows if row.opponent == opponent]
        valid = [row for row in group if row.outcome != "error"]
        wins = sum(row.outcome == "win" for row in valid)
        ties = sum(row.outcome == "tie" for row in valid)
        losses = sum(row.outcome == "loss" for row in valid)
        margins = [
            row.candidate_reward - row.opponent_reward
            for row in valid
            if row.candidate_reward is not None and row.opponent_reward is not None
        ]
        seats = {
            seat: score_rate([row for row in valid if row.candidate_seat == seat])
            for seat in (0, 1)
        }
        summaries.append(
            {
                "opponent": opponent,
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "errors": len(group) - len(valid),
                "score_rate": score_rate(valid),
                "wilson_lower": wilson_lower(wins + 0.5 * ties, len(valid)),
                "seat0_score_rate": seats[0],
                "seat1_score_rate": seats[1],
                "mean_margin": statistics.mean(margins) if margins else None,
                "min_margin": min(margins) if margins else None,
                "max_margin": max(margins) if margins else None,
            }
        )
    return summaries


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument(
        "--opponent", action="append", type=parse_opponent, required=True
    )
    parser.add_argument("--seeds", type=parse_seeds, default=parse_seeds("0:10"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--jobs", type=int, default=max(1, min(4, os.cpu_count() or 1))
    )
    args = parser.parse_args()

    candidate = args.candidate.resolve()
    if not candidate.is_file():
        parser.error(f"Candidate not found: {candidate}")
    for name, path in args.opponent:
        if not Path(path).is_file():
            parser.error(f"Opponent {name} not found: {path}")

    games = [
        Game(name, path, seed, seat)
        for name, path in args.opponent
        for seed in args.seeds
        for seat in (0, 1)
    ]
    rows: list[Result] = []
    with ProcessPoolExecutor(max_workers=args.jobs) as executor:
        futures = {executor.submit(play, str(candidate), game): game for game in games}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(
                f"{row.opponent} seed={row.seed} seat={row.candidate_seat} "
                f"outcome={row.outcome} rewards="
                f"{row.candidate_reward}/{row.opponent_reward}"
            )

    rows.sort(key=lambda row: (row.opponent, row.seed, row.candidate_seat))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        metadata = {
            "type": "metadata",
            "engine": EXPECTED_ENGINE,
            "candidate": str(candidate),
            "candidate_sha256": sha256(candidate),
            "seeds": args.seeds,
        }
        handle.write(json.dumps(metadata, sort_keys=True) + "\n")
        for row in rows:
            handle.write(json.dumps(asdict(row), sort_keys=True) + "\n")

    print(json.dumps(summarize(rows), indent=2, sort_keys=True))
    if any(row.outcome == "error" for row in rows):
        raise SystemExit(2)


if __name__ == "__main__":
    main()

