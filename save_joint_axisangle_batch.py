import os
import glob
import numpy as np
import pandas as pd

# --- 設定 ---
horse_id = 'ID_4'
input_dir = os.path.join('dataset', horse_id, 'MODEL_DATA')
output_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Data_from_poses', horse_id)

# hSMAL 36セグメント正式名称リスト
segment_names = [
    'pelvis', 'left_hip', 'right_hip', 'spine1', 'left_knee', 'right_knee', 'spine2', 'left_ankle', 'right_ankle',
    'spine3', 'left_foot', 'right_foot', 'neck', 'left_collar', 'right_collar', 'head', 'left_shoulder', 'right_shoulder',
    'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'jaw', 'left_eye_smplhf', 'right_eye_smplhf',
    'left_index1', 'left_index2', 'left_index3', 'left_middle1', 'left_middle2', 'left_middle3',
    'left_pinky1', 'left_pinky2', 'left_pinky3', 'left_ring1', 'left_ring2'
]

os.makedirs(output_dir, exist_ok=True)

npz_files = sorted(glob.glob(os.path.join(input_dir, '*_hsmal.npz')))

if not npz_files:
    print(f"No npz files found in {input_dir}")
    exit(1)

for npz_path in npz_files:
    npz = np.load(npz_path, allow_pickle=True)
    poses = npz['poses']  # shape: (フレーム数, 108)
    n_frames = poses.shape[0]
    n_joints = 36
    assert poses.shape[1] == n_joints * 3, f"poses shape mismatch: {poses.shape}"

    data = {}
    for j, name in enumerate(segment_names[:n_joints]):
        data[f'{j}_{name}_axis_x'] = poses[:, j*3 + 0]
        data[f'{j}_{name}_axis_y'] = poses[:, j*3 + 1]
        data[f'{j}_{name}_axis_z'] = poses[:, j*3 + 2]
    df = pd.DataFrame(data)
    df.insert(0, 'frame', range(n_frames))

    npz_base = os.path.splitext(os.path.basename(npz_path))[0]
    csv_filename = f"{npz_base}_axisangle.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"Saved: {csv_path}") 