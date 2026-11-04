# -*- coding: utf-8 -*-
"""Comprehensive audit of every dataset disclosed by the project (repo root CSVs).

Read-only. Writes JSON + printed summary. No third-party libs.
Usage: python audit_all_project_data.py <repo_root> <out_json>
"""
import csv
import hashlib
import io
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "audit_all_data.json"))

FILES = [
    "daily_generation_by_fuel.csv",
    "daily_generation_total.csv",
    "daily_demand.csv",
    "wind_farm_generation.csv",
    "daily_market_index_price.csv",
]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(name):
    path = os.path.join(REPO, name)
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    crlf = raw.count(b"\r\n")
    lf_total = raw.count(b"\n")
    info = {
        "path": name,
        "bytes": len(raw),
        "sha256": sha256(path),
        "bom": raw.startswith(b"\xef\xbb\xbf"),
        "crlf": crlf,
        "bare_lf": lf_total - crlf,
        "ends_with_newline": raw.endswith(b"\n"),
        "lines": len(text.splitlines()),
    }
    rows = list(csv.reader(io.StringIO(text, newline="")))
    info["header"] = rows[0]
    body = rows[1:]
    info["data_rows"] = len(body)
    info["ncol_hist"] = dict(Counter(len(r) for r in body))
    info["empty_cells"] = sum(1 for r in body for c in r if c.strip() == "")
    return info, body


def parse_dates(rows, idx, fmt_check=None):
    ds = []
    bad = []
    for r in rows:
        v = r[idx].strip()
        if fmt_check and not fmt_check.match(v):
            bad.append(v)
        ds.append(v[:10])
    return ds, bad


def missing_calendar(dates, lo, hi):
    import datetime as dt
    have = set(dates)
    cur = dt.date.fromisoformat(lo)
    end = dt.date.fromisoformat(hi)
    miss = []
    while cur <= end:
        s = cur.isoformat()
        if s not in have:
            miss.append(s)
        cur += dt.timedelta(days=1)
    return miss


def num_stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {}
    s = sorted(vals)
    n = len(s)

    def q(p):
        return s[min(n - 1, max(0, int(round(p * (n - 1)))))]

    return {
        "n": n,
        "min": s[0],
        "p01": q(0.01),
        "p05": q(0.05),
        "p25": q(0.25),
        "p50": q(0.5),
        "p75": q(0.75),
        "p95": q(0.95),
        "p99": q(0.99),
        "max": s[-1],
        "mean": round(statistics.fmean(s), 6),
    }


def runs(sorted_dates):
    """Group consecutive ISO dates into [start, end, ndays] blocks."""
    import datetime as dt
    out = []
    cur = None
    prev = None
    for d in sorted_dates:
        day = dt.date.fromisoformat(d)
        if cur is None:
            cur = [d, d, 1]
        elif (day - prev).days == 1:
            cur[1] = d
            cur[2] += 1
        else:
            out.append(cur)
            cur = [d, d, 1]
        prev = day
    if cur:
        out.append(cur)
    return out


def year_of(d):
    return d[:4]


res = {"repo": REPO, "inventory": {}, "series": {}, "cross": {}, "manifest_check": {}, "repair": {}}
for f in FILES:
    info, body = inventory(f)
    res["inventory"][f] = info
    print("[inv]", f, info["bytes"], "B", info["data_rows"], "rows", "cols", info["header"],
          "crlf=%d bare_lf=%d" % (info["crlf"], info["bare_lf"]), "empty_cells=%d" % info["empty_cells"])

# ---------------------------------------------------------------- generation by fuel
info, body = inventory("daily_generation_by_fuel.csv")
gen = defaultdict(dict)          # date -> psr -> MW
dups = []
fuels = Counter()
nonint = 0
neg = defaultdict(list)
for r in body:
    d, p, mw = r[0].strip(), r[1].strip(), r[2].strip()
    v = float(mw)
    if not v.is_integer():
        nonint += 1
    if v < 0:
        neg[p].append((d, v))
    if p in gen[d]:
        dups.append((d, p))
    gen[d][p] = v
    fuels[p] += 1
