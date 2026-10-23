# SPEC — APAAR Student Data Management & Verification Platform

**SIH 2026 · Problem Statement 26263 · AICTE (Regulation Bureau) · Theme: Smart Automation**
Team MIGA. This file is the single source of truth for the build. Read all of it before writing code.

---

## 0. How to work (instructions for Claude Code)

- Build in the **phases in section 12, one phase at a time**. At the start of each phase, enter plan mode, show the plan, and wait for approval. At the end of each phase: run all tests, fix failures, update `README.md`, and make one git commit.
- Every feature must trace back to a requirement in section 1. If something isn't traceable, don't build it.
- **No real personal data, ever.** All students are synthetic. Never call any real government production API. Never invent real APAAR or Aadhaar numbers belonging to real people.
- Keep it simple and working over clever and half-done. A feature that runs in the demo beats three that don't.
- When a fact about AICTE rules is uncertain (marked ⚠ below), implement it as **configurable** and leave a `TODO(verify)` comment, never hardcode it.
- Don't add features, pages, or roles not listed here. Ask first.
- Prefer small, typed, tested modules. Python: type hints + pydantic. TypeScript: strict mode.
- Ask before: deploying anything, adding a paid service, or deleting files you didn't create.

---

## 1. The problem and the requirements (from the problem statement)

AICTE gets student data from institutions inconsistently — PGDM institutions send detailed student data, others mostly send totals. AICTE needs a platform where institutions submit **student-level data keyed by APAAR ID** after admissions, with real-time validation, monitoring and verification.

Pipeline: **Institution → Student Data Upload → APAAR Validation → Data Verification → AICTE Central Repository → Analytics & Monitoring → Authorized Verification**

| # | Requirement | Where it's built |
|---|---|---|
| R1 | Secure platform/API for institutions to upload and update student-level data using APAAR ID as unique identifier | Institution upload (Excel + REST API), versioned updates |
| R2 | Fields: Approved Intake, Actual Enrolment, Supernumerary Seats, NRI, OCI status, FN status, other student info | Data model (section 5) |
| R3 | Automated validation: duplicates, invalid/missing APAAR, admissions exceeding intake, inconsistencies, duplicate enrolment across institutions | Validation engine (section 6) |
| R4 | Real-time dashboards for AICTE and institutions | Both portals |
| R5 | Secure verification mechanism for authorized stakeholders (AICTE, institutions, employers, regulators) | Public `/verify` page + verification API |
| R6 | Verifiable student records linked to academic identity | Ed25519-signed records with QR |
| R7 | Integration/API with institutional and AICTE systems | Documented REST API (OpenAPI), per-institution API keys |
| R8 | Security, privacy, authentication, RBAC, audit trails, consent | Section 8 |
| R9 | Reports for policy, accreditation, monitoring, regulation | Report generator (4 types) |
| R10 | Printing/display of APAAR ID with student ID on certificates | Certificate module |
| Innovation | Automated validation, intelligent anomaly detection, real-time monitoring, secure verification, analytics | Anomaly layer (section 6.2) |

---

## 2. Scope

**Exactly two portals plus one public page:**

1. **Institution portal** (`/institution/*`) — colleges upload and manage student data.
2. **AICTE portal** (`/aicte/*`) — national monitoring, anomaly handling, rules, reports.
3. **Public Verify page** (`/verify`) — no login; anyone scans a QR or enters a certificate ID and sees Valid / Revoked / Not found. (Needed for R5, R6, R10.)

Out of scope: student portal, employer portal, payments, chat, mobile app.

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui, one app with role-based routes |
| i18n | `next-intl` — English (`en`), Hindi (`hi`), Marathi (`mr`). All strings in message files, none hardcoded |
| Charts / map | Recharts + India states GeoJSON (react-simple-maps or d3-geo) |
| Graph view | react-force-graph (2D) or Cytoscape.js |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2 + Alembic, pydantic v2 |
| DB | PostgreSQL 16 |
| Jobs | Run validation in a FastAPI BackgroundTask; no Celery unless needed |
| ML / analysis | scikit-learn (IsolationForest), networkx (graph clustering), rapidfuzz (name matching) |
| Crypto | `cryptography` (Ed25519 signing, AES-GCM field encryption), `pyotp` (TOTP MFA), `argon2-cffi` (passwords) |
| Documents | `openpyxl` (Excel), WeasyPrint (PDF certificates and reports), `qrcode` |
| Mock ABC registry | Separate FastAPI service (`services/mock-abc`) |
| Local dev | Docker Compose (postgres, api, mock-abc, web) |
| Cloud (later) | AWS: ECS or EC2 for services, RDS Postgres, S3 for documents, KMS for keys. Behind env vars; local uses filesystem + a local key |

