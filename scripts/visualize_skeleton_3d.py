"""
このスクリプトは、各フレーム・各ジョイントの3次元座標CSVと親子関係情報をもとに、
指定したフレームのスケルトン構造を3Dで可視化します。

【入力ファイル】
- JOINT_MODEL_DATA/Spatial_xyz_Data/ID_4/20201129_ID_4_0007_hsmal_joints_xyz.csv
  （各フレーム・各ジョイントの3次元座標CSV）
- JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv
  （親子関係インデックスCSV）

【出力】
- 3Dプロットによるスケルトン可視化（ファイル出力はなし）
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def main():
    # --- 設定 ---
    horse_id = 'ID_4'
    joints_csv = os.path.join('JOINT_MODEL_DATA', 'Spatial_xyz_Data', horse_id, '20201129_ID_4_0007_hsmal_joints_xyz.csv')
    parents_csv = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', horse_id, 'parents_hsmal36.csv')
    frame = 0  # 可視化したいフレーム番号

    # セグメント名リスト
    segment_names = [
        'pelvis', 'left_hip', 'right_hip', 'spine1', 'left_knee', 'right_knee', 'spine2', 'left_ankle', 'right_ankle',
        'spine3', 'left_foot', 'right_foot', 'neck', 'left_collar', 'right_collar', 'head', 'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'jaw', 'left_eye_smplhf', 'right_eye_smplhf',
        'left_index1', 'left_index2', 'left_index3', 'left_middle1', 'left_middle2', 'left_middle3',
        'left_pinky1', 'left_pinky2', 'left_pinky3', 'left_ring1', 'left_ring2'
    ]

    # 親子リストの読み込み
    parents_df = pd.read_csv(parents_csv, index_col=0)
    parents = parents_df['parent_index'].values.tolist()

    # jointsデータの読み込み
    joints_df = pd.read_csv(joints_csv)
    xyz = []
    for j, name in enumerate(segment_names):
        xyz.append([
            joints_df.loc[frame, f'{j}_{name}_x [mm]'], 
            joints_df.loc[frame, f'{j}_{name}_y [mm]'],
            joints_df.loc[frame, f'{j}_{name}_z [mm]']
        ])
    xyz = np.array(xyz)

    # 3D可視化
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(xyz[:,0], xyz[:,1], xyz[:,2], c='b', label='joints')
    for child, parent in enumerate(parents):
        if parent == -1:
            continue
        ax.plot([xyz[child,0], xyz[parent,0]], [xyz[child,1], xyz[parent,1]], [xyz[child,2], xyz[parent,2]], 'k-')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'Skeleton 3D Visualization (frame={frame})')
    ax.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main() 