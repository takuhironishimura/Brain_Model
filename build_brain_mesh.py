"""
build_brain_mesh.py  --  reproducible brain-mesh builder.

Sources (single fsaverage space, so cortical surface and aseg volumes align):
  * Cortex surface : fsaverage lh/rh.pial            (FreeSurfer tkrRAS)
  * Deep structures: fsaverage aseg.mgz              (via vox2ras-tkr -> same tkrRAS)

Design decisions (locked):
  * fsaverage = AVERAGE brain. Adopted as-is. NO volume correction, NO mask
    shrinking, NO probability-threshold tuning to chase literature volumes.
  * marching-cubes isosurface level is FIXED at 0.5 for every structure.
  * Volumes are recorded (measured, reference range, % diff) in structures.json.

Milestone flag INCLUDE controls which structures go into the exported GLB.
"""
import os, json, argparse
import numpy as np
import nibabel as nib
import trimesh
from skimage import measure
from scipy import ndimage
import mne

# ------------------------------------------------------------------ registry
# name -> dict(en, ja, category, aseg_ids or 'surface', ref range per side, color)
CORTEX = {
    "Cortex_L": dict(en="Cerebral Cortex (Left)", ja="大脳皮質（左）",
                     category="cortex", source="surface:lh.pial", ref=None,
                     color=[205, 195, 180]),
    "Cortex_R": dict(en="Cerebral Cortex (Right)", ja="大脳皮質（右）",
                     category="cortex", source="surface:rh.pial", ref=None,
                     color=[205, 195, 180]),
}
DEEP = {
    "Thalamus_L": dict(en="Thalamus (Left)", ja="視床（左）", category="subcortical",
                       ids=[10], ref=[6000, 8000], color=[196, 122, 88]),
    "Thalamus_R": dict(en="Thalamus (Right)", ja="視床（右）", category="subcortical",
                       ids=[49], ref=[6000, 8000], color=[196, 122, 88]),
    "Caudate_L": dict(en="Caudate (Left)", ja="尾状核（左）", category="subcortical",
                      ids=[11], ref=[3000, 4000], color=[132, 158, 190]),
    "Caudate_R": dict(en="Caudate (Right)", ja="尾状核（右）", category="subcortical",
                      ids=[50], ref=[3000, 4000], color=[132, 158, 190]),
    "Putamen_L": dict(en="Putamen (Left)", ja="被殻（左）", category="subcortical",
                      ids=[12], ref=[4000, 5500], color=[150, 120, 175]),
    "Putamen_R": dict(en="Putamen (Right)", ja="被殻（右）", category="subcortical",
                      ids=[51], ref=[4000, 5500], color=[150, 120, 175]),
    "Pallidum_L": dict(en="Pallidum (Left)", ja="淡蒼球（左）", category="subcortical",
                       ids=[13], ref=[1500, 2200], color=[120, 145, 120]),
    "Pallidum_R": dict(en="Pallidum (Right)", ja="淡蒼球（右）", category="subcortical",
                       ids=[52], ref=[1500, 2200], color=[120, 145, 120]),
    "Hippocampus_L": dict(en="Hippocampus (Left)", ja="海馬（左）", category="subcortical",
                          ids=[17], ref=[3000, 4500], color=[90, 160, 120]),
    "Hippocampus_R": dict(en="Hippocampus (Right)", ja="海馬（右）", category="subcortical",
                          ids=[53], ref=[3000, 4500], color=[90, 160, 120]),
    "Amygdala_L": dict(en="Amygdala (Left)", ja="扁桃体（左）", category="subcortical",
                       ids=[18], ref=[1200, 1900], color=[210, 170, 90]),
    "Amygdala_R": dict(en="Amygdala (Right)", ja="扁桃体（右）", category="subcortical",
                       ids=[54], ref=[1200, 1900], color=[210, 170, 90]),
    "Accumbens_L": dict(en="Accumbens (Left)", ja="側坐核（左）", category="subcortical",
                        ids=[26], ref=[400, 700], color=[200, 140, 150]),
    "Accumbens_R": dict(en="Accumbens (Right)", ja="側坐核（右）", category="subcortical",
                        ids=[58], ref=[400, 700], color=[200, 140, 150]),
    "Cerebellum_L": dict(en="Cerebellum (Left)", ja="小脳（左）", category="cerebellum",
                         ids=[8, 7], ref=[55000, 75000], color=[170, 150, 190]),
    "Cerebellum_R": dict(en="Cerebellum (Right)", ja="小脳（右）", category="cerebellum",
                         ids=[47, 46], ref=[55000, 75000], color=[170, 150, 190]),
    "BrainStem": dict(en="Brainstem", ja="脳幹", category="brainstem",
                      ids=[16], ref=[20000, 35000], color=[180, 130, 110]),
    "VentralDC_L": dict(en="Ventral Diencephalon (Left)", ja="腹側間脳（左）",
                        category="brainstem", ids=[28], ref=None, color=[160, 140, 120]),
    "VentralDC_R": dict(en="Ventral Diencephalon (Right)", ja="腹側間脳（右）",
                        category="brainstem", ids=[60], ref=None, color=[160, 140, 120]),
    "LateralVentricle_L": dict(en="Lateral Ventricle (Left)", ja="側脳室（左）",
                               category="ventricle", ids=[4, 5], ref=None, color=[110, 170, 200]),
    "LateralVentricle_R": dict(en="Lateral Ventricle (Right)", ja="側脳室（右）",
                               category="ventricle", ids=[43, 44], ref=None, color=[110, 170, 200]),
    "ThirdVentricle": dict(en="Third Ventricle", ja="第三脳室", category="ventricle",
                           ids=[14], ref=None, color=[100, 180, 210]),
    "FourthVentricle": dict(en="Fourth Ventricle", ja="第四脳室", category="ventricle",
                            ids=[15], ref=None, color=[100, 180, 210]),
}
# Per-structure decimation policy (face targets chosen for each shape's
# characteristics; thin ventricles are NOT decimated to avoid breakage).
#   target = face_count aim ; decimate=False keeps raw marching-cubes faces.
DECIM = {
    # thin sheets / narrow tubes -> keep raw (floor = natural face count)
    "ThirdVentricle":  dict(target=None, decimate=False),
    "FourthVentricle": dict(target=None, decimate=False),
    # lateral ventricle: thin curved with inferior horn -> keep high
    "LateralVentricle_L": dict(target=12000, decimate=True),
    "LateralVentricle_R": dict(target=12000, decimate=True),
    # cerebellum: foliated -> light decimation to preserve foliation
    "Cerebellum_L": dict(target=22000, decimate=True),
    "Cerebellum_R": dict(target=22000, decimate=True),
    # compact solids
    "BrainStem":  dict(target=8000, decimate=True),
    "VentralDC_L": dict(target=6000, decimate=True),
    "VentralDC_R": dict(target=6000, decimate=True),
}
DECIM_DEFAULT = dict(target=5000, decimate=True)   # subcortical nuclei

