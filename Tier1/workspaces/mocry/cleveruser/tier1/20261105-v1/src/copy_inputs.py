import csv, hashlib, io, pathlib, shutil, urllib.request, json, datetime

ROOT = pathlib.Path(r"D:\projects\CU projects\course check\MMCS Project\mmcs-group15-project")
SRC = ROOT / "Tier1/public/data_quality/full_data_repair/20261104-v2/data"
PKG = ROOT / "Tier1/workspaces/mocry/cleveruser/tier1/20261105-v1"
(PKG / "data").mkdir(parents=True, exist_ok=True)

FILES = ["daily_generation_total.csv", "daily_demand.csv", "daily_market_index_price.csv",
         "wind_farm_generation.csv", "daily_generation_by_fuel.csv", "date_quality.csv"]
man = {}
for name in FILES:
    dst = PKG / "data" / name
    shutil.copyfile(SRC / name, dst)
    b = dst.read_bytes()
    man[name] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

# CPI: fetch the same ONS D7BT series directly (independent provenance)
url = "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
cpi = urllib.request.urlopen(req, timeout=60).read()
(PKG / "data" / "ONS-CPI-D7BT.csv").write_bytes(cpi)
man["ONS-CPI-D7BT.csv"] = {"sha256": hashlib.sha256(cpi).hexdigest(), "bytes": len(cpi),
                           "url": url, "fetched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}

(PKG / "data" / "SOURCE_MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(man, indent=1)[:1200])
print("copied to", PKG)
