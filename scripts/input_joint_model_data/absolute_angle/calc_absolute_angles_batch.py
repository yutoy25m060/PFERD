"""
このスクリプトは、Angle_xyz_Data_from_posesの各CSVファイルから、
親子関係を用いて各ジョイントの絶対角度（ワールド座標系でのx, y, z角度, degree）を計算し、
JOINT_MODEL_DATA/Absolute_Angles/ID_4/ に短いファイル名で保存します。

【「絶対角度」とは】
- 各ジョイントが「ワールド座標系（グローバル座標系）」に対してどの向きに回転しているかを表す角度。
  親ジョイントから見た相対角度（poses に入っている値）とは異なる。
- 算出方法: 親子関係をルートからたどり、親のグローバル回転行列に自身の相対回転行列を
  右から掛けて累積する（R_global[j] = R_global[parent] @ R_local[j]）。
  得られたグローバル回転行列を xyz 順のオイラー角（度）に変換して出力する。
- Tポーズ（全ジョイントの相対角度が0）では、全ジョイントの絶対角度も0度になる。

【入力ファイル】
- JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4/*.csv
- JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv

【出力ファイル】
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/元ファイル名_hsmal_absolute.csv
  （各行：frame, joint0_pelvis_x [deg], joint0_pelvis_y [deg], joint0_pelvis_z [deg], ...）
"""
import os
import glob
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.cli import parse_horse_id
from scripts.utils.joint_utils import load_joint_names, get_parents_list


def compute_absolute_eulers(xyz_angles, parents):
    """
    相対回転（axis-angle）から絶対回転のオイラー角[deg]を計算する

    R_global[j] = R_global[parent[j]] @ R_local[j] を親から順に累積する。
    フレーム方向はまとめて処理するため、ループはジョイント数（36回）だけで済む。

    Args:
        xyz_angles: (フレーム数, ジョイント数, 3) の axis-angle [rad]
        parents: parents[j] = ジョイントjの親インデックス（ルートは-1）

    Returns:
        ndarray: (フレーム数, ジョイント数, 3) のオイラー角 [deg]（xyz順）
    """
    n_frames, n_joints, _ = xyz_angles.shape

    # 親を先に計算し終えている必要があるため、親のインデックスが自分より小さいことを確認する
    for j, p in enumerate(parents):
        if p != -1 and not 0 <= p < j:
            raise ValueError(
                f"親子構造が親→子の順に並んでいません（joint{j} の親が {p}）。"
                "parents_hsmal36.csv を確認してください。")

    # 全フレーム・全ジョイントの相対回転行列を一括変換
    rel_mats = R.from_rotvec(xyz_angles.reshape(-1, 3)).as_matrix()
    rel_mats = rel_mats.reshape(n_frames, n_joints, 3, 3)

    abs_mats = np.empty_like(rel_mats)
    for j, p in enumerate(parents):
        if p == -1:
            abs_mats[:, j] = rel_mats[:, j]
        else:
            # (フレーム数,3,3) @ (フレーム数,3,3) のバッチ行列積
            abs_mats[:, j] = abs_mats[:, p] @ rel_mats[:, j]

    eulers = R.from_matrix(abs_mats.reshape(-1, 3, 3)).as_euler('xyz', degrees=True)
    return eulers.reshape(n_frames, n_joints, 3)


def main():
    horse_id = parse_horse_id('各ジョイントの絶対角度（ワールド座標系）を計算する')
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Data_from_poses', horse_id)
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id)
    os.makedirs(output_dir, exist_ok=True)

    # 親子構造とジョイント名をCSVファイルから読み込み
    # parents[j] はジョイントjの親。インデックス順が保証された取得方法を使うこと。
    parents = get_parents_list(horse_id)
    joint_names = load_joint_names(horse_id)
    n_joints = len(joint_names)

    csv_files = sorted(glob.glob(os.path.join(input_dir, '*.csv')))
    if not csv_files:
        print(f'No CSV files found in {input_dir}')
        return

    for csv_file in csv_files:
        print(f'Processing: {os.path.basename(csv_file)}')
        df = pd.read_csv(csv_file)
        data = df.values  # shape: (frame数, 関節数×3 + 1)
        n_frames, n_cols = data.shape
        # 1列目（frame列）を除外
        data = data[:, 1:]
        xyz_angles = data.reshape(n_frames, n_joints, 3)  # (frame, joint, xyz)

        abs_eulers = compute_absolute_eulers(xyz_angles, parents)
        # DataFrame化
        columns = []
        for j, name in enumerate(joint_names):
            columns.extend([f'joint{j}_{name}_x [deg]', f'joint{j}_{name}_y [deg]', f'joint{j}_{name}_z [deg]'])
        out_df = pd.DataFrame(abs_eulers.reshape(n_frames, n_joints*3), columns=columns)
        out_df.insert(0, 'frame', range(n_frames))
        # 出力ファイル名
        base = os.path.basename(csv_file).replace('_axisangle.csv', '').replace('.csv', '')
        out_name = f'{base}_hsmal_absolute.csv'
        out_path = os.path.join(output_dir, out_name)
        out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 