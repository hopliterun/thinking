"""T02: Can a small team build a working MIDAS pre-validator from public ESMA artifacts, and do the
public artifacts agree with each other?

Prestated discriminators (written before running):
  * Feasibility PASS if the prototype detects >= 90% of targeted single-rule mutations of ESMA's own samples
    with the expected code and no spurious rejections on the unmodified samples.
  * "Spec friction" is evidenced if ESMA's own published samples/filenames/text trigger ESMA's own rules
    under a literal reading. Absence of such conflicts would weaken the "pre-validation is valuable" claim.
Limits: synthetic mutations of ESMA samples are not CASP production data; ESMA's real validator may
interpret rules differently; passing here does not prove acceptance in UAT.
"""
import copy
import json
import time
from collections import Counter
from pathlib import Path

import midas_prevalidator as mv

D = mv.DATA
LEI = "R0MUWSFPU8XXXO8K5P83"  # LEI used in ESMA's samples
RK = json.loads((D / "ESMA65-955014868-17735_MIDAS_CryptoAssetRecordKeeping.json").read_text())
OB = json.loads((D / "ESMA65-955014868-17736_MIDAS_CryptoAssetOrderBook.json").read_text())
RK_NAME, OB_NAME = "CryptoAssetRecordKeeping_21052026_1_1.json", "CryptoAssetOrderBook_21052026_1_1.json"
result = {}

# (a) ESMA's own artifacts under a literal reading
annex4_name = "CryptoAssetRecordKeeping_21052026_part1.json"  # filename shown in Annex 4 of the instructions
result["a_annex4_sample_filename_FIL101"] = [f[0] for f in mv.check_names([annex4_name])]
for label, name, doc in (("rk", RK_NAME, RK), ("ob", OB_NAME, OB)):
    ft, f = mv.validate(name, doc, LEI)
    result[f"a_esma_sample_{label}_findings"] = dict(Counter(x[0] for x in f))
    result[f"a_esma_sample_{label}_examples"] = [list(map(str, x)) for x in f[:3]]
n_orders = len(mv.orders(OB))
result["a_ob_sample_records"] = n_orders
result["a_rk_sample_records"] = len(mv.exec_records(RK))

# MET-006's example format ("YYYY-MM-DD HH:mm:ss.fff", space separator) vs the schema's ISO 'T' pattern
rk_space = copy.deepcopy(RK)
for t in rk_space["Document"]["CrptAsstRcrdKeepgRpt"]["Tx"]:
    t["New"]["Tx"]["TradDt"] = t["New"]["Tx"]["TradDt"].replace("T", " ")
result["a_met006_text_format_outcome"] = sorted({x[0] for x in mv.validate(RK_NAME, rk_space, LEI)[1]})


# (b) targeted single-rule mutations
def ob_mut(fn):
    d = copy.deepcopy(OB)
    fn(mv.orders(d))
    return d


def rk_mut(fn):
    d = copy.deepcopy(RK)
    fn([t["New"] for t in d["Document"]["CrptAsstRcrdKeepgRpt"]["Tx"]])
    return d


def rk_dup():
    d = copy.deepcopy(RK)
    txs = d["Document"]["CrptAsstRcrdKeepgRpt"]["Tx"]
    txs.append(copy.deepcopy(txs[3]))
    return d


def first(recs, pred):
    return next(r for r in recs if pred(r))


fill = lambda o: o["OrdrIdData"]["EvtTp"]["Cd"] in ("FILL", "PARF")
newo = lambda o: o["OrdrIdData"]["EvtTp"]["Cd"] == "NEWO"
U = lambda node: node["DgtlTknQty"]
P = lambda node: node["DgtlTknPric"]["DgtlTknQty"]

