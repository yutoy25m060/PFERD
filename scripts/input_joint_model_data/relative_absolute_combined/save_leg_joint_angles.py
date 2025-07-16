"""
脚部の基準ジョイント（4, 9, 18, 23）の絶対角度＋その子孫の相対角度をCSV出力するスクリプト

入力：
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/*.csv
- JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4/*.csv
- JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv

出力：
- JOINT_MODEL_DATA/Leg_Joint_Angles/ID_4/<元ファイル名>_leg_joint_angles.csv
  （各行：frame, <基準ジョイント絶対角度>, <子孫相対角度>...）
"""
import os
import glob
import pandas as pd
import numpy as np
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.joint_utils import load_joint_names, load_joint_hierarchy, get_descendants_dfs

def main():
    horse_id = 'ID_4'
    abs_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id)
    rel_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Degree_from_poses', horse_id)
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Leg_Joint_Angles', horse_id)
    os.makedirs(output_dir, exist_ok=True)

    # 親子構造とジョイント名をCSVファイルから読み込み
    parent_dict = load_joint_hierarchy(horse_id)
    joint_names = load_joint_names(horse_id)
    base_joints = [4, 9, 18, 23]



    abs_files = sorted(glob.glob(os.path.join(abs_dir, '*.csv')))
    rel_files = sorted(glob.glob(os.path.join(rel_dir, '*.csv')))
    if len(abs_files) != len(rel_files):
        print('Warning: ファイル数が一致しません')

    for abs_path, rel_path in zip(abs_files, rel_files):
        print(f'Processing: {os.path.basename(abs_path)}')
        abs_df = pd.read_csv(abs_path)
        rel_df = pd.read_csv(rel_path)
        n_frames = abs_df.shape[0]
        # --- 出力カラム構成 ---
        # 既存のcolumns生成処理
        columns = ['frame']
        # 基準ジョイント:絶対角度
        for j in base_joints:
            for axis in ['x', 'y', 'z']:
                columns.append(f'joint{j}_{joint_names[j]}_{axis}_abs [deg]')
        # 子孫:相対角度（DFS順）
        descendants_dict = {}
        for base in base_joints:
            descendants = get_descendants_dfs(base, parent_dict)
            descendants_dict[base] = descendants
            for j in descendants:
                for axis in ['x', 'y', 'z']:
                    columns.append(f'joint{j}_{joint_names[j]}_{axis}_rel_from_{base} [deg]')
        # --- データ抽出 ---
        out_data = []
        for idx in range(n_frames):
            row = [idx]
            # 絶対角度
            for j in base_joints:
                for axis in ['x', 'y', 'z']:
                    col = f'joint{j}_{joint_names[j]}_{axis} [deg]'
                    row.append(abs_df.at[idx, col])
            # 相対角度（DFS順）
            for base in base_joints:
                descendants = descendants_dict[base]
                for j in descendants:
                    for axis in ['x', 'y', 'z']:
                        col = f'joint{j}_{joint_names[j]}_{axis} [deg]'
                        row.append(rel_df.at[idx, col])
            out_data.append(row)
        out_df = pd.DataFrame(out_data, columns=columns)
        # --- カラム順を指定順に並べ替え ---
        ordered_joints = [4,5,6,7,8,9,10,11,12,13,18,19,20,21,22,23,24,25,26,27]
        ordered_columns = ['frame']
        for j in ordered_joints:
            # 絶対角度カラム
            abs_col = f'joint{j}_{joint_names[j]}_x_abs [deg]'
            if abs_col in out_df.columns:
                for axis in ['x','y','z']:
                    ordered_columns.append(f'joint{j}_{joint_names[j]}_{axis}_abs [deg]')
            # 相対角度カラム
            for base in base_joints:
                rel_col = f'joint{j}_{joint_names[j]}_x_rel_from_{base} [deg]'
                if rel_col in out_df.columns:
                    for axis in ['x','y','z']:
                        ordered_columns.append(f'joint{j}_{joint_names[j]}_{axis}_rel_from_{base} [deg]')
        # frame以外のカラムが重複しないように
        ordered_columns = ['frame'] + [col for col in ordered_columns if col != 'frame' and col in out_df.columns]
        out_df = out_df[ordered_columns]
        # 保存
        base = os.path.splitext(os.path.basename(abs_path))[0].replace('_hsmal_hsmal_absolute', '')
        out_name = f'{base}_leg_joint_angles.csv'
        out_path = os.path.join(output_dir, out_name)
        out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 