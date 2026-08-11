#!/usr/bin/env python3
"""Train PPO linear policy and save weights to data/models/ppo_policy.json."""

from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _synthetic_samples(n: int = 200) -> list[tuple[dict[str, float], float]]:
    samples: list[tuple[dict[str, float], float]] = []
    for _ in range(n):
        ret = random.uniform(-0.08, 0.08)  # nosec B311 — synthetic ML training data
        vol = random.uniform(0.01, 0.15)  # nosec B311 — synthetic ML training data
        obi = random.uniform(-1, 1)  # nosec B311 — synthetic ML training data
        sent = random.uniform(-1, 1)  # nosec B311 — synthetic ML training data
        reward = ret * 2 + obi * 0.4 + sent * 0.2 - vol * 0.5
        samples.append(
            (
                {"ret_24h": ret, "volatility": vol, "obi_score": obi, "sentiment_score": sent},
                reward,
            )
        )
    return samples


def main() -> None:
    from ml.rl_policy import train_ppo_policy

    result = train_ppo_policy(_synthetic_samples(300), epochs=80, lr=0.04)
    print(f"PPO policy saved → {result['saved_to']}")
    print(f"Samples: {result['samples']} · Final loss: {result['final_loss']:.4f}")


if __name__ == "__main__":
    main()
