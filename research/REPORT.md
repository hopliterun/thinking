# Crypto product discovery — decision report

Task packet: `CRYPTO_PRODUCT_DISCOVERY_COLD_V18` · Run mode: cold start · Research date: 2026-11-07 (UTC)
Audit trail: [`LEDGER.md`](LEDGER.md) (actions + claims) · Test code and outputs: [`tests/`](tests/) · Files: [`MANIFEST.md`](MANIFEST.md)

## 1. Verdict

**RECOMMEND_LIMITED_TEST — limited preflight, not a proven opportunity.**

Best candidate: **a pre-validation and submission-operations pipeline for ESMA's new MIDAS crypto
market-surveillance feed, for small and mid-size EU crypto-asset service providers (CASPs).**

Why it leads: it is the only candidate found that is **mandatory, recurring (every two weeks), brand new
(instructions published 21 Oct 2026), and has a countable set of obligated buyers (314–359 CASPs)**. ESMA's own
artifacts contradict each other in ways that would get files rejected, and no productized tool was found. What it
lacks: **any direct evidence of buyer pain or willingness to pay.** The obligation is only two weeks old, no CASP
has gone public with complaints, and no conversations were held. A modest experiment is warranted. Building is not
yet justified.

## 2. Problem and buyer

**The job.** Under MiCA Art. 68(9), 76(15) and 94, every CASP that executes crypto-asset transactions must send
execution records (ISO 20022-style `auth.117`) to ESMA's MIDAS system. CASPs that operate a trading platform must
also send order-book records (`auth.118`). The rules:

- **Format and delivery.** UTF-8 JSON over SFTP, **every two weeks**, max 500 MB per file, strict file naming.
  Onboarding goes through UAT; production starts per national authority (NCA) (C01–C03).
- **Three validation layers.** FIL (whole file rejected), MET (record rejected) and QUA (warning): 26 published
  rules (C04).
- **Duplicates.** Checked against **the entire MIDAS history**, not just the file (C05).
- **Re-sending an unchanged file** requires emailing ESMA **≥3 business days ahead**. Otherwise the records are
  dropped as duplicates.
- **Correcting an accepted record** requires a new record plus an advance email (C06).
- **Feedback.** A 17-column CSV that the CASP must poll for and reconcile (C07).

**Who.** Heads of compliance or regulatory reporting, and COOs, at CASPs.

- **Register count (T01, ESMA register updated 3 Nov 2026):** 314 (narrow) to 359 (broad) active CASPs have
  execution-type services; 21 are trading platforms.
- **Excluded from the target:** 111 Art. 60 notified entities (banks, investment firms), which likely have
  existing reporting stacks.
- **Excluded as likely in-house:** large groups such as Coinbase, Kraken, OKX and Bitpanda. Bitpanda runs "over
  100 reports" in-house (C13).
- **Plausible buyers:** roughly **150–180 small and mid-size CASPs** (T03, a name-heuristic count; see
  limitations). The largest pools are FR, CY, NL, MT, LV and CZ.

**Cost and workaround today.**

- **In-house mapping** of matching-engine, broker or liquidity-provider fill data to ESMA JSON, plus a manual
  upload, feedback and correction loop. Effort is unknown; my assumption is 1–3 months to build and 0.2–0.5 FTE to
  run.
- **Services build.** One firm quotes **€45k–140k to build, then €5k–9k/month to run** (C12; a vendor's asking
  price, not observed purchases).
- **Reference data.** A Digital Token Identifier (DTI) is mandatory per crypto-asset. A missing DTI rejects the
  record (MET-001).
  - DTIF charges **€186 per new DTI**.
  - API access costs **€7,409–28,744/year**, with no free operational tier (C11).

**Why it matters.** Rejected records leave gaps in a regulator's market-abuse surveillance. Phase 2 (Q4 2027,
subject to ESMA Board approval) is expected to widen scope, including personal identifiers (C09).

**Evidence quality.** The obligation, mechanics and buyer count are **OBSERVED** in primary ESMA documents. That
compliance is painful is **INFERRED**: hard rejections, history-wide duplicate rules, the contradictions below, law
firms marketing MIDAS help (C14), and a services firm pricing it. **No buyer statement of pain or budget was
obtained.**

