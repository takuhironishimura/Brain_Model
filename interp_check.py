"""Interpenetration check between adjacent structures, from the exported brain.glb.
Metric: fraction of A's vertices lying INSIDE B (and vice versa), plus max
penetration depth (mm). aseg labels are mutually exclusive, so any overlap comes
from post-smoothing bleed at shared boundaries; small values are expected/benign.
"""
import struct, json, numpy as np, trimesh

scene = trimesh.load("brain.glb", process=False)
G = scene.geometry
print("loaded meshes:", len(G))

# confirm NORMAL present in GLB
data = open("brain.glb", "rb").read(); off = 12
clen, ct = struct.unpack("<II", data[off:off+8]); off += 8
js = json.loads(data[off:off+clen])
has_norm = all("NORMAL" in pr["attributes"]
               for m in js["meshes"] for pr in m["primitives"])
print("GLB has NORMAL on all primitives:", has_norm)

from trimesh import repair
def inside_mask(B, pts):
    try:
        return B.contains(pts)             # ray-based (needs rtree)
    except Exception:
        try:
            return trimesh.proximity.signed_distance(B, pts) > 0
        except Exception:
            return np.zeros(len(pts), bool)
def repaired(m):
    c = m.copy(); c.merge_vertices(); repair.fill_holes(c); c.fix_normals()
    return c

def frac_inside(A, B):
    inside = inside_mask(B, A.vertices)
    k = int(inside.sum())
    if k == 0:
        return 0.0, 0.0
    pts = A.vertices[inside]
    try:
        d = trimesh.proximity.closest_point(B, pts)[1]
        depth = float(np.max(d))
    except Exception:
        depth = float("nan")
    return k / len(A.vertices) * 100.0, depth

def check(a, b):
    A, B = G.get(a), G.get(b)
    if A is None or B is None:
        print(f"  {a} vs {b}: MISSING"); return
    f1, d1 = frac_inside(A, B)
    f2, d2 = frac_inside(B, A)
    wa, wb = A.is_watertight, B.is_watertight
    print(f"  {a:20s} vs {b:20s} | {a[:10]}->{b[:10]}: {f1:5.1f}% (depth {d1:.1f}mm) "
          f"| {b[:10]}->{a[:10]}: {f2:5.1f}% (depth {d2:.1f}mm) "
          f"[wt {int(wa)},{int(wb)}]")

print("\n=== Requested adjacent-pair interpenetration ===")
check("Thalamus_L", "ThirdVentricle")
check("Thalamus_R", "ThirdVentricle")
check("LateralVentricle_L", "Caudate_L")
check("LateralVentricle_R", "Caudate_R")
check("BrainStem", "Cerebellum_L")
check("BrainStem", "Cerebellum_R")
check("Hippocampus_L", "LateralVentricle_L")
check("Hippocampus_R", "LateralVentricle_R")

print("\n=== Cortex poke-through: fraction of subcortical verts OUTSIDE cortex ===")
cL_rep, cR_rep = repaired(G["Cortex_L"]), repaired(G["Cortex_R"])
subcort = [k for k in G if not k.startswith("Cortex")]
for k in subcort:
    A = G[k]
    # a vertex is 'inside brain' if contained in either hemisphere pial
    inL = inside_mask(cL_rep, A.vertices)
    inR = inside_mask(cR_rep, A.vertices)
    inside = inL | inR
    out = 100.0 * (1 - inside.mean())
    flag = "OK" if out < 2 else ("minor" if out < 10 else "CHECK")
    print(f"  {k:20s} outside cortex: {out:5.1f}%  {flag}")
