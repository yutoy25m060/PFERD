# PFERD/hSMAL データ処理・可視化パイプライン

## 概要

本プロジェクトは、PFERDデータセットおよびhSMALモデルを用いた馬の3Dポーズ・体型・親子構造・物理シミュレーション連携のためのデータ処理・可視化パイプラインです。  
各種npzデータから空間座標・軸角・体型パラメータ・親子間距離などを抽出・変換・可視化し、物理エンジン（MuJoCo等）への応用も想定しています。

---

## ディレクトリ構成

```
JOINT_MODEL_DATA/
  ├── Spatial_xyz_Data/           # 各ジョイントの空間座標（frameごと、36ジョイント分）
  ├── Angle_xyz_Data_from_poses/  # 各ジョイントの軸角（axis-angle, 36ジョイント分）
  ├── Beta_shape_Data/            # 体型パラメータ（betas, 10次元）
  ├── Parents_Info/               # 親子構造リスト（parents_hsmal36.csv）
  ├── ParentChild_Distances/      # 親子間距離（全フレーム・全親子ペア、統計量も別ファイル）
  ├── Angle_Y_Degree_from_poses/  # 各ジョイントのy軸角度のみ（degree, 相対角度）
  ├── Angle_xyz_Degree_from_poses/# 各ジョイントのxyz角度（degree, 相対角度）
  ├── Absolute_Angles/            # 各ジョイントのxyz絶対角度（degree, ワールド座標系）
  ├── Absolute_Y_Degree/          # 各ジョイントのy軸絶対角度のみ（degree, ワールド座標系）
  ├── Spatial_xyz_Data_from_trans/# モデル全体の並進データ（trans）
  ├── Whole_Model_xyz_Data_from_trans/ # モデル全体の並進データ（別用途/形式）
  └── Motion_Movie_from_Load_Visualization/ # 可視化動画や説明ファイル
```

---

## スクリプト一覧・役割（scripts/ フォルダ）

| スクリプト名 | 概要 |
|:---|:---|
| save_betas_batch.py | npzファイルから体型パラメータ（betas）を抽出し、CSV保存 |
| save_joint_axisangle_batch.py | npzファイルから各ジョイントの軸角（axis-angle）を抽出し、CSV保存（新ジョイント名対応） |
| save_translation_batch.py | npzファイルからモデル全体の並進（trans）を抽出し、CSV保存 |
| forward_kinematics_example.py | npzファイルから各ジョイントの空間座標を計算し、CSV保存（hSMALモデル・パラメータを用いたフォワードキネマティクス。出力は36ジョイント分のxyz座標。座標系や出力例は下記参照） |
| check_joint_count.py | npzファイルからジョイント数を確認し、標準出力に表示 |
| calc_parent_child_distances_batch.py | 空間座標CSVと親子リストCSVから親子間距離・統計量を計算し、CSV保存 |
| extract_joint_y_angle_from_axisangle.py | 各CSVから各関節のy軸角度（degree, 相対角度）のみを抽出し、CSV保存（新ジョイント名対応） |
| extract_joint_xyz_angle_from_axisangle.py | 各CSVから各関節のxyz角度（degree, 相対角度）を抽出し、CSV保存（新ジョイント名対応） |
| calc_absolute_angles_batch.py | 親子構造を用いて各ジョイントの絶対角度（xyz, degree, ワールド座標系）を計算し、CSV保存 |
| extract_joint_y_absolute_angle.py | 絶対角度CSVから各ジョイントのy軸絶対角度のみを抽出し、CSV保存 |
| create_xyz_angle_graphs.py | xyz角度（相対角度, degree）のグラフ（散布図・平滑線）を出力 |
| create_xyz_absolute_angle_graphs.py | xyz絶対角度（degree, ワールド座標系）のグラフ（散布図・平滑線）を出力 |
| create_y_absolute_angle_graphs.py | y軸絶対角度（degree, ワールド座標系）のグラフ（散布図・平滑線）を出力 |
| visualize_skeleton_3d.py | 空間座標CSVと親子リストCSVを使い、1フレーム分のスケルトンを3D可視化（matplotlib） |

---

## ジョイント名・親子構造（最新版）

