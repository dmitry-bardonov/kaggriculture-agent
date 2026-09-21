# Experiment ledger

All dates are absolute and all records are from the perspective of the first
named agent. Local results use engine 1.32.2.

## 2026-08-04 — initial public cross-play

Five seeds, both seats (10 games/pair), no runtime errors:

| Agent | Opponent | W-L-T | Mean margin |
|---|---|---:|---:|
| c27 | Kaito V18 | 7-3-0 | +1845.7 |
| c27 | Hamburger V27 | 9-1-0 | +2884.6 |
| c27 | Frontier V7 | 10-0-0 | +17427.9 |
| Kaito V18 | Hamburger V27 | 9-1-0 | +3512.3 |
| Kaito V18 | Frontier V7 | 10-0-0 | +17786.2 |
| Hamburger V27 | Frontier V7 | 10-0-0 | +22478.2 |

c27 also went 10-0 against the public Mega Ensemble, Wide Sigma, Night
Harvest, and Adaptive agents. Those agents are not in the core promotion set
because they were far below the frontier controls.

## 2026-08-04 — c27 seed robustness

Twenty self-play seeds with independently loaded modules produced a seat-0
record of 8-11-1. Banks ranged from about 99k to 154k. Normal paths had roughly
25-40 invalid field actions; damaged paths had 100-159, concentrated in FEED,
CARE, COLLECT_FERTILIZER, and WATER. This supports a divergence-recovery
research branch.

## 2026-08-04 — rejected local fallback

Candidate: replace every illegal c27 field action with the highest-priority
valid action on the current tile.

Result: 0-20 against c27, zero errors, mean margin approximately -141291.

Decision: reject. Per-action repair destroys the positional synchronization of
the replay route. Future recovery must switch coherent policy blocks at safe
checkpoints.

## 2026-08-04 — c27 calibration gate and submission

Exact public c27 source SHA-256:
`b7f17796744b0d7050618fc019b5647f2bad891eef8559e227efdea5c2338196`.

Three seeds, both seats (six games/opponent), exact engine 1.32.2:

| Agent | Opponent | W-L-T | Mean margin |
|---|---|---:|---:|
| c27 | Kaito V18 | 5-1-0 | +2667.5 |
| c27 | Hamburger V27 | 6-0-0 | +3649.0 |

All four contract tests passed, including full self-play and archive identity.
Submitted as Kaggle submission `55237613` with four daily slots left. Validation
episode `89915086` completed without errors: c27 self-play ended 110694-110305.
The initial displayed skill rating was 600; this is a calibration value before
live matchmaking evidence, not a promotion result.

The first three public episodes were all wins with no runtime errors:

| Episode | Opponent | Seat | Final bank | Opponent bank |
|---:|---|---:|---:|---:|
| 89915618 | kreiack | 0 | 153905 | 66615 |
| 89916226 | Garigariyong | 0 | 163645 | 80458 |
| 89916846 | Nolan Liang | 1 | 114942 | 88835 |

These opponents were rated 799.4, 781.1, and 905.1 in the 10:53 UTC full
leaderboard snapshot. The control had reached 1035.8/rank 396 and was still
climbing, so these matches validate execution but not top-tier strength.

## 2026-08-04 — rejected early terminal handoff

Switching the replay route to c27's observation-driven terminal controller at
step 710 went 5-5 against c27 with mean margin -16.0. Starting at step 714 also
went 5-5 with mean margin -1.4. Reject: no paired-seat edge.

## 2026-08-04 — opponent-sale recurrence prototype

The prototype reconstructs our successful premium-product sales from the prior
shed, DROP/PICKUP actions, and declared market orders. After town demand and our
own supply are removed from the public inventory delta, the residual estimates
the opponent's net sale. It moves a c27 sale one step earlier only when the same
item appeared one production cycle ago and no intervening town-consumption step
would replenish supply.

Five seeds, both seats:

| Candidate | Opponent | W-L-T | Mean margin | c27 control margin |
|---|---|---:|---:|---:|
| recurrence | Kaito V18 | 7-3-0 | +1938.4 | +1845.7 |
| recurrence | Hamburger V27 | 9-1-0 | +2879.7 | +2884.6 |

Against c27 over ten seeds/both seats it went 10-10 with mean margin +46.35.
Decision: keep as a research component, but do not submit; the observed edge is
too small relative to paired-seed variance.

## 2026-08-04 — logistics cargo model v1

The model uses only public state. It confirms opponent premium harvests from
tile-yield transitions, carries estimated cargo by worker identity, and predicts
the sale window when a loaded worker is one to four moves from a shed tile. It
front-runs only quantities already scheduled in c27's next few trace steps and
skips steps immediately followed by town consumption.

Five seeds, both seats against public controls:

| Candidate | Opponent | W-L-T | Mean margin | c27 control |
|---|---|---:|---:|---:|
| logistics v1 | Kaito V18 | 9-1-0 | +2604.7 | 7-3, +1845.7 |
| logistics v1 | Hamburger V27 | 9-1-0 | +2684.2 | 9-1, +2884.6 |

