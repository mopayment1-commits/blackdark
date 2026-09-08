"""Account lifecycle — ID-020."""

from __future__ import annotations

from enum import StrEnum


class AccountState(StrEnum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    SUSPENDED = "SUSPENDED"
    COMPROMISED = "COMPROMISED"
    DELETION_PENDING = "DELETION_PENDING"
    DELETED = "DELETED"
    ANONYMIZED = "ANONYMIZED"


_AUTH_ALLOWED = frozenset({AccountState.ACTIVE, AccountState.PENDING_VERIFICATION})


def can_authenticate(state: str | AccountState | None) -> bool:
    try:
        return AccountState(str(state or AccountState.ACTIVE)) in _AUTH_ALLOWED
    except ValueError:
        return False


def transition_account_state(current: str, target: str) -> str:
    cur = AccountState(current)
    tgt = AccountState(target)
    allowed: dict[AccountState, set[AccountState]] = {
        AccountState.PENDING_VERIFICATION: {AccountState.ACTIVE, AccountState.DELETION_PENDING, AccountState.DELETED},
        AccountState.ACTIVE: {
            AccountState.LOCKED,
            AccountState.SUSPENDED,
            AccountState.COMPROMISED,
            AccountState.DELETION_PENDING,
        },
        AccountState.LOCKED: {AccountState.ACTIVE, AccountState.DELETION_PENDING},
        AccountState.SUSPENDED: {AccountState.ACTIVE, AccountState.DELETION_PENDING},
        AccountState.COMPROMISED: {AccountState.ACTIVE, AccountState.LOCKED, AccountState.DELETION_PENDING},
        AccountState.DELETION_PENDING: {AccountState.DELETED, AccountState.ANONYMIZED, AccountState.ACTIVE},
        AccountState.DELETED: {AccountState.ANONYMIZED},
        AccountState.ANONYMIZED: set(),
    }
    if tgt not in allowed.get(cur, set()):
        raise ValueError(f"Invalid account state transition {cur} -> {tgt}")
    return tgt.value
