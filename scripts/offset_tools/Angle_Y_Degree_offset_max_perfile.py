"""
【スクリプト説明】
JOINT_MODEL_DATA/Angle_Y_Degree_from_poses/ID_4_offset 内の各CSVファイルごとに、
各joint列の「最大値（max）」と「最小値（min）」を集計し、
JOINT_MODEL_DATA/Angle_Y_Degree_from_poses/ID_4_offset_max フォルダに同名で保存します。

【使い方（Windowsコマンドプロンプト例）】
cd /d C:\Users\Yuto\github_repositories\PFERD\PFERD
set PYTHONPATH=.
python scripts/offset_tools/Angle_Y_Degree_offset_max_perfile.py
"""
import os
import pandas as pd

SRC_DIR = os.path.join('JOINT_MODEL_DATA', 'Angle_Y_Degree_from_poses', 'ID_4_offset')
DST_DIR = os.path.join('JOINT_MODEL_DATA', 'Angle_Y_Degree_from_poses', 'ID_4_offset_max')
os.makedirs(DST_DIR, exist_ok=True)

for fname in os.listdir(SRC_DIR):
    if not fname.endswith('.csv'):
        continue
    src_path = os.path.join(SRC_DIR, fname)
    base, ext = os.path.splitext(fname)
    dst_fname = base + '_max' + ext
    dst_path = os.path.join(DST_DIR, dst_fname)
    df = pd.read_csv(src_path)

    # joint列のみ抽出（frame列など除外）
    joint_cols = [col for col in df.columns if col.startswith('joint')]
    result = []
    for col in joint_cols:
        vals = df[col].dropna()
        max_val = vals.max() if not vals.empty else None
        min_val = vals.min() if not vals.empty else None
        result.append({'joint': col, 'max': max_val, 'min': min_val})
    out_df = pd.DataFrame(result)
    out_df_T = out_df.set_index('joint').T
    out_df_T.to_csv(dst_path)
    print(f"保存: {dst_path}")
