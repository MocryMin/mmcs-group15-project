import re, urllib.request

# 1) ITM Power site links
req = urllib.request.Request('https://itm-power.com/', headers={'User-Agent': 'Mozilla/5.0'})
h = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
links = sorted(set(re.findall(r'href="([^"]+)"', h)))
keep = [l for l in links if any(k in l.lower() for k in
        ('product', 'service', 'hydrogen', 'electroly', 'datasheet', 'pdf', 'hg', 'mw', 'tech'))]
print("-- ITM links", len(links))
for l in keep[:60]:
    print("  ", l)

# 2) openpyxl probe on the 2021 annex
print("-- openpyxl probe")
try:
    import openpyxl
    wb = openpyxl.load_workbook('h2_production_costs_2021_annex.xlsx', read_only=True, data_only=True)
    print("sheets:", wb.sheetnames)
except Exception as e:
    print("openpyxl unavailable:", type(e).__name__, e)
