# GTA VI Twitch CCU Forecast — DESIGN.md (gta6-twitch-ccu-forecast-01)

- Competition: gta6-twitch-ccu-forecast-01, $250, top 20 paid ($50/$35/$25/$10×7/$7).
- Deadline: 2026-11-19T01:00:00Z (19 Nov 08:00 WIB). FREE entry. 2,773 submissions already.
- Task: forecast Twitch viewers in "Grand Theft Auto VI" category for hours 2–24 (UTC) of release day, 5 quantiles each (5%, 25%, 50%, 75%, 95%) of that hour's mean count. Final case cut at deadline = first hour's data only. Scoring: pinball loss on log scale. Must beat BOTH the house baseline (persistence, loss 0.387 on practice) AND a house AI model.
- Entry: public GitHub repo (created after competition opens, OSI licence) with main.py (Python 3.13) in root; reads /input/<id>.in, writes /output/<id>.out. Deterministic, ≤8s, 1 CPU, 1024 MB, stdlib only, no network, no model calls. Max 10 submissions/day, 20 total; last submission before deadline is final. Transcripts required (same strict transcript rules as frontend-01: recording FIRST, agent writes code INSIDE the recorded session, ≥30% lines authored, ≥5 turns, ≥2 write/edit per file).
- Repo: `gta6-twitch-forecast` under nagn4g, MIT. Payout wallet: existing make.fun Solana wallet ETUdAbs5...PvUx. Build on this VM with Codex in a recording.

