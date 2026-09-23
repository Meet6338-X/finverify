"""
Unit tests for the Deterministic Symbolic Re-Executor engine.
"""
import pytest
from src.reexecutor.engine import SymbolicReExecutor, VerificationStatus, VerificationResult


@pytest.fixture
def executor():
    return SymbolicReExecutor()


class TestArithmeticOperations:
    def test_addition(self, executor):
        res = executor.execute("claim_1", "addition", {"a": 100, "b": 50}, 150.0)
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 150.0
        assert res.relative_error == 0.0
        assert len(res.discrepancy_trace) == 1

    def test_subtraction(self, executor):
        res = executor.execute("claim_2", "subtraction", {"a": 100, "b": 35}, 65.0)
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 65.0

    def test_multiplication(self, executor):
        res = executor.execute("claim_3", "multiplication", {"a": 12.5, "b": 4}, 50.0)
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 50.0

    def test_division(self, executor):
        res = executor.execute("claim_4", "division", {"a": 100, "b": 4}, 25.0)
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 25.0

    def test_division_by_zero(self, executor):
        res = executor.execute("claim_5", "division", {"a": 100, "b": 0}, 25.0)
        assert res.status == VerificationStatus.UNVERIFIABLE
        assert res.computed_value is None


class TestFinancialRatios:
    def test_gross_margin_pass(self, executor):
        # rev: 4820, cogs: 2780 -> gross margin = (4820 - 2780)/4820 = 2040/4820 ≈ 0.4232365
        res = executor.execute(
            "gm_1",
            "gross_margin",
            {"rev": 4820000000, "cogs": 2780000000},
            0.423236,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value is not None

    def test_gross_margin_warning(self, executor):
        # expected is off by ~0.5% (between 0.2% and 1.0%)
        res = executor.execute(
            "gm_2",
            "gross_margin",
            {"rev": 4820000000, "cogs": 2780000000},
            0.4253,
        )
        assert res.status == VerificationStatus.PASS_WITH_WARNING
        assert 0.002 <= res.relative_error <= 0.01

    def test_gross_margin_fail(self, executor):
        # expected is off by > 1%
        res = executor.execute(
            "gm_3",
            "gross_margin",
            {"rev": 4820000000, "cogs": 2780000000},
            0.5000,
        )
        assert res.status == VerificationStatus.FAIL
        assert res.relative_error > 0.01

    def test_operating_margin(self, executor):
        res = executor.execute(
            "om_1",
            "operating_margin",
            {"rev": 1000, "cogs": 400, "opex": 200},
            0.40,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 0.40

    def test_net_margin(self, executor):
        res = executor.execute(
            "nm_1",
            "net_margin",
            {"net_income": 150, "rev": 1000},
            0.15,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 0.15

    def test_basic_eps(self, executor):
        res = executor.execute(
            "eps_1",
            "basic_eps",
            {"net_income": 50000000, "shares": 10000000},
            5.0,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 5.0

    def test_diluted_eps(self, executor):
        res = executor.execute(
            "eps_2",
            "diluted_eps",
            {"net_income": 50000000, "diluted_shares": 12500000},
            4.0,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 4.0

    def test_pe_ratio(self, executor):
        res = executor.execute(
            "pe_1",
            "pe_ratio",
            {"price": 150.0, "eps": 5.0},
            30.0,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 30.0

    def test_debt_to_equity(self, executor):
        res = executor.execute(
            "de_1",
            "debt_to_equity",
            {"total_debt": 2000000, "total_equity": 1000000},
            2.0,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 2.0

    def test_current_ratio(self, executor):
        res = executor.execute(
            "cr_1",
            "current_ratio",
            {"current_assets": 300000, "current_liabilities": 150000},
            2.0,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 2.0

    def test_interest_coverage(self, executor):
        res = executor.execute(
            "ic_1",
            "interest_coverage",
            {"ebit": 1000000, "interest_expense": 200000},
            5.0,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 5.0


class TestPeriodAndAggregations:
    def test_yoy_change(self, executor):
        res = executor.execute(
            "yoy_1",
            "yoy_change",
            {"new": 120, "old": 100},
            0.20,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 0.20

    def test_cagr(self, executor):
        # 100 to 200 in 3 years -> 2^(1/3) - 1 ≈ 0.259921
        res = executor.execute(
            "cagr_1",
            "cagr",
            {"end": 200, "begin": 100, "n": 3},
            0.259921,
        )
        assert res.status == VerificationStatus.PASS

    def test_segment_sum(self, executor):
        res = executor.execute(
            "seg_1",
            "segment_sum",
            {"segments": [100, 200, 350.5]},
            650.5,
        )
        assert res.status == VerificationStatus.PASS
        assert res.computed_value == 650.5

    def test_weighted_average(self, executor):
        res = executor.execute(
            "wa_1",
            "weighted_average",
            {"values": [10, 20, 30], "weights": [1, 2, 3]},
            23.333333,
        )
        assert res.status == VerificationStatus.PASS


class TestEdgeCasesAndUnverifiables:
    def test_unsupported_operation(self, executor):
        res = executor.execute(
            "unsupp_1",
            "black_scholes_exotic",
            {"spot": 100},
            10.0,
        )
        assert res.status == VerificationStatus.UNVERIFIABLE
        assert res.discrepancy_trace[0]["reason"] == "unsupported_operation"

    def test_missing_input(self, executor):
        res = executor.execute(
            "miss_1",
            "gross_margin",
            {"rev": 1000},  # missing cogs
            0.5,
        )
        assert res.status == VerificationStatus.UNVERIFIABLE
        assert res.discrepancy_trace[0]["reason"] == "missing_input"
