"""T03: How many obligated CASPs are plausible buyers of a third-party MIDAS pipeline?

Heuristic segmentation (labelled as such in the report):
  - Art. 60 notified entities (banks, investment firms, etc.) -> assumed to have existing regulatory
    reporting stacks or crypto-as-a-service providers; lower fit.
  - Large international groups (name match against a hand-written list) -> assumed to build in-house.
  - Remainder = candidate small/mid CASPs.
The brand list is an assumption; misclassification risk is reported, and the full remainder list is saved
so the classification can be audited.
"""
import csv
import io
import json
import pathlib
import re

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
rows = list(csv.DictReader(io.StringIO((DATA / "CASPS.csv").read_text(encoding="utf-8-sig"))))
CORE = set("bcde")
LARGE = re.compile(
    r"coinbase|kraken|payward|okx|okcoin|bybit|gemini|crypto\.com|foris|bitpanda|revolut|binance|bitstamp|bitvavo|"
    r"gate|kucoin|htx|robinhood|etoro|trade republic|circle|paxos|ripple|uphold|bitget|blockchain\.com|zero ?hash|"
    r"moonpay|anchorage|bitgo|boerse stuttgart|börse stuttgart|deutsche b(ö|oe)rse|clearstream|n26|scalable|"
    r"societe generale|société générale|bbva|santander|ing |commerzbank|dz bank|dekabank|raiffeisen|"
    r"unicredit|intesa|bnp|deutsche bank|sparkasse|volksbank|wise|paypal|nexo|bitfinex|mexc|bitmart|"
    r"backpack|hyperliquid|deribit|coinshares|21shares|swissquote|interactive brokers|saxo|degiro|flatex",
    re.I,
)


def codes(r):
    return {c.strip()[0] for c in r["ac_serviceCode"].split("|") if c.strip()}


core = {}
for r in rows:
    if not r["ac_authorisationEndDate"].strip() and codes(r) & CORE:
        core[r["ae_lei"]] = r

art60 = {k: r for k, r in core.items() if "60" in r["ac_legal_basis"] and "63" not in r["ac_legal_basis"]}
rest = {k: r for k, r in core.items() if k not in art60}
name = lambda r: (r["ae_commercial_name"] or r["ae_lei_name"]).strip()
large = {k: r for k, r in rest.items() if LARGE.search(name(r) + " " + r["ae_lei_name"])}
small = {k: r for k, r in rest.items() if k not in large}

out = {
    "core_execution_reporters": len(core),
    "art60_notified": len(art60),
    "art63_or_blank_basis": len(rest),
    "large_group_name_matches": len(large),
    "candidate_small_mid": len(small),
    "candidate_small_mid_trading_platforms": sum("b" in codes(r) for r in small.values()),
    "candidate_small_mid_by_state_top8": dict(
        sorted(
            {s: sum(r["ae_homeMemberState"] == s for r in small.values()) for s in {r["ae_homeMemberState"] for r in small.values()}}.items(),
            key=lambda kv: -kv[1],
        )[:8]
    ),
    "large_group_examples": sorted({name(r) for r in large.values()})[:40],
}
print(json.dumps(out, indent=1, ensure_ascii=False))
(pathlib.Path(__file__).with_name("t03_candidate_small_mid_casps.csv")).write_text(
    "lei,name,home_state,legal_basis,services\n"
    + "\n".join(
        f'{k},"{name(r)}",{r["ae_homeMemberState"]},"{r["ac_legal_basis"]}","{"".join(sorted(codes(r)))}"' for k, r in sorted(small.items(), key=lambda kv: name(kv[1]))
    )
    + "\n",
    encoding="utf-8",
)
