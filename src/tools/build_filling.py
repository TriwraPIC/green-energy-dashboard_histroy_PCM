#!/usr/bin/env python3
"""
build_filling.py — 由「附件一 各管理處推動太陽光電案件辦理情形」Excel 產生 filling.html（基底資料快照）

產物給 Firebase 填報頁的「📥 匯入基底資料」使用（讀 <script id="snapshot-data"> 內的 JSON）。
只含太陽光電(solar_addendum)；小水力四個陣列為空，因為來源 Excel 沒有那些 sheet。

用法：
  python3 build_filling.py --xlsx 檔案.xlsx                      # 自動選最後一個「附件一…」sheet、從檔名推期別/日期
  python3 build_filling.py --xlsx 檔案.xlsx --list-sheets        # 只列出 sheet 名稱
  python3 build_filling.py --xlsx 檔案.xlsx --sheet "附件一 …_1020" --period 11510 --date 2026-10-20 --out filling.html

注意：openpyxl 一般模式讀這類檔案會因圖表解析失敗，所以一律用 read_only=True。
"""
import argparse, datetime, json, os, re, sys, warnings, zipfile
warnings.filterwarnings('ignore')
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))

def col2idx(letters):
    n = 0
    for ch in letters: n = n * 26 + (ord(ch) - 64)
    return n - 1

def sheet_xml_path(z, sheet_name):
    wbx = z.read('xl/workbook.xml').decode('utf8')
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf8')
    m = re.search(r'<sheet [^>]*name="%s"[^>]*r:id="([^"]+)"' % re.escape(sheet_name), wbx)
    if not m: return None
    rid = m.group(1)
    t = (re.search(r'<Relationship [^>]*Id="%s"[^>]*Target="([^"]+)"' % rid, rels)
         or re.search(r'<Relationship [^>]*Target="([^"]+)"[^>]*Id="%s"' % rid, rels))
    return 'xl/' + t.group(1).lstrip('/').replace('xl/', '') if t else None

def s(v):
    if v is None: return ''
    if isinstance(v, float) and v.is_integer(): v = int(v)
    t = str(v).strip()
    return '' if t.startswith('#') else t          # #REF! / #VALUE! 一律視為空白

