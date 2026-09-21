from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator

Platform = Literal["LinkedIn", "Instagram", "Email", "X"]

class CopyRequest(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=5, max_length=5000)
    platform: Platform
    tone: str = Field(min_length=2, max_length=80)
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.9, gt=0, le=1)

    @field_validator("tone")
    @classmethod
    def clean_tone(cls, value: str) -> str:
        return " ".join(value.strip().split())

class GeneratedCopy(BaseModel):
    product_name: str
    platform: Platform
    tone: str
    subject: str = ""
    headline: str
    body: str
    call_to_action: str
    hashtags: list[str] = Field(default_factory=list)
    character_count: int = Field(ge=0)
    compliance_notes: list[str] = Field(default_factory=list)

class BatchRequest(BaseModel):
    custom_id: str = Field(min_length=1, max_length=64)
    request: CopyRequest
