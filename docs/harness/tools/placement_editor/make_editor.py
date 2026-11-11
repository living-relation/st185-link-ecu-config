"""Build one placement-editor page from editor.html and a seed JSON (DECISIONS B8: N120, top view only; B22 names).

    python make_editor.py <seed.json> <topview.png | old-editor.html> <out.html> [--master MASTER-wirelist.csv]

The seed JSON is the format documented at the top of editor.html, without "bg.img" (this script fills it).
Optional seed keys read only here: "title" (the page title, default "<harness> Placement Editor"; keeps an artifact's
title when one editor serves two harnesses) and "harnesses" (the master harnesses whose parts the editor owns, e.g. the
one wheel speed editor for WheelSpeed-Front and WheelSpeed-Rear, Dan X9: a device of any other harness is an error).
The background is either the top-view plan PNG or an earlier editor page whose top-view data URI is reused.
Device and fixed-marker names come from the master's plain names (from_id / to_id -> from_name / to_name), so a
rebuild after any master rename shows the new names; ids are keys only and are never shown (DECISIONS B22).
Publish <out.html> with the Artifact tool to that harness's existing editor URL (declare db + user).
"""
import base64, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "..", "..", "MASTER-wirelist.csv")
# Codes Dan may see (B22 exceptions): fuse box / relay codes, bus pins, factory EWD plug IDs (e.g. IE1, A15).
OK_CODE = re.compile(r"^(K-[A-Z0-9-]+|RLY-[A-Z0-9-]+|F-[A-Z0-9-]+|BUS[0-9A-Z-]*|[A-Z]{1,2}[0-9]{1,3})$")
CODE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")


def bg_uri(path):
    if path.lower().endswith(".png"):
        return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
    page = open(path, encoding="utf-8").read()
    m = re.search(r'(data:image/png;base64,[A-Za-z0-9+/=]{1000,})', page)   # old editors (top:{img}) and new ones (bg.img)
    if not m:
        sys.exit("no top-view image found in " + path)
    return m.group(1)


def master_names(path, owners=None):
    names = {}
    if not os.path.exists(path):
        return names
    for r in csv.DictReader(open(path, encoding="utf-8-sig", newline="")):
        for s in ("from", "to"):
            i, n = (r.get(s + "_id") or "").strip(), (r.get(s + "_name") or "").strip()
            if i and n and i not in names:
                names[i] = n
            if i and owners is not None and r.get("harness"):
                owners.setdefault(i, set()).add(r["harness"].strip())
    return names


def shown_codes(text):
    return [c for c in CODE.findall(text or "") if not OK_CODE.match(c)]


def main(seed_path, bg_path, out_path, master=MASTER):
    seed = json.load(open(seed_path, encoding="utf-8"))
    for k in ("harness", "doc", "seedVersion", "bg", "lines", "devices"):
        if k not in seed:
            sys.exit("seed is missing " + k)
    ids = [d["id"] for d in seed["devices"]]
    if len(ids) != len(set(ids)):
        sys.exit("duplicate device id in seed")
    lines = {l["id"] for l in seed["lines"]}
    for d in seed["devices"]:
        if d.get("line") and d["line"] not in lines:
            sys.exit("device %s hangs on unknown line %s" % (d["id"], d["line"]))
    refs = [r["id"] for r in seed.get("refs", [])]
    if set(refs) & set(ids):
        sys.exit("a fixed marker has the same id as a device: %s" % sorted(set(refs) & set(ids)))
    owners = {}
    names = master_names(master, owners)
    if seed.get("harnesses"):
        for d in seed["devices"]:
            if d["id"] in owners and not owners[d["id"]] & set(seed["harnesses"]):
                sys.exit("device %s belongs to %s, not to %s" % (d["id"], sorted(owners[d["id"]]), seed["harnesses"]))
    for d in seed["devices"] + seed.get("refs", []):
        if d["id"] in names:
            d["name"] = names[d["id"]]
    warn = []
    for d in seed["devices"] + seed.get("refs", []):
        for f in ("name", "short", "label", "note"):
            for c in shown_codes(d.get(f)):
                warn.append("%s %s: code %s" % (d["id"], f, c))
    for l in seed["lines"]:
        for f in ("name", "short"):
            for c in shown_codes(l.get(f)):
                warn.append("line %s %s: code %s" % (l["id"], f, c))
    for w in warn:
        print("WARNING (B22, no codes where Dan reads):", w)
    seed["bg"]["img"] = bg_uri(bg_path)
    tpl = open(os.path.join(HERE, "editor.html"), encoding="utf-8").read()
    blob = json.dumps(seed, ensure_ascii=False).replace("</", "<\\/")
    page = tpl.replace("__TITLE__", seed.get("title") or seed["harness"] + " Placement Editor").replace("__SEED__", blob)
    open(out_path, "w", encoding="utf-8").write(page)
    print("wrote", out_path, len(page), "bytes,", len(seed["devices"]), "devices,", len(seed["lines"]), "lines,",
          sum(1 for d in seed["devices"] if d["id"] in names), "names from the master,", len(warn), "code warnings")
    return len(warn)


if __name__ == "__main__":
    a = sys.argv[1:]
    m = MASTER
    if "--master" in a:
        i = a.index("--master"); m = a[i + 1]; del a[i:i + 2]
    if len(a) != 3:
        sys.exit(__doc__)
    main(*a, master=m)
