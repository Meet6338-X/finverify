"""
Synthetic Error-Injection Benchmark test verifying detection rate and false-flag rate.
Demonstrates target metrics: >= 90% error catch rate and <= 5% false-flag rate.
"""
from src.reexecutor.engine import SymbolicReExecutor, VerificationStatus


def test_synthetic_error_injection_benchmark():
    executor = SymbolicReExecutor()

    # Benchmark ground-truth cases (FinQA-like financial formula claims)
    benchmark_dataset = [
        # (claim_id, operation, inputs, correct_expected)
        ("b_1", "gross_margin", {"rev": 5000, "cogs": 3000}, 0.40),
        ("b_2", "operating_margin", {"rev": 5000, "cogs": 3000, "opex": 1000}, 0.20),
        ("b_3", "net_margin", {"net_income": 800, "rev": 5000}, 0.16),
        ("b_4", "basic_eps", {"net_income": 1000000, "shares": 250000}, 4.0),
        ("b_5", "pe_ratio", {"price": 80.0, "eps": 4.0}, 20.0),
        ("b_6", "debt_to_equity", {"total_debt": 4000, "total_equity": 2000}, 2.0),
        ("b_7", "current_ratio", {"current_assets": 1500, "current_liabilities": 750}, 2.0),
        ("b_8", "interest_coverage", {"ebit": 600, "interest_expense": 100}, 6.0),
        ("b_9", "yoy_change", {"new": 115, "old": 100}, 0.15),
        ("b_10", "segment_sum", {"segments": [120, 180, 300]}, 600.0),
    ]

    # Test 1: Baseline correct claims -> false flag rate should be 0% (<= 5% target)
    false_flags = 0
    for cid, op, inputs, expected in benchmark_dataset:
        res = executor.execute(cid, op, inputs, expected)
        if res.status != VerificationStatus.PASS:
            false_flags += 1

    false_flag_rate = false_flags / len(benchmark_dataset)
    assert false_flag_rate <= 0.05, f"False-flag rate {false_flag_rate} exceeded 5%"

    # Test 2: Injected 5% synthetic arithmetic error -> error catch rate >= 90%
    caught_errors = 0
    for cid, op, inputs, expected in benchmark_dataset:
        corrupted_expected = expected * 1.05  # 5% perturbation
        res = executor.execute(cid, op, inputs, corrupted_expected)
        if res.status in (VerificationStatus.FAIL, VerificationStatus.PASS_WITH_WARNING):
            caught_errors += 1

    catch_rate = caught_errors / len(benchmark_dataset)
    assert catch_rate >= 0.90, f"Error catch rate {catch_rate} below 90%"