Ten seeds/both seats against c27: **16-4-0**, mean margin **+1072.65**,
Wilson 95% lower bound 0.584. The standalone merge reproduced prototype
rewards exactly on a three-seed parity gate and passed all contract tests.

Submitted SHA-256
`c8396fa7b8c36cb8ec7faadc81be802b200b105126e2f9cb9f0c3fba4529d470`
as Kaggle submission `55238098`, leaving three daily slots.

### Logistics lookahead ablation

Fixed seeds 0-4, both seats:

| Horizon / town rule | c27 | Mean margin | Kaito V18 | Mean margin |
|---|---:|---:|---:|---:|
| 2 / skip | 5-5 | +403.5 | 8-2 | +2156.1 |
| 4 / skip (submitted v1) | 8-2 | +1291.0 | 9-1 | +2604.7 |
| 5 / skip | 8-2 | +1362.7 | 9-1 | +2676.4 |
| 6 / skip | 8-2 | +1397.2 | 9-1 | +2705.1 |
| 8 / skip | 8-2 | +1420.9 | 9-1 | +2726.6 |
| 8 / no skip (v2 candidate) | **9-1** | **+1573.3** | **9-1** | +2721.9 |

Horizon 8 is the board's maximum Manhattan distance from a corner to a shed
access tile. On held-out seeds 5-14, v2 went 17-3 against c27 with mean margin
+1240.4, for a combined **26-4 over 15 seeds/both seats**. It retained a 9-1
record against Hamburger V27. Decision: freeze as v2, but wait to submit until
the active c27 control has reached stronger live opponents; a third submission
would deactivate that control under the two-active-submission rule.

## 2026-08-04 — logistics v2 denial and auto-shed ablation

The cargo estimate is a timing signal, not a reliable quantity ceiling. Keeping
the opponent-cargo multiplier low left profitable planned c27 sales unadvanced.
Fixed seeds 0-9, both seats against c27:

| Quantity policy | W-L-T | Mean margin |
|---|---:|---:|
| 2x inferred cargo | 18-2-0 | +2433.40 |
| 3x inferred cargo | 18-2-0 | +2928.85 |
| Full planned sale | 18-2-0 | +3253.05 |
| Full planned sale + end-of-day auto-shed signal | **18-2-0** | **+3545.65** |

The final rule aggregates tracked worker cargo into an auto-shed arrival signal
at day end because worker inventories are automatically deposited overnight.
On the fixed c27 seeds 0-4 it went 9-1 with mean margin +3555.5; on held-out
seeds 5-14 it went 17-3 with +3269.9, for **26-4 overall**. Against Hamburger
V27 it went 9-1 (+1602.9) on seeds 0-4 and 17-3 (+1182.05) on seeds 5-14,
also **26-4 overall**. It remained 9-1 against Kaito V18 (+3535.8).

The standalone `submission/main.py` exactly reproduced the prototype rewards
on seeds 0-2 and all four contract tests passed. Submitted archive SHA-256
`862c8ab49e52664429e487c049f108509e19a3ee938b877d401dcd3f3f5852bb`
as Kaggle submission `55238816`, leaving two daily slots. Its first seven public
matches were seven wins with no runtime errors; the sixth beat
`the_vinci_coder` 150820-119244 and the seventh beat Gopal Krishna Gundumalla
149116-114032. The displayed skill rating was 1284.1 at the latest check and
was still in early calibration. Submitted v1 was independently 15-0 live and
had reached 1762.1, including a 157038-34845 win over `Chloe`, whose concurrent
leaderboard rating was 2651.7.

## 2026-08-04 — live trajectory regression set

Downloaded live replays revealed that replay step 0 is initialization with a
PASS action; the action produced from observation step N is stored at replay
step N+1. The extractor was corrected to use `steps[1:]`, producing 719-action
attributed opponents. Exact-engine reproduction gates passed:

| Live opponent | Seed | c27 seat | Reproduced banks |
|---|---:|---:|---:|
| webcainiao | 73798450 | 1 | 134198-129180 |
| Thiago Munhoz da Nobrega | 2056054047 | 0 | 118087-121640 |

The Thiago episode is the first live c27 loss. c27 also lost the reverse seat
on the same seed, 118332-121434, so it is a genuine strategy/seed weakness and
not only first-player ordering. The v2 candidate flipped both seats to wins,
120389-117951 and 120611-117745.

Broader paired-seat regression:

| Candidate | Opponent | Seeds | W-L-T | Mean margin |
|---|---|---:|---:|---:|
| logistics v1 | webcainiao | 0-9 | 17-3-0 | +4218.70 |
| logistics v2 | webcainiao | 0-9 | 17-3-0 | +3142.55 |
| logistics v1 | Thiago | 0-9 | **8-12-0** | **-1371.20** |
| logistics v2 | Thiago | 0-14 | **25-5-0** | **+1815.33** |

