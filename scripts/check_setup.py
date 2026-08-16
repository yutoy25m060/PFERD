"""
このスクリプトは、PFERDパイプラインを実行するための環境が整っているかを診断します。

【チェック項目】
1. 必須Pythonパッケージ（torch, smplx, aitviewer, scipy, pandas, matplotlib, PIL, chumpy）のimport可否
2. CONFIG.py の各パス設定（hSMALモデル.pkl/.npz、ポーズ事前分布、データセットディレクトリ）の存在確認
3. JOINT_MODEL_DATA/Parents_Info/<horse-id>/parents_hsmal36.csv の存在確認
   （パイプライン全体が依存する親子構造ファイル。CLAUDE.mdの「ジョイント構造」参照）
4. CONFIG.DEVICE の解決結果（GPU利用可否とフォールバック状況）

【使い方】
    python scripts/check_setup.py
    python scripts/check_setup.py --horse-id 1

【出力】
- 各チェック項目のpass/fail一覧を標準出力に表示（✓/✗）
- 全てpassならexit code 0、1件でもfailならexit code 1
"""
import importlib
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.utils.cli import build_parser

REQUIRED_PACKAGES = ['torch', 'smplx', 'aitviewer', 'scipy', 'pandas', 'matplotlib', 'PIL', 'chumpy']

CHUMPY_HINT = (" chumpyは新しいsetuptools環境ではソースビルドに失敗することがあります。"
               "pip install chumpy が失敗する場合は setuptools<58 の環境を使うか、"
               "prebuiltなwheelを探してください。")


def check_packages():
    """REQUIRED_PACKAGESを1つずつimportし、(ok, message)のリストを返す"""
    results = []
    for name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(name)
            results.append((True, name))
        except ImportError as e:
            hint = CHUMPY_HINT if name == 'chumpy' else ''
            results.append((False, f"{name}: {e}{hint}"))
    return results


def check_config_paths():
    """CONFIG.ModelPATH/ModelPriorPATH/ModelNPZPATH/DatasetPATHの存在確認"""
    import CONFIG
    targets = [
        ('hSMALモデル (.pkl)', CONFIG.ModelPATH),
        ('ポーズ事前分布 (.pkl)', CONFIG.ModelPriorPATH),
        ('hSMALモデル (.npz)', CONFIG.ModelNPZPATH),
        ('データセットディレクトリ', CONFIG.DatasetPATH),
    ]
    results = []
    for label, path in targets:
        exists = os.path.exists(path)
        results.append((exists, f"{label}: {path}" if exists else f"{label}: 見つかりません ({path})"))
    return results


def check_parents_csv(horse_id):
    """JOINT_MODEL_DATA/Parents_Info/<horse_id>/parents_hsmal36.csv の存在確認"""
    path = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', horse_id, 'parents_hsmal36.csv')
    exists = os.path.exists(path)
    msg = f"{horse_id}: {path}" if exists else f"{horse_id}: 見つかりません ({path})"
    return [(exists, msg)]


def check_device():
    """CONFIG.DEVICEの解決結果とCUDA可否を表示（常にok=True、情報表示のみ）"""
    import CONFIG
    msg = f"CONFIG.DEVICE = {CONFIG.DEVICE}"
    if CONFIG.DEVICE == 'cpu':
        msg += "（GPUが使えないためCPUにフォールバック済み。処理は遅くなりますが動作します）"
    return [(True, msg)]


def main():
    parser = build_parser('環境セットアップの診断（パッケージ・パス・デバイス）')
    args = parser.parse_args()

    sections = [
        ('パッケージ', check_packages()),
        ('CONFIG.py のパス', check_config_paths()),
        ('親子構造CSV', check_parents_csv(args.horse_id)),
        ('デバイス', check_device()),
    ]

    all_ok = True
    for title, results in sections:
        print(f'\n[{title}]')
        for ok, msg in results:
            print(f'  {"✓" if ok else "✗"} {msg}')
            all_ok = all_ok and ok

    print('\n' + ('すべてのチェックに合格しました。' if all_ok else '一部のチェックに失敗しました。上記を確認してください。'))
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
