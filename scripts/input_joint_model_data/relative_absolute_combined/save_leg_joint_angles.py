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
import re
import glob
import pandas as pd
import numpy as np
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.joint_utils import load_joint_names, load_joint_hierarchy, get_descendants_dfs

# 計測データ名（例: 20201129_ID_4_0002）をファイル名の先頭から取り出す
DATA_KEY_RE = re.compile(r'^(\d{8}_ID_\d+_\d+)')


def build_key_map(paths):
    """計測データ名 -> ファイルパス の辞書を作る（キーを取れないファイルは無視）"""
    key_map = {}
    for path in sorted(paths):
        m = DATA_KEY_RE.match(os.path.basename(path))
        if m:
            key_map[m.group(1)] = path
    return key_map


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



    # 絶対角度CSVと相対角度CSVは「計測データ名」をキーにして対応付ける。
    # ソート順のindexで zip すると、片方に過不足があったときに
    # 別の計測データ同士を1行に混ぜたCSVをエラーなしで生成してしまうため。
    abs_map = build_key_map(glob.glob(os.path.join(abs_dir, '*.csv')))
    rel_map = build_key_map(glob.glob(os.path.join(rel_dir, '*.csv')))

    common_keys = sorted(set(abs_map) & set(rel_map))
    for key in sorted(set(abs_map) ^ set(rel_map)):
        side = '相対角度' if key in abs_map else '絶対角度'
        print(f'Warning: {key} は{side}CSVが見つからないためスキップします')
    if not common_keys:
        print(f'対応するファイルペアが見つかりません: {abs_dir} / {rel_dir}')
        return

    for key in common_keys:
        abs_path, rel_path = abs_map[key], rel_map[key]
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
        # 保存（ファイル名は計測データ名から組み立てる）
        out_name = f'{key}_leg_joint_angles.csv'
        out_path = os.path.join(output_dir, out_name)
        out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 