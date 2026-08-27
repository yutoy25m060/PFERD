"""
このスクリプトは、各馬の体型パラメータ（betas）から脚部の骨格比を導出します。

【なぜbetasだけで骨長が決まるのか】
hSMAL/SMALはリグ型のモデルで、親子ジョイント間の距離（＝骨の長さ）は
ポーズ（関節角度 poses）を変えても変化せず、体型パラメータ betas だけで決まります。
そのため「その馬の骨格比」を知るには、実betasを与えたTポーズを1フレーム計算すれば十分です。
（フレームごとの姿勢データは不要ですが、--verify で裏付け検証に使えます）

【処理の流れ】
1. dataset/ 配下の ID_* を自動検出（--horse-id で1頭に絞り込みも可能）
2. 各馬の全npzから betas を読み、平均する（同時にばらつきを表示して一貫性を確認）
3. 平均betasでTポーズ（poses=0, trans=0）のフォワードキネマティクスを1回実行
4. 脚部チェーンに沿って親子間距離＝骨セグメント長を算出
5. 脚内比率・体幹基準比率に正規化し、左右対称性もチェック

【入力ファイル】
- dataset/<horse_id>/MODEL_DATA/*_hsmal.npz （'betas' を含む）
- hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl
- JOINT_MODEL_DATA/Parents_Info/<horse_id>/parents_hsmal36.csv

【出力ファイル】
- JOINT_MODEL_DATA/Leg_Skeletal_Ratios/<horse_id>_leg_segment_lengths_mm.csv
  （馬ごと：セグメント長と各種比率の明細）
- JOINT_MODEL_DATA/Leg_Skeletal_Ratios/all_horses_leg_segment_lengths_mm.csv
  （全馬比較：行=馬、列=セグメント、値=長さmm）
- JOINT_MODEL_DATA/Leg_Skeletal_Ratios/all_horses_leg_segment_ratios.csv
  （全馬比較：同上、値=脚内比率）
- JOINT_MODEL_DATA/Leg_Skeletal_Ratios/all_horses_leg_symmetry.csv
  （左右差のチェック結果）

【使い方】
    set PYTHONPATH=.
    python scripts/analysis/calc_leg_skeletal_ratios.py              # 全馬
    python scripts/analysis/calc_leg_skeletal_ratios.py --horse-id 4 # ID_4のみ
    python scripts/analysis/calc_leg_skeletal_ratios.py --verify     # 実モーションでの骨長安定性も検証
"""
import argparse
import glob
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import numpy as np
import pandas as pd

from scripts.utils.cli import normalize_horse_id
from scripts.utils.joint_utils import (
    LEG_CHAINS,
    LEG_SYMMETRY_PAIRS,
    TORSO_CHAIN,
    load_joint_names,
)

OUTPUT_DIRNAME = os.path.join('JOINT_MODEL_DATA', 'Leg_Skeletal_Ratios')
MODEL_PATH = os.path.join('hSMALdata', 'my_smpl_0000_horse_new_skeleton_horse.pkl')


# --------------------------------------------------------------------------
# データ探索・betas集約（モデル本体を読まずに動く部分）
# --------------------------------------------------------------------------

def discover_horse_ids(dataset_dir='dataset'):
    """dataset/ 配下から、npzを実際に持っている ID_* を検出して昇順で返す"""
    found = []
    for path in sorted(glob.glob(os.path.join(dataset_dir, 'ID_*'))):
        if not os.path.isdir(path):
            continue
        horse_id = os.path.basename(path)
        if glob.glob(os.path.join(path, 'MODEL_DATA', '*_hsmal.npz')):
            found.append(horse_id)
    # ID_2 が ID_10 より先に来るよう数値順に並べ替える
    return sorted(found, key=lambda h: int(re.sub(r'\D', '', h) or 0))


