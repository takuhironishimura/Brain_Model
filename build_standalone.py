"""
Build a fully self-contained single-file viewer:  viewer_standalone.html

Embeds, so it runs by double-clicking (file://), offline, no server:
  * Three.js r160 (three.module.js + OrbitControls + GLTFLoader + BufferGeometryUtils)
    inlined as data: URLs in the import map
  * brain.glb        -> base64, decoded in-page and passed to GLTFLoader.parse
  * structures.json  -> inline JS object

Reproducible: the Three.js sources are downloaded at build time.
"""
import base64, json, urllib.request, re, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "viewer.html")
GLB = os.path.join(HERE, "brain.glb")
JSON_ = os.path.join(HERE, "structures.json")
OUT = os.path.join(HERE, "viewer_standalone.html")

BASE = "https://unpkg.com/three@0.160.0"
THREE_FILES = {
    "three": "/build/three.module.js",
    "three/addons/controls/OrbitControls.js": "/examples/jsm/controls/OrbitControls.js",
    "three/addons/loaders/GLTFLoader.js": "/examples/jsm/loaders/GLTFLoader.js",
    "three/addons/utils/BufferGeometryUtils.js": "/examples/jsm/utils/BufferGeometryUtils.js",
}

def fetch(url):
    print("  download", url)
    return urllib.request.urlopen(url, timeout=60).read().decode("utf-8")

def data_url(js_text):
    b64 = base64.b64encode(js_text.encode("utf-8")).decode("ascii")
    return "data:text/javascript;base64," + b64

print("Fetching Three.js r160 modules ...")
mods = {name: fetch(BASE + path) for name, path in THREE_FILES.items()}

# GLTFLoader uses a RELATIVE import that cannot resolve from a data: URL.
# Rewrite it to the bare specifier we provide in the import map.
before = "'../utils/BufferGeometryUtils.js'"
after = "'three/addons/utils/BufferGeometryUtils.js'"
assert before in mods["three/addons/loaders/GLTFLoader.js"], "relative import not found"
mods["three/addons/loaders/GLTFLoader.js"] = \
    mods["three/addons/loaders/GLTFLoader.js"].replace(before, after)

# sanity: no other relative cross-file imports remain
for name, txt in mods.items():
    rel = re.findall(r"from\s+'(\.[^']+)'", txt)
    if rel:
        print(f"  WARNING: {name} still has relative imports: {rel}")

importmap = {"imports": {name: data_url(txt) for name, txt in mods.items()}}
importmap_json = json.dumps(importmap, indent=2)

print("Embedding data ...")
glb_b64 = base64.b64encode(open(GLB, "rb").read()).decode("ascii")
structures = json.load(open(JSON_))
structures_js = json.dumps(structures, ensure_ascii=False)

html = open(SRC, encoding="utf-8").read()

# 1) replace the CDN import map with the inlined (data: URL) import map
html = re.sub(
    r'<script type="importmap">.*?</script>',
    '<script type="importmap">\n' + importmap_json + '\n</script>',
    html, count=1, flags=re.S)

# 2) inject inline data constants right after the three import statements
inject = (
    "\n// ---- inlined data (self-contained build) ----\n"
    "const __STRUCTURES__ = " + structures_js + ";\n"
    "const __GLB_B64__ = \"" + glb_b64 + "\";\n"
    "function __glbBuffer(){ const b=atob(__GLB_B64__), n=b.length, a=new Uint8Array(n);"
    " for(let i=0;i<n;i++) a[i]=b.charCodeAt(i); return a.buffer; }\n"
)
anchor = "import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';"
assert anchor in html, "GLTFLoader import anchor not found"
html = html.replace(anchor, anchor + inject, 1)

# 3) replace external fetch/load with inline sources
html = html.replace("fetch('structures.json').then(r=>r.json())",
                    "Promise.resolve(__STRUCTURES__)")
html = html.replace("new GLTFLoader().load('brain.glb', res, undefined, rej)",
                    "new GLTFLoader().parse(__glbBuffer(), '', res, rej)")

# 4) tweak the load-failure hint (no server needed anymore)
html = html.replace("読み込み中… (ローカルHTTPサーバ経由で開いてください)",
                    "読み込み中… / Loading…")

# 5) mark title so it's distinguishable
html = html.replace("<title>脳3Dビューア / Brain 3D Viewer</title>",
                    "<title>脳3Dビューア / Brain 3D Viewer (standalone)</title>")

open(OUT, "w", encoding="utf-8").write(html)
size = os.path.getsize(OUT)
print(f"\nWrote {OUT}  ({size/1e6:.2f} MB)")
print("Self-contained: open by double-click (file://), offline, no server.")
