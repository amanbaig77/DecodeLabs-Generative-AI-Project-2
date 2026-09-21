from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from .config import Settings
from .models import CopyRequest, GeneratedCopy
from .prompts import build_master_prompt
from .validators import validate_platform_length


# ============================================================
# MOCK RESULT
# ============================================================

def _mock_result(request: CopyRequest) -> GeneratedCopy:
    """
    Offline demo fallback.

    Uses the supplied product description directly and avoids
    inventing product features, prices, certifications,
    statistics, testimonials, or performance claims.
    """

    # Email gets a subject line.
    if request.platform == "Email":
        subject = f"Discover {request.product_name}"
    else:
        subject = ""

    # Platform-specific hashtags.
    if request.platform == "Instagram":
        hashtags = [
            f"#{request.product_name.replace(' ', '')}",
            "#Product",
            "#ShopNow",
        ]

    elif request.platform == "LinkedIn":
        hashtags = [
            f"#{request.product_name.replace(' ', '')}",
            "#Product",
            "#Business",
        ]

    elif request.platform == "X":
        hashtags = [
            f"#{request.product_name.replace(' ', '')}",
            "#Product",
        ]

    else:
        # Email normally does not need hashtags.
        hashtags = []

    result = GeneratedCopy(
        product_name=request.product_name,
        platform=request.platform,
        tone=request.tone,
        subject=subject,
        headline=f"Meet {request.product_name}",
        body=request.description.strip(),
        call_to_action=f"Discover {request.product_name} today.",
        hashtags=hashtags,
        character_count=0,
        compliance_notes=[
            "Offline mock output; no API call was made.",
            "Copy is based only on the supplied product description.",
        ],
    )

    # Verify the final customer-facing character count
    # against the selected platform limit.
    return validate_platform_length(result)


# ============================================================
# SINGLE GEMINI GENERATION
# ============================================================

async def _generate_one(
    request: CopyRequest,
    client: Any,
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> GeneratedCopy:

    async with semaphore:

        # Build the assignment-required dynamic prompt.
        prompt = f"""
{build_master_prompt(request)}

OUTPUT REQUIREMENTS:

Return ONLY one complete JSON object.

Do not use Markdown.
Do not use ```json.
Do not add explanations outside the JSON object.

Required JSON fields:

{{
  "product_name": "{request.product_name}",
  "platform": "{request.platform}",
  "tone": "{request.tone}",
  "subject": "",
  "headline": "",
  "body": "",
  "call_to_action": "",
  "hashtags": [],
  "character_count": 0,
  "compliance_notes": []
}}

IMPORTANT:

- Use only information supported by the raw product description.
- Do not invent prices, discounts, awards, certifications,
  statistics, testimonials, guarantees, or unsupported features.
- For Email, provide a useful subject.
- For LinkedIn and Instagram, hashtags may be included.
- Keep the generated copy concise.
- Stay within the platform character limit.
- character_count must represent the complete customer-facing copy.
- Return valid JSON only.
- Make sure all strings, arrays, and the JSON object are properly closed.
""".strip()

        # Gemini generation configuration.
        config = types.GenerateContentConfig(
            temperature=request.temperature,
            top_p=request.top_p,
            max_output_tokens=4096,
            response_mime_type="application/json",
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            ),
        )

        # google-genai client is synchronous, so run it in a worker thread
        # to keep the async batch pipeline responsive.
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=settings.model,
            contents=prompt,
            config=config,
        )

        raw = response.text

        if not raw:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        raw = raw.strip()

        # --------------------------------------------------------
        # Remove Markdown JSON fences if Gemini adds them.
        # --------------------------------------------------------

        if raw.startswith("```"):

            lines = raw.splitlines()

            # Remove first fence.
            if lines:
                lines = lines[1:]

            # Remove closing fence.
            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            raw = "\n".join(lines).strip()

        # --------------------------------------------------------
        # Parse JSON.
        # --------------------------------------------------------

        try:

            data = json.loads(raw)

        except json.JSONDecodeError:

            # Attempt to recover a JSON object if Gemini
            # accidentally added surrounding text.
            start = raw.find("{")
            end = raw.rfind("}")

            if (
                start == -1
                or end == -1
                or end <= start
            ):
                raise RuntimeError(
                    "Gemini returned invalid JSON:\n"
                    f"{raw}"
                )

            try:

                data = json.loads(
                    raw[start:end + 1]
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    "Gemini returned incomplete JSON:\n"
                    f"{raw}"
                ) from exc

        # --------------------------------------------------------
        # Validate Gemini response with Pydantic.
        # --------------------------------------------------------

        try:

            result = GeneratedCopy.model_validate(
                data
            )

        except Exception as exc:

            raise RuntimeError(
                "Gemini output does not match "
                "GeneratedCopy model.\n\n"
                f"{json.dumps(data, indent=2, ensure_ascii=False)}"
            ) from exc

        # --------------------------------------------------------
        # Never trust the model for identity fields.
        # The application knows the original request.
        # --------------------------------------------------------

        result.product_name = request.product_name
        result.platform = request.platform
        result.tone = request.tone

        # --------------------------------------------------------
        # Validate the final customer-facing copy.
        # This also recalculates character_count.
        # --------------------------------------------------------

        return validate_platform_length(result)


# ============================================================
# GENERATE BATCH
# ============================================================

async def generate_batch(
    requests: list[CopyRequest],
    settings: Settings,
) -> list[GeneratedCopy]:

    # Validate API key/settings unless mock mode is enabled.
    settings.validate()

    # --------------------------------------------------------
    # Offline mock mode
    # --------------------------------------------------------

    if settings.mock_mode:
        return [
            _mock_result(request)
            for request in requests
        ]

    # --------------------------------------------------------
    # Gemini client
    # --------------------------------------------------------

    client = genai.Client(
        api_key=settings.api_key
    )

    # Limit simultaneous Gemini requests.
    semaphore = asyncio.Semaphore(
        settings.max_concurrent
    )

    # Create asynchronous generation tasks.
    tasks = [
        _generate_one(
            request,
            client,
            settings,
            semaphore,
        )
        for request in requests
    ]

    # Run all requests concurrently.
    return await asyncio.gather(*tasks)


# ============================================================
# CREATE BATCH
#
# Kept for compatibility with existing cli.py.
# ============================================================

async def create_batch(
    requests: list[CopyRequest],
    settings: Settings,
) -> list[GeneratedCopy]:

    return await generate_batch(
        requests,
        settings,
    )


# ============================================================
# DOWNLOAD BATCH OUTPUT
#
# Writes generated results to a JSON file.
# ============================================================

def download_batch_output(
    results: list[GeneratedCopy],
    output_path: str = "batch_output.json",
) -> str:

    path = Path(output_path)

    output: list[dict[str, Any]] = []

    for result in results:

        if hasattr(result, "model_dump"):

            output.append(
                result.model_dump()
            )

        else:

            output.append(result)

    path.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return str(path)


# ============================================================
# LOAD REQUESTS FROM JSON
# ============================================================

def load_requests(
    path: str,
) -> list[CopyRequest]:

    file_path = Path(path)

    if not file_path.exists():

        raise FileNotFoundError(
            f"Input file not found: {path}"
        )

    try:

        data = json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            f"Invalid JSON in batch input: {path}"
        ) from exc

    if not isinstance(data, list):

        raise ValueError(
            "Batch input must be a JSON array."
        )

    return [
        CopyRequest.model_validate(item)
        for item in data
    ]