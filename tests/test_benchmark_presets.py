from src.extractor.claim_extractor import ClaimExtractor
from src.reexecutor.engine import SymbolicReExecutor

def test_benchmark_presets():
    ex = ClaimExtractor()
    eng = SymbolicReExecutor()

    # 1. Apple Gross Margin Pass
    apple_text = "In fiscal 2025, Apple reported gross margin of 42.32% based on total net revenues of $4.82B and cost of goods sold of $2.78B."
    claims = ex.extract_claims(apple_text, '0000320193', '2025-Q4', '10-K')
    assert len(claims) == 1
    c = claims[0]
    inputs_dict = {i['name']: i['value'] for i in c['inputs']}
    assert inputs_dict['rev'] == 4820000000.0
    assert inputs_dict['cogs'] == 2780000000.0
    res = eng.execute(c['claim_id'], c['operation'], inputs_dict, c['output']['value'])
    assert res.status.value == "PASS"

    # 2. Tesla Operating Margin Fail
    tesla_text = "Operating margin expanded significantly to 21.0% in 2024 based on total revenues of $96.77B, cost of revenues of $79.11B, and operating expenses of $8.77B."
    claims = ex.extract_claims(tesla_text, '0001318605', '2024-Q4', '10-K')
    assert len(claims) == 1
    c = claims[0]
    inputs_dict = {i['name']: i['value'] for i in c['inputs']}
    assert inputs_dict['rev'] == 96770000000.0
    assert inputs_dict['cogs'] == 79110000000.0
    assert inputs_dict['opex'] == 8770000000.0
    res = eng.execute(c['claim_id'], c['operation'], inputs_dict, c['output']['value'])
    assert res.status.value == "FAIL"

    # 3. Microsoft Diluted EPS Pass
    msft_text = "Diluted earnings per share reached $3.23 in Q1 based on net income of $24.10B and 7.46B diluted shares."
    claims = ex.extract_claims(msft_text, '0000789019', '2025-Q1', '10-Q')
    assert len(claims) == 1
    c = claims[0]
    inputs_dict = {i['name']: i['value'] for i in c['inputs']}
    assert inputs_dict['net_income'] == 24100000000.0
    assert inputs_dict['diluted_shares'] == 7460000000.0
    res = eng.execute(c['claim_id'], c['operation'], inputs_dict, c['output']['value'])
    assert res.status.value == "PASS"

    # 4. Alphabet Net Margin Pass
    goog_text = "Alphabet achieved a net margin of 27.70% with net income reaching $88.2B on total revenues of $318.4B in FY2024."
    claims = ex.extract_claims(goog_text, '0001652044', '2024-FY', '10-K')
    assert len(claims) == 1
    c = claims[0]
    inputs_dict = {i['name']: i['value'] for i in c['inputs']}
    assert inputs_dict['net_income'] == 88200000000.0
    assert inputs_dict['rev'] == 318400000000.0
    res = eng.execute(c['claim_id'], c['operation'], inputs_dict, c['output']['value'])
    assert res.status.value == "PASS"

    # 5. Footnote Unverifiable (Routed to Review Queue)
    footnote_text = "Adjusted EBITDA reached $14.5B with estimated synthetic synergies of $2.3B across undisclosed business lines."
    claims = ex.extract_claims(footnote_text, '0000320193', '2025-Q4', '10-K')
    assert len(claims) == 1
    c = claims[0]
    assert c['claim_type'] == "non-computable"
