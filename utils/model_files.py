"""
hSMALモデル関連ファイルの存在チェックと、分かりやすいエラー表示を共通化するヘルパ。

SMALLayer/smplx.SMPL や human_body_prior.BodyModel は、モデルファイルが無いと
内部で生のFileNotFoundError等を投げて分かりにくいトレースバックで落ちる。
ここで事前にファイルの有無を確認し、どのファイルが・どこから入手できるかを
表示してから終了することで、README.mdの該当セクションにすぐ辿り着けるようにする。
"""
import os
import sys

HSMAL_DOWNLOAD_URL = "https://sites.google.com/view/cv4horses/cv4horses"
HSMAL_README_SECTION = "README.md の「Access to the hSMAL Model」セクション"


def require_files(*paths, exit_on_missing=True):
    """
    指定した全ファイルの存在を確認する。1つでも欠けていれば、
    欠けているファイルと入手方法を表示する。

    Args:
        *paths: 存在を確認するファイルパス
        exit_on_missing (bool): Trueなら欠落時にプロセスを終了する

    Returns:
        bool: 全て存在すればTrue
    """
    missing = [p for p in paths if not os.path.exists(p)]
    if not missing:
        return True

    print("エラー: 以下の必須ファイルが見つかりません。")
    for p in missing:
        print(f"  - {p}")
    print(f"入手先: {HSMAL_DOWNLOAD_URL}")
    print(f"詳細は {HSMAL_README_SECTION} を参照し、./hSMALdata フォルダに配置してください。")

    if exit_on_missing:
        sys.exit(1)
    return False
