"""Thin-slice demo: planner Muse Spark (via OpenAI-compatible) + gate local."""
from __future__ import annotations
import os
import sys
from verify import verify_draft


def main(prompt: str) -> int:
    draft = {
        "prompt": prompt,
        "amounts": [{"cents": 245000000, "tool_call_id": "call_demo_1", "concept": "servicio"}],
        "dian_schema_ok": True,
    }
    ok, msg = verify_draft(draft)
    print(f"veredicto: {msg}")
    print(f"transmit: {'SI' if ok else 'NO'} (META_MODEL_API={'configurada' if os.getenv('META_MODEL_API_KEY') else 'mock local'})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(" ".join(sys.argv[1:]) or "factura demo"))
