"""
このスクリプトは、Absolute_AnglesディレクトリにあるCSVファイルを読み取り、
各ジョイントのX軸、Y軸、Z軸絶対角度をフレーム数に対してプロットしたグラフを作成します。

【入力ファイル】
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/*.csv
  （各フレーム・各ジョイントのXYZ絶対角度CSV）

【出力ファイル】
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/graphs/CSVファイル名/joint番号/軸名_scatter.png
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/graphs/CSVファイル名/joint番号/軸名_smooth.png
  （各ジョイントの各軸絶対角度グラフ）
"""
import os
import glob
import pandas as pd

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.cli import build_parser
from scripts.utils.joint_utils import load_joint_names
from scripts.utils.plotting import save_scatter, save_smooth

def main():
    args = build_parser('各ジョイントのxyz絶対角度のグラフを生成する', graph_args=True).parse_args()
    horse_id = args.horse_id
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id)
    output_base_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id, 'graphs')
    os.makedirs(output_base_dir, exist_ok=True)

    axes = ['x', 'y', 'z']
    # ジョイント名をCSVファイルから読み込み
    joint_names = load_joint_names(horse_id)

    csv_files = sorted(glob.glob(os.path.join(input_dir, '*.csv')))
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
        for joint_idx, joint_name in enumerate(joint_names):
            if args.joints is not None and joint_idx not in args.joints:
                continue
            joint_dir = os.path.join(csv_output_dir, f'joint{joint_idx}')
            os.makedirs(joint_dir, exist_ok=True)
            for axis in axes:
                col = f'joint{joint_idx}_{joint_name}_{axis} [deg]'
                if col not in df.columns:
                    print(f"Warning: Column {col} not found in {csv_file}")
                    continue
                angles = df[col].values
                ylabel = f'{axis.upper()} Angle [deg]'
                # 散布図
                name_scatter = f"{col}_scatter.png"
                save_scatter(frames, angles, ylabel,
                             os.path.join(joint_dir, name_scatter), dpi=args.dpi)
                print(f"  Saved: joint{joint_idx}/{name_scatter}")
                # 平滑線
                name_smooth = f"{col}_smooth.png"
                if save_smooth(frames, angles, ylabel,
                               os.path.join(joint_dir, name_smooth), dpi=args.dpi):
                    print(f"  Saved: joint{joint_idx}/{name_smooth}")

if __name__ == '__main__':
    main() 