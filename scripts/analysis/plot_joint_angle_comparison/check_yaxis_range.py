import os
import re
import sys

# 設定
horse_id = 'ID_4'
abs_sel_dir = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id, 'Absolute_Angles')
xyz_sel_dir = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id, 'Angle_xyz_Degree_from_poses')

# サブディレクトリ名のリストを取得
def extract_key(dirname):
    # 測定日時_ID_ID番号_測定データ番号 の部分を抽出
    m = re.match(r'^(\d{8}_ID_\d+_\d+)', dirname)
    return m.group(1) if m else None

for d in (abs_sel_dir, xyz_sel_dir):
    if not os.path.isdir(d):
        print(f'入力ディレクトリが見つかりません: {d}')
        print('先に plot_joint_angle_comparison.py を実行してください。')
        sys.exit(0)

abs_subdirs = sorted([d for d in os.listdir(abs_sel_dir) if os.path.isdir(os.path.join(abs_sel_dir, d))])
xyz_subdirs = sorted([d for d in os.listdir(xyz_sel_dir) if os.path.isdir(os.path.join(xyz_sel_dir, d))])

# キー（測定日時_ID_ID番号_測定データ番号）でマッピング
abs_map = {}
for d in abs_subdirs:
    key = extract_key(d)
    if key:
        abs_map[key] = d
xyz_map = {}
for d in xyz_subdirs:
    key = extract_key(d)
    if key:
        xyz_map[key] = d

common_keys = sorted(set(abs_map.keys()) & set(xyz_map.keys()))

if not common_keys:
    print('対応するサブディレクトリペアが見つかりません')
    exit()

all_ok = True
for key in common_keys:
    print(f'--- サブディレクトリ: {key} を処理中 ---')
    abs_dir = os.path.join(abs_sel_dir, abs_map[key])
    xyz_dir = os.path.join(xyz_sel_dir, xyz_map[key])
    # jointサブディレクトリ
    abs_joints = sorted([d for d in os.listdir(abs_dir) if os.path.isdir(os.path.join(abs_dir, d))])
    xyz_joints = sorted([d for d in os.listdir(xyz_dir) if os.path.isdir(os.path.join(xyz_dir, d))])
    joint_keys = sorted(set(abs_joints) & set(xyz_joints))
    for joint in joint_keys:
        print(f'  - ジョイント: {joint} を処理中')
        abs_joint_dir = os.path.join(abs_dir, joint)
        xyz_joint_dir = os.path.join(xyz_dir, joint)
        # yaxisファイルを列挙
        abs_yaxis_files = sorted([f for f in os.listdir(abs_joint_dir) if f.endswith('_yaxis.txt')])
        xyz_yaxis_files = sorted([f for f in os.listdir(xyz_joint_dir) if f.endswith('_yaxis.txt')])
        axis_keys = sorted(set(abs_yaxis_files) & set(xyz_yaxis_files))
        for axis_file in axis_keys:
            print(f'    * ファイル: {axis_file} を比較中')
            abs_path = os.path.join(abs_joint_dir, axis_file)
            xyz_path = os.path.join(xyz_joint_dir, axis_file)
            with open(abs_path, 'r', encoding='utf-8') as f:
                abs_yaxis = f.read().strip()
            with open(xyz_path, 'r', encoding='utf-8') as f:
                xyz_yaxis = f.read().strip()
            if abs_yaxis == xyz_yaxis:
                print(f'OK: {key}/{joint}/{axis_file} → y軸範囲一致 ({abs_yaxis})')
            else:
                print(f'NG: {key}/{joint}/{axis_file} → 不一致! Absolute={abs_yaxis}, Angle_xyz={xyz_yaxis}')
                all_ok = False
if all_ok:
    print('\n全てのy軸範囲が一致しています。')
else:
    print('\n一部にy軸範囲の不一致があります。') 