def load_mean_betas(horse_id, dataset_dir='dataset'):
    """
    その馬の全npzからbetasを読み、平均を返す。

    同一馬なら全録画でbetasはほぼ同じはずなので、ばらつき（標準偏差の最大値）も
    併せて返し、前提が崩れていないかを呼び出し側で確認できるようにする。

    Returns:
        (mean_betas, max_std, n_files) — npzが無ければ (None, None, 0)
    """
    npz_files = sorted(glob.glob(os.path.join(dataset_dir, horse_id, 'MODEL_DATA', '*_hsmal.npz')))
    if not npz_files:
        return None, None, 0

    all_betas = []
    for npz_path in npz_files:
        npz = np.load(npz_path, allow_pickle=True)
        all_betas.append(np.asarray(npz['betas'], dtype=np.float64).ravel())

    lengths = {b.shape[0] for b in all_betas}
    if len(lengths) != 1:
        raise ValueError(f"{horse_id}: npzごとにbetasの次元が異なります {sorted(lengths)}")

    stacked = np.stack(all_betas)
    max_std = float(stacked.std(axis=0).max()) if len(stacked) > 1 else 0.0
    return stacked.mean(axis=0), max_std, len(npz_files)


# --------------------------------------------------------------------------
# 幾何計算（ジョイント座標さえあれば動く純粋な部分）
# --------------------------------------------------------------------------

def chain_segment_lengths(joints, chain):
    """
    チェーンに沿った隣接ジョイント間の距離を返す

    Args:
        joints: (ジョイント数, 3) のTポーズ座標
        chain: 根元→末端のジョイントインデックス列

    Returns:
        list[float]: len(chain)-1 本のセグメント長
    """
    return [float(np.linalg.norm(joints[c] - joints[p]))
            for p, c in zip(chain[:-1], chain[1:])]


def build_segment_table(joints, joint_names):
    """
    全脚のセグメント長と正規化比率を1つのDataFrameにまとめる

    - ratio_within_leg: その脚の合計長に対する比率（ロボットのリンク長比に相当）
    - ratio_to_torso  : 体幹長に対する比率（馬ごとの体格差を除いた比較用）
    """
    torso_length = sum(chain_segment_lengths(joints, TORSO_CHAIN))

    rows = []
    for leg_name, chain in LEG_CHAINS.items():
        lengths = chain_segment_lengths(joints, chain)
        leg_total = sum(lengths)
        for i, (parent, child) in enumerate(zip(chain[:-1], chain[1:])):
            rows.append({
                'leg': leg_name,
                'segment_index': i,
                'parent_joint': f'{parent}_{joint_names[parent]}',
                'child_joint': f'{child}_{joint_names[child]}',
                'segment': f'{joint_names[parent]}→{joint_names[child]}',
                'length_mm': lengths[i],
                'ratio_within_leg': lengths[i] / leg_total if leg_total else np.nan,
                'ratio_to_torso': lengths[i] / torso_length if torso_length else np.nan,
                'leg_total_mm': leg_total,
                'torso_length_mm': torso_length,
            })
    return pd.DataFrame(rows)


def build_symmetry_table(segment_df):
    """左右の対応するセグメント長を突き合わせ、差と相対差を返す"""
    rows = []
    for left, right in LEG_SYMMETRY_PAIRS:
        left_rows = segment_df[segment_df['leg'] == left].sort_values('segment_index')
        right_rows = segment_df[segment_df['leg'] == right].sort_values('segment_index')
        for (_, l), (_, r) in zip(left_rows.iterrows(), right_rows.iterrows()):
            mean_len = (l['length_mm'] + r['length_mm']) / 2
            diff = l['length_mm'] - r['length_mm']
            rows.append({
                'pair': f'{left} vs {right}',
                'segment_index': l['segment_index'],
                'segment': l['segment'],
                'left_mm': l['length_mm'],
                'right_mm': r['length_mm'],
                'diff_mm': diff,
                'diff_percent': (abs(diff) / mean_len * 100) if mean_len else np.nan,
            })
    return pd.DataFrame(rows)


def wide_column_name(row):
    """全馬比較用テーブルの列名（全馬で同一になるようジョイント名から組み立てる）"""
    return f"{row['leg']}_{row['segment_index']}_{row['segment']}"


