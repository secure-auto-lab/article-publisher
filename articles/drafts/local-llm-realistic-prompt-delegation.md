---
title: "【決定版】Qwen3.6-27Bは本当にClaude Codeの代替になるか｜現実タスク+丸投げ+プロンプト工学で実測した完全比較"
slug: "local-llm-realistic-prompt-delegation"
description: "ローカル LLM の真の実用判断は『二分探索』ではなく『CSV 重複削除』『じゃんけんゲーム作成』で決まる。Q4_K_M / Q5_K_M を 14 タスク × 3 プロンプト = 60 計測で全実測。プロンプトエンジニアリング最新調査も含めた完全版。"
tags: [LLM, Qwen3, Coding, プロンプトエンジニアリング, Ollama, ベンチマーク, ClaudeCode]
category: "tech"
author: "Secure Auto Lab"
created_at: 2026-05-04
updated_at: 2026-05-04

platforms:
  note:
    enabled: true
    price: 0
  zenn:
    enabled: true
    emoji: "🎯"
    topics: [llm, qwen, ollama, benchmark, promptengineering]
  qiita:
    enabled: true
  blog:
    enabled: true

announcement:
  enabled: true
  platforms:
    - twitter
    - bluesky
    - misskey

ogp:
  theme: "default"
---

## 🎯 この記事で得られること

> **「Qwen3.6-27B はあなたの実業務で使えるか?」 を、現実的なタスクで判断できるようになります。**
>
> - ✅ **現実タスク** で 92-96% 合格率（Q4 + 良いプロンプト = 100%）
> - ✅ **じゃんけん・ブラックジャック・TODO アプリ** などの "丸投げ" にも対応
> - ✅ **プロンプトを変えるだけで 25 ポイント改善**（モデル昇格より効果大）
> - ✅ **2024-2026 最新プロンプトエンジニアリング** 完全レビュー

---

## 😰 前回までの反省: タスクが学術的すぎた

過去の Coding 編で測定したタスク:

- ❌ 「二分探索を実装してください」
- ❌ 「メモ化フィボナッチを書いてください」
- ❌ 「ラウンドロビンクラスを作ってください」

これらは **教科書のお題** であり、**「あなたの実業務で出てくる依頼」とは違います**。読者の方からも「**結局現場で使えるかが分からない**」というご指摘がありました。

そこで本記事では **2 種類の現実タスク**で再測定しました。

| タスク種別 | 内容 | タスク数 |
|---|---|---|
| **現実タスク** | "CSV 重複削除"、"JSON からメール抽出" など日常 Python | **8 個** |
| **丸投げタスク** | "じゃんけんゲーム作って"、"TODO アプリ作って" など仕様補完が必要 | **6 個** |

合計 **14 タスク × 3 プロンプト変種 × 2 量子化 = 約 60 計測** です。

---

## 📚 本題に入る前に: 2024-2026 プロンプトエンジニアリング最新事情

近年のプロンプトエンジニアリングの主要トレンドを、論文ソースつきで整理します。

| 手法 | 出版年 | 効果が高い場面 |
|---|---|---|
| **Chain-of-Thought (CoT)** | Wei 2022, Kojima 2022 | 推論が必要なタスク全般。"step by step" を加えるだけ |
| **Plan-and-Solve (PS)** | Wang 2023 (ACL) | 複雑問題で CoT より +5-10% 精度向上 |
| **Few-shot prompting** | Brown 2020 | 1-3 例で niche タスク精度向上 |
| **Role prompting** | 古典 | 「あなたは○○です」で語彙・スタイル制御 |
| **XML structuring** | Anthropic 公式 | `<task>` `<example>` でタグ構造化、Claude で特に有効 |
| **Self-Consistency** | Wang 2022 | 複数生成→多数決で +5-15% |
| **Tree of Thoughts (ToT)** | Yao 2023 | 複雑分岐の問題で +10-30% |
| **Reflexion** | Shinn 2023 | 自己批判で再試行、コーディングで +15-25% |
| **ReAct** | Yao 2022 | 推論+ツール実行ループ、エージェント基本 |
| **Skeleton-of-Thought** | Ning 2023 | 並列骨格生成で速度+品質 |
| **Extended Thinking** | Anthropic 2025 | Claude の think タグ、難問で +10-25% |
| **Context Engineering** | 2025 トレンド | プロンプト工学から拡張、メモリ・状態統合 |
| **MIPRO** | DSPy 2024 | ベイズ最適化による自動プロンプト改善 |
| **TextGrad** | 2024 (Nature) | テキスト勾配でプロンプト自動最適化 |