gdates = sorted(gen)
gfuels = sorted(fuels)
res["series"]["generation_by_fuel"] = {
    "distinct_dates": len(gdates),
    "first": gdates[0],
    "last": gdates[-1],
    "fuels": {k: v for k, v in sorted(fuels.items())},
    "duplicate_date_fuel": dups[:50],
    "n_duplicate": len(dups),
    "non_integer_values": nonint,
    "negative_by_fuel": {k: {"n": len(v), "min": min(x[1] for x in v)} for k, v in neg.items()},
    "missing_calendar_days": missing_calendar(gdates, "2020-01-01", "2026-09-17"),
    "date_format_bad": [d for d in gdates if not DATE_RE.match(d)][:20],
    "rows_per_date_hist": dict(Counter(len(gen[d]) for d in gdates)),
    "sorted_by_date": gdates == sorted(gdates),
}
days_g = set(gdates)

# per-fuel coverage and zeros
per_fuel = {}
all_zero_days = []
nonwind_zero_days = []   # every non-wind fuel exactly 0
for p in gfuels:
    vals = [(d, gen[d][p]) for d in gdates if p in gen[d]]
    zeros = [d for d, v in vals if v == 0]
    per_fuel[p] = {
        "days_present": len(vals),
        "missing_days": len(gdates) - len(vals),
        "zero_days": len(zeros),
        "stats": num_stats([v for _, v in vals]),
    }
for d in gdates:
    row = gen[d]
    if all(v == 0 for v in row.values()):
        all_zero_days.append(d)
    nw = [p for p in row if "Wind" not in p]
    if nw and all(row[p] == 0 for p in nw):
        nonwind_zero_days.append(d)
res["series"]["generation_by_fuel"]["per_fuel"] = per_fuel
res["series"]["generation_by_fuel"]["all_zero_days"] = {
    "n": len(all_zero_days), "dates": all_zero_days, "runs": runs(all_zero_days)}
res["series"]["generation_by_fuel"]["all_nonwind_zero_days"] = {
    "n": len(nonwind_zero_days), "dates": nonwind_zero_days, "runs": runs(nonwind_zero_days)}

# ---------------------------------------------------------------- generation total
info, body = inventory("daily_generation_total.csv")
tot = {}
dup_t = []
for r in body:
    d, v = r[0].strip(), float(r[1])
    if d in tot:
        dup_t.append(d)
    tot[d] = v
tdates = sorted(tot)
res["series"]["generation_total"] = {
    "distinct_dates": len(tdates),
    "first": tdates[0],
    "last": tdates[-1],
    "n_duplicate": len(dup_t),
    "non_integer_values": sum(1 for v in tot.values() if not v.is_integer()),
    "zeros": sum(1 for v in tot.values() if v == 0),
    "negatives": [d for d, v in tot.items() if v < 0],
    "missing_calendar_days": missing_calendar(tdates, "2020-01-01", "2026-09-17"),
    "stats": num_stats(list(tot.values())),
    "identical_date_set_to_by_fuel": set(tdates) == days_g,
}

# identity: sum(fuels) == total
mism = []
for d in sorted(set(tdates) & days_g):
    s = sum(gen[d].values())
    if abs(s - tot[d]) > 1e-9:
        mism.append((d, round(s, 6), tot[d], round(s - tot[d], 6)))
res["cross"]["fuel_sum_equals_total"] = {
    "n_compared": len(set(tdates) & days_g),
    "n_mismatch": len(mism),
    "max_abs_diff": max([abs(m[3]) for m in mism], default=0.0),
    "examples": mism[:20],
}

# ---------------------------------------------------------------- demand
info, body = inventory("daily_demand.csv")
dem = {}
dup_dem = []
rtypes = Counter()
ts_bad = []
nonmidnight = []
for r in body:
    rt, ts, v = r[0].strip(), r[1].strip(), r[2].strip()
    rtypes[rt] += 1
    if not TS_RE.match(ts):
        ts_bad.append(ts)
    if not ts.endswith("T00:00:00Z"):
        nonmidnight.append(ts)
    d = ts[:10]
    if d in dem:
        dup_dem.append((d, rt, dem[d][0]))
    dem[d] = (rt, float(v))
