r"""
Y軸の角度オフセットを加算するスクリプト

Angle_Y_Degree_from_poses/ID_4 の各CSVファイルに対し、指定したjoint番号にオフセット値を加算し、
Angle_Y_Degree_from_poses/ID_4_offset に新規保存するスクリプト。

【スクリプト説明】
Angle_Y_Degree_from_poses/ID_4 の各CSVファイルに対し、指定したjoint番号にオフセット値を加算し、
Angle_Y_Degree_from_poses/ID_4_offset に新規保存するスクリプトです。

【用途】
- 指定した関節(joint)の角度データに任意のオフセット値を加えた新しいCSVファイルを作成します。
- 元のファイルは変更せず、新しいディレクトリに保存します。

【実行例（Windowsコマンドプロンプト）】
cd /d C:\Users\Yuto\github_repositories\PFERD\PFERD
set PYTHONPATH=.
python scripts/offset_tools/Angle_Y_Degree_add_joint_angle_offset.py

【オフセット設定】
脚の根本関節（Viwerで手動で確認）
18, 23, 4, 9
4, 9:  -20度 前脚
18, 23:  2度 後脚


参考文献
JOINT_MODEL_DATA\T_Pose_Straight_Leg_Angles
四捨五入前
5: 12.2463861
6: 0.898286309
7: 23.16685571
10: 12.2463861
11: 0.898286309
12: 23.16685571
19: -36.19341811
20: 29.25174381
21: 26.60145232
24: -36.19341811
25: 29.25174381
26: 26.60145232

オフセットするときは符号が逆になるので注意
r"""

import os
import pandas as pd


# 1. オフセット設定（joint番号: オフセット値）
JOINT_OFFSETS = {
    #5: 10.0,   # 例: joint番号5に+10度
    #12: -5.0,  # 例: joint番号12に-5度
    # 必要に応じて追加
    #オフセットするときは符号が逆になるので注意

    4: 20.0,
    5: -12.2,
    6: -0.9,
    7: -23.2,
    9: 20.0,
    10: -12.2,
    11: -0.9,
    12: -23.2,
    18: -2.0,
    19: 36.2,
    20: -29.3,
    21: -26.6,
    23: -2.0,
    24: 36.2,
    25: -29.3,
    26: -26.6
}

SRC_DIR = os.path.join('JOINT_MODEL_DATA', 'Angle_Y_Degree_from_poses', 'ID_4')
DST_DIR = os.path.join('JOINT_MODEL_DATA', 'Angle_Y_Degree_from_poses', 'ID_4_offset')
os.makedirs(DST_DIR, exist_ok=True)

for fname in os.listdir(SRC_DIR):
    if not fname.endswith('.csv'):
        continue
    src_path = os.path.join(SRC_DIR, fname)
    base, ext = os.path.splitext(fname)
    dst_fname = base + '_offset' + ext
    dst_path = os.path.join(DST_DIR, dst_fname)
    df = pd.read_csv(src_path)

    # joint_index列が無い場合はjointX_...列形式として処理
    updated = False
    for joint_idx, offset in JOINT_OFFSETS.items():
        # 列名例: joint4_l_shoulder_y [deg]
        col_candidates = [col for col in df.columns if col.startswith(f"joint{joint_idx}_")]
        for col in col_candidates:
            df[col] = df[col] + offset
            updated = True

    if updated:
        df.to_csv(dst_path, index=False)
        print(f"保存: {dst_path}")
    else:
        print(f"スキップ: {fname} (該当joint列がありません)")