特に注目すべき 2025 トレンド:

> **「プロンプトエンジニアリング」から「コンテキストエンジニアリング」へ**
> 単発のテンプレ最適化を超え、Agent 状態・メモリ・ツール連携を **コンテキスト全体として設計** する考え方が主流に。

ローカル LLM で特に効果が高いとされる手法:

1. **Role + Output Format** ─ 小型モデルほど効果大
2. **Plan-and-Solve** ─ コーディングで +10-20% 精度向上
3. **Few-shot** ─ ニッチドメインで強力
4. **Negative Prompting** ─ "○○しないでください" で誤動作回避

これらの効果を、本記事では **Q4_K_M で実測** しました。

---

## 🔬 本記事で検証したプロンプト変種

### Variant A: bare（素のリクエスト）

```text
顧客リストの CSV ファイルからメールアドレスで重複を削除して新しい CSV に保存する Python 関数を書いてください。
```

普通にユーザーが頼む状態。

### Variant B: role（役割 + 出力フォーマット）

```text
あなたは Python 3.10+ に精通したエンジニアです。

# 要求
顧客リストの CSV ファイルからメールアドレスで重複を削除して...

# 制約
- 必要な import を全て含めること
- コードは Markdown コードブロック (```python) で返すこと
- 余分な説明は最小限に
```

役割宣言 + 出力フォーマット指定。エンタープライズ用途で標準的。

### Variant C: cot（Plan-and-Solve）

```text
あなたは Python 3.10+ に精通したエンジニアです。
Plan-and-Solve 手法で解いてください。

# 要求
{タスク}

# 手順
1. **実装方針**: 3 行以内の箇条書きで設計を述べる
2. **完全なコード**: Markdown コードブロックで返す
3. **使用例**: 1 つ示す

