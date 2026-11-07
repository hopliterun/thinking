"""T04: Internal consistency of ESMA's own MIDAS artifacts (each check is a direct, reproducible observation).

Prestated: if ESMA's artifacts were mutually consistent, a CASP could rely on them alone and the value of a
third-party "interpretation + pre-validation" layer would be lower.
"""
import csv
import io
import json
import re
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data"
txt = (D / "midas_instructions.txt").read_text()
out = {}

# 1. Field-level examples in the instructions vs the schema's ISODateTime pattern (requires 'T').
examples = re.findall(r"Example\s+(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\.\d{3})", txt)
schema = json.loads((D / "msgspec/CryptoAssetRecordKeepingReport-auth117-V1.0.schema.json").read_text())
iso_pat = next(v["pattern"] for k, v in (schema.get("$defs") or schema["definitions"]).items() if k.startswith("ISODateTime"))
out["instruction_timestamp_examples"] = examples
out["examples_matching_schema_ISODateTime"] = sum(bool(re.match(iso_pat, e)) for e in examples)

# 2. Feedback sample: RecordRef values in float/scientific notation (precision lost, e.g. 1.77932E+18).
fb = list(csv.DictReader(io.StringIO((D / "ESMA65-955014868-17734_MIDAS_Feedback_File_Sample.csv").read_text(encoding="utf-8-sig"))))
refs = [r["RecordRef"] for r in fb if r["RecordRef"]]
out["feedback_rows"] = len(fb)
out["feedback_rows_with_recordref"] = len(refs)
out["recordref_in_scientific_notation"] = sum(bool(re.search(r"E\+\d+$", x)) for x in refs)
out["distinct_recordref_values"] = sorted(set(refs))[:6]

# 3. Schema files referenced by Annex 2 are not among the MIDAS downloads (they live in the Nov 2025 zip).
out["annex2_references_schema_files"] = sorted(set(re.findall(r"(\w+-auth11[78]-V1\.0\.schema\.json)", txt.replace("\n", "").replace(" ", ""))))
out["schema_files_in_2025_zip"] = sorted(p.name for p in (D / "msgspec").glob("*.schema.json"))

print(json.dumps(out, indent=1))
Path(__file__).with_name("t04_output.json").write_text(json.dumps(out, indent=1))
