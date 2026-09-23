import asyncio
import uuid
from datetime import timedelta
from dataclasses import dataclass
from typing import Optional
try:
    from temporalio import workflow
    from temporalio.common import RetryPolicy

    # Use with_activities imports
    with workflow.unsafe.imports_passed_through():
        from src.workflows.activities import (
            parse_input_activity,
            extract_claims_activity,
            link_edgar_source_activity,
            symbolic_reexecute_activity,
            sign_certificate_activity,
            aggregate_report_activity,
            execute_webhook_activity,
        )
except ImportError:
    class _MockWorkflow:
        @staticmethod
        def defn(cls=None, **kwargs):
            if cls is not None:
                return cls
            return lambda c: c
        @staticmethod
        def run(func):
            return func
        @staticmethod
        def signal(func):
            return func
        @staticmethod
        def query(func):
            return func
        @staticmethod
        async def execute_activity(*args, **kwargs):
            pass
    class RetryPolicy:
        def __init__(self, *args, **kwargs):
            pass
    workflow = _MockWorkflow()
    from src.workflows.activities import (
        parse_input_activity,
        extract_claims_activity,
        link_edgar_source_activity,
        symbolic_reexecute_activity,
        sign_certificate_activity,
        aggregate_report_activity,
        execute_webhook_activity,
    )

@dataclass
class VerifyReportInput:
    content: str
    content_format: str
    filing_cik: str
    filing_period: str
    form_type: str
    report_id: str
    llm_model: Optional[str] = None
    callback_url: Optional[str] = None

@dataclass
class VerifyReportOutput:
    report_id: str
    status: str
    total_claims: int
    passed: int
    failed: int
    warnings: int
    unverifiable: int

@workflow.defn
class VerifyReportWorkflow:
    def __init__(self):
        self._progress = {"status": "started", "claims_processed": 0, "total_claims": 0}
        self._pending_decisions = {}
        self._unverifiable_events = asyncio.Queue()

    @workflow.run
    async def run(self, input: VerifyReportInput) -> VerifyReportOutput:
        retry_policy = RetryPolicy(maximum_attempts=3, backoff_coefficient=2.0)
        
        parsed_text = await workflow.execute_activity(
            parse_input_activity,
            args=[input.content, input.content_format],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        claims = await workflow.execute_activity(
            extract_claims_activity,
            args=[parsed_text, input.filing_cik, input.filing_period, input.form_type, input.report_id],
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=retry_policy,
        )

        self._progress["total_claims"] = len(claims)

        async def process_claim(claim):
            claim_id = claim.get("claim_id") or claim.get("id") or str(uuid.uuid4())
            sourced_claim = await workflow.execute_activity(
                link_edgar_source_activity,
                args=[claim, input.filing_cik, input.filing_period, input.form_type],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=retry_policy,
            )
            
            verification_result = await workflow.execute_activity(
                symbolic_reexecute_activity,
                args=[sourced_claim],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            )
            
            if claim_id in self._pending_decisions:
                verification_result['review_decision'] = self._pending_decisions.pop(claim_id)
            
            cert = await workflow.execute_activity(
                sign_certificate_activity,
                args=[claim, verification_result, input.report_id],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            )
            
            self._progress["claims_processed"] += 1
            return cert

        certificates = await asyncio.gather(*(process_claim(claim) for claim in claims))
        
        report_summary = await workflow.execute_activity(
            aggregate_report_activity,
            args=[input.report_id, certificates],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )
        
        if input.callback_url:
            await workflow.execute_activity(
                execute_webhook_activity,
                args=[input.callback_url, report_summary],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            )
            
        self._progress["status"] = "completed"
        
        return VerifyReportOutput(
            report_id=input.report_id,
            status=report_summary.get("status", "completed"),
            total_claims=report_summary.get("total_claims", len(certificates)),
            passed=report_summary.get("passed", 0),
            failed=report_summary.get("failed", 0),
            warnings=report_summary.get("warnings", 0),
            unverifiable=report_summary.get("unverifiable", 0)
        )

    async def wait_for_decision(self, claim_id: str):
        while claim_id not in self._pending_decisions:
            await self._unverifiable_events.get()
        return self._pending_decisions.pop(claim_id)

    @workflow.signal
    def review_decision(self, decision: dict):
        claim_id = decision.get("claim_id")
        if claim_id:
            self._pending_decisions[claim_id] = decision
            self._unverifiable_events.put_nowait(True)

    @workflow.query
    def get_progress(self) -> dict:
        return self._progress
