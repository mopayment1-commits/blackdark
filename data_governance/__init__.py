"""BLACKDARK Data Governance package (BGS-010 / DIG requirements)."""

from data_governance.registry import SourceRecord, list_sources, register_source
from data_governance.rights import assert_usage_allowed, usage_rights_status

__all__ = [
    "SourceRecord",
    "assert_usage_allowed",
    "list_sources",
    "register_source",
    "usage_rights_status",
]
