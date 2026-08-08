"""Public cryptographic proof — hash chain + Merkle inclusion + ZK-style commitments."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CHAIN_PATH = Path(os.getenv("ORACLE_AUDIT_CHAIN_PATH", "data/oracle_audit_chain.jsonl"))


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _hash_pair(left: str, right: str) -> str:
    return hashlib.sha256(f"{left}{right}".encode()).hexdigest()


def _leaf_hash(entry: dict[str, Any]) -> str:
    body = {k: v for k, v in entry.items() if k not in {"chain_hash", "merkle_proof"}}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


def _load_chain_entries() -> list[dict[str, Any]]:
    if not CHAIN_PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    with CHAIN_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def build_merkle_tree(entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    entries = entries if entries is not None else _load_chain_entries()
    if not entries:
        return {"root": "0" * 64, "leaves": 0, "levels": []}

    level = [_leaf_hash(e) for e in entries]
    levels: list[list[str]] = [level[:]]
    while len(level) > 1:
        nxt: list[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(_hash_pair(left, right))
        level = nxt
        levels.append(level[:])
    return {"root": level[0], "leaves": len(entries), "levels": levels}


def merkle_inclusion_proof(seq: int) -> dict[str, Any]:
    """Generate Merkle proof for record seq (1-based) without exposing siblings' data."""
    entries = _load_chain_entries()
    if seq < 1 or seq > len(entries):
        return {"valid": False, "error": "seq_out_of_range", "seq": seq, "total": len(entries)}

    tree = build_merkle_tree(entries)
    levels = tree["levels"]
    idx = seq - 1
    proof: list[dict[str, str]] = []
    for level in levels[:-1]:
        sibling_idx = idx ^ 1
        if sibling_idx < len(level):
            proof.append({"hash": level[sibling_idx], "position": "right" if idx % 2 == 0 else "left"})
        idx //= 2

    leaf = levels[0][seq - 1]
    return {
        "valid": True,
        "seq": seq,
        "leaf_hash": leaf,
        "merkle_root": tree["root"],
        "proof": proof,
        "verify_algorithm": "sha256(left+right) pairwise",
        "zk_style": "Verifier checks membership without full chain download",
    }


def verify_merkle_inclusion(proof_payload: dict[str, Any]) -> dict[str, Any]:
    leaf = proof_payload.get("leaf_hash", "")
    root = proof_payload.get("merkle_root", "")
    proof = proof_payload.get("proof") or []
    if not leaf or not root:
        return {"valid": False, "reason": "missing_leaf_or_root"}

    current = leaf
    for step in proof:
        sibling = step.get("hash", "")
        current = _hash_pair(current, sibling) if step.get("position") == "right" else _hash_pair(sibling, current)
    return {"valid": current == root, "computed_root": current, "expected_root": root}


def commit_record(record: dict[str, Any], *, salt: str | None = None) -> dict[str, Any]:
    """ZK-style commitment: publish hash(record||salt) — verifier checks without seeing record."""
    salt = salt or hashlib.sha256(os.urandom(32)).hexdigest()[:16]
    payload = json.dumps(record, sort_keys=True, default=str)
    commitment = hashlib.sha256(f"{salt}|{payload}".encode()).hexdigest()
    return {
        "commitment": commitment,
        "salt": salt,
        "algorithm": "sha256(salt|json(record))",
        "note": "Prover reveals record+salt later; verifier recomputes commitment",
    }


def verify_commitment(record: dict[str, Any], salt: str, commitment: str) -> dict[str, Any]:
    payload = json.dumps(record, sort_keys=True, default=str)
    expected = hashlib.sha256(f"{salt}|{payload}".encode()).hexdigest()
    return {"valid": expected == commitment, "commitment": commitment, "expected": expected}


def build_public_proof(*, tx_id: str | None = None, seq: int | None = None) -> dict[str, Any]:
    from oracle_audit_chain import chain_summary, verify_chain

    summary = chain_summary()
    verify = verify_chain()
    records = verify.get("records") or 0
    merkle = build_merkle_tree()

    root_payload = {
        "product": "BLACKDARK",
        "records": records,
        "valid": verify.get("valid"),
        "merkle_root": merkle["root"],
        "timestamp": _utcnow(),
    }
    merkle_root = hashlib.sha256(
        json.dumps(root_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    inclusion = merkle_inclusion_proof(seq) if seq else None

    return {
        "proof_type": "merkle_hash_chain_with_zk_commitments",
        "note": "Tamper-evident chain + Merkle inclusion proofs + commitment scheme",
        "merkle_root": merkle_root,
        "chain_merkle_root": merkle["root"],
        "chain_valid": verify.get("valid"),
        "total_records": records,
        "tx_id": tx_id,
        "inclusion_proof": inclusion,
        "endpoints": {
            "verify_chain": "/api/oracle/audit-chain/verify",
            "inclusion": "/api/platform/proof/inclusion?seq=N",
            "commit": "POST /api/platform/proof/commit",
            "verify_commitment": "POST /api/platform/proof/verify-commitment",
        },
        "public_accuracy": "/api/oracle/accuracy/public",
        "summary": summary,
    }
