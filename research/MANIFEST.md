# Manifest

| Path | What it is |
|---|---|
| `REPORT.md` | Decision report (verdict, evidence, product, commercial path, tests, risks, diagnostic) |
| `LEDGER.md` | Action ledger and claim ledger |
| `fetch_data.sh` | Downloads the public inputs into `data/` and checks the ESMA MIDAS artifacts against the SHA-256 values seen on 2026-11-07 |
| `requirements.txt` | Python dependency for the tests |
| `tests/midas_prevalidator.py` | Research prototype: FIL/MET/QUA checks from ESMA's MIDAS Annex 3 plus official V1.0 schemas, with a duplicate store across submissions |
| `tests/t01_casp_register.py`, `t01_output.json` | Obligated-CASP counts from ESMA's interim register |
| `tests/t02_prevalidator_probe.py`, `t02_output.json` | ESMA samples under ESMA's rules, mutation suite, history duplicates, throughput |
| `tests/t03_buyer_segmentation.py`, `t03_output.json`, `t03_candidate_small_mid_casps.csv` | Heuristic buyer-pool segmentation, with the full remainder list for audit |
| `tests/t04_artifact_consistency.py`, `t04_output.json` | Internal-consistency checks of ESMA's MIDAS artifacts |

`data/` is not committed (third-party files). Recreate it, then run the tests:

```bash
cd research && ./fetch_data.sh          # needs curl, unzip, pdftotext
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cd tests && for t in t01_casp_register t02_prevalidator_probe t03_buyer_segmentation t04_artifact_consistency; do python $t.py; done
```

`t02` takes about 20 s. Register-based outputs (`t01`, `t03`) will drift as ESMA updates `CASPS.csv`.
