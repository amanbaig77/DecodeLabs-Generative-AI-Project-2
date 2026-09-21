from __future__ import annotations

from .models import GeneratedCopy
from .prompts import PLATFORM_LIMITS

def customer_facing_text(copy: GeneratedCopy) -> str:
    parts = [
        copy.subject,
        copy.headline,
        copy.body,
        copy.call_to_action,
        " ".join(copy.hashtags),
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())

def validate_platform_length(copy: GeneratedCopy) -> GeneratedCopy:
    text = customer_facing_text(copy)
    actual = len(text)
    limit = PLATFORM_LIMITS[copy.platform]
    if actual > limit:
        raise ValueError(
            f"{copy.platform} copy is {actual} characters; limit is {limit}."
        )
    # Normalize the reported count to the application-verified count.
    copy.character_count = actual
    return copy
