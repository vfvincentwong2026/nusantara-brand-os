# -*- coding: utf-8 -*-
"""存量页面 Pinterest 浅色统一换色（幂等，可重复跑）。"""
import re, pathlib

MAP = [
    # 深色底 → 白/浅灰
    ('#0b0f14', '#ffffff'), ('#0d1219', '#ffffff'), ('#121820', '#ffffff'),
    ('#151c26', '#ffffff'), ('#161b22', '#ffffff'),
    ('#181f29', '#f2f2f2'), ('#1a222d', '#f2f2f2'),
    ('#1f2733', '#e5e5e5'), ('#232c3a', '#e5e5e5'), ('#33405a', '#cccccc'),
    # 浅色字 → 深/灰
    ('#e8eef5', '#111111'), ('#e6edf3', '#111111'),
    ('#aebacd', '#444444'), ('#a9b6c6', '#444444'),
    ('#8b98a8', '#767676'), ('#8b949e', '#767676'), ('#6e7681', '#767676'),
    ('#5b6779', '#767676'), ('#999999', '#767676'),
    # 强调色收敛
    ('#e4022b', '#e60023'), ('rgba(228,2,43', 'rgba(230,0,35'),
    ('#34d17b', '#2e7d32'), ('rgba(52,209,123', 'rgba(46,125,35'),
    ('#ff5c7a', '#e60023'), ('rgba(255,92,122', 'rgba(230,0,35'),
    ('#ff9a3d', '#b26a00'), ('#e8b246', '#b26a00'), ('rgba(232,178,70', 'rgba(182,106,0'),
    ('#4da3ff', '#767676'), ('rgba(77,163,255', 'rgba(118,118,118'),
    ('#58a6ff', '#767676'), ('#ffd700', '#b26a00'),
    ('#f85149', '#e60023'), ('#d29922', '#b26a00'),
    # 半透明覆盖层
    ('rgba(11,14,19,.92)', 'rgba(255,255,255,.92)'),
    ('rgba(22,27,34,.92)', 'rgba(255,255,255,.92)'),
    ('rgba(255,255,255,.05)', '#f7f7f7'), ('rgba(255,255,255,.06)', '#f7f7f7'),
    ('rgba(255,255,255,.22)', '#e5e5e5'), ('rgba(255,255,255,.02)', 'rgba(0,0,0,.02)'),
]

def recolor(path: pathlib.Path):
    s = path.read_text(encoding='utf-8')
    orig = s
    for old, new in MAP:
        s = s.replace(old, new)
    # #999 词边界（避免误伤 #999999 已先行处理）
    s = re.sub(r'#999(?![0-9a-fA-F])', '#767676', s)
    # 白字压深（深色底已翻白）
    s = re.sub(r'color:#fff\b', 'color:#111111', s)
    if s != orig:
        path.write_text(s, encoding='utf-8')
        print(f'recolored {path}')
    else:
        print(f'unchanged {path}')

if __name__ == '__main__':
    root = pathlib.Path(__file__).resolve().parent.parent
    for page in ('assembly', 'brandkit', 'launch', 'tower', 'map', 'library', 'playbook'):
        recolor(root / 'web' / page / 'index.html')
