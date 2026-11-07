# Evidence ledger

Observable summaries of what was done and what each load-bearing claim rests on. "Lane" rows are sub-agent
reports: they are REPORTED here and were not independently re-verified unless stated.

## Action ledger

`ACTION_ID | QUESTION | ACTION_EXECUTED | TOOL/SOURCE | RESULT | DECISION_IMPACT | NEXT / BLOCKER`

| ID | Question | Action | Tool / source | Result | Decision impact | Next / blocker |
|---|---|---|---|---|---|---|
| A00 | Are the obvious time-sensitive leads real? | 3 web searches: Defender sunset, MiCA white-paper iXBRL, Stream Finance | WebSearch | Defender retired 2026-07-01, already 3+ migration vendors. iXBRL mandatory since 2025-12-23. Stream fallout documented | Defender and iXBRL marked crowded or commoditized early | Lane research |
| A01 | Security ops pain? | Lane A sub-agent | Web + public RPC | Leader: signing tripwire and containment. Defender replacement crowded (8+ vendors) | Challenger | — |
| A02 | Stablecoin and business finance pain? | Lane B sub-agent | Web + EDGAR | No strong gap. Digital-asset-treasury close controls only limited preflight. 1099-DA reconciliation already in Koinly, CoinTracker and others | Lane mostly negative | — |
| A03 | Regulatory reporting pain? | Lane C sub-agent | ESMA register, ESMA docs, Arelle | Leader: MIDAS pipeline. iXBRL white papers: 14% uptake but €490 tools exist. DAC8 XML commoditized | **Incumbent candidate** | Validate (A07+) |
| A04 | DeFi risk ops pain? | Lane D sub-agent | Morpho API, public RPC, forums | Leader: reduce-only responder for ~20 small curators. No willingness-to-pay evidence | Challenger | Resolv backtest not run |
| A05 | Dev infra pain? | Lane E sub-agent | GitHub, web | Leader: bounty intake and dedup triage (fewer than ~25 self-run programs). Others crowded | Challenger | — |
| A06 | Emerging/adjacent pain? | Lane F sub-agent | Court filings, EDGAR, web | Leader: crypto-ATM compliance (willingness to pay untested). Treasury-company control weaknesses in 2/55 10-Ks | Challenger. Contradicts lane B's ~10% estimate | — |
| A07 | Are the MIDAS instructions real, and what do they require? | Downloaded 4 ESMA MIDAS files. Extracted PDF text | curl from esma.europa.eu, pdftotext | 85-page PDF, ESMA65-955014868-17690, dated 21 Oct 2026. Two-weekly JSON over SFTP. 26 rules | Obligation confirmed (primary) | Read rules |
| A08 | Are the ".json" downloads schemas? | Parsed both files | python | **Sample instances, not schemas** (root `Document`) | Corrects lane C's claim | Find schemas |
| A09 | Are schemas embedded in the PDF? | `pdfdetach -list` | poppler | 0 embedded files | Schemas not in the MIDAS package | Search ESMA library |
| A10 | Does ESMA publish the schemas anywhere? | ESMA library search for "MIDAS" and the Nov 2025 spec page | curl + grep | MIDAS search: only the 4 files. Schemas found in the ESMA65-955014868-15160 zip (2025-11) | Corrects my "unpublished" assumption | Validate samples |
| A11 | Do ESMA's samples pass ESMA's schemas? | jsonschema 2020-12 validation | python | 0 errors on all 4 sample files (positive control) | Validator works | Build rules |
| A12 | How many firms are obligated? | T01 on `CASPS.csv` (last update 03/11/2026) | python | 397 rows, 394 LEIs. 314–359 execution reporters. 21 trading platforms | Buyer count bounded | Segment |
| A13 | Which rules can only be checked beyond the schema? | Read Annex 3 and field tables. Profiled schema constraints | pdftotext, python | Schema requires TradVn and VldtyDtTm. Enums and maxLength sit in the schema | Found severity conflicts | Prototype |
| A14 | Can a small team build a pre-validator? | Wrote `midas_prevalidator.py` and T02 | python | 14/17 expected-code detection. 3 escalated to FIL-102. 637/637 resubmission dups. ~1.5k rec/s | Feasible. Prestated bar missed (reported) | — |
| A15 | Do ESMA's own artifacts conflict? | T02a + T04 | python | Timestamp examples vs schema, QUA-006 vs required TradVn, lossy `RecordRef`, Annex 4 filename, MET-013/MET-008 on the sample | Supports the "interpretation layer" value | — |
| A16 | Any open-source MIDAS tooling? | 6 GitHub repo searches | GitHub API | 0 results each | No OSS substitute found | Limit: repo search only |
| A17 | Any MIDAS vendors? | 3 web searches. Fetched Intellectum Lab page | WebSearch, WebFetch | Only a services firm (€45k–140k + €5k–9k/month), law firms, evidence layers. Bitpanda in-house | Residual gap plausible | A25 |
| A18 | Reference-data cost? | ISO 10383 MIC CSV. DTIF fees page | curl, WebFetch | PGSL = Kraken IE MIC (active). DTI €186 each. API €7,409–28,744/yr | Adds a concrete cost for small CASPs | — |
| A19 | When does it start? | Grep of instructions. ESMA 2027 work-programme summary. Seqlense note | grep, WebFetch | No date in the instructions. Phase 1 "fully operational by 2027" (secondary). No uniform start | Timing risk recorded | — |
| A20 | Realistic buyer pool? | T03 heuristic segmentation | python | 111 Art. 60, 35 name-matched large, 168 remainder (range 150–180 after noting misclassification) | Market sizing input | — |
| A21 | Re-run reproducibility | `fetch_data.sh` into a clean dir, checksum check | bash | All 5 ESMA artifact hashes match | Reproducible inputs | — |
| A22 | Fix test harness | Found MET-005 mutation bug (mutated a copy). Fixed | python | MET-005 then detected | Avoided a false negative | — |
| A23 | Clean re-run | T01–T04 re-run | python | All exit 0, same results | Outputs verified | — |
| A25 | Embedded substitutes? | 3 searches: exchange software, RegTech, crypto-as-a-service vendors + MIDAS | WebSearch | No MIDAS export product found. Tangany: firms moving to white-label partners post-July 2026 | Kill criterion 1 not triggered by public evidence | Only outreach can resolve |
| A-B1 | Willingness to pay | **Not executed:** outreach to CASPs, advisors, ESMA | — | Needs user authorization | Decision-changing | Blocked on permission |