---

## 4. Repository layout

```
/apps/web                 Next.js app (both portals + /verify)
/services/api             FastAPI main backend
  /app/models             SQLAlchemy models
  /app/schemas            pydantic schemas
  /app/routers            auth, institution, aicte, verify, rules, reports, audit
  /app/validation         rule engine (one module per rule group)
  /app/anomaly            isolation forest, graph clustering, risk score
  /app/integrations       adapters: abc_registry.py, digilocker.py (interfaces + impls)
  /app/security           crypto, rbac, audit chain, rate limit
  /app/reports            report builders
  /app/certificates       certificate + signing
  /tests
/services/mock-abc        mock APAAR/ABC registry service
/data/generator           synthetic data generator (section 9)
/data/rules               rules_2026_27.json etc.
/data/seed                generated output (gitignored)
/i18n                     shared message files if needed
docker-compose.yml
SPEC.md  README.md
```

---

## 5. Data model (PostgreSQL)

Use UUID primary keys. All tables get `created_at`, `updated_at`.

- **institution**: id, aicte_id (e.g. `1-1234567890`), name, state, district, region (Northern/Southern/Eastern/Western/Central/North-Eastern/South-Western), type (Govt/Private/Deemed), lat, lng
- **course**: id, institution_id, level (`DIPLOMA`|`UG`|`PG`), program (`ENGINEERING`|`MANAGEMENT`|`DESIGN`|`OTHER_TECH`), name (e.g. "Computer Science and Engineering"), approved_intake (int), academic_year (e.g. `2026-27`). **Institutions cannot edit approved_intake.**
- **student**: id, apaar_id_enc (encrypted), apaar_id_hash (HMAC-SHA256 for lookups/uniqueness), apaar_last4, name, dob, gender, phone_enc, phone_hash, email_enc, email_hash, guardian_name, address_hash (normalized-address hash for graph), nationality, qualifying_board (e.g. CBSE, MSBSHSE, IB, FOREIGN), passport_no_enc (FN/OCI only)
- **enrolment**: id, student_id, institution_id, course_id, academic_year, admission_date, category (`REGULAR`|`NRI`|`FN`|`OCI`|`PIO`|`CIWGC`), seat_type (`WITHIN_INTAKE`|`SUPERNUMERARY` — derived from category, never user-entered), oci_card_issue_date (nullable), nri_sponsor_doc_id (nullable), status (`ACTIVE`|`WITHDRAWN`|`COMPLETED`), apaar_status (`VERIFIED`|`PENDING_CONSENT`|`MISMATCH`|`NOT_FOUND`|`EXEMPT`), version (int)
- **enrolment_version**: full snapshot JSON of every change (R1 "update" history)
- **document**: id, enrolment_id, kind (`NRI_SPONSOR`|`PASSPORT`|`OCI_CARD`|`VISA`|`OTHER`), storage_key, sha256
- **upload_batch**: id, institution_id, uploaded_by, filename, row_count, status (`VALIDATING`|`HAS_ERRORS`|`READY`|`SUBMITTED`), submitted_at
- **validation_issue**: id, batch_id (nullable), enrolment_id (nullable), institution_id, rule_code, severity (`ERROR`|`WARNING`), row_number, field, message_key (i18n key), params (JSON)
- **flag** (AICTE-side anomaly): id, institution_id, enrolment_ids (array), type, severity (`LOW`|`MEDIUM`|`HIGH`|`CRITICAL`), reason_key, params, score, status (`OPEN`|`ASSIGNED`|`SENT_TO_INSTITUTION`|`INSTITUTION_RESPONDED`|`CONFIRMED_VIOLATION`|`CLEARED`), assigned_to, institution_response, response_docs
- **consent**: id, student_id, purpose (`APAAR_VERIFICATION`), channel (`OTP`|`DIGILOCKER`), granted_at, revoked_at, token_hash, ip
- **certificate**: id, enrolment_id, cert_no (human-readable, e.g. `AICTE-2026-XXXXXXXX`), payload_json, signature (base64), key_id, issued_at, revoked_at, revoke_reason
- **rule_set**: id, academic_year, json (validated by pydantic), created_by, active
- **user**: id, email, password_hash, role, institution_id (nullable), region (nullable), totp_secret_enc, mfa_enabled
- **audit_log**: id (bigserial), ts, actor_id, actor_role, action, entity, entity_id, before_hash, after_hash, ip, prev_hash, entry_hash
- **api_key**: id, institution_id, key_hash, label, last_used_at, revoked_at

