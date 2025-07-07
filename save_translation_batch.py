import os
import glob
import numpy as np
import pandas as pd

# --- 設定 ---
horse_id = 'ID_4'
input_dir = os.path.join('dataset', horse_id, 'MODEL_DATA')
output_dir = os.path.join('JOINT_MODEL_DATA', 'Spatial_xyz_Data_from_trans', horse_id)

# transはモデル全体の並進なのでカラム名は frame, trans_x, trans_y, trans_z のままでOK
os.makedirs(output_dir, exist_ok=True)

npz_files = sorted(glob.glob(os.path.join(input_dir, '*_hsmal.npz')))

if not npz_files:
    print(f"No npz files found in {input_dir}")
    exit(1)

for npz_path in npz_files:
    npz = np.load(npz_path, allow_pickle=True)
    trans = npz['trans']  # shape: (フレーム数, 3)
    n_frames = trans.shape[0]
    assert trans.shape[1] == 3, f"trans shape mismatch: {trans.shape}"

    df = pd.DataFrame(trans, columns=['trans_x', 'trans_y', 'trans_z'])
    df.insert(0, 'frame', range(n_frames))

    npz_base = os.path.splitext(os.path.basename(npz_path))[0]
    csv_filename = f"{npz_base}_trans.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"Saved: {csv_path}") 