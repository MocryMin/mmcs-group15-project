"""Fetch official CPI and FX series and compute the annual values used in REPORT.md.

Sources (all official, fetched 2026-11-03 UTC by this script):
  * ONS series D7BT  - CPI INDEX 00: ALL ITEMS 2015=100 (monthly, unit: index)
  * ONS series D7G7  - CPI ANNUAL RATE 00: ALL ITEMS 2015=100 (annual, unit: %)
  * ECB Data Portal  - EXR/D.GBP.EUR.SP00.A, GBP per EUR, daily reference rate

Output: finance_evidence.json  (typed values + the raw monthly/daily figures used)
"""
import csv
import io
import json
import ssl
import statistics
import urllib.request as u

import certifi

CTX = ssl.create_default_context(cafile=certifi.where())
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

ONS = "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/{cdid}/mm23/data"
ECB = ("https://data-api.ecb.europa.eu/service/data/EXR/D.GBP.EUR.SP00.A"
       "?format=csvdata&startPeriod=2019-01-01")


def get(url):
    with u.urlopen(u.Request(url, headers=UA), timeout=60, context=CTX) as r:
        return r.read()


def ons(cdid):
    doc = json.loads(get(ONS.format(cdid=cdid.lower())))
    return doc


out = {}

# ---- ONS CPI index D7BT (monthly) ----
idx_doc = ons("D7BT")
months = idx_doc["months"]
out["ons_d7bt"] = {
    "title": idx_doc["description"]["title"],
    "cdid": idx_doc["description"]["cdid"],
    "unit": idx_doc["description"]["unit"],
    "release_date": idx_doc["description"].get("releaseDate"),
    "n_months": len(months),
    "first": months[0]["date"], "last": months[-1]["date"],
}
by_year = {}
for m in months:
    y = int(m["date"][:4])
    by_year.setdefault(y, []).append((m["date"], float(m["value"])))
annual_index = {}
for y, rows in sorted(by_year.items()):
    vals = [v for _, v in rows]
    annual_index[y] = {
        "n_months": len(rows),
        "mean_index": round(statistics.fmean(vals), 4),
        "jan": rows[0][1] if rows[0][0].endswith("-01") else None,
        "dec": rows[-1][1] if rows[-1][0].endswith("-12") else None,
        "last_month": rows[-1][0],
        "last_value": vals[-1],
    }
out["cpi_index_annual"] = {str(k): v for k, v in annual_index.items() if k >= 2019}

# ---- ONS CPI annual rate D7G7 ----
rate_doc = ons("D7G7")
out["ons_d7g7"] = {
    "title": rate_doc["description"]["title"],
    "cdid": rate_doc["description"]["cdid"],
    "unit": rate_doc["description"]["unit"],
    "release_date": rate_doc["description"].get("releaseDate"),
}
out["cpi_annual_rate"] = {y["date"]: float(y["value"]) for y in rate_doc["years"]
                          if int(y["date"]) >= 2019}
out["cpi_annual_rate_monthly_2026"] = [
    (m["date"], float(m["value"])) for m in rate_doc["months"] if m["date"].startswith("2026")
]

# ---- ECB EUR/GBP daily reference rate ----
raw = get(ECB).decode("utf-8")
rows = list(csv.DictReader(io.StringIO(raw)))
fx = {}
by_year_fx = {}
for r in rows:
    v = r["OBS_VALUE"]
    if not v:
        continue
    d = r["TIME_PERIOD"]
    by_year_fx.setdefault(int(d[:4]), []).append(float(v))
fx["series_key"] = rows[0]["KEY"] if rows else None
fx["n_obs"] = sum(len(v) for v in by_year_fx.values())
fx["first"] = rows[0]["TIME_PERIOD"]
fx["last"] = rows[-1]["TIME_PERIOD"]
fx["annual_mean_gbp_per_eur"] = {str(y): round(statistics.fmean(v), 5)
                                 for y, v in sorted(by_year_fx.items())}
fx["latest_obs"] = {"date": rows[-1]["TIME_PERIOD"], "gbp_per_eur": float(rows[-1]["OBS_VALUE"])}
out["ecb_exr_gbp_eur"] = fx

# ---- derived: EUR -> GBP conversion of the brief's 0.288 m EUR/MWh ----
eur_per_mwh = 0.288e6
conv = {}
for y, rate in fx["annual_mean_gbp_per_eur"].items():
    conv[y] = round(eur_per_mwh * rate, 1)
out["battery_capex_eur0.288m_per_MWh_in_gbp"] = {
    "eur_per_MWh": eur_per_mwh,
    "rule": "GBP/MWh = EUR/MWh * (GBP per EUR annual mean)",
    "gbp_per_MWh_by_year": conv,
}

with open("finance_evidence.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
    fh.write("\n")

print("CPI index D7BT title:", out["ons_d7bt"]["title"], "| last:", out["ons_d7bt"]["last"])
for y, v in out["cpi_index_annual"].items():
    print("  %s mean=%.3f n=%d last=%s %.3f" % (y, v["mean_index"], v["n_months"],
                                                v["last_month"], v["last_value"]))
print("CPI annual rate D7G7:", out["cpi_annual_rate"])
print("CPI 2026 monthly rates:", out["cpi_annual_rate_monthly_2026"])
print("ECB key:", fx["series_key"], "obs:", fx["n_obs"], fx["first"], "..", fx["last"])
print("GBP per EUR annual means:", fx["annual_mean_gbp_per_eur"])
print("latest:", fx["latest_obs"])
print("EUR 0.288m/MWh in GBP:", conv)
