# PFERD/hSMALデータ処理・可視化パイプライン README

## 概要

本プロジェクトは、PFERDデータセットおよびhSMALモデルを用いた馬の3Dポーズ・体型・親子構造・物理シミュレーション連携のためのデータ処理・可視化パイプラインです。  
各種npzデータから、空間座標・軸角・体型パラメータ・親子間距離などを抽出・変換・可視化し、物理エンジン（MuJoCo等）への応用も想定しています。

---

## ディレクトリ構成

```
JOINT_MODEL_DATA/
  ├── Spatial_xyz_Data/           # 各ジョイントの空間座標（frameごと、36ジョイント分）
  ├── Angle_xyz_Data_from_poses/  # 各ジョイントの軸角（axis-angle, 36ジョイント分）
  ├── Beta_shape_Data/            # 体型パラメータ（betas, 36次元）
  ├── Parents_Info/               # 親子構造リスト（parents_hsmal36.csv）
  ├── ParentChild_Distances/      # 親子間距離（全フレーム・全親子ペア、統計量も別ファイル）
  └── Whole_Model_xyz_Data_from_trans/ # モデル全体の並進データ（trans）
```

---

## スクリプト一覧・役割

### 1. save_betas_batch.py
- 各npzファイルから**体型パラメータ（betas）**を抽出し、`Beta_shape_Data/ID_x/`にCSV保存。
- カラム名は `beta_0, beta_1, ...` など。

### 2. save_joint_axisangle_batch.py
- 各npzファイルから**各ジョイントの軸角（axis-angle）**を抽出し、`Angle_xyz_Data_from_poses/ID_x/`にCSV保存。
- カラム名は `0_pelvis_axis_x, ...` のようにインデックス＋名称＋成分。

### 3. save_translation_batch.py
- 各npzファイルから**モデル全体の並進（trans）**を抽出し、`Spatial_xyz_Data_from_trans/ID_x/`にCSV保存。
- カラム名は `frame, trans_x, trans_y, trans_z`。

### 4. forward_kinematics_example.py
- npzファイルから**各ジョイントの空間座標**を計算し、`Spatial_xyz_Data/ID_x/`にCSV保存。
- カラム名は `0_pelvis_x, 0_pelvis_y, ...` のようにインデックス＋名称＋成分。

### 5. check_joint_count.py
- npzファイルから**ジョイント数**を確認し、標準出力に表示。

### 6. calc_parent_child_distances_batch.py
- 空間座標CSVと親子リストCSVを使い、**各親子ペアの距離（mm）**を全フレーム分計算し、`ParentChild_Distances/ID_x/`に保存。
- カラム名は `0_pelvis→1_left_hip [mm]` のようにインデックス＋名称＋単位。
- 統計量（mean, std, min, max）は別CSVに保存。

### 7. visualize_skeleton_3d.py
- 空間座標CSVと親子リストCSVを使い、**1フレーム分のスケルトンを3D可視化**。
- matplotlibで表示。frame番号を変更すれば任意フレーム可視化可能。

---

## データ例・可視化例

### スケルトン3D可視化（例: Figure_1.png）

![Figure_1](Figure_1.png)

- 青点：各ジョイント
- 黒線：親子構造（スケルトン）

---

## 座標系について

- **hSMALローカル座標**：X=前方、Y=左、Z=上
- **ワールド座標（可視化・MuJoCo等）**：X=右、Y=上、Z=前
- MuJoCo等の物理エンジンに連携する場合は、座標変換が必要です。

---

## 使い方（例）

1. 必要なスクリプトを順に実行し、各種CSVデータを生成
2. 可視化や統計量計算、物理エンジン連携など、目的に応じてデータを活用

---

## 参考：親子リスト（parents_hsmal36.csv）

- 36ジョイント分の親インデックス（-1はroot）

---

## 注意・カスタマイズ

- 各スクリプトの`horse_id`やファイルパスは適宜変更してください。
- 別IDや他のnpzファイルにも対応可能です。
- 可視化や出力形式のカスタマイズも柔軟に対応できます。

---

## お問い合わせ・追加要望

- さらなる可視化、統計解析、物理エンジン連携、データ変換など、ご要望があればご相談ください。

---

このREADMEをベースに、あなたの研究・開発に合わせて自由に追記・編集してください！ 