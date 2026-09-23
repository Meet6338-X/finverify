"""
SQLAlchemy 2.0 models for FinVerify Database Schema.
"""
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (
    String, Text, Numeric, LargeBinary, ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, TIMESTAMP

class Base(DeclarativeBase):
    pass

class Report(Base):
    __tablename__ = 'reports'

    report_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid4)
    submitted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    llm_model: Mapped[Optional[str]] = mapped_column(String(128))
    filing_cik: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    filing_period: Mapped[str] = mapped_column(String(16), nullable=False)
    form_type: Mapped[str] = mapped_column(String(16), nullable=False, server_default='10-K')
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default='pending')
    summary_cert_json: Mapped[Optional[Any]] = mapped_column(JSONB)
    summary_signature: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="report", cascade="all, delete-orphan")

class Claim(Base):
    __tablename__ = 'claims'

    claim_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid4)
    report_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('reports.report_id', ondelete="CASCADE"), index=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(32), nullable=False)
    inputs_json: Mapped[Optional[Any]] = mapped_column(JSONB)
    operation: Mapped[Optional[str]] = mapped_column(String(64))
    output_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    unit: Mapped[Optional[str]] = mapped_column(String(64))
    source_refs_json: Mapped[Optional[Any]] = mapped_column(JSONB)

    report: Mapped[Optional["Report"]] = relationship("Report", back_populates="claims")
    certificates: Mapped[List["Certificate"]] = relationship("Certificate", back_populates="claim")

    __table_args__ = (
        CheckConstraint("claim_type IN ('computable', 'non-computable')", name="check_claim_type"),
    )

class Certificate(Base):
    __tablename__ = 'certificates'

    cert_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid4)
    claim_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('claims.claim_id'), index=True)
    issued_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    expected_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    computed_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 6))
    relative_error: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    discrepancy_trace: Mapped[Optional[Any]] = mapped_column(JSONB)
    cert_payload_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    signature: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    qr_code_url: Mapped[Optional[str]] = mapped_column(String(512))

    claim: Mapped[Optional["Claim"]] = relationship("Claim", back_populates="certificates")
    reviewer_decisions: Mapped[List["ReviewerDecision"]] = relationship("ReviewerDecision", back_populates="certificate")

    __table_args__ = (
        CheckConstraint("status IN ('pass', 'fail', 'pass_with_warning', 'unverifiable')", name="check_status"),
    )

class ReviewerDecision(Base):
    __tablename__ = 'reviewer_decisions'

    decision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid4)
    cert_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('certificates.cert_id'), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    annotation: Mapped[Optional[str]] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    decision_signature: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    certificate: Mapped[Optional["Certificate"]] = relationship("Certificate", back_populates="reviewer_decisions")

    __table_args__ = (
        CheckConstraint("decision IN ('accepted', 'rejected', 'annotated')", name="check_decision"),
    )
