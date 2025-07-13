"""
このスクリプトは、hSMALモデルの推定結果（ポーズ・ベータ・トランスレーション）を3Dビューワーで可視化するためのものです。
オプションでモーションキャプチャデータ（C3D）も重ねて表示できます。

【入力ファイル】
- CONFIG.py で指定されたパスのhSMAL推定結果（例: dataset/ID_x/MODEL_DATA/xxxx_hsmal.npz）
- hSMALモデル: hSMALdata/my_smpl_0000_horse_new_skeleton_horse.pkl
- （オプション）モーションキャプチャ: dataset/ID_x/C3D_DATA/xxxx.c3d

【出力】
- 3Dビューワーによる可視化（ファイル出力はなし）
"""
import CONFIG
import numpy as np
import os
# aitviewerのSMPL系メッシュシーケンス（3D人体メッシュアニメーション）を扱うクラス
from aitviewer.renderables.smpl import SMPLSequence
# 3Dビューワー本体のクラス
from aitviewer.viewer import Viewer
# 3D空間上に球（点群など）を描画するためのクラス
from aitviewer.renderables.spheres import Spheres
# hSMALモデルのレイヤー生成クラスとhSMALモデル本体クラス
from utils.smal import SMALLayer, HSMAL
# モーションキャプチャデータや推定結果（npz）を読み込む関数
from utils.readfile import read_mocap,read_results
from aitviewer.panels.panel import Panel
import imgui

# 欠損フレームやダウンサンプリングを考慮して、可視化対象のフレームインデックスを計算する関数
# missing: 欠損フレームのインデックスリスト
# data_length: 全フレーム数
# start, end: 可視化開始・終了フレーム
# downSample: ダウンサンプリング間隔
# 戻り値: 有効フレームのフラグ配列, 有効フレームのインデックス配列

def find_id(missing, data_length, start, end, downSample):
    enabled_frames = np.ones(data_length, dtype=np.bool8)
    if len(missing) != 0 :
        enabled_frames[missing] = 0
    enabled_frames = enabled_frames[start:end]
    if downSample == 1:
        id_ = np.where(enabled_frames)[0]
        return enabled_frames, id_
    else:
        downSample_flag = np.zeros(enabled_frames.shape, dtype=np.bool8)
        downSample_flag[::downSample] = True
        downSample_flag = np.logical_and(enabled_frames, downSample_flag)
        downSample_enable_frame = downSample_flag[::downSample]
        id_ = np.where(downSample_flag)[0]
        return downSample_enable_frame, id_

# hSMAL推定結果を3Dビューワーで可視化するメイン関数
# ID: 被験者ID
# mocapname: モーションキャプチャ名
# start, end: 可視化開始・終了フレーム
# downSample: ダウンサンプリング間隔
# VISUAL_MOCAP: モーションキャプチャ点群も表示するか
# num_betas: 形状パラメータ数

