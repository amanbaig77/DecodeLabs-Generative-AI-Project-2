from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .batch import create_batch, download_batch_output
from .config import Settings
from .generator import CopyGenerator
from .models import CopyRequest

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DecodeLabs Project 2 — Automated Copywriting & Tone Transformer"
    )
    parser.add_argument("--product-name")
    parser.add_argument("--description")
    parser.add_argument(
        "--platform",
        action="append",
        choices=["LinkedIn", "Instagram", "Email", "X"],
        help="Repeat this option to target multiple platforms.",
    )
    parser.add_argument("--tone", default="professional")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--mode", choices=["realtime", "batch"], default="realtime")
    parser.add_argument("--batch-file", help="JSON file containing batch request objects.")
    parser.add_argument("--batch-output", help="Output path for a completed batch.")
    parser.add_argument("--batch-id", help="Existing batch ID to download.")
    parser.add_argument("--mock", action="store_true", help="Run without an API call.")
    return parser

def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    if args.mock:
        settings = Settings(mock_mode=True)

    if args.mode == "batch" and args.batch_id:
        destination = args.batch_output or "outputs/batch_output.jsonl"
        path = download_batch_output(args.batch_id, settings, destination)
        print(f"Batch output saved to: {path}")
        return

    if args.mode == "batch":
        if not args.batch_file:
            raise SystemExit("--batch-file is required for --mode batch.")
        payload = json.loads(Path(args.batch_file).read_text(encoding="utf-8"))
        requests = [CopyRequest(**item) for item in payload]
        batch_id = create_batch(requests, settings)
        print(f"Batch created successfully: {batch_id}")
        print("Monitor the batch until it reaches completed status, then use --batch-id.")
        return

    if not args.product_name or not args.description or not args.platform:
        raise SystemExit(
            "--product-name, --description, and at least one --platform are required."
        )

    temperature = settings.temperature if args.temperature is None else args.temperature
    top_p = settings.top_p if args.top_p is None else args.top_p

    requests = [
        CopyRequest(
            product_name=args.product_name,
            description=args.description,
            platform=platform,
            tone=args.tone,
            temperature=temperature,
            top_p=top_p,
        )
        for platform in args.platform
    ]

    generator = CopyGenerator(settings)
    results = asyncio.run(generator.generate_many(requests))

    for result in results:
        print("\n" + "=" * 72)
        print(result.platform.upper())
        print("=" * 72)
        if result.subject:
            print(f"Subject: {result.subject}")
        print(f"Headline: {result.headline}")
        print(f"\n{result.body}")
        print(f"\nCTA: {result.call_to_action}")
        if result.hashtags:
            print("Hashtags:", " ".join(result.hashtags))
        print(f"\nCharacter count: {result.character_count}")
        if result.compliance_notes:
            print("Notes:", "; ".join(result.compliance_notes))

if __name__ == "__main__":
    main()
