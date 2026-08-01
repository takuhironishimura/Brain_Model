# 脳3Dモデル / Brain 3D Model

解剖学的に正確な脳の3Dモデルと、ブラウザで閲覧できるインタラクティブビューア。
研究・教育用途。公開標準脳テンプレート／アトラスから再構成。

> **これは特定個人の脳ではなく「平均的な参照脳」です。診断・手術計画・定量計測には使用できません。**（詳細は「既知の制限」）

---

## データ出典 / Data sources

| 用途 | データ | 空間 |
|---|---|---|
| 皮質表面 | fsaverage `surf/{lh,rh}.pial`（FreeSurfer） | FreeSurfer surface RAS (tkrRAS) |
| 深部構造（皮質下・小脳・脳幹・脳室・腹側間脳） | fsaverage `mri/aseg.mgz`（FreeSurfer aseg） | 同上（`vox2ras-tkr` 経由で表面と一致） |

皮質表面と深部を**同一の fsaverage subject** から取得しているため、両者は追加の空間登録なしに整合します（座標系は tkrRAS、`x>0` が右）。

- fsaverage / aseg 取得: `mne.datasets.fetch_fsaverage()`（MNE-Python 経由でダウンロード）
- FreeSurfer / fsaverage: Fischl et al., *Human Brain Mapping* (1999); aseg 法: Fischl et al., *Neuron* (2002)

> 当初検討した Harvard-Oxford / ICBM152 2009c は、小脳パーセレーションを欠く・皮質表面と別空間になる等の理由から採用しませんでした（`step1_inspect.py` に検証記録）。AAL はライセンス制約のため不使用。

## 処理パイプライン

`build_brain_mesh.py`：
1. aseg ラベルごとに二値マスク生成
2. ガウシアン平滑化（σ=0.5 voxel）
3. marching cubes で等値面抽出（**閾値 0.5 固定・構造ごとに変えない**）
4. Taubin 平滑化（収縮補正あり、5回）／連結成分クリーンアップ（最大成分の1%未満を除去）
5. 二次誤差計量による面数削減（皮質 各半球 ≤60,000面、皮質下 ≤5,000面、小脳・脳幹 ≤8,000面）
6. `vox2ras-tkr` で表面 RAS(mm) へ変換
7. 単一 GLB にエクスポート（ノード名＝構造名、マテリアル単位で色分け）

体積は `structures.json` に記録：実測体積(mm³)・参照文献値範囲・出典・差(%)。

## 実行手順

```bash
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
# 最小構成（皮質L/R + 視床 + 海馬）
.venv/bin/python build_brain_mesh.py --include minimal --out brain.glb
# 全構造
.venv/bin/python build_brain_mesh.py --include all --out brain.glb
# ビューア
open viewer.html   # brain.glb を同ディレクトリに置く
```

## 成果物

| ファイル | 内容 |
|---|---|
| `build_brain_mesh.py` | データ取得〜GLB生成の再現可能スクリプト |
| `requirements.txt` | バージョン固定 |
| `brain.glb` | 生成された3Dモデル |
| `structures.json` | ラベル・英名・和名・色・実測体積・文献値・差(%) |
| `viewer.html` | Webビューア |
| `README.md` | 本ファイル |

---

## 既知の制限 / Known limitations

1. **平均脳である**：本モデルは fsaverage（約40脳を平均した FreeSurfer 標準脳）の aseg 由来であり、**特定個人の脳ではありません**。個々の脳の形状・非対称・病変は表現しません。

2. **体積は手動計測より系統的に大きい**：各構造の体積は、手動トレースによる計測プロトコルと比較して**系統的に大きく出ます**（例：海馬 +約38%、視床 +約23%、小脳 +約19%／`structures.json` 参照）。これは
   - fsaverage が平均脳であるため境界がぼける、
   - FreeSurfer aseg と手動トレースで**境界定義プロトコルが異なる**、
   という理由による**既知の系統差であり、エラーではありません**。体積を文献値に合わせるためのマスク収縮・閾値調整などの補正は**意図的に行っていません**。

3. **定量計測に使用しないこと**：上記のとおり体積が系統的に偏るため、本モデルを**体積の定量的計測に使用しないでください**。

4. **臨床利用不可**：標準脳テンプレート由来の平均脳であり、**診断・手術計画には使用できません**。

### その他の技術的制限
- 脳幹は aseg の単一ラベル（中脳・橋・延髄への細分なし）。細分には別アトラス（FreeSurfer Brainstem Substructures／SUIT 等、要ライセンス確認）が必要。
- 小脳は左右半球（皮質＋白質）を各1メッシュとし、虫部（vermis）は分離していない。
- 皮質区分は現状 左右半球単位。Desikan-Killiany 等の領域区分は今後追加予定。
- 扁桃体の左右差が約13%（fsaverage 平均脳由来のアーティファクト）。向きは全構造で検証済み（`x>0` が右）。

## ライセンス

- fsaverage / FreeSurfer データ: FreeSurfer Software License（研究用途、要帰属表示）に従うこと。外部公開時は各データの帰属表示を確認。
- 本モデルは研究・教育目的。臨床・診断用途不可。

## 参照文献 / References
- Fischl B, et al. Cortical surface-based analysis / fsaverage. *Human Brain Mapping* (1999).
- Fischl B, et al. Whole brain segmentation (aseg). *Neuron* 33:341–355 (2002).
- 各構造の参照体積範囲は成人 MRI 手動トレース研究に基づく代表的正常範囲（`structures.json` の `reference_source` を参照）。
