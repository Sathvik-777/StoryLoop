"""Run-scoped API usage and cost reporting for StoryLoop."""

from __future__ import annotations

import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


USD_TO_INR = _env_float("STORYLOOP_USD_TO_INR", 96.64)
FX_RATE_DATE = os.getenv("STORYLOOP_FX_RATE_DATE", "2026-10-11")
FX_RATE_SOURCE = os.getenv(
    "STORYLOOP_FX_RATE_SOURCE", "Upstox mid-market USD/INR, 2026-10-11"
)

# USD per million tokens; update these when provider pricing changes.
TOKEN_PRICES = {
    "gpt-5-mini": {"input": 0.25, "cached_input": 0.025, "output": 2.00},
    "gpt-5-mini-2025-08-07": {
        "input": 0.25,
        "cached_input": 0.025,
        "output": 2.00,
    },
    "gpt-4.1-mini": {"input": 0.40, "cached_input": 0.10, "output": 1.60},
    "gpt-4.1-mini-2025-04-14": {
        "input": 0.40,
        "cached_input": 0.10,
        "output": 1.60,
    },
    "gpt-4o-mini-tts": {"input": 0.60, "cached_input": 0.60, "output": 12.00},
    "gpt-4o-mini-tts-2025-03-20": {
        "input": 0.60,
        "cached_input": 0.60,
        "output": 12.00,
    },
    "gpt-4o-mini-tts-2025-12-15": {
        "input": 0.60,
        "cached_input": 0.60,
        "output": 12.00,
    },
}

OPENAI_PRICING_SOURCE = "https://developers.openai.com/api/docs/pricing"


def _value(obj: Any, key: str, default: Any = 0) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _estimated_tokens(text: str) -> int:
    # TTS does not return usage metadata. Four characters/token is an estimate.
    return math.ceil(len(text) / 4) if text else 0


