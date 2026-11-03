import ssl
import json
import urllib.request as u
import urllib.error as e

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/csv,application/json,text/html;q=0.9,*/*;q=0.8",
}

try:
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    print("certifi:", certifi.where())
except Exception as exc:
    ctx = ssl.create_default_context()
    print("no certifi:", exc)

targets = [
    "https://data-api.ecb.europa.eu/service/data/EXR/D.GBP.EUR.SP00.A?format=csvdata&startPeriod=2019-12-01",
    "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip",
]
for x in targets:
    try:
        r = u.urlopen(u.Request(x, headers=UA), timeout=45, context=ctx)
        b = r.read()
        print("OK  ", r.status, len(b), x)
        print("     head:", b[:200])
    except e.HTTPError as exc:
        print("HTTP", exc.code, x)
    except Exception as exc:
        print("ERR ", type(exc).__name__, exc, x)

# candidate ONS CDIDs for a consumer price INDEX (level), 2015=100
for cdid in ["L55O", "D7BT", "D7G7", "Z8VK"]:
    x = "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/%s/mm23/data" % cdid.lower()
    try:
        r = u.urlopen(u.Request(x, headers=UA), timeout=45, context=ctx)
        b = r.read()
        d = json.loads(b)
        print("ONS OK", cdid, len(b), "| title:", d.get("description", {}).get("title"),
              "| unit:", d.get("description", {}).get("unit"))
    except e.HTTPError as exc:
        print("ONS HTTP", exc.code, cdid)
    except Exception as exc:
        print("ONS ERR", type(exc).__name__, cdid, exc)
