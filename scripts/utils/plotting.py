"""
グラフ生成の共通ヘルパ

各グラフスクリプトは 1CSVあたり数百枚のPNGを書き出す。
毎回 plt.figure() で新しいFigureを作ると生成・破棄のコストが積み上がるため、
1枚のFigureを使い回す。あわせてバックエンドを Agg に固定し、
GUIバックエンドの初期化を避ける。
"""
import matplotlib

matplotlib.use('Agg')  # 画面表示は行わないので描画専用バックエンドに固定する

import matplotlib.pyplot as plt  # noqa: E402  (use()より後にimportする必要がある)
import numpy as np  # noqa: E402
from scipy.interpolate import make_interp_spline  # noqa: E402

# 日本語フォントは環境依存なので、確実に存在するフォントを使う
plt.rcParams['font.family'] = 'DejaVu Sans'

_FIGURE = None


def get_figure(figsize=(12, 6)):
    """使い回し用のFigureを返す（中身はクリア済み）"""
    global _FIGURE
    if _FIGURE is None:
        _FIGURE = plt.figure(figsize=figsize)
    else:
        _FIGURE.clf()
        _FIGURE.set_size_inches(*figsize)
    return _FIGURE


def save_scatter(frames, values, ylabel, out_path, dpi=150, ylim=None):
    """散布図を描いて保存する"""
    fig = get_figure()
    ax = fig.add_subplot(111)
    ax.scatter(frames, values, alpha=0.6, s=1, color='blue', label='Data points')
    _finish(fig, ax, ylabel, out_path, dpi, ylim)


def save_smooth(frames, values, ylabel, out_path, dpi=150, ylim=None):
    """
    平滑線グラフを描いて保存する

    データ点が少なすぎてスプライン近似できない場合は False を返す（保存しない）。
    """
    if len(frames) <= 10:
        return False

    step = max(1, len(frames) // 1000)
    sf, sv = frames[::step], values[::step]
    if len(sf) <= 3:
        return False

    fig = get_figure()
    ax = fig.add_subplot(111)
    try:
        spline = make_interp_spline(sf, sv, k=3)
        smooth_x = np.linspace(frames[0], frames[-1], 1000)
        ax.plot(smooth_x, spline(smooth_x), color='red', linewidth=2, label='Smooth line')
    except Exception as e:
        # スプライン近似は入力が単調でない等で失敗しうる。その場合は間引いた生データを描く。
        # 裸の except にすると KeyboardInterrupt まで飲み込んでしまうので Exception を明示する。
        print(f'  Spline error: {e}, fallback to simple plot.')
        ax.plot(sf, sv, color='red', linewidth=2, label='Smooth line')
    _finish(fig, ax, ylabel, out_path, dpi, ylim)
    return True


def _finish(fig, ax, ylabel, out_path, dpi, ylim):
    ax.set_xlabel('Frame', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight')
