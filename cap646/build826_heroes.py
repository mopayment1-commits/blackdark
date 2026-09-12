"""Six Heroes binding resolver for CAPABILITY_BUILD_826 program.

Maps capability IDs to primary Hero, entry path, and binding status using the
canonical HERO_ENGINES registry (docs/HERO_SIX_BINDING_REPORT.json lineage).
"""
from __future__ import annotations

from typing import Any

# Canonical six-hero engines — capability_id membership from pentagonal binding report.
HERO_ENGINES: dict[str, dict[str, Any]] = {
    "Single-Sentence Oracle": {
        "live_endpoint": {"method": "GET", "path": "/api/oracle/persona-clarity/demo"},
        "ui_path": "/dashboard",
        "capability_ids": {
            24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 40, 47, 48, 50, 55, 56, 59, 66, 69, 86, 89, 90,
        },
    },
    "Public Accuracy Ledger": {
        "live_endpoint": {"method": "GET", "path": "/api/oracle/audit-chain/verify"},
        "ui_path": "/oracle-accuracy",
        "capability_ids": {61, 63, 64, 65, 100},
    },
    "Arbitrage Scanner": {
        "live_endpoint": {"method": "GET", "path": "/api/arbitrage/scanner/status"},
        "ui_path": "/dashboard",
        "capability_ids": {11, 40, 47, 48, 50, 52, 57, 69, 82, 83, 85, 86, 87, 88, 89},
    },
    "Whale Signal vs Noise": {
        "live_endpoint": {"method": "GET", "path": "/api/whale/signal-vs-noise"},
        "ui_path": "/dashboard",
        "capability_ids": {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 72, 75, 81, 85, 86, 88, 91, 92, 98},
    },
    "Stealth Advisor": {
        "live_endpoint": {"method": "POST", "path": "/api/whale/stealth-advisor"},
        "ui_path": "/dashboard",
        "capability_ids": {40, 50, 85, 86, 87, 88},
    },
    "B2B Feed": {
        "live_endpoint": {"method": "GET", "path": "/api/b2b/demo"},
        "ui_path": "/institutional",
        "capability_ids": {67, 68, 71, 74, 77, 81, 84, 91, 92, 98, 99, 100},
    },
}

# Batch01 build IDs with explicit hero when not in HERO_ENGINES lists above.
_BATCH01_FALLBACK: dict[int, str] = {
    17: "Whale Signal vs Noise",
}

# Batch02 (26–50) — oracle / on-chain / market surfaces
_BATCH02_FALLBACK: dict[int, str] = {
    **{cid: "Single-Sentence Oracle" for cid in range(26, 36)},
    36: "Whale Signal vs Noise",
    37: "Whale Signal vs Noise",
    38: "Whale Signal vs Noise",
    39: "Whale Signal vs Noise",
    41: "Whale Signal vs Noise",
    42: "Whale Signal vs Noise",
    43: "Whale Signal vs Noise",
    44: "Whale Signal vs Noise",
    45: "Whale Signal vs Noise",
    46: "Whale Signal vs Noise",
    47: "Single-Sentence Oracle",
    48: "Single-Sentence Oracle",
    49: "Arbitrage Scanner",
    50: "Single-Sentence Oracle",
}

# Build batch 03 (51–75) — official batch02 spine
_BATCH03_FALLBACK: dict[int, str] = {
    51: "Single-Sentence Oracle",
    52: "Arbitrage Scanner",
    53: "Single-Sentence Oracle",
    54: "Arbitrage Scanner",
    58: "Single-Sentence Oracle",
    60: "Whale Signal vs Noise",
    62: "B2B Feed",
    63: "Public Accuracy Ledger",
    64: "Public Accuracy Ledger",
    65: "Public Accuracy Ledger",
    66: "Single-Sentence Oracle",
    67: "B2B Feed",
    68: "B2B Feed",
    70: "Whale Signal vs Noise",
    71: "Whale Signal vs Noise",
    72: "Whale Signal vs Noise",
    73: "Whale Signal vs Noise",
    74: "B2B Feed",
    75: "Whale Signal vs Noise",
    76: "Whale Signal vs Noise",
    77: "B2B Feed",
    78: "Whale Signal vs Noise",
    79: "Arbitrage Scanner",
    80: "Whale Signal vs Noise",
    81: "Whale Signal vs Noise",
    82: "Arbitrage Scanner",
    83: "Arbitrage Scanner",
    84: "B2B Feed",
    85: "Whale Signal vs Noise",
    86: "Single-Sentence Oracle",
    87: "Stealth Advisor",
    88: "Stealth Advisor",
    89: "Single-Sentence Oracle",
    90: "Single-Sentence Oracle",
    91: "B2B Feed",
    92: "B2B Feed",
    93: "Single-Sentence Oracle",
    94: "Single-Sentence Oracle",
    95: "Single-Sentence Oracle",
    96: "Single-Sentence Oracle",
    97: "Single-Sentence Oracle",
    98: "B2B Feed",
    99: "B2B Feed",
    100: "Public Accuracy Ledger",
}

