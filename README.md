# Kaggriculture agent research

Research code, evaluation tools, and experiment notes for the 2026 Kaggle
**Kaggriculture** simulation competition. The project targets a top-10 finish by
optimizing paired-seat win rate against a changing pool of strong public and
live opponents.

> **Repository checkpoint:** the code in this repository is the reproducible
> August 4 V3 checkpoint (`submission/main.py`, SHA-256
> `81a9e01b84594b917e0816910c637a22b403df09d93405eebe3732007a89a6ce`). Later
> V17–V47 submissions were developed and submitted from a newer workspace that
> is not available in this checkout. Their Kaggle results are documented below
> so the distinction between reproducible code and historical results is clear.

## Competition model

- One season contains 719 decisions, indexed 0–718.
- Each action has a one-second timeout and 60 seconds of cumulative overage.
- Ranking uses win/loss/tie skill rating; final coin margin is diagnostic only.
- Only the two most recent submissions remain active.
- The validated local engine is `kaggle-environments==1.32.2`. Version 1.32.3
  changes locked-tile movement and is not interchangeable.

The agent builds an early melon economy, expands into three quadrants, develops
a cow/sheep/strawberry farm, and uses public market state to anticipate an
opponent's premium-product sales. V3 combines a current-meta field route with a
horizon-eight cargo tracker, planned-sale denial, and end-of-day auto-shed
inference.

## Results

### Reproducible V3 checkpoint

The packaged V3 agent completed self-play without runtime errors and scored
**263–37 over 300 non-self-play local games**:

| Opponent | Games | W–L–T |
| --- | ---: | ---: |
| Kaito V19 | 60 | 52–8–0 |
| Logistics V2 | 60 | 51–9–0 |
| c27 | 30 | 26–4–0 |
| Hamburger V27 | 30 | 26–4–0 |
| Kaito V18 | 30 | 26–4–0 |
| Thiago live trajectory | 30 | 26–4–0 |
| webcainiao live trajectory | 30 | 26–4–0 |
| Structured Economic Policy | 30 | 30–0–0 |

Kaggle submission `55240030` passed server validation and completed its first
public match without errors.

### Later Kaggle submissions

These scores are historical Kaggle ratings and are not reproduced by the code
in this checkout:

| Version | Submission | Submitted | Rating |
| --- | ---: | --- | ---: |
| V17 Khafidin H4 | `55401961` | 2026-08-10 | **2918.8** |
| V47 exact public reactive | `56337164` | 2026-09-18 | 2117.2 |
| V39 Mkai safety | `56200170` | 2026-09-13 | 1585.4 |

At the September 21 snapshot, V47 and V39 were the active submissions. The
account ranked 1519/9710, while the top-10 cutoff had risen to 3001.6. V17 was
the strongest historical result but was no longer active.

Full experiment tables, rejected ideas, and failure analysis are recorded in
[`EXPERIMENTS.md`](EXPERIMENTS.md).

## Repository layout

```text
submission/main.py      packaged competition agent
candidates/             strategy variants and ablations
opponents/              attributed public and live regression opponents
scripts/tournament.py   paired-seat evaluation harness
scripts/                replay, trace, and packaging utilities
tests/                   loader and execution contract tests
EXPERIMENTS.md           chronological experiment log
THIRD_PARTY.md           source attribution
```

Large replay files, generated results, packaged submissions, and the virtual
environment are intentionally excluded from version control.

## Setup

```bash
./setup_env.sh
```

Run the contract tests:

```bash
.venv/bin/pytest -q
```

Run a paired-seat control tournament:

```bash
.venv/bin/python scripts/tournament.py \
  --candidate submission/main.py \
  --opponent c27=opponents/public/c27/main.py \
  --opponent kaito_v18=opponents/public/kaito_v18/main.py \
  --opponent hamburger_v27=opponents/public/hamburger_v27/main.py \
  --opponent frontier_v7=opponents/public/frontier_v7/main.py \
  --seeds 0:10 \
  --output results/control.jsonl
```

Package the exact tested file:

```bash
.venv/bin/python scripts/package_submission.py \
  submission/main.py artifacts/submission.tar.gz
```

Kaggle submission is deliberately a separate manual operation so a scarce
daily slot is never consumed by a local test or packaging command.

## Methodology

Candidate promotion requires clean self-play, both seats on every seed, the
previous best agent plus unrelated opponent families, and at least 100 paired
games. Decisions prioritize W/L/T; coin margin is used only as a tie-breaker.
Negative results are retained to prevent repeating failed experiments.

## License and attribution

This repository contains adapted public competition agents used as evaluation
controls. See [`THIRD_PARTY.md`](THIRD_PARTY.md) for attribution and source
details. No general-purpose license is asserted for third-party material.
