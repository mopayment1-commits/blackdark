"""Pydantic models for security-sensitive API inputs."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AuthRegisterBody(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)
    name: str = Field(default="", max_length=80)
    username: str = Field(default="", max_length=24)
    accepted_terms: bool = False


class AuthLoginBody(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    mfa_code: str | None = Field(default=None, max_length=64)


class AuthMfaConfirmBody(BaseModel):
    code: str = Field(min_length=6, max_length=64)


class AuthMfaChallengeBody(BaseModel):
    challenge: str = Field(min_length=8, max_length=128)
    code: str = Field(min_length=6, max_length=64)


class AuthForgotPasswordBody(BaseModel):
    email: str = Field(min_length=5, max_length=254)


class AuthResetPasswordBody(BaseModel):
    token: str = Field(min_length=16, max_length=200)
    password: str = Field(min_length=10, max_length=128)


class AuthChangePasswordBody(BaseModel):
    current_password: str = Field(default="", max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class AuthProfileUpdateBody(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    username: str | None = Field(default=None, max_length=24)
    telegram_chat_id: str | None = Field(default=None, max_length=64)
    ui_lang: str | None = Field(default=None, max_length=12)
    ux_mode_pref: str | None = Field(default=None, max_length=24)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("ux_mode_pref")
    @classmethod
    def normalize_ux(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in {"beginner", "pro"}:
            raise ValueError("ux_mode_pref must be beginner or pro")
        return v


class ExecutionAutoBody(BaseModel):
    enabled: bool


class ExecutionOrderBody(BaseModel):
    symbol: str = Field(min_length=2, max_length=20)
    side: str = Field(pattern=r"^(buy|sell)$")
    amount_usd: float = Field(gt=0, le=100_000)


class UserApiKeyBody(BaseModel):
    exchange: str = Field(min_length=2, max_length=32)
    api_key: str = Field(min_length=8, max_length=256)
    api_secret: str = Field(min_length=8, max_length=256)
    label: str = Field(default="", max_length=64)

    @field_validator("exchange")
    @classmethod
    def normalize_exchange(cls, v: str) -> str:
        return v.strip().lower()


class RiskFreezeBody(BaseModel):
    reason: str = Field(default="manual", max_length=200)
