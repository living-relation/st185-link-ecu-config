"""Build one placement-editor page from editor.html and a seed JSON (DECISIONS B8: N120, top view only).

    python make_editor.py <seed.json> <topview.png | old-editor.html> <out.html>

The seed JSON is the format documented at the top of editor.html, without "bg.img" (this script fills it).
The background is either the top-view plan PNG or an earlier editor page whose top-view data URI is reused.
Publish <out.html> with the Artifact tool to that harness's existing editor URL (declare db + user).
"""
import base64, json, re, sys


def bg_uri(path):
    if path.lower().endswith(".png"):
        return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
    m = re.search(r'top:\{vb:"[^"]*",img:"(data:image/png;base64,[^"]+)"', open(path, encoding="utf-8").read())
    if not m:
        sys.exit("no top-view image found in " + path)
    return m.group(1)


def main(seed_path, bg_path, out_path):
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
    seed["bg"]["img"] = bg_uri(bg_path)
    tpl = open(__file__.replace("make_editor.py", "editor.html"), encoding="utf-8").read()
    blob = json.dumps(seed, ensure_ascii=False).replace("</", "<\\/")
    page = tpl.replace("__TITLE__", seed["harness"] + " Placement Editor").replace("__SEED__", blob)
    open(out_path, "w", encoding="utf-8").write(page)
    print("wrote", out_path, len(page), "bytes,", len(seed["devices"]), "devices,", len(seed["lines"]), "lines")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
