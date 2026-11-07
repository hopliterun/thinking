"""MIDAS pre-validator probe (research prototype, not a product).

Implements the checks from ESMA MIDAS Reporting Instructions (ESMA65-955014868-17690, 21 Oct 2026),
Annex 3, that can be evaluated locally:
  FIL-101/102, MET-002..016 (record-level, as written in Annex 3), QUA-001/002/004/005/006/007/008.
Schema: official V1.0 JSON schemas from ESMA65-955014868-15160 (Nov 2025 zip).
Not implemented: QUA-003 (needs the paid DTIF registry), MET-003 (ranges are not published).

Each finding: (code, severity, record_index or None, field, detail).
"""
from __future__ import annotations

import json
import re
import sqlite3
import datetime as dt
from decimal import Decimal, InvalidOperation
from pathlib import Path

import jsonschema
from jsonschema import validators

DATA = Path(__file__).resolve().parents[1] / "data"
SCHEMAS = {
    "CryptoAssetRecordKeeping": DATA / "msgspec/CryptoAssetRecordKeepingReport-auth117-V1.0.schema.json",
    "CryptoAssetOrderBook": DATA / "msgspec/CryptoAssetOrderBookReport-auth118-V1.0.schema.json",
}
NAME_RE = re.compile(r"^(CryptoAssetRecordKeeping|CryptoAssetOrderBook)_(\d{2})(\d{2})(\d{4})_(\d+)_(\d+)\.json$")
TS_MS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}$")
FILLS = {"FILL", "PARF"}
ENUMS = {
    "BuySellInd": {"BUYI", "SELL"},
    "VldtyPrdCd": {"DAVY", "GTCV", "GTTV", "GTDV", "GTSV", "GATV", "GADV", "GASV", "IOCV", "FOKV"},
    "OrdrTpClssfctn": {"LMTO", "STOP"},
    "PssvOrAggrssvInd": {"PASV", "AGRE"},
    "EvtTp": {"NEWO", "TRIG", "REME", "REMA", "REMH", "CHME", "CHMO", "CAME", "CAMO", "REMO", "EXPI", "PARF", "FILL"},
}
MAX_FILE_BYTES = 500 * 1024 * 1024


def _mics() -> set[str]:
    import csv, io
    raw = (DATA / "ISO10383_MIC.csv").read_bytes().decode("utf-8-sig", errors="replace")
    return {r["MIC"] for r in csv.DictReader(io.StringIO(raw)) if r.get("STATUS") == "ACTIVE"}


MICS = _mics()


def dec(x):
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError):
        return None


