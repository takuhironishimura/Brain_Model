"""
Minimal end-to-end slice (hybrid space):
  - Cortex: fsaverage6 pial surface (both hemispheres), MNI305 -> MNI152 refine
  - Deep : Harvard-Oxford subcortical (MNI152 1mm) -> marching cubes
           thalamus L/R, hippocampus L/R
Reports volumes, L/R symmetry, orientation, face counts. Exports minimal GLB.
"""
import numpy as np
import nibabel as nib
import trimesh
from skimage import measure
from scipy import ndimage
from nilearn import datasets, surface

# FreeSurfer MNI305 -> MNI152 linear transform (Fischl; widely used)
M305to152 = np.array([
    [0.9975, -0.0073,  0.0176, -0.0429],
    [0.0146,  1.0009, -0.0024,  1.5496],
    [-0.0130, -0.0093, 0.9971,  1.1840],
    [0.0,     0.0,     0.0,     1.0],
])


def apply_affine(aff, pts):
    return (aff[:3, :3] @ pts.T).T + aff[:3, 3]


def mask_to_mesh(mask, affine, gaussian_sigma=0.5, taubin_iter=5,
                 target_faces=5000, min_frac=0.01):
    """Prompt pipeline: gaussian -> marching cubes(0.5) -> taubin -> decimate ->
    connected-component cleanup -> vox->world."""
    vol = ndimage.gaussian_filter(mask.astype(np.float32), sigma=gaussian_sigma)
    if vol.max() < 0.5:
        return None
    verts, faces, _, _ = measure.marching_cubes(vol, level=0.5)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    # remove tiny disconnected noise components (<min_frac of largest by volume proxy=area)
    comps = mesh.split(only_watertight=False)
    if len(comps) > 1:
        areas = np.array([c.area for c in comps])
        keep = comps[int(areas.argmax())]
        for c, a in zip(comps, areas):
            if a >= min_frac * areas.max() and c is not keep:
                keep = trimesh.util.concatenate([keep, c])
        mesh = keep
    # Taubin smoothing (Laplacian with shrink correction)
    trimesh.smoothing.filter_taubin(mesh, iterations=taubin_iter)
    # decimate
    if len(mesh.faces) > target_faces:
        mesh = mesh.simplify_quadric_decimation(face_count=target_faces)
    mesh.fix_normals()          # consistent outward winding -> positive volume
    # voxel(index i,j,k) -> world mm
    mesh.vertices = apply_affine(affine, mesh.vertices)
    return mesh


def report(name, mesh, vox_count=None, voxel_vol=1.0):
    c = mesh.centroid
    mv = mesh.volume if mesh.is_watertight else float("nan")
    line = (f"  {name:18s} faces={len(mesh.faces):6d} "
            f"centroid=({c[0]:6.1f},{c[1]:6.1f},{c[2]:6.1f}) "
            f"mesh_vol={mv:8.0f}mm3")
    if vox_count is not None:
        line += f" voxel_vol={vox_count*voxel_vol:8.0f}mm3"
    print(line)
    return c, (vox_count * voxel_vol if vox_count is not None else mv)


print("=" * 74)
print("MINIMAL BUILD: cortex(fsaverage) + thalamus/hippocampus(HO)")
print("=" * 74)

# ---------------- Harvard-Oxford subcortical
ho = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr25-1mm")
sub_img = ho["maps"] if not isinstance(ho["maps"], str) else nib.load(ho["maps"])
if isinstance(sub_img, str):
    sub_img = nib.load(sub_img)
lab = np.asarray(sub_img.dataobj)
aff = sub_img.affine
voxvol = float(np.abs(np.linalg.det(aff[:3, :3])))
print(f"HO voxel volume = {voxvol:.3f} mm3")

