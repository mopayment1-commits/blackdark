"""Step-up gate for sensitive identity operations (password change, etc.)."""

from __future__ import annotations

from privileged_access.operations import ProtectedOperation

IDENTITY_PASSWORD_CHANGE = ProtectedOperation.IDENTITY_PASSWORD_CHANGE.value
IDENTITY_EMAIL_CHANGE = ProtectedOperation.IDENTITY_EMAIL_CHANGE.value
IDENTITY_ACCOUNT_DELETE = ProtectedOperation.PRIVACY_DSR_ERASE.value


def identity_step_up_satisfied(
    *,
    subject_id: str,
    operation: str,
    step_up_token: str | None = None,
    current_password: str | None = None,
    stored_hash: str | None = None,
) -> bool:
    """True when a fresh step-up token or successful password re-auth is present."""
    if step_up_token:
        from privileged_access.step_up import verify_step_up_grant

        if verify_step_up_grant(
            token=step_up_token,
            subject_id=subject_id,
            operation=operation,
            consume=True,
        ):
            return True
    if current_password and stored_hash:
        from auth_service import verify_password

        return verify_password(current_password, stored_hash)
    return False
