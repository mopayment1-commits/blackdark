"""
Deprecated stub — DO NOT USE.

Real whale intelligence lives in:
- whale_tracker.py
- whale_signal_classifier.py
- /api/whale/signal-vs-noise

Kept only so accidental imports fail loudly instead of returning fake scores.
"""

from __future__ import annotations


def detect_whale(*_args, **_kwargs):
    raise RuntimeError(
        "whale.detect_whale is deprecated. Use whale_tracker / whale_signal_classifier."
    )
