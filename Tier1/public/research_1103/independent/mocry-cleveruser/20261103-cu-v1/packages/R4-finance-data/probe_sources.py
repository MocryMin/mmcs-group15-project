import urllib.request as u
import urllib.error as e

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/csv,application/json,text/html;q=0.9,*/*;q=0.8",
}
urls = [
    "https://api.ons.gov.uk/timeseries/d7g7/dataset/mm23/data",
    "https://api.ons.gov.uk/timeseries/D7G7/dataset/MM23",
    "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23/data",
    "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7g7/mm23",
    "https://data-api.ecb.europa.eu/service/data/EXR/D.GBP.EUR.SP00.A?format=csvdata&startPeriod=2019-12-01",
    "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2020&Dateto=17/Sep/2026&SeriesCodes=XUDLER&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N",
]
for x in urls:
    try:
        r = u.urlopen(u.Request(x, headers=UA), timeout=45)
        body = r.read()
        print("OK  ", r.status, len(body), x)
        print("     head:", body[:160])
    except e.HTTPError as exc:
        print("HTTP", exc.code, x)
    except Exception as exc:
        print("ERR ", type(exc).__name__, exc, x)
