"""
このスクリプトは、フォワードキネマティクスで算出された全フレーム・全ジョイントの3次元座標（CSVファイル）をもとに、
特定ジョイント（18番: left_elbow と 22番: jaw）の高さ（Z座標）差を分析・可視化します。

【主な処理内容】
- 指定CSVファイル（JOINT_MODEL_DATA/Spatial_xyz_Data/ID_4/20201129_ID_4_0002_hsmal_joints_xyz.csv）を読み込み
- left_elbow（18番）とjaw（22番）のZ座標差（jaw - left_elbow）を計算
- 統計量（平均・最小・最大・標準偏差・中央値など）を出力
- フレームごとの高さ差や、各ジョイントのZ座標の推移をグラフ化
- 高さ差のヒストグラムや、X座標と高さ差の散布図も作成
- 結果グラフを joint_height_difference_analysis.png として保存

【注意】
- 入力CSVファイルのパスやジョイント番号は必要に応じて変更してください。
- matplotlib, pandas, numpy が必要です。

【出力】
- 統計情報（標準出力）
- 可視化グラフ（joint_height_difference_analysis.png）
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def analyze_joint_height_difference():
    # データ読み込み
    df = pd.read_csv('JOINT_MODEL_DATA/Spatial_xyz_Data/ID_4/20201129_ID_4_0002_hsmal_joints_xyz.csv')
    
    # ジョイント18番（l_hip）と22番（lh_hoof）のZ座標を取得
    joint18_z = df['18_l_hip_z [mm]']
    joint22_z = df['22_lh_hoof_z [mm]']
    
    # 高さ差を計算（lh_hoof - l_hip）
    height_diff = joint22_z - joint18_z
    
    print("=== ジョイント18番（l_hip）と22番（lh_hoof）の高さ差分析 ===")
    print(f"ジョイント18番（l_hip）のZ座標範囲: {joint18_z.min():.2f} ~ {joint18_z.max():.2f} mm")
    print(f"ジョイント22番（lh_hoof）のZ座標範囲: {joint22_z.min():.2f} ~ {joint22_z.max():.2f} mm")
    print()
    print("高さ差（lh_hoof - l_hip）:")
    print(f"  平均: {height_diff.mean():.2f} mm")
    print(f"  最小: {height_diff.min():.2f} mm")
    print(f"  最大: {height_diff.max():.2f} mm")
    print(f"  標準偏差: {height_diff.std():.2f} mm")
    print(f"  中央値: {height_diff.median():.2f} mm")
    print()
    
    # 特定フレームでの詳細
    frames_to_check = [0, 50, 100, 200, 300, 400, 500]
    print("特定フレームでの高さ差:")
    for frame in frames_to_check:
        if frame < len(height_diff):
            print(f"  フレーム{frame}: {height_diff.iloc[frame]:.2f} mm")
    
    print()
    print("統計情報:")
    print(f"  正の値（lh_hoofが高い）の割合: {(height_diff > 0).mean() * 100:.1f}%")
    print(f"  負の値（l_hipが高い）の割合: {(height_diff < 0).mean() * 100:.1f}%")
    print(f"  ゼロに近い値（±10mm以内）の割合: {(abs(height_diff) <= 10).mean() * 100:.1f}%")
    
    # グラフ作成
    plt.figure(figsize=(12, 8))
    
    # サブプロット1: 高さ差の時系列
    plt.subplot(2, 2, 1)
    plt.plot(height_diff.values, alpha=0.7)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.title('高さ差の時系列変化 (lh_hoof - l_hip)')
    plt.xlabel('フレーム')
    plt.ylabel('高さ差 [mm]')
    plt.grid(True, alpha=0.3)
    
    # サブプロット2: 各ジョイントのZ座標
    plt.subplot(2, 2, 2)
    plt.plot(joint18_z.values, label='l_hip (18番)', alpha=0.7)
    plt.plot(joint22_z.values, label='lh_hoof (22番)', alpha=0.7)
    plt.title('各ジョイントのZ座標')
    plt.xlabel('フレーム')
    plt.ylabel('Z座標 [mm]')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # サブプロット3: 高さ差のヒストグラム
    plt.subplot(2, 2, 3)
    plt.hist(height_diff.values, bins=50, alpha=0.7, edgecolor='black')
    plt.axvline(x=0, color='r', linestyle='--', alpha=0.5)
    plt.title('高さ差の分布')
    plt.xlabel('高さ差 [mm]')
    plt.ylabel('頻度')
    plt.grid(True, alpha=0.3)
    
    # サブプロット4: 散布図（X座標 vs 高さ差）
    plt.subplot(2, 2, 4)
    joint18_x = df['18_l_hip_x [mm]']
    plt.scatter(joint18_x.values, height_diff.values, alpha=0.5, s=1)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.title('X座標 vs 高さ差')
    plt.xlabel('l_hip X座標 [mm]')
    plt.ylabel('高さ差 [mm]')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('joint_height_difference_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return height_diff

if __name__ == "__main__":
    height_diff = analyze_joint_height_difference() 