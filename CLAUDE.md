# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## プロジェクト概要

PFERD (Poses for Equine Research Dataset) は、馬の3Dポーズ・体型を扱う研究用データセットの公式コードリポジトリです（Scientific Data 2024 掲載論文の実装）。hSMALモデルを用いた馬の姿勢・体型推定結果の可視化・評価コードを提供します。

このブランチ（`fearture`）では、`README_my_pipeline.md` に記載された独自のデータ処理・可視化パイプラインが追加されています。npzファイル（hSMAL推定結果）から関節の空間座標・軸角・体型パラメータ・親子間距離などを抽出し、CSV化・グラフ化・3D可視化する一連のスクリプト群です。

## セットアップ

Python 3.8 + PyTorch 1.8.2 を前提とした環境です（[uv](https://docs.astral.sh/uv/) で管理）。
依存関係は `pyproject.toml` / `uv.lock` に固定されています。

```bash
git clone --recurse-submodules https://github.com/Celiali/PFERD.git
cd PFERD
uv sync
```

`uv sync` は `.python-version`（3.8）に従って自動的にPythonをダウンロードし、`.venv` に依存パッケージ一式（torch/torchvision/torchaudio はPyTorch LTS 1.8 の cu111 インデックスから）をインストールします。
スクリプトは `uv run python <script>` で実行するか、`.venv` をアクティベートしてから実行してください。

**ezc3d は含まれていません。** PyPI版は Python>=3.10 専用で、torch==1.8.2 が要求する Python 3.8 と共存できないため。
`--VISUAL_MOCAP`（C3Dモーションキャプチャ重畳表示、[Load_Visualization.py](Load_Visualization.py)のオプション機能）を使う場合のみ必要で、npzベースの本パイプライン（`scripts/` 配下）では未使用です。必要な場合は別途 conda 環境で `conda install -c conda-forge ezc3d=1.4.9` するか、CMake+MSVCでソースビルドしてください。

設定は `CONFIG.py` に集約されており、モデルパス・データセットパス・デバイス指定（`DEVICE`）はここを参照します。
`DEVICE` はCUDAが使えない環境では自動的にCPUへフォールバックします（警告表示あり）。

セットアップ後は `uv run python scripts/check_setup.py` で依存パッケージ・モデル/データセットの配置・デバイス設定を確認できます。

**hSMALモデル・PFERDデータセットの入手方法**は README.md の「Access to the hSMAL Model」「Access to
the PFERD Dataset」節を参照してください（hSMALモデルは `hSMALdata/` に、PFERDデータセットは
`dataset/` に、それぞれ配置します）。

**`moshpp` サブモジュールについて（既知の問題・保留中）**: `.gitmodules` が固定しているコミット
（`922ebf9c...`）が upstream の `nghorbani/moshpp` リポジトリから消失しており、
`git clone --recurse-submodules` / `git submodule update --init --recursive` は失敗します
（`fatal: remote error: upload-pack: not our ref ...`）。npzベースの本パイプライン（`scripts/`
配下）は moshpp に依存しないため影響はありませんが、`--VISUAL_MOCAP` や `Eval_3Ddistance.py` 等
upstream の一部機能は現状 moshpp なしでは動作しません。

## ディレクトリ構成

- `hSMALdata/` — hSMALモデル本体（.pkl）とポーズ事前分布
- `dataset/` — 入力データセット（`ID_x/MODEL_DATA/xxxx_hsmal.npz` 形式）
- `moshpp/` — MoSh++連携コード（サブモジュール、`sys.path` に `moshpp/src` を追加して利用）
- `scripts/` — データ処理・可視化パイプラインのスクリプト群（`analysis`, `batch`, `input_dataset`, `input_joint_model_data`, `offset_tools`, `others`, `utils`）
- `utils/` — 共通ユーティリティ（`project.py`, `readfile.py`, `render.py`, `smal.py`）
- `JOINT_MODEL_DATA/` — パイプラインの出力先（空間座標・軸角・体型パラメータ・親子間距離などのCSV／可視化）
- `Load_Visualization.py`, `Projection.py`, `Eval_iou.py`, `Eval_3Ddistance.py` — 可視化・評価用トップレベルスクリプト

## パイプラインの実行順序

`scripts/` 配下のスクリプトはnpzファイルからのデータ抽出 → CSV変換 → 統計量計算 → グラフ化・3D可視化、という順に依存関係があります（詳細は `README_my_pipeline.md` を参照）。

1. `save_betas_batch.py` / `save_joint_axisangle_batch.py` / `save_translation_batch.py` — npzから各種パラメータを抽出しCSV保存
2. `forward_kinematics_example.py` — hSMALモデルでフォワードキネマティクスを計算し、各ジョイントの空間座標（36ジョイント、mm単位）を出力
3. `calc_parent_child_distances_batch.py` / `calc_absolute_angles_batch.py` — 空間座標・親子構造から距離・絶対角度を算出
4. `extract_joint_*` 系スクリプト — 相対・絶対角度からY軸／XYZ角度成分を抽出
5. `create_*_graphs.py` — 角度データのグラフ化
6. `plot_joint_angle_comparison.py` → `generate_axis_summary_images.py` → `generate_axis_gallery_html.py` — 絶対角度と相対角度の比較グラフ、サマリー画像、一覧HTMLの生成（この順序に依存）
7. `check_yaxis_range.py` — 絶対角度・相対角度グラフのy軸範囲の整合性を検証（出力ファイルなし、標準出力のみ）

`scripts/batch/update_joint_model_data.py` が上記18本を依存順に一括実行します。

## スクリプト共通のコマンドライン引数

`scripts/utils/cli.py` が共通の引数を提供します。パイプラインの各スクリプトに `'ID_4'` を
直書きせず、必ずこのヘルパを経由してください。

- `--horse-id` — 対象馬ID（`4` / `ID_4` のどちらでも可。環境変数 `PFERD_HORSE_ID` でも指定可）。既定 `ID_4`
- `--joints` — グラフ化するジョイントの絞り込み（`all` / `legs` / `4,5,6`）。グラフ生成スクリプトのみ
- `--dpi` — 出力PNGの解像度。既定 150。グラフ生成スクリプトのみ

バッチランナーは `--horse-id` を全スクリプトへ、`--joints` / `--dpi` を `GRAPH_SCRIPTS`
に登録されたスクリプトへのみ転送します。グラフ系スクリプトを追加したらこの集合にも追加してください。

グラフ描画は `scripts/utils/plotting.py` の `save_scatter` / `save_smooth` を使います
（Aggバックエンド固定・Figure使い回し）。`plt.figure()` を直接呼ばないでください。

## 座標系の注意

- hSMALローカル座標: X=前方, Y=左, Z=上
- ワールド座標（可視化・MuJoCo等）: X=右, Y=上, Z=前
- 本パイプラインのCSV出力・可視化: X=横方向, Z=奥行き（床平面）, Y=上方向（Y-up、上が正）
- MuJoCo等の物理エンジンに連携する場合は座標変換が必要

## 可視化スクリプトの実行例

```sh
set KMP_DUPLICATE_LIB_OK=TRUE
python Load_Visualization.py --ID 4 --mocapname 20201129_ID_4_0007 --start 0 --end 100 --downSample 8 --VISUAL_MOCAP
```

`--ID` は対象馬ID、`--mocapname` はモデル推定結果ファイル名（拡張子・パス不要）、`--VISUAL_MOCAP` を付けるとC3Dモーションキャプチャデータも重ねて表示します。

## ジョイント構造

36ジョイントの親子構造は `JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv` に定義されています。ジョイント名や親子関係を変更する場合はこのCSVと整合性を取ってください（`README_my_pipeline.md` に全ジョイント名の一覧あり）。
