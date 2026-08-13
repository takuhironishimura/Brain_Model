# 脳3Dモデル / Brain 3D Model

[English](README.md) | **日本語**

解剖学的に正確な脳の3Dモデルと、ブラウザで閲覧できるインタラクティブビューア。
研究・教育用途。公開標準脳テンプレート／アトラス（fsaverage）から再構成。

> ⚠️ **これは特定個人の脳ではなく「平均的な参照脳」です。診断・手術計画・定量計測には使用できません。**（→「既知の制限」）

25構造（大脳皮質左右・皮質下7対・小脳左右・脳幹・腹側間脳左右・脳室系）を**個別メッシュ**として単一 GLB に収録。総面数 269,936 / 6.85 MB。ビューアは回転・断面（キャップ塗りつぶし付き）・構造選択・体積表示・日英切替に対応。

---

## 1. 再現手順（コピペ実行可）

前提: macOS/Linux、[uv](https://docs.astral.sh/uv/)（`brew install uv` など）。ネットワーク接続必須。

```bash
# 取得（このリポジトリの brain_model/ に入る）
cd brain_model

# Python 3.12 の隔離環境を作成（システム Python は変更しない）
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

# データ取得〜GLB生成（fsaverage を自動ダウンロード）
#   --include all  : 全25構造
#   --include minimal : 皮質+視床+海馬のみ（動作確認用）
.venv/bin/python build_brain_mesh.py --include all --out brain.glb

# ビューアを起動（file:// では GLB 読込が CORS で失敗するため HTTP 配信する）
.venv/bin/python -m http.server 8731
#   → ブラウザで  http://localhost:8731/viewer.html  を開く
```

**所要時間の目安**（10コア/24GB, Apple Silicon 実測）
- 環境構築（uv + 依存インストール）: 約1–2分
- fsaverage 初回ダウンロード: 約20–60秒（回線依存、約240MB）
- `build_brain_mesh.py --include all`: 約1–2分
- 合計: 初回 約5分程度

**ディスク使用量の目安**
- `.venv`（依存一式）: 約1.5 GB
- fsaverage データ（`~/mne_data`）: 約250 MB／Harvard-Oxford 検証用（`~/nilearn_data`、Step1 検証時のみ）: 約1 GB
- 生成物（`brain.glb` ほか）: 約10 MB

## 2. データ出典とライセンス

| 用途 | データ | 空間 | 取得 |
|---|---|---|---|
| 皮質表面 | fsaverage `surf/{lh,rh}.pial` | FreeSurfer surface RAS (tkrRAS) | `mne.datasets.fetch_fsaverage()` |
| 深部構造 | fsaverage `mri/aseg.mgz`（FreeSurfer aseg セグメンテーション） | 同上（`vox2ras-tkr` で表面と一致） | 同上 |

皮質表面と深部を**同一 fsaverage subject** から取得しているため、両者は追加の空間登録なしに整合します（座標系 tkrRAS、`x>0`＝被験者の右）。

**出典文献**
- fsaverage / 皮質表面法: Fischl B, Sereno MI, Tootell RBH, Dale AM. *Human Brain Mapping* 8:272–284 (1999).
- aseg（皮質下自動セグメンテーション法）: Fischl B, et al. "Whole brain segmentation." *Neuron* 33:341–355 (2002).
- Desikan-Killiany アトラス（皮質区分、本モデルでは**未収録**・将来拡張候補）: Desikan RS, et al. *NeuroImage* 31:968–980 (2006).
- ICBM152 2009c（Step1 で空間検証に使用、最終モデルには**不採用**）: Fonov V, et al. *NeuroImage* (2011).
- Harvard-Oxford（Step1 で検討、**不採用**）: FSL / Harvard Center for Morphometric Analysis.

**利用・再配布条件（重要）**
- fsaverage / aseg は **FreeSurfer** の一部として配布され、[FreeSurfer Software License](https://surfer.nmr.mgh.harvard.edu/registration.html) に従います。**研究目的で利用・再配布可**。臨床診断用途は不可。
- 本モデル（GLB／メッシュ）は fsaverage aseg・pial の**派生物**です。公開・再配布する場合は次の帰属表示を必ず含めてください。
  - 「Derived from FreeSurfer's fsaverage subject (aseg segmentation and pial surfaces). Fischl et al., Neuron 2002; Fischl et al., Human Brain Mapping 1999.」
- **AAL アトラスは使用していません**（非商用・帰属制約があり公開時に問題となるため）。
- Three.js（ビューア、CDN 読込）は MIT ライセンス。

## 3. 収録構造一覧

ラベルIDは FreeSurfer aseg（FreeSurferColorLUT）準拠。体積は**実測（補正なし）**。文献値は成人 MRI 手動トレース研究の代表的正常範囲。差%は文献値レンジ中央値との差。

| 構造 (EN) | 和名 | ソース/ラベルID | 面数 | 実測体積(mm³) | 文献値(mm³) | 差% |
|---|---|---|---|---|---|---|
| Cerebral Cortex (Left) | 大脳皮質（左） | lh.pial | 60,000 | (表面積 76,433mm²) | — | — |
| Cerebral Cortex (Right) | 大脳皮質（右） | rh.pial | 60,000 | (表面積 76,361mm²) | — | — |
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
| **合計** |  |  | **269,936** |  |  |  |

- 側脳室は側脳室本体（4/43）＋下角（5/44）を統合。小脳は皮質（8/47）＋白質（7/46）を統合。
- 完全な機械可読データは `structures.json`（実測体積・文献値・差%・色・重心を格納）。

## 4. 処理パイプライン

`build_brain_mesh.py`：
1. aseg ラベルごとに二値マスク生成
2. ガウシアン平滑化（σ=0.5 voxel）
3. marching cubes で等値面抽出（**閾値 0.5 固定・構造ごとに変えない**）
4. Taubin 平滑化（収縮補正あり、5回）／連結成分クリーンアップ（最大成分の1%未満を除去）
5. **構造別**の面数削減（下記）。`vox2ras-tkr` で表面RAS(mm)へ変換、法線付きで単一GLBへ

面数削減は構造特性に応じて変えています（一律比率は不可）:
- 皮質: 各半球 60,000 / 皮質下核: 5,000（自然面数がこれ未満の淡蒼球・扁桃体・側坐核は未削減）
- 小脳: 22,000/半球（foliation 保持のため軽め）/ 脳幹: 8,000 / 腹側間脳: 6,000
- 側脳室: 12,000/半球（下角の細部保持）/ **第三・第四脳室: 削減しない**（薄く細いため破断防止の下限確保）

## 5. ビューア機能（`viewer.html`）

単一HTML / Three.js r160（CDN importmap）/ GLB外部参照。
- **日英切替トグル**（右上ボタン。UI全文言と構造名をその場で切替、状態は保持）
- OrbitControls（回転・ズーム・パン）
- 構造ツリー（分類→個別、表示トグル＋不透明度スライダー、分類一括）
- プリセット6方向（前後左右上下、解剖学的方向・L/Rラベル付き）
- **直交3断面クリッピング**（矢状・冠状・水平、位置スライダー＋方向反転）＋**切断面キャップ**（構造色で塗りつぶし。トグルで ON/OFF）
- 構造クリック選択（英/和名・分類・体積mm³・文献差%を表示、ハイライト）
- 「皮質を半透明にして深部を見る」ワンクリック
- mmグリッド・L/Rラベル（ワールド座標固定で取り違え不能）
- PNG書き出し（透過背景オプション）

## 6. 検証結果（実測）

- **向き**: 全構造で `x<0`＝左 / `x>0`＝右（RAS準拠、取り違えなし）
- **左右対称性**: 対構造の体積差 ≤10%（例外: 扁桃体 12.9%＝平均脳由来のアーティファクト）
- **スケール**: L-R 139mm / A-P 174mm / S-I 149mm（≒実寸）
- **干渉**: 指定隣接ペアの貫入深さ ≤0.1mm（相互排他ラベルの平滑化由来の微小接触のみ）。皮質下核（尾状核・被殻・淡蒼球・側坐核）の皮質突き抜け 0%
- **面数/サイズ**: 269,936面（目標≤300,000）/ 6.85MB（目標≤50MB）
- **ビューア**: ヘッドレスブラウザで水平断・冠状断・矢状断すべて正しく描画、キャップ破綻なし、**約60fps**、コンソールエラーなし

## 7. 既知の制限（省略不可）

1. **平均脳である**: fsaverage（約40脳を平均した FreeSurfer 標準脳）由来であり、**特定個人の脳ではありません**。個々の形状・非対称・病変は表現しません。
2. **体積が手動計測と系統的に異なる**: 各構造の体積は手動トレース計測プロトコルと比較して**系統的に大きく**出ます（被殻 +約50%、海馬 +約40%、視床 +約23% 等／`structures.json` 参照）。これは (a) 平均脳ゆえの境界のぼけ、(b) FreeSurfer aseg と手動トレースの**境界定義プロトコルの違い**による**既知の系統差であり、エラーではありません**。体積を文献値に合わせるための補正（マスク収縮・閾値調整）は**意図的に行っていません**。→ **本モデルを体積の定量計測に使用しないでください。**
3. **脳幹が細分されていない**: aseg の単一ラベル（ID=16）で、**中脳・橋・延髄の区別はありません**。
4. **小脳の虫部（vermis）が独立していない**: 小脳は左右半球（皮質＋白質）を各1メッシュとし、正中の虫部を分離していません。
5. **臨床利用不可**: 平均脳由来であり、**診断・手術計画には使用できません**。
6. **断面キャップの制限**:
   - キャップは各構造の閉曲面をステンシルで塗るため、**非watertight／自己交差のある構造**（一部の脳室・小脳）では切断面の縁がわずかに乱れる場合があります（実測では目立つ破綻なし）。
   - 相互排他ラベルの平滑化で境界が最大約0.1mm重なるため、隣接構造の断面境界が極接近箇所でごく僅かに重畳し得ます。
   - 斜め（任意方向）断面は非対応（直交3方向のみ）。

## 8. 設計上の判断と理由（判断を追えるように）

- **深部構造を Harvard-Oxford ではなく fsaverage aseg に統一した理由**:
  Step1 の検証で、(1) Harvard-Oxford には**小脳パーセレーションが無い**、(2) HO 体積空間（FSL MNI152）は**皮質表面 fsaverage とは別空間**で数mmのズレが生じる、ことが判明。一方 **aseg は皮質下・小脳・脳幹・脳室を全て含み**、しかも fsaverage の**皮質表面と同一 subject（同一 tkrRAS 空間）**にあるため、追加の空間登録なしに全構造が整合する。単一被験者 aseg（より文献値に近い）も検討したが、それでは fsaverage 表面との整合が崩れ本末転倒のため不採用とした。
- **体積を補正しなかった理由**:
  体積の系統差はアトラスの確率閾値の問題ではなく**境界定義プロトコルの違い**に由来する（marching cubes の等値面閾値 0.5 とは別問題）。aseg 出力をそのまま提示し、実測値・文献値・差%を `structures.json` と本README に記録することで**透明性を確保**する方針とした。補正は解剖学的形状を歪めるため行わない。
- **座標系に tkrRAS を採用した理由**:
  皮質表面（pial）が tkrRAS で定義され、aseg も `vox2ras-tkr` で同座標に変換できるため、両者を無変換で重ねられる。

## 9. 今後の拡張候補（記録のみ・未実装）

- **Desikan-Killiany による皮質34領域の区分**: fsaverage の `?h.aparc.annot`（templateflow / FreeSurfer 同梱）で皮質を領域別に色分け・ラベル保持。
- **任意方向（斜め）の切断平面**: 現状の直交3平面に加え、自由法線のクリッピング平面。
- **MRI断面テクスチャ表示**: 断面に T1（fsaverage `mri/T1.mgz`）のスライス画像を貼る。
- **脳幹の細分（中脳・橋・延髄）**: FreeSurfer Brainstem Substructures（ICBM152 2009c 空間）／SUIT 等の追加アトラス（要ライセンス確認）。
- **小脳の詳細区分・虫部分離**: SUIT アトラス。
- **3Dプリント対応**: 各構造の watertight 化・STL 出力・最小肉厚確保。

## 10. 成果物

| ファイル | 内容 |
|---|---|
| `build_brain_mesh.py` | データ取得〜GLB生成の再現可能スクリプト（`--include all|minimal`） |
| `requirements.txt` | バージョン固定 |
| `brain.glb` | 生成された3Dモデル（25構造） |
| `structures.json` | ラベル・英名・和名・色・実測体積・文献値・差% |
| `viewer.html` | Webビューア（HTTP配信で開く。日英切替あり） |
| `viewer_stable.html` | キャップ実装前の安定版ビューア（保全用コピー） |
| `README.md` / `README.ja.md` | 英語版 / 本ファイル（日本語版） |
| `step1_inspect.py` / `verify_aseg.py` / `interp_check.py` / `test_caps.py` / `test_i18n.py` | 検証スクリプト（データ空間確認・体積検証・干渉チェック・キャップ検証・日英切替検証） |
| `drive_viewer.py` / `drive_full.py` | ヘッドレスブラウザ検証ドライバ（スクショ＋FPS計測） |

Git: `v1.0-nocaps` タグ＝キャップ実装前の動作確認済み版（`git checkout v1.0-nocaps` で復元可）／`v1.1-caps` タグ＝断面キャップ搭載版。

## 参照文献 / References
- Fischl B, Sereno MI, Tootell RBH, Dale AM. High-resolution intersubject averaging and a coordinate system for the cortical surface. *Human Brain Mapping* 8:272–284 (1999).
- Fischl B, et al. Whole brain segmentation: automated labeling of neuroanatomical structures (aseg). *Neuron* 33:341–355 (2002).
- Desikan RS, et al. An automated labeling system... (Desikan-Killiany). *NeuroImage* 31:968–980 (2006).
- Fonov V, et al. Unbiased average age-appropriate atlases (ICBM152 2009c). *NeuroImage* (2011).
- 構造の参照体積範囲は成人 MRI 手動トレース研究に基づく代表的正常範囲（`structures.json` の `reference_source` を参照）。
