import re, urllib.request, os
UA = {'User-Agent': 'Mozilla/5.0 (research)'}
FILES = {
 'itm_poseidon_spec.pdf': 'https://itm-power-assets.s3.eu-west-2.amazonaws.com/POSEIDON_DATA_SHEET_2_7_2e1f89da3f.pdf',
 'itm_neptune2_spec.pdf': 'https://itm-power-assets.s3.eu-west-2.amazonaws.com/Neptune_II_Spec_Sheet_2_15_e7016ca8f8.pdf',
}
for n, u in FILES.items():
    if not os.path.exists(n):
        d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        open(n, 'wb').write(d)
    print(n, os.path.getsize(n))

try:
    import fitz
    for n in FILES:
        doc = fitz.open(n)
        print("\n=====", n, doc.page_count)
        for i, page in enumerate(doc):
            t = re.sub(r'[ \t]+', ' ', page.get_text())
            t = re.sub(r'\n+', '\n', t).strip()
            if t:
                print(f"-- p{i+1}\n{t[:1600]}")
except ImportError as e:
    print("no pymupdf:", e)