ddates = sorted(dem)
res["series"]["demand"] = {
    "distinct_dates": len(ddates),
    "first": ddates[0],
    "last": ddates[-1],
    "record_types": dict(rtypes),
    "timestamp_format_bad": ts_bad[:20],
    "non_midnight_timestamps": {"n": len(nonmidnight), "examples": nonmidnight[:20]},
    "n_duplicate_date": len(dup_dem),
    "missing_calendar_days": missing_calendar(ddates, "2020-01-01", "2026-09-17"),
    "zeros": [d for d in ddates if dem[d][1] == 0],
    "negatives": [(d, dem[d][1]) for d in ddates if dem[d][1] < 0],
    "non_integer_values": sum(1 for d in ddates if not dem[d][1].is_integer()),
    "stats": num_stats([dem[d][1] for d in ddates]),
    "top10": sorted(((dem[d][1], d) for d in ddates), reverse=True)[:10],
    "bottom10": sorted(((dem[d][1], d) for d in ddates))[:10],
}

# ---------------------------------------------------------------- wind farm
info, body = inventory("wind_farm_generation.csv")
wf = {}
dup_w = []
dec_places = 0
for r in body:
    d, v = r[0].strip(), r[1].strip()
    if d in wf:
        dup_w.append(d)
    wf[d] = float(v)
    if "." in v:
        dec_places = max(dec_places, len(v.split(".")[1]))
wdates = sorted(wf)
res["series"]["wind_farm"] = {
    "distinct_dates": len(wdates),
    "first": wdates[0],
    "last": wdates[-1],
    "n_duplicate": len(dup_w),
    "max_decimal_places": dec_places,
    "zeros": [d for d in wdates if wf[d] == 0],
    "negatives": [(d, wf[d]) for d in wdates if wf[d] < 0],
    "missing_calendar_days": missing_calendar(wdates, "2020-01-01", "2026-09-18"),
    "stats": num_stats(list(wf.values())),
    "dates_outside_generation": sorted(set(wdates) - days_g),
}

# wind vs fuel columns
wind_cols = [p for p in gfuels if "Wind" in p]
cmp_rows = []
for d in sorted(set(wdates) & days_g):
    s = sum(gen[d].get(p, 0.0) for p in wind_cols)
    cmp_rows.append((d, wf[d], s, wf[d] - s))
diffs = [abs(c[3]) for c in cmp_rows]
res["cross"]["wind_farm_vs_fuel_wind"] = {
    "wind_columns": wind_cols,
    "n_compared": len(cmp_rows),
    "n_exact": sum(1 for c in cmp_rows if abs(c[3]) < 1e-6),
    "n_within_1MW": sum(1 for c in cmp_rows if abs(c[3]) < 1.0),
    "max_abs_diff": max(diffs) if diffs else None,
    "mean_abs_diff": round(statistics.fmean(diffs), 4) if diffs else None,
    "worst20": sorted(((abs(c[3]), c[0], c[3]) for c in cmp_rows), reverse=True)[:20],
    "sign_counts": {
        "wf_gt_fuel": sum(1 for c in cmp_rows if c[3] > 1e-6),
        "wf_lt_fuel": sum(1 for c in cmp_rows if c[3] < -1e-6),
    },
}

# ---------------------------------------------------------------- price
info, body = inventory("daily_market_index_price.csv")
pr = {}
dup_p = []
for r in body:
    d, a, b = r[0].strip(), float(r[1]), float(r[2])
    if d in pr:
        dup_p.append(d)
    pr[d] = (a, b)
pdates = sorted(pr)
dev = []
for d in pdates:
    a, b = pr[d]
    dev.append((abs(b - 24.0 * a), d, a, b))
dev.sort(reverse=True)
res["series"]["price"] = {
    "distinct_dates": len(pdates),
    "first": pdates[0],
    "last": pdates[-1],
    "n_duplicate": len(dup_p),
    "missing_calendar_days": missing_calendar(pdates, "2020-01-01", "2026-09-17"),
    "identical_date_set_to_total": set(pdates) == set(tdates),
    "avg_price_MWh_stats": num_stats([pr[d][0] for d in pdates]),
    "avg_price_MWday_stats": num_stats([pr[d][1] for d in pdates]),
    "negative_price_days": [(d, pr[d][0]) for d in pdates if pr[d][0] < 0],
    "zero_price_days": [(d, pr[d][0]) for d in pdates if pr[d][0] == 0],
    "price_over_1000": [(d, pr[d][0]) for d in pdates if pr[d][0] >= 1000],
    "price_under_minus100": [(d, pr[d][0]) for d in pdates if pr[d][0] < -100],
    "identity_24x": {
        "max_abs_dev": round(dev[0][0], 6) if dev else None,
        "n_dev_gt_0.01": sum(1 for x in dev if x[0] > 0.01),
        "n_dev_gt_1": sum(1 for x in dev if x[0] > 1.0),
        "worst20": [(d, round(x, 4), round(a, 4), round(b, 4)) for x, d, a, b in dev[:20]],
    },
    "implied_hours": {
        "median": round(statistics.median([pr[d][1] / pr[d][0] for d in pdates if pr[d][0] != 0]), 6),
        "n_23": sum(1 for d in pdates if pr[d][0] != 0 and abs(pr[d][1] / pr[d][0] - 23) < 1e-6),
        "n_24": sum(1 for d in pdates if pr[d][0] != 0 and abs(pr[d][1] / pr[d][0] - 24) < 1e-6),
        "n_25": sum(1 for d in pdates if pr[d][0] != 0 and abs(pr[d][1] / pr[d][0] - 25) < 1e-6),
        "n_other": sum(1 for d in pdates if pr[d][0] != 0 and min(abs(pr[d][1] / pr[d][0] - h) for h in (23, 24, 25)) > 1e-6),
    },
}

