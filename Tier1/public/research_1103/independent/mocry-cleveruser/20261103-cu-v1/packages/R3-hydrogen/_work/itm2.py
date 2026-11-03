import re, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (research)'}
def fetch(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    d = urllib.request.urlopen(req, timeout=60).read()
    return d if binary else d.decode('utf-8', 'replace')

h = fetch('https://itm-power.com/products')
links = sorted(set(re.findall(r'href="([^"]+)"', h)))
print("product-ish links:")
for l in links:
    if '/products' in l or 'spec' in l.lower() or l.lower().endswith('.pdf'):
        print("  ", l)

url = 'https://itm-power-assets.s3.eu-west-2.amazonaws.com/14299_ITM_Alpha_Spec_Sheet_1_7_5db44f3d20.pdf'
b = fetch(url, binary=True)
open('itm_alpha50_spec.pdf', 'wb').write(b)
print("spec pdf bytes", len(b))
