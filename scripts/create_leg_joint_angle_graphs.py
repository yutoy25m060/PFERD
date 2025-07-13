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
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import re


def main():
    horse_id = 'ID_4'
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Leg_Joint_Angles', horse_id)
    output_base_dir = os.path.join(input_dir, 'graphs')
    os.makedirs(output_base_dir, exist_ok=True)

    # CSVファイルを全て取得
    csv_files = sorted(glob.glob(os.path.join(input_dir, '*_leg_joint_angles.csv')))
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    # 日本語フォント設定
    plt.rcParams['font.family'] = 'DejaVu Sans'

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
            m = re.match(r'(joint\d+)_', col)
            joint_dir = csv_output_dir
            if m:
                # '_abs'がカラム名に含まれる場合はjointXX_abs、それ以外はjointXX
                if '_abs' in col:
                    joint_dir = os.path.join(csv_output_dir, m.group(1) + '_abs')
                else:
                    joint_dir = os.path.join(csv_output_dir, m.group(1))
                os.makedirs(joint_dir, exist_ok=True)
            angles = df[col].values
            # --- 散布図 ---
            plt.figure(figsize=(12, 6))
            plt.scatter(frames, angles, alpha=0.6, s=1, color='blue', label='Data points')
            plt.xlabel('Frame', fontsize=12)
            plt.ylabel(col, fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            output_filename_scatter = f"{col}_scatter.png"
            output_path_scatter = os.path.join(joint_dir, output_filename_scatter)
            plt.tight_layout()
            plt.savefig(output_path_scatter, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  Saved: {os.path.relpath(output_path_scatter, csv_output_dir)}")
            # --- 平滑線 ---
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
                    except Exception as e:
                        print(f"  Spline error: {e}, fallback to simple plot.")
                        plt.plot(smooth_frames, smooth_angles, color='red', linewidth=2, label='Smooth line')
                    plt.xlabel('Frame', fontsize=12)
                    plt.ylabel(col, fontsize=12)
                    plt.grid(True, alpha=0.3)
                    plt.legend()
                    output_filename_smooth = f"{col}_smooth.png"
                    output_path_smooth = os.path.join(joint_dir, output_filename_smooth)
                    plt.tight_layout()
                    plt.savefig(output_path_smooth, dpi=300, bbox_inches='tight')
                    plt.close()
                    print(f"  Saved: {os.path.relpath(output_path_smooth, csv_output_dir)}")

if __name__ == '__main__':
    main() 