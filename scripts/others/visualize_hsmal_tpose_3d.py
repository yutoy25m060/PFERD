"""
このスクリプトは、hSMALモデルのテンプレートポーズ（Tポーズ）を3Dビューワーで可視化するためのものです。
Load_Visualization.pyと同様のaitviewerを使用し、Tポーズにおける各関節の位置と軸方向を視覚的に確認できます。

【注意】
Windows環境や一部の環境では、OpenMPの競合エラー回避のため、
実行前に以下のコマンドで環境変数を設定してください：
    set KMP_DUPLICATE_LIB_OK=TRUE
    python scripts/others/visualize_hsmal_tpose_3d.py

【入力ファイル】
- hSMALモデル: hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl
- 親子構造情報: JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv

【出力】
- 3DビューワーによるTポーズ可視化（ファイル出力はなし）
- 各関節の位置と軸方向の表示
- スケルトン構造の可視化

【使い方】
Tポーズのみ (デフォルト)
- set KMP_DUPLICATE_LIB_OK=TRUE
- python scripts/others/visualize_hsmal_tpose_3d.py

Tポーズ + 脚を直線状にした結果 (オプション) 
- set KMP_DUPLICATE_LIB_OK=TRUE
- python scripts/others/visualize_hsmal_tpose_3d.py --show_straight_legs
""" 

import CONFIG
import numpy as np
import os
import csv
import torch
from aitviewer.renderables.smpl import SMPLSequence
from aitviewer.viewer import Viewer
from aitviewer.renderables.spheres import Spheres
from aitviewer.renderables.lines import Lines
from utils.smal import SMALLayer, HSMAL

