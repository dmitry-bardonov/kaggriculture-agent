# Kaggriculture project memory

## Objective

Finish in the top 10 of the Kaggriculture simulation competition. At the
2026-08-04 11:59 UTC snapshot, the leader was 2929.5 and rank 10 was 2827.4;
use 2900 as the working safety target because ratings move continuously.

## Authoritative environment

- Competition: `kaggriculture`
- Engine for local promotion tests: `kaggle-environments==1.32.2`
- Season: 719 executed decisions, indexed 0 through 718
- Configuration: 720 episode steps, 24 turns/day, 30 days, starting money 3000
- Per-action timeout: 1 second; cumulative overage: 60 seconds
- Evaluation: win/loss/tie skill rating; coin margin does not directly affect rating
- Submission limit: 5/day; only latest 2 remain active
- Submission: `main.py` with `agent(obs)` at archive root
- Runtime: no network ingress or egress

Do not upgrade the engine without first diffing `kaggriculture.py`. Version
1.32.3 permits movement onto locked tiles; 1.32.2 does not.

## Engine facts that override prose documentation

- CARE banks +1 on each fed-and-cared day, not +2.
- Fertilizer is sellable through the generic SELL path.
- Market orders execute before town consumption.
- A sale at the $1 floor removes private stock but does not add market inventory.
- Only shed inventory can be sold; carried inventory must be dropped first.
- End-of-day shed overflow above 100 items is destroyed.
- A newly hired hand begins acting on the following turn.
- The final executed action is step 718.

## Current public meta

Strong public agents have converged around an early melon capital event,
three unlocked quadrants, approximately 8 cows, 5-6 sheep, strawberry
production, and about 12 hands/day. Recent differentiation is primarily market
timing, clone-aware front-running, and terminal liquidation rather than mature
farm composition.

`opponents/public/c27/main.py` is the strongest reproduced public control in
the initial local screen. The current `submission/main.py` is logistics v2:
the c27 field route plus a public-state opponent-cargo tracker, horizon-8 sale
front-running, full planned-sale denial, and end-of-day auto-shed inference.
It went 26-4 against c27 and 26-4 against Hamburger over seeds 0-14/both seats.

Submission state at the 2026-08-04 pause:

- `55238816`: logistics v2, SHA-256 `862c8ab4...52bb`; displayed rating 2230.9
  at the latest checkpoint, 15-0 through the audited live episodes.
- `55239942`: v19+logistics v3, SHA-256 `3d7b5eba...9d5e`; validation ERROR
  because Kaggle's raw loader selected `_v3_front_run` instead of `agent`.
- `55240030`: loader-corrected v3, SHA-256 `81a9e01b...a6ce`; server validation
  episode `89933183` completed all 720 steps as `DONE`/`DONE`, no errors,
  110805-110409. Its first public episode `89933745` was a clean 185042-11771
  win over Felix Allistar; displayed calibration rating 658.2.
- The user explicitly requested stopping after this correction because of the
  broader submission budget. Do not make another submission without a new
  explicit resume instruction.

The fixed but unsubmitted `submission/main.py` is SHA-256
`81a9e01b84594b917e0816910c637a22b403df09d93405eebe3732007a89a6ce`.
It defines a fresh `submission_agent(obs)` as the final callable and passes a
raw-file loader regression test plus the four original contract tests.

## Promotion protocol

1. Import the exact packaged `main.py`.
2. Self-play must finish `DONE`/`DONE`.
3. Test every seed from both seats.
4. Include the prior best and at least two unrelated public families.
5. Optimize W/L/T first; margin is a tie-breaker.
6. Inspect losses and preserve negative results.
7. Change one material variable per Kaggle submission.
8. Never submit an artifact that was not locally imported and executed.

Working promotion target: zero errors, overall score rate at least 60%, and
worst-seat score rate at least 50% over at least 100 paired games. A small
screen is evidence for further testing, not promotion proof.

## Negative results

- Replacing every invalid replay-tape action with an immediately useful local
  action lost 0-20 to c27 with mean margin about -141k. Replay routes depend on
  synchronized worker positions; isolated corrections cause cascading drift.
- Fixed micro-batching does not intrinsically preserve revenue. With no town
  consumption or opponent transaction between orders, permanent inventory
  impact makes split and unsplit liquidation equivalent.
- Logistics v1 loses 8-12 to the attributed Thiago live trajectory, mean
  margin -1371.2. V2 repairs this to 25-5 over 15 seeds/both seats and flips
  both seats on the exact live-loss seed.

## Resume checkpoint

Do not submit automatically when reopening the project. First re-read the
current competition limit and leaderboard and verify the user's submission
budget. V3 is the promotion leader: 263-37 across 300 non-self-play games,
including 52-8 against Kaito v19 and 51-9 against submitted v2. The fixed V3 is
already live as `55240030`; monitor its matches and turn its first meaningful
loss into a regression opponent. Preserve v2 as the live fallback.
