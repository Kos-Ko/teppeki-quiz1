---
name: teppeki-quiz
description: 鉄壁の単語リストから文脈穴埋め4択の問題バンクをまとめて作り、GitHub Pagesで公開できるクイズサイト（index.html + questions.js）として返す。「鉄壁テスト」「問題バンクを作って」「teppeki-quiz.zip」を渡されたとき、または「Section ○から出題して」と言われたときに使う。
---

# 鉄壁 文脈穴埋めテスト：一括作成パッケージ（AI向けの手順書）

このzip（`teppeki-quiz/`）を受け取ったAIは、以下の手順を **自分で最後まで実行する**。
ユーザーへの質問は、手順の中で「聞く」と書いてある場面だけにする。

## zipの構成
```
teppeki-quiz/            ← この中身がそのままGitHub Pagesのサイトになる
├─ index.html            クイズ本体（questions.js を読み込む。基本的に触らない）
├─ questions.js          問題データ（このパッケージで作り直す対象）
├─ README.md             公開手順とPagesのリンク
├─ .nojekyll
└─ kit/
   ├─ SKILL.md           この手順書
   ├─ banks/             問題バンク（.md）。bank_sample.md は動作確認用
   ├─ references/
   │   ├─ bank_generation.md   問題の作成基準（品質ルール・出力形式・自己チェック）← 必ず読む
   │   ├─ quiz_engine.md       チャットで出題するときのルール
   │   ├─ quick_version.md     単語リストがないときの簡易版
   │   └─ guide_for_humans.md  人間向けの説明書
   ├─ templates/wordlist_template.csv
   └─ scripts/
       ├─ check_bank.py   バンクの形式とかたよりを検査する
       ├─ bank_to_js.py   バンク（.md）→ questions.js に変換する
       └─ pick.py         チャットで出題するとき用のランダムな選択とシャッフル
```

## 手順

### 0. 入力を確認する
- **単語リスト**（`section,word,pos,meaning,note` のCSV、またはそれに近い表・テキスト・写真）があるか確認する。
  - 形式が違っていても、セクション番号と単語が読み取れれば、AIが整えて作業フォルダに `wordlist.csv` として保存する（zipには入れない）。
  - 単語リストがなければ、`templates/wordlist_template.csv` を渡して入力を **聞く**。今すぐ試したい場合は、`references/quick_version.md` を使ってチャットで出題できることも伝える。
- **鉄壁の収録語やセクションの割り振りを、記憶から再現しない。** 不正確になるうえ、市販の教材の転載にもなるため。
- GitHubのユーザー名が分かれば、README.md の「ユーザー名」を置き換える。分からなければ置き換えずに、最後の報告でその旨を一言伝える。
- 作成範囲の指定がなければ、単語リストにある全セクションを対象にする。

### 1. 問題バンクを作る（ここが本体）
- `references/bank_generation.md` を読み、その基準どおりに作る。
- **5セクションずつ** のバッチに分けて作る。1セクションにつき20問。
- 各バッチを `kit/banks/bank_secXX-YY.md` に保存する。
- 1バッチを書き終えるたびに、次を実行する。
  ```
  python3 kit/scripts/check_bank.py kit/banks/bank_secXX-YY.md --wordlist wordlist.csv
  ```
  - `ERROR` が出たら、その問題を直してから再度チェックする。`WARN` は内容を見て判断する。
  - スクリプトで分かるのは形式だけ。そのうえで、`bank_generation.md` の「自己チェック」（正解以外の選択肢が文脈上入らないか、など）を自分の目で1問ずつ行い、怪しい問題は作り直す。
- バッチが多いときは、進み具合（例：「Section 1〜15 完了」）を短く報告しながら最後まで続ける。「続けますか？」と聞いて止まらない。
- 本番の問題ができたら、`kit/banks/bank_sample.md` を削除する。

### 2. サイト用に変換してzipにする
```
python3 kit/scripts/check_bank.py kit/banks/                 # 全体を最終チェック
python3 kit/scripts/bank_to_js.py kit/banks/ -o questions.js # questions.js を作り直す
```
- `index.html` をブラウザで開ける環境であれば、表示を確認する（セクションの一覧が出る、出題・採点ができる）。
- `teppeki-quiz/` フォルダ全体（`.nojekyll` を含む。**`wordlist.csv` は含めない**）を `teppeki-quiz.zip` にまとめて、ユーザーに渡す。
  ```
  cd 親フォルダ && zip -r teppeki-quiz.zip teppeki-quiz -x "*/wordlist.csv" "*/__pycache__/*"
  ```
- 最後に、次のことを短く報告する。
  - 総問題数と、セクションごとの問題数の表
  - 作り直した問題の数
  - 次にやること：「zipを解凍し、GitHubのリポジトリに上書きアップロード → 数分で反映」（詳しくは README.md）

### 3. （任意）チャットで出題する
ユーザーが「Section 3」などと送ってきたら、`references/quiz_engine.md` のルールで出題する。
問題の選び方には `kit/scripts/pick.py` を使う（使い方はスクリプトの冒頭を参照）。
