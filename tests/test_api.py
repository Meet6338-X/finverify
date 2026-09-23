"""
Integration and unit tests for FastAPI endpoints.
Tests /health, /api/v1/verify, /api/v1/jobs, /api/v1/reports, /api/v1/certificates, /api/v1/review, /api/v1/ledger, and /api/v1/certificates/{id}/pdf.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from src.api.main import app
from src.api.routes import get_db_session, get_temporal_client
from src.db.models import Report, Claim, Certificate, ReviewerDecision


@pytest.fixture
def mock_temporal_client():
    mock_client = AsyncMock()
    mock_client.start_workflow = AsyncMock(return_value=None)
    
    mock_handle = AsyncMock()
    mock_desc = MagicMock()
    mock_desc.status.name = "RUNNING"
    mock_handle.describe = AsyncMock(return_value=mock_desc)
    mock_handle.query = AsyncMock(return_value={"status": "running", "claims_processed": 1, "total_claims": 2})
    mock_handle.signal = AsyncMock(return_value=None)
    
    mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
    return mock_client


@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    return mock_session


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_verify_endpoint(mock_temporal_client, mock_db_session):
    async def override_get_db():
        yield mock_db_session

    async def override_get_temporal():
        return mock_temporal_client

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_temporal_client] = override_get_temporal

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "content": "Gross margin was 42.3% on revenue of $4.82B and COGS of $2.78B.",
            "content_format": "text",
            "filing_cik": "0000320193",
            "filing_period": "2025-Q4",
            "form_type": "10-K",
            "llm_model": "gpt-4o"
        }
        response = await client.post("/api/v1/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "report_id" in data
        assert mock_db_session.add.called
        assert mock_temporal_client.start_workflow.called

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_job_status(mock_temporal_client):
    async def override_get_temporal():
        return mock_temporal_client

    app.dependency_overrides[get_temporal_client] = override_get_temporal

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/jobs/verify-test-123")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "verify-test-123"
        assert data["status"] == "RUNNING"
        assert data["progress"]["total_claims"] == 2

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_report_endpoint(mock_db_session):
    report_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    cert_id = uuid.uuid4()

    mock_report = Report(
        report_id=report_id,
        filing_cik="0000320193",
        filing_period="2025-Q4",
        form_type="10-K",
        llm_model="gpt-4o",
        status="pass",
        submitted_at=datetime.now(timezone.utc),
        summary_cert_json={"total_claims": 1, "passed": 1}
    )

    mock_cert = Certificate(
        cert_id=cert_id,
        claim_id=claim_id,
        issued_at=datetime.now(timezone.utc),
        status="pass",
        expected_value=42.3,
        computed_value=42.32,
        relative_error=0.00047,
        signature=b"x" * 64
    )
    mock_claim = Claim(
        claim_id=claim_id,
        report_id=report_id,
        claim_text="Gross margin was 42.3%",
        claim_type="computable"
    )

    mock_result_report = MagicMock()
    mock_result_report.scalar_one_or_none.return_value = mock_report

    mock_result_certs = MagicMock()
    mock_result_certs.all.return_value = [(mock_cert, mock_claim)]

    mock_db_session.execute = AsyncMock(side_effect=[mock_result_report, mock_result_certs, MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))))])

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == str(report_id)
        assert data["filing_cik"] == "0000320193"
        assert len(data["certificates"]) == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_certificate_and_pdf_endpoints(mock_db_session):
    cert_id = uuid.uuid4()
    claim_id = uuid.uuid4()

    mock_cert = Certificate(
        cert_id=cert_id,
        claim_id=claim_id,
        issued_at=datetime.now(timezone.utc),
        status="pass",
        expected_value=42.3,
        computed_value=42.32,
        relative_error=0.00047,
        discrepancy_trace=[{"step_name": "gross_margin", "formula": "(rev-cogs)/rev", "computed_value": 0.4232}],
        cert_payload_json={"claim_id": str(claim_id), "status": "pass", "source_refs": ["edgar://..."]},
        signature=b"test-sig-" * 8
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cert
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test JSON certificate retrieval
        response = await client.get(f"/api/v1/certificates/{cert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["cert_id"] == str(cert_id)
        assert data["status"] == "pass"

        # Test PDF certificate retrieval
        pdf_response = await client.get(f"/api/v1/certificates/{cert_id}/pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert pdf_response.content[:4] == b"%PDF"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_review_endpoint(mock_db_session, mock_temporal_client):
    cert_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    report_id = uuid.uuid4()

    mock_cert = Certificate(cert_id=cert_id, claim_id=claim_id)
    mock_claim = Claim(claim_id=claim_id, report_id=report_id)

    mock_res_cert = MagicMock()
    mock_res_cert.scalar_one_or_none.return_value = mock_cert

    mock_res_claim = MagicMock()
    mock_res_claim.scalar_one_or_none.return_value = mock_claim

    mock_db_session.execute = AsyncMock(side_effect=[mock_res_cert, mock_res_claim])

    async def override_get_db():
        yield mock_db_session

    async def override_get_temporal():
        return mock_temporal_client

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_temporal_client] = override_get_temporal

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        review_payload = {
            "reviewer_id": "auditor_01",
            "decision": "rejected",
            "annotation": "Input numbers mismatched footnote disclosure."
        }
        response = await client.post(f"/api/v1/review/{cert_id}", json=review_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["cert_id"] == str(cert_id)
        assert "decision_id" in data
        assert mock_db_session.add.called
        assert mock_temporal_client.get_workflow_handle.called

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ledger_endpoint(mock_db_session):
    cert_id = uuid.uuid4()
    claim_id = uuid.uuid4()

    mock_cert = Certificate(
        cert_id=cert_id,
        claim_id=claim_id,
        issued_at=datetime.now(timezone.utc),
        status="pass",
        expected_value=100.0,
        computed_value=100.0,
        relative_error=0.0
    )
    mock_claim = Claim(
        claim_id=claim_id,
        claim_text="Revenue was $100M"
    )

    mock_count_res = MagicMock()
    mock_count_res.scalar.return_value = 1

    mock_items_res = MagicMock()
    mock_items_res.all.return_value = [(mock_cert, mock_claim)]

    mock_dec_res = MagicMock()
    mock_dec_res.scalars.return_value.first.return_value = None

    mock_db_session.execute = AsyncMock(side_effect=[mock_count_res, mock_items_res, mock_dec_res])

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ledger?page=1&page_size=20&status=pass")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["cert_id"] == str(cert_id)

    app.dependency_overrides.clear()
