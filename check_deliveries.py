"""Group SAP delivery rows into deliveries and flag problems (never crashes on bad rows)."""
import csv
import sys
from collections import OrderedDict

CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "SAP_delivery_sample.csv"
UNKNOWN_SHOPS = {"100999"}   # assumption from the brief: LMS knows every shop except 0000100999


def norm(code):
    """Compare codes without leading zeros: Excel/Sheets often strip them (0000100999 -> 100999)."""
    return code.strip().lstrip("0")


def parse_weight(raw):
    """Return weight as float, or None if blank / not a number / not positive."""
    try:
        value = float((raw or "").strip().replace(",", ""))
    except ValueError:
        return None
    return value if value > 0 else None


deliveries = OrderedDict()
with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        d = deliveries.setdefault(row["VBELN"].strip(), {
            "shop_code": row["KUNNR"].strip(), "shop_name": row["NAME1"].strip(),
            "items": 0, "weight": 0.0, "problems": []})
        d["items"] += 1
        w = parse_weight(row.get("BRGEW"))
        if w is None:
            d["problems"].append(f"item {row['POSNR'].strip()} ({row['MATNR'].strip()}): missing/invalid weight")
        else:
            d["weight"] += w
        if norm(row["KUNNR"]) in UNKNOWN_SHOPS and "unknown shop" not in d["problems"]:
            d["problems"].append("unknown shop")

print(f"{'Delivery':<12}{'Shop':<40}{'Items':>6}{'Weight (kg)':>14}  Status")
ok = flagged = 0
for number, d in deliveries.items():
    has_missing_weight = any("weight" in p for p in d["problems"])
    weight_txt = "n/a" if has_missing_weight else f"{d['weight']:.2f}"
    shop = f"{d['shop_name']} ({norm(d['shop_code'])})"
    if d["problems"]:
        flagged += 1
        status = "FLAGGED - " + "; ".join(d["problems"])
    else:
        ok += 1
        status = "OK"
    print(f"{number.strip().zfill(10):<12}{shop:<40}{d['items']:>6}{weight_txt:>14}  {status}")
print(f"\n{len(deliveries)} deliveries: {ok} OK, {flagged} flagged")