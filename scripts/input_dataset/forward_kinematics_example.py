"""
このスクリプトは、hSMALモデルのパラメータ（ポーズ、ベータ、トランスレーション）を用いて、
フォワードキネマティクスにより各フレームの全ジョイントの3次元座標を計算し、
その結果をCSVファイルとして保存します。

同ディレクトリの save_*_batch.py と同様、対象ディレクトリ内の全npzを一括処理します。

【注意】
このスクリプトを実行する際は、PYTHONPATH にプロジェクトルート（PFERD/PFERD）を追加してください。
例: Windowsの場合
    set PYTHONPATH=%cd% && python scripts/input_dataset/forward_kinematics_example.py


【入力ファイル】
- モデルパラメータ: dataset/ID_4/MODEL_DATA/*_hsmal.npz
  （'poses', 'betas', 'trans' を含む）
- hSMALモデル: hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl

【出力ファイル】
- JOINT_MODEL_DATA/Spatial_xyz_Data/ID_4/<npzファイル名>_joints_xyz.csv
  （各フレーム・各ジョイントの3次元座標を格納したCSV、mm単位）
"""
import os
import sys

# utils.smal / scripts.utils を import する前にプロジェクトルートを通しておく
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import glob
import numpy as np
import pandas as pd
import torch

from utils.smal import SMALLayer, HSMAL
from scripts.utils.joint_utils import load_joint_names


def compute_joints_xyz(smal_layer, poses, betas, trans, device):
    """1本のモーションについてフォワードキネマティクスを行い、ジョイント座標[mm]を返す"""
    # posesの最初の3次元がroot、残りがbody
    poses_root = torch.from_numpy(poses[:, :3]).float().to(device)
    poses_body = torch.from_numpy(poses[:, 3:]).float().to(device)
    betas_t = torch.from_numpy(betas).float().to(device)
    trans_t = torch.from_numpy(trans).float().to(device)

    _, joints = smal_layer(poses_body, betas_t, trans_t, poses_root)
    joints = joints.cpu().numpy()  # (フレーム数, ジョイント数, 3)
    return joints * 1000  # m → mm に変換


def main():
    # --- 設定 ---
    horse_id = 'ID_4'
    input_dir = os.path.join('dataset', horse_id, 'MODEL_DATA')
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Spatial_xyz_Data', horse_id)
    model_path = os.path.join('hSMALdata', 'my_smpl_0000_horse_new_skeleton_horse.pkl')
    device = 'cpu'  # 必要に応じて'cuda:0'

    os.makedirs(output_dir, exist_ok=True)

    npz_files = sorted(glob.glob(os.path.join(input_dir, '*_hsmal.npz')))
    if not npz_files:
        print(f"No npz files found in {input_dir}")
        return

    segment_names = load_joint_names(horse_id)

    # モデルのロードは重い（.pklが約58MB）ので、num_betasが同じ間は使い回す
    smal_layer = None
    loaded_num_betas = None

    for npz_path in npz_files:
        print(f'Processing: {os.path.basename(npz_path)}')
        npz = np.load(npz_path, allow_pickle=True)
        poses = npz['poses']      # (フレーム数, 3×ジョイント数)
        betas = npz['betas']      # (体型パラメータ,)
        trans = npz['trans']      # (フレーム数, 3)

        num_betas = betas.shape[0]
        if smal_layer is None or loaded_num_betas != num_betas:
            smal_layer = SMALLayer(
                model_path=model_path,
                model_cls=HSMAL,
                device=device,
                num_betas=num_betas,
            )
            loaded_num_betas = num_betas

        joints = compute_joints_xyz(smal_layer, poses, betas, trans, device)

        num_frames, num_joints, _ = joints.shape
        if num_joints != len(segment_names):
            print(f"  警告: ジョイント数({num_joints})とセグメント名リスト({len(segment_names)})が一致しません。")

        data = {}
        for j, name in enumerate(segment_names[:num_joints]):
            data[f'{j}_{name}_x [mm]'] = joints[:, j, 0]
            data[f'{j}_{name}_y [mm]'] = joints[:, j, 1]
            data[f'{j}_{name}_z [mm]'] = joints[:, j, 2]
        df = pd.DataFrame(data)
        df.insert(0, 'frame', range(num_frames))

        csv_filename = os.path.splitext(os.path.basename(npz_path))[0] + '_joints_xyz.csv'
        csv_path = os.path.join(output_dir, csv_filename)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {csv_path} ({num_frames}フレーム × {num_joints}ジョイント)")


if __name__ == '__main__':
    main()