Decision: promote v2. It preserves the webcainiao win rate while dramatically
repairing the exact opponent style that defeated the public control and that
also beats submitted v1 locally. Because skill rating depends on wins rather
than bank margin, v1's larger webcainiao margin is not an advantage. Keep both
active agents for live calibration and spend neither remaining slot without a
new live loss or a locally verified matchup fix.

## 2026-08-04 — current-meta refresh and v3

Periodic public-notebook recon found Kaito v19, SHA-256
`9f18c729b16133443c981b0456515ef21824da72c89ce1387edab69c7e2fb536`.
Its published chronological study reports 41/49 wins on untouched
future/unseen replay cases. The decisive ablation was a refreshed current-meta
Himanshu medoid route: frozen v18 scored 23/46, c27 28/46, the new medoid 38/46,
and clone-aware late liquidation 39/46. Terminal liquidation alone added no
win. The exact public artifact was reconstructed and passed both-seat smoke.

On identical seeds 0-14/both seats against v19:

| Candidate | W-L-T | Mean margin |
|---|---:|---:|
| c27 | 4-26-0 | -4445.50 |
| submitted logistics v1 | 4-26-0 | -3397.70 |
| submitted logistics v2 | **25-5-0** | **+1137.57** |

This isolates the logistics timing layer as the cause of the reversal rather
than the inherited c27 field route. V3 therefore changes one material element:
use v19's current-meta field/market expert beneath the frozen horizon-8,
full-planned-sale, auto-shed logistics controller.

The code was frozen before held-out and unrelated-family tests. Results:

| Opponent | Seeds | W-L-T | Mean margin |
|---|---:|---:|---:|
| Kaito v19 | 0-14 | 26-4-0 | +2500.03 |
| Kaito v19 held-out | 15-29 | 26-4-0 | +2346.87 |
| logistics v2 | 0-14 | 25-5-0 | +1968.90 |
| logistics v2 held-out | 15-29 | 26-4-0 | +2277.03 |
| c27 | 0-14 | 26-4-0 | +4356.30 |
| Hamburger v27 | 0-14 | 26-4-0 | +1252.97 |
| Kaito v18 | 0-14 | 26-4-0 | +4731.77 |
| Thiago live trajectory | 0-14 | 26-4-0 | +4420.63 |
| webcainiao live trajectory | 0-14 | 26-4-0 | +3197.03 |
| Structured Economic Policy | 0-14 | **30-0-0** | +22842.53 |

Across the non-self-play gate, V3 was **263-37 over 300 games** with zero
errors. Independently loaded V3 self-play was symmetric at 14-14-2. Five local
contract tests now pass.

### Failed submission and repaired checkpoint

Submission `55239942` used source SHA-256
`3d7b5eba3ae37c0feca0d1008b9f7afc70988de4bf93d7edc40ca54628839d5e`
and failed validation episode `89932557` at step 1 in both seats. Server logs:

```text
TypeError: _v3_front_run() missing 2 required positional arguments: 'opponent' and 'step'
```

Root cause: code submissions use `get_last_callable`, which returns the last
new callable inserted into the executed module namespace. Redefining the
already-existing `agent` and `_kaggle_submission_entrypoint` names does not move
their insertion order, making newly introduced `_v3_front_run` the selected
callable. Normal module-import tests could not detect this.

The unsubmitted checkpoint defines a new one-argument `submission_agent` last
and adds a raw-file self-play test exercising Kaggle's loader path. All five
tests pass. Fixed source SHA-256:
`81a9e01b84594b917e0816910c637a22b403df09d93405eebe3732007a89a6ce`.
Per the user's 2026-08-04 pause instruction, do not resubmit until work resumes.
One daily slot remained at the pause.

The user then explicitly authorized fixing the errored submission. The exact
loader-only correction, SHA-256
`81a9e01b84594b917e0816910c637a22b403df09d93405eebe3732007a89a6ce`,
was submitted as `55240030`. Validation episode `89933183` ran all 720 steps:
both seats finished `DONE` without errors, retained the full 60 seconds of
overage, and ended 110805-110409. The submission status became `COMPLETE` with
the initial calibration rating 600.0. Stop here as requested; do not spend
another slot during this pause.

At the final read-only checkpoint, corrected v3 had no public episodes yet.
V2 added clean wins over `cmasch` (145274-31272) and Junichiro Morita
(172185-36955), reaching **15-0 audited live** at rating 2230.9. The concurrent
rank-10 cutoff was 2823.5.

Corrected v3's first public episode `89933745` then completed all 720 steps
without errors and beat Felix Allistar 185042-11771 from seat 1. It retained
all 60 seconds of overage and moved from the initial 600.0 calibration value to
658.2. This confirms live execution, but the opponent tier is not evidence of
top-10 strength; await stronger matchmaking after the pause.
