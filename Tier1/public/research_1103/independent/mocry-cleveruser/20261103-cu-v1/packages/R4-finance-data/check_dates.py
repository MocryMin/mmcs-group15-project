import csv
import datetime as dt

b = "Tier1/workspaces/mocry/cleveruser/inputs/"


def ds(p, col):
    s = set()
    for r in csv.DictReader(open(b + p, encoding="utf-8-sig", newline="")):
        v = r[col].strip()
        s.add(dt.date.fromisoformat(v.replace("Z", "").split("T")[0]))
    return s


g = ds("daily_generation_total.csv", "date")
d = ds("daily_demand.csv", "startTime")
pr = ds("daily_market_index_price.csv", "date")
w = ds("wind_farm_generation.csv", "date")
f = ds("daily_generation_by_fuel.csv", "date")
print("counts g,d,price,wind,fuel:", len(g), len(d), len(pr), len(w), len(f))
print("gen minus demand:", len(g - d), sorted(x.isoformat() for x in g - d)[:25])
print("demand minus gen:", len(d - g), sorted(x.isoformat() for x in d - g)[:25])
print("price minus gen:", len(pr - g))
print("wind minus gen:", len(w - g), sorted(x.isoformat() for x in (w - g))[:10])
print("fuel != gen:", len(f ^ g))
print("intersection all five:", len(g & d & pr & w & f))
print("missing in demand within span:", sorted(
    (dt.date(2020, 1, 1) + dt.timedelta(days=i)).isoformat()
    for i in range(2452)
) and [x.isoformat() for x in (g | d) - d])