# Build batches 05–06 (101–150) — official batch03 spine
_BATCH05_FALLBACK: dict[int, str] = {
    101: "Single-Sentence Oracle",
    102: "Single-Sentence Oracle",
    103: "B2B Feed",
    104: "B2B Feed",
    105: "Whale Signal vs Noise",
    106: "Public Accuracy Ledger",
    107: "Public Accuracy Ledger",
    108: "B2B Feed",
    109: "Single-Sentence Oracle",
    110: "Single-Sentence Oracle",
    111: "Whale Signal vs Noise",
    112: "Whale Signal vs Noise",
    113: "Whale Signal vs Noise",
    114: "Whale Signal vs Noise",
    115: "Whale Signal vs Noise",
    116: "Whale Signal vs Noise",
    117: "Public Accuracy Ledger",
    118: "Whale Signal vs Noise",
    119: "Whale Signal vs Noise",
    120: "Whale Signal vs Noise",
    121: "Whale Signal vs Noise",
    122: "Whale Signal vs Noise",
    123: "Whale Signal vs Noise",
    124: "Arbitrage Scanner",
    125: "Arbitrage Scanner",
    126: "Arbitrage Scanner",
    127: "Whale Signal vs Noise",
    128: "Whale Signal vs Noise",
    129: "Single-Sentence Oracle",
    130: "Single-Sentence Oracle",
    131: "Single-Sentence Oracle",
    132: "Single-Sentence Oracle",
    133: "Single-Sentence Oracle",
    134: "Single-Sentence Oracle",
    135: "Single-Sentence Oracle",
    136: "Single-Sentence Oracle",
    137: "Whale Signal vs Noise",
    138: "Whale Signal vs Noise",
    139: "Whale Signal vs Noise",
    140: "Whale Signal vs Noise",
    141: "Whale Signal vs Noise",
    142: "Whale Signal vs Noise",
    143: "Whale Signal vs Noise",
    144: "Whale Signal vs Noise",
    145: "Whale Signal vs Noise",
    146: "B2B Feed",
    147: "Arbitrage Scanner",
    148: "Single-Sentence Oracle",
    149: "Whale Signal vs Noise",
    150: "Whale Signal vs Noise",
}

