"""
各フレーム・各ジョイントの3次元座標CSV（Spatial_xyz_Data）と親子関係情報をもとに、
全フレーム・全ジョイントの親子間距離を計算し、その結果と統計量をCSVファイルとして保存するスクリプト

【注意】
このスクリプトを実行する際は、PYTHONPATH にプロジェクトルート（PFERD/PFERD）を追加してください。
例: Windowsの場合
    set PYTHONPATH=%cd% && python scripts/calc_parent_child_distances_batch.py

【入力ファイル】
- JOINT_MODEL_DATA/Spatial_xyz_Data/ID_4/*_joints_xyz.csv
- JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv

【出力ファイル】
- JOINT_MODEL_DATA/ParentChild_Distances/ID_4/*_parentchild_dist.csv
- JOINT_MODEL_DATA/ParentChild_Distances/ID_4/*_parentchild_dist_stats.csv
"""
import os
import glob
import pandas as pd
import numpy as np

import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from scripts.utils.joint_utils import load_joint_hierarchy

# --- 設定 ---
horse_id = 'ID_4'
input_dir = os.path.join('JOINT_MODEL_DATA', 'Spatial_xyz_Data', horse_id)
output_dir = os.path.join('JOINT_MODEL_DATA', 'ParentChild_Distances', horse_id)
os.makedirs(output_dir, exist_ok=True)

# 親子関係の読み込み
parent_dict = load_joint_hierarchy(horse_id)
parent_pairs = [(child, parent) for child, parent in parent_dict.items() if parent != -1]

# joints_xyzファイル一覧
csv_files = sorted(glob.glob(os.path.join(input_dir, '*_joints_xyz.csv')))
if not csv_files:
    print(f'入力ファイルが見つかりません: {input_dir}')
    exit(1)

# ジョイント名リストを推定（カラム名から抽出）
def get_joint_names(joints_df):
    names = []
    for col in joints_df.columns:
        if '_x [mm]' in col:
            idx_name = col.split('_x [mm]')[0]
            idx, name = idx_name.split('_', 1)
            names.append(name)
    return names

for csv_file in csv_files:
    print(f'Processing: {os.path.basename(csv_file)}')
    joints_df = pd.read_csv(csv_file)
    n_frames = joints_df.shape[0]
    joint_names = get_joint_names(joints_df)
    n_joints = len(joint_names)

    # 全座標をnumpy配列化 (shape: [n_frames, n_joints, 3])
    xyz = np.zeros((n_frames, n_joints, 3), dtype=np.float32)
    for j, name in enumerate(joint_names):
        xyz[:, j, 0] = joints_df[f'{j}_{name}_x [mm]'].values
        xyz[:, j, 1] = joints_df[f'{j}_{name}_y [mm]'].values
        xyz[:, j, 2] = joints_df[f'{j}_{name}_z [mm]'].values

    # 親子間距離を一括計算
    dist_arr = np.zeros((n_frames, len(parent_pairs)), dtype=np.float32)
    for i, (child, parent) in enumerate(parent_pairs):
        dist_arr[:, i] = np.linalg.norm(xyz[:, child, :] - xyz[:, parent, :], axis=1)

    # ヘッダー名を「親ジョイント→子ジョイント [mm]」形式に
    dist_columns = [
        f'{parent}_{joint_names[parent]}→{child}_{joint_names[child]} [mm]'
        for child, parent in parent_pairs
    ]
    dist_df = pd.DataFrame(dist_arr, columns=dist_columns)
    dist_df.insert(0, 'frame', np.arange(n_frames))

    # 保存ファイル名
    base = os.path.splitext(os.path.basename(csv_file))[0]
    out_dist = os.path.join(output_dir, f'{base}_parentchild_dist.csv')
    dist_df.to_csv(out_dist, index=False, encoding='utf-8-sig')
    print(f'Saved: {out_dist}')

    # 統計量計算
    stats_df = dist_df.drop('frame', axis=1).agg(['mean', 'std', 'min', 'max', 'median']).T.reset_index()
    stats_df = stats_df.rename(columns={'index': 'joint_pair'})
    out_stats = os.path.join(output_dir, f'{base}_parentchild_dist_stats.csv')
    stats_df.to_csv(out_stats, index=False, encoding='utf-8-sig')
    print(f'Saved: {out_stats}') 