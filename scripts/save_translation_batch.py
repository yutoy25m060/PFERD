"""
このスクリプトは、hSMALモデル推定結果（npzファイル）から全体の並進（trans）を抽出し、
CSVファイルとして保存します。

【入力ファイル】
- dataset/ID_4/MODEL_DATA/*_hsmal.npz
  （'trans' を含む）

【出力ファイル】
- JOINT_MODEL_DATA/Spatial_xyz_Data_from_trans/ID_4/*_trans.csv
  （全体の並進（trans）のCSV）
"""
import os
import glob
import numpy as np
import pandas as pd

def main():
    # --- 設定 ---
    horse_id = 'ID_4'
    input_dir = os.path.join('dataset', horse_id, 'MODEL_DATA')
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Spatial_xyz_Data_from_trans', horse_id)

    # transはモデル全体の並進なのでカラム名は frame, trans_x, trans_y, trans_z のままでOK
    os.makedirs(output_dir, exist_ok=True)

    npz_files = sorted(glob.glob(os.path.join(input_dir, '*_hsmal.npz')))

    if not npz_files:
        print(f"No npz files found in {input_dir}")
        return

    for npz_path in npz_files:
        npz = np.load(npz_path, allow_pickle=True)
        trans = npz['trans']  # shape: (フレーム数, 3)
        trans = trans * 1000  # m → mm に変換
        n_frames = trans.shape[0]
        assert trans.shape[1] == 3, f"trans shape mismatch: {trans.shape}"

        df = pd.DataFrame(trans, columns=['trans_x [mm]', 'trans_y [mm]', 'trans_z [mm]'])
        df.insert(0, 'frame', range(n_frames))

        npz_base = os.path.splitext(os.path.basename(npz_path))[0]
        csv_filename = f"{npz_base}_trans.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {csv_path}")

if __name__ == '__main__':
    main() 