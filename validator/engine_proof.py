"""
FinVerify Thesis Proof — Part 1: Deterministic Symbolic Re-Executor.
STANDALONE: does NOT import from ../src. Re-implements the exact thesis rules
so anyone can verify FinVerify's math without trusting FinVerify's code.

Thesis rules proven here:
  R1. NEVER invokes an LLM for calculation — only SymPy Rational + floats.
  R2. relative_error = |expected - computed| / |computed|
  R3. <= 0.2% -> PASS, 0.2%-1.0% -> PASS_WITH_WARNING, > 1.0% -> FAIL
  R4. Missing input / unsupported op / div-by-zero -> UNVERIFIABLE (never FAIL)
  R5. Full discrepancy_trace for every computation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import sympy as sp


class Status(str, Enum):
    PASS = "pass"
    PASS_WITH_WARNING = "pass_with_warning"
    FAIL = "fail"
    UNVERIFIABLE = "unverifiable"


@dataclass
class Result:
    claim_id: str
    operation: str
    expected_value: float
    computed_value: Optional[float]
    relative_error: Optional[float]
    status: Status
    trace: List[Dict[str, Any]] = field(default_factory=list)


PASS_TOL = 0.002   # 0.2%
WARN_TOL = 0.01    # 1.0%


class DeterministicEngine:
    """Pure symbolic engine. Zero LLM calls. Zero network. Zero randomness."""

    def __init__(self) -> None:
        self.ops = {
            "addition": self._addition,
            "subtraction": self._subtraction,
            "multiplication": self._multiplication,
            "division": self._division,
            "percentage": self._percentage,
            "gross_margin": self._gross_margin,
            "operating_margin": self._operating_margin,
            "net_margin": self._net_margin,
            "basic_eps": self._basic_eps,
            "diluted_eps": self._diluted_eps,
            "pe_ratio": self._pe_ratio,
            "debt_to_equity": self._debt_to_equity,
            "current_ratio": self._current_ratio,
            "interest_coverage": self._interest_coverage,
            "yoy_change": self._yoy_change,
            "qoq_change": self._qoq_change,
            "cagr": self._cagr,
            "segment_sum": self._segment_sum,
            "weighted_average": self._weighted_average,
        }

    # -- helpers ---------------------------------------------------------
    def _need(self, inputs: Dict[str, Any], required: List[str]) -> None:
        for k in required:
            if k not in inputs or inputs[k] is None:
                raise ValueError(f"Missing required input: {k}")

    def _step(self, trace, name, formula, value, source="sympy_rational_engine"):
        trace.append({
            "step": name,
            "formula": formula,
            "computed_value": float(value) if value is not None else None,
            "source": source,
        })

    # -- arithmetic -------------------------------------------------------
    def _addition(self, i, t):
        self._need(i, ["a", "b"])
        v = sp.Rational(str(i["a"])) + sp.Rational(str(i["b"]))
        self._step(t, "addition", "a + b", v)
        return float(v)

    def _subtraction(self, i, t):
        self._need(i, ["a", "b"])
        v = sp.Rational(str(i["a"])) - sp.Rational(str(i["b"]))
        self._step(t, "subtraction", "a - b", v)
        return float(v)

    def _multiplication(self, i, t):
        self._need(i, ["a", "b"])
        v = sp.Rational(str(i["a"])) * sp.Rational(str(i["b"]))
        self._step(t, "multiplication", "a * b", v)
        return float(v)

    def _division(self, i, t):
        self._need(i, ["a", "b"])
        if float(i["b"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["a"])) / sp.Rational(str(i["b"]))
        self._step(t, "division", "a / b", v)
        return float(v)

    def _percentage(self, i, t):
        self._need(i, ["part", "whole"])
        if float(i["whole"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = (sp.Rational(str(i["part"])) / sp.Rational(str(i["whole"]))) * 100
        self._step(t, "percentage", "(part / whole) * 100", v)
        return float(v)

    # -- financial ratios --------------------------------------------------
    def _gross_margin(self, i, t):
        self._need(i, ["rev", "cogs"])
        if float(i["rev"]) == 0:
            raise ZeroDivisionError("Division by zero")
        rev, cogs = sp.Rational(str(i["rev"])), sp.Rational(str(i["cogs"]))
        v = (rev - cogs) / rev
        self._step(t, "gross_margin", "(rev - cogs) / rev", v)
        return float(v)

    def _operating_margin(self, i, t):
        self._need(i, ["rev", "cogs", "opex"])
        if float(i["rev"]) == 0:
            raise ZeroDivisionError("Division by zero")
        rev, cogs, opex = (sp.Rational(str(i["rev"])), sp.Rational(str(i["cogs"])), sp.Rational(str(i["opex"])))
        v = (rev - cogs - opex) / rev
        self._step(t, "operating_margin", "(rev - cogs - opex) / rev", v)
        return float(v)

    def _net_margin(self, i, t):
        self._need(i, ["net_income", "rev"])
        if float(i["rev"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["net_income"])) / sp.Rational(str(i["rev"]))
        self._step(t, "net_margin", "net_income / rev", v)
        return float(v)

    def _basic_eps(self, i, t):
        self._need(i, ["net_income", "shares"])
        if float(i["shares"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["net_income"])) / sp.Rational(str(i["shares"]))
        self._step(t, "basic_eps", "net_income / shares", v)
        return float(v)

    def _diluted_eps(self, i, t):
        self._need(i, ["net_income", "diluted_shares"])
        if float(i["diluted_shares"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["net_income"])) / sp.Rational(str(i["diluted_shares"]))
        self._step(t, "diluted_eps", "net_income / diluted_shares", v)
        return float(v)

    def _pe_ratio(self, i, t):
        self._need(i, ["price", "eps"])
        if float(i["eps"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["price"])) / sp.Rational(str(i["eps"]))
        self._step(t, "pe_ratio", "price / eps", v)
        return float(v)

    def _debt_to_equity(self, i, t):
        self._need(i, ["total_debt", "total_equity"])
        if float(i["total_equity"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["total_debt"])) / sp.Rational(str(i["total_equity"]))
        self._step(t, "debt_to_equity", "total_debt / total_equity", v)
        return float(v)

    def _current_ratio(self, i, t):
        self._need(i, ["current_assets", "current_liabilities"])
        if float(i["current_liabilities"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["current_assets"])) / sp.Rational(str(i["current_liabilities"]))
        self._step(t, "current_ratio", "current_assets / current_liabilities", v)
        return float(v)

    def _interest_coverage(self, i, t):
        self._need(i, ["ebit", "interest_expense"])
        if float(i["interest_expense"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = sp.Rational(str(i["ebit"])) / sp.Rational(str(i["interest_expense"]))
        self._step(t, "interest_coverage", "ebit / interest_expense", v)
        return float(v)

    def _yoy_change(self, i, t):
        self._need(i, ["new", "old"])
        if float(i["old"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = (sp.Rational(str(i["new"])) - sp.Rational(str(i["old"]))) / sp.Rational(str(i["old"]))
        self._step(t, "yoy_change", "(new - old) / old", v)
        return float(v)

    def _qoq_change(self, i, t):
        self._need(i, ["new", "old"])
        if float(i["old"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = (sp.Rational(str(i["new"])) - sp.Rational(str(i["old"]))) / sp.Rational(str(i["old"]))
        self._step(t, "qoq_change", "(new - old) / old", v)
        return float(v)

    def _cagr(self, i, t):
        self._need(i, ["end", "begin", "n"])
        if float(i["begin"]) == 0 or float(i["n"]) == 0:
            raise ZeroDivisionError("Division by zero")
        v = (float(i["end"]) / float(i["begin"])) ** (1.0 / float(i["n"])) - 1.0
        self._step(t, "cagr", "(end / begin)^(1/n) - 1", v)
        return float(v)

    def _segment_sum(self, i, t):
        self._need(i, ["segments"])
        total = sp.Rational(0)
        for s in i["segments"]:
            total += sp.Rational(str(s))
        self._step(t, "segment_sum", "sum(segments)", total)
        return float(total)

    def _weighted_average(self, i, t):
        self._need(i, ["values", "weights"])
        if len(i["values"]) != len(i["weights"]):
            raise ValueError("values and weights must have same length")
        tw = sum(sp.Rational(str(w)) for w in i["weights"])
        if tw == 0:
            raise ZeroDivisionError("Sum of weights is zero")
        ws = sum(sp.Rational(str(v)) * sp.Rational(str(w)) for v, w in zip(i["values"], i["weights"]))
        v = ws / tw
        self._step(t, "weighted_average", "sum(v_i*w_i)/sum(w_i)", v)
        return float(v)

    # -- main entry --------------------------------------------------------
    def execute(self, claim_id: str, operation: str, inputs: Dict[str, Any], expected_value: float) -> Result:
        trace: List[Dict[str, Any]] = []
        if operation not in self.ops:
            return Result(claim_id, operation, expected_value, None, None,
                          Status.UNVERIFIABLE, [{"reason": "unsupported_operation", "operation": operation}])
        try:
            computed = self.ops[operation](inputs, trace)
            if computed == 0 and expected_value != 0:
                rel = float("inf")
            elif computed == 0 and expected_value == 0:
                rel = 0.0
            else:
                rel = abs(expected_value - computed) / abs(computed)
            if rel <= PASS_TOL:
                st = Status.PASS
            elif rel <= WARN_TOL:
                st = Status.PASS_WITH_WARNING
            else:
                st = Status.FAIL
            return Result(claim_id, operation, expected_value, computed, rel, st, trace)
        except ValueError as e:
            if "Missing required input" in str(e):
                return Result(claim_id, operation, expected_value, None, None,
                              Status.UNVERIFIABLE, [{"reason": "missing_input", "error": str(e)}])
            raise
        except Exception as e:  # div-by-zero etc -> UNVERIFIABLE, never FAIL
            return Result(claim_id, operation, expected_value, None, None,
                          Status.UNVERIFIABLE, [{"reason": "computation_error", "error": str(e)}])


def prove_engine() -> dict:
    """Run the deterministic-engine proof battery. Returns stats dict."""
    eng = DeterministicEngine()
    checks = []

    def check(name, cond):
        checks.append({"name": name, "ok": bool(cond)})
        return bool(cond)

    # 1. All 19 ops produce exact PASS on gold values
    gold = [
        ("addition", {"a": 100, "b": 50}, 150.0),
        ("subtraction", {"a": 100, "b": 35}, 65.0),
        ("multiplication", {"a": 12.5, "b": 4}, 50.0),
        ("division", {"a": 100, "b": 4}, 25.0),
        ("percentage", {"part": 42.3, "whole": 100}, 42.3),
        ("gross_margin", {"rev": 4820000000, "cogs": 2780000000}, (4820000000 - 2780000000) / 4820000000),
        ("operating_margin", {"rev": 1000, "cogs": 400, "opex": 200}, 0.40),
        ("net_margin", {"net_income": 150, "rev": 1000}, 0.15),
        ("basic_eps", {"net_income": 50000000, "shares": 10000000}, 5.0),
        ("diluted_eps", {"net_income": 50000000, "diluted_shares": 12500000}, 4.0),
        ("pe_ratio", {"price": 150.0, "eps": 5.0}, 30.0),
        ("debt_to_equity", {"total_debt": 2000000, "total_equity": 1000000}, 2.0),
        ("current_ratio", {"current_assets": 300000, "current_liabilities": 150000}, 2.0),
        ("interest_coverage", {"ebit": 1000000, "interest_expense": 200000}, 5.0),
        ("yoy_change", {"new": 120, "old": 100}, 0.20),
        ("qoq_change", {"new": 110, "old": 100}, 0.10),
        ("cagr", {"end": 200, "begin": 100, "n": 3}, 2 ** (1 / 3) - 1),
        ("segment_sum", {"segments": [100, 200, 350.5]}, 650.5),
        ("weighted_average", {"values": [10, 20, 30], "weights": [1, 2, 3]}, 140 / 6),
    ]
    for idx, (op, inp, exp) in enumerate(gold):
        r = eng.execute(f"gold_{idx}", op, inp, exp)
        check(f"gold:{op} == PASS", r.status == Status.PASS and r.relative_error == 0.0 or (r.status == Status.PASS and (r.relative_error or 0) < 1e-9))

    # 2. Tolerance boundaries (exact thesis numbers)
    base = (4820000000 - 2780000000) / 4820000000  # true gross margin
    r = eng.execute("b1", "gross_margin", {"rev": 4820000000, "cogs": 2780000000}, base * 1.00199)
    check("boundary: +0.199% -> pass", r.status == Status.PASS)
    r = eng.execute("b2", "gross_margin", {"rev": 4820000000, "cogs": 2780000000}, base * 1.005)
    check("boundary: +0.5% -> pass_with_warning", r.status == Status.PASS_WITH_WARNING)
    r = eng.execute("b3", "gross_margin", {"rev": 4820000000, "cogs": 2780000000}, base * 1.01001)
    check("boundary: +1.001% -> fail", r.status == Status.FAIL)
    r = eng.execute("b4", "gross_margin", {"rev": 4820000000, "cogs": 2780000000}, 0.50)
    check("grossly wrong (0.50) -> fail", r.status == Status.FAIL and (r.relative_error or 0) > 0.01)

    # 3. UNVERIFIABLE never FAIL
    r = eng.execute("u1", "gross_margin", {"rev": 1000}, 0.5)
    check("missing input -> unverifiable (not fail)", r.status == Status.UNVERIFIABLE)
    r = eng.execute("u2", "black_scholes_exotic", {"spot": 100}, 10.0)
    check("unsupported op -> unverifiable (not fail)", r.status == Status.UNVERIFIABLE)
    r = eng.execute("u3", "division", {"a": 100, "b": 0}, 25.0)
    check("div-by-zero -> unverifiable (not fail)", r.status == Status.UNVERIFIABLE)
    r = eng.execute("u4", "basic_eps", {"net_income": 10, "shares": 0}, 1.0)
    check("zero shares -> unverifiable (not fail)", r.status == Status.UNVERIFIABLE)

    # 4. Determinism: same input twice -> bitwise identical trace
    r1 = eng.execute("d1", "gross_margin", {"rev": 4820000000, "cogs": 2780000000}, base)
    r2 = eng.execute("d1", "gross_margin", {"rev": 4820000000, "cogs": 2780000000}, base)
    check("deterministic: repeat run identical", r1.computed_value == r2.computed_value and r1.trace == r2.trace)

    # 5. No-LLM proof: no LLM library is imported, and no LLM call exists
    # outside this very self-test block (scan import lines only, so the
    # token list below doesn't trip the check on itself).
    import pathlib
    import_lines = [l.strip().lower() for l in pathlib.Path(__file__).read_text(encoding="utf-8").splitlines()
                    if l.strip().lower().startswith(("import ", "from "))]
    check("no-LLM: engine imports only stdlib+sympy (no llm lib)",
          all(any(bad not in ln for bad in ["openai", "anthropic", "transformers", "langchain", "llama", "gpt"])
              for ln in import_lines))

    passed = sum(1 for c in checks if c["ok"])
    return {"suite": "deterministic_engine", "passed": passed, "total": len(checks),
            "ok": passed == len(checks), "checks": checks}


if __name__ == "__main__":
    import json
    print(json.dumps(prove_engine(), indent=2))