deep = {
    "Thalamus_L": 4, "Thalamus_R": 15,
    "Hippocampus_L": 9, "Hippocampus_R": 19,
}
print("\n--- deep structures (HO marching cubes) ---")
meshes = {}
info = {}
for nm, lid in deep.items():
    mask = (lab == lid)
    n = int(mask.sum())
    m = mask_to_mesh(mask, aff, target_faces=5000)
    meshes[nm] = m
    cen, vol = report(nm, m, vox_count=n, voxel_vol=voxvol)
    info[nm] = dict(centroid=cen, voxel_vol=n * voxvol, faces=len(m.faces))

# ---------------- fsaverage cortex
print("\n--- cortex (fsaverage6 pial) ---")
fs = datasets.fetch_surf_fsaverage(mesh="fsaverage6")
for hemi, key in [("Cortex_L", "pial_left"), ("Cortex_R", "pial_right")]:
    v, f = surface.load_surf_mesh(fs[key])
    v152 = apply_affine(M305to152, v)          # MNI305 -> MNI152 refine
    m = trimesh.Trimesh(vertices=v152, faces=f, process=True)
    if len(m.faces) > 60000:
        m = m.simplify_quadric_decimation(face_count=60000)
    meshes[hemi] = m
    cen = m.centroid
    print(f"  {hemi:18s} faces={len(m.faces):6d} "
          f"centroid=({cen[0]:6.1f},{cen[1]:6.1f},{cen[2]:6.1f}) "
          f"x-range[{m.vertices[:,0].min():6.1f},{m.vertices[:,0].max():6.1f}]")
    info[hemi] = dict(centroid=cen, faces=len(m.faces))

# ---------------- verification
print("\n" + "=" * 74)
print("VERIFICATION")
print("=" * 74)

def sym(a, b, key):
    va, vb = info[a]["voxel_vol"], info[b]["voxel_vol"]
    d = abs(va - vb) / max(va, vb) * 100
    print(f"  L/R symmetry {key:12s}: L={va:7.0f} R={vb:7.0f} mm3  diff={d:4.1f}% "
          f"{'OK' if d<=10 else 'CHECK'}")

sym("Thalamus_L", "Thalamus_R", "thalamus")
sym("Hippocampus_L", "Hippocampus_R", "hippocampus")

print("\n  Orientation (RAS: x>0 = RIGHT):")
for l, r in [("Thalamus_L", "Thalamus_R"), ("Hippocampus_L", "Hippocampus_R"),
             ("Cortex_L", "Cortex_R")]:
    xl, xr = info[l]["centroid"][0], info[r]["centroid"][0]
    ok = (xl < 0) and (xr > 0)
    print(f"    {l[:-2]:12s}: L.x={xl:6.1f}  R.x={xr:6.1f}  "
          f"{'OK (L<0,R>0)' if ok else '*** SWAPPED ***'}")

print("\n  Literature ranges: hippocampus ~3000-4000, thalamus ~6000-8000 mm3 (per side)")

# ---------------- alignment residual (cortex vs deep bbox center)
allv = np.vstack([meshes[k].vertices for k in meshes])
print(f"\n  Combined bounding box (mm): "
      f"x[{allv[:,0].min():.0f},{allv[:,0].max():.0f}] "
      f"y[{allv[:,1].min():.0f},{allv[:,1].max():.0f}] "
      f"z[{allv[:,2].min():.0f},{allv[:,2].max():.0f}]")

# ---------------- export minimal GLB
scene = trimesh.Scene()
colors = {"Thalamus_L": [200,120,80], "Thalamus_R": [200,120,80],
          "Hippocampus_L": [90,160,120], "Hippocampus_R": [90,160,120],
          "Cortex_L": [200,190,175], "Cortex_R": [200,190,175]}
for nm, m in meshes.items():
    mm = m.copy()
    mm.visual = trimesh.visual.ColorVisuals(mm, face_colors=colors[nm]+[255])
    scene.add_geometry(mm, node_name=nm, geom_name=nm)
out = "brain_minimal.glb"
scene.export(out)
import os
print(f"\n  Exported {out}  ({os.path.getsize(out)/1e6:.2f} MB), "
      f"total faces={sum(len(m.faces) for m in meshes.values())}")
print("\nDONE minimal build.")
