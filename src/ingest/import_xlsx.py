#!/usr/bin/env python3
import json
import os
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

from src.utils.normalize import normalize_text, normalize_for_match, split_aliases


def read_xlsx_sheets(path: str) -> Tuple[List[Tuple[str, str]], Dict[str, List[List[str]]]]:
    """Return (sheets, data) where sheets is list of (name, ws_path) and data maps ws_path to rows (list of cell strings)."""
    rows_by_path: Dict[str, List[List[str]]] = {}
    with zipfile.ZipFile(path) as z:
        # Shared strings
        sst: List[str] = []
        if 'xl/sharedStrings.xml' in z.namelist():
            sroot = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in sroot.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                texts = []
                for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                    texts.append(t.text or '')
                sst.append(''.join(texts))

        # Sheets list
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets: List[Tuple[str, str]] = []
        for sh in wb.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
            name = sh.attrib.get('name')
            r_id = sh.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            sheets.append((name, r_id))

        # Resolve r:id -> worksheet target
        rels = {}
        rels_root = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        for r in rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
            rels[r.attrib['Id']] = r.attrib['Target']

        # Read each worksheet rows as list of string values
        for name, rid in sheets:
            target = rels.get(rid)
            ws_path = 'xl/' + target if not target.startswith('xl/') else target
            if ws_path not in z.namelist():
                continue
            ws = ET.fromstring(z.read(ws_path))
            ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
            all_rows: List[List[str]] = []
            for row in ws.findall(f'.//{ns}row'):
                vals: List[str] = []
                for c in row.findall(f'{ns}c'):
                    t = c.attrib.get('t')
                    v = c.find(f'{ns}v')
                    val = ''
                    if v is not None and v.text is not None:
                        if t == 's':
                            try:
                                idx = int(v.text)
                                val = sst[idx] if 0 <= idx < len(sst) else v.text
                            except Exception:
                                val = v.text
                        else:
                            val = v.text
                    vals.append(val)
                # Trim trailing empties
                while vals and (vals[-1] is None or vals[-1] == ''):
                    vals.pop()
                all_rows.append(vals)
            rows_by_path[ws_path] = all_rows
        # Attach resolved paths to sheet names for return
        sheet_pairs = []
        for name, rid in sheets:
            target = rels.get(rid)
            ws_path = 'xl/' + target if not target.startswith('xl/') else target
            sheet_pairs.append((name, ws_path))
        return sheet_pairs, rows_by_path


def header_map(row: List[str]) -> Dict[str, int]:
    m: Dict[str, int] = {}
    for i, h in enumerate(row):
        hn = normalize_text(h).strip()
        m[hn] = i
    return m


