"""
このスクリプトは、PyTorchを用いてhSMALモデルのテンプレートポーズ（Tポーズ）における
各関節のグローバル回転行列（絶対角度）をforward計算で取得し、
オイラー角（xyz順、度）に変換してCSVファイルとして保存します。

【用途・目的】
- テンプレートメッシュの「本当のオフセット角度」を抽出し、
  ロボット制御や運動学計算の基準統一に利用できます。

【出力】
- JOINT_MODEL_DATA/Absolute_Angles/hsmal_tpose_offsets_pytorch.csv
  （各ジョイントごとにx, y, z軸の絶対角度[deg]を出力）

【使い方】
- set PYTHONPATH=.
- python scripts/others/extract_hsmal_tpose_offsets_pytorch.py

【備考】
- ジョイント名は scripts/utils/joint_utils.py の load_joint_names('ID_4') から取得します。
- モデルパスや出力先は必要に応じて修正してください。
"""
import torch
from utils.smal import HSMAL
from scipy.spatial.transform import Rotation as R
import numpy as np
import pandas as pd
import os

MODEL_PATH = 'hSMALdata/hSMAL_template.npz'
OUTPUT_PATH = 'JOINT_MODEL_DATA/Absolute_Angles/hsmal_tpose_offsets_pytorch.csv'

print('1. hSMALモデルをロード')
model = HSMAL(model_path=MODEL_PATH)

print('2. Tポーズ（全ポーズパラメータ0）をセット')
poses_body = torch.zeros((1, model.NUM_JOINTS * 3))
betas = torch.zeros((1, model.NUM_BETAS))
trans = torch.zeros((1, 3))

print('3. forward計算')
output = model(betas=betas, poses_body=poses_body, trans=trans)
rotmats = output.joint_rotmats[0].detach().cpu().numpy()  # (N, 3, 3)
print(f'   rotmats shape: {rotmats.shape}')

print('4. オイラー角に変換')
euler_angles = [R.from_matrix(rotmat).as_euler('xyz', degrees=True) for rotmat in rotmats]
euler_angles = np.array(euler_angles)

print('5. ジョイント名の取得')
from scripts.utils.joint_utils import load_joint_names
joint_names = load_joint_names('ID_4')

print('6. CSV保存')
df = pd.DataFrame(euler_angles, columns=['x(deg)', 'y(deg)', 'z(deg)'])
df.insert(0, 'joint', joint_names)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)
print(f'完了: {OUTPUT_PATH} に保存しました') 