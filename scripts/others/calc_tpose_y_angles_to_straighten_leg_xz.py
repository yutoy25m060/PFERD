"""
このスクリプトは、hSMALモデルのテンプレートポーズ（Tポーズ）から、
脚の各関節がxz平面で直線状になるようにするためのy軸回転角度を計算するものです。

【プロンプト】
以下のスクリプトを作成したいです。どのようなスクリプトにすれば確実に要件が満たせるかわからないので相談したいです。
動機：hSMALモデルのテンプレートポーズ（Tポーズ）はある立脚姿勢の時の関節角度を0度としている。この姿勢から脚が鉛直方向にまっすぐ伸ばした状態の関節角度を知りたい。

やりたい事（大まか）
各ジョイントのxyz空間における座標を取得する。
y座標を考慮しないxz平面において2つのジョイントを結ぶ直線が他の直線と平行になる角度を探す。
例：18番と19番のジョイントを結ぶ直線と19番と20番を結ぶ直線が平衡になるように19番のy軸回転角度を変更する。

もしかしたら二直線のなす角を求めて3つのジョイントが直線に並ぶ方の角度を求めることでも出来るかも？
この角度はジョイントの親子構造に準じて順番に行っていく。
脚部の基準ジョイント（4, 9, 18, 23）を元に子ジョンとの角度を求めていく



【注意】
このスクリプトは未完成
CSV: JOINT_MODEL_DATA/T_Pose_Straight_Leg_Angles/<ID>_tpose_y_to_straight_xz_保存版.csvに一応保存しておく
4_tpose_y_to_straight_xz_修正版.csvには手動で角度を修正したものを保存しておく

-----4,9番ジョイントが親ジョイントとの角度がロボットようになっていないので修正したい


【目的】
- Tポーズ基準（全関節0度）から、脚の各中間関節が「xz平面で直線状（親-子が一直線）」になるように、
  各関節の「y軸回転角（yaw）」を算出する

【基本アイデア】
- Tポーズの各ジョイント座標を取得
- xz平面に射影して計算（y成分は無視）
- 中間関節jについて、親pと子cを結ぶベクトルv1, v2が直線状になる角度を計算
- 必要角度: theta = signed_angle_xz(v2, -v1)（degree）

【脚の連鎖構造】
- 前脚: 4(l_shoulder), 9(r_shoulder)
- 後脚: 18(l_hip), 23(r_hip)
- 各脚チェーン（parents_hsmal36.csv準拠）:
  - 左前脚: 4→5→6→7→8（中間: 5,6,7）
  - 右前脚: 9→10→11→12→13（中間: 10,11,12）
  - 左後脚: 18→19→20→21→22（中間: 19,20,21）
  - 右後脚: 23→24→25→26→27（中間: 24,25,26）

【出力】
- CSV: JOINT_MODEL_DATA/T_Pose_Straight_Leg_Angles/<ID>_tpose_y_to_straight_xz.csv
- 列: joint_index,joint_name,parent,child,theta_y_deg_to_straight_xz,|v1|,|v2|

【使い方】
- set PYTHONPATH=.
- python scripts/others/calc_tpose_y_angles_to_straighten_leg_xz.py
"""

import CONFIG
import numpy as np
import os
import csv
import torch
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

def get_tpose_joints(model_path, device, num_betas=10):
    """Tポーズのジョイント座標を取得"""
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
    
    return joints

def proj_xz(vector):
    """ベクトルをxz平面に射影（y成分を0にする）"""
    return np.array([vector[0], 0, vector[2]])

def signed_angle_xz(v1, v2):
    """xz平面での2つのベクトルの有向角度を計算（degree）"""
    # ベクトルの長さをチェック
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    # 正規化
    v1_norm = v1 / norm_v1
    v2_norm = v2 / norm_v2
    
    # 内積から角度を計算
    dot_product = np.dot(v1_norm, v2_norm)
    dot_product = np.clip(dot_product, -1.0, 1.0)  # 数値誤差対策
    angle_rad = np.arccos(dot_product)
    
    # 外積のz成分で符号を決定（右手系）
    cross_z = np.cross(v1_norm, v2_norm)[1]  # y成分（xz平面ではy軸が上）
    
    if cross_z < 0:
        angle_rad = -angle_rad
    
    return np.degrees(angle_rad)