# --------------------------------------------------------------------------
# モデル本体を使う部分（重い依存はここでだけ読み込む）
# --------------------------------------------------------------------------

def compute_tpose_joints(model_path, betas, device='cpu'):
    """
    実betasを与えたTポーズ（poses=0, trans=0）のジョイント座標[mm]を返す

    パイプラインの Spatial_xyz_Data と同じ計算経路になるよう、
    forward_kinematics_example.compute_joints_xyz をそのまま再利用する。
    """
    # torch/smplx/aitviewer はここでだけ必要。幾何計算のテストを軽く保つため遅延import。
    from scripts.input_dataset.forward_kinematics_example import compute_joints_xyz
    from utils.smal import SMALLayer, HSMAL

    num_betas = int(betas.shape[0])
    smal_layer = SMALLayer(
        model_path=model_path,
        model_cls=HSMAL,
        device=device,
        num_betas=num_betas,
    )

    n_joints_pose = len(load_joint_names_cached())
    poses = np.zeros((1, n_joints_pose * 3), dtype=np.float32)
    trans = np.zeros((1, 3), dtype=np.float32)

    joints = compute_joints_xyz(smal_layer, poses, betas.astype(np.float32), trans, device)
    return joints[0]  # (ジョイント数, 3) [mm]


_JOINT_NAMES_CACHE = {}


def load_joint_names_cached(horse_id='ID_4'):
    """ジョイント名は全馬共通なので一度読んだら使い回す"""
    if horse_id not in _JOINT_NAMES_CACHE:
        _JOINT_NAMES_CACHE[horse_id] = load_joint_names(horse_id)
    return _JOINT_NAMES_CACHE[horse_id]


# --------------------------------------------------------------------------
# 裏付け検証（任意）
# --------------------------------------------------------------------------

def verify_against_motion(horse_id, segment_df):
    """
    既存の ParentChild_Distances の統計CSVと突き合わせ、
    Tポーズ由来の骨長が実モーション中もほぼ一定であることを確認する。
    """
    stats_files = sorted(glob.glob(os.path.join(
        'JOINT_MODEL_DATA', 'ParentChild_Distances', horse_id, '*_parentchild_dist_stats.csv')))
    if not stats_files:
        print(f'  [検証] {horse_id}: ParentChild_Distances の統計CSVが無いためスキップ')
        print('         （先に scripts/batch/update_joint_model_data.py を実行してください）')
        return

    expected = {row['segment']: row['length_mm'] for _, row in segment_df.iterrows()}
    print(f'  [検証] {len(stats_files)} 件の統計CSVと突き合わせます')
    for stats_path in stats_files:
        stats = pd.read_csv(stats_path)
        worst_std, worst_diff, worst_name = 0.0, 0.0, ''
        for _, row in stats.iterrows():
            # joint_pair 列は "3_shoulderBlade→4_l_shoulder [mm]" 形式
            m = re.match(r'\d+_(.+?)→\d+_(.+?)\s*\[mm\]', str(row['joint_pair']))
            if not m:
                continue
            key = f'{m.group(1)}→{m.group(2)}'
            if key not in expected:
                continue
            if row['std'] > worst_std:
                worst_std, worst_name = row['std'], key
            diff = abs(row['mean'] - expected[key])
            worst_diff = max(worst_diff, diff)
        print(f'    {os.path.basename(stats_path)}: '
              f'フレーム間の最大std={worst_std:.3f}mm ({worst_name}), '
              f'Tポーズとの最大差={worst_diff:.3f}mm')


# --------------------------------------------------------------------------

