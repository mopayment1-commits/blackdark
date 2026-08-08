#!/usr/bin/env python3
"""
Activate & verify infrastructure stack (Postgres, Kafka, Vault, RL, Microservices).

Usage:
  python scripts/activate_infra.py          # verify local modules
  python scripts/activate_infra.py --train-rl
  python scripts/activate_infra.py --docker # print docker compose commands
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def _verify() -> dict:
    from bd_platform.infra_status import infra_ready_score

    return infra_ready_score()


def main() -> None:
    parser = argparse.ArgumentParser(description="BLACKDARK infra activation")
    parser.add_argument("--train-rl", action="store_true", help="Train PPO weights")
    parser.add_argument("--docker", action="store_true", help="Show docker compose up command")
    args = parser.parse_args()

    if args.docker:
        print("Docker stack (Postgres + Redis + Kafka + Vault + workers):")
        print("  set POSTGRES_PASSWORD=your_secret_in_.env")
        print("  docker compose up -d --build")
        print("  Web UI: http://localhost:8080")
        print("  Vault:  http://localhost:8200 (token: blackdark-dev-root)")
        print("  Kafka:  localhost:9092")
        return

    if args.train_rl:
        import random

        from ml.rl_policy import train_ppo_policy

        samples = [
            (
                {
                    "ret_24h": random.uniform(-0.08, 0.08),
                    "volatility": random.uniform(0.01, 0.15),
                    "obi_score": random.uniform(-1, 1),
                    "sentiment_score": random.uniform(-1, 1),
                },
                random.uniform(-1, 1),
            )
            for _ in range(300)
        ]
        r = train_ppo_policy(samples, epochs=80)
        print(f"PPO trained → {r['saved_to']}")

    score = asyncio.run(_verify())
    print(f"\nInfra ready: {score['ready_count']}/{score['total']} ({score['ready_percent']}%)")
    for name, ok in score["checks"].items():
        icon = "✅" if ok else "⏭️"
        print(f"  {icon} {name}")
    print("\nMatrix:")
    import json

    print(json.dumps(score["matrix"], indent=2, default=str)[:2000])


if __name__ == "__main__":
    main()