## 3. Closest alternatives and residual gap

| Alternative | What it actually provides | Maturity (evidence) | Gap for a small CASP |
|---|---|---|---|
| Build in-house | Full control | Large CASPs do this (Bitpanda: in-house reporting team, C13) | Needs engineering plus continuous interpretation tracking |
| Intellectum Lab (custom engineering) | Fixed-fee diagnostic, then custom mapping to ESMA JSON and "schema validation" | Released as a service. No named CASP customers. Does not mention SFTP or feedback handling (C12) | €45k–140k plus €5k–9k/month. Bespoke |
| Law firms (d&a partners, Kohler Gotzev, Kadri) | Legal guidance, "can assist you" | Advisory (C14) | No software |
| Qalypto, OriginStamp | Sealed or verifiable market-data evidence in ESMA format | Released. Not MIDAS submission tools (C15) | Different job (evidence integrity) |
| Solidus Labs | Trade surveillance. Claims ESMA picked it as the "sole official" MiCA surveillance provider for NCAs | Vendor claim (C16) | Regulator-side and surveillance focus. No CASP-side MIDAS feed product found |
| Exchange software and crypto-as-a-service providers | May add MIDAS export as a feature | Desk check (A25): no MIDAS export found for AlphaPoint, Shift, B2Broker, ChainUp, Modulus, HollaEx, Upvest, Tangany, Bitpanda Technology Solutions, Boerse Stuttgart Digital or Crypto Finance. Products this new may simply not be indexed yet | **Biggest residual substitute risk**: can only be resolved by asking buyers |
| Established transaction-reporting RegTech (Regnology, Vermeg, Kaizen, Novatus, Qomply, S&P Cappitech) | Could extend to MIDAS | Two searches (A17, A25) found no MIDAS or MiCA record-keeping product. Not exhaustive | Unknown |
| Open source | None found. GitHub repository search returned 0 hits for 6 queries (A16) | — | — |

**Residual gap (inferred):** a productized, self-hostable tool that turns a small CASP's data into
first-time-accepted MIDAS files every two weeks. It would encode ESMA's ambiguous rules consistently, stop
avoidable whole-file rejections, track history-wide duplicates, and reconcile feedback back to source records.
The contradictions below show that "just validate against the schema" is not enough.

## 4. The product

**Workflow (MVP = executions only, `auth.117`; that covers ~290+ non-trading-platform CASPs):**

1. **Connectors:** CSV, SQL, or liquidity-provider fill exports, mapped to a canonical execution model. Handles
   the leg rules: brokers report one leg, venues report both.
2. **Reference mapping:** venue → ISO 10383 MIC (or `XOFF`/`XXXX`); asset/pair → DTI, flagging assets that need
   a DTI allocation.
3. **Build:** JSON per day and file type, split under 500 MB, with names that pass FIL-101 and a check that the
   part set is complete.
4. **Pre-validate:** official schema plus all locally checkable FIL/MET/QUA rules, under an explicit, versioned
   "interpretation policy" for ambiguous rules.
5. **Submit and reconcile:** SFTP push (UAT and prod), feedback polling, findings matched to source rows by file
   and JSON line, not only by `RecordRef` (see contradiction 4).
6. **Correct:** derive the resubmission set, check it against a local copy of accepted keys (MIDAS-wide
   duplicates), and draft the advance-notice emails ESMA requires.
7. **Audit:** an evidence pack per submission for the NCA.

**Customer outcome:** two-weekly submissions accepted first time without engineering involvement, with an audit
trail.

**Deployment:** a container that runs inside the CASP, so data stays in-house. Phase 1 excludes personal data
(C08), which keeps GDPR and trust exposure low at the start.

**Executed feasibility probe (T02).** A ~300-line Python prototype built only from public ESMA artifacts
implements FIL-101/102, batch completeness, 14 MET rules and 7 QUA rules, plus a duplicate store across
submissions. Results:

- **Mutations:** 14 of 17 single-rule mutations of ESMA's own samples were caught with the expected code. All 17
  produced a rejection.
- **Resubmission:** re-sending an accepted file flagged all 637 records as MIDAS-wide duplicates.
- **Throughput:** ~1,500 records/s in pure Python. A maximum-size file (~940k records) takes about 10 minutes, so
  speed is not a hurdle.

