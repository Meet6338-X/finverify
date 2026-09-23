"""
Temporal activity definitions for the FinVerify verification pipeline.

Each activity represents a discrete step in the verification workflow,
with proper error handling, DB persistence, and heartbeat support for long-running operations.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
try:
    from temporalio import activity
except ImportError:
    class _MockActivity:
        @staticmethod
        def defn(func=None, **kwargs):
            if func is not None:
                return func
            return lambda f: f
        @staticmethod
        def heartbeat(*args, **kwargs):
            pass
    activity = _MockActivity()

from sqlalchemy import select
from src.parsers.document_parser import DocumentParser
from src.extractor.claim_extractor import ClaimExtractor
from src.ingestion.edgar_client import EdgarClient
from src.reexecutor.engine import SymbolicReExecutor, VerificationStatus
from src.crypto.signer import CertificateSigner, build_certificate_payload
from src.db.connection import get_session_factory
from src.db.models import Report, Claim, Certificate
from src.config import settings

logger = logging.getLogger(__name__)


@activity.defn
async def parse_input_activity(content: str, content_format: str) -> str:
    """Parse raw input content into normalized text."""
    activity.heartbeat("Parsing input document")
    parser = DocumentParser()
    return parser.parse(content, content_format)


@activity.defn
async def extract_claims_activity(
    parsed_text: str,
    filing_cik: str,
    filing_period: str,
    form_type: str,
    report_id: str,
) -> list[dict]:
    """Extract structured claims from parsed text and persist to DB."""
    activity.heartbeat("Extracting claims")
    extractor = ClaimExtractor()
    claims = extractor.extract_claims(parsed_text, filing_cik, filing_period, form_type)

    session_factory = get_session_factory()
    if session_factory:
        try:
            async with session_factory() as db:
                for claim_data in claims:
                    cid = claim_data.get("claim_id", str(uuid.uuid4()))
                    claim_obj = Claim(
                        claim_id=uuid.UUID(cid),
                        report_id=uuid.UUID(report_id) if report_id else None,
                        claim_text=claim_data.get("claim_text", ""),
                        claim_type=claim_data.get("claim_type", "computable"),
                        inputs_json=claim_data.get("inputs", []),
                        operation=claim_data.get("operation"),
                        output_value=claim_data.get("output", {}).get("value") if isinstance(claim_data.get("output"), dict) else claim_data.get("output"),
                        unit=claim_data.get("output", {}).get("unit") if isinstance(claim_data.get("output"), dict) else None,
                        source_refs_json=claim_data.get("source_refs", []),
                    )
                    db.add(claim_obj)
                await db.commit()
        except Exception as e:
            logger.warning(f"Could not persist claims to DB: {e}")

    for claim in claims:
        claim["report_id"] = report_id
    return claims


@activity.defn
async def link_edgar_source_activity(
    claim: dict,
    filing_cik: str,
    filing_period: str,
    form_type: str,
) -> dict:
    """Resolve claim input values against SEC EDGAR XBRL data."""
    activity.heartbeat("Linking EDGAR sources")
    client = EdgarClient(
        user_agent=settings.sec_edgar_user_agent,
        redis_host=settings.redis_host,
        redis_port=settings.redis_port,
    )
    try:
        inputs = claim.get("inputs", [])
        resolved = await client.resolve_claim_sources(
            cik=filing_cik,
            period=filing_period,
            form_type=form_type,
            inputs=inputs,
        )
        claim["inputs"] = resolved
        claim["source_refs"] = [
            inp.get("source_uri")
            for inp in resolved
            if inp.get("source_uri")
        ]
        claim["source_not_found"] = any(
            inp.get("source_not_found", False) for inp in resolved
        )
    except Exception as e:
        logger.error(f"EDGAR source linking failed for claim {claim.get('claim_id')}: {e}")
        claim["source_not_found"] = True
        claim["source_refs"] = []
    finally:
        await client.close()
    return claim


@activity.defn
async def symbolic_reexecute_activity(sourced_claim: dict) -> dict:
    """Deterministically re-execute the claim's computation and compare."""
    activity.heartbeat("Re-executing claim symbolically")
    executor = SymbolicReExecutor()

    claim_id = sourced_claim.get("claim_id", str(uuid.uuid4()))
    operation = sourced_claim.get("operation", "")
    output = sourced_claim.get("output", {})
    expected_value = output.get("value", 0.0) if isinstance(output, dict) else float(output or 0.0)

    # Build inputs dict from the claim's input list
    inputs_list = sourced_claim.get("inputs", [])
    inputs_dict: dict[str, Any] = {}
    for inp in inputs_list:
        name = inp.get("name", "")
        value = inp.get("resolved_value") if inp.get("resolved_value") is not None else inp.get("value")
        if name and value is not None:
            inputs_dict[name] = value

    # If inputs were extracted or resolved, run symbolic re-execution
    result = executor.execute(claim_id, operation, inputs_dict, expected_value)

    # If computation was unverifiable (e.g. missing inputs / unsupported operation), return unverifiable trace
    if result.status.value.lower() == "unverifiable":
        return {
            "claim_id": claim_id,
            "expected_value": expected_value,
            "computed_value": None,
            "relative_error": None,
            "status": "unverifiable",
            "discrepancy_trace": result.discrepancy_trace if result.discrepancy_trace else [{"reason": "source_not_found"}],
        }

    return {
        "claim_id": result.claim_id,
        "expected_value": result.expected_value,
        "computed_value": result.computed_value,
        "relative_error": result.relative_error,
        "status": result.status.value.lower(),
        "discrepancy_trace": result.discrepancy_trace,
    }


