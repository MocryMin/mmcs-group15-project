import json, statistics, urllib.request

def mid(day):
    url = ("https://data.elexon.co.uk/bmrs/api/v1/datasets/MID?from=" + day + "T00%3A00Z&to="
           + day + "T23%3A59Z&format=json")
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)

for day in ("2020-01-01", "2023-05-09"):
    data = mid(day)
    rows = data.get("data", data) if isinstance(data, dict) else data
    by_hh = {}
    for rec in rows:
        ts = rec.get("settlementPeriod") or rec.get("startTime")
        key = rec.get("startTime") or (day + " SP" + str(ts))
        by_hh.setdefault(key, []).append((float(rec["price"]), float(rec.get("volume", 0))))
    hh_active, flat = [], []
    for k, vals in by_hh.items():
        flat.extend(p for p, v in vals)
        num = sum(p * v for p, v in vals if v > 0)
        den = sum(v for _, v in vals if v > 0)
        if den > 0:
            hh_active.append(num / den)
    print(day, "records", len(rows), "half-hours", len(by_hh),
          "live active-vw day mean=%.4f" % statistics.mean(hh_active),
          "live flat mean over all records=%.4f" % statistics.mean(flat))
