---
title: "【Q4_K_M編】RTX 5090でQwen3.6-27Bを17GBに圧縮、ローカルLLMコーディングは実用に耐えるか"
slug: "local-llm-qwen3-q4-km-coding"
description: "Claude Code月額3万円から解放されたいエンジニア必見。RTX 5090 + Qwen3.6-27B Q4_K_Mで実測した6.0 tok/sの実用性を、6種類のコーディングタスクで検証した全記録。"
tags: [LLM, Qwen3, Ollama, RTX5090, ローカルAI, 量子化]
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
    emoji: "🚀"
    topics: [llm, qwen, ollama, ai, gpu]
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

> **この記事を読むと、あなたは以下を判断できるようになります。**
>
> - ✅ Qwen3.6-27B Q4_K_M (17GB) が**自分の用途で使えるか**を実測値で判断できる
> - ✅ RTX 5090 (32GB VRAM) でローカル LLM を動かす **正確なセットアップ手順** が分かる
> - ✅ Claude Code やChatGPT API との **コスト分岐点** を計算できる

---

## 😰 こんな悩みを抱えていませんか？

- 「Claude Code に毎月3万円払い続けるのは、正直キツい…」
- 「機密コードを外部 API に投げるのは、社内ルール上アウトなんだよな…」
- 「ローカル LLM って『ホビー用』のイメージで、業務で使えるレベルなのかが分からない…」

**私もまったく同じでした。** 結婚式 SaaS の開発で Claude Code をフル活用していましたが、月額が3万円を超え始めて「これ、ハードウェア買った方が安くないか?」と疑い始めたのが事の発端です。

---

## 📖 私のストーリー：API 課金から解放されるまでの道のり

### Before：API 料金が膨らみ続ける日々

正直に告白します。私は当時、こんな状況でした。

- 平日 8 時間 × 20 日、Claude Code を回し続ける
- ピーク月で **API 料金が 3.2 万円**
- 機密性の高い案件は別途 Cursor (年間 240 ドル) も併用
- 月のサブスク総額が **約 5 万円** に到達

「年間 60 万円か…これで RTX 5090 が買えるな」と気づいた瞬間、ローカル LLM への移行を決意しました。

### 転機：RTX 5090 (32GB VRAM) との出会い

NVIDIA RTX 5090 を導入。VRAM 32GB は、ついに 27B〜30B クラスのモデルを **量子化なしに近い品質**で動かせる規模になりました。

- 27B モデル = LLaMA 3.3 / Qwen3.6 / Gemma 3 など、商用 GPT-3.5 を凌ぐ性能のレンジ
- 量子化 Q4_K_M なら 17GB → 32GB VRAM に余裕で乗る

そこで選んだのが **Qwen3.6-27B Q4_K_M** です。Apache 2.0 ライセンスで商用利用も自由、日本語の品質も Llama より明らかに良い。

### After：6 種類のコーディングタスクで実測した結果

結論から言うと、**Q4_K_M は「サクサク使える日常アシスタント」のレンジ** に確実に到達していました。

---

## 📊 実測データ（6 タスクで検証）

### サマリー

| 指標 | 実測値 |
|---|---|
| **平均スループット** | **6.0 tokens/sec** |
| **平均 E2E レイテンシ** | **33.75 秒** |
| **VRAM ピーク** | 27.7 GB（32GB に対し 86%）|
| **GPU 使用率** | 78%（フル活用）|
| **消費電力** | 327 W |
| **モデルディスク** | 17 GB |

### タスク別 詳細

| タスク | 内容 | E2E | tok/s | 結果 |
|---|---|---|---|---|
| **fizzbuzz** | FizzBuzz 実装 | 26.7s | 2.0 | ✅ 完璧 |
| **fibonacci_memo** | メモ化フィボナッチ | 28.8s | 4.6 | ✅ 完璧（lru_cache 使用） |
| **bug_fix** | JS の off-by-one バグ修正 | 13.2s | 8.8 | ✅ バグ特定＋修正版提示 |
| **refactor_smell** | コードの可読性改善 | 45.0s | 5.4 | ✅ dataclass 化＋早期 return |
| **japanese_explain** | 日本語で GIL を200字説明 | 18.8s | 5.0 | ✅ 自然な日本語 |
| **multi_file_design** | FastAPI の3ファイル設計 | 70.0s | 10.4 | ✅ main/models/database 完備 |

**全 6 タスクで正答**。日本語の応答も自然で、ChatGPT-3.5 と遜色ないレベル。

---

## 🛠 セットアップ手順（5 ステップ）

### Step 1. Ollama インストール

