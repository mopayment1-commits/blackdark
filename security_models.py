"""Pydantic models for security-sensitive API inputs."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AuthRegisterBody(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=120)


class AuthLoginBody(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


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
