"""
スクリプト共通のコマンドライン引数ヘルパ

パイプラインの各スクリプトが同じ書式で `--horse-id` を受け取れるようにする。
以前は各スクリプトに 'ID_4' がハードコードされており、別の馬を処理するには
全ファイルを手で書き換える必要があった。

【馬IDの指定方法】（上にあるものが優先）
  1. コマンドライン引数   --horse-id 1  /  --horse-id ID_1
  2. 環境変数             PFERD_HORSE_ID=ID_1
  3. 既定値               ID_4
"""
import argparse
import os
import re

DEFAULT_HORSE_ID = 'ID_4'
HORSE_ID_ENV = 'PFERD_HORSE_ID'

# 脚部のジョイント（前脚: 4-13、後脚: 18-27）。グラフ生成の絞り込みプリセットに使う。
LEG_JOINT_INDICES = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                     18, 19, 20, 21, 22, 23, 24, 25, 26, 27]


def normalize_horse_id(value):
    """'4' / 'id_4' / 'ID_4' のいずれも 'ID_4' に正規化する"""
    text = str(value).strip()
    if text.isdigit():
        return f'ID_{text}'
    m = re.fullmatch(r'ID_(\d+)', text, flags=re.IGNORECASE)
    if m:
        return f'ID_{m.group(1)}'
    raise argparse.ArgumentTypeError(f"馬IDの形式が不正です: {value!r}（例: 4 または ID_4）")


def default_horse_id():
    """環境変数があればそれを、なければ既定値を返す"""
    return normalize_horse_id(os.environ.get(HORSE_ID_ENV) or DEFAULT_HORSE_ID)


def parse_joint_filter(value):
    """
    --joints の値を「対象ジョイント番号の集合」に変換する

    'all'  -> None（全ジョイント。絞り込みなし）
    'legs' -> 脚部20ジョイント
    '4,5,6'-> 指定した番号のみ
    """
    text = str(value).strip().lower()
    if text in ('', 'all'):
        return None
    if text == 'legs':
        return set(LEG_JOINT_INDICES)
    try:
        return {int(x) for x in text.replace(' ', '').split(',') if x}
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"--joints の値が不正です: {value!r}（'all' / 'legs' / '4,5,6' のいずれか）")


def add_horse_id_argument(parser):
    """パーサに --horse-id を追加する"""
    parser.add_argument(
        '--horse-id', type=normalize_horse_id, default=default_horse_id(),
        help=f"対象馬ID（例: 4 または ID_4。既定: 環境変数{HORSE_ID_ENV} または {DEFAULT_HORSE_ID}）")
    return parser


def add_graph_arguments(parser):
    """グラフ生成スクリプト向けの共通引数（--dpi / --joints）を追加する"""
    parser.add_argument(
        '--dpi', type=int, default=150,
        help='出力PNGの解像度（既定: 150。印刷用に高精細が必要な場合のみ300を指定）')
    parser.add_argument(
        '--joints', type=parse_joint_filter, default=None,
        help="グラフ化するジョイントの絞り込み（'all' / 'legs' / '4,5,6'。既定: all）")
    return parser


def build_parser(description=None, graph_args=False):
    """--horse-id（必要なら --dpi / --joints も）を備えたパーサを作る"""
    parser = argparse.ArgumentParser(description=description)
    add_horse_id_argument(parser)
    if graph_args:
        add_graph_arguments(parser)
    return parser


def parse_horse_id(description=None):
    """--horse-id だけを受け取るスクリプト向けのショートカット"""
    return build_parser(description).parse_args().horse_id
