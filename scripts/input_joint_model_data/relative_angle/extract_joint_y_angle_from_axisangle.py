"""
Angle_xyz_Data_from_posesの各CSVから、各関節のフレームごとのy軸角度（degree）を抽出し、CSV保存するスクリプト

入力：
- JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4/*.csv
  （各行：axis-angle（x, y, z）が関節数分並ぶ）

出力：
- JOINT_MODEL_DATA/Angle_Y_Degree_from_poses/ID_4/<元ファイル名>_yangle_deg.csv
  （各行：frame, joint0_pelvis_y [deg], joint1_left_hip_y [deg], ...）
"""
import os
import glob
import numpy as np
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.joint_utils import load_joint_names

def main():
    horse_id = 'ID_4'
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Data_from_poses', horse_id)
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_Y_Degree_from_poses', horse_id)
    os.makedirs(output_dir, exist_ok=True)

    # ジョイント名をCSVファイルから読み込み
    joint_names = load_joint_names(horse_id)

    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    for csv_file in csv_files:
        print(f'Processing: {os.path.basename(csv_file)}')
        # CSV読み込み
        df = pd.read_csv(csv_file)
        data = df.values  # shape: (frame数, 関節数×3)
        n_frames, n_cols = data.shape
        n_joints = n_cols // 3
        # y軸角度（2番目）だけ抽出
        y_angles = data[:, 2::3]  # shape: (frame数, 関節数)
        # rad→degree変換
        y_angles_deg = np.degrees(y_angles)
        # DataFrame化
        columns = []
        for j in range(n_joints):
            joint_name = joint_names[j] if j < len(joint_names) else f'joint{j}'
            columns.append(f'joint{j}_{joint_name}_y [deg]')
        out_df = pd.DataFrame(y_angles_deg, columns=columns)
        out_df.insert(0, 'frame', range(n_frames))
        # 保存
        out_name = os.path.splitext(os.path.basename(csv_file))[0] + '_yangle_deg.csv'
        out_path = os.path.join(output_dir, out_name)
        out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 