# 制約
- 仕様の細部（境界・空入力・型）まで厳守
```

「考えてからコード」する Plan-and-Solve 方式。

---

## 📊 結果 1: 現実タスク × プロンプト変種

8 つの現実 Python タスク（CSV 重複削除 / JSON 抽出 / 日付計算 / 統計 / メール解析 / HTML title 抽出 / 辞書再帰マージ / 文字列正規化）で測定。

### 合格率マトリクス

| variant | bare | role | cot | 平均 |
|---|---|---|---|---|
| **Q4_K_M** | **75% (6/8)** | **100% (8/8)** | **100% (8/8)** | 92% |
| **Q5_K_M** | 88% (7/8) | 100% (8/8) | 100% (8/8) | 96% |

### 平均応答時間（秒）

| variant | bare | role | cot |
|---|---|---|---|
| Q4_K_M | 42.4s | **37.8s** | 62.5s |
| Q5_K_M | 54.5s | **42.3s** | 71.2s |

### 衝撃の事実 1: プロンプトを上げると Q4 が +25 ポイント

**Q4 bare 75% → Q4 role 100%（+25 ポイント）**

これは **Q5 にモデルを上げる効果（+13 ポイント）の約 2 倍**。

> **「Q4 + 良いプロンプト > Q5 + 普通のプロンプト」**

このシンプルな事実が、データで明確に証明されました。

### 衝撃の事実 2: role は bare より速い

| | bare | role |
|---|---|---|
| Q4 | 42.4s | **37.8s（11% 速い）** |
| Q5 | 54.5s | **42.3s（22% 速い）** |

期待通りに JSON コードブロックで返す指示があるため、**冗長な前置きが省略**されて高速化。

### 衝撃の事実 3: cot は遅くて、合格率は role と同じ

| | bare | role | cot |
|---|---|---|---|
| 合格率 | 75-88% | 100% | 100% |
| 速度 | 普通 | **最速** | 30-50% 遅い |

「考えてから書く」のは品質に効くが、**この粒度のタスクでは role で十分**。Plan-and-Solve は複雑問題向けで、日常タスクでは過剰投資。

### 失敗 → 改善のパターン

bare で失敗した 3 ケース全てが、role と cot で改善:

| variant | task | bare → role |
|---|---|---|
| Q4 | json_extract | ❌ NameError → ✅ 完璧 |
| Q4 | html_title | ❌ NameError → ✅ 完璧 |
| Q5 | dict_merge | ❌ NameError → ✅ 完璧 |

**全失敗が `NameError`** = LLM が**関数定義を省略して使用例だけ返した**ため。「完全なコードを Markdown コードブロックで」と明示するだけで解消。

---

## 🎮 結果 2: 丸投げタスク（ゲーム + 機能委譲）

仕様が曖昧、または既存システムへの追加実装。**Plan-and-Solve プロンプト** で実施。

### 6 つの丸投げタスク

| # | タスク | 内容 |
|---|---|---|
| 01 | じゃんけん | `play_round(user, computer)` で勝敗判定 |
| 02 | ブラックジャック | カード合計計算（A=1か11の動的選択）|
| 03 | 数当てゲーム | 状態を持つ `GuessGame` クラス |
| 04 | TODO アプリ | localStorage 永続化の単一 HTML（CSS/JS 全部入り）|
| 05 | qwen-coder ツール追加 | `count_lines()` 関数を既存ツール群に追加 |
| 06 | 記事公開システム機能追加 | `extract_summary()` 関数（Markdown/HTML 除去 + 単語境界）|

### 結果

| variant | 合格率 | 失敗ケース |
|---|---|---|
| **Q4_K_M** | **67% (4/6)** | blackjack, extract_summary |
| **Q5_K_M** | 83% (5/6) | rps_game（実は誤判定）|

### 各タスクの実況

#### ✅ TODO アプリ HTML（両 variant とも完走）

最も「丸投げ」っぽいタスク。**Q4 が 7,249 文字、Q5 が 5,576 文字** の HTML を生成。
両方とも:
- 入力欄 + 追加ボタン
- LocalStorage で永続化
- チェック機能 + 削除機能
- 内蔵 CSS / JS

私が手動でブラウザで開いてみたところ、**両方とも実用レベル**で動作しました。Q5 はちゃんと CSS でデザインされていて、Q4 はシンプル実装。

#### ✅ じゃんけん（Q4 完璧、Q5 は判定ミス?）

Q4 のコード:
```python
VALID_HANDS = frozenset({'グー', 'チョキ', 'パー'})
WIN_RULES = {
    'グー': 'チョキ',
    'チョキ': 'パー',
    'パー': 'グー'
}

def play_round(user: str, computer: str) -> str:
    if not isinstance(user, str) or not isinstance(computer, str):
        raise TypeError("引数は文字列である必要があります。")
    if user not in VALID_HANDS or computer not in VALID_HANDS:
        raise ValueError(f"無効な手です。有効な値: {VALID_HANDS}")
    if user == computer:
        return 'draw'
    return 'win' if WIN_RULES[user] == computer else 'lose'