Indexes: unique (apaar_id_hash) on student; index on enrolment(academic_year, status), enrolment(institution_id, course_id); phone_hash, email_hash, address_hash.

---

## 6. Validation engine (R3) — the core

Implement as a pipeline of independent rule modules. Each returns `ValidationIssue` objects with a `rule_code`, `severity`, `message_key` and `params` (messages are translated on the frontend). Runs on (a) an upload batch before submission and (b) the whole national repository nightly / on demand.

### 6.1 Rule groups

**V1 — Duplicate records** (ERROR)
- `V1.DUP_IN_BATCH`: same APAAR twice in one upload
- `V1.DUP_IN_INSTITUTION`: APAAR already has an ACTIVE enrolment at this institution for this year

**V2 — Invalid / missing APAAR**
- `V2.FORMAT` (ERROR): not exactly 12 digits. Do **not** invent a checksum (no official spec known) — `TODO(verify)`.
- `V2.MISSING` (ERROR): blank, unless category is FN (then passport_no required instead → else `V2.MISSING_PASSPORT`)
- `V2.NOT_FOUND` (ERROR): not in ABC registry (via adapter)
- `V2.NAME_MISMATCH` (WARNING if similarity 80–90, ERROR below 80): rapidfuzz `token_sort_ratio` after normalization (lowercase, strip honorifics, collapse spaces, common transliteration folds: `ee→i`, `oo→u`, `w→v`, `y↔i` at end)
- `V2.DOB_MISMATCH` (ERROR)

**V3 — Exceeding intake** (per course, per academic year, using the active rule_set)
- `V3.WITHIN_INTAKE_EXCEEDED` (ERROR): count(REGULAR + NRI) > approved_intake
- `V3.NRI_CAP_EXCEEDED` (ERROR): count(NRI) > floor(approved_intake × nri_cap_pct)
- `V3.SUPERNUMERARY_EXCEEDED` (ERROR): count(FN+OCI+PIO+CIWGC) > floor(approved_intake × supernumerary_pct[level][program])
- `V3.CIWGC_SPLIT` (WARNING): sub-pool split violated, accounting for the vacancy-transfer rule (configurable)
- `V3.NEAR_CAP` (WARNING): ≥ 95% of any cap

**V4 — Inconsistencies**
- `V4.FN_INDIAN_BOARD` (WARNING→HIGH flag): category FN but qualifying_board is an Indian board
- `V4.FN_HAS_APAAR` (WARNING): category FN but has a VERIFIED APAAR (APAAR requires Aadhaar)
- `V4.NRI_NO_SPONSOR_DOC` (ERROR): NRI with no NRI_SPONSOR document
- `V4.OCI_NO_CARD_DATE` (ERROR): OCI without oci_card_issue_date
- `V4.OCI_CLASSIFICATION` (INFO): OCI card date on/after `oci_foreign_cutoff_date` → counts as foreign/supernumerary ⚠ configurable
- `V4.AGE_IMPLAUSIBLE` (ERROR): age at admission < 15 or > 60 (configurable)
- `V4.ADMISSION_DATE_OUT_OF_YEAR` (ERROR)
- `V4.REGULAR_FOREIGN_NATIONALITY` (WARNING): category REGULAR but nationality ≠ Indian

