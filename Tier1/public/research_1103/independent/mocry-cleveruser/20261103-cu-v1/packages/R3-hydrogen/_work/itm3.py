import re, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (research)'}
def strip(h):
    h = re.sub(r'(?is)<(script|style|svg)[^>]*>.*?</\1>', ' ', h)
    t = re.sub(r'(?s)<[^>]+>', ' ', h)
    t = re.sub(r'&nbsp;|&#160;', ' ', t).replace('&amp;', '&')
    return re.sub(r'\s+', ' ', t)

for slug in ['poseidon', 'neptune-2', 'trident']:
    url = 'https://itm-power.com/products/' + slug
    try:
        h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'replace')
    except Exception as e:
        print("FAIL", url, e); continue
    print("\n=====", url)
    print(strip(h)[:2200])
    print("PDFs:", sorted(set(re.findall(r'href="([^"]+\.pdf)"', h, re.I)))[:6])
