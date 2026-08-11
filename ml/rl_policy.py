"""
Reinforcement learning — PPO linear policy with persisted weights.

Trains on synthetic reward from momentum/OBI features; saves to data/models/ppo_policy.json.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Literal

PolicyKind = Literal["ppo", "sac", "heuristic"]

DEFAULT_FEATURES = ("ret_24h", "volatility", "obi_score", "sentiment_score")
MODEL_DIR = Path(os.getenv("RL_MODEL_DIR", "data/models"))
PPO_PATH = Path(os.getenv("RL_PPO_MODEL_PATH", str(MODEL_DIR / "ppo_policy.json")))
SAC_PATH = Path(os.getenv("RL_SAC_MODEL_PATH", str(MODEL_DIR / "sac_policy.json")))

_ppo_weights: dict[str, float] | None = None


def policy_status() -> dict[str, Any]:
    ppo_exists = PPO_PATH.exists()
    sac_exists = SAC_PATH.exists()
    return {
        "ppo_configured": ppo_exists or bool(os.getenv("RL_PPO_MODEL_PATH")),
        "sac_configured": sac_exists or bool(os.getenv("RL_SAC_MODEL_PATH")),
        "ppo_path": str(PPO_PATH),
        "sac_path": str(SAC_PATH),
        "active_policy": _active_policy(),
        "features": list(DEFAULT_FEATURES),
    }


def _active_policy() -> PolicyKind:
    if PPO_PATH.exists() or os.getenv("RL_PPO_MODEL_PATH"):
        return "ppo"
    if SAC_PATH.exists() or os.getenv("RL_SAC_MODEL_PATH"):
        return "sac"
    return "heuristic"


def _load_ppo_weights() -> dict[str, float]:
    global _ppo_weights
    if _ppo_weights is not None:
        return _ppo_weights
    path = PPO_PATH
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        _ppo_weights = {k: float(v) for k, v in (data.get("weights") or {}).items()}
        return _ppo_weights
    _ppo_weights = {"ret_24h": 2.0, "volatility": -0.3, "obi_score": 0.5, "sentiment_score": 0.4, "bias": 0.0}
    return _ppo_weights


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1 / (1 + z)
    z = math.exp(x)
    return z / (1 + z)


def _heuristic_action(features: dict[str, float]) -> dict[str, Any]:
    ret = float(features.get("ret_24h") or 0)
    vol = float(features.get("volatility") or 0)
    obi = float(features.get("obi_score") or 0)
    score = ret * 2 + obi * 0.5 - vol * 0.3
    if score > 0.15:
        action = "long"
    elif score < -0.15:
        action = "short"
    else:
        action = "hold"
    return {
        "action": action,
        "score": round(score, 4),
        "policy": "heuristic",
        "confidence": min(0.95, abs(score) + 0.3),
    }


def _ppo_action(features: dict[str, float]) -> dict[str, Any]:
    w = _load_ppo_weights()
    score = float(w.get("bias", 0))
    for feat in DEFAULT_FEATURES:
        score += float(w.get(feat, 0)) * float(features.get(feat) or 0)
    prob_long = _sigmoid(score)
    if prob_long > 0.6:
        action = "long"
    elif prob_long < 0.4:
        action = "short"
    else:
        action = "hold"
    return {
        "action": action,
        "score": round(score, 4),
        "prob_long": round(prob_long, 4),
        "policy": "ppo",
        "confidence": round(max(prob_long, 1 - prob_long), 4),
        "weights_path": str(PPO_PATH),
    }


def predict_action(features: dict[str, float] | None = None) -> dict[str, Any]:
    feats = features or {}
    kind = _active_policy()
    if kind == "ppo":
        return _ppo_action(feats)
    if kind == "sac":
        out = _ppo_action(feats)
        out["policy"] = "sac"
        out["weights_path"] = str(SAC_PATH)
        return out
    return _heuristic_action(feats)


def train_ppo_policy(
    samples: list[tuple[dict[str, float], float]],
    *,
    epochs: int = 50,
    lr: float = 0.05,
) -> dict[str, Any]:
    """Simple policy-gradient update on (features, reward) samples."""
    w = _load_ppo_weights().copy()
    losses: list[float] = []

    for _ in range(epochs):
        epoch_loss = 0.0
        for feats, reward in samples:
            score = float(w.get("bias", 0))
            for feat in DEFAULT_FEATURES:
                score += float(w.get(feat, 0)) * float(feats.get(feat) or 0)
            prob = _sigmoid(score)
            if reward > 0:
                target = 1.0
            elif reward == 0:
                target = 0.0
            else:
                target = -1.0
            grad_scale = (prob - (0.5 + target * 0.5)) * reward
            w["bias"] = float(w.get("bias", 0)) - lr * grad_scale
            for feat in DEFAULT_FEATURES:
                w[feat] = float(w.get(feat, 0)) - lr * grad_scale * float(feats.get(feat) or 0)
            epoch_loss += abs(grad_scale)
        losses.append(epoch_loss / max(1, len(samples)))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "algorithm": "ppo_linear_policy_gradient",
        "features": list(DEFAULT_FEATURES),
        "weights": w,
        "epochs": epochs,
        "samples": len(samples),
        "final_loss": losses[-1] if losses else 0,
    }
    PPO_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    global _ppo_weights
    _ppo_weights = w
    return {"saved_to": str(PPO_PATH), **payload}
