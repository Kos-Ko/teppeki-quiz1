#!/usr/bin/env python3
"""問題バンク（.md）を、サイトで読み込む questions.js に変換する。

使い方:
  python3 bank_to_js.py banks/ -o ../questions.js
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_bank import load_bank, parse_wrong  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("-o", "--out", default="questions.js")
    a = ap.parse_args()

    out = []
    for q in load_bank(a.paths):
        opts = q["options"]
        letter = q.get("正解", "")[:1]
        if sorted(opts) != ["A", "B", "C", "D"] or letter not in opts:
            print(f"SKIP {q.get('ID')}: 選択肢か正解が不正です", file=sys.stderr)
            continue
        words = [opts[k] for k in "ABCD"]
        ja = q.get("和訳", "")
        out.append({
            "id": q["ID"],
            "section": int(re.match(r"S(\d+)", q["ID"]).group(1)),
            "word": q.get("正解語", ""),
            "level": max(1, min(3, q.get("難易度", "").count("★") or 2)),
            "type": q.get("出題タイプ", ""),
            "instruction": q.get("指示", "").replace("「〜」", f"「{ja}」"),
            "ja": ja,
            "en": q.get("英文", ""),
            "options": words,
            "answer": "ABCD".index(letter),
            "core": q.get("核イメージ", ""),
            "key": q.get("決め手", ""),
            "wrong": parse_wrong(q),
            "usage": q.get("語法メモ", ""),
        })
    out.sort(key=lambda x: x["id"])
    js = ("// このファイルは kit/scripts/bank_to_js.py で自動生成しています。\n"
          "// 手で直すときは、各問題の { } の中身を書き換えてください（answer は options の何番目が正解か。0から数える）。\n"
          "window.QUESTIONS = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    Path(a.out).write_text(js, encoding="utf-8")
    secs = sorted({x["section"] for x in out})
    print(f"{len(out)}問を {a.out} に書き出しました（セクション {secs[0] if secs else '-'}〜{secs[-1] if secs else '-'}、{len(secs)}個）")


if __name__ == "__main__":
    main()
