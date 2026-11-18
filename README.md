# The World in One Page — 17 November 2026

[![make.fun](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/ariallg90-gif/news-image-20261117/rank.svg)](https://make.fun/bounty/news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/ariallg90-gif/news-image-20261117/reward.svg)](https://make.fun/bounty/news-image-20261117)

A one-page newspaper front page that sums up the world news of
**Tuesday 17 November 2026** in a single image.

`main.py` (Python 3.13, standard library only) draws the whole page from
scratch — a hand-made 5×7 bitmap font, a small raster canvas and a
minimal PNG encoder — and writes it to `entry.png` (1024×1024, well
under 1 MiB). No network, no randomness: two runs produce byte-identical
output.

## The six stories

1. **US strikes Iran** — US warplanes hit a missile site on Qeshm Island
   after attacks on ships in the Strait of Hormuz.
2. **Kerch Bridge hit** — Ukraine struck the bridge linking Russia to
   Crimea; a road span collapsed into the water.
3. **Trump lands in Manila** — Trump arrived for the ASEAN summit, opening
   a three-day Asia trip ending in talks with Xi and Putin.
4. **US loses measles status** — the US lost its measles elimination
   status after a year of nonstop spread, the first time since 2000.
5. **Mongolia president quits** — President Khurelsukh resigned after
   embezzlement accusations over a railway project.
6. **Japan scrambles jets** — Japan sent fighter jets up after two
   suspected Russian aircraft entered its airspace near Okinoshima.

Sources: Reuters, AP, Al Jazeera, PAHO and ABC World News Tonight
reporting of 17 November 2026.

## Run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## License

MIT — see [LICENSE](LICENSE).