def g(d, *path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def qty(node):
    return dec(g(node, "DgtlTknQty", "Unit"))


def price(node):
    return dec(g(node, "DgtlTknPric", "DgtlTknQty", "Unit"))


# ---------------------------------------------------------------- file level
def check_names(names: list[str]):
    """FIL-101 per file, plus batch completeness (missing parts make a submission incomplete)."""
    out, groups = [], {}
    for n in names:
        m = NAME_RE.match(n)
        ok = bool(m)
        if m:
            d, mo, y, pn, pm = map(int, m.groups()[1:])
            try:
                dt.date(y, mo, d)
            except ValueError:
                ok = False
            ok = ok and 1 <= pn <= pm
            if ok:
                groups.setdefault((m.group(1), m.group(2) + m.group(3) + m.group(4), pm), set()).add(pn)
        if not ok:
            out.append(("FIL-101", "FILE_REJECTION", None, n, "name does not match <FileType>_<DDMMYYYY>_<partN>_<partM>.json"))
    for (ft, date, pm), parts in groups.items():
        missing = sorted(set(range(1, pm + 1)) - parts)
        if missing:
            out.append(("BATCH-INCOMPLETE", "FILE_REJECTION", None, f"{ft}_{date}", f"missing parts {missing} of {pm}"))
    return out


def check_schema(doc: dict, file_type: str):
    schema = json.loads(SCHEMAS[file_type].read_text())
    v = validators.validator_for(schema)(schema)
    errs = list(v.iter_errors(doc))
    return [("FIL-102", "FILE_REJECTION", None, "/".join(map(str, e.absolute_path))[:120], e.message[:160]) for e in errs[:20]]


# ---------------------------------------------------------- executions auth.117
def exec_records(doc):
    return [t["New"] for t in doc["Document"]["CrptAsstRcrdKeepgRpt"]["Tx"] if "New" in t]


def check_executions(doc, lei: str, history: sqlite3.Connection | None = None, midnight_threshold=0.10):
    out = []
    recs = exec_records(doc)
    fmt_ref = None
    seen = set()
    for i, r in enumerate(recs):
        ts = g(r, "Tx", "TradDt") or ""
        q, p = qty(g(r, "Tx", "Qty") or {}), price(g(r, "Tx", "Pric") or {})
        for name, val in (("Quantity", q), ("Price", p)):
            if val is not None and val <= 0:
                out.append(("MET-004", "REJECTION", i, name, str(val)))
        shape = "ms" if TS_MS_RE.match(ts) else "other"
        fmt_ref = fmt_ref or shape
        if shape != "ms" or shape != fmt_ref:
            out.append(("MET-006", "REJECTION", i, "Trading date time", ts))
        venue = g(r, "Tx", "TradVn")
        if venue and venue not in MICS | {"XOFF", "XXXX"}:
            out.append(("QUA-002", "WARNING", i, "Trading platform for crypto-asset", venue))
        key = (venue, r.get("TxRcrdId"), g(r, "Tx", "TradPlcMtchgId"), ts)
        if key in seen:
            out.append(("MET-005", "REJECTION", i, "Execution unique key", "duplicate within file"))
        elif history is not None and history.execute("select 1 from exec_keys where lei=? and k=?", (lei, repr(key))).fetchone():
            out.append(("MET-005", "REJECTION", i, "Execution unique key", "duplicate of previously accepted record"))
        seen.add(key)
    # QUA-005: isolated print >= 1000% away from both neighbours, partitioned by price currency + venue.
    parts = {}
    for i, r in enumerate(recs):
        k = (g(r, "Tx", "Pric", "DgtlTknPric", "DgtlTknQty", "Idr", "DTIShrtNm"), g(r, "Tx", "TradVn"))
        parts.setdefault(k, []).append((g(r, "Tx", "TradDt"), i, price(g(r, "Tx", "Pric") or {})))
    for seq in parts.values():
        seq.sort()
        for (_, _, a), (_, i, b), (_, _, c) in zip(seq, seq[1:], seq[2:]):
            if a and b and c and min(a, c) > 0:
                far = lambda x, y: max(x, y) / min(x, y) >= 11  # 1,000% variance = 11x
                if far(a, b) and far(b, c) and not far(a, c):
                    out.append(("QUA-005", "WARNING", i, "Price", str(b)))
    mid = sum(1 for r in recs if (g(r, "Tx", "TradDt") or "").endswith("00:00:00.000"))
    if recs and mid / len(recs) > midnight_threshold:
        out.append(("QUA-008", "WARNING", None, "Trading date time", f"{mid}/{len(recs)} at midnight"))
    return out


# ---------------------------------------------------------- order book auth.118
def orders(doc):
    return doc["Document"]["CrptAsstOrdrBookRpt"]["OrdrRpt"]["New"]["Ordr"]


def check_orderbook(doc, lei: str, history: sqlite3.Connection | None = None, midnight_threshold=0.10):
    out = []
    recs = orders(doc)
    seen = set()
    for i, o in enumerate(recs):
        idd, od = o.get("OrdrIdData", {}), o.get("OrdrData", {})
        st = g(idd, "EvtTp", "Cd")
        txid = g(od, "TxData", "TxId")
        traded = qty(g(od, "TxData", "TraddQty") or {})
        txp = price(g(od, "TxData", "TxPric") or {})
        init = qty(g(od, "InstrData", "InitlQty") or {})
        rem = qty(g(od, "InstrData", "RmngQty") or {})
        lmt = price(g(od, "OrdrPrics", "LmtPric") or {})
        side = g(od, "InstrData", "BuySellInd")
        vcode = g(idd, "VldtyPrd", "VldtyPrdCd")
        vts, ts = idd.get("VldtyDtTm"), idd.get("TmStmp") or ""
        otype = g(od, "OrdrClssfctn", "OrdrTpClssfctn")
        pa = g(od, "TxData", "PssvOrAggrssvInd")
        seg = idd.get("TradVn")
        if init is not None and init <= 0:
            out.append(("MET-004", "REJECTION", i, "Initial quantity", str(init)))
        if lmt is not None and lmt <= 0:
            out.append(("MET-004", "REJECTION", i, "Limit price", str(lmt)))
        for f, v in (("Date and time", ts), ("Validity period and time", vts)):
            if v and not TS_MS_RE.match(v):
                out.append(("MET-006", "REJECTION", i, f, v))
        if vcode == "GTDV" and not vts:
            out.append(("MET-007", "REJECTION", i, "Validity period and time", "missing for GTDV"))
        if vts and ts and vts <= ts:
            out.append(("MET-008", "REJECTION", i, "Validity period and time", f"{vts} <= {ts}"))
        if st in FILLS and (not txid or rem is None or traded is None):
            out.append(("MET-009", "REJECTION", i, "Transaction identification code", "required for FILL/PARF"))
        if st not in FILLS and txid:
            out.append(("MET-010", "REJECTION", i, "Transaction identification code", f"must be empty for {st}"))
        if not txid and (traded is not None or txp is not None):
            out.append(("MET-011", "REJECTION", i, "Traded quantity / Transaction price", "populated without TxId"))
        if txid and traded is not None and init is not None and not (0 <= traded <= init):
            out.append(("MET-012", "REJECTION", i, "Traded quantity", f"{traded} vs initial {init}"))
        if st in FILLS and otype == "LMTO" and (lmt is None or txp is None):
            out.append(("MET-013", "REJECTION", i, "Limit price", "required for filled LMTO"))
        if rem is not None and init is not None and not (0 <= rem <= init):
            out.append(("MET-014", "REJECTION", i, "Remaining quantity", f"{rem} vs initial {init}"))
        if st in FILLS and lmt is not None and txid:
            if txp is None or txp <= 0 or (side == "BUYI" and txp > lmt) or (side == "SELL" and txp < lmt):
                out.append(("MET-015", "REJECTION", i, "Transaction price", f"{txp} vs limit {lmt} ({side})"))
        for f, v in (("BuySellInd", side), ("VldtyPrdCd", vcode), ("OrdrTpClssfctn", otype), ("PssvOrAggrssvInd", pa), ("EvtTp", st)):
            if v is not None and v not in ENUMS[f]:
                out.append(("MET-016", "REJECTION", i, f, v))
        if len(idd.get("OrdrId") or "") > 50 or len(txid or "") > 52:
            out.append(("QUA-001", "WARNING", i, "Order/Transaction identification code", "too long"))
        if txid and seg and seg not in MICS | {"XOFF", "XXXX"}:
            out.append(("QUA-002", "WARNING", i, "Segment MIC", seg))
        if not txid and seg:
            out.append(("QUA-006", "WARNING", i, "Segment MIC", f"{seg} populated without TxId ({st})"))
        if pa and st not in FILLS:
            out.append(("QUA-007", "WARNING", i, "Passive or aggressive indicator", f"{pa} for {st}"))
        key = (idd.get("OrdrId"), ts, st, txid, seg, lei)
        if key in seen:
            out.append(("MET-005", "REJECTION", i, "Order unique key", "duplicate within file"))
        elif history is not None and history.execute("select 1 from order_keys where lei=? and k=?", (lei, repr(key))).fetchone():
            out.append(("MET-005", "REJECTION", i, "Order unique key", "duplicate of previously accepted record"))
        seen.add(key)
    n = len(recs)
    if n:
        canc = sum(1 for o in recs if g(o, "OrdrIdData", "EvtTp", "Cd") in {"CAME", "CAMO"})
        buys = sum(1 for o in recs if g(o, "OrdrData", "InstrData", "BuySellInd") == "BUYI")
        if not (0.05 <= canc / n <= 0.95):
            out.append(("QUA-004", "WARNING", None, "Status", f"cancelled share {canc}/{n}"))
        if max(buys, n - buys) / n > 0.90:
            out.append(("QUA-004", "WARNING", None, "Side", f"buy share {buys}/{n}"))
        mid = sum(1 for o in recs if (g(o, "OrdrIdData", "TmStmp") or "").endswith("00:00:00.000"))
        if mid / n > midnight_threshold:
            out.append(("QUA-008", "WARNING", None, "Date and time", f"{mid}/{n} at midnight"))
    return out


def history_db(path=":memory:"):
    con = sqlite3.connect(path)
    con.execute("create table if not exists exec_keys(lei text, k text, primary key(lei,k))")
    con.execute("create table if not exists order_keys(lei text, k text, primary key(lei,k))")
    return con


def remember(con, doc, file_type, lei, rejected_idx: set[int]):
    """Store keys of accepted records so later submissions can be checked for MIDAS-wide duplicates."""
    if file_type == "CryptoAssetRecordKeeping":
        for i, r in enumerate(exec_records(doc)):
            if i not in rejected_idx:
                k = (g(r, "Tx", "TradVn"), r.get("TxRcrdId"), g(r, "Tx", "TradPlcMtchgId"), g(r, "Tx", "TradDt"))
                con.execute("insert or ignore into exec_keys values(?,?)", (lei, repr(k)))
    else:
        for i, o in enumerate(orders(doc)):
            if i not in rejected_idx:
                idd = o["OrdrIdData"]
                k = (idd.get("OrdrId"), idd.get("TmStmp"), g(idd, "EvtTp", "Cd"), g(o, "OrdrData", "TxData", "TxId"), idd.get("TradVn"), lei)
                con.execute("insert or ignore into order_keys values(?,?)", (lei, repr(k)))


def validate(name: str, doc: dict, lei: str, history=None):
    findings = check_names([name])
    m = NAME_RE.match(name)
    ft = m.group(1) if m else ("CryptoAssetOrderBook" if "CrptAsstOrdrBookRpt" in doc.get("Document", {}) else "CryptoAssetRecordKeeping")
    if findings:
        return ft, findings
    sf = check_schema(doc, ft)
    if sf:
        return ft, sf  # whole file rejected, no record processing
    rec = check_executions(doc, lei, history) if ft == "CryptoAssetRecordKeeping" else check_orderbook(doc, lei, history)
    return ft, rec
