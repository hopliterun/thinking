"""T01: Who is obligated to report to MIDAS? Counts from ESMA's interim MiCA CASP register.

Source: https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv (downloaded to research/data/CASPS.csv).
MIDAS scope (Reporting Instructions ESMA65-955014868-17690, s.1.2): executions (auth.117) for CASPs under
MiCA Art. 68(9); order book (auth.118) for CASPs operating a trading platform (service code "b").
Which service codes produce *executions* is our interpretation, so two bounds are reported.
"""
import collections
import csv
import io
import json
import pathlib
import sys

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
rows = list(csv.DictReader(io.StringIO((DATA / "CASPS.csv").read_text(encoding="utf-8-sig"))))

def codes(r):
    return {c.strip()[0] for c in r["ac_serviceCode"].split("|") if c.strip()}

active = [r for r in rows if not r["ac_authorisationEndDate"].strip()]
leis_all = {r["ae_lei"] for r in rows}
leis_active = {r["ae_lei"] for r in active}

CORE = set("bcde")        # trading platform, exchange vs funds, exchange vs crypto, execution of orders
BROAD = CORE | set("fgi")  # + placing, reception/transmission, portfolio management

core = {r["ae_lei"]: r for r in active if codes(r) & CORE}
broad = {r["ae_lei"]: r for r in active if codes(r) & BROAD}
tp = {r["ae_lei"]: r for r in active if "b" in codes(r)}

legal = collections.Counter(r["ac_legal_basis"].strip() or "(blank)" for r in core.values())
by_state = collections.Counter(r["ae_homeMemberState"] for r in core.values())
last_update = max((r["ac_lastupdate"] for r in rows if r["ac_lastupdate"]), key=lambda d: d.split("/")[::-1])

out = {
    "register_rows": len(rows),
    "unique_leis": len(leis_all),
    "active_rows_no_end_date": len(active),
    "unique_active_leis": len(leis_active),
    "lower_bound_execution_reporters_bcde": len(core),
    "upper_bound_execution_reporters_bcdefgi": len(broad),
    "trading_platforms_b_orderbook_reporters": len(tp),
    "trading_platform_names": sorted(r["ae_commercial_name"] or r["ae_lei_name"] for r in tp.values()),
    "legal_basis_of_core": dict(legal.most_common()),
    "home_state_of_core_top10": dict(by_state.most_common(10)),
    "latest_ac_lastupdate": last_update,
}
print(json.dumps(out, indent=1, ensure_ascii=False))

# Sanity checks: a broken parse would give zero or absurd counts.
assert len(rows) > 100 and len(core) <= len(broad) <= len(leis_active), "parse sanity check failed"
sys.exit(0)
