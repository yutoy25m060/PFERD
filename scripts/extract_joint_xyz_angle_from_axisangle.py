"""
Angle_xyz_Data_from_posesの各CSVから、各関節のフレームごとのx, y, z軸角度（degree）を抽出し、CSV保存するスクリプト

入力：
- JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4/*.csv
  （各行：axis-angle（x, y, z）が関節数分並ぶ）

出力：
- JOINT_MODEL_DATA/Angle_xyz_Degree_from_poses/ID_4/<元ファイル名>_xyzangle_deg.csv
  （各行：frame, joint0_pelvis_x [deg], joint0_pelvis_y [deg], joint0_pelvis_z [deg], ...）
"""
import os
import glob
import numpy as np
import pandas as pd

def main():
    input_dir = 'JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4'
    output_dir = 'JOINT_MODEL_DATA/Angle_xyz_Degree_from_poses/ID_4'
    os.makedirs(output_dir, exist_ok=True)

    # ジョイント名リスト（馬のジョイント名）
    joint_names = [
        'pelvis', 'spine1', 'spine2', 'shoulderBlade', 'l_shoulder', 'l_elbow', 'l_carpal', 'lf_fetlock', 'lf_hoof',
        'r_shoulder', 'r_elbow', 'r_carpal', 'rf_fetlock', 'rf_hoof', 'neck_under', 'neck_upper', 'head_base', 'head_tip',
        'l_hip', 'l_knee', 'l_hock', 'lh_fetlock', 'lh_hoof', 'r_hip', 'r_knee', 'r_hock', 'rh_fetlock', 'rh_hoof',
        'tail_base', 'tail_mid', 'tail_mid2', 'tail_mid3', 'tail_tip', 'ear_l', 'ear_r', 'jaw_tip'
    ]

    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    for csv_file in csv_files:
        print(f'Processing: {os.path.basename(csv_file)}')
        # CSV読み込み
        df = pd.read_csv(csv_file)
        data = df.values  # shape: (frame数, 関節数×3 + 1)
        n_frames, n_cols = data.shape
        # 1列目（frame列）を除外
        data = data[:, 1:]
        n_joints = data.shape[1] // 3
        # x, y, z軸角度を抽出
        xyz_angles = data.reshape(n_frames, n_joints, 3)  # shape: (frame数, 関節数, 3)
        xyz_angles_deg = np.degrees(xyz_angles)  # rad→degree変換
        # DataFrame化
        columns = []
        for j in range(n_joints):
            joint_name = joint_names[j] if j < len(joint_names) else f'joint{j}'
            columns.extend([f'joint{j}_{joint_name}_x [deg]', f'joint{j}_{joint_name}_y [deg]', f'joint{j}_{joint_name}_z [deg]'])
        out_df = pd.DataFrame(xyz_angles_deg.reshape(n_frames, n_joints*3), columns=columns)
        out_df.insert(0, 'frame', range(n_frames))
        # 保存
        out_name = os.path.splitext(os.path.basename(csv_file))[0] + '_xyzangle_deg.csv'
        out_path = os.path.join(output_dir, out_name)
        out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 