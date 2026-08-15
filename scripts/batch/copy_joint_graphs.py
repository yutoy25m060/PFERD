"""
このスクリプトは、
- create_xyz_absolute_angle_graphs.py
- create_xyz_angle_graphs.py
- create_leg_joint_angle_graphs.py
で出力されたグラフ画像（png）をまとめて新しいディレクトリにコピーします。

コピー元:
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/graphs/
- JOINT_MODEL_DATA/Angle_xyz_Degree_from_poses/ID_4/graphs/
- JOINT_MODEL_DATA/Leg_Joint_Angles/ID_4/graphs/

コピー先:
- JOINT_MODEL_DATA/Selected_Joint_Graphs/ID_4/<分類名>/（元のサブディレクトリ構造を維持）

【注意】
このスクリプトは update_joint_model_data.py のパイプラインには含まれていません。
コピー先は plot_joint_angle_comparison.py の出力先と同じディレクトリなので、
パイプライン実行後にこれを走らせると2種類のグラフが同じ場所に混在します。
単体で使う場合のみ実行してください。

【使い方】
python scripts/batch/copy_joint_graphs.py
"""
import os
import shutil
import glob

from scripts.utils.cli import LEG_JOINT_INDICES, parse_horse_id

# コピー元とコピー先のディレクトリ
horse_id = parse_horse_id('各種グラフ画像を1箇所にまとめてコピーする')
sources = [
    (os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id, 'graphs'), 'Absolute_Angles'),
    (os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Degree_from_poses', horse_id, 'graphs'), 'Angle_xyz_Degree_from_poses'),
    (os.path.join('JOINT_MODEL_DATA', 'Leg_Joint_Angles', horse_id, 'graphs'), 'Leg_Joint_Angles'),
]
dest_base = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id)

# コピーしたいジョイント番号リスト（脚部20ジョイント）
copy_joint_indices = LEG_JOINT_INDICES
copy_joint_strs = [f'joint{idx}' for idx in copy_joint_indices]

for src, category in sources:
    if not os.path.exists(src):
        print(f'コピー元が存在しません: {src}')
        continue
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        # jointXX ディレクトリ or ファイル名にjointXXが含まれる場合のみコピー
        if not any(joint in rel_root for joint in copy_joint_strs) and not any(any(joint in f for joint in copy_joint_strs) for f in files):
            continue
        dest_dir = os.path.join(dest_base, category, rel_root)
        os.makedirs(dest_dir, exist_ok=True)
        for file in files:
            if file.endswith('.png') and any(joint in file for joint in copy_joint_strs):
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                shutil.copy2(src_file, dest_file)
                print(f'コピー: {src_file} → {dest_file}') 