**V5 — Cross-institution duplicate enrolment** (ERROR at batch level, CRITICAL flag nationally)
- `V5.ACTIVE_ELSEWHERE`: same APAAR ACTIVE at another institution in the same academic year. Show both institutions and admission dates.

Batch submission is **blocked while any ERROR exists**. WARNINGS may be submitted with a written justification stored on the batch.

### 6.2 Intelligent layer (Innovation)

- **Isolation Forest** over institution-year features: enrolment/intake ratio, YoY enrolment change, % supernumerary, % NRI, % APAAR verified, % name mismatches, share of students with shared phone/email, mean age, gender ratio. Output anomaly score 0–100 → flag type `INSTITUTION_OUTLIER` with the top 3 contributing features explained in plain words (compute feature deviation vs median to explain).
- **Ghost-student graph**: networkx graph, nodes = students, edges when they share phone_hash, email_hash, guardian_name+address_hash, across **different** institutions or many within one. Connected components with ≥ 5 students sharing ≤ 3 contact points → flag `GHOST_CLUSTER`. Expose the component as JSON for the graph view.
- **Institution risk score** (0–100): weighted sum of open flags by severity, over-intake history (last 3 years), APAAR verification rate, isolation-forest score. Weights in rule_set config.

---

## 7. Rules configuration (versioned per academic year)

`/data/rules/rules_2026_27.json`, loaded into `rule_set`, editable in the AICTE Rules Manager (validated with pydantic, every change audited):

```json
{
  "academic_year": "2026-27",
  "nri_cap_pct": 0.05,
  "supernumerary_pct": {
    "UG":      {"ENGINEERING": 0.15, "MANAGEMENT": 0.25, "DESIGN": 0.25, "OTHER_TECH": 0.25},
    "DIPLOMA": {"ENGINEERING": 0.15, "MANAGEMENT": 0.25, "DESIGN": 0.25, "OTHER_TECH": 0.25},
    "PG":      {"ENGINEERING": 0.25, "MANAGEMENT": 0.25, "DESIGN": 0.25, "OTHER_TECH": 0.25}
  },
  "ciwgc_fraction_of_supernumerary": 0.3333,
  "ciwgc_vacancy_transfer": true,
  "oci_foreign_cutoff_date": "2021-03-04",
  "near_cap_threshold": 0.95,
  "age_min": 15, "age_max": 60,
  "name_match": {"warn_below": 90, "error_below": 80},
  "risk_weights": {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 4, "LOW": 1, "over_intake_year": 8, "unverified_pct": 0.3, "iforest": 0.3}
}
```

⚠ The 2026-27 AICTE Approval Process Handbook changed supernumerary caps (15% UG/diploma engineering, 25% PG engineering and management/design/other technical) and says supernumerary seats are exclusively for international students. Whether the 1/3 CIWGC split survived that rewrite is **not verified** — keep it configurable and mark `TODO(verify)`. Also include `rules_2025_26.json` with the old single 15% slab so the year-switch is demonstrable.

---

## 8. Security, privacy, consent (R8)

- **Roles (RBAC)**, enforced in a FastAPI dependency on every route and mirrored in Next.js middleware:

  | Role | Portal | Access |
  |---|---|---|
  | `AICTE_SUPER_ADMIN` | AICTE | everything, users, rules |
  | `AICTE_REGIONAL_OFFICER` | AICTE | own region only (row-level filter) |
  | `AICTE_ANALYST` | AICTE | read-only, PII masked |
  | `INST_ADMIN` | Institution | own institution, approves/submits, manages API keys |
  | `INST_OPERATOR` | Institution | upload/edit, cannot submit |

