"""
ジョイント関連の共通ユーティリティ関数
"""
import pandas as pd
import os

def load_joint_hierarchy(horse_id='ID_4', hierarchy_file='parents_hsmal36.csv'):
    """
    指定された親子構造CSVファイルを読み込み、辞書形式で返す
    
    Args:
        horse_id (str): 馬のID
        hierarchy_file (str): 親子構造CSVファイル名
    
    Returns:
        dict: {joint_index: parent_index} の辞書（joint_index昇順）
    """
    hierarchy_path = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', horse_id, hierarchy_file)
    if not os.path.exists(hierarchy_path):
        raise FileNotFoundError(f"親子構造ファイルが見つかりません: {hierarchy_path}")

    df = pd.read_csv(hierarchy_path)
    # load_joint_names と同じくインデックス順に揃える。
    # 呼び出し側が list(hierarchy.values()) のように挿入順に依存しても壊れないようにするため。
    df_sorted = df.sort_values('joint_index')
    hierarchy = dict(zip(df_sorted['joint_index'].astype(int), df_sorted['parent_index'].astype(int)))
    return hierarchy


def get_parents_list(horse_id='ID_4', hierarchy_file='parents_hsmal36.csv'):
    """
    親子構造を「インデックス順のリスト」で返す（parents[j] = ジョイントjの親、ルートは-1）

    load_joint_hierarchy() の戻り値を list(...values()) するとCSVの行順に依存するため、
    順序が意味を持つ用途では必ずこちらを使うこと。

    Args:
        horse_id (str): 馬のID
        hierarchy_file (str): 親子構造CSVファイル名

    Returns:
        list: parents[joint_index] = parent_index
    """
    hierarchy = load_joint_hierarchy(horse_id, hierarchy_file)
    missing = [j for j in range(len(hierarchy)) if j not in hierarchy]
    if missing:
        raise ValueError(f"親子構造CSVのjoint_indexが0..{len(hierarchy) - 1}で連続していません（欠番: {missing}）")
    return [hierarchy[j] for j in range(len(hierarchy))]

def load_joint_names(horse_id='ID_4', names_file='parents_hsmal36.csv'):
    """
    指定されたジョイント名CSVファイルを読み込み、リスト形式で返す
    
    Args:
        horse_id (str): 馬のID
        names_file (str): ジョイント名CSVファイル名
    
    Returns:
        list: ジョイント名のリスト（インデックス順）
    """
    names_path = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', horse_id, names_file)
    if not os.path.exists(names_path):
        raise FileNotFoundError(f"ジョイント名ファイルが見つかりません: {names_path}")
    
    df = pd.read_csv(names_path)
    # インデックス順にソートしてジョイント名を取得
    df_sorted = df.sort_values('joint_index')
    joint_names = df_sorted['joint_name'].str.strip().tolist()
    return joint_names

def get_joint_hierarchy_and_names(horse_id='ID_4'):
    """
    親子構造とジョイント名を同時に読み込む
    
    Args:
        horse_id (str): 馬のID
    
    Returns:
        tuple: (hierarchy_dict, joint_names_list)
    """
    hierarchy = load_joint_hierarchy(horse_id)
    joint_names = load_joint_names(horse_id)
    return hierarchy, joint_names

def get_descendants_dfs(base, parent_dict):
    """
    指定されたジョイントの子孫を深さ優先探索で取得
    
    Args:
        base (int): 基準ジョイントのインデックス
        parent_dict (dict): 親子関係の辞書
    
    Returns:
        list: 子孫ジョイントのインデックスリスト
    """
    descendants = []
    def dfs(node):
        children = [k for k, v in parent_dict.items() if v == node]
        for child in children:
            descendants.append(child)
            dfs(child)
    dfs(base)
    return descendants 