**Hardest engineering problem.** Not JSON. It is (a) semantic mapping from varied CASP data (legs, venue codes,
DTIs) and (b) keeping the interpretation policy aligned with what ESMA's validator actually does. Only UAT
feedback can confirm (b).

**Team feasibility.** One strong backend engineer could build the MVP in about 4–8 weeks (estimate). The heavier
non-code load is a DORA-grade vendor posture: Art. 30 contract terms, security certification over time.

## 5. Commercial path

- **Payer:** the CASP's compliance budget. The spend is mandatory, recurring and supervised.
- **Buyer-side value (ranges, assumptions):**
  - Avoids a €45k–140k build plus €60k–108k/year to run (services quote).
  - Or avoids 0.2–0.5 FTE plus 1–3 months of engineering.
  - Lowers the risk of rejected files reaching the supervisor.
- **Pricing hypothesis (unvalidated):** €750–2,500/month plus €5k–15k onboarding.
- **Vendor-side costs:**
  - Infrastructure is negligible: self-hosted, or under €500/month for a control plane.
  - Real costs: security certification (rough €20k–40k), DORA contract and legal work, support peaks around each
    two-week cycle, and tracking spec changes. Phase 2 will add scope.
- **Market math (illustrative):** 150–180 candidate CASPs × 10–15% adoption ≈ 15–27 customers ≈
  **€135k–810k ARR**. A modest niche that fits a solo founder or small team, not a venture-scale market.
- **First 5–10 customers:**
  - Direct outreach to small CASPs listed (with websites) in ESMA's public register, starting with FR, CY, NL and
    MT.
  - Channel partners: law firms and compliance consultancies already publishing on MIDAS (C14).
  - A free open-source validator, or a public "ambiguity sheet", as the lead magnet.
- **Biggest pricing uncertainty:** whether CASPs see this as a one-off integration (a services sale) or ongoing
  operations (SaaS).

## 6. Executed falsification tests

| ID | Test (prestated discriminator) | Result | What it does **not** prove |
|---|---|---|---|
| T01 | Count obligated CASPs from ESMA's register | 314–359 execution reporters, 21 trading platforms, 111 Art. 60 | Which firms are in onboarding now. Whether they would buy |
| T02a | Do ESMA's own samples, filenames and text pass ESMA's own rules under a literal reading? (Conflicts = evidence of friction) | **Conflicts found** (contradictions below) | That ESMA's validator applies the literal reading |
| T02b | Feasibility: ≥90% of targeted single-rule mutations caught with the expected code, and no spurious rejections on clean samples | **Not met as written.** 14/17 (82%). The 3 misses are cases where the official schema rejects the whole file first (MET-007, MET-016, QUA-001). Clean order-book sample: 17 literal-reading rejections | Acceptance in UAT. Real CASP data |
| T02c | Re-sending an accepted file shows up as history-wide duplicates | 637/637 flagged | ESMA's exact key normalization |
| T03 | Size of the realistic buyer pool after removing banks and large groups | ~168 by heuristic; plausible range 150–180 | Firm size or budgets. Name matching is crude |
| T04 | Internal consistency of ESMA's artifacts | 3/3 timestamp examples fail the schema. 8/22 feedback `RecordRef`s are lossy (`1.77932E+18`) | How much this matters in production |
| A16–A18 | Competitor and open-source search | No MIDAS product or OSS found. Services firm and law firms only | Absence. Search was not exhaustive (see unexecuted actions) |

**Contradictions in ESMA's public artifacts (T02, T04; reproducible):**

1. **Field examples vs schema.** The instructions' field examples and MET-006 use `YYYY-MM-DD HH:mm:ss.fff` with
   a space. The official schema requires the ISO `T` separator. Following the text as written gets **the whole
   file rejected (FIL-102)**.
2. **QUA-006 vs required field.** QUA-006 says Segment MIC must be empty when there is no transaction ID, but the
   schema makes `OrdrIdData/TradVn` **required** on every order. Obeying QUA-006 gets the whole file rejected,
   which is why ESMA's own sample carries 4 QUA-006 warnings.
