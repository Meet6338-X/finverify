"""
FastAPI API routes for FinVerify.

Implements all REST endpoints for verification job submission, status polling,
certificate retrieval, human review, ledger queries, and PDF generation.
"""
import uuid
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
try:
    from temporalio.client import Client
except ImportError:
    class Client:
        @classmethod
        async def connect(cls, *args, **kwargs):
            raise RuntimeError("Temporal client is not available on host without temporalio package")

from src.api.schemas import (
    VerifyRequest, VerifyResponse, JobStatusResponse,
    ReportResponse, CertificateResponse, ReviewRequest, ReviewResponse,
    LedgerResponse,
)
from src.workflows.verify_workflow import VerifyReportWorkflow, VerifyReportInput
from src.db.connection import get_db_session
from src.db.models import Report, Claim, Certificate, ReviewerDecision
from src.reports.pdf_generator import CertificatePDFGenerator
from src.config import settings

router = APIRouter(prefix="/api/v1")


async def get_temporal_client() -> Client:
    """Create a Temporal client connection."""
    return await Client.connect(
        f"{settings.temporal_host}:{settings.temporal_port}",
        namespace=settings.temporal_namespace,
    )


# ─── GET /public-key ─────────────────────────────────────────────────────────

@router.get("/public-key")
async def get_public_key():
    """Retrieve the Ed25519 public key hex string used for signing certificates."""
    from src.crypto.signer import CertificateSigner
    signer = CertificateSigner(settings.finverify_signing_key_path)
    return {
        "public_key": signer.get_public_key_hex(),
        "algorithm": "Ed25519 (RFC 8032)",
        "canonicalization": "RFC 8785 JSON Canonicalization Scheme (JCS)"
    }


# ─── POST /verify ───────────────────────────────────────────────────────────

@router.post("/verify", response_model=VerifyResponse)
async def verify_report(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db_session),
    temporal: Client = Depends(get_temporal_client),
):
    """Submit LLM-generated financial content for verification."""
    report_id = str(uuid.uuid4())
    job_id = f"verify-{report_id}"

    # Persist the report record
    report = Report(
        report_id=uuid.UUID(report_id),
        llm_model=request.llm_model,
        filing_cik=request.filing_cik,
        filing_period=request.filing_period,
        form_type=request.form_type,
        status="pending",
    )
    db.add(report)
    await db.commit()

    # Start the Temporal workflow (non-blocking)
    input_data = VerifyReportInput(
        content=request.content,
        content_format=request.content_format,
        filing_cik=request.filing_cik,
        filing_period=request.filing_period,
        form_type=request.form_type,
        report_id=report_id,
        llm_model=request.llm_model,
        callback_url=str(request.callback_url) if request.callback_url else None,
    )

    await temporal.start_workflow(
        VerifyReportWorkflow.run,
        input_data,
        id=job_id,
        task_queue=settings.temporal_task_queue,
    )

    return VerifyResponse(
        job_id=job_id,
        report_id=report_id,
        message="Verification job submitted successfully",
    )


# ─── GET /jobs/{job_id} ─────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    temporal: Client = Depends(get_temporal_client),
):
    """Retrieve the status of a verification job."""
    try:
        handle = temporal.get_workflow_handle(job_id)
        desc = await handle.describe()
        try:
            progress = await handle.query(VerifyReportWorkflow.get_progress)
        except Exception:
            progress = None
        return JobStatusResponse(
            job_id=job_id,
            status=desc.status.name,
            progress=progress,
        )
    except Exception:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")


