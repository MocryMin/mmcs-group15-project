import re, urllib.request

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (research)'})
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')

def strip(h):
    h = re.sub(r'(?is)<(script|style|nav|footer|svg)[^>]*>.*?</\1>', ' ', h)
    t = re.sub(r'(?s)<[^>]+>', ' ', h)
    t = re.sub(r'&nbsp;|&#160;', ' ', t)
    t = re.sub(r'&amp;', '&', t)
    return re.sub(r'\s+', ' ', t)

for url in ['https://itm-power.com/products', 'https://itm-power.com/products/alpha']:
    try:
        h = fetch(url)
    except Exception as e:
        print("FAIL", url, type(e).__name__, e); continue
    txt = strip(h)
    print("\n=====", url, len(h))
    print(txt[:3000])
    pdfs = sorted(set(re.findall(r'href="([^"]+\.pdf)"', h, re.I)))
    print("PDFs:", pdfs[:15])
