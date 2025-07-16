"""
hSMALモデルのテンプレートポーズ（Tポーズ）における各ジョイントの空間座標と親子関係情報をもとに、
3Dスケルトン＋各ジョイントのxyz軸ベクトルを可視化するスクリプト

【使い方】
- Windows環境では、以下の環境変数設定が必要です:
    set KMP_DUPLICATE_LIB_OK=TRUE&& set PYTHONPATH=.
- 実行:
    set KMP_DUPLICATE_LIB_OK=TRUE&& set PYTHONPATH=.&& python scripts/others/visualize_hsmal_axes.py
"""
import numpy as np
import torch
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import csv
import os
from utils.smal import SMALLayer, HSMAL
from scipy.spatial.transform import Rotation as R

# --- 設定 ---
model_path = os.path.join('hSMALdata', 'my_smpl_0000_horse_new_skeleton_horse.pkl')
parents_csv = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', 'ID_4', 'parents_hsmal36.csv')
names_csv = parents_csv  # 統合ファイルを参照
device = 'cpu'

# --- 親子関係の読み込み ---
def load_parents(parents_csv):
    parents = []
    with open(parents_csv, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            parents.append(int(row['parent_index']))
    return parents

def load_joint_names(names_csv):
    names = []
    with open(names_csv, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            names.append(row['joint_name'])
    return names

# --- hSMALテンプレートポーズのジョイント座標・回転行列取得 ---
def get_tpose_joints_and_rotmats(model_path, device):
    num_betas = 10
    smal_layer = SMALLayer(
        model_path=model_path,
        model_cls=HSMAL,
        device=device,
        num_betas=num_betas,
    )
    batch_size = 1
    poses_body = torch.zeros((batch_size, HSMAL.NUM_BODY_JOINTS * 3), dtype=torch.float32, device=device)
    betas = torch.zeros((batch_size, num_betas), dtype=torch.float32, device=device)
    trans = torch.zeros((batch_size, 3), dtype=torch.float32, device=device)
    poses_root = torch.zeros((batch_size, 3), dtype=torch.float32, device=device)
    output = smal_layer.bm(
        betas=betas,
        body_pose=poses_body,
        global_orient=poses_root,
        transl=trans,
        return_full_pose=True
    )
    joints = output.joints[0].cpu().numpy()  # (N, 3)
    axis_angles = output.full_pose[0].cpu().numpy()  # (N*3,)
    num_joints = axis_angles.shape[0] // 3
    rot_mats = R.from_rotvec(axis_angles.reshape(num_joints, 3)).as_matrix()  # (N, 3, 3)
    return joints, rot_mats

# --- メイン処理 ---
def main():
    parents = load_parents(parents_csv)
    joint_names = load_joint_names(names_csv)
    joints, rot_mats = get_tpose_joints_and_rotmats(model_path, device)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # ジョイントを点で描画
    ax.scatter(joints[:, 0], joints[:, 1], joints[:, 2], c='r', s=40)

    # 親子関係で線を描画
    for i, parent in enumerate(parents):
        if parent == -1:
            continue
        xs = [joints[i, 0], joints[parent, 0]]
        ys = [joints[i, 1], joints[parent, 1]]
        zs = [joints[i, 2], joints[parent, 2]]
        ax.plot(xs, ys, zs, c='b')
        ax.text(joints[i, 0], joints[i, 1], joints[i, 2], joint_names[i], fontsize=8)

    # --- 各ジョイントのxyz軸ベクトルを可視化 ---
    axis_len = 0.05  # 矢印の長さ
    for i in range(joints.shape[0]):
        origin = joints[i]
        x_axis = rot_mats[i][:, 0]  # ローカルx軸
        y_axis = rot_mats[i][:, 1]  # ローカルy軸
        z_axis = rot_mats[i][:, 2]  # ローカルz軸
        ax.quiver(
            origin[0], origin[1], origin[2],
            x_axis[0], x_axis[1], x_axis[2],
            length=axis_len, color='r', arrow_length_ratio=0.3, linewidth=1.5, label='x' if i==0 else ""
        )
        ax.quiver(
            origin[0], origin[1], origin[2],
            y_axis[0], y_axis[1], y_axis[2],
            length=axis_len, color='g', arrow_length_ratio=0.3, linewidth=1.5, label='y' if i==0 else ""
        )
        ax.quiver(
            origin[0], origin[1], origin[2],
            z_axis[0], z_axis[1], z_axis[2],
            length=axis_len, color='b', arrow_length_ratio=0.3, linewidth=1.5, label='z' if i==0 else ""
        )

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('hSMAL Skeleton (T-pose) with Joint Axes')
    plt.tight_layout()
    ax.set_box_aspect([1, 1, 1])  # xyz軸のスケールを等しく
    plt.show()

if __name__ == '__main__':
    main() 