- **Auth**: email + password (argon2id), JWT access (15 min) + refresh (httpOnly cookie), **TOTP MFA mandatory** for `AICTE_*` and `INST_ADMIN`. Lockout after 5 failed attempts.
- **Field encryption**: APAAR, phone, email, passport encrypted with AES-256-GCM (envelope: data key from KMS in cloud, local master key in dev). Lookups via HMAC-SHA256 hashes. **Aadhaar is never collected or stored.**
- **Masking**: UI shows `XXXX-XXXX-1234`. Full value only to roles that need it, and each reveal is audited.
- **Audit trail (tamper-evident)**: every write and every PII reveal appends to `audit_log` with `entry_hash = SHA256(prev_hash || canonical_json(entry))`. Provide `GET /audit/verify` that walks the chain and returns the first broken entry. Also a script `scripts/tamper_demo.py` that edits one row directly in Postgres (for the demo).
- **Consent**: before APAAR data is fetched from the registry/DigiLocker, the student must consent. Dev flow: generate a one-time consent link + OTP (printed to console/email-log, no real SMS), student page `/consent/[token]` shows what will be shared and with whom → Approve/Decline. Store in `consent`. Revocation supported. Enrolment `apaar_status = PENDING_CONSENT` until then.
- **Uploads**: allowlist `.xlsx`/`.csv`, max 10 MB, row limit 20k, strip formulas and prefix cells starting with `= + - @` (CSV-injection), MIME sniffing.
- **API**: per-institution API keys (hashed), rate limiting (slowapi), CORS locked to web origin, security headers (CSP, HSTS in prod), pydantic validation everywhere, SQLAlchemy only (no raw string SQL).
- **Verify page**: returns only name (partially masked), course, institution, year, status, issue date. No DOB, phone, APAAR beyond last 4.
- **Data minimization**: store only fields listed in section 5.

---

## 9. Data (synthetic + real reference)

### 9.1 Real reference data
- Institutions and approved intake: if a public AICTE approved-institutions list is reachable, use a real subset (2–4 states incl. Maharashtra). If not reachable from the sandbox, generate realistic institutions and **ask the user to drop the CSV into `/data/reference/`**. Never scrape behind logins.
- India states GeoJSON: public-domain source, committed to `/apps/web/public/geo/`.

### 9.2 Synthetic generator (`/data/generator/generate.py`)
- `Faker('en_IN')` + custom name lists for regional variety. Deterministic with `--seed`.
- ~100 institutions, ~3–6 courses each, intakes 30/60/120/180, ~35k students, academic years 2025-26 and 2026-27.
- Writes: Postgres seed, the **mock-ABC registry dataset** (the "truth": APAAR → name, dob, gender), and **per-institution Excel upload files** matching the template.
- **Planted fraud with a ground-truth manifest** (`/data/seed/planted.json`) so tests and the demo know exactly what must be caught:

  | Planted case | Count |
  |---|---|
  | Duplicate APAAR in one batch | 15 |
  | Invalid format APAAR | 20 |
  | APAAR not in registry | 25 |
  | Name mismatch (spelling variants that should PASS) | 40 |
  | Name mismatch (different person, should FAIL) | 15 |
  | Institution over within-intake | 4 institutions |
  | NRI over 5% | 3 courses |
  | Supernumerary over cap | 3 courses |
  | FN with Indian board | 12 |
  | NRI without sponsor doc | 10 |
  | Same APAAR active at 2 institutions | 18 |
  | Ghost cluster: 40 students across 3 institutions sharing 3 phones | 1 |
  | Smaller ghost clusters | 3 |
  | Outlier institution (enrolment jumped 0.4× → 1.15× intake) | 2 |

- `tests/test_planted.py` asserts every planted case is detected and that the "should PASS" spelling variants are **not** flagged as errors.

### 9.3 Mock ABC registry (`services/mock-abc`)
Mirrors the shape of an institutional ABC verification API:
- `POST /v1/apaar/verify` `{apaar_id, name, dob}` → `{exists, match: {name_score, dob_match}, masked_name, status}`
- `GET /v1/apaar/{id}/status` → `{exists, active}`
- Auth via `x-client-id` / `x-client-secret`. Adds 50–300 ms latency and a 1% random 503 to prove retry/backoff handling.

### 9.4 Integration adapters (`app/integrations`)
- `AbcRegistry` interface with `MockAbcRegistry` (default) and `AbcRegistryProduction` stub (raises NotImplemented, documented).
- `DigiLockerProvider` interface with `MockDigiLocker` (default; simulates the OAuth consent → issued-document pull of the APAAR/ABC ID card) and `ApiSetuSandboxDigiLocker` stub. **The team hasn't yet confirmed which endpoints the API Setu sandbox (sandbox.api-setu.in) exposes** — leave the sandbox adapter as a clearly marked stub with config keys, so it can be filled in later. Select implementation via env var.
- Pitch line in README: "Production swap = change one env var once AICTE onboards as DigiLocker requester / ABC integrator."

