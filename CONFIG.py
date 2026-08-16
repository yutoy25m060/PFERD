"""
このファイルは、プロジェクト全体で使用するパスやデバイス設定などを一元管理する設定ファイルです。
- 各種データ・モデルのパス
- デバイス（CPU/GPU）指定
などを定義します。
"""
import os
ProjectPATH = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.append(os.path.join(ProjectPATH, 'moshpp/src'))
ModelPATH = os.path.join(ProjectPATH, 'hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl')
ModelPriorPATH = os.path.join(ProjectPATH, 'hSMALdata/walking_toy_symmetric_smal_0000_new_skeleton_pose_prior_new_36parts.pkl')
ModelNPZPATH = os.path.join(ProjectPATH, 'hSMALdata/my_smpl_0000_horse_new_skeleton_horse.npz')
DatasetPATH = os.path.join(ProjectPATH, 'dataset')

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

_PREFERRED_DEVICE = "cuda:0"

def resolve_device(preferred=_PREFERRED_DEVICE):
    """
    希望デバイス(既定 "cuda:0")が使えない環境ではCPUにフォールバックする。
    GPUのない環境で "cuda:0" 決め打ちのまま落ちるのを防ぐための共通ヘルパ。
    torch自体が無い場合は判定できないのでそのまま返す（どのみち後続処理で失敗する）。
    """
    if not _TORCH_AVAILABLE:
        return preferred
    if preferred.startswith("cuda") and not torch.cuda.is_available():
        print(f"[CONFIG] 警告: {preferred} が利用できないため、CPUにフォールバックします。")
        return "cpu"
    return preferred

DEVICE = resolve_device()