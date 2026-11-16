#!/usr/bin/env python3
"""問題バンク（--- 区切りの Sxx-yy 形式）の形式とかたよりを検査する。

使い方:
  python3 check_bank.py banks/bank_sec01-05.md [他のファイル...] [--wordlist wordlist.csv]
  python3 check_bank.py banks/               # フォルダ内の .md をまとめて検査
"""
import argparse, csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path

REQUIRED = ["ID", "正解語", "難易度", "出題タイプ", "指示", "和訳", "英文", "正解",
            "核イメージ", "決め手", "誤答チェック", "語法メモ"]


def parse_file(path):
    text = Path(path).read_text(encoding="utf-8")
    items = []
    for block in re.split(r"^-{3,}\s*$", text, flags=re.M):
        if not re.search(r"^ID:\s*S\d+-\d+", block, flags=re.M):
            continue
        q = {"_file": str(path), "options": {}}
        for line in block.strip().splitlines():
            line = line.strip()
            m = re.match(r"^([A-D])[\.．]\s*(.+)$", line)
            if m:
                q["options"][m.group(1)] = m.group(2).strip()
                continue
            m = re.match(r"^([^:：]+)[:：]\s*(.*)$", line)
            if m and m.group(1).strip() in REQUIRED:
                q[m.group(1).strip()] = m.group(2).strip()
        items.append(q)
    return items


def parse_wrong(q):
    """誤答チェック「B 理由 / C 理由 / D 理由」を {選択肢の語: 理由} にする。"""
    out = {}
    for seg in re.split(r"\s*[/／]\s*", q.get("誤答チェック", "")):
        m = re.match(r"^([A-D])[\s\.．:：]+(.+)$", seg.strip())
        if m and m.group(1) in q["options"]:
            out[q["options"][m.group(1)]] = m.group(2).strip()
    return out


def load_bank(paths):
    files = []
    for p in paths:
        p = Path(p)
        files += sorted(p.glob("*.md")) if p.is_dir() else [p]
    items = []
    for f in files:
        items += parse_file(f)
    return items


def load_wordlist(path):
    words = set()
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            w = (row.get("word") or "").strip().lower()
            if w:
                words.add(w)
    return words


def stem_match(option, words):
    o = option.lower().strip()
    if o in words:
        return True
    # 活用形をざっくり許容（-s, -es, -ed, -d, -ing, -ied, 語尾e落ち）
    for w in words:
        if not o.startswith(w[: max(3, len(w) - 2)]):
            continue
        if o in {w + "s", w + "es", w + "ed", w + "d", w + "ing", w[:-1] + "ing",
                 w[:-1] + "ied", w[:-1] + "ies", w + w[-1] + "ed", w + w[-1] + "ing"}:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--wordlist")
    ap.add_argument("--per-section", type=int, default=20)
    a = ap.parse_args()

    items = load_bank(a.paths)
    words = load_wordlist(a.wordlist) if a.wordlist else None
    errors, warns = [], []
    ids = Counter(q.get("ID") for q in items)
    by_sec = defaultdict(list)

    for q in items:
        qid = q.get("ID", "?")
        for k in REQUIRED:
            if not q.get(k):
                errors.append(f"{qid}: 項目「{k}」がない")
        if ids[qid] > 1:
            errors.append(f"{qid}: IDが重複している")
        opts = q["options"]
        if sorted(opts) != ["A", "B", "C", "D"]:
            errors.append(f"{qid}: 選択肢がA〜Dの4つそろっていない（{''.join(sorted(opts))}）")
        if len(set(v.lower() for v in opts.values())) < len(opts):
            errors.append(f"{qid}: 選択肢に同じ語がある")
        ans = q.get("正解", "").strip()[:1]
        if ans not in opts:
            errors.append(f"{qid}: 正解記号「{ans}」が選択肢にない")
        en = q.get("英文", "")
        if en.count("(   )") != 1:
            errors.append(f"{qid}: 英文の空欄 (   ) が1つではない")
        n = len(re.findall(r"[A-Za-z']+", en.replace("(   )", "")))
        if not 13 <= n <= 27:
            warns.append(f"{qid}: 英文が{n}語（目安は15〜25語）")
        if "【" not in q.get("和訳", ""):
            warns.append(f"{qid}: 和訳に【　】がない")
        if words is not None:
            for k, v in opts.items():
                if not stem_match(v.split()[0], words):
                    warns.append(f"{qid}: 選択肢{k}「{v}」が単語リストにない（活用形なら無視してOK）")
        m = re.match(r"S(\d+)-", qid)
        if m:
            by_sec[int(m.group(1))].append(q)

    print(f"総問題数: {len(items)}")
    print("section | 問題数 | A B C D | ★1 ★2 ★3 | 正解語の重複")
    for s in sorted(by_sec):
        qs = by_sec[s]
        pos = Counter(q.get("正解", "")[:1] for q in qs)
        star = Counter(q.get("難易度", "").count("★") for q in qs)
        dup = [w for w, c in Counter(q.get("正解語", "").lower() for q in qs).items() if c > 1]
        print(f"S{s:02d}     | {len(qs):>4}   | {pos['A']} {pos['B']} {pos['C']} {pos['D']} | "
              f"{star[1]:>2} {star[2]:>2} {star[3]:>2}  | {','.join(dup) or '-'}")
        if len(qs) != a.per_section:
            warns.append(f"S{s:02d}: 問題数が{len(qs)}（目標{a.per_section}）")
        if dup:
            errors.append(f"S{s:02d}: 正解語が重複している → {', '.join(dup)}")
        if qs and max(pos.values()) > len(qs) * 0.4:
            warns.append(f"S{s:02d}: 正解の記号がかたよっている {dict(pos)}")

    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN ", w)
    print(f"\n結果: ERROR {len(errors)}件 / WARN {len(warns)}件")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
