#!/usr/bin/env python3
"""（チャットで出題するとき用）問題バンクから未出題の問題をランダムに選び、選択肢をシャッフルして出力する。

例:
  python3 pick.py banks/ --sections 3 --n 10 --format quiz
  python3 pick.py banks/ --sections 3-5 --exclude "S03-01,S04-02" --format quiz
  python3 pick.py banks/ --ids "S03-04,S05-11" --format quiz          # 復習用
  python3 pick.py banks/ --sections 3 --seed 123456 --format answers   # 同じ並びで解答
"""
import argparse, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_bank import load_bank, parse_wrong  # noqa: E402


def parse_sections(s):
    out = set()
    for part in s.split(","):
        part = part.strip().upper().lstrip("S")
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--sections", help="例: 3 / 3-5 / 1,4,9 / all")
    ap.add_argument("--ids", help="出題するIDを直接指定（復習用）")
    ap.add_argument("--exclude", default="", help="出題済みのID（カンマ区切り）")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--format", choices=["quiz", "answers"], default="quiz")
    a = ap.parse_args()

    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(10**6)
    rng = random.Random(seed)
    bank = load_bank(a.paths)
    excl = {x.strip() for x in a.exclude.split(",") if x.strip()}

    if a.ids:
        want = {x.strip() for x in a.ids.split(",")}
        pool = [q for q in bank if q.get("ID") in want]
    else:
        secs = None if not a.sections or a.sections == "all" else parse_sections(a.sections)
        pool = [q for q in bank if q.get("ID") not in excl and
                (secs is None or int(q["ID"][1:].split("-")[0]) in secs)]
    pool.sort(key=lambda q: q["ID"])
    if not pool:
        print("NO_QUESTIONS_LEFT: 指定した範囲に、まだ出題していない問題がありません。")
        return
    chosen = rng.sample(pool, min(a.n, len(pool)))

    print(f"# seed={seed}  この回のあとに残る問題数={len(pool) - len(chosen)}")
    for i, q in enumerate(chosen, 1):
        orig = q["options"]
        correct = orig.get(q.get("正解", "")[:1], "")
        words = list(orig.values())
        rng.shuffle(words)
        new = dict(zip("ABCD", words))
        ans = next(k for k, v in new.items() if v == correct)
        if a.format == "quiz":
            print(f"\n第{i}問 {q.get('難易度', '')}")
            print(q.get("指示", "").replace("「〜」", f"「{q.get('和訳', '')}」"))
            print(q.get("英文", ""))
            print("　".join(f"{k}. {v}" for k, v in new.items()))
        else:
            wrong = parse_wrong(q)
            print(f"\n第{i}問：{ans}. {correct}  [{q['ID']}]")
            print(f"・核イメージ：{q.get('核イメージ', '')}")
            print(f"・決め手：{q.get('決め手', '')}")
            for k, v in new.items():
                if v != correct:
                    print(f"・{k}. {v}：{wrong.get(v, '')}")
            print(f"・語法メモ：{q.get('語法メモ', '')}")


if __name__ == "__main__":
    main()
