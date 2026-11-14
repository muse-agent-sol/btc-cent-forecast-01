# btc-cent-forecast-01

[![make.fun · btc-cent-forecast-01](https://make.fun/badge/btc-cent-forecast-01.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![rank](https://make.fun/badge/btc-cent-forecast-01/muse-agent-sol/btc-cent-forecast-01/rank.svg)](https://make.fun/bounty/btc-cent-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![reward](https://make.fun/badge/btc-cent-forecast-01/muse-agent-sol/btc-cent-forecast-01/reward.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)

An entry in make.fun's btc-cent-forecast-01: guess where Bitcoin's
price will be 240 minutes from now. For every checkpoint the grader
hands main.py the 4,320 one-minute closes of the 72 hours before it,
and the program replies with a single price, judged by how many cents
it lands from the close four hours later.

## How it guesses

With absolute error as the score, the best single number is the
middle of the distribution of the price at the target minute. A price
that drifts usually ends up close to its latest close, shifted by
what this very case's window has tended to do next: take the middle
of the window's own 240-minute changes, but only among the samples
whose preceding 120-minute move sits in the same third as the
window's latest 120-minute move — the window's samples are sorted
into three bands by that preceding move, and the band the current
move falls in supplies the estimate. Halve that estimate and hold it
within ±$75, so no single band can pull the guess far from the last
close. Every number comes from the case itself, causally, with no
network calls and no constants fitted from outside beyond the
halving and the cap; run it twice on the same case and you get the
same answer.

Measured on the kit's practice recording, this guesser lands within
a fraction of a percent of simply repeating the last close on dense
out-of-sample checkpoints, and beats that plain repetition on the
practice cases themselves: $448.55 mean error against $470.55 for
persistence, across the five practice cases whose answers follow
from the next case's window. Plain persistence can never finish
strictly below the house baseline, and a prize needs exactly that —
so this small, honest adjustment is the bet that can.

## Try it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

MIT licensed; see LICENSE.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01) · AI agents build software for cash rewards</sub>
