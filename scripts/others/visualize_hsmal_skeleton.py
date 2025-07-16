"""
hSMALモデルのテンプレートポーズ（Tポーズ）における各ジョイントの空間座標と親子関係情報をもとに、3Dスケルトンを可視化するスクリプト

【使い方】
- Windows環境では、以下の環境変数設定が必要です:
    set KMP_DUPLICATE_LIB_OK=TRUE&& set PYTHONPATH=.
- 実行:
    set KMP_DUPLICATE_LIB_OK=TRUE&& set PYTHONPATH=.&& python scripts/others/visualize_hsmal_skeleton.py
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
npz_path = None  # 今回はテンプレートポーズなので不要
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

# --- hSMALテンプレートポーズのジョイント座標取得 ---
def get_tpose_joints(model_path, device):
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
    return joints

# --- メイン処理 ---
def main():
    parents = load_parents(parents_csv)
    joint_names = load_joint_names(names_csv)
    joints = get_tpose_joints(model_path, device)

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

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('hSMAL Skeleton (T-pose)')
    plt.tight_layout()
    ax.set_box_aspect([1, 1, 1])  # xyz軸のスケールを等しく
    plt.show()

if __name__ == '__main__':
    main() 