def Load_Visualization(ID=1, mocapname='20201128_ID_1_0008', start=None, end = None,downSample = 1, VISUAL_MOCAP = False, num_betas = 10):
    # hSMAL推定結果（npzファイル）を読み込み
    results_path = os.path.join(CONFIG.DatasetPATH, f'ID_{ID}', 'MODEL_DATA', f'{mocapname}_hsmal.npz')
    data = read_results(results_path)
    data_length = data['trans'].shape[0]
    start = 0 if start is None else start
    end = data_length if end is None or end > data_length else end
    betas = data['betas'][start:end,:]
    poses = data['poses'][start:end,:]
    trans = data['trans'][start:end,:]

    missing_frame = data['missing_frame']
    # 欠損フレームやダウンサンプリングを考慮して有効フレームを取得
    enabled_frames, id_ = find_id(missing_frame, data_length, start, end, downSample = downSample)

    # hSMALモデル（SMALLayer）を初期化
    smal_layer = SMALLayer(
        model_path=CONFIG.ModelPATH,
        model_cls=HSMAL,
        device=CONFIG.DEVICE,
        num_betas=num_betas,
    )

    # aitviewerのSMPLSequenceを作成し、3Dメッシュとして可視化
    smal_seq = SMPLSequence(
        poses_body=poses[id_,3:],
        smpl_layer=smal_layer,
        poses_root=poses[id_,:3],
        betas=betas[id_],
        trans=trans[id_],
        device=CONFIG.DEVICE,
        color=(149/255, 149/255, 149/255, 0.8),
        z_up=True,
        enabled_frames= enabled_frames
    )

    # メッシュのアウトラインを描画し、スケルトン表示はオフ
    smal_seq.mesh_seq.draw_outline = True
    smal_seq.skeleton_seq.enabled = False

    # モーションキャプチャ点群も表示する場合
    if VISUAL_MOCAP:
        mocapfile = os.path.join(CONFIG.DatasetPATH, f'ID_{ID}', 'C3D_DATA', f'{mocapname}.c3d')
        data,_ = read_mocap(mocapfile)
        mocapdata = data.markers.copy()
        mocapdata = mocapdata[start:end, ...]
        # 不可視マーカーはnanにして非表示化
        mocapdata[mocapdata == 0] = np.nan
        assert mocapdata.shape[0] == poses.shape[0] == trans.shape[0] == betas.shape[0]
        ptc_mocap = Spheres(mocapdata[id_,...],color=(149 / 255, 85 / 255, 149 / 255, 0.5), radius=0.05,rotation=np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]),
                            enabled_frames=enabled_frames,)
    else:
        ptc_mocap = None

    # 3Dビューワー（aitviewer）を起動し、シーンにSMPLメッシュや点群を追加
    v = Viewer()
    v.scene.camera.position = (0,3,15)
    v.playback_fps = int(240/downSample)

    v.scene.add(smal_seq)
    if VISUAL_MOCAP:
        v.scene.add(ptc_mocap)

    # --- ここから独自パネルの追加 ---
    class JointAnglePanel(Panel):
        def __init__(self, smal_seq, joint_indices=[0, 1, 2]):
            super().__init__(name="Joint Angles")
            self.smal_seq = smal_seq
            self.joint_indices = joint_indices

        def draw(self, viewer):
            imgui.text("ジョイント角度データ（ラジアン/度）")
            # 現在のフレーム番号を取得
            frame = viewer.current_frame if hasattr(viewer, "current_frame") else 0
            poses = self.smal_seq.poses_body[frame]
            for idx in self.joint_indices:
                angle_rad = poses[idx*3:(idx+1)*3]
                angle_deg = np.degrees(angle_rad)
                imgui.text(f"Joint {idx}: [{angle_rad[0]:.2f}, {angle_rad[1]:.2f}, {angle_rad[2]:.2f}] rad  →  [{angle_deg[0]:.1f}, {angle_deg[1]:.1f}, {angle_deg[2]:.1f}] deg")
    # パネルを追加（例：ジョイント0,1,2）
    v.add_panel(JointAnglePanel(smal_seq, joint_indices=[0, 1, 2]))
    # --- ここまで独自パネルの追加 ---

    v.run()

# コマンドライン引数をパースする関数
# --ID, --mocapname, --start, --end, --downSample, --VISUAL_MOCAP などを受け取る

def parse_augment():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ID", type=int, default=1)
    parser.add_argument("--mocapname", type=str, default='20201128_ID_1_0007')
    parser.add_argument("--start", type=int, default=None)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--downSample", type=int, default=8, help='mocap framerate 240hz, downsample the mocap data')
    parser.add_argument('--VISUAL_MOCAP', action='store_true', help='Whether visualizing')
    args = parser.parse_args()
    return args

# スクリプトが直接実行された場合、コマンドライン引数を受け取りLoad_Visualizationを呼び出す
if __name__ == '__main__':
    args = parse_augment()
    Load_Visualization(ID=args.ID, mocapname=args.mocapname,start=args.start, end = args.end, downSample = args.downSample, VISUAL_MOCAP = args.VISUAL_MOCAP)