```

→ **Q4 でも完璧な品質**。frozenset / TypeError / ValueError の境界処理まで自発的に実装。

Q5 は機能的にはほぼ同じコードを書いたが、**Q5 は自前の __main__ テスト**を含めてしまい、その自前テストにバグがあって SystemExit 1 を呼んだため、自動採点が FAIL に。**コードロジック自体は正しい**ので、これは LLM ではなくテスト基盤の問題。

> **教訓**: LLM が `if __name__ == '__main__':` に独自のテストを書くケースを想定し、テスト実行時は別ファイルに分離する設計が安全。

#### ❌ Q4 ブラックジャック: コード抽出失敗

Q4 が応答にコードブロックを含めず、テキスト中心の説明だけ返した。**プロンプトで「コードのみ」と指定しても発生**。これは Q4 の **指示遵守力の限界** と言える。

#### ❌ Q4 extract_summary: 572 秒の無限ループ

Markdown と HTML タグを除去 + 単語境界で切る、という複合要件のタスク。Q4 が **9 分半** 生成し続けた末、コード抽出失敗。

> **教訓**: Q4 は **複数要件の複合タスクで暴走**することがある。タイムアウトを必ず設定し、長時間実行は中断すべき。

Q5 は同タスクを **101 秒で正常完了** ─ **Q4 の限界が見えるケース**。

#### ✅ qwen-coder への count_lines() 追加

私が運用している実プロジェクト `qwen-coder` への機能追加。

Q4 のコード:
```python
def count_lines(workspace: Path, path: str) -> str:
    target = Path(path)
    if not target.is_absolute():
        target = workspace / target
    target = target.resolve()
    if not target.exists():
        raise FileNotFoundError(f"File not found: {target}")
    if target.is_dir():
        raise IsADirectoryError(f"Path is a directory: {target}")
    total = blank = code = comment = 0
    try:
        with target.open('r', encoding='utf-8') as f:
            for line in f:
                total += 1
                if line.strip() == '':
                    blank += 1
                elif line.lstrip().startswith('#'):
                    comment += 1
                else:
                    code += 1
    except UnicodeDecodeError:
        raise ValueError(f"Binary or non-UTF-8 file: {target}")
    return f'total: {total}, blank: {blank}, code: {code}, comment: {comment}'
```

→ FileNotFoundError / IsADirectoryError / UnicodeDecodeError まで処理する **本番品質**。Q4 でも **既存システムへの統合** は十分こなせる。

---

## 💡 14 タスクから見えた 5 つの法則

### 法則 1: プロンプトが最大の変数

| 変数 | 効果 |
|---|---|
| プロンプトを bare → role | **+25 ポイント (Q4)** |
| Q4 → Q5 にモデル昇格 | +13 ポイント |
| Q4 + role | **= Q5 + role** |

**プロンプト最適化の方が、モデル選択より効率的**。

### 法則 2: 「完全なコード」を要求するだけで NameError が消える

bare で頻出した「関数定義なし、使用例だけ」の失敗は、**「Markdown コードブロックで完全なコードを返す」と明示するだけ**で完全解消。

### 法則 3: Plan-and-Solve は複雑問題でだけ価値がある

簡単タスク: cot は role と同じ合格率なのに 30-50% 遅い。
複雑タスク（丸投げ）: cot プロンプトで Q4 でも 67% 達成。

→ **タスクの粒度に応じて使い分け**。

### 法則 4: 丸投げ HTML 生成は両 variant とも実用レベル

7,000 文字超の単一 HTML（CSS/JS 全部入り）が一発で動く。**プロトタイプ作成にローカル LLM が完全に使える**ことを示すデータ。

### 法則 5: Q4 の限界 = 複合要件タスク

Markdown 除去 + 単語境界 + 文字数制限 のような **3 つ以上の複合制約**で Q4 は時々暴走。Q5 は安定。

→ **複雑な業務タスクは Q5 が安全**、シンプルなタスクは Q4 で十分。

---

## 📐 推奨プロンプトテンプレート（実用品質）

### 日常タスク向け（高速・高品質）

```text
あなたは Python 3.10+ に精通したエンジニアです。

# 要求
{ここに要求}

