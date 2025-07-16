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
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.joint_utils import load_joint_names

def main():
    horse_id = 'ID_4'
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

    plt.rcParams['font.family'] = 'DejaVu Sans'
    for csv_file in csv_files:
        print(f"Processing: {os.path.basename(csv_file)}")
        csv_basename = os.path.splitext(os.path.basename(csv_file))[0]
        csv_output_dir = os.path.join(output_base_dir, csv_basename)
        os.makedirs(csv_output_dir, exist_ok=True)
        df = pd.read_csv(csv_file)
        frames = df['frame'].values
        for joint_idx, joint_name in enumerate(joint_names):
            joint_dir = os.path.join(csv_output_dir, f'joint{joint_idx}')
            os.makedirs(joint_dir, exist_ok=True)
            for axis in axes:
                col = f'joint{joint_idx}_{joint_name}_{axis} [deg]'
                if col not in df.columns:
                    print(f"Warning: Column {col} not found in {csv_file}")
                    continue
                angles = df[col].values
                # 散布図
                plt.figure(figsize=(12, 6))
                plt.scatter(frames, angles, alpha=0.6, s=1, color='blue', label='Data points')
                plt.xlabel('Frame', fontsize=12)
                plt.ylabel(f'{axis.upper()} Angle [deg]', fontsize=12)
                plt.grid(True, alpha=0.3)
                plt.legend()
                output_filename_scatter = f"{col}_scatter.png"
                output_path_scatter = os.path.join(joint_dir, output_filename_scatter)
                plt.tight_layout()
                plt.savefig(output_path_scatter, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  Saved: joint{joint_idx}/{output_filename_scatter}")
                # 平滑線
                if len(frames) > 10:
                    step = max(1, len(frames) // 1000)
                    smooth_frames = frames[::step]
                    smooth_angles = angles[::step]
                    if len(smooth_frames) > 3:
                        plt.figure(figsize=(12, 6))
                        try:
                            spline = make_interp_spline(smooth_frames, smooth_angles, k=3)
                            smooth_x = np.linspace(frames[0], frames[-1], 1000)
                            smooth_y = spline(smooth_x)
                            plt.plot(smooth_x, smooth_y, color='red', linewidth=2, label='Smooth line')
                        except:
                            plt.plot(smooth_frames, smooth_angles, color='red', linewidth=2, label='Smooth line')
                        plt.xlabel('Frame', fontsize=12)
                        plt.ylabel(f'{axis.upper()} Angle [deg]', fontsize=12)
                        plt.grid(True, alpha=0.3)
                        plt.legend()
                        output_filename_smooth = f"{col}_smooth.png"
                        output_path_smooth = os.path.join(joint_dir, output_filename_smooth)
                        plt.tight_layout()
                        plt.savefig(output_path_smooth, dpi=300, bbox_inches='tight')
                        plt.close()
                        print(f"  Saved: joint{joint_idx}/{output_filename_smooth}")

if __name__ == '__main__':
    main() 