```powershell
winget install --id Ollama.Ollama -e
```

### Step 2. モデル取得（17GB ダウンロード）

```powershell
ollama pull qwen3.6:27b-q4_K_M
```

私の環境（光回線）では **約 4 分**で完了しました。

### Step 3. Python 環境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install openai rich prompt_toolkit pynvml
```

### Step 4. CLI 起動

OpenAI 互換 API 経由で接続するだけ。

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # 任意の値で OK
)

resp = client.chat.completions.create(
    model="qwen3.6:27b-q4_K_M",
    messages=[
        {"role": "system", "content": "あなたは熟練のエンジニアです。\n/no_think"},
        {"role": "user", "content": "Pythonで リストを反転する一行コードを示してください。"},
    ],
)
print(resp.choices[0].message.content)
```

### Step 5. ⚠️ 必須：思考モードを OFF にする

Qwen3 系は **デフォルトで thinking モードが ON**。コーディング用途では遅くなるだけなので必ず OFF にしてください。

```python
# system プロンプトの末尾に /no_think を追加するだけ
"あなたは熟練のエンジニアです。\n/no_think"
```

私の環境では、これで **応答時間が 60 秒 → 20 秒（3 倍速）** になりました。

---

## 💰 損益分岐点：Claude Code との比較

| 項目 | Claude Code (Pro) | Q4_K_M ローカル |
|---|---|---|
| 月額固定費 | 3,000 円 | 0 円 |
| 従量課金 | あり（重い使用で +2-3 万円）| なし |
| GPU 初期投資 | 0 円 | RTX 5090 約 50 万円 |
| 電気代 | 0 円 | 327W × 8h × 20日 = **約 1,500 円/月** |
| 機密性 | クラウド送信 | **完全ローカル** |
| 月のトータル | 〜33,000 円 | **1,500 円** |

**月 3 万円のヘビーユーザーなら、約 1.5 年で元が取れる計算**です。電気代を含めても圧倒的にローカルが安い。

ただし注意点として:
- 軽い用途（月 1-2 万円程度）なら、Claude Code の方が手軽でコスパ◎
- ハードウェアの初期投資 + セットアップ工数を許容できる人向け

---

## ✅ Q4_K_M はこんな用途に向いている

| 用途 | 適合度 | 理由 |
|---|---|---|
| 日常的なコード生成 | ⭐⭐⭐⭐⭐ | 6.0 tok/s で十分実用的 |
| バグ調査 | ⭐⭐⭐⭐⭐ | off-by-one を一発で特定 |
| リファクタリング | ⭐⭐⭐⭐ | 提案の質が高い |
| 日本語ドキュメント | ⭐⭐⭐⭐ | 自然な日本語 |
| 機密案件 | ⭐⭐⭐⭐⭐ | 完全ローカル |
| 大規模コード生成（500行超）| ⭐⭐⭐ | 70秒待ちは長い |
| リアルタイム補完 | ⭐ | 6 tok/s では遅い |

---

## ⚠️ ハマりポイントと回避策

### 1. PowerShell の文字化け

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

を起動時に必ずセット。日本語応答が文字化けで読めなくなります。

### 2. Ollama 起動忘れ

別ターミナルで `ollama serve` を立ち上げ忘れると、エラーが出続けます。死活確認:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

### 3. Q4 で「これ無理かな」と思ったら

実際に試して品質が足りないなら **Q5_K_M (20GB) に上げる**選択肢があります。Q5_K_M は Ollama 公式にはありませんが、HuggingFace の bartowski さんが量子化版を公開しているので、Modelfile を自作して登録できます。

→ 詳細は次回の **【Q5_K_M 編】** で解説します。

---

## 📝 まとめ：今日からできる 3 ステップ

1. **`winget install Ollama.Ollama`** で Ollama を入れる
2. **`ollama pull qwen3.6:27b-q4_K_M`** で 17GB を pull
3. **system prompt 末尾に `/no_think`** を必ず付ける

この 3 ステップで、月 3 万円の API 課金から解放される第一歩を踏み出せます。

---

## おわりに

「ローカル LLM はオモチャ」と言われていた時代は、もう終わりつつあります。**RTX 5090 + Qwen3.6-27B Q4_K_M** という組み合わせは、業務に耐える「真の道具」のレンジに突入しました。

次回は **【Q5_K_M 編】**で、Ollama 公式にない Q5_K_M を HuggingFace から自作する全手順を解説します。

---

**この記事が役に立ったら**:
- 🐦 X で感想シェア（[@secure_auto_lab](https://twitter.com/secure_auto_lab)）
- 💬 コメントでご質問・ご感想お待ちしています
