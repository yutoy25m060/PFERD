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
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.cli import parse_horse_id
from scripts.utils.joint_utils import load_joint_names

def main():
    horse_id = parse_horse_id('絶対角度CSVからY軸成分のみを抽出しCSV保存する')
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id)
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Y_Degree', horse_id)
    os.makedirs(output_dir, exist_ok=True)

    # ジョイント名をCSVファイルから読み込み
    joint_names = load_joint_names(horse_id)

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