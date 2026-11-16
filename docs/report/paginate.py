"""Find the printed page label of every heading, figure and table in the PDF.

    python3 docs/report/paginate.py REPORT.pdf report_items.json pages.json

Page 1 = title page (no number); front pages are i, ii, iii ...; the body
starts at 1 on the page with "1. Introduction" (as in the sample report).
"""

import json
import re
import subprocess
import sys

pdf, items_path, out = sys.argv[1:4]
items = json.load(open(items_path))
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True,
                                                      text=True).stdout).group(1))
pages = []
for i in range(1, n + 1):
    t = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"],
                       capture_output=True, text=True).stdout
    pages.append([re.sub(r"\s+", " ", ln).strip() for ln in t.splitlines()])


def roman(k):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    s = ""
    for v, r in vals:
        while k >= v:
            s += r
            k -= v
    return s


def find(text, start=0, exact=False):
    key = re.sub(r"\s+", " ", text).strip()
    for i in range(start, n):
        for ln in pages[i]:
            if (ln == key) if exact else ln.startswith(key):
                return i
    raise SystemExit(f"not found: {text}")


body0 = find("1. Introduction", find("Writing Allocation", 1, exact=True) + 1, exact=True)


def label(i):
    return str(i - body0 + 1) if i >= body0 else roman(i)   # page index 1 -> i


res = {}
for h in ("Declaration", "Abstract", "List of Figures", "Writing Allocation"):
    res[h] = label(find(h, 1, exact=True))
for h in items["heads"]:
    res[h] = label(find(h, body0, exact=True))
for e in items["figures"] + items["tables"]:
    key = e.split(":")[0]
    res[key] = label(find(key + ":", body0))
res["_last"] = label(n - 1)
json.dump(res, open(out, "w"), indent=1)
print(f"{n} pages; body starts on PDF page {body0 + 1}")
print(res)
