"""
Step 1: データ取得と空間整合性の確認
Fetch standard templates/atlases and report affine, voxel size, shape, and label lists.
This does NOT build any mesh; it only downloads and inspects.
"""
import numpy as np
import nibabel as nib
from nilearn import datasets


def vox_size(affine):
    return np.sqrt((affine[:3, :3] ** 2).sum(axis=0))


def report_img(name, img):
    aff = img.affine
    print(f"\n### {name}")
    print(f"  shape      : {img.shape}")
    print(f"  voxel (mm) : {np.round(vox_size(aff), 4).tolist()}")
    print(f"  dtype      : {img.get_fdata().dtype if False else img.get_data_dtype()}")
    print(f"  affine     :")
    for row in np.round(aff, 3):
        print(f"    {row.tolist()}")
    # origin = world coord of voxel (0,0,0) and of center
    center_vox = np.array(img.shape[:3]) / 2.0
    center_world = aff[:3, :3] @ center_vox + aff[:3, 3]
    print(f"  world @ vox(0,0,0) : {np.round(aff[:3,3],2).tolist()}")
    print(f"  world @ center     : {np.round(center_world,2).tolist()}")
    return aff


print("=" * 70)
print("STEP 1: DATA ACQUISITION & SPATIAL CONSISTENCY CHECK")
print("=" * 70)

# ---------------------------------------------------------------- ICBM152 2009c
print("\n[1] ICBM152 2009c nonlinear asymmetric template ...")
icbm = datasets.fetch_icbm152_2009()
print("  keys:", [k for k in icbm.keys() if not k.startswith("_")] if hasattr(icbm, "keys") else dir(icbm))
t1 = nib.load(icbm["t1"])
icbm_aff = report_img("ICBM152 2009c T1", t1)

# ---------------------------------------------------------- Harvard-Oxford cort
print("\n[2] Harvard-Oxford CORTICAL (maxprob thr25, 1mm) ...")
ho_cort = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-1mm")
cort_img = ho_cort["maps"] if not isinstance(ho_cort["maps"], str) else nib.load(ho_cort["maps"])
if isinstance(cort_img, str):
    cort_img = nib.load(cort_img)
cort_aff = report_img("HO cortical maxprob-thr25-1mm", cort_img)
cort_labels = ho_cort["labels"]
print(f"  #labels (incl background): {len(cort_labels)}")

# ------------------------------------------------------------ Harvard-Oxford sub
print("\n[3] Harvard-Oxford SUBCORTICAL (maxprob thr25, 1mm) ...")
ho_sub = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr25-1mm")
sub_img = ho_sub["maps"]
if isinstance(sub_img, str):
    sub_img = nib.load(sub_img)
sub_aff = report_img("HO subcortical maxprob-thr25-1mm", sub_img)
sub_labels = ho_sub["labels"]

# ----------------------------------------------------------------- fsaverage6
print("\n[4] fsaverage6 surface ...")
fs = datasets.fetch_surf_fsaverage(mesh="fsaverage6")
print("  keys:", list(fs.keys()))
try:
    import nibabel.freesurfer.io as fsio
    coords, faces = nib.freesurfer.read_geometry(fs["pial_left"]) if False else (None, None)
except Exception as e:
    pass
# load pial coords via nilearn surface loader
from nilearn import surface
pial_l = surface.load_surf_mesh(fs["pial_left"])
print(f"  pial_left  : {pial_l[0].shape[0]} verts, {pial_l[1].shape[0]} faces")
print(f"  pial_left coord range x[{pial_l[0][:,0].min():.1f},{pial_l[0][:,0].max():.1f}] "
      f"y[{pial_l[0][:,1].min():.1f},{pial_l[0][:,1].max():.1f}] "
      f"z[{pial_l[0][:,2].min():.1f},{pial_l[0][:,2].max():.1f}]")

# ------------------------------------------------------------- label listings
print("\n" + "=" * 70)
print("LABEL LISTS")
print("=" * 70)
print("\n--- Harvard-Oxford CORTICAL labels (%d) ---" % len(cort_labels))
for i, l in enumerate(cort_labels):
    print(f"  {i:3d}  {l}")
print("\n--- Harvard-Oxford SUBCORTICAL labels (%d) ---" % len(sub_labels))
for i, l in enumerate(sub_labels):
    print(f"  {i:3d}  {l}")

# ------------------------------------------------ spatial consistency summary
print("\n" + "=" * 70)
print("SPATIAL CONSISTENCY SUMMARY")
print("=" * 70)
same_cort_sub = np.allclose(cort_aff, sub_aff) and cort_img.shape == sub_img.shape
print(f"  HO cort vs HO sub  : same affine & shape? {same_cort_sub}")
print(f"  ICBM152 vs HO cort : same affine & shape? "
      f"{np.allclose(icbm_aff, cort_aff) and t1.shape==cort_img.shape}")
print("  (fsaverage is a SURFACE in FreeSurfer tkrRAS-like space, not MNI152 voxel space)")

# ------------------------------------------ probe cerebellum atlas availability
print("\n--- Cerebellum atlas availability probe ---")
for attr in dir(datasets):
    if "cereb" in attr.lower() or "aal" in attr.lower():
        print("  candidate fetcher:", attr)
print("  (Harvard-Oxford subcortical does NOT include cerebellum parcellation)")

print("\nDONE step 1.")
