"""
このスクリプトは、hSMALモデルのパラメータ（ポーズ、ベータ、トランスレーション）を用いて、
フォワードキネマティクスにより各フレームの全ジョイントの3次元座標を計算し、
その結果をCSVファイルとして保存します。

【注意】
このスクリプトを実行する際は、PYTHONPATH にプロジェクトルート（PFERD/PFERD）を追加してください。
例: Windowsの場合
    set PYTHONPATH=%cd% && python scripts/forward_kinematics_example.py


【入力ファイル】
- モデルパラメータ: dataset/ID_4/MODEL_DATA/20201129_ID_4_0002_hsmal.npz
  （'poses', 'betas', 'trans' を含む）
- hSMALモデル: hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl

【出力ファイル】
- JOINT_MODEL_DATA/Spatial_xyz_Data/ID_4/20201129_ID_4_0002_hsmal_joints_xyz.csv
  （各フレーム・各ジョイントの3次元座標を格納したCSV）
"""
import numpy as np
import torch
from utils.smal import SMALLayer, HSMAL
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.joint_utils import load_joint_names

def get_hsmal_segment_names():
    # ジョイント名をCSVファイルから読み込み
    return load_joint_names('ID_4')

def main():
    # 1. モデルのパラメータ（poses, betas, trans）を用意
    horse_id = 'ID_4'
    npz_path = os.path.join('dataset', horse_id, 'MODEL_DATA', '20201129_ID_4_0002_hsmal.npz')
    model_path = os.path.join('hSMALdata', 'my_smpl_0000_horse_new_skeleton_horse.pkl')
    npz = np.load(npz_path, allow_pickle=True)
    poses = npz['poses']      # (フレーム数, 3×ジョイント数)
    betas = npz['betas']      # (体型パラメータ)
    trans = npz['trans']      # (フレーム数, 3)

    # posesを分割（例：最初の3次元がroot、残りがbody）
    poses_root = poses[:, :3]
    poses_body = poses[:, 3:]

    # torch.tensorに変換
    device = 'cpu'  # 必要に応じて'cuda:0'
    poses_body = torch.from_numpy(poses_body).float().to(device)
    betas = torch.from_numpy(betas).float().to(device)
    trans = torch.from_numpy(trans).float().to(device)
    poses_root = torch.from_numpy(poses_root).float().to(device)

    # 2. スケルトン階層に従ってフォワードキネマティクスを実行
    # 3. モデルクラス（SMALLayer）でforward計算
    smal_layer = SMALLayer(
        model_path=model_path,
        model_cls=HSMAL,
        device=device,
        num_betas=betas.shape[0],
    )
    # forward計算で各ジョイントの空間座標を取得
    _, joints = smal_layer(poses_body, betas, trans, poses_root)
    joints = joints.cpu().numpy()  # (フレーム数, ジョイント数, 3)
    joints = joints * 1000  # m → mm に変換


    print(f"joints shape: {joints.shape}")
    print(f"ジョイント数: {joints.shape[1]}")
    print(f"1フレーム目の全ジョイント座標:\n{joints[0]}")

    # --- CSV保存処理 ---
    num_frames, num_joints, _ = joints.shape
    segment_names = get_hsmal_segment_names()
    if num_joints != len(segment_names):
        print(f"警告: ジョイント数({num_joints})とセグメント名リスト({len(segment_names)})が一致しません。")
    data = {}
    for j, name in enumerate(segment_names[:num_joints]):
        data[f'{j}_{name}_x [mm]'] = joints[:, j, 0]
        data[f'{j}_{name}_y [mm]'] = joints[:, j, 1]
        data[f'{j}_{name}_z [mm]'] = joints[:, j, 2]
    df = pd.DataFrame(data)
    df.insert(0, 'frame', range(num_frames))
    # 出力先ディレクトリ
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Spatial_xyz_Data', horse_id)
    os.makedirs(output_dir, exist_ok=True)
    csv_filename = os.path.splitext(os.path.basename(npz_path))[0] + '_joints_xyz.csv'
    csv_path = os.path.join(output_dir, csv_filename)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"Saved: {csv_path}")

if __name__ == '__main__':
    main() 