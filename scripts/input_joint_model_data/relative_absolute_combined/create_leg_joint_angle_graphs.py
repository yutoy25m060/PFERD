"""
このスクリプトは、Leg_Joint_AnglesディレクトリにあるCSVファイルを読み取り、
各カラム（絶対角度・相対角度）をフレーム数に対してプロットしたグラフを作成します。

【入力ファイル】
- JOINT_MODEL_DATA/Leg_Joint_Angles/ID_4/*.csv
  （各フレーム・各脚部ジョイントの角度CSV）

【出力ファイル】
- JOINT_MODEL_DATA/Leg_Joint_Angles/ID_4/graphs/CSVファイル名/カラム名_scatter.png
- JOINT_MODEL_DATA/Leg_Joint_Angles/ID_4/graphs/CSVファイル名/カラム名_smooth.png
  （各カラムのグラフ）
"""
import os
import glob
import pandas as pd
import re

from scripts.utils.cli import build_parser
from scripts.utils.plotting import save_scatter, save_smooth


def main():
    args = build_parser('脚部ジョイント角度のグラフを生成する', graph_args=True).parse_args()
    horse_id = args.horse_id
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Leg_Joint_Angles', horse_id)
    output_base_dir = os.path.join(input_dir, 'graphs')
    os.makedirs(output_base_dir, exist_ok=True)

    # CSVファイルを全て取得
    csv_files = sorted(glob.glob(os.path.join(input_dir, '*_leg_joint_angles.csv')))
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    for csv_file in csv_files:
        print(f"Processing: {os.path.basename(csv_file)}")
        csv_basename = os.path.splitext(os.path.basename(csv_file))[0]
        csv_output_dir = os.path.join(output_base_dir, csv_basename)
        os.makedirs(csv_output_dir, exist_ok=True)
        df = pd.read_csv(csv_file)
        frames = df['frame'].values
        # 'frame'以外の全カラムでグラフ作成
        for col in df.columns:
            if col == 'frame':
                continue
            # カラム名からjointXX部分を抽出
            m = re.match(r'joint(\d+)_', col)
            if m and args.joints is not None and int(m.group(1)) not in args.joints:
                continue
            joint_dir = csv_output_dir
            if m:
                # '_abs'がカラム名に含まれる場合はjointXX_abs、それ以外はjointXX
                suffix = '_abs' if '_abs' in col else ''
                joint_dir = os.path.join(csv_output_dir, f'joint{m.group(1)}{suffix}')
                os.makedirs(joint_dir, exist_ok=True)
            angles = df[col].values
            # --- 散布図 ---
            path_scatter = os.path.join(joint_dir, f"{col}_scatter.png")
            save_scatter(frames, angles, col, path_scatter, dpi=args.dpi)
            print(f"  Saved: {os.path.relpath(path_scatter, csv_output_dir)}")
            # --- 平滑線 ---
            path_smooth = os.path.join(joint_dir, f"{col}_smooth.png")
            if save_smooth(frames, angles, col, path_smooth, dpi=args.dpi):
                print(f"  Saved: {os.path.relpath(path_smooth, csv_output_dir)}")

if __name__ == '__main__':
    main() 