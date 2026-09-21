from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    api_key: str | None = field(default=None)
    model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    )
    mock_mode: bool = field(
        default_factory=lambda: os.getenv("MOCK_MODE", "0").strip() == "1"
    )

    temperature: float = field(
        default_factory=lambda: float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    )
    top_p: float = field(
        default_factory=lambda: float(os.getenv("DEFAULT_TOP_P", "0.9"))
    )

    max_concurrent: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    )
    max_retries: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRIES", "5"))
    )

    def __post_init__(self):
        # Load Gemini API key automatically from .env
        if self.api_key is None:
            self.api_key = os.getenv("GEMINI_API_KEY")

    @classmethod
    def from_env(cls, mock_mode: bool | None = None) -> "Settings":
        return cls(
            api_key=os.getenv("GEMINI_API_KEY"),
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            mock_mode=(
                os.getenv("MOCK_MODE", "0").strip() == "1"
                if mock_mode is None
                else mock_mode
            ),
            temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            top_p=float(os.getenv("DEFAULT_TOP_P", "0.9")),
            max_concurrent=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
            max_retries=int(os.getenv("MAX_RETRIES", "5")),
        )

    def validate(self) -> None:
        if self.mock_mode:
            return

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Add it to .env or use --mock."
            )