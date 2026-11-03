import json, os, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.gov.uk/api/content"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()

def dump(slug, rel):
    data = json.loads(get(BASE + rel))
    with open(os.path.join(OUT, slug + ".json"), "wb") as f:
        f.write(json.dumps(data, indent=1).encode())
    found = []
    def walk(node, path=""):
        if isinstance(node, dict):
            # gov.uk content api uses "url" keys on attachments
            if "url" in node and isinstance(node["url"], str):
                found.append((path, node.get("title", ""), node["url"],
                              node.get("content_type", ""), node.get("file_size", "")))
            for k, v in node.items():
                walk(v, path + "/" + k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + "/%d" % i)
    walk(data)
    print("==", slug, data.get("title"))
    for p, t, u, ct, fs in found:
        if any(x in u for x in (".pdf", ".xlsx", ".xls", ".ods", ".csv")):
            print("  ", t, "|", u, "|", ct, fs)
    return found

dump("h2_transport_storage", "/government/publications/hydrogen-transport-and-storage-cost")
dump("h2_prod_costs_2021", "/government/publications/hydrogen-production-costs-2021")