TXPRIC = copy.deepcopy(next(o for o in mv.orders(OB) if fill(o))["OrdrData"]["TxData"]["TxPric"])
MUTATIONS = {
    "MET-004": ("rk", lambda rs: U(rs[5]["Tx"]["Qty"]).__setitem__("Unit", "0")),
    "MET-005": ("rk-dup", None),
    "MET-006": ("rk", lambda rs: rs[7]["Tx"].__setitem__("TradDt", rs[7]["Tx"]["TradDt"][:19] + ".5")),
    "QUA-002": ("rk", lambda rs: rs[9]["Tx"].__setitem__("TradVn", "ZZZZ")),
    "QUA-005": ("rk", lambda rs: P(rs[20]["Tx"]["Pric"]).__setitem__("Unit", str(float(P(rs[20]["Tx"]["Pric"])["Unit"]) * 50))),
    "QUA-008": ("rk", lambda rs: [r["Tx"].__setitem__("TradDt", r["Tx"]["TradDt"][:10] + "T00:00:00.000") for r in rs[:200]]),
    "MET-007": ("ob", lambda os: (first(os, newo)["OrdrIdData"]["VldtyPrd"].__setitem__("VldtyPrdCd", "GTDV"), first(os, newo)["OrdrIdData"].pop("VldtyDtTm", None))),
    "MET-008": ("ob", lambda os: os[0]["OrdrIdData"].__setitem__("VldtyDtTm", "2026-05-20T00:00:00.000")),
    "MET-009": ("ob", lambda os: first(os, fill)["OrdrData"]["TxData"].pop("TxId")),
    "MET-010": ("ob", lambda os: first(os, newo)["OrdrData"].__setitem__("TxData", {"TxId": "X1", "TxPric": copy.deepcopy(TXPRIC)})),
    "MET-012": ("ob", lambda os: U(first(os, fill)["OrdrData"]["TxData"]["TraddQty"]).__setitem__("Unit", "999999")),
    "MET-014": ("ob", lambda os: U(first(os, fill)["OrdrData"]["InstrData"]["RmngQty"]).__setitem__("Unit", "999999")),
    "MET-015": ("ob", lambda os: P(first(os, fill)["OrdrData"]["TxData"]["TxPric"]).__setitem__("Unit", "99999")),
    "MET-016": ("ob", lambda os: first(os, fill)["OrdrData"]["TxData"].__setitem__("PssvOrAggrssvInd", "XXXX")),
    "QUA-001": ("ob", lambda os: os[0]["OrdrIdData"].__setitem__("OrdrId", "O" * 51)),
    # QUA-007 cannot occur alone: the schema requires TxPric inside TxData, which then also breaks MET-011.
    "QUA-007": ("ob", lambda os: first(os, newo)["OrdrData"].__setitem__("TxData", {"PssvOrAggrssvInd": "AGRE", "TxPric": copy.deepcopy(TXPRIC)})),
    "MET-011": ("ob", lambda os: first(os, newo)["OrdrData"].__setitem__("TxData", {"TxPric": copy.deepcopy(TXPRIC)})),
}
base = {"rk": Counter(x[0] for x in mv.validate(RK_NAME, RK, LEI)[1]), "ob": Counter(x[0] for x in mv.validate(OB_NAME, OB, LEI)[1])}
mut_results = {}
for code, (kind, fn) in MUTATIONS.items():
    doc = rk_dup() if kind == "rk-dup" else rk_mut(fn) if kind == "rk" else ob_mut(fn)
    kind = kind[:2]
    codes = Counter(x[0] for x in mv.validate(RK_NAME if kind == "rk" else OB_NAME, doc, LEI)[1])
    detected = codes[code] > base[kind][code]
    mut_results[code] = {"detected": detected, "new_codes": sorted(c for c in codes if codes[c] > base[kind][c])}
result["b_mutations"] = mut_results
hits = sum(v["detected"] for v in mut_results.values())
result["b_detection_rate"] = f"{hits}/{len(mut_results)}"
# Mutations the schema itself catches end as FIL-102 (whole file) instead of the record-level code.
result["b_escalated_to_FIL102"] = sorted(c for c, v in mut_results.items() if "FIL-102" in v["new_codes"])

# (b2) schema vs Annex 3 severity conflicts, tested directly
def drop_segment_mic_without_txid(os):
    for o in os:
        if not mv.g(o, "OrdrData", "TxData", "TxId"):
            o["OrdrIdData"].pop("TradVn", None)

result["b2_follow_QUA006_drop_segment_mic"] = sorted({x[0] for x in mv.validate(OB_NAME, ob_mut(drop_segment_mic_without_txid), LEI)[1]})
result["b2_QUA001_overlong_order_id"] = sorted({x[0] for x in mv.validate(OB_NAME, ob_mut(MUTATIONS["QUA-001"][1]), LEI)[1]})
result["b2_MET016_bad_enum"] = sorted({x[0] for x in mv.validate(OB_NAME, ob_mut(MUTATIONS["MET-016"][1]), LEI)[1]})
result["b2_MET007_gtdv_without_validity_time"] = sorted({x[0] for x in mv.validate(OB_NAME, ob_mut(MUTATIONS["MET-007"][1]), LEI)[1]})

# (c) resubmission against history: accepted records resent unchanged are MIDAS-wide duplicates
con = mv.history_db()
_, f1 = mv.validate(RK_NAME, RK, LEI, con)
mv.remember(con, RK, "CryptoAssetRecordKeeping", LEI, {x[2] for x in f1 if x[1] == "REJECTION"})
_, f2 = mv.validate("CryptoAssetRecordKeeping_22052026_1_1.json", RK, LEI, con)
result["c_resubmission_duplicates"] = sum(1 for x in f2 if x[0] == "MET-005")

# (d) batch completeness + throughput on a scaled file (records replicated with unique ids)
result["d_batch_missing_part"] = [x[0] for x in mv.check_names(["CryptoAssetOrderBook_21052026_1_3.json", "CryptoAssetOrderBook_21052026_3_3.json"])]
big = copy.deepcopy(RK)
txs = big["Document"]["CrptAsstRcrdKeepgRpt"]["Tx"]
proto = copy.deepcopy(txs)
for k in range(1, 40):
    for t in proto:
        c = copy.deepcopy(t)
        c["New"]["TxRcrdId"] = f'{c["New"]["TxRcrdId"]}{k:03d}'
        txs.append(c)
raw = json.dumps(big)
t0 = time.perf_counter()
_, fb = mv.validate(RK_NAME, json.loads(raw), LEI)
el = time.perf_counter() - t0
n = len(txs)
result["d_scaled_records"] = n
result["d_bytes_per_record_compact"] = round(len(raw) / n)
result["d_records_per_500MB_file_est"] = int(500 * 1024 * 1024 / (len(raw) / n))
result["d_validate_seconds"] = round(el, 2)
result["d_records_per_second"] = int(n / el)
result["d_findings_on_scaled"] = dict(Counter(x[0] for x in fb))

print(json.dumps(result, indent=1))
Path(__file__).with_name("t02_output.json").write_text(json.dumps(result, indent=1))