_BATCH07_FALLBACK: dict[int, str] = {
    151: "Single-Sentence Oracle",
    152: "Single-Sentence Oracle",
    153: "Public Accuracy Ledger",
    154: "Single-Sentence Oracle",
    155: "Single-Sentence Oracle",
    156: "Single-Sentence Oracle",
    157: "Single-Sentence Oracle",
    158: "Single-Sentence Oracle",
    159: "B2B Feed",
    160: "B2B Feed",
    161: "B2B Feed",
    162: "Public Accuracy Ledger",
    163: "Single-Sentence Oracle",
    164: "Single-Sentence Oracle",
    165: "Single-Sentence Oracle",
    166: "Single-Sentence Oracle",
    167: "Single-Sentence Oracle",
    168: "Single-Sentence Oracle",
    169: "Single-Sentence Oracle",
    170: "Single-Sentence Oracle",
    171: "Single-Sentence Oracle",
    172: "Single-Sentence Oracle",
    173: "Single-Sentence Oracle",
    174: "Single-Sentence Oracle",
    175: "Single-Sentence Oracle",
    176: "Single-Sentence Oracle",
    177: "Single-Sentence Oracle",
    178: "Single-Sentence Oracle",
    179: "Single-Sentence Oracle",
    180: "Single-Sentence Oracle",
    181: "Single-Sentence Oracle",
    182: "Single-Sentence Oracle",
    183: "Whale Signal vs Noise",
    184: "Whale Signal vs Noise",
    185: "Whale Signal vs Noise",
    186: "Whale Signal vs Noise",
    187: "Whale Signal vs Noise",
    188: "Whale Signal vs Noise",
    189: "Whale Signal vs Noise",
    190: "Whale Signal vs Noise",
    191: "Whale Signal vs Noise",
    192: "Whale Signal vs Noise",
    193: "Whale Signal vs Noise",
    194: "Whale Signal vs Noise",
    195: "Whale Signal vs Noise",
    196: "Single-Sentence Oracle",
    197: "Whale Signal vs Noise",
    198: "Single-Sentence Oracle",
    199: "Single-Sentence Oracle",
    200: "Single-Sentence Oracle",
    201: "Whale Signal vs Noise",
    202: "Whale Signal vs Noise",
    203: "Single-Sentence Oracle",
    204: "Single-Sentence Oracle",
    205: "Single-Sentence Oracle",
    206: "Arbitrage Scanner",
    207: "Single-Sentence Oracle",
    208: "Single-Sentence Oracle",
    209: "Single-Sentence Oracle",
    210: "Single-Sentence Oracle",
    211: "Single-Sentence Oracle",
    212: "Single-Sentence Oracle",
    213: "Single-Sentence Oracle",
    214: "Single-Sentence Oracle",
    215: "Single-Sentence Oracle",
    216: "Single-Sentence Oracle",
    217: "B2B Feed",
    218: "Single-Sentence Oracle",
    219: "Public Accuracy Ledger",
    220: "Single-Sentence Oracle",
    221: "Public Accuracy Ledger",
    222: "Public Accuracy Ledger",
    223: "Single-Sentence Oracle",
    224: "Single-Sentence Oracle",
    225: "Single-Sentence Oracle",
    226: "Single-Sentence Oracle",
    227: "Single-Sentence Oracle",
    228: "Arbitrage Scanner",
    229: "Arbitrage Scanner",
    230: "Arbitrage Scanner",
    231: "Arbitrage Scanner",
    232: "Single-Sentence Oracle",
    233: "Arbitrage Scanner",
    234: "Single-Sentence Oracle",
    235: "Single-Sentence Oracle",
    236: "Single-Sentence Oracle",
    237: "Single-Sentence Oracle",
    238: "Single-Sentence Oracle",
    239: "Single-Sentence Oracle",
    240: "Single-Sentence Oracle",
    241: "Single-Sentence Oracle",
    242: "Single-Sentence Oracle",
    243: "Single-Sentence Oracle",
    244: "Single-Sentence Oracle",
    245: "Single-Sentence Oracle",
    246: "Public Accuracy Ledger",
    247: "B2B Feed",
    248: "Single-Sentence Oracle",
    249: "B2B Feed",
    250: "B2B Feed",
}



def _heroes_for(cid: int) -> list[str]:
    return [name for name, meta in HERO_ENGINES.items() if cid in meta["capability_ids"]]


def _primary_hero_for(cid: int) -> str | None:
    hits = _heroes_for(cid)
    if hits:
        return hits[0]
    if cid in _BATCH01_FALLBACK:
        return _BATCH01_FALLBACK[cid]
    if cid in _BATCH02_FALLBACK:
        return _BATCH02_FALLBACK[cid]
    return _BATCH03_FALLBACK.get(cid) or _BATCH05_FALLBACK.get(cid) or _BATCH07_FALLBACK.get(cid)


def hero_binding_for(cid: int) -> dict[str, Any]:
    """Return primary_hero, hero_entry_path, hero_binding_status for register."""
    heroes = _heroes_for(cid)
    if not heroes:
        fb = (
            _BATCH01_FALLBACK.get(cid)
            or _BATCH02_FALLBACK.get(cid)
            or _BATCH03_FALLBACK.get(cid)
            or _BATCH05_FALLBACK.get(cid)
            or _BATCH07_FALLBACK.get(cid)
        )
        if fb:
            heroes = [fb]
    hero = heroes[0] if heroes else None
    if not hero:
        return {
            "primary_hero": None,
            "secondary_heroes": [],
            "hero_entry_path": None,
            "hero_ui_path": None,
            "hero_binding_status": "UNBOUND",
        }
    meta = HERO_ENGINES[hero]
    cap_path = f"/api/cap646/{cid}/execute"
    entry = meta["live_endpoint"]["path"]
    return {
        "primary_hero": hero,
        "secondary_heroes": heroes[1:],
        "hero_entry_path": f"{entry} → {cap_path}",
        "hero_ui_path": meta.get("ui_path", "/cap646"),
        "hero_binding_status": "BOUND",
        "cap646_execute_path": cap_path,
    }


def enrich_binding_row(cid: int, row: dict[str, Any]) -> dict[str, Any]:
    binding = hero_binding_for(cid)
    row.update(binding)
    if binding["hero_binding_status"] == "UNBOUND" and row.get("status") == "COMPLETE_V6":
        blockers = list(row.get("blocker") or [])
        blockers.append("hero_binding:UNBOUND")
        row["status"] = "PARTIAL"
        row["blocker"] = blockers
    return row
