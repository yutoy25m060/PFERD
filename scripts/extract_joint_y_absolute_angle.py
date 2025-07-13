"""
絶対角度CSV（Absolute_Angles）から各ジョイントのY軸絶対角度（degree）のみを抽出し、
新しいCSVとして保存するスクリプト

入力：
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/*.csv
  （各行：frame, joint0_x [deg], joint0_y [deg], joint0_z [deg], ...）

出力：
- JOINT_MODEL_DATA/Absolute_Y_Degree/ID_4/<元ファイル名>_abs_yangle_deg.csv
  （各行：frame, joint0_ジョイント名_y [deg], ...）
"""
import os
import glob
import pandas as pd

def main():
    input_dir = 'JOINT_MODEL_DATA/Absolute_Angles/ID_4'
    output_dir = 'JOINT_MODEL_DATA/Absolute_Y_Degree/ID_4'
    os.makedirs(output_dir, exist_ok=True)

    joint_names = [
        'pelvis', 'spine1', 'spine2', 'shoulderBlade', 'l_shoulder', 'l_elbow', 'l_carpal', 'lf_fetlock', 'lf_hoof',
        'r_shoulder', 'r_elbow', 'r_carpal', 'rf_fetlock', 'rf_hoof', 'neck_under', 'neck_upper', 'head_base', 'head_tip',
        'l_hip', 'l_knee', 'l_hock', 'lh_fetlock', 'lh_hoof', 'r_hip', 'r_knee', 'r_hock', 'rh_fetlock', 'rh_hoof',
        'tail_base', 'tail_mid', 'tail_mid2', 'tail_mid3', 'tail_tip', 'ear_l', 'ear_r', 'jaw_tip'
    ]

    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    for csv_file in csv_files:
        print(f'Processing: {os.path.basename(csv_file)}')
        df = pd.read_csv(csv_file)
        y_cols = [f'joint{j}_{name}_y [deg]' for j, name in enumerate(joint_names)]
        y_df = df[['frame'] + y_cols]
        out_name = os.path.splitext(os.path.basename(csv_file))[0] + '_abs_yangle_deg.csv'
        out_path = os.path.join(output_dir, out_name)
        y_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 