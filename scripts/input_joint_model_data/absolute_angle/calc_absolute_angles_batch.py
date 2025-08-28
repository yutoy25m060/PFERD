"""
このスクリプトは、Angle_xyz_Data_from_posesの各CSVファイルから、
親子関係を用いて各ジョイントの絶対角度（ワールド座標系でのx, y, z角度, degree）を計算し、
JOINT_MODEL_DATA/Absolute_Angles/ID_4/ に短いファイル名で保存します。

`/scripts/input_joint_model_data/absolute_angle` ディレクトリで出力される「絶対角度」は、  
**ワールド座標系（グローバル座標系）を基準**に各ジョイントの回転を算出したものです。

---

### 詳細解説

#### 1. 「絶対角度」とは？
- **絶対角度**は「各ジョイントがワールド座標系（グローバル座標系）に対して、どの向きに回転しているか」を表します。
- これは「親ジョイントからの相対角度」ではなく、「空間全体に対する絶対的な回転角度」です。

#### 2. 算出方法
- 代表的なスクリプト `calc_absolute_angles_batch.py` では、フォワードキネマティクス（全身の親子関係をたどる）を使って、  
  各ジョイントの「グローバル回転行列」を計算します。
- そのグローバル回転行列をオイラー角（xyz順など）に変換し、「絶対角度」として出力しています。

#### 3. どこが基準か？
- **基準はワールド座標系（グローバル座標系、すなわち「地面に対しての向き」）です。**
- 例えば、Tポーズ（全角度0）なら全てのジョイントの絶対角度も0度になります。
- あるジョイントが「絶対角度30度」となっていれば、「地面（ワールド座標系）に対して30度回転している」ことを意味します。

#### 4. 参考
- スクリプト内で「親子関係をたどってグローバル回転を計算」している部分が該当します。
- 例：`calc_absolute_angles_batch.py` の「親からの回転を累積してグローバル回転を得る」処理。

---

### まとめ

- **絶対角度の基準は「ワールド座標系（グローバル座標系）」です。**
- 各ジョイントが「空間全体に対して」どの向きかを表します。

もし「相対角度（親から見た回転）」との違いや、具体的な計算式などさらに詳しく知りたい場合はご質問ください。

【入力ファイル】
- JOINT_MODEL_DATA/Angle_xyz_Data_from_poses/ID_4/*.csv
- JOINT_MODEL_DATA/Parents_Info/ID_4/parents_hsmal36.csv

【出力ファイル】
- JOINT_MODEL_DATA/Absolute_Angles/ID_4/元ファイル名_hsmal_absolute.csv
  （各行：frame, joint0_pelvis_x [deg], joint0_pelvis_y [deg], joint0_pelvis_z [deg], ...）
"""
import os
import glob
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils')))
from scripts.utils.joint_utils import load_joint_names, load_joint_hierarchy

def main():
    horse_id = 'ID_4'
    input_dir = os.path.join('JOINT_MODEL_DATA', 'Angle_xyz_Data_from_poses', horse_id)
    output_dir = os.path.join('JOINT_MODEL_DATA', 'Absolute_Angles', horse_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # 親子構造とジョイント名をCSVファイルから読み込み
    parent_dict = load_joint_hierarchy(horse_id)
    joint_names = load_joint_names(horse_id)
    parents = list(parent_dict.values())
    n_joints = len(joint_names)

    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    for csv_file in csv_files:
        print(f'Processing: {os.path.basename(csv_file)}')
        df = pd.read_csv(csv_file)
        data = df.values  # shape: (frame数, 関節数×3 + 1)
        n_frames, n_cols = data.shape
        # 1列目（frame列）を除外
        data = data[:, 1:]
        xyz_angles = data.reshape(n_frames, n_joints, 3)  # (frame, joint, xyz)

        # 絶対回転（回転行列）を格納
        abs_rotmats = np.zeros((n_frames, n_joints, 3, 3))
        abs_eulers = np.zeros((n_frames, n_joints, 3))
        for f in range(n_frames):
            for j in range(n_joints):
                # 自身の相対回転（axis-angle→回転行列）
                rel_rot = R.from_rotvec(xyz_angles[f, j, :])
                if parents[j] == -1:
                    abs_rotmats[f, j] = rel_rot.as_matrix()
                else:
                    abs_rotmats[f, j] = abs_rotmats[f, int(parents[j])] @ rel_rot.as_matrix()
                # 絶対回転行列→オイラー角（xyz順、度）
                abs_eulers[f, j, :] = R.from_matrix(abs_rotmats[f, j]).as_euler('xyz', degrees=True)
        # DataFrame化
        columns = []
        for j, name in enumerate(joint_names):
            columns.extend([f'joint{j}_{name}_x [deg]', f'joint{j}_{name}_y [deg]', f'joint{j}_{name}_z [deg]'])
        out_df = pd.DataFrame(abs_eulers.reshape(n_frames, n_joints*3), columns=columns)
        out_df.insert(0, 'frame', range(n_frames))
        # 出力ファイル名
        base = os.path.basename(csv_file).replace('_axisangle.csv', '').replace('.csv', '')
        out_name = f'{base}_hsmal_absolute.csv'
        out_path = os.path.join(output_dir, out_name)
        out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f'Saved: {out_path}')

if __name__ == '__main__':
    main() 