# ---------------------------------------------------------------- gaps / surplus
common = sorted(days_g & set(tdates) & set(ddates) & set(pdates) & set(wdates))
gap = []
for d in common:
    g = tot[d] - dem[d][1]
    gap.append((d, tot[d], dem[d][1], g, pr[d][0], wf[d]))
res["cross"]["coverage"] = {
    "gen_days": len(days_g),
    "total_days": len(tdates),
    "demand_days": len(ddates),
    "price_days": len(pdates),
    "wind_days": len(wdates),
    "common_5way": len(common),
    "gen_minus_common": sorted(days_g - set(common))[:40],
    "demand_only_days": sorted(set(ddates) - days_g),
    "wind_only_days": sorted(set(wdates) - days_g),
}
by_year = {}
for y in sorted({year_of(d) for d, *_ in gap}):
    rows = [r for r in gap if year_of(r[0]) == y]
    days = len(rows)
    surplus = sum(r[3] for r in rows if r[3] > 0) * 24 / 1e6
    deficit = sum(r[3] for r in rows if r[3] < 0) * 24 / 1e6
    net = sum(r[3] for r in rows) * 24 / 1e6
    by_year[y] = {
        "days": days,
        "net_TWh": round(net, 4),
        "deficit_TWh": round(deficit, 4),
        "surplus_TWh": round(surplus, 4),
        "max_deficit_MW": round(min(r[3] for r in rows), 2),
        "max_surplus_MW": round(max(r[3] for r in rows), 2),
        "neg_price_days": sum(1 for r in rows if r[4] < 0),
        "zero_price_days": sum(1 for r in rows if r[4] == 0),
        "nonwind_zero_days": sum(1 for r in rows if r[0] in set(nonwind_zero_days)),
        "mean_price": round(statistics.fmean([r[4] for r in rows]), 4),
        "mean_wind": round(statistics.fmean([r[5] for r in rows]), 2),
    }
res["cross"]["gap_by_year_original"] = by_year
gapstats = num_stats([r[3] for r in gap])
res["cross"]["gap_original_stats"] = gapstats
res["cross"]["gap_original_totals"] = {
    "days": len(gap),
    "deficit_TWh": round(sum(r[3] for r in gap if r[3] < 0) * 24 / 1e6, 4),
    "surplus_TWh": round(sum(r[3] for r in gap if r[3] > 0) * 24 / 1e6, 4),
    "net_TWh": round(sum(r[3] for r in gap) * 24 / 1e6, 4),
}

# correlation gap vs price, wind vs price
def corr(xs, ys):
    n = len(xs)
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return round(sxy / (sxx * syy) ** 0.5, 4) if sxx and syy else None


res["cross"]["correlations"] = {
    "gap_vs_price": corr([r[3] for r in gap], [r[4] for r in gap]),
    "wind_vs_price": corr([r[5] for r in gap], [r[4] for r in gap]),
    "demand_vs_price": corr([r[2] for r in gap], [r[4] for r in gap]),
    "gen_vs_price": corr([r[1] for r in gap], [r[4] for r in gap]),
    "gap_vs_wind": corr([r[3] for r in gap], [r[5] for r in gap]),
}
# price in surplus vs deficit buckets
buckets = {"gap<-5GW": [], "gap -5..0": [], "gap 0..5": [], "gap>5GW": []}
for r in gap:
    g, p = r[3], r[4]
    k = "gap<-5GW" if g < -5000 else "gap -5..0" if g < 0 else "gap 0..5" if g < 5000 else "gap>5GW"
    buckets[k].append(p)
