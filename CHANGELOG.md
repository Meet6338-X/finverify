# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Note on versioning.** FinVerify is released under a proprietary license.
> Minor and patch releases may contain breaking changes to internal APIs, the
> DSL operation set, or certificate payload schemas. Certificate consumers
> should pin the major version and verify payload shapes before deploying an
> upgrade.

---

## [Unreleased]

### Added
- Nothing yet — open a pull request.

---

## [1.0.0] — 2026-09-23

The first complete, end-to-end release: a full verification stack, a reviewer
dashboard, an independent proof pack, and the project governance files.

### Added

#### Verification core
- **Deterministic symbolic re-executor** (`src/reexecutor/engine.py`) with 19
  operations — `addition`, `subtraction`, `multiplication`, `division`,
  `percentage`, `gross_margin`, `operating_margin`, `net_margin`, `basic_eps`,
  `diluted_eps`, `pe_ratio`, `debt_to_equity`, `current_ratio`,
  `interest_coverage`, `yoy_change`, `qoq_change`, `cagr`, `segment_sum`,
  `weighted_average` — computed with exact `sympy.Rational` arithmetic.
- **Tiered tolerance model**: `≤ 0.2% → pass`, `0.2%–1.0% → pass_with_warning`,
  `> 1.0% → fail`. Unresolvable input, unsupported operation, and division by
  zero resolve to `unverifiable` — never `fail`.
- **Step-level discrepancy traces** recording every intermediate formula,
  computed value, and source reference.
- **Claim extraction** (`src/extractor/claim_extractor.py`) with a structured
  JSON fast path and a regex/heuristic fallback. Parses `$4.82B`,
  `4.82 billion`, `42.3%`, and `1,234.56`; classifies claims as computable or
  non-computable; infers the likely operation.

#### Source linking
- **SEC EDGAR Company Facts client** (`src/ingestion/edgar_client.py`) with a
  10 req/s token-bucket rate limiter, a 24-hour Redis cache, and `us-gaap:*`
  XBRL tag mapping emitting `edgar://CIK…#us-gaap:Tag` source references.
- `source_not_found` flagging when a claim cannot be linked to a filing cell.

#### Cryptography & ledger
- **Ed25519 (RFC 8032) certificate signing** (`src/crypto/signer.py`) over
  canonical JSON — sorted keys, no insignificant whitespace, UTF-8.
- **Append-only ledger** (`src/db/init.sql`) — `certificates` and
  `reviewer_decisions` are `INSERT`-only, enforced by database rules.
- **QR code generation** embedded in certificate payloads.
- **Deterministic key derivation** from `JWT_SECRET` so every container shares
  one keypair; explicit key-file loading takes precedence.

#### Pipeline & orchestration
- **Multi-format document parsing** (`src/parsers/document_parser.py`) — text,
  JSON, PDF, DOCX, and CSV, with a 100,000-character ceiling and CIK/period
  format validation.
- **Temporal workflow orchestration** (`src/workflows/`) — a durable,
  resumable six-stage verification workflow with parallel source linking,
  re-execution, and signing activities; retry policies, timeouts, and
  heartbeats; and a human-review signal channel.

#### API
- **FastAPI service** (`src/api/`) with `/api/v1` routes:
  `GET /public-key`, `POST /verify`, `GET /jobs/{job_id}`,
  `GET /reports/{report_id}`, `GET /certificates/{cert_id}`,
  `POST /review/{cert_id}`, `GET /ledger`, and
  `GET /certificates/{cert_id}/pdf` — plus `GET /health`.
- Interactive OpenAPI documentation at `/docs`.
- Filterable, paginated ledger queries by status, filing CIK, and
  unreviewed-only.
- Certificate re-signing on human adjudication.

#### Reports
- **PDF claim certificates and report summaries** (`src/reports/pdf_generator.py`)
  via ReportLab — status badge, details table, computation-trace table, source
  references, signature preview, and embedded QR code.

#### Reviewer dashboard
- **React 18 + Vite 5 + TailwindCSS 3** single-page application with six
  surfaces: Dashboard, New Audit, Report Detail, Review Queue, Certificate
  Detail, Benchmark Studio, and a Tamper Verifier.
- **Offline client-side Ed25519 verification** in the browser via `tweetnacl`
  — no network call, no backend trust.
- **Benchmark Studio** — model comparison cards, stress-test scenarios, and
  simulated run progress.

#### Proof pack
- **Standalone validator** (`validator/`) — an independent re-implementation of
  the engine and crypto layer that never imports `src/`. 62 checks covering
  engine behaviour, tolerance boundaries, tamper resistance, ledger hash
  chaining, third-party verification, error-injection benchmarks, latency, and
  artifact generation.

#### Testing & benchmarks
- **46 tests across 9 modules** — re-executor, API, crypto, parsers, PDF,
  end-to-end pipeline, EDGAR, and benchmark presets.
- **FinQA-style error-injection benchmark** asserting ≥ 90% catch rate and
  ≤ 5% false-flag rate.
- Real-company benchmark presets for Apple, Tesla, Microsoft, and Alphabet.

#### Deployment
- **Seven-service Docker Compose topology** — API, Temporal worker (2
  replicas), React frontend behind Nginx, PostgreSQL 16, Redis 7, Temporal
  server, and the Temporal web console.
- **Development overlay** (`docker-compose.dev.yml`) with API hot reload and
  frontend HMR.
- **One-command scripts** — `start.sh` / `start.bat` and `stop.sh` / `stop.bat`.
- `.env.example` configuration template.

#### Governance
- **FinVerify Proprietary License v1.0** (`LICENSE`) — All Rights Reserved, with
  an explicit contributor grant that keeps pull requests fully open.
- `CONTRIBUTING.md` — branch naming, commit conventions, the PR checklist, and
  the review and merge policy.
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 with project-specific
  editorial standards.
- `SECURITY.md` — private disclosure process, security model, known
  limitations, and a deployment hardening checklist.
- `CHANGELOG.md`, GitHub issue and pull request templates, `CODEOWNERS`, and a
  three-leg GitHub Actions CI pipeline.

[Unreleased]: https://github.com/Meet6338-X/finverify/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Meet6338-X/finverify/releases/tag/v1.0.0