3. **Severity escalation.** Annex 3 lists some problems as record-level rejections (MET-016) or warnings
   (QUA-001), but the schema enforces the same constraints. Under FIL-102 as written, one bad enum or one
   over-long ID rejects **the entire file**.
4. **Lossy feedback references.** ESMA's sample feedback file has `RecordRef` values mangled to `1.77932E+18`,
   apparently by a spreadsheet round-trip. These refs can't locate records.
5. **Filename.** The Annex 4 sample filename (`..._part1.json`) breaks FIL-101.
6. **Ambiguous rules on ESMA's own sample.** Under a literal reading, ESMA's order-book sample has 14 MET-013
   rejections (filled limit orders with `NoPric` limit price) and 3 MET-008 rejections (validity time equal to,
   not after, the event time).

**Corrections made during the run:**

- **Schemas.** A sub-agent said the MIDAS downloads include two JSON schemas. They are sample instances. I then
  assumed the schemas were unpublished, but they are public inside the Nov 2025 message-spec zip
  (ESMA65-955014868-15160).
- **Harness bug.** A bug in my MET-005 mutation was found and fixed.
- **T03 classification.** The regex marked some small firms as large (e.g. Coingate, GateHub) and kept some
  non-small firms in the small set (e.g. B2C2, BVNK, OSL). That is why a range is reported.
- **Missed bar.** The prestated feasibility bar was missed and is reported as missed.

## 7. Risks, kill criteria, next action

**Risks (highest first):**

1. **Embedded substitutes.** Exchange software and crypto-as-a-service providers ship MIDAS export, or big RegTech
   vendors bundle it. A desk check found none, but that is weak evidence of absence. After July 2026 many firms
   moved under white-label licensed partners (Tangany guide, A25). That concentrates reporting at fewer CASPs and
   may shrink the pool of small buyers.
2. **Free tooling from ESMA.** ESMA or its provider (European Dynamics, per the document control page) ships a
   free validator, or clarifies the rules, eroding the pre-validation value.
3. **Integration seen as one-off.** CASPs treat this as a one-time integration and won't pay recurring fees.
4. **Timing.** NCAs stagger go-live. ESMA's 2027 programme targets phase 1 "fully operational by 2027", so the
   urgency window may be short or late.
5. **Procurement friction.** DORA-driven vendor due diligence slows procurement for a solo vendor.
6. **Reference-data licensing.** DTIF licence terms may limit sharing DTI data across customers.

**Kill criteria:**

- ≥3 of the first 10 qualified CASPs say an existing vendor already delivers MIDAS files, **or**
- ESMA publishes a free validator covering the FIL/MET/QUA rules, **or**
- fewer than 2 of 10 agree to a paid pilot or LOI at ≥€500/month, **or**
- NCAs publish production dates after Q4 2027.

**Smallest next validation action (needs your authorization, because it means contacting people):**

- **Reach out:** 15 short messages to small CASPs from the register (FR, CY, NL, MT), plus 3 law firms or
  consultancies already writing about MIDAS.
- **Ask about:** UAT status, current approach (in-house, vendor or not started), who owns it, and budget.
  Attach the contradiction list as the conversation opener.
- **Separately:** ask ESMA MIDAS support how it interprets contradictions 1–3.
- **Cost:** ~20–30 founder hours, €0, 2–3 weeks.
- **Decision rule:** build the MVP if ≥3 CASPs have no vendor and ≥2 agree to a paid pilot or LOI. Otherwise apply
  the kill criteria.

## 8. Alternatives and stopping record

Six parallel discovery lanes were run (security ops, stablecoin finance, regulatory reporting, DeFi risk, developer
infrastructure, emerging/adjacent). Their strongest candidates, and why each ranks below MIDAS:

| Challenger | Strongest evidence | Why it ranks lower |
|---|---|---|
| Signing tripwire and containment for self-hosted signers (exchanges, payment firms) | Repeated signing-path and hot-wallet incidents (reported). Lane replayed one EIP-7702 sweep pattern | Willingness to pay inferred. Heavy trust and integration needs. Fireblocks, Turnkey and others are strong substitutes |
| Reduce-only incident responder for small Morpho curators | Resolv incident (Mar 2026): $6.2M moved in ~90 min. 26 curators, 20 with under $130M | ~20 buyers. No willingness-to-pay evidence. Morpho Sentinel and Philidor overlap |
| Digital-asset-treasury close controls and audit evidence | SEC filings with crypto-specific control weaknesses | Lanes disagree on prevalence (~10% heuristic vs 2/55 10-Ks). Accounting incumbents exist |
| Bug-bounty intake and dedup triage for self-run programs | Jump: 809 submissions → 127 unique valid. Dedup prototype top-1 0.67–0.71 | Fewer than ~25 self-run programs. Trust barriers |
| Crypto-ATM compliance and refunds | FBI IC3: 13,460 complaints, $389M (2025) | Willingness to pay untested. State bans can shrink the market |
| DAC8/CARF reporting, MiCA white-paper iXBRL QA, Defender replacement | Real mandates or migrations | XML/iXBRL validation is commoditized and cheap. Defender replacement has 8+ vendors |

**Serious actions left unexecuted:** buyer interviews (need permission). Asking ESMA for clarification (contact).
UAT access (only obligated CASPs can get it). Private vendor roadmaps (only reachable by asking). Collecting
NCA-specific go-live dates. Checking whether ESMA's sample DTIs resolve (the DTIF API is paid; the free UAT tier
is limited). Challenger checks the lanes proposed but did not run (Resolv backtest, signer-vendor buyer check).

```text
<RUN_DIAGNOSTIC_V18>
TASK_PACKET_ID: CRYPTO_PRODUCT_DISCOVERY_COLD_V18
RUN_MODE: COLD_START
TASK_OUTCOME: RECOMMEND_LIMITED_TEST
RUN_OUTCOME: DECISION_READY
HOST_STOP_REASON: UNKNOWN
HOST_STOP_EVIDENCE: NONE
STRONGEST_VERIFIED_RESULT: MIDAS is a mandatory two-weekly JSON/SFTP feed for 314-359 register-listed CASPs, and ESMA's public artifacts contradict each other in ways that cause whole-file rejection (tests/t01_output.json, tests/t02_output.json, tests/t04_output.json)
IMPORTANT_CORRECTION_OR_FALSIFICATION: "MIDAS downloads include JSON schemas" was false (they are samples; schemas are in the 2025-11 zip). Prestated feasibility bar not met (14/17 expected-code detection; 17 literal-reading rejections on ESMA's clean sample) - tests/t02_output.json
SERIOUS_ALTERNATIVES_CHECKED: 6 discovery lanes (LEDGER A01-A06); challengers in section 8
LAST_MATERIAL_ACTION_EXECUTED: A25 desk check for embedded substitutes (exchange software, crypto-as-a-service, RegTech): no MIDAS export product found; kill criterion 1 not triggered by public evidence
NEXT_BEST_FEASIBLE_ACTION: NONE_IDENTIFIED_WITH_REASON - the remaining decision-changing unknowns (willingness to pay, private vendor roadmaps, ESMA's interpretation) are only reachable by contacting people
BEST_BLOCKED_ACTION: A-B1 buyer outreach to 15 CASPs + 3 advisors, and an ESMA clarification email - needs user authorization to contact people
POTENTIALLY_DECISION_CHANGING_ACTION_LEFT_UNEXECUTED: A-B1 (willingness to pay and embedded substitutes as buyers see them)
WHY_END_NOW: Every remaining decision-changing uncertainty needs outreach, which is not authorized; the scoped decision (run a limited test vs build) is stable under the desk evidence gathered
CLAIMS_OR_TESTS_NOT_INDEPENDENTLY_VERIFIED: sub-agent lane findings in section 8 (incident figures, Morpho probe counts, dedup scores); DTIF and Intellectum pricing (single fetch each, summarized by a fetch model); ESMA 2027 work-programme quote (secondary source); Solidus "sole provider" (vendor claim)
ARTIFACTS_VERIFIED: research/REPORT.md, research/LEDGER.md, research/MANIFEST.md, research/fetch_data.sh, research/requirements.txt, research/tests/*.py, research/tests/t0[1-4]_output.json, research/tests/t03_candidate_small_mid_casps.csv
</RUN_DIAGNOSTIC_V18>
```