def calculate_leg_straightening_angles(joints, parents, joint_names):
    """脚を直線状にするためのy軸回転角度を計算"""
    
    # 脚の基準ジョイントとチェーン定義
    leg_chains = {
        # 左前脚: 4(l_shoulder) → 5 → 6 → 7 → 8
        'left_front': {'root': 4, 'chain': [4, 5, 6, 7, 8]},
        # 右前脚: 9(r_shoulder) → 10 → 11 → 12 → 13
        'right_front': {'root': 9, 'chain': [9, 10, 11, 12, 13]},
        # 左後脚: 18(l_hip) → 19 → 20 → 21 → 22
        'left_hind': {'root': 18, 'chain': [18, 19, 20, 21, 22]},
        # 右後脚: 23(r_hip) → 24 → 25 → 26 → 27
        'right_hind': {'root': 23, 'chain': [23, 24, 25, 26, 27]}
    }
    
    results = []
    
    for leg_name, leg_info in leg_chains.items():
        print(f"  {leg_name}脚の計算中...")
        chain = leg_info['chain']
        
        # 各中間関節について角度を計算
        for i in range(1, len(chain) - 1):  # 最初と最後以外（中間関節）
            j = chain[i]  # 中間関節
            p = chain[i-1]  # 親関節
            c = chain[i+1]  # 子関節
            
            # ベクトルを計算
            v1 = joints[j] - joints[p]  # 親から中間
            v2 = joints[c] - joints[j]  # 中間から子
            
            # xz平面に射影
            v1_xz = proj_xz(v1)
            v2_xz = proj_xz(v2)
            
            # 直線状にする角度を計算（v2を-v1に一致させる）
            angle_to_straight = signed_angle_xz(v2_xz, -v1_xz)
            
            # ベクトルの長さ
            norm_v1 = np.linalg.norm(v1_xz)
            norm_v2 = np.linalg.norm(v2_xz)
            
            result = {
                'joint_index': j,
                'joint_name': joint_names[j],
                'parent': joint_names[p],
                'child': joint_names[c],
                'theta_y_deg_to_straight_xz': angle_to_straight,
                'v1_magnitude': norm_v1,
                'v2_magnitude': norm_v2
            }
            
            results.append(result)
            
            print(f"    関節{j}({joint_names[j]}): {angle_to_straight:.2f}度")
    
    return results

def save_results_to_csv(results, output_path):
    """結果をCSVファイルに保存"""
    if not results:
        print("  保存する結果がありません")
        return
    
    # 出力ディレクトリの作成
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # CSVファイルとして保存
    fieldnames = ['joint_index', 'joint_name', 'parent', 'child', 
                  'theta_y_deg_to_straight_xz', 'v1_magnitude', 'v2_magnitude']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"  結果を保存しました: {output_path}")

def main(ID=4, num_betas=10):
    """メイン処理"""
    print("hSMALモデルのTポーズから脚を直線状にする角度計算を開始します")
    
    # パス設定
    model_path = os.path.join('hSMALdata', 'my_smpl_0000_horse_new_skeleton_horse.pkl')
    parents_csv = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', f'ID_{ID}', 'parents_hsmal36.csv')
    output_path = os.path.join('JOINT_MODEL_DATA', 'T_Pose_Straight_Leg_Angles', 
                              f'{ID}_tpose_y_to_straight_xz.csv')
    
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
    
    print("2. Tポーズのジョイント座標を取得中...")
    joints = get_tpose_joints(model_path, CONFIG.DEVICE, num_betas)
    print(f"   ジョイント座標の形状: {joints.shape}")
    
    print("3. 脚を直線状にする角度を計算中...")
    results = calculate_leg_straightening_angles(joints, parents, joint_names)
    
    print("4. 結果をCSVファイルに保存中...")
    save_results_to_csv(results, output_path)
    
    print("5. 計算結果のサマリー:")
    for result in results:
        print(f"   関節{result['joint_index']}({result['joint_name']}): "
              f"{result['theta_y_deg_to_straight_xz']:.2f}度 "
              f"(親: {result['parent']} → 子: {result['child']})")
    
    print("\n完了！脚をxz平面で直線状にするためのy軸回転角度を計算しました。")
    print("この角度を各関節に適用することで、脚が鉛直方向にまっすぐ伸びた状態になります。")

def parse_arguments():
    """コマンドライン引数の解析"""
    import argparse
    parser = argparse.ArgumentParser(description='hSMALモデルのTポーズから脚を直線状にする角度を計算')
    parser.add_argument("--ID", type=int, default=4, help='対象馬ID（デフォルト: 4）')
    parser.add_argument("--num_betas", type=int, default=10, help='体型パラメータ数（デフォルト: 10）')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    try:
        main(ID=args.ID, num_betas=args.num_betas)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()