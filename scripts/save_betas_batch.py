"""
このスクリプトは、hSMALモデル推定結果（npzファイル）から体型パラメータ（betas）を抽出し、
CSVファイルとして保存します。

【入力ファイル】
- dataset/ID_4/MODEL_DATA/*_hsmal.npz
  （'betas' を含む）

【出力ファイル】
- JOINT_MODEL_DATA/Beta_shape_Data/ID_4/*_betas.csv
  （体型パラメータ（betas）のCSV）
"""
import os
import glob
import numpy as np
import pandas as pd

def main():
    # --- 設定 ---
    horse_id = 'ID_4'
    input_dir = os.path.join('dataset', horse_id, 'MODEL_DATA')
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Beta_shape_Data', horse_id)

    os.makedirs(output_dir, exist_ok=True)

    npz_files = sorted(glob.glob(os.path.join(input_dir, '*_hsmal.npz')))

    if not npz_files:
        print(f"No npz files found in {input_dir}")
        return

    for npz_path in npz_files:
        npz = np.load(npz_path, allow_pickle=True)
        betas = npz['betas']  # shape: (10,)
        df = pd.DataFrame([betas], columns=[f'beta_{i}' for i in range(len(betas))])

        npz_base = os.path.splitext(os.path.basename(npz_path))[0]
        csv_filename = f"{npz_base}_betas.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Saved: {csv_path}")

if __name__ == '__main__':
    main() 