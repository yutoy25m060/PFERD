"""
このスクリプトは、Angle_xyz_Data_from_posesの各CSVファイルから、
親子関係を用いて各ジョイントの絶対角度（ワールド座標系でのx, y, z角度, degree）を計算し、
JOINT_MODEL_DATA/Absolute_Angles/ID_4/ に短いファイル名で保存します。

【入力ファイル】
- JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4/*.csv
- JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv

【出力ファイル】
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/元ファイル名_hsmal_absolute.csv
  （各行：frame, joint0_pelvis_x [deg], joint0_pelvis_y [deg], joint0_pelvis_z [deg], ...）
"""
import os
import glob
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R

def load_parents(parents_csv):
    df = pd.read_csv(parents_csv)
    return df['parent_index'].values

def main():
    horse_id = 'ID_4'
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Data_from_poses', horse_id)
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id)
    os.makedirs(output_dir, exist_ok=True)
    parents_csv = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', horse_id, 'parents_hsmal36.csv')
    parents = load_parents(parents_csv)

    joint_names = [
        'pelvis', 'spine1', 'spine2', 'shoulderBlade', 'l_shoulder', 'l_elbow', 'l_carpal', 'lf_fetlock', 'lf_hoof',
        'r_shoulder', 'r_elbow', 'r_carpal', 'rf_fetlock', 'rf_hoof', 'neck_under', 'neck_upper', 'head_base', 'head_tip',
        'l_hip', 'l_knee', 'l_hock', 'lh_fetlock', 'lh_hoof', 'r_hip', 'r_knee', 'r_hock', 'rh_fetlock', 'rh_hoof',
        'tail_base', 'tail_mid', 'tail_mid2', 'tail_mid3', 'tail_tip', 'ear_l', 'ear_r', 'jaw_tip'
    ]
    n_joints = len(joint_names)

    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    for csv_file in csv_files:
        print(f'Processing: {os.path.basename(csv_file)}')
        df = pd.read_csv(csv_file)
        data = df.values  # shape: (frame数, 関節数×3 + 1)
        n_frames, n_cols = data.shape
        # 1列目（frame列）を除外
        data = data[:, 1:]
        xyz_angles = data.reshape(n_frames, n_joints, 3)  # (frame, joint, xyz)

        # 絶対回転（回転行列）を格納
        abs_rotmats = np.zeros((n_frames, n_joints, 3, 3))
        abs_eulers = np.zeros((n_frames, n_joints, 3))
        for f in range(n_frames):
            for j in range(n_joints):
                # 自身の相対回転（axis-angle→回転行列）
                rel_rot = R.from_rotvec(xyz_angles[f, j, :])
                if parents[j] == -1:
                    abs_rotmats[f, j] = rel_rot.as_matrix()
                else:
                    abs_rotmats[f, j] = abs_rotmats[f, int(parents[j])] @ rel_rot.as_matrix()
                # 絶対回転行列→オイラー角（xyz順、度）
                abs_eulers[f, j, :] = R.from_matrix(abs_rotmats[f, j]).as_euler('xyz', degrees=True)
        # DataFrame化
        columns = []
        for j, name in enumerate(joint_names):
            columns.extend([f'joint{j}_{name}_x [deg]', f'joint{j}_{name}_y [deg]', f'joint{j}_{name}_z [deg]'])
        out_df = pd.DataFrame(abs_eulers.reshape(n_frames, n_joints*3), columns=columns)
        out_df.insert(0, 'frame', range(n_frames))
        # 出力ファイル名
        base = os.path.basename(csv_file).replace('_axisangle.csv', '').replace('.csv', '')
        out_name = f'{base}_hsmal_absolute.csv'
        out_path = os.path.join(output_dir, out_name)
        out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 