# ─── GET /reports/{report_id} ───────────────────────────────────────────────

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve a report with its claim certificates and human review decisions."""
    result = await db.execute(
        select(Report).where(Report.report_id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Fetch associated certificates via claims
    certs_result = await db.execute(
        select(Certificate, Claim)
        .join(Claim, Certificate.claim_id == Claim.claim_id, isouter=True)
        .where(Claim.report_id == report.report_id)
    )
    cert_pairs = certs_result.all()

    cert_list = []
    for row in cert_pairs:
        try:
            c = row[0]
            cl = row[1] if len(row) > 1 else None
        except Exception:
            c = row
            cl = getattr(row, 'claim', None)

        if not isinstance(c, Certificate):
            c = getattr(row, 'Certificate', c)

        # Check for reviewer decision
        dec = None
        try:
            dec_res = await db.execute(
                select(ReviewerDecision)
                .where(ReviewerDecision.cert_id == c.cert_id)
                .order_by(ReviewerDecision.decided_at.desc())
            )
            dec = dec_res.scalars().first()
        except Exception:
            pass

        effective_status = getattr(c, 'status', 'unverifiable')
        if dec:
            if dec.decision == "accepted":
                effective_status = "pass"
            elif dec.decision == "rejected":
                effective_status = "fail"

        cert_list.append({
            "cert_id": str(c.cert_id),
            "claim_id": str(c.claim_id) if c.claim_id else "",
            "claim_text": getattr(cl, 'claim_text', "") if cl else "",
            "status": effective_status,
            "original_status": getattr(c, 'status', effective_status),
            "expected_value": float(c.expected_value) if getattr(c, 'expected_value', None) is not None else None,
            "computed_value": float(c.computed_value) if getattr(c, 'computed_value', None) is not None else None,
            "relative_error": float(c.relative_error) if getattr(c, 'relative_error', None) is not None else None,
            "discrepancy_trace": getattr(c, 'discrepancy_trace', None),
            "issued_at": c.issued_at.isoformat() if getattr(c, 'issued_at', None) else None,
            "reviewer_decision": {
                "decision": dec.decision,
                "reviewer_id": dec.reviewer_id,
                "annotation": dec.annotation,
                "decided_at": dec.decided_at.isoformat()
            } if dec else None
        })

    return ReportResponse(
        report_id=str(report.report_id),
        status=report.status,
        submitted_at=report.submitted_at,
        filing_cik=report.filing_cik,
        filing_period=report.filing_period,
        form_type=report.form_type,
        llm_model=report.llm_model,
        summary=report.summary_cert_json,
        certificates=cert_list,
    )


# ─── GET /certificates/{cert_id} ────────────────────────────────────────────

@router.get("/certificates/{cert_id}", response_model=CertificateResponse)
async def get_certificate(
    cert_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Retrieve a specific claim verification certificate with review adjudication."""
    result = await db.execute(
        select(Certificate).where(Certificate.cert_id == uuid.UUID(cert_id))
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Check for claim text
    claim_text = ""
    if cert.claim_id:
        try:
            cl_res = await db.execute(select(Claim).where(Claim.claim_id == cert.claim_id))
            cl = cl_res.scalar_one_or_none()
            if cl:
                claim_text = getattr(cl, 'claim_text', "")
        except Exception:
            pass

    # Check for reviewer decision
    dec = None
    try:
        dec_res = await db.execute(
            select(ReviewerDecision)
            .where(ReviewerDecision.cert_id == cert.cert_id)
            .order_by(ReviewerDecision.decided_at.desc())
        )
        dec = dec_res.scalars().first()
    except Exception:
        pass

    effective_status = cert.status
    payload = getattr(cert, 'cert_payload_json', {}) or {}
    effective_sig = cert.signature.hex() if cert.signature else ""

    if dec:
        if dec.decision == "accepted":
            effective_status = "pass"
        elif dec.decision == "rejected":
            effective_status = "fail"

        # Re-sign the updated certificate payload with the adjudication verdict
        try:
            from src.crypto.signer import CertificateSigner
            signer = CertificateSigner(settings.finverify_signing_key_path)
            adjudicated_payload = {
                "claim_id": payload.get("claim_id") or (str(cert.claim_id) if cert.claim_id else ""),
                "status": effective_status,
                "expected_value": float(cert.expected_value) if cert.expected_value is not None else None,
                "computed_value": float(cert.computed_value) if cert.computed_value is not None else None,
                "relative_error": float(cert.relative_error) if cert.relative_error is not None else None,
                "discrepancy_trace": cert.discrepancy_trace or [],
                "source_refs": payload.get("source_refs") or [],
                "timestamp": dec.decided_at.isoformat() if dec.decided_at else (cert.issued_at.isoformat() if cert.issued_at else "")
            }
            sig_bytes, _ = signer.sign(adjudicated_payload)
            payload = adjudicated_payload
            effective_sig = sig_bytes.hex()
        except Exception:
            pass

    return CertificateResponse(
        cert_id=str(cert.cert_id),
        claim_id=str(cert.claim_id) if cert.claim_id else "",
        claim_text=claim_text,
        status=effective_status,
        expected_value=float(cert.expected_value) if cert.expected_value is not None else None,
        computed_value=float(cert.computed_value) if cert.computed_value is not None else None,
        relative_error=float(cert.relative_error) if cert.relative_error is not None else None,
        discrepancy_trace=cert.discrepancy_trace,
        source_refs=payload.get("source_refs"),
        issued_at=cert.issued_at,
        signature=effective_sig,
        qr_code_url=cert.qr_code_url,
        cert_payload_json=payload,
        reviewer_decision={
            "decision": dec.decision,
            "reviewer_id": dec.reviewer_id,
            "annotation": dec.annotation,
            "decided_at": dec.decided_at.isoformat() if dec.decided_at else None
        } if dec else None
    )


# ─── POST /review/{cert_id} ─────────────────────────────────────────────────

@router.post("/review/{cert_id}", response_model=ReviewResponse)
async def review_certificate(
    cert_id: str,
    request: ReviewRequest,
    db: AsyncSession = Depends(get_db_session),
    temporal: Client = Depends(get_temporal_client),
):
    """Submit a human reviewer decision for a certificate."""
    # Verify the certificate exists
    result = await db.execute(
        select(Certificate).where(Certificate.cert_id == uuid.UUID(cert_id))
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    decision_id = str(uuid.uuid4())

    # Cryptographically sign reviewer decision
    decision_signature = b""
    try:
        from src.crypto.signer import CertificateSigner
        signer = CertificateSigner(settings.finverify_signing_key_path)
        dec_payload = {
            "cert_id": str(cert.cert_id),
            "decision_id": decision_id,
            "reviewer_id": request.reviewer_id,
            "decision": request.decision,
            "annotation": request.annotation or "",
        }
        decision_signature, _ = signer.sign(dec_payload)
    except Exception:
        pass

    # Persist the reviewer decision
    decision = ReviewerDecision(
        decision_id=uuid.UUID(decision_id),
        cert_id=cert.cert_id,
        reviewer_id=request.reviewer_id,
        decision=request.decision,
        annotation=request.annotation,
        decision_signature=decision_signature,
    )
    db.add(decision)
    await db.commit()

    # Signal the workflow about the review decision
    try:
        claim_result = await db.execute(
            select(Claim).where(Claim.claim_id == cert.claim_id)
        )
        claim = claim_result.scalar_one_or_none()
        if claim and claim.report_id:
            job_id = f"verify-{claim.report_id}"
            handle = temporal.get_workflow_handle(job_id)
            await handle.signal(
                VerifyReportWorkflow.review_decision,
                {
                    "claim_id": str(cert.claim_id),
                    "decision": request.decision,
                    "annotation": request.annotation,
                },
            )
    except Exception:
        pass

    return ReviewResponse(decision_id=decision_id, cert_id=cert_id, status="recorded")


# ─── GET /ledger ─────────────────────────────────────────────────────────────

@router.get("/ledger", response_model=LedgerResponse)
async def get_ledger(
    status: Optional[str] = Query(None, description="Filter by certificate status"),
    filing_cik: Optional[str] = Query(None, description="Filter by filing CIK"),
    unreviewed_only: Optional[bool] = Query(None, description="Filter only unreviewed queue items"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
):
    """Query the append-only certificate ledger with human adjudication state."""
    query = select(Certificate, Claim).join(Claim, Certificate.claim_id == Claim.claim_id, isouter=True)
    count_query = select(func.count(Certificate.cert_id))

    if filing_cik:
        query = query.join(Report, Claim.report_id == Report.report_id, isouter=True).where(
            Report.filing_cik == filing_cik
        )
        count_query = count_query.join(Claim, Certificate.claim_id == Claim.claim_id, isouter=True).join(
            Report, Claim.report_id == Report.report_id, isouter=True
        ).where(Report.filing_cik == filing_cik)

    if status:
        query = query.where(Certificate.status == status)
        count_query = count_query.where(Certificate.status == status)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Certificate.issued_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for row in rows:
        try:
            c = row[0]
            cl = row[1] if len(row) > 1 else None
        except Exception:
            c = row
            cl = getattr(row, 'claim', None)

        if not isinstance(c, Certificate):
            c = getattr(row, 'Certificate', c)

        # Check for reviewer decision
        dec = None
        try:
            dec_res = await db.execute(
                select(ReviewerDecision)
                .where(ReviewerDecision.cert_id == c.cert_id)
                .order_by(ReviewerDecision.decided_at.desc())
            )
            dec = dec_res.scalars().first()
        except Exception:
            pass

        if unreviewed_only and dec is not None:
            continue

        effective_status = getattr(c, 'status', 'unverifiable')
        if dec:
            if dec.decision == "accepted":
                effective_status = "pass"
            elif dec.decision == "rejected":
                effective_status = "fail"

        items.append({
            "cert_id": str(c.cert_id),
            "claim_id": str(c.claim_id) if c.claim_id else "",
            "claim_text": getattr(cl, 'claim_text', "") if cl else "",
            "status": effective_status,
            "original_status": getattr(c, 'status', effective_status),
            "expected_value": float(c.expected_value) if getattr(c, 'expected_value', None) is not None else None,
            "computed_value": float(c.computed_value) if getattr(c, 'computed_value', None) is not None else None,
            "relative_error": float(c.relative_error) if getattr(c, 'relative_error', None) is not None else None,
            "discrepancy_trace": getattr(c, 'discrepancy_trace', None),
            "source_refs": (getattr(c, 'cert_payload_json', {}) or {}).get("source_refs", []),
            "issued_at": c.issued_at.isoformat() if getattr(c, 'issued_at', None) else None,
            "qr_code_url": getattr(c, 'qr_code_url', None),
            "reviewer_decision": {
                "decision": dec.decision,
                "reviewer_id": dec.reviewer_id,
                "annotation": dec.annotation,
                "decided_at": dec.decided_at.isoformat()
            } if dec else None
        })

    return LedgerResponse(items=items, total=total, page=page, page_size=page_size)


# ─── GET /certificates/{cert_id}/pdf ─────────────────────────────────────────

@router.get("/certificates/{cert_id}/pdf")
async def get_certificate_pdf(
    cert_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate and download a PDF certificate."""
    result = await db.execute(
        select(Certificate).where(Certificate.cert_id == uuid.UUID(cert_id))
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    payload = getattr(cert, 'cert_payload_json', {}) or {}
    payload["cert_id"] = str(cert.cert_id)
    payload["signature"] = cert.signature.hex() if cert.signature else ""

    # Check for reviewer decision
    try:
        dec_res = await db.execute(
            select(ReviewerDecision)
            .where(ReviewerDecision.cert_id == cert.cert_id)
            .order_by(ReviewerDecision.decided_at.desc())
        )
        dec = dec_res.scalars().first()
        if dec:
            if dec.decision == "accepted":
                payload["status"] = "PASS"
            elif dec.decision == "rejected":
                payload["status"] = "FAIL"
    except Exception:
        pass

    generator = CertificatePDFGenerator()
    pdf_bytes = generator.generate_claim_certificate(payload)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=finverify_cert_{cert_id[:8]}.pdf"
        },
    )