class APICostTracker:
    def __init__(self, report_path: str | Path):
        self.report_path = Path(report_path)
        self.entries: list[dict[str, Any]] = []
        self.write_report()

    def record_openai_response(self, response: Any, requested_model: str) -> None:
        usage = _value(response, "usage", None)
        model = _value(response, "model", requested_model) or requested_model
        if usage is None:
            self.entries.append(
                {
                    "provider": "OpenAI",
                    "endpoint": "responses.create",
                    "model": model,
                    "input_tokens": None,
                    "cached_tokens": 0,
                    "output_tokens": None,
                    "cost_usd": None,
                    "note": "API response did not include usage metadata",
                }
            )
            self.write_report()
            return

        input_tokens = int(_value(usage, "input_tokens", 0) or 0)
        output_tokens = int(_value(usage, "output_tokens", 0) or 0)
        input_details = _value(usage, "input_tokens_details", {}) or {}
        cached_tokens = int(_value(input_details, "cached_tokens", 0) or 0)
        prices = TOKEN_PRICES.get(model)
        cost = None
        if prices is not None:
            regular_input = max(0, input_tokens - cached_tokens)
            cost = (
                regular_input * prices["input"]
                + cached_tokens * prices["cached_input"]
                + output_tokens * prices["output"]
            ) / 1_000_000

        self.entries.append(
            {
                "provider": "OpenAI",
                "endpoint": "responses.create",
                "model": model,
                "input_tokens": input_tokens,
                "cached_tokens": cached_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "note": "Provider usage metadata",
            }
        )
        self.write_report()

    def record_openai_error(self, endpoint: str, model: str) -> None:
        self.entries.append(
            {
                "provider": "OpenAI",
                "endpoint": endpoint,
                "model": model,
                "input_tokens": None,
                "cached_tokens": 0,
                "output_tokens": None,
                "cost_usd": None,
                "note": "Request failed; usage and billed amount unavailable",
            }
        )
        self.write_report()

    def record_speech(self, model: str, text: str) -> None:
        input_tokens = _estimated_tokens(text)
        prices = TOKEN_PRICES.get(model)
        # Audio token count is not returned by audio.speech.create. Keep it
        # unavailable instead of presenting an unsupported audio-cost guess.
        cost = (
            input_tokens * prices["input"] / 1_000_000
            if prices is not None
            else None
        )
        self.entries.append(
            {
                "provider": "OpenAI",
                "endpoint": "audio.speech.create",
                "model": model,
                "input_tokens": input_tokens,
                "cached_tokens": 0,
                "output_tokens": None,
                "cost_usd": cost,
                "note": "Input tokens estimated from text length; audio output usage is not exposed by endpoint",
            }
        )
        self.write_report()

    def record_external_api(
        self,
        provider: str,
        endpoint: str,
        *,
        quota_units: int = 0,
        note: str = "Free API request; no direct USD charge",
    ) -> None:
        self.entries.append(
            {
                "provider": provider,
                "endpoint": endpoint,
                "model": "—",
                "input_tokens": None,
                "cached_tokens": 0,
                "output_tokens": None,
                "quota_units": quota_units,
                "cost_usd": 0.0,
                "note": note,
            }
        )
        self.write_report()

    def write_report(self) -> Path:
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        total_input = sum(row["input_tokens"] or 0 for row in self.entries)
        total_cached = sum(row["cached_tokens"] or 0 for row in self.entries)
        total_output = sum(row["output_tokens"] or 0 for row in self.entries)
        known_cost = sum(
            row["cost_usd"] or 0.0
            for row in self.entries
            if row["cost_usd"] is not None
        )
        unknown_costs = sum(row["cost_usd"] is None for row in self.entries)
        total_quota = sum(row.get("quota_units", 0) for row in self.entries)

        lines = [
            "STORYLOOP API USAGE AND COST REPORT",
            f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
            f"USD to INR rate: 1 USD = ₹{USD_TO_INR:.4f} ({FX_RATE_DATE}; {FX_RATE_SOURCE})",
            f"Pricing reference: {OPENAI_PRICING_SOURCE}",
            "",
            "Requests:",
        ]
        if not self.entries:
            lines.append("  No tracked API requests recorded.")
        for index, row in enumerate(self.entries, start=1):
            cost = (
                f"${row['cost_usd']:.8f} / ₹{row['cost_usd'] * USD_TO_INR:.6f}"
                if row["cost_usd"] is not None
                else "unavailable"
            )
            input_count = "n/a" if row["input_tokens"] is None else str(row["input_tokens"])
            output_count = "n/a" if row["output_tokens"] is None else str(row["output_tokens"])
            cached_count = row.get("cached_tokens", 0)
            quota = row.get("quota_units", 0)
            lines.append(
                f"{index}. {row['provider']} | {row['endpoint']} | {row['model']}"
            )
            lines.append(
                f"   Tokens: input {input_count} (cached {cached_count}), output {output_count}; "
                f"quota units {quota}; cost {cost}"
            )
            lines.append(f"   Note: {row['note']}")

        lines.extend(
            [
                "",
                "TOTALS",
                f"Tracked API requests: {len(self.entries)}",
                f"Input tokens: {total_input} (cached: {total_cached})",
                f"Output tokens: {total_output}",
                f"YouTube quota units tracked: {total_quota}",
                f"Known USD cost: ${known_cost:.8f}",
                f"Known INR cost: ₹{known_cost * USD_TO_INR:.6f}",
                f"Requests with unavailable USD cost: {unknown_costs}",
                "Note: known totals exclude any request whose provider did not expose usage or whose model has no configured rate.",
            ]
        )
        self.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.report_path


_tracker: APICostTracker | None = None


def start_cost_tracking(run_dir: str | Path) -> APICostTracker:
    global _tracker
    _tracker = APICostTracker(Path(run_dir) / "api_cost_report.txt")
    return _tracker


def get_cost_tracker() -> APICostTracker:
    global _tracker
    if _tracker is None:
        root = Path(__file__).resolve().parent.parent
        _tracker = APICostTracker(root / "output" / "current_run" / "api_cost_report.txt")
    return _tracker
