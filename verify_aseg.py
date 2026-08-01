"""
Generate ALL deep structures from fsaverage aseg and verify volumes vs literature.
Marching-cubes isosurface level fixed at 0.5 (unchanged). No HO used.
"""
import os, numpy as np, nibabel as nib, trimesh
from skimage import measure
from scipy import ndimage
import mne

SUBJ = mne.datasets.fetch_fsaverage(verbose=False)
aseg_path = os.path.join(SUBJ, "mri", "aseg.mgz")
img = nib.load(aseg_path)
data = np.asarray(img.dataobj).astype(np.int32)
aff = img.affine
voxvol = float(abs(np.linalg.det(aff[:3, :3])))
print(f"aseg: shape={img.shape} voxvol={voxvol:.3f}mm3")
print("affine:\n", np.round(aff, 2))


def apply_affine(a, p):
    return (a[:3, :3] @ p.T).T + a[:3, 3]


def build(labels, sigma=0.5, taubin=5, target=6000):
    mask = np.isin(data, labels)
    n = int(mask.sum())
    if n == 0:
        return None, 0, None
    vol = ndimage.gaussian_filter(mask.astype(np.float32), sigma=sigma)
    if vol.max() < 0.5:
        return None, n, None
    v, f, _, _ = measure.marching_cubes(vol, level=0.5)          # 0.5 fixed
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    comps = m.split(only_watertight=False)
    if len(comps) > 1:
        areas = np.array([c.area for c in comps]); keep = comps[int(areas.argmax())]
        for c, a in zip(comps, areas):
            if a >= 0.01 * areas.max() and c is not keep:
                keep = trimesh.util.concatenate([keep, c])
        m = keep
    trimesh.smoothing.filter_taubin(m, iterations=taubin)
    if len(m.faces) > target:
        m = m.simplify_quadric_decimation(face_count=target)
    m.fix_normals()
    m.vertices = apply_affine(aff, m.vertices)
    return m, n, m.centroid


# structure -> (aseg label ids, literature per-side range mm3 or None)
STRUCT = {
    "Thalamus_L": ([10], (6000, 8000)), "Thalamus_R": ([49], (6000, 8000)),
    "Caudate_L": ([11], (3000, 4000)), "Caudate_R": ([50], (3000, 4000)),
    "Putamen_L": ([12], (4000, 5500)), "Putamen_R": ([51], (4000, 5500)),
    "Pallidum_L": ([13], (1500, 2200)), "Pallidum_R": ([52], (1500, 2200)),
    "Hippocampus_L": ([17], (3000, 4500)), "Hippocampus_R": ([53], (3000, 4500)),
    "Amygdala_L": ([18], (1200, 1900)), "Amygdala_R": ([54], (1200, 1900)),
    "Accumbens_L": ([26], (400, 700)), "Accumbens_R": ([58], (400, 700)),
    "Cerebellum_L": ([8, 7], (50000, 65000)), "Cerebellum_R": ([47, 46], (50000, 65000)),
    "BrainStem": ([16], (20000, 35000)),
    "LateralVentricle_L": ([4, 5], (None)), "LateralVentricle_R": ([43, 44], (None)),
    "ThirdVentricle": ([14], (None)),
    "FourthVentricle": ([15], (None)),
    "VentralDC_L": ([28], (None)), "VentralDC_R": ([60], (None)),
}

print("\n%-20s %8s %8s %9s %-16s %s" % ("STRUCTURE","vox_vol","mesh_vol","faces","lit_range","flag"))
print("-"*78)
info = {}; meshes = {}
for nm, (ids, lit) in STRUCT.items():
    target = 8000 if "Cerebellum" in nm or nm == "BrainStem" else 5000
    m, n, cen = build(ids, target=target)
    if m is None:
        print("%-20s  MISSING (0 voxels)" % nm); continue
    vv = n * voxvol
    mv = m.volume if m.is_watertight else float("nan")
    flag = ""
    if lit and lit != (None):
        lo, hi = lit
        flag = "OK" if lo <= vv <= hi else ("HIGH" if vv > hi else "LOW")
    lits = f"{lit[0]}-{lit[1]}" if (lit and lit != (None)) else "-"
    print("%-20s %8.0f %8.0f %9d %-16s %s" % (nm, vv, mv, len(m.faces), lits, flag))
    info[nm] = dict(vv=vv, cen=cen); meshes[nm] = m

# ---- L/R symmetry
print("\n--- L/R symmetry (target <=10%) ---")
pairs = [("Thalamus","L","R"),("Caudate","L","R"),("Putamen","L","R"),
         ("Pallidum","L","R"),("Hippocampus","L","R"),("Amygdala","L","R"),
         ("Accumbens","L","R"),("Cerebellum","L","R"),("LateralVentricle","L","R"),
         ("VentralDC","L","R")]
for base,l,r in pairs:
    a,b=f"{base}_{l}",f"{base}_{r}"
    if a in info and b in info:
        va,vb=info[a]["vv"],info[b]["vv"]; d=abs(va-vb)/max(va,vb)*100
        print(f"  {base:18s} L={va:8.0f} R={vb:8.0f}  diff={d:4.1f}% {'OK' if d<=10 else 'CHECK'}")

# ---- orientation
print("\n--- Orientation (RAS: x>0=RIGHT) ---")
for base,_,_ in pairs:
    a,b=f"{base}_L",f"{base}_R"
    if a in info and b in info:
        xl,xr=info[a]["cen"][0],info[b]["cen"][0]
        ok=(xl<0)and(xr>0)
        print(f"  {base:18s} L.x={xl:6.1f} R.x={xr:6.1f} {'OK' if ok else '*** SWAPPED ***'}")

print("\nDONE aseg verification.")
