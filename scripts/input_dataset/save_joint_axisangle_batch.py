"""
このスクリプトは、hSMALモデル推定結果（npzファイル）から各ジョイントの軸角（axis-angle）パラメータを抽出し、
CSVファイルとして保存します。

【入力ファイル】
- dataset/ID_4/MODEL_DATA/*_hsmal.npz
  （'poses' を含む）

【出力ファイル】
- JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4/*_axisangle.csv
  （各ジョイントの軸角（axis-angle）パラメータのCSV）
"""
import os
import glob
import numpy as np
import pandas as pd

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.cli import parse_horse_id
from scripts.utils.joint_utils import load_joint_names

def main():
    # --- 設定 ---
    horse_id = parse_horse_id('npzから各ジョイントの軸角（axis-angle）を抽出しCSV保存する')
    input_dir = os.path.join('dataset', horse_id, 'MODEL_DATA')
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Data_from_poses', horse_id)

    # ジョイント名をCSVファイルから読み込み
    segment_names = load_joint_names(horse_id)

    os.makedirs(output_dir, exist_ok=True)

    npz_files = sorted(glob.glob(os.path.join(input_dir, '*_hsmal.npz')))

    if not npz_files:
        print(f"No npz files found in {input_dir}")
        return

    for npz_path in npz_files:
        npz = np.load(npz_path, allow_pickle=True)
        poses = npz['poses']  # shape: (フレーム数, ジョイント数×3)
        n_frames = poses.shape[0]
        n_joints = len(segment_names)  # 親子構造CSVを唯一の情報源とする
        assert poses.shape[1] == n_joints * 3, \
            f"poses shape mismatch: {poses.shape} (期待: (*, {n_joints * 3}))"

        data = {}
        for j, name in enumerate(segment_names[:n_joints]):
            data[f'joint{j}_{name}_x [rad]'] = poses[:, j*3 + 0]
            data[f'joint{j}_{name}_y [rad]'] = poses[:, j*3 + 1]
            data[f'joint{j}_{name}_z [rad]'] = poses[:, j*3 + 2]
        df = pd.DataFrame(data)
        df.insert(0, 'frame', range(n_frames))

        npz_base = os.path.splitext(os.path.basename(npz_path))[0]
        csv_filename = f"{npz_base}_axisangle.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {csv_path}")

if __name__ == '__main__':
    main() 