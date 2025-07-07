import numpy as np
import torch
from utils.smal import SMALLayer, HSMAL
import os
import pandas as pd

def get_hsmal_segment_names():
    # hSMAL 36セグメント正式名称リスト（インデックス順）
    return [
        'pelvis', 'left_hip', 'right_hip', 'spine1', 'left_knee', 'right_knee', 'spine2', 'left_ankle', 'right_ankle',
        'spine3', 'left_foot', 'right_foot', 'neck', 'left_collar', 'right_collar', 'head', 'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'jaw', 'left_eye_smplhf', 'right_eye_smplhf',
        'left_index1', 'left_index2', 'left_index3', 'left_middle1', 'left_middle2', 'left_middle3',
        'left_pinky1', 'left_pinky2', 'left_pinky3', 'left_ring1', 'left_ring2'
    ]

def main():
    # 1. モデルのパラメータ（poses, betas, trans）を用意
    horse_id = 'ID_4'
    npz_path = os.path.join('dataset', horse_id, 'MODEL_DATA', '20201129_ID_4_0007_hsmal.npz')
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
        data[f'{j}_{name}_x'] = joints[:, j, 0]
        data[f'{j}_{name}_y'] = joints[:, j, 1]
        data[f'{j}_{name}_z'] = joints[:, j, 2]
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