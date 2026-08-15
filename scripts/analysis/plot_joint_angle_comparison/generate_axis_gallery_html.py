"""
# ジョイント角度サマリー画像ギャラリーHTML自動生成スクリプト
#
# このスクリプトは、summary ディレクトリに保存された
# joint{番号}_{軸}_summary.png 形式のサマリー画像を一覧表示する
# HTMLギャラリー（axis_gallery.html）を自動生成します。
#
# - 画像が存在しない場合は「画像なし」と表示されます。
# - 画像クリックで拡大・縮小表示が可能です。
# - 出力先: JOINT_MODEL_DATA/Selected_Joint_Graphs/{horse_id}/axis_gallery.html
#
# 事前に summary ディレクトリにサマリー画像が生成されている必要があります。
"""
import os
import re
import csv
import sys

horse_id = 'ID_4'
summary_dir = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id, 'summary')
output_html = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id, 'axis_gallery.html')

if not os.path.isdir(summary_dir):
    print(f'サマリー画像ディレクトリが見つかりません: {summary_dir}')
    print('先に generate_axis_summary_images.py を実行してください。')
    sys.exit(0)

data_keys = [d for d in sorted(os.listdir(summary_dir)) if os.path.isdir(os.path.join(summary_dir, d))]
if not data_keys:
    print(f'サマリー画像が1件も見つかりません: {summary_dir}')
    sys.exit(0)

# joint_names_expected.csvのパス
joint_names_csv = os.path.join('JOINT_MODEL_DATA', 'Parents_Info', horse_id, 'parents_hsmal36.csv')

# joint_index→joint_nameの辞書を作成
joint_index_to_name = {}
with open(joint_names_csv, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        joint_index_to_name[row['joint_index']] = row['joint_name']

def joint_sort_key(joint_dir):
    m = re.match(r'joint(\d+)', joint_dir)
    return int(m.group(1)) if m else 9999

# 1. 各計測データごとに個別HTMLを生成
top_links = []
for data_key in data_keys:
    data_path = os.path.join(summary_dir, data_key)
    indiv_html_name = f'axis_gallery_{data_key}.html'
    indiv_html_path = os.path.join('JOINT_MODEL_DATA', 'Selected_Joint_Graphs', horse_id, indiv_html_name)
    top_links.append(f'<li><a href="{indiv_html_name}">{data_key} のギャラリーを見る</a></li>')
    html = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>軸別ジョイントサマリーギャラリー - {data_key}</title>
<style>
table { border-collapse: collapse; margin-bottom: 40px; }
th, td { border: 1px solid #aaa; padding: 8px; text-align: center; }
th { background: #eee; }
img { max-width: 200px; height: auto; cursor: pointer; transition: 0.2s; }
img.enlarged { max-width: 90vw; max-height: 90vh; position: fixed; top: 5vh; left: 5vw; z-index: 1000; background: #fff; box-shadow: 0 0 20px #333; }
.overlay { display: none; position: fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.5); z-index:999; }
</style>
</head>
<body>
<h1>軸別ジョイントサマリーギャラリー - {data_key}</h1>
<p>画像をクリックすると拡大表示します。もう一度クリックで戻ります。</p>
<div class="overlay" id="overlay"></div>
<script>
function enlarge(img) {
  var overlay = document.getElementById('overlay');
  if(img.classList.contains('enlarged')) {
    img.classList.remove('enlarged');
    overlay.style.display = 'none';
  } else {
    img.classList.add('enlarged');
    overlay.style.display = 'block';
    overlay.onclick = function() { enlarge(img); };
  }
}
</script>
'''.replace('{data_key}', data_key)
    html += '<table>'
    html += '<tr><th>ジョイント番号</th><th>ジョイント名</th><th>x_smooth</th><th>x_scatter</th><th>y_smooth</th><th>y_scatter</th><th>z_smooth</th><th>z_scatter</th></tr>'
    for joint_dir in sorted(os.listdir(data_path), key=joint_sort_key):
        joint_path = os.path.join(data_path, joint_dir)
        if not os.path.isdir(joint_path):
            continue
        m = re.match(r'joint(\d+)(?:_(.+))?', joint_dir)
        joint_number = m.group(1) if m else joint_dir
        joint_name_csv = joint_index_to_name.get(joint_number, '').strip()
        joint_name = m.group(2) if m and m.group(2) else joint_name_csv
        row = f'<tr><td>joint{joint_number}</td><td>{joint_name}</td>'
        for axis in ['x', 'y', 'z']:
            for mode in ['smooth', 'scatter']:
                fname1 = f'joint{joint_number}_{axis}_summary_{mode}.png'
                fname2 = f'joint{joint_number}_{axis}_{mode}.png'
                fpath1 = os.path.join(joint_path, fname1)
                fpath2 = os.path.join(joint_path, fname2)
                rel_path1 = f'summary/{data_key}/{joint_dir}/{fname1}'
                rel_path2 = f'summary/{data_key}/{joint_dir}/{fname2}'
                if os.path.exists(fpath1):
                    print(f"{data_key}/{joint_dir}/{fname1}: OK")
                    row += f'<td><img src="{rel_path1}" onclick="enlarge(this)"></td>'
                elif os.path.exists(fpath2):
                    print(f"{data_key}/{joint_dir}/{fname2}: OK")
                    row += f'<td><img src="{rel_path2}" onclick="enlarge(this)"></td>'
                else:
                    print(f"{data_key}/{joint_dir}/{fname1}: なし & {fname2}: なし")
                    row += '<td>（画像なし）</td>'
        row += '</tr>'
        html += row
    html += '</table>'
    html += '<p><a href="axis_gallery.html">トップに戻る</a></p>'
    html += '</body></html>'
    with open(indiv_html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'個別HTMLを出力: {indiv_html_path}')

# 2. トップページを生成
top_html = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>軸別ジョイントサマリーギャラリートップ</title>
</head>
<body>
<h1>軸別ジョイントサマリーギャラリートップ</h1>
<ul>
'''
top_html += '\n'.join(top_links)
top_html += '''
</ul>
</body></html>
'''
with open(output_html, 'w', encoding='utf-8') as f:
    f.write(top_html)
print(f'トップHTMLを出力: {output_html}') 