def ns_uuid(name: str) -> str:
    # Stable UUID5 based on normalized name
    key = f"series:{normalize_for_match(name)}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def import_xlsx(xlsx_path: str, out_path: str) -> None:
    sheets, data = read_xlsx_sheets(xlsx_path)

    # Identify sheet paths by known names
    path_by_name = {name: path for name, path in sheets}

    series: Dict[str, Dict] = {}
    aliases: List[Dict] = []
    whitelist: List[Dict] = []

    alias_index: Dict[str, str] = {}  # normalized alias -> series_id

    # Sheet: 自制版权文件
    s2_path = path_by_name.get('自制版权文件')
    if s2_path and s2_path in data:
        rows = data[s2_path]
        if not rows:
            print('自制版权文件 sheet is empty')
        else:
            h = header_map(rows[0])
            for r in rows[1:]:
                def get(col):
                    idx = h.get(col)
                    return normalize_text(r[idx]) if idx is not None and idx < len(r) else ''

                name_raw = get('上线剧名') or get('剧名')
                if not name_raw:
                    continue
                sid = ns_uuid(name_raw)
                if sid not in series:
                    series[sid] = {
                        'series_id': sid,
                        'canonical_title': normalize_text(name_raw),
                        'content_type': get('作品类型') or None,
                        'exclusive': (get('是否独家') in ('是', 'yes', 'Yes', 'TRUE', 'true')),
                        'doc_reference': get('版本证明文件（脱敏版）') or None,
                        'cover': get('封面') or None,
                    }
                # Aliases: 剧名, 上线剧名, 别名 (split)
                alias_sources = [
                    ('sheet2', get('剧名')),
                    ('sheet2', get('上线剧名')),
                ]
                for a in split_aliases(get('别名')):
                    alias_sources.append(('sheet2', a))

                for src, a in alias_sources:
                    a = normalize_text(a)
                    if not a:
                        continue
                    norm = normalize_for_match(a)
                    if norm in alias_index:
                        continue
                    alias_index[norm] = sid
                    aliases.append({
                        'series_id': sid,
                        'name': a,
                        'lang': None,
                        'source': src,
                        'is_primary': a == series[sid]['canonical_title'],
                    })

    # Sheet: 自制剧多语言剧名
    s3_path = path_by_name.get('自制剧多语言剧名')
    if s3_path and s3_path in data:
        rows = data[s3_path]
        if rows:
            h = header_map(rows[0])
            lang_map = {
                'English (英语)': 'en',
                'Spanish (西班牙语)': 'es',
                'Portuguese (葡萄牙语)': 'pt',
                'Indonesian (印尼语)': 'id',
                'French (法语)': 'fr',
                'German (德语)': 'de',
                'Italian (意大利语)': 'it',
                'Korean (韩语)': 'ko',
                'Japanese (日语)': 'ja',
                'Thai (泰语)': 'th',
            }
            for r in rows[1:]:
                # Use English as join key when present
                eng_idx = h.get('English (英语)')
                eng = normalize_text(r[eng_idx]) if eng_idx is not None and eng_idx < len(r) else ''
                if not eng:
                    continue
                sid = alias_index.get(normalize_for_match(eng)) or ns_uuid(eng)
                if sid not in series:
                    series[sid] = {
                        'series_id': sid,
                        'canonical_title': eng,
                        'content_type': None,
                        'exclusive': None,
                        'doc_reference': None,
                        'cover': None,
                    }
                # Add language-specific names
                for col, lang in lang_map.items():
                    idx = h.get(col)
                    if idx is None or idx >= len(r):
                        continue
                    val = normalize_text(r[idx])
                    if not val:
                        continue
                    norm = normalize_for_match(val)
                    if norm in alias_index:
                        continue
                    alias_index[norm] = sid
                    aliases.append({
                        'series_id': sid,
                        'name': val,
                        'lang': lang,
                        'source': 'sheet3',
                        'is_primary': False,
                    })

    # Sheet: sereal自制剧单-多语言
    s5_path = path_by_name.get('sereal自制剧单-多语言')
    if s5_path and s5_path in data:
        rows = data[s5_path]
        if rows:
            h = header_map(rows[0])
            base_col = '原剧名（英语或日语）'
            # Map headers to ISO lang codes where reasonable
            col_lang = {
                '西语': 'es', '葡语': 'pt', '意语': 'it', '德语': 'de', '法语': 'fr',
                '日语': 'ja', '韩语': 'ko', '印尼语': 'id', '泰语': 'th', '繁中': 'zh-Hant'
            }
            for r in rows[1:]:
                base = normalize_text(r[h.get(base_col, -1)]) if h.get(base_col) is not None and h.get(base_col) < len(r) else ''
                if not base:
                    continue
                # Try match against any existing alias
                norm_base = normalize_for_match(base)
                sid = alias_index.get(norm_base) or ns_uuid(base)
                if sid not in series:
                    series[sid] = {
                        'series_id': sid,
                        'canonical_title': base,
                        'content_type': None,
                        'exclusive': None,
                        'doc_reference': None,
                        'cover': None,
                    }
                # Insert base as alias if new
                if norm_base not in alias_index:
                    alias_index[norm_base] = sid
                    aliases.append({
                        'series_id': sid,
                        'name': base,
                        'lang': None,
                        'source': 'sheet5',
                        'is_primary': False,
                    })
                # Other language columns
                for col, lang in col_lang.items():
                    idx = h.get(col)
                    if idx is None or idx >= len(r):
                        continue
                    val = normalize_text(r[idx])
                    if not val:
                        continue
                    norm = normalize_for_match(val)
                    if norm in alias_index:
                        continue
                    alias_index[norm] = sid
                    aliases.append({
                        'series_id': sid,
                        'name': val,
                        'lang': lang,
                        'source': 'sheet5',
                        'is_primary': False,
                    })

    # Sheet: YouTube频道链接-投放侧账号 -> whitelist (YouTube)
    s4_path = path_by_name.get('YouTube频道链接-投放侧账号')
    if s4_path and s4_path in data:
        rows = data[s4_path]
        if rows:
            h = header_map(rows[0])
            for r in rows[1:]:
                link = normalize_text(r[h.get('频道链接', -1)]) if h.get('频道链接') is not None and h.get('频道链接') < len(r) else ''
                owner = normalize_text(r[h.get('所属人', -1)]) if h.get('所属人') is not None and h.get('所属人') < len(r) else ''
                name = normalize_text(r[h.get('头像+账户名', -1)]) if h.get('头像+账户名') is not None and h.get('头像+账户名') < len(r) else ''
                if link:
                    whitelist.append({
                        'platform': 'youtube',
                        'channel_url': link,
                        'owner': owner or None,
                        'display_name': name or None,
                    })

    # Build output structure
    out = {
        'series': list(series.values()),
        'aliases': aliases,
        'whitelist': whitelist,
        'meta': {
            'source_file': os.path.basename(xlsx_path),
        },
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f'Wrote {out_path}: {len(out["series"])} series, {len(out["aliases"])} aliases, {len(out["whitelist"])} whitelist entries')


if __name__ == '__main__':
    xlsx = sys.argv[1] if len(sys.argv) > 1 else '打击盗版相关剧.xlsx'
    out = sys.argv[2] if len(sys.argv) > 2 else 'data/data.json'
    import_xlsx(xlsx, out)

