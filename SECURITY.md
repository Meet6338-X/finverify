# Security Policy

FinVerify's entire value proposition is that outputs are **provably** correct
and **provably** untampered. A weakness in the verification path is a
first-class security defect, treated accordingly.

---

## 🔒 Reporting a vulnerability

**Do not open a public issue, discussion, or pull request for a security
vulnerability.** A public report gives an attacker a head start and creates
noise for everyone tracking the tracker.

### Private disclosure

Use GitHub's private reporting:

> **Security → Report a vulnerability** on
> <https://github.com/Meet6338-X/finverify>

Or email the maintainer directly at the address listed in the repository
metadata. If you cannot reach the maintainer, use GitHub's private advisory
flow — it is the fallback, not the first choice.

Please include:

| What | Why it helps |
|---|---|
| **Type** | e.g. signature bypass, ledger tampering, key exposure, injection |
| **Location** | file, function, endpoint, or configuration |
| **Reproduction** | exact steps or a script — a proof-of-concept is worth far more than a description |
| **Impact** | what an attacker gains, and under what preconditions |
| **Environment** | commit SHA, deployment mode, configuration in use |
| **Suggested fix** | optional, but appreciated |

### What to expect

| Stage | Target |
|---|---|
| Acknowledgement | Within **3 business days** |
| Initial assessment | Within **10 business days** |
| Fix or mitigation plan | Within **30 business days** of confirmation |
| Public disclosure | Coordinated with you, after a fix ships |

We will keep you updated throughout, credit you in the release notes unless you
prefer otherwise, and we will not pursue legal action against good-faith
research that follows this policy.

---

## 🛡️ Security model

### What FinVerify protects

- **Certificate integrity.** Every certificate is signed with **Ed25519**
  (RFC 8032) over **canonical JSON** — sorted keys, no insignificant
  whitespace, UTF-8. Any modification to the payload, including a single bit,
  invalidates the signature.
- **Ledger immutability.** Certificates and reviewer decisions are `INSERT`-only,
  enforced by database-level rules. A compromised application layer still
  cannot rewrite history.
- **Verifiability without trust.** A third party needs only the 32-byte public
  key to verify a certificate. No API, no database, no access to FinVerify.
- **Determinism.** Verification arithmetic is pure SymPy/NumPy. No LLM is
  consulted, so no model can be prompted to reach a different answer.

### What FinVerify does not protect

Be clear-eyed about the boundaries:

- **Narrative claims.** Only *numerical* claims are verified. Statements about
  outlook, strategy, or intent are out of scope and are classified
  `unverifiable`.
- **The source data itself.** FinVerify checks the LLM's arithmetic against
  EDGAR. If EDGAR is wrong, the certificate reflects EDGAR.
- **Completeness.** A certificate proves a claim is correct — it does not prove
  that every claim in a document was extracted. Extraction coverage is a
  stated limitation, not a guarantee.
- **The signing key's custody.** Whoever holds the private key can mint
  certificates. Key management is the operator's responsibility.
- **Legal, accounting, or investment advice.** FinVerify is a verification
  tool, not an advisor.

---

## ⚠️ Known limitations

Reported honestly, so nobody is surprised:

| Area | Detail | Mitigation |
|---|---|---|
| **Default secrets** | `.env.example` ships `JWT_SECRET=changeme-jwt-secret` and `POSTGRES_PASSWORD=changeme`. The Ed25519 seed is deterministically derived from `JWT_SECRET`. | Rotate before any real deployment; mount externally-managed key material. |
| **JWT not enforced** | `python-jose` and the JWT settings are wired into config, but the API routes do not yet enforce authentication. | Do not expose the API publicly until auth lands. Tracked as a roadmap item. |
| **Signing-key rotation** | Changing `JWT_SECRET` re-derives the signing key and **invalidates every previously issued certificate**. | Migrate to an explicit key file at `FINVERIFY_SIGNING_KEY_PATH` before rotating. |
| **No rate limiting on the API** | Only the outbound EDGAR client is rate-limited. Inbound abuse controls are not implemented. | Deploy behind a reverse proxy with rate limiting; keep the API off the public internet. |
| **Tamper verifier is client-side** | The browser verifier trusts the public key it is given. A substituted key means substituted truth. | Distribute the public key out-of-band and pin it; the pinned key is the trust anchor. |
| **SEC fair-access** | EDGAR access depends on an honest `User-Agent` and honest rate limiting. | Set a genuine contact address. Misrepresenting yourself to the SEC violates their policy. |

---

## 🔑 Handling key material

- Signing keys live in `keys/` and `*.pem` — **already git-ignored**. Keep it
  that way.
- Never commit a key, a `.env` file, or a database dump. Not "just once", not
  "just to test".
- Use a distinct, randomly generated `JWT_SECRET` for every deployment. Do not
  reuse the example value.
- Keep signing keys out of container images. Mount them at runtime or use a
  secrets manager.
- If a key is exposed — committed, pasted in an issue, logged — **rotate it
  immediately** and notify the maintainer. Treat it as compromised the moment
  it leaves the trusted boundary.

---

## 🏗️ Deployment hardening checklist

Before FinVerify handles anything real:

- [ ] `JWT_SECRET` rotated to a strong random value
- [ ] `POSTGRES_PASSWORD` rotated
- [ ] `SEC_EDGAR_USER_AGENT` set to a genuine contact address
- [ ] Signing key mounted from outside the image, with restrictive permissions
- [ ] `keys/` and `.env` confirmed absent from the image and from git history
- [ ] API bound to a private interface or placed behind an authenticating proxy
- [ ] TLS terminated in front of the API and the dashboard
- [ ] Postgres and Redis on an internal network, not published
- [ ] Automated backups of the ledger enabled
- [ ] `LOG_LEVEL` set appropriately (not `DEBUG` in production)

---

## 🔭 Scope

**In scope**

- Signature bypass, forgery, or verification weakness.
- Ledger tampering, mutation, or deletion.
- Key exposure or predictable key derivation.
- Injection (SQL, command, SSRF) in the API, worker, or EDGAR client.
- Path traversal or arbitrary file read/write.
- Authentication and authorization bypass.
- Unsafe deserialisation.
- Vulnerabilities in the shipped Docker images or dependencies.

**Out of scope**

- Vulnerabilities in third-party services we do not control (SEC EDGAR, Docker
  Hub, PyPI, npm) — report those upstream.
- Findings that require an already-compromised host.
- Denial of service through pure volume on a development deployment.
- Missing hardening headers with no demonstrable impact.
- Social engineering or phishing.
- Reports generated by automated scanners with no working proof of concept.
- The project being unlicensed for your use case — that is a licensing
  question, not a vulnerability. See [`LICENSE`](LICENSE) §16.

---

## 📣 Disclosure policy

- The security advisory is published only after a fix is available, unless an
  active exploit is being used against users.
- Credit is given to the reporter unless anonymity is requested.
- We will not name a reporter without explicit consent.
- We do not pursue legal action against researchers who act in good faith,
  respect user privacy, avoid degradation of service, and give us reasonable
  time to respond.

---

<div align="center">

**Security issues are private until a fix exists.**

</div>