## Claim ledger

`CLAIM_ID | EXACT_CLAIM | SUPPORT | CONTRARY_EVIDENCE | STATUS | LIMITS`

| ID | Claim | Support | Contrary evidence | Status | Limits |
|---|---|---|---|---|---|
| C01 | CASPs must submit MIDAS files every two weeks via SFTP, as UTF-8 JSON, max 500 MB | Instructions s.3.1–3.2 (line ~456 of `data/midas_instructions.txt`) | Another frequency can be agreed with the provider and NCAs | OBSERVED | — |
| C02 | Executions for all Art. 68(9) CASPs. Order book for trading platforms | Instructions s.1.2 | — | OBSERVED | Which service codes yield "executions" is my interpretation (two bounds) |
| C03 | Production starts after UAT and NCA approval. No uniform start date | Instructions s.4.1.4. Seqlense note (2026-11-03) | — | OBSERVED / REPORTED | — |
| C04 | 26 validation rules: FIL-101/102, MET-001–016, QUA-001–008 | Instructions Annex 3 | — | OBSERVED | — |
| C05 | Duplicates are checked against the entire MIDAS history | Instructions s.3.5.4.3 | — | OBSERVED | — |
| C06 | Unchanged resubmission needs ≥3 business days' email notice. Corrections need an advance email | Instructions s.3.5.4.2–3 | — | OBSERVED | — |
| C07 | Feedback is a 17-column CSV. ESMA sample has 27 rows | `ESMA65-955014868-17734` CSV header. T04 | — | OBSERVED | — |
| C08 | Phase 1 excludes personal data | Instructions s.3.1 | Later phases may add identifiers | OBSERVED | — |
| C09 | Phase 1 "fully operational by 2027". Phase 2 Q4 2027, subject to Board | thedenouement.com summary of ESMA22-50751485-1673 | — | REPORTED | Primary work programme not fetched |
| C10 | 314–359 active CASPs have execution-type services. 21 trading platforms. 111 Art. 60 | T01 output | Register is "interim" and may lag | OBSERVED | Service-code interpretation |
| C11 | DTI allocation costs €186. Registry API €7,409–28,744/yr. No free operational tier | dtif.org/dti-fees (fetched 2026-11-07) | Free UAT API with limited records | OBSERVED (fetch-model summary) | Single fetch |
| C12 | Intellectum Lab: €4.9k snapshot, €15k–22k diagnostic, €45k–140k build, €5k–9k/month run. No named CASP customers | intellectumlab.com/digital-assets.html | — | OBSERVED (fetch-model summary) | Vendor asking price, not purchases |
| C13 | Bitpanda runs a regulatory reporting team handling "over 100 reports" | Solidus Labs podcast page | — | REPORTED | Secondary |
| C14 | Law firms market MIDAS assistance (d&a partners 2026-10-28, Kohler Gotzev 2026-10-27, Kadri 2026-11-03) | Search results | — | OBSERVED (search snippets) | Marketing ≠ demand |
| C15 | Qalypto and OriginStamp sell evidence integrity for ESMA-format data, not MIDAS submission | Search snippets | — | OBSERVED (snippets) | Not fetched in full |
| C16 | Solidus Labs says ESMA chose it (July 2025) as the sole MiCA trade-surveillance provider for NCAs | soliduslabs.com/research/mica-masters | MIDAS document lists European Dynamics as solution provider | REPORTED (vendor claim) | — |
| C17 | ESMA's schema rejects the timestamp format shown in ESMA's own field examples | T04: 0/3 examples match the `ISODateTime` pattern. T02: space format → FIL-102 | — | OBSERVED | ESMA's live validator not tested |
| C18 | Following QUA-006 (empty Segment MIC without TxId) fails the schema, because TradVn is required | T02 b2 → FIL-102. Schema `required` list | — | OBSERVED | Same |
| C19 | Under a literal reading, ESMA's order-book sample has 14 MET-013 and 3 MET-008 rejections | T02a | `NoPric`/NOAP may count as "populated". Equal timestamps may be accepted | INFERRED (interpretation-dependent) | — |
| C20 | A pre-validator from public artifacts is feasible for one engineer | T02 (14/17 + 3 schema escalations; 1.5k rec/s in Python) | Missed the prestated 90% expected-code bar | OBSERVED (prototype) | Synthetic mutations of samples, not CASP data |
| C21 | No public MIDAS tooling or productized vendor exists | A16, A17, A25 | Absence of evidence. Private or unindexed products possible | INFERRED | — |
| C22 | Small CASPs would pay €750–2,500/month | None | — | ASSUMED | Core unknown, test A-B1 |