REF_SOURCE = ("Representative adult normative ranges from manual-tracing MRI "
              "studies; see README references. Values here are FreeSurfer aseg "
              "outputs on the fsaverage average brain and run systematically "
              "larger than manual tracing (boundary-definition difference).")

# ------------------------------------------------------------------ meshing
def apply_affine(a, p):
    return (a[:3, :3] @ p.T).T + a[:3, 3]

def clean_and_smooth(m, target, taubin=5, min_frac=0.01):
    comps = m.split(only_watertight=False)
    if len(comps) > 1:
        areas = np.array([c.area for c in comps]); keep = comps[int(areas.argmax())]
        for c, a in zip(comps, areas):
            if a >= min_frac * areas.max() and c is not keep:
                keep = trimesh.util.concatenate([keep, c])
        m = keep
    trimesh.smoothing.filter_taubin(m, iterations=taubin)
    if len(m.faces) > target:
        m = m.simplify_quadric_decimation(face_count=target)
    return m

def mesh_from_aseg(data, ids, tkr_affine, target, sigma=0.5, decimate=True):
    mask = np.isin(data, ids)
    n = int(mask.sum())
    if n == 0:
        return None, 0
    vol = ndimage.gaussian_filter(mask.astype(np.float32), sigma=sigma)
    if vol.max() < 0.5:
        return None, n
    v, f, _, _ = measure.marching_cubes(vol, level=0.5)      # 0.5 fixed
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    tgt = target if decimate else 10**9      # thin structures: skip decimation
    m = clean_and_smooth(m, tgt)
    m.vertices = apply_affine(tkr_affine, m.vertices)
    # tkr affine may be left-handed (det<0) -> ensure outward normals AFTER transform
    m.fix_normals()
    if m.is_watertight and m.volume < 0:
        m.invert()
    m.vertex_normals   # force-compute so GLB export includes NORMAL
    return m, n

def mesh_from_surface(coords, faces, target):
    m = trimesh.Trimesh(vertices=coords, faces=faces, process=True)
    if len(m.faces) > target:
        m = m.simplify_quadric_decimation(face_count=target)
    m.fix_normals()
    m.vertex_normals   # force-compute so GLB export includes NORMAL
    return m

# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include", default="minimal",
                    choices=["minimal", "all"],
                    help="minimal = cortex+thalamus+hippocampus; all = every structure")
    ap.add_argument("--out", default="brain.glb")
    args = ap.parse_args()

    subj = mne.datasets.fetch_fsaverage(verbose=False)
    aseg = nib.load(os.path.join(subj, "mri", "aseg.mgz"))
    data = np.asarray(aseg.dataobj).astype(np.int32)
    tkr = aseg.header.get_vox2ras_tkr()          # aseg voxel -> surface(tkr) RAS
    voxvol = float(abs(np.linalg.det(aseg.affine[:3, :3])))
    print(f"aseg voxvol={voxvol:.3f}mm3   tkr affine det={np.linalg.det(tkr[:3,:3]):.2f}")

    if args.include == "minimal":
        deep_keys = ["Thalamus_L", "Thalamus_R", "Hippocampus_L", "Hippocampus_R"]
    else:
        deep_keys = list(DEEP.keys())

    meshes, records = {}, {}

    # cortex (always both hemispheres)
    for key, cfg in CORTEX.items():
        hemi = "lh" if key.endswith("_L") else "rh"
        coords, faces = nib.freesurfer.read_geometry(
            os.path.join(subj, "surf", f"{hemi}.pial"))
        m = mesh_from_surface(coords, faces, target=60000)
        meshes[key] = m
        cen = m.centroid
        records[key] = dict(name_en=cfg["en"], name_ja=cfg["ja"],
                            category=cfg["category"], source=cfg["source"],
                            faces=int(len(m.faces)),
                            surface_area_mm2=round(float(m.area), 1),
                            centroid_mm=[round(float(x), 1) for x in cen],
                            volume_mm3_measured=None, reference_range_mm3=None,
                            reference_source=None, pct_diff_vs_reference=None,
                            color=cfg["color"])
        print(f"  {key:20s} faces={len(m.faces):6d} area={m.area:8.0f}mm2 "
              f"cen.x={cen[0]:6.1f}")

    # deep structures
    for key in DEEP:                     # measure ALL for JSON record
        cfg = DEEP[key]
        pol = DECIM.get(key, DECIM_DEFAULT)
        m, n = mesh_from_aseg(data, cfg["ids"], tkr,
                              pol["target"] or 0, decimate=pol["decimate"])
        if m is None:
            print(f"  {key:20s} MISSING"); continue
        vv = round(n * voxvol, 1)
        ref = cfg["ref"]; pct = None
        if ref:
            mid = (ref[0] + ref[1]) / 2.0
            pct = round((vv - mid) / mid * 100.0, 1)
        rec = dict(name_en=cfg["en"], name_ja=cfg["ja"], category=cfg["category"],
                   source="aseg:" + "+".join(map(str, cfg["ids"])),
                   faces=int(len(m.faces)),
                   volume_mm3_measured=vv,
                   reference_range_mm3=ref,
                   reference_source=(REF_SOURCE if ref else None),
                   pct_diff_vs_reference=pct,
                   centroid_mm=[round(float(x), 1) for x in m.centroid],
                   color=cfg["color"])
        records[key] = rec
        if key in deep_keys:
            meshes[key] = m
        flag = "" if not ref else ("OK" if ref[0] <= vv <= ref[1]
                                   else ("HIGH" if vv > ref[1] else "LOW"))
        print(f"  {key:20s} faces={len(m.faces):6d} vol={vv:8.0f}mm3 "
              f"ref={ref} {flag} ({'in GLB' if key in deep_keys else 'json only'})")

    # export GLB (only INCLUDE set)
    scene = trimesh.Scene()
    for key, m in meshes.items():
        mm = m.copy()
        col = (CORTEX.get(key) or DEEP.get(key))["color"]
        mm.visual = trimesh.visual.ColorVisuals(mm, face_colors=col + [255])
        scene.add_geometry(mm, node_name=key, geom_name=key)
    glb = trimesh.exchange.gltf.export_glb(scene, include_normals=True)
    with open(args.out, "wb") as fh:
        fh.write(glb)
    total_faces = sum(len(m.faces) for m in meshes.values())
    print(f"\nExported {args.out}  ({os.path.getsize(args.out)/1e6:.2f} MB), "
          f"nodes={len(meshes)}, faces={total_faces}")

    # structures.json (record for ALL measured structures)
    meta = dict(
        template="fsaverage (FreeSurfer average brain)",
        deep_source="fsaverage/mri/aseg.mgz",
        cortex_source="fsaverage/surf/{lh,rh}.pial",
        coordinate_space="FreeSurfer surface RAS (tkrRAS); x>0 = RIGHT",
        marching_cubes_level=0.5,
        note=("Average-brain model. Volumes are recorded as measured and are "
              "NOT corrected. Do not use for quantitative volumetry or clinical "
              "purposes. See README known-limitations."),
        included_in_glb=list(meshes.keys()),
    )
    with open("structures.json", "w") as fh:
        json.dump(dict(meta=meta, structures=records), fh,
                  ensure_ascii=False, indent=2)
    print("Wrote structures.json  (%d structures recorded)" % len(records))

if __name__ == "__main__":
    main()
