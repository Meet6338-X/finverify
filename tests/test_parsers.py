"""
Unit tests for document parsing and claim extraction.
"""
import pytest
from src.parsers.document_parser import DocumentParser, DocumentParsingError
from src.extractor.claim_extractor import ClaimExtractor


class TestDocumentParser:
    def test_parse_text(self):
        parser = DocumentParser()
        text = "Gross margin improved to 42.3% in Q4 2025."
        result = parser.parse(text, "text")
        assert result == text

    def test_parse_json(self):
        parser = DocumentParser()
        json_str = '{"commentary": "Revenue was $4.82B and net income was $1.2B."}'
        result = parser.parse(json_str, "json")
        assert "$4.82B" in result

    def test_parse_csv(self):
        parser = DocumentParser()
        csv_str = "Metric,Q4_2025,Q4_2024\nRevenue,4820,4300\nCOGS,2780,2600"
        result = parser.parse(csv_str, "csv")
        assert "Revenue" in result
        assert "4820" in result

    def test_text_length_limit(self):
        parser = DocumentParser()
        huge_text = "A" * 100001
        with pytest.raises(DocumentParsingError):
            parser.parse(huge_text, "text")


class TestClaimExtractor:
    def test_extract_claims_from_financial_text(self):
        extractor = ClaimExtractor()
        text = "Gross margin improved to 42.3% in Q4 2025, driven by revenue of $4.82B and cost of goods sold of $2.78B."
        claims = extractor.extract_claims(
            text=text,
            filing_cik="0000320193",
            filing_period="2025-Q4",
            form_type="10-K",
        )
        assert len(claims) >= 1
        claim = claims[0]
        assert "claim_id" in claim
        assert "claim_text" in claim
        assert "inputs" in claim
        assert "output" in claim

    def test_number_parsing(self):
        extractor = ClaimExtractor()
        assert extractor._parse_number("$4.82B") == 4820000000.0
        assert extractor._parse_number("$12.5M") == 12500000.0
        assert extractor._parse_number("42.3%") == 0.423
        assert extractor._parse_number("1,234.56") == 1234.56