def load_parents_and_names(parents_csv):
    """親子関係とジョイント名を読み込み"""
    parents = []
    joint_names = []
    
    with open(parents_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            parents.append(int(row['parent_index']))
            joint_names.append(row['joint_name'])
    
    return parents, joint_names

def get_tpose_joints_and_axes(model_path, device, parents, num_betas=10):
    """Tポーズのジョイント座標と軸方向を取得"""
    smal_layer = SMALLayer(
        model_path=model_path,
        model_cls=HSMAL,
        device=device,
        num_betas=num_betas,
    )
    
    # Tポーズ（全パラメータ0）
    batch_size = 1
    poses_body = np.zeros((batch_size, HSMAL.NUM_BODY_JOINTS * 3), dtype=np.float32)
    betas = np.zeros((batch_size, num_betas), dtype=np.float32)
    trans = np.zeros((batch_size, 3), dtype=np.float32)
    poses_root = np.zeros((batch_size, 3), dtype=np.float32)
    
    # モデルからジョイント座標を取得
    # SMALLayerから直接取得（より確実）
    print("   SMALLayerから直接ジョイント座標を取得中...")
    with torch.no_grad():
        output = smal_layer.bm(
            betas=torch.tensor(betas, dtype=torch.float32, device=device),
            body_pose=torch.tensor(poses_body, dtype=torch.float32, device=device),
            global_orient=torch.tensor(poses_root, dtype=torch.float32, device=device),
            transl=torch.tensor(trans, dtype=torch.float32, device=device),
            return_full_pose=True
        )
        joints = output.joints[0].cpu().numpy()  # (N, 3)
    
    # 各ジョイントの軸方向を計算（Tポーズではローカル軸がそのまま）
    # 親ジョイントからの相対的な軸方向を計算
    joint_axes = []
    for i in range(len(joints)):
        if i == 0:  # pelvis（ルート）
            # ワールド座標系の軸
            x_axis = np.array([1, 0, 0])  # 右方向
            y_axis = np.array([0, 1, 0])  # 上方向
            z_axis = np.array([0, 0, 1])  # 前方向
        else:
            # 親ジョイントからの相対的な軸方向
            parent_idx = parents[i]
            if parent_idx != -1:
                # 親から子への方向ベクトル
                direction = joints[i] - joints[parent_idx]
                direction = direction / np.linalg.norm(direction)
                
                # 垂直な軸を計算
                up = np.array([0, 1, 0])  # Y軸上向き
                right = np.cross(direction, up)
                right = right / np.linalg.norm(right)
                forward = np.cross(right, direction)
                
                x_axis = right
                y_axis = direction
                z_axis = forward
            else:
                x_axis = np.array([1, 0, 0])
                y_axis = np.array([0, 1, 0])
                z_axis = np.array([0, 0, 1])
        
        joint_axes.append({
            'x': x_axis,
            'y': y_axis,
            'z': z_axis
        })
    
    return joints, joint_axes

def load_straight_leg_angles(ID):
    """脚を直線状にする角度を読み込み"""
    angles_path = os.path.join('JOINT_MODEL_DATA', 'T_Pose_Straight_Leg_Angles', 
                               f'{ID}_tpose_y_to_straight_xz.csv')
    
    if not os.path.exists(angles_path):
        print(f"   警告: 角度ファイルが見つかりません: {angles_path}")
        print("   先にcalc_tpose_y_angles_to_straighten_leg_xz.pyを実行してください")
        return None
    
    angles_dict = {}
    with open(angles_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            joint_idx = int(row['joint_index'])
            angle = float(row['theta_y_deg_to_straight_xz'])
            angles_dict[joint_idx] = angle
    
    print(f"   {len(angles_dict)}個の関節角度を読み込みました")
    return angles_dict

def create_straight_legs_sequence(model_path, joints, parents, joint_names, num_betas):
    """脚を直線状にしたFK結果を生成"""
    try:
        # 角度ファイルを読み込み
        ID = 4  # デフォルトID（必要に応じて修正）
        angles_dict = load_straight_leg_angles(ID)
        if not angles_dict:
            return None
        
        # SMALLayerを初期化
        smal_layer = SMALLayer(
            model_path=model_path,
            model_cls=HSMAL,
            device=CONFIG.DEVICE,
            num_betas=num_betas,
        )
        
        # Tポーズのパラメータ（全0）
        batch_size = 1
        poses_body = np.zeros((batch_size, HSMAL.NUM_BODY_JOINTS * 3), dtype=np.float32)
        betas = np.zeros((batch_size, num_betas), dtype=np.float32)
        trans = np.zeros((batch_size, 3), dtype=np.float32)
        poses_root = np.zeros((batch_size, 3), dtype=np.float32)
        
        # 脚の関節に角度を適用
        for joint_idx, angle_deg in angles_dict.items():
            if joint_idx < HSMAL.NUM_BODY_JOINTS:
                # 角度をラジアンに変換
                angle_rad = np.radians(angle_deg)
                
                # y軸回転（Y軸周りの回転）
                # hSMALの関節順序に注意（0ベースインデックス）
                joint_offset = (joint_idx - 1) * 3  # ルート関節（pelvis）は除く
                if joint_offset >= 0:
                    poses_body[0, joint_offset + 1] = angle_rad  # Y軸回転
        
        # FKを実行
        with torch.no_grad():
            output = smal_layer.bm(
                betas=torch.tensor(betas, dtype=torch.float32, device=CONFIG.DEVICE),
                body_pose=torch.tensor(poses_body, dtype=torch.float32, device=CONFIG.DEVICE),
                global_orient=torch.tensor(poses_root, dtype=torch.float32, device=CONFIG.DEVICE),
                transl=torch.tensor(trans, dtype=torch.float32, device=CONFIG.DEVICE),
                return_full_pose=True
            )
        
        # SMPLSequenceとして作成
        straight_legs_seq = SMPLSequence(
            poses_body=poses_body,
            smpl_layer=smal_layer,
            poses_root=poses_root,
            betas=betas,
            trans=trans,
            device=CONFIG.DEVICE,
            color=(100/255, 255/255, 100/255, 0.6),  # 緑色（半透明）
            z_up=True,
            enabled_frames=np.array([True], dtype=bool)
        )
        
        # メッシュのアウトラインを表示
        straight_legs_seq.mesh_seq.draw_outline = True
        straight_legs_seq.skeleton_seq.enabled = True
        
        return straight_legs_seq
        
    except Exception as e:
        print(f"   エラー: 脚を直線状にしたFK結果の生成に失敗: {e}")
        return None

def visualize_tpose_3d(ID=4, num_betas=10, show_straight_legs=False):
    """Tポーズを3Dビューワーで可視化"""
    # パス設定
    model_path = os.path.join('hSMALdata', 'my_smpl_0000_horse_new_skeleton_horse.pkl')
    parents_csv = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', f'ID_{ID}', 'parents_hsmal36.csv')
    
    # ファイル存在確認
    if not os.path.exists(model_path):
        print(f"エラー: モデルファイルが見つかりません: {model_path}")
        return
    
    if not os.path.exists(parents_csv):
        print(f"エラー: 親子構造ファイルが見つかりません: {parents_csv}")
        return
    
    print("1. 親子構造とジョイント名の読み込み中...")
    parents, joint_names = load_parents_and_names(parents_csv)
    print(f"   ジョイント数: {len(joint_names)}")
    
    print("2. Tポーズのジョイント座標と軸方向を計算中...")
    joints, joint_axes = get_tpose_joints_and_axes(model_path, CONFIG.DEVICE, parents, num_betas)
    print(f"   ジョイント座標の形状: {joints.shape}")
    
    print("3. 3Dビューワーの初期化中...")
    v = Viewer()
    v.scene.camera.position = (0, 3, 15)
    v.playback_fps = 30
    
    # hSMALモデルのTポーズを表示
    print("4. hSMALモデルのTポーズを表示中...")
    smal_layer = SMALLayer(
        model_path=model_path,
        model_cls=HSMAL,
        device=CONFIG.DEVICE,
        num_betas=num_betas,
    )
    
    # Tポーズのパラメータ
    poses_body = np.zeros((1, HSMAL.NUM_BODY_JOINTS * 3), dtype=np.float32)
    betas = np.zeros((1, num_betas), dtype=np.float32)
    trans = np.zeros((1, 3), dtype=np.float32)
    poses_root = np.zeros((1, 3), dtype=np.float32)
    
    smal_seq = SMPLSequence(
        poses_body=poses_body,
        smpl_layer=smal_layer,
        poses_root=poses_root,
        betas=betas,
        trans=trans,
        device=CONFIG.DEVICE,
        color=(149/255, 149/255, 149/255, 0.8),
        z_up=True,
        enabled_frames=np.array([True], dtype=bool)
    )
    
    # メッシュのアウトラインを表示
    smal_seq.mesh_seq.draw_outline = True
    smal_seq.skeleton_seq.enabled = True  # スケルトンを有効化
    
    v.scene.add(smal_seq)
    
    # 各ジョイントの位置を球で表示
    print("5. 各ジョイントの位置を表示中...")
    # jointsの形状を確認
    if len(joints.shape) == 2:
        # 単一フレームの場合、次元を追加
        joints_expanded = joints[np.newaxis, :, :]  # (1, N, 3)
        print(f"   ジョイント座標を(1, N, 3)に拡張: {joints_expanded.shape}")
    else:
        joints_expanded = joints
    
    joint_spheres = Spheres(
        joints_expanded,
        color=(255/255, 100/255, 100/255, 0.8),
        radius=0.1,
        enabled_frames=np.array([True] * joints_expanded.shape[0], dtype=bool)
    )
    v.scene.add(joint_spheres)
    
    # 親子関係を線で表示
    print("6. 親子関係（スケルトン）を表示中...")
    skeleton_lines = []
    for i, parent in enumerate(parents):
        if parent != -1:
            start_point = joints[parent]
            end_point = joints[i]
            skeleton_lines.append([start_point, end_point])
    
    if skeleton_lines:
        skeleton_lines = np.array(skeleton_lines)
        print(f"   スケルトンラインの形状: {skeleton_lines.shape}")
        # enabled_framesの長さをスケルトンラインのフレーム数に合わせる
        n_frames = skeleton_lines.shape[0]
        skeleton_renderable = Lines(
            skeleton_lines,
            color=(100/255, 100/255, 255/255, 0.8),
            enabled_frames=np.array([True] * n_frames, dtype=bool)
        )
        v.scene.add(skeleton_renderable)
    
    # 各ジョイントの軸方向を表示（オプション）
    print("7. ジョイント軸方向の表示準備完了")
    print("   軸の表示/非表示は、ビューワー内で右クリックメニューから制御できます")
    
    # 脚を直線状にしたFK結果を重ね描画（オプション）
    if show_straight_legs:
        print("8. 脚を直線状にしたFK結果を計算・表示中...")
        straight_legs_seq = create_straight_legs_sequence(model_path, joints, parents, joint_names, num_betas)
        if straight_legs_seq:
            v.scene.add(straight_legs_seq)
            print("   脚を直線状にしたモデルを追加しました（緑色）")
    
    print("9. 3Dビューワーを起動中...")
    print("   - マウス左ドラッグ: 回転")
    print("   - マウス右ドラッグ: パン")
    print("   - マウスホイール: ズーム")
    print("   - 右クリック: メニュー")
    
    v.run()

def parse_arguments():
    """コマンドライン引数の解析"""
    import argparse
    parser = argparse.ArgumentParser(description='hSMALモデルのTポーズを3Dビューワーで可視化')
    parser.add_argument("--ID", type=int, default=4, help='対象馬ID（デフォルト: 4）')
    parser.add_argument("--num_betas", type=int, default=10, help='体型パラメータ数（デフォルト: 10）')
    parser.add_argument("--show_straight_legs", action='store_true', 
                       help='脚を直線状にしたFK結果も重ね描画する')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    try:
        visualize_tpose_3d(ID=args.ID, num_betas=args.num_betas, 
                          show_straight_legs=args.show_straight_legs)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
