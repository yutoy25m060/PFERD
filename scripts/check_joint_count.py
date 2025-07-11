"""
このスクリプトは、hSMALモデルのパラメータファイル（npz）を読み込み、
フォワードキネマティクス計算を通じてジョイント数や形状を確認するためのものです。

【入力ファイル】
- dataset/ID_4/MODEL_DATA/20201129_ID_4_0007_hsmal.npz
  （'poses', 'betas', 'trans' を含む）
- hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl

【出力】
- 標準出力にジョイント数やshapeを表示
"""
import numpy as np
import torch
from utils.smal import SMALLayer, HSMAL
import os

def main():
    npz_path = os.path.join('dataset', 'ID_4', 'MODEL_DATA', '20201129_ID_4_0007_hsmal.npz')
    model_path = os.path.join('hSMALdata', 'my_smpl_0000_horse_new_skeleton_horse.pkl')
    npz = np.load(npz_path, allow_pickle=True)
    poses = npz['poses']
    betas = npz['betas']
    trans = npz['trans']
    poses_root = poses[:, :3]
    poses_body = poses[:, 3:]
    device = 'cpu'
    poses_body = torch.from_numpy(poses_body).float().to(device)
    betas = torch.from_numpy(betas).float().to(device)
    trans = torch.from_numpy(trans).float().to(device)
    poses_root = torch.from_numpy(poses_root).float().to(device)
    smal_layer = SMALLayer(
        model_path=model_path,
        model_cls=HSMAL,
        device=device,
        num_betas=betas.shape[0],
    )
    _, joints = smal_layer(poses_body, betas, trans, poses_root)
    joints = joints.cpu().numpy()
    print(f"joints.shape: {joints.shape}")
    print(f"ジョイント数: {joints.shape[1]}")

if __name__ == '__main__':
    main() 