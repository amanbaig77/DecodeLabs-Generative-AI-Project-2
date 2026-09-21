import asyncio
import time

import pytest

from src.config import Settings
from src.generator import CopyGenerator
from src.models import CopyRequest, GeneratedCopy
from src.prompts import build_master_prompt, PLATFORM_LIMITS
from src.retry import with_retry
from src.validators import validate_platform_length

def request(platform="LinkedIn"):
    return CopyRequest(
        product_name="AeroFlex Shoes",
        description="Lightweight running shoes with breathable mesh and a flexible sole.",
        platform=platform,
        tone="witty",
        temperature=0.8,
        top_p=0.9,
    )

def test_dynamic_prompt_compilation():
    prompt = build_master_prompt(request())
    assert "AeroFlex Shoes" in prompt
    assert "LinkedIn" in prompt
    assert "witty" in prompt
    assert "Temperature: 0.8" in prompt
    assert "Top_P: 0.9" in prompt

def test_platform_limit_is_enforced():
    copy = GeneratedCopy(
        product_name="Test",
        platform="X",
        tone="professional",
        headline="A",
        body="B",
        call_to_action="C",
        hashtags=["#Test"],
        character_count=999,
    )
    assert validate_platform_length(copy).character_count == len("A B C #Test")

def test_over_limit_copy_fails():
    copy = GeneratedCopy(
        product_name="Test",
        platform="X",
        tone="professional",
        headline="x" * 300,
        body="B",
        call_to_action="C",
        hashtags=[],
        character_count=0,
    )
    with pytest.raises(ValueError):
        validate_platform_length(copy)

def test_retry_uses_backoff_and_eventually_succeeds():
    state = {"calls": 0}

    async def flaky():
        state["calls"] += 1
        if state["calls"] < 3:
            raise TimeoutError("temporary")
        return "ok"

    result = asyncio.run(with_retry(flaky, max_retries=3, base_delay=0.001))
    assert result == "ok"
    assert state["calls"] == 3

def test_async_generator_handles_multiple_platforms():
    generator = CopyGenerator(Settings(mock_mode=True, max_concurrent=2))
    results = asyncio.run(generator.generate_many([request("LinkedIn"), request("Instagram")]))
    assert [r.platform for r in results] == ["LinkedIn", "Instagram"]
    assert all(r.character_count <= PLATFORM_LIMITS[r.platform] for r in results)
