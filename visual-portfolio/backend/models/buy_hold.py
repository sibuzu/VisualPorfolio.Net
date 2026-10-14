from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class BuyHoldRequest(BaseModel):
    date: str = Field(min_length=1)
    amount_wan: str = Field(min_length=1)
    product_type: str = Field(min_length=1)
    code: str = Field(min_length=1)
    leverage: str | None = None

    @field_validator("product_type")
    @classmethod
    def normalize_product_type(cls, value: str) -> str:
        text = str(value or "").strip()
        aliases = {
            "stock": "股票",
            "stocks": "股票",
            "股票": "股票",
            "future": "期貨",
            "futures": "期貨",
            "期貨": "期貨",
        }
        normalized = aliases.get(text.lower()) or aliases.get(text)
        if not normalized:
            raise ValueError("商品 must be 股票 or 期貨")
        return normalized

    @field_validator("date", "amount_wan", "code", "leverage")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(value).strip()


class BuyHoldResponse(BaseModel):
    ok: bool = True
    filename: str
    display_name: str
