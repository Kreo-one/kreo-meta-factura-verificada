"""Kreo Fiscal Shield deterministic gate: blocks numbers without tool-result.

Numeric rules modeled on DIAN (Colombia) electronic invoicing: int cents,
zero floats, schema validated before transmit."""
from __future__ import annotations


def verify_draft(draft: dict) -> tuple[bool, str]:
    amounts = draft.get("amounts", [])
    for item in amounts:
        if not item.get("tool_call_id"):
            return False, f"bloqueado: cifra sin tool_call_id en {item!r}"
        cents = item.get("cents")
        if not isinstance(cents, int):
            return False, f"bloqueado: cents debe ser int, llego {cents!r}"
    if not draft.get("dian_schema_ok"):
        return False, "bloqueado: schema DIAN no validado antes de transmitir"
    return True, "PASS"


if __name__ == "__main__":
    ok, msg = verify_draft({"amounts": [{"cents": 245000000, "tool_call_id": "call_demo_1"}], "dian_schema_ok": True})
    print(ok, msg)
    bad, msg2 = verify_draft({"amounts": [{"cents": 245000000}], "dian_schema_ok": True})
    print(bad, msg2)
    assert ok and not bad
    print("gate OK")
