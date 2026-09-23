import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import sympy as sp
import numpy as np

class VerificationStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PASS_WITH_WARNING = "PASS_WITH_WARNING"
    UNVERIFIABLE = "UNVERIFIABLE"

@dataclass
class VerificationResult:
    claim_id: str
    expected_value: float
    computed_value: Optional[float]
    relative_error: Optional[float]
    status: VerificationStatus
    discrepancy_trace: List[Dict[str, Any]] = field(default_factory=list)

class SymbolicReExecutor:
    """
    Deterministic symbolic re-execution engine.
    """
    
    def __init__(self):
        self.operations = {
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

    def _require_inputs(self, inputs: Dict[str, Any], required: List[str]):
        for req in required:
            if req not in inputs or inputs[req] is None:
                raise ValueError(f"Missing required input: {req}")

    def _record_step(self, trace: List[Dict[str, Any]], step_name: str, formula: str, computed: Any, source: str = "computation"):
        trace.append({
            "step_name": step_name,
            "formula": formula,
            "computed_value": float(computed) if computed is not None else None,
            "source_reference": source
        })

    def _addition(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["a", "b"])
        val = sp.Rational(str(inputs["a"])) + sp.Rational(str(inputs["b"]))
        self._record_step(trace, "addition", "a + b", val)
        return float(val)

    def _subtraction(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["a", "b"])
        val = sp.Rational(str(inputs["a"])) - sp.Rational(str(inputs["b"]))
        self._record_step(trace, "subtraction", "a - b", val)
        return float(val)

    def _multiplication(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["a", "b"])
        val = sp.Rational(str(inputs["a"])) * sp.Rational(str(inputs["b"]))
        self._record_step(trace, "multiplication", "a * b", val)
        return float(val)

    def _division(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["a", "b"])
        if float(inputs["b"]) == 0:
            raise ZeroDivisionError("Division by zero")
        val = sp.Rational(str(inputs["a"])) / sp.Rational(str(inputs["b"]))
        self._record_step(trace, "division", "a / b", val)
        return float(val)

    def _percentage(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["part", "whole"])
        if float(inputs["whole"]) == 0:
            raise ZeroDivisionError("Division by zero")
        val = (sp.Rational(str(inputs["part"])) / sp.Rational(str(inputs["whole"]))) * 100
        self._record_step(trace, "percentage", "(part / whole) * 100", val)
        return float(val)

    def _gross_margin(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["rev", "cogs"])
        if float(inputs["rev"]) == 0:
            raise ZeroDivisionError("Division by zero")
        rev = sp.Rational(str(inputs["rev"]))
        cogs = sp.Rational(str(inputs["cogs"]))
        val = (rev - cogs) / rev
        self._record_step(trace, "gross_margin", "(rev - cogs) / rev", val)
        return float(val)

    def _operating_margin(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["rev", "cogs", "opex"])
        if float(inputs["rev"]) == 0:
            raise ZeroDivisionError("Division by zero")
        rev = sp.Rational(str(inputs["rev"]))
        cogs = sp.Rational(str(inputs["cogs"]))
        opex = sp.Rational(str(inputs["opex"]))
        val = (rev - cogs - opex) / rev
        self._record_step(trace, "operating_margin", "(rev - cogs - opex) / rev", val)
        return float(val)

    def _net_margin(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["net_income", "rev"])
        if float(inputs["rev"]) == 0:
            raise ZeroDivisionError("Division by zero")
        ni = sp.Rational(str(inputs["net_income"]))
        rev = sp.Rational(str(inputs["rev"]))
        val = ni / rev
        self._record_step(trace, "net_margin", "net_income / rev", val)
        return float(val)

    def _basic_eps(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["net_income", "shares"])
        if float(inputs["shares"]) == 0:
            raise ZeroDivisionError("Division by zero")
        ni = sp.Rational(str(inputs["net_income"]))
        shares = sp.Rational(str(inputs["shares"]))
        val = ni / shares
        self._record_step(trace, "basic_eps", "net_income / shares", val)
        return float(val)

    def _diluted_eps(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["net_income", "diluted_shares"])
        if float(inputs["diluted_shares"]) == 0:
            raise ZeroDivisionError("Division by zero")
        ni = sp.Rational(str(inputs["net_income"]))
        shares = sp.Rational(str(inputs["diluted_shares"]))
        val = ni / shares
        self._record_step(trace, "diluted_eps", "net_income / diluted_shares", val)
        return float(val)

    def _pe_ratio(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["price", "eps"])
        if float(inputs["eps"]) == 0:
            raise ZeroDivisionError("Division by zero")
        price = sp.Rational(str(inputs["price"]))
        eps = sp.Rational(str(inputs["eps"]))
        val = price / eps
        self._record_step(trace, "pe_ratio", "price / eps", val)
        return float(val)

    def _debt_to_equity(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["total_debt", "total_equity"])
        if float(inputs["total_equity"]) == 0:
            raise ZeroDivisionError("Division by zero")
        debt = sp.Rational(str(inputs["total_debt"]))
        equity = sp.Rational(str(inputs["total_equity"]))
        val = debt / equity
        self._record_step(trace, "debt_to_equity", "total_debt / total_equity", val)
        return float(val)

    def _current_ratio(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["current_assets", "current_liabilities"])
        if float(inputs["current_liabilities"]) == 0:
            raise ZeroDivisionError("Division by zero")
        assets = sp.Rational(str(inputs["current_assets"]))
        liabs = sp.Rational(str(inputs["current_liabilities"]))
        val = assets / liabs
        self._record_step(trace, "current_ratio", "current_assets / current_liabilities", val)
        return float(val)

    def _interest_coverage(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["ebit", "interest_expense"])
        if float(inputs["interest_expense"]) == 0:
            raise ZeroDivisionError("Division by zero")
        ebit = sp.Rational(str(inputs["ebit"]))
        interest = sp.Rational(str(inputs["interest_expense"]))
        val = ebit / interest
        self._record_step(trace, "interest_coverage", "ebit / interest_expense", val)
        return float(val)

    def _yoy_change(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["new", "old"])
        if float(inputs["old"]) == 0:
            raise ZeroDivisionError("Division by zero")
        new = sp.Rational(str(inputs["new"]))
        old = sp.Rational(str(inputs["old"]))
        val = (new - old) / old
        self._record_step(trace, "yoy_change", "(new - old) / old", val)
        return float(val)

    def _qoq_change(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["new", "old"])
        if float(inputs["old"]) == 0:
            raise ZeroDivisionError("Division by zero")
        new = sp.Rational(str(inputs["new"]))
        old = sp.Rational(str(inputs["old"]))
        val = (new - old) / old
        self._record_step(trace, "qoq_change", "(new - old) / old", val)
        return float(val)

    def _cagr(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["end", "begin", "n"])
        if float(inputs["begin"]) == 0:
            raise ZeroDivisionError("Division by zero")
        if float(inputs["n"]) == 0:
            raise ZeroDivisionError("Division by zero for n")
        
        end = float(inputs["end"])
        begin = float(inputs["begin"])
        n = float(inputs["n"])
        
        val = (end / begin) ** (1 / n) - 1
        self._record_step(trace, "cagr", "(end / begin)^(1/n) - 1", val)
        return val

    def _segment_sum(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["segments"])
        segments = inputs["segments"]
        total = sp.Rational(0)
        for s in segments:
            total += sp.Rational(str(s))
        self._record_step(trace, "segment_sum", "sum(segments)", total)
        return float(total)

    def _weighted_average(self, inputs: Dict[str, Any], trace: List[Dict[str, Any]]) -> float:
        self._require_inputs(inputs, ["values", "weights"])
        values = inputs["values"]
        weights = inputs["weights"]
        if len(values) != len(weights):
            raise ValueError("values and weights must have same length")
        
        total_weight = sum(sp.Rational(str(w)) for w in weights)
        if total_weight == 0:
            raise ZeroDivisionError("Sum of weights is zero")
            
        weighted_sum = sum(sp.Rational(str(v)) * sp.Rational(str(w)) for v, w in zip(values, weights))
        val = weighted_sum / total_weight
        self._record_step(trace, "weighted_average", "sum(v_i * w_i) / sum(w_i)", val)
        return float(val)

    def execute(self, claim_id: str, operation: str, inputs: Dict[str, Any], expected_value: float) -> VerificationResult:
        trace: List[Dict[str, Any]] = []
        
        if operation not in self.operations:
            return VerificationResult(
                claim_id=claim_id,
                expected_value=expected_value,
                computed_value=None,
                relative_error=None,
                status=VerificationStatus.UNVERIFIABLE,
                discrepancy_trace=[{"reason": "unsupported_operation"}]
            )
            
        try:
            computed_value = self.operations[operation](inputs, trace)
            
            if computed_value == 0 and expected_value != 0:
                relative_error = float("inf")
            elif computed_value == 0 and expected_value == 0:
                relative_error = 0.0
            else:
                relative_error = abs(expected_value - computed_value) / abs(computed_value)
                
            if relative_error <= 0.002:
                status = VerificationStatus.PASS
            elif relative_error <= 0.01:
                status = VerificationStatus.PASS_WITH_WARNING
            else:
                status = VerificationStatus.FAIL
                
            return VerificationResult(
                claim_id=claim_id,
                expected_value=expected_value,
                computed_value=computed_value,
                relative_error=relative_error,
                status=status,
                discrepancy_trace=trace
            )
            
        except ValueError as e:
            if "Missing required input" in str(e):
                return VerificationResult(
                    claim_id=claim_id,
                    expected_value=expected_value,
                    computed_value=None,
                    relative_error=None,
                    status=VerificationStatus.UNVERIFIABLE,
                    discrepancy_trace=[{"reason": "missing_input", "error": str(e)}]
                )
            raise
        except Exception as e:
            return VerificationResult(
                claim_id=claim_id,
                expected_value=expected_value,
                computed_value=None,
                relative_error=None,
                status=VerificationStatus.UNVERIFIABLE,
                discrepancy_trace=[{"reason": "computation_error", "error": str(e)}]
            )
