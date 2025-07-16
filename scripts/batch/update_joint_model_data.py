"""
このスクリプトは、/scripts ディレクトリ内のデータ生成系スクリプト（visualize_skeleton_3d.py以外）を順次実行し、
/JOINT_MODEL_DATA 配下の各種データ（空間座標・角度・体型・親子距離など）を一括で最新化します。

【注意】
- 親子関係・ジョイント名は parents_hsmal36.csv（3カラム: joint_index, parent_index, joint_name）に統一されています。
- 必要に応じて horse_id や mocapname などを変更してください。
"""
import subprocess
import sys
import os
import time

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # OpenMP競合回避

# スクリプト実行関数
def run_script(script, args=None, env=None):
    cmd = [sys.executable, script]
    if args:
        cmd += args
    print(f'実行: {" ".join(cmd)}')
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f'エラー: {script} の実行中に失敗しました')
        raise e

# スクリプトリスト（順序・コメント付き）
SCRIPT_LIST = [
    ('scripts/input_dataset/save_joint_axisangle_batch.py', '各ジョイントの軸角（axis-angle）'),
    ('scripts/input_dataset/save_betas_batch.py', '体型パラメータ'),
    ('scripts/input_dataset/save_translation_batch.py', 'モデル全体の並進'),
    ('scripts/input_dataset/forward_kinematics_example.py', '空間座標（フォワードキネマティクス）'),
    ('scripts/input_joint_model_data/spatial_data/calc_parent_child_distances_batch.py', '親子間距離'),
    ('scripts/input_joint_model_data/relative_angle/extract_joint_xyz_angle_from_axisangle.py', '各ジョイントのxyz角度'),
    ('scripts/input_joint_model_data/relative_angle/extract_joint_y_angle_from_axisangle.py', '各ジョイントのy軸角度'),
    ('scripts/input_joint_model_data/absolute_angle/calc_absolute_angles_batch.py', '各ジョイントの絶対角度'),
    ('scripts/input_joint_model_data/absolute_angle/extract_joint_y_absolute_angle.py', '各ジョイントのy軸絶対角度'),
    ('scripts/input_joint_model_data/relative_absolute_combined/save_leg_joint_angles.py', '脚部ジョイント角度'),
    ('scripts/input_joint_model_data/relative_absolute_combined/extract_leg_joint_y_angle.py', '脚部ジョイントy軸角度'),
    ('scripts/input_joint_model_data/relative_angle/create_xyz_angle_graphs.py', 'xyz角度グラフ生成'),
    ('scripts/input_joint_model_data/absolute_angle/create_xyz_absolute_angle_graphs.py', '絶対角度グラフ生成'),
    ('scripts/input_joint_model_data/relative_absolute_combined/create_leg_joint_angle_graphs.py', '脚用グラフ生成'),
    ('scripts/analysis/plot_joint_angle_comparison/plot_joint_angle_comparison.py', '角度比較グラフ生成'),
    ('scripts/analysis/plot_joint_angle_comparison/generate_axis_gallery_html.py', 'ギャラリーHTML生成'),
    ('scripts/analysis/plot_joint_angle_comparison/generate_axis_summary_images.py', 'サマリー画像生成'),
    ('scripts/analysis/plot_joint_angle_comparison/check_yaxis_range.py', 'y軸範囲チェック'),
]

if __name__ == '__main__':
    # PYTHONPATHをプロジェクトルートに統一
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env = os.environ.copy()
    env['PYTHONPATH'] = "C:/Users/Yuto/github_repositories/PFERD/PFERD"

    total_scripts = len(SCRIPT_LIST)
    times = []
    start_all = time.time()

    for idx, (script, desc) in enumerate(SCRIPT_LIST, 1):
        print(f'\n[{idx}/{total_scripts}] {desc} ({script})')
        start = time.time()
        run_script(script, env=env)
        elapsed = time.time() - start
        times.append(elapsed)
        avg_time = sum(times) / len(times)
        remaining = total_scripts - idx
        est_remaining = avg_time * remaining
        print(f'  実行時間: {elapsed:.1f}秒 / 平均: {avg_time:.1f}秒')
        if remaining > 0:
            print(f'  残り{remaining}件、予想残り時間: {est_remaining/60:.1f}分')

    total_elapsed = time.time() - start_all
    print(f'\n全てのデータ更新が完了しました。総所要時間: {total_elapsed/60:.1f}分') 