@activity.defn
async def sign_certificate_activity(
    claim: dict,
    verification_result: dict,
    report_id: str,
) -> dict:
    """Build, sign, and persist a verification certificate."""
    activity.heartbeat("Signing certificate")
    signer = CertificateSigner(settings.finverify_signing_key_path)

    claim_id_str = verification_result.get("claim_id") or claim.get("claim_id") or str(uuid.uuid4())
    status_str = verification_result.get("status", "unverifiable")

    cert_payload = build_certificate_payload(
        claim_id=claim_id_str,
        status=status_str,
        expected_value=verification_result.get("expected_value"),
        computed_value=verification_result.get("computed_value"),
        relative_error=verification_result.get("relative_error"),
        discrepancy_trace=verification_result.get("discrepancy_trace", []),
        source_refs=claim.get("source_refs", []),
    )

    signature, _ = signer.sign(cert_payload)
    cert_id = str(uuid.uuid4())

    session_factory = get_session_factory()
    if session_factory:
        try:
            async with session_factory() as db:
                cert_obj = Certificate(
                    cert_id=uuid.UUID(cert_id),
                    claim_id=uuid.UUID(claim_id_str) if claim_id_str else None,
                    status=status_str,
                    expected_value=cert_payload.get("expected_value"),
                    computed_value=cert_payload.get("computed_value"),
                    relative_error=cert_payload.get("relative_error"),
                    discrepancy_trace=cert_payload.get("discrepancy_trace"),
                    cert_payload_json=cert_payload,
                    signature=signature,
                    qr_code_url=cert_payload.get("qr_code_url"),
                )
                db.add(cert_obj)
                await db.commit()
        except Exception as e:
            logger.warning(f"Could not persist certificate to DB: {e}")

    certificate = {
        "cert_id": cert_id,
        "claim_id": cert_payload["claim_id"],
        "report_id": report_id,
        "issued_at": cert_payload["timestamp"],
        "status": cert_payload["status"],
        "expected_value": cert_payload["expected_value"],
        "computed_value": cert_payload["computed_value"],
        "relative_error": cert_payload["relative_error"],
        "discrepancy_trace": cert_payload["discrepancy_trace"],
        "source_refs": cert_payload["source_refs"],
        "cert_payload_json": cert_payload,
        "signature": signature.hex(),
        "qr_code_url": cert_payload.get("qr_code_url"),
    }

    return certificate


@activity.defn
async def aggregate_report_activity(
    report_id: str,
    certificates: list[dict],
) -> dict:
    """Aggregate claim-level results into a report-level summary."""
    activity.heartbeat("Aggregating report")

    status_counts = {"pass": 0, "fail": 0, "pass_with_warning": 0, "unverifiable": 0}
    for cert in certificates:
        cert_status = cert.get("status", "unverifiable").lower()
        if cert_status in status_counts:
            status_counts[cert_status] += 1

    total = len(certificates)
    if total == 0:
        overall_status = "unverifiable"
    elif status_counts["fail"] > 0:
        overall_status = "fail"
    elif status_counts["unverifiable"] == total:
        overall_status = "unverifiable"
    elif status_counts["pass_with_warning"] > 0 or status_counts["unverifiable"] > 0:
        overall_status = "partial"
    else:
        overall_status = "pass"

    summary = {
        "report_id": report_id,
        "status": overall_status,
        "total_claims": total,
        "passed": status_counts["pass"],
        "failed": status_counts["fail"],
        "warnings": status_counts["pass_with_warning"],
        "unverifiable": status_counts["unverifiable"],
    }

    # Sign the summary
    signer = CertificateSigner(settings.finverify_signing_key_path)
    signature, _ = signer.sign(summary)
    summary["summary_signature"] = signature.hex()

    session_factory = get_session_factory()
    if session_factory:
        try:
            async with session_factory() as db:
                result = await db.execute(select(Report).where(Report.report_id == uuid.UUID(report_id)))
                rep = result.scalar_one_or_none()
                if rep:
                    rep.status = overall_status
                    rep.summary_cert_json = summary
                    rep.summary_signature = signature
                    await db.commit()
        except Exception as e:
            logger.warning(f"Could not update report summary in DB: {e}")

    return summary


@activity.defn
async def execute_webhook_activity(
    callback_url: str,
    report_summary: dict,
) -> None:
    """POST report summary to the caller's webhook URL."""
    activity.heartbeat("Executing webhook callback")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(callback_url, json=report_summary)
        response.raise_for_status()
        logger.info(f"Webhook callback to {callback_url} succeeded: {response.status_code}")
