"""
このスクリプトは、指定したディレクトリ（デフォルト: JOINT_MODEL_DATA/Leg_Joint_Angles/ID_4）内の全てのCSVファイルから、脚の関節角度データのうちY軸（絶対角度: '_y_abs [deg]' または相対角度: '_y_rel_from_' を含むカラム）のみを抽出し、新しいCSVファイルとして保存します。

出力先ディレクトリ（デフォルト: JOINT_MODEL_DATA/Leg_Joint_Angles_y_only）が自動的に作成され、各ファイルは元のファイル名に'_yonly'を付加した名前で保存されます。

【使い方】
python extract_leg_joint_y_angle.py

必要に応じて input_dir や output_dir を書き換えてください。
"""
import os
import glob
import pandas as pd
from scripts.utils.joint_utils import load_joint_names, load_joint_hierarchy

# joint_utilsのimportが必要な場合は以下を追加
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))

def main():
    input_dir = 'JOINT_MODEL_DATA/Leg_Joint_Angles/ID_4'
    output_dir = 'JOINT_MODEL_DATA/Leg_Joint_Angles_y_only'
    os.makedirs(output_dir, exist_ok=True)

    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    for csv_file in csv_files:
        print(f'Processing: {os.path.basename(csv_file)}')
        df = pd.read_csv(csv_file)
        # y軸角度カラムのみ抽出（_y_abs [deg] または _y_rel_from_ を含むもの）
        y_cols = [col for col in df.columns if ('_y_abs [deg]' in col) or ('_y_rel_from_' in col)]
        y_df = df[['frame'] + y_cols]
        out_name = os.path.splitext(os.path.basename(csv_file))[0] + '_yonly.csv'
        out_path = os.path.join(output_dir, out_name)
        y_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 