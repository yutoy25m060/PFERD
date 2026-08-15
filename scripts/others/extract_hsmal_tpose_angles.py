"""
このスクリプトは、hSMALモデルのテンプレートポーズ（Tポーズ）における
各関節のグローバル回転行列（絶対角度）をオイラー角（xyz順、度）に変換し、
CSVファイルとして保存するものです。

【用途・目的】
- hSMALのTポーズ（全ポーズパラメータ0）は、動物の自然な立脚姿勢であり、
  工学的な「Z軸方向に脚をまっすぐ伸ばした基準姿勢（0度）」とは異なります。
- 本スクリプトで得られる各関節の角度は、
  「Z軸基準から見たTポーズのオフセット角度」として、
  ロボット制御や運動学計算の基準統一に利用できます。

【出力】
- JOINT_MODEL_DATA/Absolute_Angles/hsmal_tpose_angles.csv
  （各ジョイントごとにx, y, z軸の絶対角度[deg]を出力）

【使い方】
- set PYTHONPATH=.
- python scripts/others/extract_hsmal_tpose_angles.py

【備考】
- ジョイント名は scripts/utils/joint_utils.py の load_joint_names(horse_id) から取得します。
- モデルパスや出力先は必要に応じて修正してください。
"""
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
import os

print('1. joint_utilsのimport')
from scripts.utils.cli import parse_horse_id
from scripts.utils.joint_utils import load_joint_names, get_parents_list

try:
    print('2. 出力パス設定')
    OUTPUT_PATH = 'JOINT_MODEL_DATA/Absolute_Angles/hsmal_tpose_angles.csv'

    print('3. 親子関係とジョイント名の取得')
    # parents[j] はジョイントjの親。インデックス順が保証された取得方法を使うこと。
    horse_id = parse_horse_id('Tポーズにおける各関節の絶対角度をCSV保存する')
    parents = get_parents_list(horse_id)
    joint_names = load_joint_names(horse_id)
    n_joints = len(joint_names)
    print(f'   n_joints: {n_joints}')

    print('4. Tポーズの相対回転（全て0ベクトル）')
    xyz_angles = np.zeros((n_joints, 3))

    print('5. 絶対回転行列の計算')
    abs_rotmats = np.zeros((n_joints, 3, 3))
    abs_eulers = np.zeros((n_joints, 3))
    for j in range(n_joints):
        rel_rot = R.from_rotvec(xyz_angles[j, :])
        if parents[j] == -1:
            abs_rotmats[j] = rel_rot.as_matrix()
        else:
            abs_rotmats[j] = abs_rotmats[int(parents[j])] @ rel_rot.as_matrix()
        abs_eulers[j, :] = R.from_matrix(abs_rotmats[j]).as_euler('xyz', degrees=True)

    print('6. DataFrame化・CSV保存')
    df = pd.DataFrame(abs_eulers, columns=['x(deg)', 'y(deg)', 'z(deg)'])
    df.insert(0, 'joint', joint_names)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f'完了: {OUTPUT_PATH} に保存しました')
except Exception as e:
    print(f'エラー発生: {e}') 