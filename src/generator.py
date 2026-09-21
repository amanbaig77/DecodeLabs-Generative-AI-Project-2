from __future__ import annotations

import asyncio
import json
from typing import Any, Iterable

from .config import Settings
from .models import CopyRequest, GeneratedCopy
from .prompts import build_master_prompt
from .retry import with_retry
from .validators import validate_platform_length

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class CopyGenerator:
    """
    Automated Copywriting & Tone Transformer.

    Supports:
    - Gemini generation
    - Offline mock mode
    - Temperature
    - Top-P
    - Platform character validation
    - Retry handling
    - Batch generation
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Any = None

        if not settings.mock_mode:

            if genai is None:
                raise RuntimeError(
                    "google-genai is not installed. "
                    "Run: pip install google-genai"
                )

            settings.validate()

            self.client = genai.Client(
                api_key=settings.api_key
            )

    # ============================================================
    # SINGLE GENERATION
    # ============================================================

    async def generate(
        self,
        request: CopyRequest,
    ) -> GeneratedCopy:

        # --------------------------------------------------------
        # MOCK MODE
        # --------------------------------------------------------

        if self.settings.mock_mode:
            return self._mock(request)

        # --------------------------------------------------------
        # REAL GEMINI MODE
        # --------------------------------------------------------

        async def operation() -> GeneratedCopy:
            return await self._generate_with_gemini(request)

        result = await with_retry(
            operation,
            max_retries=self.settings.max_retries,
        )

        return validate_platform_length(result)

    # ============================================================
    # GEMINI GENERATION
    # ============================================================

    async def _generate_with_gemini(
        self,
        request: CopyRequest,
    ) -> GeneratedCopy:

        prompt = self._build_generation_prompt(request)

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

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.settings.model,
            contents=prompt,
            config=config,
        )

        raw = response.text

        if not raw:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        data = self._parse_json_response(raw)

        # --------------------------------------------------------
        # Pydantic validation
        # --------------------------------------------------------

        try:

            result = GeneratedCopy.model_validate(
                data
            )

        except Exception as exc:

            raise RuntimeError(
                "Gemini output does not match "
                "the GeneratedCopy model.\n\n"
                f"{json.dumps(data, indent=2, ensure_ascii=False)}"
            ) from exc

        # --------------------------------------------------------
        # Application-controlled fields
        #
        # Never trust the model to return these correctly.
        # The original request is authoritative.
        # --------------------------------------------------------

        result.product_name = request.product_name
        result.platform = request.platform
        result.tone = request.tone

        return validate_platform_length(result)

    # ============================================================
    # GENERATION PROMPT
    # ============================================================

    def _build_generation_prompt(
        self,
        request: CopyRequest,
    ) -> str:

        master_prompt = build_master_prompt(request)

        return f"""
{master_prompt}

OUTPUT FORMAT

Return ONLY one valid JSON object.

Do not use Markdown.
Do not use ```json.
Do not add explanations before or after the JSON.

Required fields:

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

IMPORTANT CONTENT RULES

1. Use only information supported by the raw product description.

2. Do NOT invent:
   - prices
   - discounts
   - awards
   - certifications
   - statistics
   - testimonials
   - guarantees
   - clinical claims
   - unsupported product features
   - unsupported performance claims

3. Transform the description into polished marketing copy.

4. Match the requested tone:
   {request.tone}

5. Match the requested platform:
   {request.platform}

6. For Email:
   - provide a useful subject line
   - subject should be concise
   - hashtags are normally unnecessary

7. For Instagram:
   - concise and engaging
   - hashtags are allowed

8. For LinkedIn:
   - professional and useful
   - hashtags are allowed

9. Do not exceed the platform character limit.

10. character_count must represent the final
    customer-facing content.

11. Return valid JSON only.

12. Properly close every string, array and JSON object.
""".strip()

    # ============================================================
    # JSON PARSER
    # ============================================================

    @staticmethod
    def _parse_json_response(
        raw: str,
    ) -> dict[str, Any]:

        raw = raw.strip()

        # --------------------------------------------------------
        # Remove Markdown code fences if returned by the model.
        # --------------------------------------------------------

        if raw.startswith("```"):

            lines = raw.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            raw = "\n".join(lines).strip()

        # --------------------------------------------------------
        # Normal JSON parse
        # --------------------------------------------------------

        try:

            data = json.loads(raw)

        except json.JSONDecodeError:

            # ----------------------------------------------------
            # Recovery: locate the first { and last }
            # ----------------------------------------------------

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

        if not isinstance(data, dict):

            raise RuntimeError(
                "Gemini response must be a JSON object."
            )

        return data

    # ============================================================
    # BATCH GENERATION
    # ============================================================

    async def generate_many(
        self,
        requests: Iterable[CopyRequest],
    ) -> list[GeneratedCopy]:

        request_list = list(requests)

        if not request_list:
            return []

        # --------------------------------------------------------
        # Mock mode
        # --------------------------------------------------------

        if self.settings.mock_mode:

            return [
                self._mock(request)
                for request in request_list
            ]

        # --------------------------------------------------------
        # Concurrent real generation
        # --------------------------------------------------------

        semaphore = asyncio.Semaphore(
            self.settings.max_concurrent
        )

        async def generate_limited(
            request: CopyRequest,
        ) -> GeneratedCopy:

            async with semaphore:

                return await self.generate(
                    request
                )

        tasks = [
            generate_limited(request)
            for request in request_list
        ]

        return await asyncio.gather(*tasks)

    # ============================================================
    # MOCK GENERATION
    # ============================================================

    def _mock(
        self,
        request: CopyRequest,
    ) -> GeneratedCopy:
        """
        Offline fallback used when MOCK_MODE=1.

        Important:
        The mock does not invent product features or claims.
        It uses the supplied description directly.
        """

        product_name = request.product_name.strip()
        description = request.description.strip()

        # --------------------------------------------------------
        # Subject
        # --------------------------------------------------------

        if request.platform == "Email":

            subject = (
                f"Discover {product_name}"
            )

        else:

            subject = ""

        # --------------------------------------------------------
        # Platform-specific hashtags
        # --------------------------------------------------------

        clean_product_name = (
            product_name
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

        if request.platform == "Instagram":

            hashtags = [
                f"#{clean_product_name}",
                "#Product",
                "#ShopNow",
            ]

        elif request.platform == "LinkedIn":

            hashtags = [
                f"#{clean_product_name}",
                "#Product",
                "#Business",
            ]

        elif request.platform == "X":

            hashtags = [
                f"#{clean_product_name}",
                "#Product",
            ]

        else:

            # Email
            hashtags = []

        # --------------------------------------------------------
        # Create result
        # --------------------------------------------------------

        result = GeneratedCopy(
            product_name=product_name,
            platform=request.platform,
            tone=request.tone,
            subject=subject,
            headline=f"Meet {product_name}",
            body=description,
            call_to_action=(
                f"Discover {product_name} today."
            ),
            hashtags=hashtags,
            character_count=0,
            compliance_notes=[
                "Offline mock output; no API call was made.",
                "Copy is based only on the supplied product description.",
            ],
        )

        # --------------------------------------------------------
        # Validate platform limit and calculate exact count.
        # --------------------------------------------------------

        return validate_platform_length(result)