CREATE TABLE reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    llm_model VARCHAR(128),
    filing_cik VARCHAR(16) NOT NULL,
    filing_period VARCHAR(16) NOT NULL,
    form_type VARCHAR(16) NOT NULL DEFAULT '10-K',
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    summary_cert_json JSONB,
    summary_signature BYTEA
);

CREATE TABLE claims (
    claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(report_id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(32) NOT NULL CHECK (claim_type IN ('computable','non-computable')),
    inputs_json JSONB,
    operation VARCHAR(64),
    output_value NUMERIC(20,6),
    unit VARCHAR(64),
    source_refs_json JSONB
);

CREATE TABLE certificates (
    cert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID REFERENCES claims(claim_id),
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(32) NOT NULL CHECK (status IN ('pass','fail','pass_with_warning','unverifiable')),
    expected_value NUMERIC(20,6),
    computed_value NUMERIC(20,6),
    relative_error NUMERIC(10,6),
    discrepancy_trace JSONB,
    cert_payload_json JSONB NOT NULL,
    signature BYTEA NOT NULL,
    qr_code_url VARCHAR(512)
);

CREATE TABLE reviewer_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cert_id UUID REFERENCES certificates(cert_id),
    reviewer_id VARCHAR(128) NOT NULL,
    decision VARCHAR(16) NOT NULL CHECK (decision IN ('accepted','rejected','annotated')),
    annotation TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decision_signature BYTEA
);

CREATE INDEX idx_claims_report_id ON claims(report_id);
CREATE INDEX idx_certificates_claim_id ON certificates(claim_id);
CREATE INDEX idx_reviewer_decisions_cert_id ON reviewer_decisions(cert_id);
CREATE INDEX idx_certificates_status ON certificates(status);
CREATE INDEX idx_reports_filing_cik ON reports(filing_cik);

CREATE RULE no_update_certificates AS ON UPDATE TO certificates DO INSTEAD NOTHING;
CREATE RULE no_delete_certificates AS ON DELETE TO certificates DO INSTEAD NOTHING;

CREATE RULE no_update_reviewer_decisions AS ON UPDATE TO reviewer_decisions DO INSTEAD NOTHING;
CREATE RULE no_delete_reviewer_decisions AS ON DELETE TO reviewer_decisions DO INSTEAD NOTHING;