def num(v):
    if v in (None, ''): return None
    try: n = round(float(v), 6)                      # 去除浮點尾數
    except Exception: return None
    return int(n) if n.is_integer() else n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--sheet')
    ap.add_argument('--period', help='民國年月 5 碼，如 11510；預設由檔名推得')
    ap.add_argument('--date', help='資料日期 YYYY-MM-DD；預設由檔名推得')
    ap.add_argument('--template', default=os.path.join(HERE, 'filling_template.html'))
    ap.add_argument('--out', default='filling.html')
    ap.add_argument('--list-sheets', action='store_true')
    a = ap.parse_args()

    wb = openpyxl.load_workbook(a.xlsx, data_only=True, read_only=True)
    names = [ws.title for ws in wb.worksheets]
    if a.list_sheets:
        for n in names: print(repr(n))
        return
    sheet = a.sheet or next((n for n in reversed(names) if n.startswith('附件一')), None)
    if sheet not in names: sys.exit('找不到 sheet；用 --list-sheets 檢查名稱')

    rows = [list(r) + [None] * (23 - len(r)) for r in wb[sheet].iter_rows(values_only=True)]

    # 合併儲存格：被合併的後續列沿用錨點值（read_only 模式不會自動帶）
    z = zipfile.ZipFile(a.xlsx)
    path = sheet_xml_path(z, sheet)
    if path:
        xml = z.read(path).decode('utf8')
        for c1, r1, c2, r2 in re.findall(r'<mergeCell ref="([A-Z]+)(\d+):([A-Z]+)(\d+)"', xml):
            r1, r2, c1, c2 = int(r1) - 1, int(r2) - 1, col2idx(c1), col2idx(c2)
            if r1 < 3 or r1 >= len(rows): continue            # 只處理資料列
            for rr in range(r1, min(r2, len(rows) - 1) + 1):
                for cc in range(c1, c2 + 1):
                    if rows[rr][cc] in (None, ''): rows[rr][cc] = rows[r1][c1]

    # 資料列：表頭在 index 2，資料從 index 3 起，管理處欄(2)有值才算
    recs, overridden = [], []
    for i in range(3, len(rows)):
        r = rows[i]
        if not s(r[2]): continue
        progress, stage = s(r[4]), s(r[9])
        if progress == '解約' and stage != '已解約':       # 規則：案場進度=解約 → 目前階段改為已解約
            overridden.append((s(r[2]), s(r[6]), stage)); stage = '已解約'
        recs.append({
            '_idx': i, '_kind': 'solar_addendum', 'order': s(r[0]), 'no': s(r[1]),
            'mgmt': s(r[2]), 'contract_name': s(r[3]), 'site_progress': progress,
            'vendor': s(r[5]), 'site_name': s(r[6]), 'site_count': num(r[7]), 'capacity_mw': num(r[8]),
            'current_stage': stage, 'sign_date': s(r[10]), 'install_deadline': s(r[11]),
            'expire_status': s(r[12]), 'current_operation': s(r[13]),   # 欄 13；欄 14/15 常為 #REF!，欄 16「縮短」已含在欄 13
            'difficulty': s(r[17]), 'team_suggestion': s(r[18]), 'note': s(r[19]),
        })

    # 期別/日期：由檔名中的民國 7 碼日期推得（例 1151020）
    period, date = a.period, a.date
    if not (period and date):
        for m in re.finditer(r'(\d{7})', os.path.basename(a.xlsx)):
            y, mo, d = int(m.group(1)[:3]), int(m.group(1)[3:5]), int(m.group(1)[5:7])
            if 110 <= y <= 139 and 1 <= mo <= 12 and 1 <= d <= 31:
                period = period or m.group(1)[:5]
                date = date or '%04d-%02d-%02d' % (y + 1911, mo, d); break
    if not (period and date): sys.exit('無法由檔名推得期別/日期，請用 --period 與 --date')
    yy, mm = int(period[:3]), int(period[3:])

    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + '.000Z'
    src = '%s（%s）' % (os.path.basename(a.xlsx), sheet)
    snap = {'imported_at': now,
            'source_files': [{'name': os.path.basename(a.xlsx), 'sheets_found': ['solar_addendum']}],
            'solar_addendum': recs, 'hydro_tender': [], 'hydro_test': [], 'hydro_potential': [], 'hydro_inquiry': []}
    meta = {'period': period, 'created_at': now, 'snapshot_date': date, 'snapshot_source': src}
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    rep = {'__PERIOD__': period, '__PERIOD_LABEL__': '民國 %d 年 %d 月' % (yy, mm),
           '__SNAPSHOT_DATE__': date, '__SNAPSHOT_SOURCE__': src, '__CREATED_AT__': now,
           '__SNAPSHOT_JSON__': dump(snap), '__METADATA_JSON__': dump(meta),
           '__SNAPSHOT_SCRIPT_TAG_OPEN__': '<' + 'script ', '__SNAPSHOT_SCRIPT_TAG_CLOSE__': '<' + '/script>'}
    html = open(a.template, encoding='utf-8').read()
    for k, v in rep.items(): html = html.replace(k, v)
    open(a.out, 'w', encoding='utf-8').write(html)

    print('sheet      :', sheet)
    print('期別/日期  :', period, date)
    print('案場數     :', len(recs))
    print('解約→已解約:', len(overridden), '筆被改寫（案場進度=解約但目前階段不是已解約）')
    for m_, n_, st in overridden: print('   ', m_, n_, '(原：%s)' % st)
    print('輸出       :', a.out)

if __name__ == '__main__':
    main()
