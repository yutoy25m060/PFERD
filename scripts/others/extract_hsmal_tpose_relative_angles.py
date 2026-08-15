"""
このスクリプトは、hSMALモデルのテンプレートポーズ（Tポーズ）における
各関節の相対回転（全て0ベクトル）を明示的に出力し、
CSVファイルとして保存するものです。

【用途・目的】
- hSMALのTポーズ（全ポーズパラメータ0）における各関節の相対回転を確認
- 相対回転が全て0ベクトル（0度）であることを明示的に出力
- ロボット制御や運動学計算の基準統一に利用

【出力】
- JOINT_MODEL_DATA/hsmal_tpose_relative_angles.csv
  （各ジョイントごとにx, y, z軸の相対回転角度[deg]を出力、全て0度）

【使い方】
- set PYTHONPATH=.
- python scripts/others/extract_hsmal_tpose_relative_angles.py

【備考】
- ジョイント名は scripts/utils/joint_utils.py の load_joint_names(horse_id) から取得します。
- モデルパスや出力先は必要に応じて修正してください。
"""
import numpy as np
import pandas as pd
import os

print('1. joint_utilsのimport')
from scripts.utils.cli import parse_horse_id
from scripts.utils.joint_utils import load_joint_names

try:
    print('2. 出力パス設定')
    OUTPUT_PATH = 'JOINT_MODEL_DATA/hsmal_tpose_relative_angles.csv'

    print('3. ジョイント名の取得')
    horse_id = parse_horse_id('Tポーズにおける各関節の相対回転（全て0度）をCSV保存する')
    joint_names = load_joint_names(horse_id)
    n_joints = len(joint_names)
    print(f'   n_joints: {n_joints}')

    print('4. Tポーズの相対回転（全て0ベクトル）')
    # Tポーズでは全ての関節の相対回転が0度
    relative_angles = np.zeros((n_joints, 3))  # (n_joints, 3) の0行列
    print(f'   relative_angles shape: {relative_angles.shape}')
    print(f'   全ての関節の相対回転が0度であることを確認: {np.all(relative_angles == 0)}')

    print('5. DataFrame化・CSV保存')
    df = pd.DataFrame(relative_angles, columns=['x(deg)', 'y(deg)', 'z(deg)'])
    df.insert(0, 'joint', joint_names)
    
    # 出力ディレクトリの作成
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # CSVファイルとして保存
    df.to_csv(OUTPUT_PATH, index=False)
    print(f'完了: {OUTPUT_PATH} に保存しました')
    
    print('6. 保存内容の確認')
    print(f'   保存されたデータの形状: {df.shape}')
    print(f'   最初の5行:')
    print(df.head())
    print(f'   全ての角度が0度であることを確認: {np.all(df[["x(deg)", "y(deg)", "z(deg)"]].values == 0)}')
    
except Exception as e:
    print(f'エラー発生: {e}')
    import traceback
    traceback.print_exc() 