res["cross"]["price_by_gap_bucket"] = {k: {"n": len(v), "mean": round(statistics.fmean(v), 3),
                                           "median": round(statistics.median(v), 3),
                                           "neg_share": round(sum(1 for x in v if x < 0) / len(v), 4)}
                                       for k, v in buckets.items() if v}

# ---------------------------------------------------------------- manifest check
man = json.load(open(os.path.join(REPO, "SOURCE_MANIFEST.json"), encoding="utf-8"))
mchk = []
for ent in man.get("files", []):
    p = ent["path"]
    row = {"path": p}
    if p.endswith(".csv"):
        info = res["inventory"][p]
        row["bytes_ok"] = info["bytes"] == ent.get("bytes")
        row["sha256_ok"] = info["sha256"] == ent.get("sha256")
        row["data_rows_ok"] = info["data_rows"] == ent.get("data_rows")
        row["columns_ok"] = info["header"] == ent.get("columns")
        row["declared"] = {k: ent.get(k) for k in ("bytes", "data_rows", "distinct_dates", "first_date", "last_date")}
        row["actual"] = {"bytes": info["bytes"], "data_rows": info["data_rows"]}
        dset = {"daily_generation_by_fuel.csv": gdates, "daily_generation_total.csv": tdates,
                "daily_demand.csv": ddates, "wind_farm_generation.csv": wdates,
                "daily_market_index_price.csv": pdates}[p]
        row["actual"]["distinct_dates"] = len(dset)
        row["actual"]["first_date"] = dset[0]
        row["actual"]["last_date"] = dset[-1]
        row["distinct_dates_ok"] = len(dset) == ent.get("distinct_dates")
        row["first_date_ok"] = dset[0] == ent.get("first_date")
        row["last_date_ok"] = dset[-1] == ent.get("last_date")
    else:
        bp = os.path.join(REPO, p)
        if os.path.exists(bp):
            row["bytes_ok"] = os.path.getsize(bp) == ent.get("bytes")
            row["sha256_ok"] = sha256(bp) == ent.get("sha256")
        else:
            row["missing"] = True
    mchk.append(row)
res["manifest_check"]["files"] = mchk
res["manifest_check"]["raw_data_modified_declared"] = man.get("raw_data_modified")
res["manifest_check"]["line_endings_declared"] = man.get("line_endings")

