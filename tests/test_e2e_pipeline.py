"""
End-to-end pipeline verification test.
Tests the full verification flow:
Document parsing -> Claim extraction -> Symbolic Re-execution -> Ed25519 Signing -> Report Summary Aggregation -> PDF Certificate Rendering.
"""
import uuid
import pytest
from src.parsers.document_parser import DocumentParser
from src.extractor.claim_extractor import ClaimExtractor
from src.reexecutor.engine import SymbolicReExecutor, VerificationStatus
from src.crypto.signer import CertificateSigner, build_certificate_payload
from src.reports.pdf_generator import CertificatePDFGenerator


def test_end_to_end_verification_flow():
    # 1. Input LLM financial commentary
    raw_document = (
        "In Q4 2025, company revenue grew to $4.82B while cost of goods sold was $2.78B. "
        "Consequently, gross margin improved to 42.32%."
    )
    filing_cik = "0000320193"
    filing_period = "2025-Q4"
    form_type = "10-K"
    report_id = str(uuid.uuid4())

    # 2. Parse Document
    parser = DocumentParser()
    parsed_text = parser.parse(raw_document, "text")
    assert "42.32%" in parsed_text

    # 3. Extract Claims
    extractor = ClaimExtractor()
    claims = extractor.extract_claims(parsed_text, filing_cik, filing_period, form_type)
    assert len(claims) >= 1

    claim = claims[0]
    assert "claim_id" in claim

    # 4. Symbolic Re-Execution
    reexecutor = SymbolicReExecutor()
    # Provide inputs for gross margin: rev = 4820000000, cogs = 2780000000
    inputs = {"rev": 4820000000, "cogs": 2780000000}
    expected_value = 0.423236  # ~42.3236%

    res = reexecutor.execute(claim["claim_id"], "gross_margin", inputs, expected_value)
    assert res.status in (VerificationStatus.PASS, VerificationStatus.PASS_WITH_WARNING)
    assert res.computed_value is not None
    assert len(res.discrepancy_trace) > 0

    # 5. Build and Sign Certificate
    signer = CertificateSigner()
    cert_payload = build_certificate_payload(
        claim_id=claim["claim_id"],
        status=res.status.value.lower(),
        expected_value=res.expected_value,
        computed_value=res.computed_value,
        relative_error=res.relative_error,
        discrepancy_trace=res.discrepancy_trace,
        source_refs=[f"edgar://CIK{filing_cik}/{form_type}/{filing_period}#us-gaap:Revenues"],
    )

    signature, canonical_bytes = signer.sign(cert_payload)
    assert len(signature) == 64
    assert signer.verify(cert_payload, signature) is True

    # 6. Generate Single Claim PDF Certificate
    pdf_gen = CertificatePDFGenerator()
    cert_payload["signature"] = signature.hex()
    pdf_bytes = pdf_gen.generate_claim_certificate(cert_payload)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b"%PDF"

    # 7. Aggregate Report & Generate Report Summary PDF
    certificates = [cert_payload]
    report_dict = {
        "report_id": report_id,
        "title": "Apple Inc. Q4 2025 Verification Audit",
        "filing_cik": filing_cik,
        "filing_period": filing_period,
    }
    summary_pdf = pdf_gen.generate_report_summary(report_dict, certificates)
    assert len(summary_pdf) > 0
    assert summary_pdf[:4] == b"%PDF"
