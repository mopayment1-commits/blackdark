"""Canonical protected financial operation registry (FDS-10/11/12)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProtectedOperation(str, Enum):
    BILLING_ADMIN_METRICS = "billing.admin.metrics"
    BILLING_ADMIN_SWEEP = "billing.admin.sweep"
    BILLING_PORTAL = "billing.portal"
    BILLING_CANCEL = "billing.cancel"
    BILLING_DOWNGRADE = "billing.downgrade"
    PRIVACY_DSR_EXPORT = "privacy.dsr.export"
    PRIVACY_DSR_ERASE = "privacy.dsr.erase"
    IDENTITY_PASSWORD_CHANGE = "identity.password.change"
    IDENTITY_EMAIL_CHANGE = "identity.email.change"
    USER_EXCHANGE_KEYS_STORE = "user.exchange_keys.store"
    USER_EXCHANGE_KEYS_DELETE = "user.exchange_keys.delete"
    INSTITUTIONAL_ROLE_CHANGE = "institutional.role.change"
    BREAK_GLASS_ACTIVATE = "break_glass.activate"
    ACCESS_REVIEW_SUBMIT = "access_review.submit"


@dataclass(frozen=True)
class OperationSpec:
    operation: ProtectedOperation
    mfa_required: bool
    step_up_required: bool
    org_permission: str | None
    resource_owner_required: bool
    privileged_session: bool
    resource_class: str
    description: str


_OPERATION_SPECS: dict[ProtectedOperation, OperationSpec] = {
    ProtectedOperation.BILLING_ADMIN_METRICS: OperationSpec(
        operation=ProtectedOperation.BILLING_ADMIN_METRICS,
        mfa_required=True,
        step_up_required=True,
        org_permission="billing.manage",
        resource_owner_required=False,
        privileged_session=True,
        resource_class="billing_admin",
        description="View privileged billing metrics",
    ),
    ProtectedOperation.BILLING_ADMIN_SWEEP: OperationSpec(
        operation=ProtectedOperation.BILLING_ADMIN_SWEEP,
        mfa_required=True,
        step_up_required=True,
        org_permission="billing.manage",
        resource_owner_required=False,
        privileged_session=True,
        resource_class="billing_admin",
        description="Run billing reconciliation sweep",
    ),
    ProtectedOperation.BILLING_PORTAL: OperationSpec(
        operation=ProtectedOperation.BILLING_PORTAL,
        mfa_required=False,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=False,
        resource_class="billing_subscription",
        description="Open hosted payment portal (payment method change)",
    ),
    ProtectedOperation.BILLING_CANCEL: OperationSpec(
        operation=ProtectedOperation.BILLING_CANCEL,
        mfa_required=False,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=False,
        resource_class="billing_subscription",
        description="Cancel subscription auto-renewal",
    ),
    ProtectedOperation.BILLING_DOWNGRADE: OperationSpec(
        operation=ProtectedOperation.BILLING_DOWNGRADE,
        mfa_required=False,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=False,
        resource_class="billing_subscription",
        description="Schedule subscription downgrade",
    ),
    ProtectedOperation.PRIVACY_DSR_EXPORT: OperationSpec(
        operation=ProtectedOperation.PRIVACY_DSR_EXPORT,
        mfa_required=True,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=True,
        resource_class="financial_export",
        description="Export personal/financial-linked data (DSR)",
    ),
    ProtectedOperation.PRIVACY_DSR_ERASE: OperationSpec(
        operation=ProtectedOperation.PRIVACY_DSR_ERASE,
        mfa_required=True,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=True,
        resource_class="financial_erasure",
        description="Erase personal data (DSR)",
    ),
    ProtectedOperation.IDENTITY_PASSWORD_CHANGE: OperationSpec(
        operation=ProtectedOperation.IDENTITY_PASSWORD_CHANGE,
        mfa_required=False,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=False,
        resource_class="identity_credential",
        description="Change account password",
    ),
    ProtectedOperation.IDENTITY_EMAIL_CHANGE: OperationSpec(
        operation=ProtectedOperation.IDENTITY_EMAIL_CHANGE,
        mfa_required=False,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=False,
        resource_class="identity_credential",
        description="Change account email",
    ),
    ProtectedOperation.USER_EXCHANGE_KEYS_STORE: OperationSpec(
        operation=ProtectedOperation.USER_EXCHANGE_KEYS_STORE,
        mfa_required=True,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=True,
        resource_class="financial_api_credential",
        description="Store exchange API credentials",
    ),
    ProtectedOperation.USER_EXCHANGE_KEYS_DELETE: OperationSpec(
        operation=ProtectedOperation.USER_EXCHANGE_KEYS_DELETE,
        mfa_required=True,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=True,
        privileged_session=True,
        resource_class="financial_api_credential",
        description="Delete exchange API credentials",
    ),
    ProtectedOperation.INSTITUTIONAL_ROLE_CHANGE: OperationSpec(
        operation=ProtectedOperation.INSTITUTIONAL_ROLE_CHANGE,
        mfa_required=True,
        step_up_required=True,
        org_permission="org.manage",
        resource_owner_required=False,
        privileged_session=True,
        resource_class="privileged_role",
        description="Change org member role/permissions",
    ),
    ProtectedOperation.BREAK_GLASS_ACTIVATE: OperationSpec(
        operation=ProtectedOperation.BREAK_GLASS_ACTIVATE,
        mfa_required=True,
        step_up_required=True,
        org_permission=None,
        resource_owner_required=False,
        privileged_session=True,
        resource_class="break_glass",
        description="Activate emergency privileged access",
    ),
    ProtectedOperation.ACCESS_REVIEW_SUBMIT: OperationSpec(
        operation=ProtectedOperation.ACCESS_REVIEW_SUBMIT,
        mfa_required=True,
        step_up_required=False,
        org_permission="compliance.view",
        resource_owner_required=False,
        privileged_session=True,
        resource_class="access_review",
        description="Submit privileged access recertification decision",
    ),
}


def operation_spec(operation: ProtectedOperation | str) -> OperationSpec:
    if isinstance(operation, str):
        operation = ProtectedOperation(operation)
    return _OPERATION_SPECS[operation]


def protected_operation_inventory() -> list[dict[str, object]]:
    return [
        {
            "operation": spec.operation.value,
            "mfa_required": spec.mfa_required,
            "step_up_required": spec.step_up_required,
            "org_permission": spec.org_permission,
            "resource_owner_required": spec.resource_owner_required,
            "resource_class": spec.resource_class,
            "description": spec.description,
        }
        for spec in _OPERATION_SPECS.values()
    ]
