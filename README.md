[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/nagn4g/gta6-twitch-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/nagn4g/gta6-twitch-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Entry for the [make.fun "Forecast GTA VI's launch-day Twitch viewers hour by hour" bounty](https://make.fun/bounty/gta6-twitch-ccu-forecast-01) ($250 in USDC).

# GTA VI Twitch CCU forecaster

Deterministic, standard-library Python entry forecasting hours 2–24 with five viewer-count quantiles. Reads every sorted `*.in` in `/input` and writes matching `*.out` files in `/output`. Python 3.13 is the deployment target.

The model embeds 37 launch curves from the kit, attributed to SullyGnome hourly Twitch category averages. It compares first-hour log scale and the final six pre-launch hours' log slope, caps similarity kernels, and blends normalized analog curves with a quadratic OLS curve in log time and persistence. Whole-launch holdouts choose the bandwidth and blend.

Held-out log residual standard deviations are smoothed across nearby hours and shrunk towards the pooled variance, with a 0.10 floor. The requested approximate Student-t offsets use the supplied normal-quantile approximation. Predictions are positive, ordered, and capped at one billion. A missing first-hour print falls back to the latest pre-launch hourly mean.

Run:

```sh
MAKEFUN_INPUT_DIR=/path/to/kit/input MAKEFUN_OUTPUT_DIR=out python3 main.py
python3 tools/test_entry.py /path/to/kit/input
python3 tools/score.py --truth-dir /path/to/answers --output-dir out
python3 tools/score.py --self-test --loo
```

Practice score: unavailable because the supplied kit has no practice truth files. Its comparables explicitly exclude the four practice launches, so their curves are not embedded. No practice answers are inferred or fabricated. The quoted house baseline 0.387 remains unverified locally.

Contract checks passed on all four practice inputs, including two byte-identical runs per isolated case, approximately 0.115 seconds per run on the development machine. The scorer accepts truth files shaped as `{"hours":[{"hour":2,"viewers":12345},...]}` and checks the rules' worked scoring example. Development Python is 3.12; the implementation uses features supported by Python 3.13.

Nested LOO across the 37 embedded comparables: pinball **0.440130**, typical miss **84.85%**, 90% coverage **89.31%**. This broad, heterogeneous-launch result is poor and is not the requested four-practice LOO. The biggest errors are launch phase and shape (simultaneous unlocks versus rolling unlocks), with corresponding level errors; spread alone cannot fix them. This v0 has not demonstrated the paid cutoff. Four-practice blend selection, practice metrics, and the baseline sanity check require the missing practice truth.
