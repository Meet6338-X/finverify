"""
Unit tests for PDF certificate generation.
"""
from src.reports.pdf_generator import CertificatePDFGenerator


def test_generate_claim_certificate():
    generator = CertificatePDFGenerator()
    certificate = {
        "claim_id": "c_9f21a3",
        "status": "PASS",
        "expected_value": 42.3,
        "computed_value": 42.32,
        "relative_error": 0.00047,
        "discrepancy_trace": [
            {"step_name": "gross_margin", "formula": "(rev-cogs)/rev", "computed_value": 0.4232, "source_reference": "us-gaap:Revenues"}
        ],
        "source_refs": ["edgar://CIK0000320193/10-K/2025Q4#us-gaap:Revenues"],
        "timestamp": "2026-08-19T10:14:02Z",
        "signature": "5f3ab21c" * 8,
    }

    pdf_bytes = generator.generate_claim_certificate(certificate)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF magic bytes
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_report_summary():
    generator = CertificatePDFGenerator()
    report = {"title": "Apple Inc. Q4 2025 Financial Audit Summary"}
    certificates = [
        {"claim_id": "c_1", "status": "PASS", "expected_value": 100, "computed_value": 100},
        {"claim_id": "c_2", "status": "FAIL", "expected_value": 50, "computed_value": 40},
        {"claim_id": "c_3", "status": "UNVERIFIABLE", "expected_value": 20, "computed_value": None},
    ]

    pdf_bytes = generator.generate_report_summary(report, certificates)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b"%PDF"
