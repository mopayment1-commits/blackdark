"""Card decline UI mapping (BILL-023)."""

from __future__ import annotations

from typing import Final

DECLINE_MAP: Final[dict[str, str]] = {
    "expired_card": "Your card has expired. Please update your payment method.",
    "incorrect_number": "The card number appears incorrect. Please check and try again.",
    "incorrect_cvc": "The security code (CVC) is incorrect.",
    "insufficient_funds": "Insufficient funds. Please use a different payment method.",
    "authentication_required": "Additional authentication is required. Please complete verification.",
    "generic_decline": "Your payment was declined. Please try another card or contact your bank.",
    "card_declined": "Your payment was declined. Please try another card or contact your bank.",
    "processing_error": "A processing error occurred. Please try again shortly.",
    "lost_card": "This card cannot be used. Please try another payment method.",
    "stolen_card": "This card cannot be used. Please try another payment method.",
}

DEFAULT_MESSAGE = "We couldn't process your payment. Please try again or use a different method."


def map_decline_code(code: str | None, *, decline_code: str | None = None) -> dict[str, str]:
    raw = (decline_code or code or "").strip().lower()
    user_message = DECLINE_MAP.get(raw, DEFAULT_MESSAGE)
    return {
        "code": raw or "unknown",
        "user_message": user_message,
        "internal_code": raw or "unknown",
    }
