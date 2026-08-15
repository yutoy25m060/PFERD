"""
このスクリプトは、Angle_xyz_Degree_from_posesディレクトリにあるCSVファイルを読み取り、
各ジョイントのX軸、Y軸、Z軸角度をフレーム数に対してプロットしたグラフを作成します。

【入力ファイル】
- JOINT_MODEL_DATA/Angle_xyz_Degree_from_poses/ID_4/*_hsmal_axisangle_xyzangle_deg.csv
  （各フレーム・各ジョイントのXYZ軸角度CSV）

【出力ファイル】
- JOINT_MODEL_DATA/Angle_xyz_Degree_from_poses/ID_4/graphs/CSVファイル名/joint番号/軸名.png
  （各ジョイントの各軸角度グラフ）
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
    # --- 設定 ---
    args = build_parser('各ジョイントのxyz角度（相対角度）のグラフを生成する', graph_args=True).parse_args()
    horse_id = args.horse_id
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Degree_from_poses', horse_id)
    output_base_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Degree_from_poses', horse_id, 'graphs')
    os.makedirs(output_base_dir, exist_ok=True)

    # 軸名リスト
    axes = ['x', 'y', 'z']
    # ジョイント名をCSVファイルから読み込み
    joint_names = load_joint_names(horse_id)

    # CSVファイルを全て取得
    csv_files = sorted(glob.glob(os.path.join(input_dir, '*_hsmal_axisangle_xyzangle_deg.csv')))

    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    for csv_file in csv_files:
        print(f"Processing: {os.path.basename(csv_file)}")
        
        # CSVファイル名からフォルダ名を生成
        csv_basename = os.path.splitext(os.path.basename(csv_file))[0]
        csv_output_dir = os.path.join(output_base_dir, csv_basename)
        os.makedirs(csv_output_dir, exist_ok=True)
        
        # CSVファイルを読み込み
        df = pd.read_csv(csv_file)
        
        # フレーム数を取得
        frames = df['frame'].values
        
        # 各ジョイントについてグラフを作成
        for joint_idx, joint_name in enumerate(joint_names):  # joint0からjoint35まで
            if args.joints is not None and joint_idx not in args.joints:
                continue
            # ジョイントフォルダを作成
            joint_dir = os.path.join(csv_output_dir, f'joint{joint_idx}')
            os.makedirs(joint_dir, exist_ok=True)

            # 各軸についてグラフを作成
            for axis in axes:
                # ジョイントの軸角度データを取得
                column_name = f'joint{joint_idx}_{joint_name}_{axis} [deg]'
                if column_name not in df.columns:
                    print(f"Warning: Column {column_name} not found in {csv_file}")
                    continue
                angles = df[column_name].values
                ylabel = f'{axis.upper()} Angle [deg]'

                # --- 散布図のみ ---
                name_scatter = f"{column_name}_scatter.png"
                save_scatter(frames, angles, ylabel,
                             os.path.join(joint_dir, name_scatter), dpi=args.dpi)
                print(f"  Saved: joint{joint_idx}/{name_scatter}")

                # --- 平滑線のみ ---
                name_smooth = f"{column_name}_smooth.png"
                if save_smooth(frames, angles, ylabel,
                               os.path.join(joint_dir, name_smooth), dpi=args.dpi):
                    print(f"  Saved: joint{joint_idx}/{name_smooth}")

if __name__ == '__main__':
    main() 