---

## 10. Features by portal

### 10.1 Institution portal
1. **Dashboard / seat matrix** (R4): per course — approved intake, filled, NRI used vs cap, supernumerary used vs cap (FN/OCI/PIO vs CIWGC), APAAR verification %. Bars turn amber ≥ 95%, red when exceeded. Data refreshes via polling (5 s) or SSE.
2. **Courses**: read-only list of approved courses and intake (from AICTE).
3. **Upload** (R1): download Excel template (with a hidden "lists" sheet for dropdowns, headers in selected language + English), upload → validation runs → **Validation report**: errors and warnings row by row with field, plain-language message (translated) and fix hint; filter by severity; download errors as Excel. Inline edit to fix a row and re-validate. Submit button (INST_ADMIN only) disabled while errors exist; warnings need justification text.
4. **Students**: searchable/paginated list with category, APAAR status chip, masked IDs; single add/edit form; version history drawer per enrolment.
5. **APAAR verification & consent**: per-student status (Verified / Pending consent / Mismatch / Not found / Exempt-FN), "Send consent requests" bulk action, resend.
6. **Flags from AICTE**: list, details, respond with text + document upload.
7. **Certificates** (R10): issue for a student → PDF (A4, bilingual Hindi + English) with student name, course, institution, **APAAR ID and institution student ID printed together**, QR code to `/verify/{cert_no}`, signature footer with key id. Revoke with reason.
8. **API access** (R7): create/revoke API keys, link to OpenAPI docs.

### 10.2 AICTE portal
1. **National dashboard** (R4): KPI tiles (total enrolment, institutions reporting, APAAR verified %, institutions over intake, open flags by severity); India choropleth (metric switch: over-intake count, verification %, risk); drill-down state → institution → course → student list. Regional officers auto-scoped.
2. **Anomaly centre** (R3 + Innovation): queue of flags with severity, type, institution, plain-language reason, score; filters; assign; workflow states (section 5); bulk "send to institution"; detail view with evidence.
3. **Duplicate resolver**: V5 cases side by side (institutions, courses, admission dates, statuses) → mark resolved / send to both institutions.
4. **Ghost network**: force-directed graph of flagged clusters, nodes colored by institution, edges labelled by shared attribute (phone/email/guardian), click → student list.
5. **Institutions**: table sorted by risk score with sparkline of score over years; institution profile page (courses, seat matrix, flags, history).
6. **Rules manager**: view/edit rule sets per academic year with validation, diff view vs previous year, activation; all changes audited.
7. **Reports** (R9) — PDF + Excel, filterable by year/state/program:
   - Intake vs enrolment (state/course)
   - Excess enrolment & violations
   - Category report (NRI/FN/OCI/PIO/CIWGC trends)
   - Institution accreditation data pack
8. **Audit log**: searchable table + "Verify chain" button showing ✓ intact or the first broken entry.
9. **Users** (super admin): create AICTE/institution users, reset MFA.

### 10.3 Public Verify (`/verify`, `/verify/[certNo]`)
Enter certificate number or scan QR → server checks Ed25519 signature over canonical payload + revocation → **Valid / Revoked (reason, date) / Invalid signature / Not found**, with minimal data (section 8). Also `GET /api/v1/verify/{cert_no}` JSON for regulators/employers (rate-limited). Publish the public key at `/.well-known/aicte-signing-keys.json`.

---

## 11. Multilingual (English, Hindi, Marathi)

- `next-intl`, language switcher in header, choice persisted in cookie.
- All UI strings **and** validation messages via keys (`validation.V3.NRI_CAP_EXCEEDED` with params). Backend never returns English prose for user-facing messages.
- Translate Hindi and Marathi once (Bhashini or careful manual), commit the files; no runtime machine translation.
- Devanagari font: Noto Sans Devanagari (web + WeasyPrint).
- Certificates bilingual (Hindi + English). Excel template headers in the chosen language with English in a second header row.
- Number and date formatting via `Intl` with `en-IN` / `hi-IN` / `mr-IN`.