# ---------------------------------------------------------------- repair comparison
rep_dir = os.path.join(REPO, "Tier1", "public", "data_quality", "generation_repair", "20261103-v1")
if os.path.isdir(rep_dir):
    rtot = {}
    with open(os.path.join(rep_dir, "daily_generation_total.csv"), encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            if r[0].strip().lower() == "date":
                continue
            rtot[r[0].strip()] = float(r[1])
    rgen = defaultdict(dict)
    with open(os.path.join(rep_dir, "daily_generation_by_fuel.csv"), encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            if r[0].strip().lower() == "date":
                continue
            rgen[r[0].strip()][r[1].strip()] = float(r[2])
    changed = sorted(d for d in rtot if d in tot and abs(rtot[d] - tot[d]) > 1e-9)
    rsum_bad = [d for d in rgen if abs(sum(rgen[d].values()) - rtot.get(d, float("nan"))) > 1e-6]
    # per-year on the common 5-way date set
    ry = {}
    for y in sorted({year_of(d) for d in common}):
        rows = [d for d in common if year_of(d) == y]
        g0 = sum(tot[d] - dem[d][1] for d in rows) * 24 / 1e6
        g1 = sum(rtot[d] - dem[d][1] for d in rows if d in rtot) * 24 / 1e6
        s0 = sum(tot[d] - dem[d][1] for d in rows if tot[d] > dem[d][1]) * 24 / 1e6
        s1 = sum(rtot[d] - dem[d][1] for d in rows if d in rtot and rtot[d] > dem[d][1]) * 24 / 1e6
        d0 = sum(tot[d] - dem[d][1] for d in rows if tot[d] < dem[d][1]) * 24 / 1e6
        d1 = sum(rtot[d] - dem[d][1] for d in rows if d in rtot and rtot[d] < dem[d][1]) * 24 / 1e6
        ry[y] = {"days": len(rows), "net_orig": round(g0, 4), "net_rep": round(g1, 4),
                 "deficit_orig": round(d0, 4), "deficit_rep": round(d1, 4),
                 "surplus_orig": round(s0, 4), "surplus_rep": round(s1, 4)}
    res["repair"] = {
        "n_dates_repaired": len(rtot),
        "n_changed_vs_original": len(changed),
        "changed_dates": changed,
        "fuel_sum_mismatch_in_repair": rsum_bad[:20],
        "n_fuel_sum_mismatch": len(rsum_bad),
        "by_year_common_dates": ry,
        "totals_common": {
            "days": len(common),
            "deficit_orig": round(sum(tot[d] - dem[d][1] for d in common if tot[d] < dem[d][1]) * 24 / 1e6, 4),
            "deficit_rep": round(sum(rtot[d] - dem[d][1] for d in common if d in rtot and rtot[d] < dem[d][1]) * 24 / 1e6, 4),
            "surplus_orig": round(sum(tot[d] - dem[d][1] for d in common if tot[d] > dem[d][1]) * 24 / 1e6, 4),
            "surplus_rep": round(sum(rtot[d] - dem[d][1] for d in common if d in rtot and rtot[d] > dem[d][1]) * 24 / 1e6, 4),
        },
    }
else:
    res["repair"] = {"present": False}

# ---------------------------------------------------------------- year x fuel coverage
cov = {}
for y in sorted({year_of(d) for d in gdates}):
    ds = [d for d in gdates if year_of(d) == y]
    cov[y] = {"days": len(ds), "n_fuels": dict(Counter(len(gen[d]) for d in ds))}
res["series"]["generation_by_fuel"]["by_year_days"] = cov

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print("\nwrote", OUT)

# ---------------------------------------------------------------- printed digest
print("\n=== dates ===")
print("gen/total/price:", gdates[0], gdates[-1], len(gdates))
print("demand:", ddates[0], ddates[-1], len(ddates), "missing:", res["series"]["demand"]["missing_calendar_days"])
print("wind:", wdates[0], wdates[-1], len(wdates), "extra:", res["series"]["wind_farm"]["dates_outside_generation"])
print("gen missing days:", res["series"]["generation_by_fuel"]["missing_calendar_days"])
print("common 5-way:", len(common))
print("\n=== fuels ===")
for p in gfuels:
    print("%-24s %s" % (p, per_fuel[p]))
print("\n=== all-zero / nonwind-zero ===")
print("all fuels zero:", len(all_zero_days), runs(all_zero_days))
print("non-wind zero:", len(nonwind_zero_days), runs(nonwind_zero_days))
print("\n=== identity ===")
print(res["cross"]["fuel_sum_equals_total"])
print(res["cross"]["wind_farm_vs_fuel_wind"]["n_exact"], "/", res["cross"]["wind_farm_vs_fuel_wind"]["n_compared"],
      "max", res["cross"]["wind_farm_vs_fuel_wind"]["max_abs_diff"],
      "signs", res["cross"]["wind_farm_vs_fuel_wind"]["sign_counts"])
print("\n=== price ===")
print("neg days", len(res["series"]["price"]["negative_price_days"]),
      "zero", len(res["series"]["price"]["zero_price_days"]),
      ">1000", len(res["series"]["price"]["price_over_1000"]))
print("24x identity:", res["series"]["price"]["identity_24x"]["max_abs_dev"],
      "n>0.01", res["series"]["price"]["identity_24x"]["n_dev_gt_0.01"],
      "implied hours", res["series"]["price"]["implied_hours"])
print("\n=== gap ===")
print(res["cross"]["gap_original_totals"])
for y, v in by_year.items():
    print(y, v)
print("\n=== correlations ===", res["cross"]["correlations"])
print(res["cross"]["price_by_gap_bucket"])
print("\n=== manifest ===")
for r in mchk:
    print({k: v for k, v in r.items() if k.endswith("_ok") or k == "path" or k == "missing"})
print("\n=== repair ===")
if res["repair"].get("n_dates_repaired"):
    print("repaired dates", res["repair"]["n_dates_repaired"], "changed", res["repair"]["n_changed_vs_original"],
          "sum mismatch", res["repair"]["n_fuel_sum_mismatch"])
    print(res["repair"]["totals_common"])
    for y, v in res["repair"]["by_year_common_dates"].items():
        print(y, v)