def process_horse(horse_id, output_dir, device, verify):
    """1頭分の処理。成功したら (明細DataFrame, 対称性DataFrame) を返す"""
    mean_betas, max_std, n_files = load_mean_betas(horse_id)
    if mean_betas is None:
        print(f'{horse_id}: npzが見つかりません。スキップします。')
        return None, None

    print(f'\n=== {horse_id} ===')
    print(f'  npz {n_files}件のbetasを平均（次元={mean_betas.shape[0]}, '
          f'録画間の最大std={max_std:.4f}）')
    if max_std > 1e-3:
        print('  注意: 録画間でbetasにばらつきがあります。'
              '同一個体として推定されていない可能性があります。')

    joints = compute_tpose_joints(MODEL_PATH, mean_betas, device=device)
    joint_names = load_joint_names_cached()
    if joints.shape[0] < len(joint_names):
        raise ValueError(f'{horse_id}: ジョイント数が不足しています '
                         f'({joints.shape[0]} < {len(joint_names)})')

    segment_df = build_segment_table(joints, joint_names)
    symmetry_df = build_symmetry_table(segment_df)

    for leg_name in LEG_CHAINS:
        total = segment_df.loc[segment_df['leg'] == leg_name, 'leg_total_mm'].iloc[0]
        ratios = segment_df.loc[segment_df['leg'] == leg_name, 'ratio_within_leg']
        print(f'  {leg_name:12s} 合計 {total:7.1f} mm  比率 '
              + ' : '.join(f'{r:.3f}' for r in ratios))
    worst = symmetry_df['diff_percent'].max()
    print(f'  左右差の最大: {worst:.2f} %')

    out_path = os.path.join(output_dir, f'{horse_id}_leg_segment_lengths_mm.csv')
    segment_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f'  Saved: {out_path}')

    if verify:
        verify_against_motion(horse_id, segment_df)

    return segment_df, symmetry_df


def parse_args():
    parser = argparse.ArgumentParser(
        description='各馬の体型パラメータ（betas）から脚部の骨格比を導出する')
    parser.add_argument(
        '--horse-id', type=normalize_horse_id, default=None,
        help='対象馬ID（例: 4 または ID_4）。省略時は dataset/ 配下の全馬を処理')
    parser.add_argument(
        '--device', default='cpu',
        help="フォワードキネマティクスに使うデバイス（既定: cpu）")
    parser.add_argument(
        '--verify', action='store_true',
        help='ParentChild_Distances の統計と突き合わせ、骨長がモーション中も一定か検証する')
    return parser.parse_args()


def main():
    args = parse_args()

    horse_ids = [args.horse_id] if args.horse_id else discover_horse_ids()
    if not horse_ids:
        print('dataset/ 配下に *_hsmal.npz を持つ ID_* が見つかりません。')
        print('README.md の「Access to the PFERD Dataset」を参照してデータを配置してください。')
        return

    print(f'対象: {", ".join(horse_ids)}')

    output_dir = OUTPUT_DIRNAME
    os.makedirs(output_dir, exist_ok=True)

    lengths_wide, ratios_wide, symmetry_all = {}, {}, []
    for horse_id in horse_ids:
        segment_df, symmetry_df = process_horse(horse_id, output_dir, args.device, args.verify)
        if segment_df is None:
            continue
        keys = segment_df.apply(wide_column_name, axis=1)
        lengths_wide[horse_id] = pd.Series(segment_df['length_mm'].values, index=keys)
        ratios_wide[horse_id] = pd.Series(segment_df['ratio_within_leg'].values, index=keys)
        symmetry_df.insert(0, 'horse_id', horse_id)
        symmetry_all.append(symmetry_df)

    if not lengths_wide:
        print('\n処理できた馬がありませんでした。')
        return

    outputs = [
        ('all_horses_leg_segment_lengths_mm.csv',
         pd.DataFrame(lengths_wide).T.rename_axis('horse_id').reset_index()),
        ('all_horses_leg_segment_ratios.csv',
         pd.DataFrame(ratios_wide).T.rename_axis('horse_id').reset_index()),
        ('all_horses_leg_symmetry.csv',
         pd.concat(symmetry_all, ignore_index=True)),
    ]
    print()
    for name, df in outputs:
        path = os.path.join(output_dir, name)
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f'Saved: {path}')


if __name__ == '__main__':
    main()
