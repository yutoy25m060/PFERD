"""
# ジョイント角度サマリー画像自動生成スクリプト（ゼロベース再実装）
#
# 指定した馬体ID（horse_id）に対応する
# JOINT_MODEL_DATA/Selected_Joint_Graphs/{horse_id}/配下の
# Absolute_Angles および Angle_xyz_Degree_from_poses ディレクトリから
# 各計測データ・各ジョイント・各軸（x, y, z）の角度グラフ画像（smooth, scatter）を探索し、
# それらを左右に並べたサマリー画像を自動生成します。
#
# - 画像が存在しない場合は白画像で補完します。
# - サマリー画像は summary ディレクトリに保存されます。
# - ファイル名: Joint {joint番号}_{Joint名}_{axis}_summary_{mode}.png
#
# 【重要】サマリー画像の左右の意味：
#   左側：絶対角度（Absolute_Angles）
#   右側：相対角度（Angle_xyz_Degree_from_poses）
"""
import os
import sys
import glob
import re
from PIL import Image

# 設定
horse_id = 'ID_4'
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..', 'JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id))
abs_dir = os.path.join(base_dir, 'Absolute_Angles')
xyz_dir = os.path.join(base_dir, 'Angle_xyz_Degree_from_poses')
summary_dir = os.path.join(base_dir, 'summary')
os.makedirs(summary_dir, exist_ok=True)

axes = ['x', 'y', 'z']
modes = ['smooth', 'scatter']
def_img_size = (600, 400)

def get_img_size(img_path, default=def_img_size):
    if img_path and os.path.exists(img_path):
        with Image.open(img_path) as img:
            return img.size
    return default

def create_white_img(size):
    return Image.new('RGB', size, (255, 255, 255))

def extract_key(dirname):
    m = re.match(r'^(\d{8}_ID_\d+_\d+)', dirname)
    return m.group(1) if m else None

# 計測データディレクトリのペアリング
for d in (abs_dir, xyz_dir):
    if not os.path.isdir(d):
        print(f'入力ディレクトリが見つかりません: {d}')
        print('先に plot_joint_angle_comparison.py を実行してください。')
        sys.exit(0)

abs_data_dirs = [d for d in os.listdir(abs_dir) if os.path.isdir(os.path.join(abs_dir, d))]
xyz_data_dirs = [d for d in os.listdir(xyz_dir) if os.path.isdir(os.path.join(xyz_dir, d))]
abs_map = {}
for d in abs_data_dirs:
    key = extract_key(d)
    if key:
        abs_map[key] = d
xyz_map = {}
for d in xyz_data_dirs:
    key = extract_key(d)
    if key:
        xyz_map[key] = d
common_keys = sorted(set(abs_map.keys()) & set(xyz_map.keys()))
print(f'検出計測データ数: {len(common_keys)}')
if not common_keys:
    print('警告: 共通の計測データディレクトリが見つかりません。')

total = 0
for data_key in common_keys:
    abs_data_dir = os.path.join(abs_dir, abs_map[data_key])
    xyz_data_dir = os.path.join(xyz_dir, xyz_map[data_key])
    # jointディレクトリ名のリストを取得
    abs_joint_dirs = [d for d in os.listdir(abs_data_dir) if os.path.isdir(os.path.join(abs_data_dir, d))]
    xyz_joint_dirs = [d for d in os.listdir(xyz_data_dir) if os.path.isdir(os.path.join(xyz_data_dir, d))]
    joint_names = sorted(set(abs_joint_dirs) & set(xyz_joint_dirs))
    print(f'[{data_key}] 検出ジョイント数: {len(joint_names)}')
    for joint in joint_names:
        abs_joint_dir = os.path.join(abs_data_dir, joint)
        xyz_joint_dir = os.path.join(xyz_data_dir, joint)
        # 保存先ディレクトリを作成
        save_dir = os.path.join(summary_dir, data_key, joint)
        os.makedirs(save_dir, exist_ok=True)
        for axis in axes:
            for mode in modes:
                abs_img_files = glob.glob(os.path.join(abs_joint_dir, f'{joint}_*_{axis}_{mode}.png'))
                xyz_img_files = glob.glob(os.path.join(xyz_joint_dir, f'{joint}_*_{axis}_{mode}.png'))
                abs_img_path = abs_img_files[0] if abs_img_files else None
                xyz_img_path = xyz_img_files[0] if xyz_img_files else None
                size = get_img_size(abs_img_path) if abs_img_path else get_img_size(xyz_img_path)
                if not size:
                    size = def_img_size
                abs_img = Image.open(abs_img_path) if abs_img_path and os.path.exists(abs_img_path) else create_white_img(size)
                xyz_img = Image.open(xyz_img_path) if xyz_img_path and os.path.exists(xyz_img_path) else create_white_img(size)
                summary_img = Image.new('RGB', (size[0]*2, size[1]), (255, 255, 255))
                summary_img.paste(abs_img, (0, 0))
                summary_img.paste(xyz_img, (size[0], 0))
                # joint名分割
                joint_parts = joint.split('_', 2)
                if len(joint_parts) >= 3:
                    joint_number = joint_parts[0] + '_' + joint_parts[1]
                    joint_name = joint_parts[2]
                else:
                    joint_number = joint
                    joint_name = ''
                if joint_name:
                    save_name = f'{joint_number}_{joint_name}_{axis}_summary_{mode}.png'
                else:
                    save_name = f'{joint_number}_{axis}_summary_{mode}.png'
                save_path = os.path.join(save_dir, save_name)
                summary_img.save(save_path)
                print(f'保存: {save_path}')
                total += 1
if total == 0:
    print('警告: 1枚もサマリー画像が生成されませんでした。')
else:
    print(f'完了: {total} 枚のサマリー画像を生成しました。') 