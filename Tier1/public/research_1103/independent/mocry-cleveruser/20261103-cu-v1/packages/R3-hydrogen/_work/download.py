import os, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
FILES = {
 "h2_transport_storage_cost_report.pdf":
   "https://assets.publishing.service.gov.uk/media/659e600b915e0b00135838a6/hydrogen-transport-and-storage-cost-report.pdf",
 "h2_production_costs_2021.pdf":
   "https://assets.publishing.service.gov.uk/media/611b710e8fa8f53dc994e59d/Hydrogen_Production_Costs_2021.pdf",
 "h2_production_costs_2021_annex.xlsx":
   "https://assets.publishing.service.gov.uk/media/611a706ed3bf7f63a7b29216/Hydrogen_Production_Cost_2021_Annex.xlsx",
}
for name, url in FILES.items():
    p = os.path.join(OUT, name)
    if os.path.exists(p) and os.path.getsize(p) > 10000:
        print("have", name, os.path.getsize(p)); continue
    req = urllib.request.Request(url, headers={"User-Agent": "research-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        b = r.read()
    with open(p, "wb") as f:
        f.write(b)
    print("got", name, len(b))