```
0  pelvis
1  spine1
2  spine2
3  shoulderBlade
4  l_shoulder
5  l_elbow
6  l_carpal
7  lf_fetlock
8  lf_hoof
9  r_shoulder
10 r_elbow
11 r_carpal
12 rf_fetlock
13 rf_hoof
14 neck_under
15 neck_upper
16 head_base
17 head_tip
18 l_hip
19 l_knee
20 l_hock
21 lh_fetlock
22 lh_hoof
23 r_hip
24 r_knee
25 r_hock
26 rh_fetlock
27 rh_hoof
28 tail_base
29 tail_mid
30 tail_mid2
31 tail_mid3
32 tail_tip
33 jaw_tip
34 ear_l
35 ear_r
```

※このリストは`JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv`に準拠

---

## データ例・可視化例

![Figure_1](JOINT_MODEL_DATA/Figure_1.png)

- 青点：各ジョイント
- 黒線：親子構造（スケルトン）

---

## 座標系について

- **hSMALローカル座標**：X=前方、Y=左、Z=上
- **ワールド座標（可視化・MuJoCo等）**：X=右、Y=上、Z=前
- **本パイプラインの出力（CSV/可視化）**：
    - **X軸**: 横方向（右方向）
    - **Z軸**: 奥行き方向（前方向、床平面）
    - **Y軸**: 上方向（鉛直、Y-up）
    - **Y軸は反転済み（上が正）**
- MuJoCo等の物理エンジンに連携する場合は、座標変換が必要です。

---

## 使い方（例）

1. 必要なスクリプトを順に実行し、各種CSVデータを生成
2. 可視化や統計量計算、物理エンジン連携など、目的に応じてデータを活用
3. 絶対角度・絶対Y角度の抽出やグラフ化も可能

---

## Load_Visualization.py の使い方

`Load_Visualization.py` は、hSMALモデル推定結果（ポーズ・ベータ・トランスレーション）を3Dビューワー（aitviewer）で可視化するためのスクリプトです。  
オプションでモーションキャプチャデータ（C3D）も重ねて表示できます。

### コマンド例

```sh
set KMP_DUPLICATE_LIB_OK=TRUE

python Load_Visualization.py --ID 4 --mocapname 20201129_ID_4_0007 --start 0 --end 100 --downSample 8 --VISUAL_MOCAP
```

- `--ID`: 対象馬ID（例: 4）
- `--mocapname`: モデル推定結果ファイル名（拡張子・パス不要）
- `--start`, `--end`: 可視化するフレーム範囲
- `--downSample`: フレーム間引き（例: 8で30fps相当）
- `--VISUAL_MOCAP`: モーションキャプチャも重ねて表示する場合に指定

### 入出力

- 入力: `CONFIG.py` で指定されたパスのhSMAL推定結果（例: dataset/ID_x/MODEL_DATA/xxxx_hsmal.npz）、hSMALモデル（.pkl）、（オプション）C3Dファイル
- 出力: 3Dビューワーによる可視化（ファイル出力はなし）

---

## 注意・カスタマイズ

- 各スクリプトの`horse_id`やファイルパスは適宜変更してください。
- 別IDや他のnpzファイルにも対応可能です。
- 可視化や出力形式のカスタマイズも柔軟に対応できます。
- 絶対角度・絶対Y角度の抽出やグラフ化もサポートしています。

---

## お問い合わせ・追加要望

- さらなる可視化、統計解析、物理エンジン連携、データ変換など、ご要望があればご相談ください。

---

このREADMEをベースに、あなたの研究・開発に合わせて自由に追記・編集してください！ 

### forward_kinematics_example.py の詳細

- 入力: dataset/ID_x/MODEL_DATA/xxxx_hsmal.npz（'poses', 'betas', 'trans'を含む）、hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl
- 出力: JOINT_MODEL_DATA/Spatial_xyz_Data/ID_x/xxxx_hsmal_joints_xyz.csv（各フレーム・各ジョイントの3次元座標 [mm]）
- 注意: ジョイント数や名称はget_hsmal_segment_names()に従う。
- **出力座標系: X-Z平面、Y-up（Y軸が鉛直上向き、上が正）**
- 実行例:

```sh
set PYTHONPATH=%cd%
python scripts/forward_kinematics_example.py
```

---

### visualize_skeleton_3d.py の詳細

- 入力: JOINT_MODEL_DATA/Spatial_xyz_Data/ID_x/xxxx_hsmal_joints_xyz.csv、親子構造CSV
- 出力: 3Dスケルトン可視化（matplotlib）
- **可視化座標系: X-Z平面、Y-up（Y軸が鉛直上向き、上が正）**
- 軸ラベル: X (mm), Z (mm), Y (mm) 