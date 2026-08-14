# Brain 3D Model

**English** | [日本語](README.ja.md)

An anatomically accurate 3D model of the brain plus an interactive in-browser viewer.
For research and education. Reconstructed from a public standard-brain template/atlas (fsaverage).

> ⚠️ **This is an "average reference brain," not any individual's brain. It cannot be used for diagnosis, surgical planning, or quantitative measurement.** (see "Known limitations")

25 structures (cerebral cortex L/R, 7 subcortical pairs, cerebellum L/R, brainstem, ventral diencephalon L/R, ventricular system) are stored as **individual meshes** in a single GLB. Total 269,936 faces / 6.85 MB. The viewer supports rotation, cross-sections (with filled caps), structure selection, volume display, and a JA/EN language toggle.

---

## 1. Reproduction steps (copy-paste runnable)

Prerequisites: macOS/Linux, [uv](https://docs.astral.sh/uv/) (e.g. `brew install uv`). Network connection required.

```bash
# enter this repository's project folder
cd brain_model

# create an isolated Python 3.12 environment (system Python is left untouched)
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

# fetch data -> build GLB (downloads fsaverage automatically)
#   --include all      : all 25 structures
#   --include minimal  : cortex + thalamus + hippocampus only (smoke test)
.venv/bin/python build_brain_mesh.py --include all --out brain.glb

# start the viewer (file:// fails to load the GLB due to CORS, so serve over HTTP)
.venv/bin/python -m http.server 8731
#   -> open  http://localhost:8731/viewer.html  in a browser
```

**Time estimate** (measured on 10-core / 24 GB, Apple Silicon)
- Environment setup (uv + install deps): ~1–2 min
- fsaverage first download: ~20–60 s (network-dependent, ~240 MB)
- `build_brain_mesh.py --include all`: ~1–2 min
- Total first run: ~5 min

**Disk usage estimate**
- `.venv` (all dependencies): ~1.5 GB
- fsaverage data (`~/mne_data`): ~250 MB / Harvard-Oxford (`~/nilearn_data`, only for Step 1 verification): ~1 GB
- Generated outputs (`brain.glb` etc.): ~10 MB

## 2. Data sources and license

| Use | Data | Space | Fetch |
|---|---|---|---|
| Cortical surface | fsaverage `surf/{lh,rh}.pial` | FreeSurfer surface RAS (tkrRAS) | `mne.datasets.fetch_fsaverage()` |
| Deep structures | fsaverage `mri/aseg.mgz` (FreeSurfer aseg segmentation) | same (matched to surface via `vox2ras-tkr`) | same |

Because the cortical surface and the deep structures come from the **same fsaverage subject**, they align without any additional spatial registration (coordinate space tkrRAS, `x>0` = subject's right).

**Source references**
- fsaverage / cortical surface method: Fischl B, Sereno MI, Tootell RBH, Dale AM. *Human Brain Mapping* 8:272–284 (1999).
- aseg (automated subcortical segmentation): Fischl B, et al. "Whole brain segmentation." *Neuron* 33:341–355 (2002).
- Desikan-Killiany atlas (cortical parcellation; **not included** here, a future extension): Desikan RS, et al. *NeuroImage* 31:968–980 (2006).
- ICBM152 2009c (used for spatial verification in Step 1, **not adopted** in the final model): Fonov V, et al. *NeuroImage* (2011).
- Harvard-Oxford (considered in Step 1, **not adopted**): FSL / Harvard Center for Morphometric Analysis.

**Usage / redistribution terms (important)**
- fsaverage / aseg are distributed as part of **FreeSurfer** and follow the [FreeSurfer Software License](https://surfer.nmr.mgh.harvard.edu/registration.html). **Free to use and redistribute for research purposes.** Not for clinical/diagnostic use.
- This model (GLB / meshes) is a **derivative** of fsaverage aseg and pial. If you publish or redistribute it, you must include the following attribution:
  - "Derived from FreeSurfer's fsaverage subject (aseg segmentation and pial surfaces). Fischl et al., Neuron 2002; Fischl et al., Human Brain Mapping 1999."
- **The AAL atlas is not used** (its non-commercial / attribution constraints would be problematic for publication).
- Three.js (viewer, loaded via CDN) is MIT-licensed.

## 3. Included structures

Label IDs follow FreeSurfer aseg (FreeSurferColorLUT). Volumes are **as measured (uncorrected)**. Reference values are representative adult normal ranges from MRI manual-tracing studies. "diff %" is the difference from the midpoint of the reference range.

| Structure (EN) | JA name | Source / label ID | Faces | Measured vol (mm³) | Reference (mm³) | diff % |
|---|---|---|---|---|---|---|
| Cerebral Cortex (Left) | 大脳皮質（左） | lh.pial | 60,000 | (surface area 76,433 mm²) | — | — |
| Cerebral Cortex (Right) | 大脳皮質（右） | rh.pial | 60,000 | (surface area 76,361 mm²) | — | — |
| Thalamus (Left) | 視床（左） | aseg 10 | 5,000 | 8,610 | 6,000–8,000 | +23.0% |
| Thalamus (Right) | 視床（右） | aseg 49 | 5,000 | 8,589 | 6,000–8,000 | +22.7% |
| Caudate (Left) | 尾状核（左） | aseg 11 | 5,000 | 3,627 | 3,000–4,000 | +3.6% |
| Caudate (Right) | 尾状核（右） | aseg 50 | 5,000 | 3,852 | 3,000–4,000 | +10.1% |
| Putamen (Left) | 被殻（左） | aseg 12 | 5,000 | 7,242 | 4,000–5,500 | +52.5% |
| Putamen (Right) | 被殻（右） | aseg 51 | 5,000 | 6,872 | 4,000–5,500 | +44.7% |
| Pallidum (Left) | 淡蒼球（左） | aseg 13 | 2,776 | 1,765 | 1,500–2,200 | -4.6% |
| Pallidum (Right) | 淡蒼球（右） | aseg 52 | 2,792 | 1,804 | 1,500–2,200 | -2.5% |
| Hippocampus (Left) | 海馬（左） | aseg 17 | 5,000 | 5,165 | 3,000–4,500 | +37.7% |
| Hippocampus (Right) | 海馬（右） | aseg 53 | 5,000 | 5,387 | 3,000–4,500 | +43.7% |
| Amygdala (Left) | 扁桃体（左） | aseg 18 | 2,856 | 1,941 | 1,200–1,900 | +25.2% |
| Amygdala (Right) | 扁桃体（右） | aseg 54 | 3,132 | 2,228 | 1,200–1,900 | +43.7% |
| Accumbens (Left) | 側坐核（左） | aseg 26 | 1,712 | 778 | 400–700 | +41.5% |
| Accumbens (Right) | 側坐核（右） | aseg 58 | 1,672 | 757 | 400–700 | +37.6% |
| Cerebellum (Left) | 小脳（左） | aseg 8+7 | 22,000 | 77,618 | 55,000–75,000 | +19.4% |
| Cerebellum (Right) | 小脳（右） | aseg 47+46 | 22,000 | 77,851 | 55,000–75,000 | +19.8% |
| Brainstem | 脳幹 | aseg 16 | 8,000 | 26,629 | 20,000–35,000 | -3.2% |
| Ventral Diencephalon (Left) | 腹側間脳（左） | aseg 28 | 6,000 | 5,142 | — | — |
| Ventral Diencephalon (Right) | 腹側間脳（右） | aseg 60 | 6,000 | 5,076 | — | — |
| Lateral Ventricle (Left) | 側脳室（左） | aseg 4+5 | 12,000 | 22,020 | — | — |
| Lateral Ventricle (Right) | 側脳室（右） | aseg 43+44 | 12,000 | 20,176 | — | — |
| Third Ventricle | 第三脳室 | aseg 14 | 3,244 | 1,941 | — | — |
| Fourth Ventricle | 第四脳室 | aseg 15 | 3,752 | 2,237 | — | — |
| **Total** |  |  | **269,936** |  |  |  |

- The lateral ventricle merges the body (4/43) + inferior horn (5/44). The cerebellum merges cortex (8/47) + white matter (7/46).
- Full machine-readable data is in `structures.json` (measured volume, reference value, diff %, color, centroid).

## 4. Processing pipeline

`build_brain_mesh.py`:
1. Build a binary mask per aseg label
2. Gaussian smoothing (σ = 0.5 voxel)
3. Isosurface via marching cubes (**level fixed at 0.5, never varied per structure**)
4. Taubin smoothing (with shrink correction, 5 iterations) / connected-component cleanup (remove components < 1% of the largest)
5. **Per-structure** face reduction (below). Convert to surface RAS (mm) via `vox2ras-tkr`, export a single GLB with normals

Decimation varies by structure characteristics (a uniform ratio is not acceptable):
- Cortex: 60,000 per hemisphere / subcortical nuclei: 5,000 (pallidum, amygdala, accumbens whose natural face count is below this are left un-decimated)
- Cerebellum: 22,000/hemisphere (light, to preserve foliation) / brainstem: 8,000 / ventral diencephalon: 6,000
- Lateral ventricle: 12,000/hemisphere (to keep the inferior-horn detail) / **third & fourth ventricles: not decimated** (thin & narrow — a floor to prevent breakage)

## 5. Viewer features (`viewer.html`)

Single HTML / Three.js r160 (CDN importmap) / external GLB reference.
- **JA/EN language toggle** (top-right button; switches all UI text and structure names live, preserving current state)
- OrbitControls (rotate / zoom / pan)
- Structure tree (category → individual, visibility toggle + opacity slider, per-category bulk toggle)
- 6 preset views (front/back/left/right/top/bottom, anatomically correct, with L/R labels)
- **3 orthogonal clipping sections** (sagittal / coronal / axial, position slider + direction flip) + **section caps** (filled with structure color; toggle on/off)
- Click-to-select a structure (shows EN/JA name, category, volume mm³, diff % vs reference; highlights it)
- One-click "make cortex translucent to see deep structures"
- mm grid, L/R labels (anchored to world coordinates so left/right cannot be swapped)
- PNG export (with transparent-background option)

## 6. Verification results (measured)

- **Orientation**: all structures `x<0` = left / `x>0` = right (RAS convention, no swap)
- **L/R symmetry**: paired-structure volume difference ≤10% (exception: amygdala 12.9% = average-brain artifact)
- **Scale**: L-R 139 mm / A-P 174 mm / S-I 149 mm (≈ real size)
- **Interpenetration**: penetration depth ≤0.1 mm for the specified adjacent pairs (only tiny contact from smoothing of mutually exclusive labels). Subcortical nuclei (caudate/putamen/pallidum/accumbens) poke-through of cortex: 0%
- **Faces / size**: 269,936 faces (target ≤300,000) / 6.85 MB (target ≤50 MB)
- **Viewer**: axial, coronal, and sagittal sections all render correctly in a headless browser, caps intact, **~60 fps**, no console errors

## 7. Known limitations (do not omit)

1. **It is an average brain**: derived from fsaverage (a FreeSurfer standard brain averaging ~40 brains), so it is **not any individual's brain**. It does not represent individual shape, asymmetry, or lesions.
2. **Volumes differ systematically from manual tracing**: each structure's volume runs **systematically larger** than a manual-tracing measurement protocol (putamen +~50%, hippocampus +~40%, thalamus +~23%, etc. / see `structures.json`). This is a **known systematic difference, not an error**, due to (a) blurred boundaries because it is an average brain, and (b) the **boundary-definition protocol difference** between FreeSurfer aseg and manual tracing. Corrections to match reference values (mask shrinking, threshold tuning) are **intentionally NOT applied**. → **Do not use this model for quantitative volumetry.**
3. **The brainstem is not subdivided**: a single aseg label (ID=16), with **no distinction of midbrain / pons / medulla**.
4. **The cerebellar vermis is not separated**: the cerebellum is one mesh per hemisphere (cortex + white matter); the midline vermis is not split out.
5. **Not for clinical use**: being an average brain, it **cannot be used for diagnosis or surgical planning**.
6. **Section-cap limitations**:
   - Because caps fill each structure's closed surface via stencil, structures that are **non-watertight / self-intersecting** (some ventricles and the cerebellum) may show slightly ragged cut edges (no conspicuous breakage observed in practice).
   - Smoothing of mutually exclusive labels overlaps boundaries by up to ~0.1 mm, so cut boundaries of adjacent structures may overlap very slightly where they nearly touch.
   - Oblique (arbitrary-direction) sections are not supported (orthogonal 3 directions only).

## 8. Design decisions and rationale (so the reasoning can be traced later)

- **Why deep structures were unified on fsaverage aseg rather than Harvard-Oxford**:
  Step 1 verification found that (1) Harvard-Oxford has **no cerebellar parcellation**, and (2) the HO volume space (FSL MNI152) is a **different space from the fsaverage cortical surface**, giving a few-mm misalignment. In contrast, **aseg includes all subcortical, cerebellum, brainstem, and ventricles**, and lives in the **same subject (same tkrRAS space) as the fsaverage cortical surface**, so all structures align without extra registration. A single-subject aseg (closer to literature values) was also considered but rejected because it would break alignment with the fsaverage surface — defeating the purpose.
- **Why volumes were not corrected**:
  The systematic volume difference is not an atlas probability-threshold issue but stems from the **boundary-definition protocol difference** (a separate matter from the marching-cubes isosurface level of 0.5). We present the aseg output as-is and record measured value, reference value, and diff % in `structures.json` and this README to **ensure transparency**. Corrections are not applied because they would distort the anatomical shape.
- **Why tkrRAS was adopted as the coordinate system**:
  The pial surface is defined in tkrRAS, and aseg can be converted to the same coordinates via `vox2ras-tkr`, so the two overlay without any transform.

## 9. Future extension candidates (recorded only, not implemented)

- **Desikan-Killiany cortical 34-region parcellation**: color/label the cortex by region using fsaverage `?h.aparc.annot` (bundled with templateflow / FreeSurfer).
- **Arbitrary-direction (oblique) clipping plane**: in addition to the current 3 orthogonal planes, a free-normal clipping plane.
- **MRI cross-section texture display**: paint T1 (fsaverage `mri/T1.mgz`) slice images onto the cut planes.
- **Brainstem subdivision (midbrain / pons / medulla)**: FreeSurfer Brainstem Substructures (ICBM152 2009c space) / SUIT and other additional atlases (license check required).
- **Detailed cerebellar parcellation / vermis separation**: SUIT atlas.
- **3D-print support**: make each structure watertight, export STL, ensure minimum wall thickness.

## 10. Deliverables

| File | Contents |
|---|---|
| `build_brain_mesh.py` | Reproducible data-fetch-to-GLB script (`--include all|minimal`) |
| `requirements.txt` | Pinned versions |
| `brain.glb` | The generated 3D model (25 structures) |
| `structures.json` | Label, EN/JA name, color, measured volume, reference value, diff % |
| `viewer.html` | Web viewer (open via HTTP; has a JA/EN toggle) |
| `viewer_standalone.html` | **Fully self-contained single file** (Three.js + GLB + structures embedded). Opens by double-click, offline, no server. |
| `build_standalone.py` | Builds `viewer_standalone.html` from the sources |
| `viewer_stable.html` | Stable pre-caps viewer (preservation copy) |
| `README.md` / `README.ja.md` | This file (English) / Japanese version |
| `step1_inspect.py` / `verify_aseg.py` / `interp_check.py` / `test_caps.py` / `test_i18n.py` | Verification scripts (data-space check, volume check, interpenetration check, cap check, i18n toggle check) |
| `drive_viewer.py` / `drive_full.py` | Headless-browser drivers (screenshots + FPS verification) |

Git: tag `v1.0-nocaps` = verified pre-caps version (`git checkout v1.0-nocaps` to restore); tag `v1.1-caps` = with section caps.

## References
- Fischl B, Sereno MI, Tootell RBH, Dale AM. High-resolution intersubject averaging and a coordinate system for the cortical surface. *Human Brain Mapping* 8:272–284 (1999).
- Fischl B, et al. Whole brain segmentation: automated labeling of neuroanatomical structures (aseg). *Neuron* 33:341–355 (2002).
- Desikan RS, et al. An automated labeling system... (Desikan-Killiany). *NeuroImage* 31:968–980 (2006).
- Fonov V, et al. Unbiased average age-appropriate atlases (ICBM152 2009c). *NeuroImage* (2011).
- Structure reference volume ranges are representative adult normal ranges from MRI manual-tracing studies (see `reference_source` in `structures.json`).
