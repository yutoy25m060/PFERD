import os
import glob
import pandas as pd
import numpy as np
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.cli import build_parser
from scripts.utils.joint_utils import load_joint_names
from scripts.utils.plotting import save_scatter, save_smooth

# 設定
args = build_parser('絶対角度と相対角度を同一y軸範囲で並べたグラフを生成する', graph_args=True).parse_args()
horse_id = args.horse_id
abs_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id)
xyz_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Degree_from_poses', horse_id)
abs_sel_dir = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id, 'Absolute_Angles')
xyz_sel_dir = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id, 'Angle_xyz_Degree_from_poses')
os.makedirs(abs_sel_dir, exist_ok=True)
os.makedirs(xyz_sel_dir, exist_ok=True)

axes = ['x', 'y', 'z']
joint_names = load_joint_names(horse_id)

# ファイルペア探索
abs_files = sorted(glob.glob(os.path.join(abs_dir, '*.csv')))
xyz_files = sorted(glob.glob(os.path.join(xyz_dir, '*_hsmal_axisangle_xyzangle_deg.csv')))

# ベース名でペアリング
abs_dict = {os.path.basename(f).replace('_hsmal_hsmal_absolute.csv', ''): f for f in abs_files}
xyz_dict = {os.path.basename(f).replace('_hsmal_axisangle_xyzangle_deg.csv', ''): f for f in xyz_files}
common_keys = sorted(set(abs_dict.keys()) & set(xyz_dict.keys()))

if not common_keys:
    print('対応するファイルペアが見つかりません')
    exit()

print(f'ペアとなるファイル数: {len(common_keys)}')
for idx, key in enumerate(common_keys):
    print(f'[{idx+1}/{len(common_keys)}] ファイルペア: {key}')
    abs_csv = abs_dict[key]
    xyz_csv = xyz_dict[key]
    abs_df = pd.read_csv(abs_csv)
    xyz_df = pd.read_csv(xyz_csv)
    frames_abs = abs_df['frame'].values
    frames_xyz = xyz_df['frame'].values
    # 各ジョイント・各軸ごとにy軸範囲を決定
    for joint_idx, joint_name in enumerate(joint_names):
        if args.joints is not None and joint_idx not in args.joints:
            continue
        print(f'  ジョイント: joint{joint_idx} ({joint_name})')
        for axis in axes:
            col = f'joint{joint_idx}_{joint_name}_{axis} [deg]'
            if col not in abs_df.columns or col not in xyz_df.columns:
                print(f'    軸: {axis} ... 対応するカラムなし（スキップ）')
                continue
            abs_angles = abs_df[col].values
            xyz_angles = xyz_df[col].values
            # y軸範囲を両方のデータから決定
            y_min = min(np.min(abs_angles), np.min(xyz_angles))
            y_max = max(np.max(abs_angles), np.max(xyz_angles))
            abs_outdir = os.path.join(abs_sel_dir, f'{key}_hsmal_hsmal_absolute', f'joint{joint_idx}')
            xyz_outdir = os.path.join(xyz_sel_dir, f'{key}_hsmal_axisangle_xyzangle_deg', f'joint{joint_idx}')
            os.makedirs(abs_outdir, exist_ok=True)
            os.makedirs(xyz_outdir, exist_ok=True)
            for mode, data, frames, outdir, label in [
                ('scatter', abs_angles, frames_abs, abs_outdir, 'Absolute_Angles'),
                ('smooth', abs_angles, frames_abs, abs_outdir, 'Absolute_Angles'),
                ('scatter', xyz_angles, frames_xyz, xyz_outdir, 'Angle_xyz_Degree_from_poses'),
                ('smooth', xyz_angles, frames_xyz, xyz_outdir, 'Angle_xyz_Degree_from_poses')
            ]:
                print(f'    軸: {axis} | {label} | {mode} ... 作成中')
                fname = f'joint{joint_idx}_{joint_name}_{axis}_{mode}.png'
                save_path = os.path.join(outdir, fname)
                ylabel = f'{axis.upper()} Angle [deg]'
                # 絶対角度と相対角度を見比べられるよう、y軸範囲は両者の和集合で揃える
                ylim = (y_min, y_max)
                if mode == 'scatter':
                    save_scatter(frames, data, ylabel, save_path, dpi=args.dpi, ylim=ylim)
                    print(f'      → 保存: {save_path}')
                elif save_smooth(frames, data, ylabel, save_path, dpi=args.dpi, ylim=ylim):
                    print(f'      → 保存: {save_path}')
                # y軸範囲をテキストで保存（scatterのときのみでOK）
                if mode == 'scatter':
                    yaxis_txt = os.path.join(outdir, f'joint{joint_idx}_{joint_name}_{axis}_yaxis.txt')
                    with open(yaxis_txt, 'w', encoding='utf-8') as f:
                        f.write(f'{y_min},{y_max}\n')

print('全てのグラフ作成が完了しました。') 