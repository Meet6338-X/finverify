from pydantic import BaseModel, HttpUrl, Field, model_validator
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime

class VerifyRequest(BaseModel):
    content: str
    content_format: Literal['text', 'json', 'pdf', 'docx', 'csv']
    llm_model: Optional[str] = None
    filing_cik: str = Field(pattern=r'^\d{10}$')
    filing_period: str = Field(pattern=r'^((Q[1-4]|FY)\d{4}|\d{4}-(Q[1-4]|FY)|\d{4}Q[1-4]|\d{4})$')
    form_type: Literal['10-K', '10-Q', '8-K']
    callback_url: Optional[HttpUrl] = None

class VerifyResponse(BaseModel):
    job_id: str
    report_id: str
    status: str = 'submitted'
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    report_id: str
    status: str
    submitted_at: datetime
    filing_cik: str
    filing_period: str
    form_type: str
    llm_model: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    certificates: List[Dict[str, Any]]

class CertificateResponse(BaseModel):
    cert_id: str
    claim_id: str
    claim_text: Optional[str] = None
    status: str
    expected_value: Optional[float] = None
    computed_value: Optional[float] = None
    relative_error: Optional[float] = None
    discrepancy_trace: Optional[List[Dict[str, Any]]] = None
    source_refs: Optional[List[str]] = None
    issued_at: datetime
    signature: str
    qr_code_url: Optional[str] = None
    cert_payload_json: Optional[Dict[str, Any]] = None
    reviewer_decision: Optional[Dict[str, Any]] = None

class ReviewRequest(BaseModel):
    reviewer_id: str
    decision: Literal['accepted', 'rejected', 'annotated']
    annotation: Optional[str] = None

    @model_validator(mode='after')
    def check_annotation_if_rejected(self):
        if self.decision == 'rejected' and not self.annotation:
            raise ValueError('annotation is required when decision is rejected')
        return self

class ReviewResponse(BaseModel):
    decision_id: str
    cert_id: str
    status: str = 'recorded'

class LedgerResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