## Verified facts (from the kit + live API, 17 Nov ~17:00 WIB)
- Practice cases (kit RULES.txt): p00 Marvel's Wolverine (2026-09-15), p01 Red Dead Redemption 2 (2018-10-26), p02 God of War Ragnarök (2022-11-09), p03 Marvel's Spider-Man 2 (2023-10-20). All console, midnight-local unlock. Source: SullyGnome hourly Twitch category averages.
- GTA VI unlock: midnight local, country by country — NZ first 2026-11-18T11:00:00Z, central Europe 23:00 UTC, UK 00:00 UTC, US east coast 05:00 UTC, west coast 08:00 UTC. Hour 1 = 00:00–01:00 UTC 19 Nov, BEFORE the US unlock → day is BACK-LOADED, peak evening UTC (19:00–22:00). Hour 1 is NOT the peak.
- Twitch game id 1867279146. Hour print = mean of valid minute reads (≥30 of 60, else no print).
- Live board (API, 17 Nov ~17:00 WIB): #1 loss 0.110 (stake-dot-com, "kernel log-log + console-shape bias"), #2 0.114, #3 0.120, #8 0.126 (best median, 16.1% miss, but band too narrow), #20 (paid cutoff) 0.133, #25 0.135. House baseline 0.387. So: need loss < 0.133 to get paid, < 0.11 to win.
- Starter main.py = persistence forecaster: quantiles = p1 * exp(z * 0.15 * sqrt(h-1)), z = [-1.645, -0.674, 0, 0.674, 1.645]. Input JSON: {"levels": [0.05,0.25,0.5,0.75,0.95], "known": [{"hour":1,"viewers":...}], "forecast": [{"hour":2},...]}. Output JSON: {"hours": [{"hour":h,"q":[5 quantiles]}]}.
- Input files contain comparables (other launches' hourly curves) + history — vendor the comparable data INTO main.py as constants (no network at runtime).

## Approach (synthesis of Duck.ai + Superbot, both consulted 17 Nov)
Core (both agree): scale-conditioned analog ensemble + parametric fallback.
- For each practice launch compute log-ratios r_{i,h} = log(Y_{i,h} / Y_{i,1}).
- Weight closer analogs (first-hour level ln p1 + pre-cutoff slope), cap weights.
- Blend analog curves + parametric curve (quadratic in log time, OLS, pure Python) + persistence (r=0). Blend weights by leave-one-launch-out (LOO) validation.
- Quantile offsets from HELD-OUT log residuals by lead-hour bins with shrinkage to pooled residuals (NOT an arbitrary widening rule). Student-t quantiles. Exponentiate, enforce positive + monotonic quantiles.
- Evaluate LOO (hours within a launch are dependent — evaluate per-launch, not per-hour).
- Keep the model SIMPLE (only 4 practice launches). Don't hard-code peak-then-decay — let the data choose the phase (hour 1 is pre-US-unlock, so the day builds).

Superbot additions (adopted, to be re-fitted from practice data — NOT hard-coded):
- Level/shape separation: level g = ln(mean over hours 6–23 of v_h) − ln p1; shape s_h = ln v_h − ln(mean over hours 6–23). Model the level once, the shape separately (hour-1 eccentricity otherwise gets baked into every hour).
- 20× peak-over-hour-1 cut (from naufalumer): above 20× means hour 1 fell before the unlock; ratios are bimodal (~1–3× vs ~9–20×+). Test on practice data.
- σ profile starting point (re-fit, don't hard-code): σ ≈ 0.16 at h2, 0.20 at h5–h8, 0.19 at h9–h14, 0.24 at h15–h19, 0.20 at h20–h24. σ_h from weighted residual SD, smoothed in h, floored at 0.10.
- Spread math: expected mean pinball ≈ 0.496·σ_h. Mis-sizing: 0.5× → +12% loss, 0.8× → +1.4%, 1.2× → +1.0%, 2.0× → +20%. Narrow is punished slightly harder than wide at the extremes. A median off 20% in log adds only ~2.1% loss.
- Extrapolation guard: GTA VI hour 1 may be 4–20× any comparable. Saturating multiplier floor (never extrapolate the log-log fit below 1.0×) — a structural guard, NOT a market claim. Do NOT hard-code market probabilities (Superbot's 1.75M+/2M+ market numbers are unverified web claims).
- DO NOT USE Superbot's ln M fit as printed (ln M = 9.22 − 0.70·ln p1): the intercept and the 4.2×→1.3× range do not reconcile arithmetically. Re-fit from the kit's practice data.

Duck.ai additions (adopted):
- Blend weights by LOO validation (not fixed).
- Warning: the 3.97M GTA VI showcase peak is NOT a Twitch launch-day forecast — don't anchor on it.
- Traps: too-narrow spread loses on surprises but huge intervals also hurt; normalize by first hour (raw scale analogs brittle).

## Build plan (v0 → v1 → v2, submit early, iterate)
- v0: weighted analog quantiles (the field's standard method) + parametric blend + residual-calibrated σ. Submit early to get a practice score on the board. Target: practice loss ≤ 0.133 (paid cutoff), ideally ≤ 0.12 (top 5).
- v1: level/shape separation + scale-conditioned median. Keep only if LOO improves.
- v2: bake off refinements (20× cut, class weights, pre-release tail, GTA tilt). Keep only what pays on LOO.
- Local scorer (tools/score.py): exact pinball loss on log scale + typical miss + 90% coverage. Must reproduce house baseline 0.387 on practice.
- NEVER hard-code practice answers. NEVER import practice truth into main.py. main.py is self-contained (stdlib only: json, math, os, sys, datetime, pathlib). Deterministic (fixed float summation order, sorted iteration, no clock, no randomness).
- Contract test: 23 rows, hours 2–24 once each, 5 finite non-decreasing quantiles in [1, 1e9], ≤8s per case.
- Submission ladder: at most ~8 submissions, one new commit each, never two in a day if avoidable, last at least 6h before deadline (19 Nov 01:00 UTC). Never submit without a local score.

## v1 implementation and calibration

v1 separates the log mean level of hours 6–23 from each launch's normalized
hourly shape. Gaussian analog weights use first-hour level and pre-release slope,
with water filling and a soft class signal from comparable peak ratios above 20.
The shape blends the analog curve with quadratic OLS in log time. Development
calibration fits a level regression correction and a linear spline shape correction on three
practice launches and evaluates the fourth. Only fitted coefficients are shipped;
the external truth file is never read by the entry or copied into the repository.
Smoothed held-out residual RMS sets Student-t(8) spreads with a 0.10 floor.
Level correction features are an intercept, log(hour-1 viewers / 100000), and
10 times the pre-release slope. Ridge strength is 0.001. The spline has fixed
knots at hours 2, 4, 6, 10, 14, 18, 21, 24 and coefficient ridge 1. These are
shared smooth calibration parameters, not stored practice curves. Final coefficients
use all four practice cases after selecting the configuration by practice LOO.

The selected Gaussian log-level bandwidth is 0.5, class strength 3, with an equal
analog/parametric shape blend. Persistence candidates of 0.10 and 0.25 were tested;
LOO selects zero persistence. The soft class probability comes from the weighted
frequency of comparable ratios exceeding 20; no target name selects a class.
Each normalized analog influence is capped at 0.25. For first-hour levels above
the comparable maximum, the predicted mean-level multiplier is floored at one.

Measured on the external practice truth, 2026-11-17:

| Case | Loss | Typical miss | 90% coverage | Contract max runtime |
| --- | ---: | ---: | ---: | ---: |
| p00 Wolverine | 0.078718 | 12.77% | 91.30% | 0.115 s |
| p01 RDR2 | 0.078112 | 13.33% | 95.65% | 0.115 s |
| p02 GoW Ragnarok | 0.058487 | 8.60% | 100.00% | 0.115 s |
| p03 Spider-Man 2 | 0.108927 | 17.41% | 91.30% | 0.115 s |
| Overall | **0.081061** | **12.98%** | **94.57%** | |

The <0.10 submission bar is met; the <0.05 stretch target is not. Practice LOO
loss is 0.096024 (per case 0.094534, 0.097053, 0.065563, 0.126947), with 91.30%
coverage. LOO selects hyperparameters on these same four cases, and sigma pools
their held-out residuals: this is a tuning diagnostic, not an independent test.
The final fitted practice score is optimistic relative to an unseen GTA VI launch.
Earlier cubic-shape variants scored 0.129441 and 0.112417; the fixed-knot spline
improved the shape errors. No practice launch is added to the analog library.

Reproduce calibration with `python3 tools/score.py --truth <external-path> --calibrate`;
score the entry with `python3 tools/score.py --truth <external-path>` (optionally
`--output-dir <saved-outputs>`). `--input-dir` selects the kit inputs. Run
`python3 tools/test_entry.py <kit-input-dir>` for two isolated runs per case.
All four cases pass finite, ordered, bounded quantiles; 23 unique hours; 8-second
limit; and byte-identical output. The scorer's rules worked-example self-test passes.
README.md and LICENSE are unchanged. No submission was made in this session.

## Risks

- Extrapolation (GTA VI hour 1 far above any comparable) — the risk that decides the result.
- Practice overfit (4 cases, all console single-player, none a mega event) — tuning to 0.11 on practice can lose on GTA VI.
- Transcripts — no recorded session = no paid place. Recording runs BEFORE the Codex session; Codex writes with apply_patch (not shell heredocs); ≥2 write/edit per file; ≥5 turns.
- Truth-source mismatch — SullyGnome hourly means vs house minute means differ by a few percent.
- Event risk — Twitch outage, category rename, Drops starting late. Wide upper tail is the only protection.
