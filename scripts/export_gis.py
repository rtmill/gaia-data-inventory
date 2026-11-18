#!/usr/bin/env python3
"""Write the files that go to OHDSI/GIS, laid out at their GIS paths (run from the repo root after build.py).

    python scripts/export_gis.py <out_dir>

Nothing here touches GIS: the release workflow (manual) or a maintainer copies <out_dir> into a GIS branch and opens a PR.
"""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv  # noqa: E402

OUT = sys.argv[1]
REPO = "https://github.com/rtmill/gaia-data-inventory"
EX = os.path.join(OUT, "exploration", "place-data-inventory")
os.makedirs(EX, exist_ok=True)
os.makedirs(os.path.join(OUT, "rmd", "data"), exist_ok=True)
os.makedirs(os.path.join(OUT, "rmd", "assets"), exist_ok=True)
st = json.load(open(os.path.join(inv.BUILD, "STATE.json"), encoding="utf-8"))
cp = lambda a, b: shutil.copyfile(os.path.join(inv.ROOT, a), b)
cp("build/inventory-all.csv", os.path.join(EX, "inventory-all.csv"))
cp("build/inventory-verified.csv", os.path.join(EX, "inventory-verified.csv"))
cp("build/site/inventory.json", os.path.join(OUT, "rmd", "data", "inventory.json"))
cp("build/site/inventory-history.json", os.path.join(OUT, "rmd", "data", "inventory-history.json"))
cp("site/inventory.Rmd", os.path.join(OUT, "rmd", "inventory.Rmd"))
cp("site/inventory.js", os.path.join(OUT, "rmd", "assets", "inventory.js"))
t = st["tiers"]
open(os.path.join(EX, "README.md"), "w", encoding="utf-8", newline="\n").write(f"""# Place-based data inventory (exploratory)

**The working inventory now lives in [{REPO.split('github.com/')[1]}]({REPO})**: method, queues, how to contribute, and the full history. This folder holds a snapshot for the site's [Data Inventory](https://ohdsi.github.io/GIS/inventory.html) page and for anyone linking here.

**Snapshot as of {st['asof']}:** {st['rows']} datasets assessed, **{st['verified']} verified** (Gold {t['Gold']}, Silver {t['Silver']}), Bronze {t['Bronze']}, Browser needed {t['Browser needed']}, Failed {t['Failed']}; {st['file_verified']} file-verified.

| File | What it is |
|---|---|
| `inventory-verified.csv` | Gold and Silver datasets, readable columns (title, publisher, landing page, unit, place key, licence, evidence) |
| `inventory-all.csv` | Every assessed dataset with every check, its detail and evidence URL |

Not everything here is in the Gaia catalog: only rows with `in_gaia` set have made it in.
""")
print("exported to", OUT)