---

## 12. Build phases (do in order; one commit per phase)

**Phase 1 — Foundation**
- Monorepo scaffold, docker-compose, `.env.example`, Makefile (`make up`, `make seed`, `make test`).
- DB models + Alembic migrations; rules JSON files + loader.
- Auth (password + TOTP MFA + JWT), RBAC dependency, audit-log hash chain + `/audit/verify`.
- Mock ABC service. Adapters with mock implementations.
- Synthetic generator + planted manifest; `make seed` loads everything.
- **Accept when:** `make up && make seed` works from scratch; login with MFA works for all 5 demo users; audit chain verifies; tests pass.

**Phase 2 — Institution core**
- Excel template download, upload, CSV-injection sanitizing, validation engine V1–V5, validation report API.
- Institution portal: dashboard seat matrix, courses, upload + report + inline fix + submit, students list/edit + version history.
- APAAR verification via adapter + consent flow.
- **Accept when:** uploading each planted Excel file produces exactly the expected issues; `test_planted.py` passes; submit is blocked with errors.

**Phase 3 — AICTE monitoring + intelligence**
- National dashboard with map and drill-down, regional scoping.
- Flags pipeline (nightly/on-demand national run), anomaly centre workflow, duplicate resolver, institution ↔ AICTE flag responses.
- Isolation Forest + explanations, ghost graph + view, risk score + institutions table.
- **Accept when:** all planted institution-level cases appear as flags with the right severity; the 40-student ghost cluster is visible in the graph.

**Phase 4 — Trust layer + reports + i18n**
- Certificate issue/revoke, Ed25519 signing, QR, bilingual PDF; public verify page + API + well-known keys.
- 4 reports (PDF + Excel). Rules manager with year switch and diff.
- Full Hindi + Marathi translations; language switcher; Devanagari in PDFs.
- **Accept when:** a scanned QR verifies Valid; revoking flips it to Revoked; editing the signed payload in DB makes it Invalid; every page renders in all 3 languages with no missing keys (add a test that fails on missing keys).

**Phase 5 — Hardening + polish + deploy prep**
- Rate limiting, security headers, lockout, PII reveal auditing, masked analyst view.
- OpenAPI docs polished with examples; API key auth tested.
- `scripts/tamper_demo.py`; demo reset script `make demo-reset`.
- README: architecture diagram (Mermaid), how to run, demo accounts, demo script (section 13), production-swap notes.
- AWS deployment files (Dockerfiles, a simple ECS or EC2 + RDS guide). **Do not deploy without asking.**
- **Accept when:** full demo script runs end to end on a fresh `make demo-reset`.

---

## 13. Demo script (must work end to end)

1. Login as institution operator, switch UI to **Hindi**, download template, upload the planted Excel → validation report shows the planted errors.
2. Fix rows inline, admin submits; consent requests sent; approve two consents → status turns Verified.
3. Login as AICTE super admin: national map shows Maharashtra with an over-intake institution; drill down to the course.
4. Anomaly centre: cross-institution duplicate (V5) and FN-with-Indian-board flagged; send to institution.
5. Ghost network: cluster of 40 "students" sharing 3 phones across 3 institutions.
6. Generate the excess-enrolment report as PDF.
7. Issue a certificate for a clean student → scan QR on phone → **Valid**. Revoke → **Revoked**.
8. Run `scripts/tamper_demo.py` → audit "Verify chain" shows the exact broken entry.

Demo users (dev only, printed by `make seed`, TOTP secrets printed too): one per role, plus one INST_ADMIN and INST_OPERATOR for a Maharashtra institution.

---

## 14. Testing

- pytest for every validation rule (positive + negative), planted-manifest test, audit chain test, signature/verify test, RBAC tests (each role denied what it shouldn't see, incl. regional scoping), upload sanitizing test.
- Playwright smoke test for the demo flow (steps 1, 3, 7).
- i18n missing-key test.
- `make test` runs everything; must be green before each phase commit.

---

## 15. Definition of done

Every row in the section 1 table is demonstrable in the running app; the demo script runs on a fresh reset; tests are green; README explains run, architecture and the production integration path; no real personal data anywhere in the repo.
