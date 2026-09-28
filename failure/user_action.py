"""Canonical user-action contract (ERR-017, ERR-018)."""

from __future__ import annotations

from enum import StrEnum


class UserAction(StrEnum):
    NONE = "NONE"
    RETRY = "RETRY"
    WAIT = "WAIT"
    REFRESH = "REFRESH"
    SIGN_IN = "SIGN_IN"
    VERIFY = "VERIFY"
    UPDATE_PAYMENT = "UPDATE_PAYMENT"
    CHANGE_INPUT = "CHANGE_INPUT"
    CONTACT_SUPPORT = "CONTACT_SUPPORT"
    VIEW_STATUS = "VIEW_STATUS"
    REVIEW_DATA = "REVIEW_DATA"
    CHECK_STATUS = "CHECK_STATUS"


# Safe actions for indeterminate side-effecting mutations — never expose blind RETRY.
INDETERMINATE_SAFE_ACTIONS = frozenset(
    {
        UserAction.CHECK_STATUS,
        UserAction.WAIT,
        UserAction.VIEW_STATUS,
        UserAction.CONTACT_SUPPORT,
        UserAction.NONE,
    }
)


def safe_actions_for_indeterminate() -> list[str]:
    return [a.value for a in sorted(INDETERMINATE_SAFE_ACTIONS, key=lambda x: x.value)]
