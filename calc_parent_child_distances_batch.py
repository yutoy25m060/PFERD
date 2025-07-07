import os
import glob
import pandas as pd
import numpy as np

# --- 設定 ---
horse_id = 'ID_4'
joints_dir = os.path.join('JOINT_MODEL_DATA', 'Spatial_xyz_Data', horse_id)
parents_csv = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', horse_id, 'parents_hsmal36.csv')
output_dir = os.path.join('JOINT_MODEL_DATA', 'ParentChild_Distances', horse_id)
os.makedirs(output_dir, exist_ok=True)

# 親子リストの読み込み
parents_df = pd.read_csv(parents_csv, index_col=0)
parents = parents_df['parent_index'].values.tolist()

# セグメント名リスト（カラム名生成用）
segment_names = [
    'pelvis', 'left_hip', 'right_hip', 'spine1', 'left_knee', 'right_knee', 'spine2', 'left_ankle', 'right_ankle',
    'spine3', 'left_foot', 'right_foot', 'neck', 'left_collar', 'right_collar', 'head', 'left_shoulder', 'right_shoulder',
    'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'jaw', 'left_eye_smplhf', 'right_eye_smplhf',
    'left_index1', 'left_index2', 'left_index3', 'left_middle1', 'left_middle2', 'left_middle3',
    'left_pinky1', 'left_pinky2', 'left_pinky3', 'left_ring1', 'left_ring2'
]

# joints CSVファイルを全て取得
joints_files = sorted(glob.glob(os.path.join(joints_dir, '*_joints_xyz.csv')))

if not joints_files:
    print(f"No joints CSV files found in {joints_dir}")
    exit(1)

for joints_csv in joints_files:
    df = pd.read_csv(joints_csv)
    num_frames = df.shape[0]
    num_joints = len(segment_names)
    # 各ジョイントの座標を3次元配列に変換
    joints_xyz = np.zeros((num_frames, num_joints, 3))
    for j, name in enumerate(segment_names):
        joints_xyz[:, j, 0] = df[f'{j}_{name}_x']
        joints_xyz[:, j, 1] = df[f'{j}_{name}_y']
        joints_xyz[:, j, 2] = df[f'{j}_{name}_z']
    # 親子間距離を計算（単位: mm）
    distances = {}
    for child_idx, parent_idx in enumerate(parents):
        if parent_idx == -1:
            continue
        key = f'{parent_idx}_{segment_names[parent_idx]}→{child_idx}_{segment_names[child_idx]} [mm]'
        d = np.linalg.norm(joints_xyz[:, child_idx, :] - joints_xyz[:, parent_idx, :], axis=-1) * 1000  # mm
        distances[key] = d
    dist_df = pd.DataFrame(distances)
    dist_df.insert(0, 'frame', range(num_frames))
    # 統計量計算
    stats = {}
    for col in dist_df.columns[1:]:
        stats[col] = [
            dist_df[col].mean(),
            dist_df[col].std(),
            dist_df[col].min(),
            dist_df[col].max()
        ]
    stats_df = pd.DataFrame(stats, index=['mean', 'std', 'min', 'max'])
    # 統計量は別ファイルに保存
    base = os.path.splitext(os.path.basename(joints_csv))[0]
    out_csv = os.path.join(output_dir, f'{base}_parentchild_dist.csv')
    stats_csv = os.path.join(output_dir, f'{base}_parentchild_dist_stats.csv')
    dist_df.to_csv(out_csv, index=False, encoding='utf-8-sig')
    stats_df.to_csv(stats_csv, encoding='utf-8-sig')
    print(f"Saved: {out_csv}")
    print(f"Saved: {stats_csv}") 