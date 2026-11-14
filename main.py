#!/usr/bin/env python3
"""btc-cent-forecast-01 entry: forecast Bitcoin's price 240 minutes ahead.

For each case file in the input directory the program reads the 4,320
one-minute closes of the 72 hours up to the checkpoint and writes one
forecast: the price expected 240 minutes after the checkpoint.

Method (everything is computed from the case's own window, causally):
the score is a mean absolute error, so the best single guess is the
median of the price's distribution at the target minute. For a price
that mostly wanders, that median sits close to the last close, adjusted
by what the window itself says usually happens next. The adjustment is
the median of the window's own 240-minute changes, conditioned on the
move of the last 120 minutes: the window's samples are split into
terciles by their preceding 120-minute move, and the median forward
change of the tercile the current move falls in is taken, halved, and
clamped to +/-75 dollars so no single regime can drag the guess far
from the last close. On the kit's practice recording this estimator is
within a fraction of a percent of plain persistence on dense
out-of-sample checkpoints and ahead of it on the practice cases
themselves; persistence alone can never finish strictly below the
house baseline, which a prize requires.

Standard library only, no network, deterministic: the same case always
produces the same forecast.
"""
import glob
import json
import math
import os
import statistics

H = 240          # horizon in minutes
LOOKBACK = 120   # conditioning window in minutes
STEP = 5         # sample every 5th start inside the window
WEIGHT = 0.5     # shrink the conditional median toward the last close
CAP = 75.0       # largest adjustment, in dollars
MIN_USABLE = H + LOOKBACK + 30  # prices needed for a full tercile estimate


def median(xs):
    return statistics.median(xs)


def clamp(x, cap):
    return max(-cap, min(cap, x))


def clean(prices):
    """Keep only finite numbers, in order; bad entries never reach the math."""
    out = []
    for p in prices or []:
        try:
            v = float(p)
        except (TypeError, ValueError):
            continue
        if math.isfinite(v):
            out.append(v)
    return out


def pick_market(markets):
    """Prefer btc-usdc when it carries a usable series; otherwise take the
    longest usable market so a renamed or thin feed still yields a forecast."""
    usable = [(m, clean(m.get("prices"))) for m in (markets or [])]
    usable = [(m, ps) for m, ps in usable if ps]
    if not usable:
        return []
    for m, ps in usable:
        if m.get("id") == "btc-usdc" and len(ps) >= MIN_USABLE:
            return ps
    return max(usable, key=lambda mp: len(mp[1]))[1]


def forecast(prices):
    prices = clean(prices)
    if not prices:
        return 0.00001
    last = prices[-1]
    n = len(prices)
    if n <= H + LOOKBACK:
        return min(max(last, 0.00001), 9999999.99999)
    priors, futs = [], []
    for i in range(LOOKBACK, n - H, STEP):
        priors.append(prices[i] - prices[i - LOOKBACK])
        futs.append(prices[i + H] - prices[i])
    if len(priors) < 30:
        est = median(futs) if futs else 0.0
        return last + clamp(WEIGHT * est, CAP)
    cur = last - prices[-1 - LOOKBACK]
    srt = sorted(priors)
    t1, t2 = srt[len(srt) // 3], srt[2 * len(srt) // 3]

    def bucket(v):
        return 0 if v <= t1 else (2 if v > t2 else 1)

    sel = [f for pr, f in zip(priors, futs) if bucket(pr) == bucket(cur)]
    est = median(sel) if len(sel) >= 30 else median(futs)
    guess = last + clamp(WEIGHT * est, CAP)
    return min(max(guess, 0.00001), 9999999.99999)


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(in_dir, "*.in"))):
        with open(path, encoding="utf-8") as fh:
            case = json.load(fh)
        case_id = case.get("case") or os.path.splitext(os.path.basename(path))[0]
        prices = pick_market(case.get("markets"))
        guess = round(forecast(prices), 5)
        out = {"forecasts": [{"case": case_id, "price": guess}]}
        out_path = os.path.join(out_dir, case_id + ".out")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh)


if __name__ == "__main__":
    main()
