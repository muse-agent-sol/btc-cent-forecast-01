#!/usr/bin/env python3
"""Bitcoin four-hour price guesser for the btc-cent-forecast-01 bounty.

Every case hands this program one file: the 4,320 one-minute closes of
Bitcoin covering the 72 hours that end at the case's checkpoint. The job
is to name a single price, the close expected 240 minutes past that
checkpoint, and the program writes that one number out per case.

How the guess is formed, using nothing but the case's own history:
scoring is by absolute error, so the honest answer is the middle of
where the price could land at the target minute. A drifting price
usually lands near its latest close, nudged by what this very window
has tended to do after similar moves. So the program gathers every
240-minute change inside the window, groups those samples into three
bands by the 120-minute move that came just before each of them, finds
which band the window's own latest 120-minute move belongs to, and
takes the middle forward change of that band. That middle change is
halved, so the guess stays anchored to the latest close, and held
within seventy-five dollars either way, so one unusual band cannot
yank the answer far from where the price actually stands. When a
window is too thin for banding, the program falls back to the middle
of all the forward changes it could gather.

Nothing here reaches the network and nothing is fitted to outside
data; the only constants are the halving and the seventy-five-dollar
leash, and the same case file always yields the same number.
"""
import glob
import json
import math
import os
import statistics

HORIZON_MIN = 240      # minutes ahead that the guess aims at
CONDITION_SPAN = 120   # minutes of recent move used to pick a band
SAMPLE_EVERY = 5       # take every fifth starting point in the window
SHRINK = 0.5           # pull the band's middle change halfway to the close
MAX_SHIFT = 75.0       # widest allowed nudge, in dollars
ENOUGH_POINTS = HORIZON_MIN + CONDITION_SPAN + 30  # closes a full banding needs
PRICE_FLOOR = 0.00001       # lowest price the grader accepts
PRICE_CEIL = 9999999.99999  # highest price the grader accepts


def middle_value(values):
    """The middle of a list of numbers."""
    return statistics.median(values)


def bound_shift(shift, limit):
    """Hold a nudge inside plus-or-minus `limit`."""
    return min(limit, max(-limit, shift))


def keep_in_range(price):
    """Hold a price inside the range the grader accepts."""
    return min(max(price, PRICE_FLOOR), PRICE_CEIL)


def sane_series(raw_series):
    """Drop anything that is not a finite number, keeping the order."""
    kept = []
    for raw in raw_series or []:
        try:
            num = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(num):
            kept.append(num)
    return kept


def choose_feed(feeds):
    """Take the btc-usdc feed when it is long enough; if not, take the
    longest feed that holds any usable closes, so an oddly named or
    sparse feed still produces a guess instead of nothing."""
    candidates = []
    for feed in feeds or []:
        series = sane_series(feed.get("prices"))
        if series:
            candidates.append((feed, series))
    if not candidates:
        return []
    for feed, series in candidates:
        if feed.get("id") == "btc-usdc" and len(series) >= ENOUGH_POINTS:
            return series
    longest = candidates[0]
    for feed, series in candidates[1:]:
        if len(series) > len(longest[1]):
            longest = (feed, series)
    return longest[1]


def project_price(series):
    """Guess the close HORIZON_MIN minutes from the end of `series`."""
    series = sane_series(series)
    if not series:
        return 0.00001
    latest = series[-1]
    count = len(series)
    if count <= HORIZON_MIN + CONDITION_SPAN:
        return keep_in_range(latest)
    earlier_moves = []
    later_moves = []
    for idx in range(CONDITION_SPAN, count - HORIZON_MIN, SAMPLE_EVERY):
        earlier_moves.append(series[idx] - series[idx - CONDITION_SPAN])
        later_moves.append(series[idx + HORIZON_MIN] - series[idx])
    if len(earlier_moves) < 30:
        typical = middle_value(later_moves) if later_moves else 0.0
        return latest + bound_shift(SHRINK * typical, MAX_SHIFT)
    recent_move = latest - series[-1 - CONDITION_SPAN]
    ordered = sorted(earlier_moves)
    low_cut = ordered[len(ordered) // 3]
    high_cut = ordered[2 * len(ordered) // 3]

    def band(move):
        if move <= low_cut:
            return 0
        if move > high_cut:
            return 2
        return 1

    peers = [
        later
        for earlier, later in zip(earlier_moves, later_moves)
        if band(earlier) == band(recent_move)
    ]
    if len(peers) >= 30:
        typical = middle_value(peers)
    else:
        typical = middle_value(later_moves)
    projection = latest + bound_shift(SHRINK * typical, MAX_SHIFT)
    return keep_in_range(projection)


def run():
    src_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    dst_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(dst_dir, exist_ok=True)
    pattern = os.path.join(src_dir, "*.in")
    for case_path in sorted(glob.glob(pattern)):
        with open(case_path, encoding="utf-8") as handle:
            payload = json.load(handle)
        stem = os.path.splitext(os.path.basename(case_path))[0]
        label = payload.get("case") or stem
        series = choose_feed(payload.get("markets"))
        price = round(project_price(series), 5)
        result = {"forecasts": [{"case": label, "price": price}]}
        dest_path = os.path.join(dst_dir, label + ".out")
        with open(dest_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle)


if __name__ == "__main__":
    run()
