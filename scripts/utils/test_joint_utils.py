"""
修正されたジョイントユーティリティのテストスクリプト
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.joint_utils import load_joint_hierarchy, load_joint_names, get_joint_hierarchy_and_names

def test_joint_utils():
    """ジョイントユーティリティのテスト"""
    print("=== ジョイントユーティリティのテスト ===")
    
    try:
        # 1. 親子構造の読み込みテスト
        print("1. 親子構造の読み込みテスト")
        hierarchy = load_joint_hierarchy('ID_4')
        print(f"   読み込み成功: {len(hierarchy)}ジョイント")
        print(f"   例: ジョイント1の親 = {hierarchy[1]}")
        print()
        
        # 2. ジョイント名の読み込みテスト
        print("2. ジョイント名の読み込みテスト")
        joint_names = load_joint_names('ID_4')
        print(f"   読み込み成功: {len(joint_names)}ジョイント")
        print(f"   例: ジョイント0 = {joint_names[0]}")
        print(f"   例: ジョイント1 = {joint_names[1]}")
        print()
        
        # 3. 同時読み込みテスト
        print("3. 同時読み込みテスト")
        hierarchy_dict, joint_names_list = get_joint_hierarchy_and_names('ID_4')
        print(f"   親子構造: {len(hierarchy_dict)}ジョイント")
        print(f"   ジョイント名: {len(joint_names_list)}ジョイント")
        print()
        
        # 4. 指定された親子構造との比較
        print("4. 指定された親子構造との比較")
        expected_parents = {
            0: -1, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7,
            9: 3, 10: 9, 11: 10, 12: 11, 13: 12, 14: 9, 15: 14, 16: 15, 17: 16,
            18: 0, 19: 18, 20: 19, 21: 20, 22: 21, 23: 0, 24: 23, 25: 24, 26: 25, 27: 26,
            28: 0, 29: 28, 30: 29, 31: 30, 32: 31, 33: 17, 34: 17, 35: 17
        }
        
        mismatches = []
        for joint_idx in range(36):
            expected = expected_parents.get(joint_idx)
            actual = hierarchy_dict.get(joint_idx)
            if expected != actual:
                mismatches.append((joint_idx, expected, actual))
        
        if mismatches:
            print("   ❌ 親子構造の不一致を発見:")
            for joint_idx, expected, actual in mismatches:
                print(f"      ジョイント{joint_idx}: 期待={expected}, 実際={actual}")
        else:
            print("   ✅ 親子構造は一致しています")
        print()
        
        # 5. ジョイント名の確認
        print("5. ジョイント名の確認")
        expected_names = [
            'pelvis', 'spine1', 'spine2', 'shoulderBlade', 'l_shoulder', 'l_elbow', 'l_carpal', 'lf_fetlock', 'lf_hoof',
            'r_shoulder', 'r_elbow', 'r_carpal', 'rf_fetlock', 'rf_hoof', 'neck_under', 'neck_upper', 'head_base', 'head_tip',
            'l_hip', 'l_knee', 'l_hock', 'lh_fetlock', 'lh_hoof', 'r_hip', 'r_knee', 'r_hock', 'rh_fetlock', 'rh_hoof',
            'tail_base', 'tail_mid', 'tail_mid2', 'tail_mid3', 'tail_tip', 'ear_l', 'ear_r', 'jaw_tip'
        ]
        
        name_mismatches = []
        for i, (expected, actual) in enumerate(zip(expected_names, joint_names_list)):
            if expected != actual:
                name_mismatches.append((i, expected, actual))
        
        if name_mismatches:
            print("   ❌ ジョイント名の不一致を発見:")
            for i, expected, actual in name_mismatches:
                print(f"      ジョイント{i}: 期待='{expected}', 実際='{actual}'")
        else:
            print("   ✅ ジョイント名は一致しています")
        print()
        
        print("🎉 すべてのテストが完了しました！")
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    test_joint_utils() 