# 制約
- 必要な import を全て含めること
- コードは Markdown コードブロック (```python) で返すこと
- 関数定義から完結した実装を提供
- 余分な説明は最小限に
```

### 複雑タスク向け（仕様補完が必要）

```text
あなたは Python 3.10+ に精通したエンジニアです。
Plan-and-Solve 手法で解いてください。

# 要求
{要求}

# 手順
1. **実装方針**: 3 行以内の箇条書き
2. **完全なコード**: Markdown コードブロック
3. **使用例**: 1 つ示す

# 制約
- 仕様の細部（境界・空入力・型）まで厳守
- 必要な import を全て含めること
```

### 既存システム機能追加向け

```text
あなたは経験豊富な Python エンジニアです。

# 既存システムの背景
{システム名}: {1-2 行で目的を説明}

# 既存コードの構造（参考）
{既存ツール / クラスのシグネチャを 5-10 行}

# 追加すべき機能
{要求 + 期待入出力例}

# 制約
- 既存コードのスタイル・命名規約に従う
- 完全なコードを Markdown コードブロックで
- import を全て含める
```

---

## 🆚 Claude Code Max との実質比較

私が普段使っている Claude Code Max（月 1.5 万円）との比較:

| 観点 | Qwen3.6-27B Q4 + role プロンプト | Claude Code Max |
|---|---|---|
| 現実タスク合格率 | **100% (8/8)** | おそらく 100% |
| 丸投げタスク合格率 | 67-83% | おそらく 90%+ |
| 1 タスク応答時間 | 約 38 秒 | 約 5-15 秒 |
| **5 時間制限** | **なし** | あり |
| **性能劣化（時間帯）** | **なし** | しばしば発生 |
| 機密案件 | ✅ 完全ローカル | ⚠️ クラウド送信 |
| 月額コスト | 電気代 約 1,500 円 | **15,000 円** |

**結論**: **8-9 割のタスクで Claude Code Max を代替できる**。残り 1-2 割（複雑な丸投げ）は Claude Code に投げる **ハイブリッド運用** がベスト。

---

## 🛠 公開コード

検証コード一式は MIT で公開しています:

→ [secure-auto-lab/local-coder](https://github.com/secure-auto-lab/local-coder)

主要ファイル:

```text
qwen-coder/bench/coding_realistic/    # 現実タスクベンチ
├── tasks.json                        # 8 タスク定義
├── run.py                            # 3 プロンプト変種で実行
└── report.py                         # 合格率 / 改善差分レポート

qwen-coder/bench/delegation/          # 丸投げタスクベンチ
├── tasks.json                        # 6 丸投げタスク（ゲーム + 機能）
└── run.py                            # subprocess でテスト実行
```

実行コマンド:

```powershell
# 現実タスク（48 ケース、約 30 分）
python -m bench.coding_realistic.run --variants q4,q5 --prompts bare,role,cot

# 丸投げタスク（12 ケース、約 15 分）
python -m bench.delegation.run --variants q4,q5
```

タスクは JSON 1 ファイルに集約。**自分の業務でよくある依頼**を追加して、自環境で再評価できます。

---

## 📝 まとめ：あなたが今日からできる 3 ステップ

### Step 1. プロンプトテンプレートを 1 つ用意

上記の **「日常タスク向け」テンプレート** をテキストエディタに保存。
業務で LLM に頼むときに **常に** これを先頭に貼る習慣を作る。

→ これだけで Q4 で **75% → 100% に改善**します。

### Step 2. ローカル LLM 環境を 30 分で構築

```powershell
winget install Ollama.Ollama
ollama pull qwen3.6:27b-q4_K_M
git clone https://github.com/secure-auto-lab/local-coder
cd local-coder/qwen-coder
.\scripts\install.ps1
.\scripts\run.ps1 -Variant q4
```

Claude Code 互換の CLI が立ち上がります。

### Step 3. 自分のタスクで再ベンチ

`bench/coding_realistic/tasks.json` に **あなたの業務タスク**を 3-5 個追加して再実行。
**その合格率があなたの実用判断値**です。

---

## おわりに

「**ローカル LLM は、現実の業務タスクでどこまで使えるのか?**」

この問いに **14 タスク × 60 計測** で答えるシリーズが、これでひとまず完結します。

私自身の使い方は:
- 朝から夕方まで: **Qwen3.6-27B Q4 + role プロンプト**（メイン）
- どうしても複雑な要件: **Claude Code Max** にスイッチ

これで月の Claude Code 利用が **5 時間制限に引っかかることがなくなり**、性能劣化に振り回されることもなくなりました。**月 1.5 万円の固定費から解放**された、というより **「依存しなくて済むようになった」** という方が実感に近いです。

プロンプトエンジニアリングの効果が思った以上に大きいことが、今回の最大の収穫でした。**モデルを上げる前にプロンプトを見直す**。これからの開発の合言葉になりそうです。

---

**この記事が役に立ったら**:
- 🐦 X でシェア（[@secure_auto_lab](https://twitter.com/secure_auto_lab)）
- 🌟 [GitHub で Star](https://github.com/secure-auto-lab/local-coder)
- 💬 「自分のタスクで試したらこうだった!」という体験談、コメントでお待ちしています
