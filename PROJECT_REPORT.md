# DecodeLabs Generative AI — Project 2 Submission Report

## Project
Automated Copywriting & Tone Transformer

## Objective
Build a Python application that converts raw product descriptions into platform-specific marketing copy using dynamic prompt variables, tone controls, and inference parameters.

## Implemented
- Product name, platform and tone variables compiled into a master f-string prompt.
- Temperature and Top_P controls.
- Pydantic request/output models and JSON-schema validation.
- Platform-specific length validation.
- Async real-time generation with asyncio.gather and an asyncio.Semaphore.
- Exponential backoff with randomized jitter for transient failures.
- OpenAI Batch API JSONL pipeline for bulk requests.
- Argparse command-line interface.
- Offline mock mode for demonstration without API credits.

## Verification
- 5/5 automated tests passed.
- Offline CLI demo successfully generated LinkedIn and Instagram outputs.

## Run
```bash
python -m src.cli --mock --product-name "AeroFlex Shoes" --description "Lightweight running shoes with breathable mesh and a flexible sole." --platform LinkedIn --platform Instagram --tone witty
```

For live generation, configure OPENAI_API_KEY in `.env`.
