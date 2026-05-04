---
title: "【Q5_K_M編】Ollama公式にない量子化をHuggingFaceから自作する全手順"
slug: "local-llm-qwen3-q5-km-from-huggingface"
description: "Qwen3.6-27B Q5_K_M が Ollama 公式にない問題に直面したエンジニアへ。HuggingFace bartowski 版 GGUF を取得し、自作 Modelfile で Ollama に登録する全手順を解説。"
tags: [LLM, Qwen3, Ollama, HuggingFace, GGUF, 量子化, Modelfile]
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
    emoji: "🔧"
    topics: [llm, ollama, huggingface, gguf, qwen]
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
  theme: "purple"
---

## 🎯 この記事で得られること

> **この記事を読むと、あなたは以下ができるようになります。**
>
> - ✅ **Ollama 公式にない量子化レベル**を HuggingFace から自分で取得できる
> - ✅ **自作 Modelfile** を作って `ollama create` で登録できる
> - ✅ Q4_K_M と Q5_K_M の **実測値の違い**を理解できる

---

## 😰 こんな状況、ありませんか？

```bash
$ ollama pull qwen3.6:27b-q5_K_M
Error: pull model manifest: file does not exist
```

**「Q5_K_M が欲しいだけなのに、Ollama 公式にない…」**

私もまったく同じ状況に陥りました。前回の **【Q4_K_M 編】** で 17GB の Q4_K_M は実用的に動いたので、次のステップとして「もう少し品質の良い Q5_K_M (約 20GB) を試したい」と思った瞬間に、上記のエラーで止まったのです。

`ollama.com/library/qwen3.6/tags` を確認すると:

| Ollama 公式の Qwen3.6:27b タグ | サイズ |
|---|---|
| qwen3.6:27b-q4_K_M | 17 GB |
| qwen3.6:27b-q8_0 | 30 GB |
| qwen3.6:27b-bf16 | 56 GB |
| qwen3.6:27b-mxfp8 | 31 GB（macOS 専用） |
| qwen3.6:27b-nvfp4 | 20 GB（macOS 専用） |
| **qwen3.6:27b-q5_K_M** | **❌ 存在しない** |

なんと **Q5_K_M タグが存在しません**。 Ollama は「整数倍の代表的な量子化」しかメンテしていない方針のようです。

---

## 💡 解決策：HuggingFace から GGUF を直接取得

実は GGUF 量子化はコミュニティで活発に作られており、特に **bartowski** さんという方が、新しいモデルが出るたびに各種量子化版を即時公開してくれます。

### Step 1. HuggingFace のリポジトリを特定

`bartowski/Qwen_Qwen3.6-27B-GGUF` を訪問:

| ファイル | サイズ |
|---|---|
| Qwen_Qwen3.6-27B-Q4_K_M.gguf | 17.5 GB |
| **Qwen_Qwen3.6-27B-Q5_K_M.gguf** | **20.5 GB** ← これ |
| Qwen_Qwen3.6-27B-Q5_K_S.gguf | 19.4 GB |
| Qwen_Qwen3.6-27B-Q6_K.gguf | 23.2 GB |
| Qwen_Qwen3.6-27B-Q8_0.gguf | 28.7 GB |

公式にはない **Q5_K_M / Q5_K_S / Q6_K** が揃っています。

### Step 2. GGUF をダウンロード

```powershell
# 約 20 分（光回線で）
curl.exe -L -o models/Qwen_Qwen3.6-27B-Q5_K_M.gguf `
    https://huggingface.co/bartowski/Qwen_Qwen3.6-27B-GGUF/resolve/main/Qwen_Qwen3.6-27B-Q5_K_M.gguf
```

### Step 3. Ollama 公式 Q4 から Modelfile テンプレを取得

これが最大のポイント。Modelfile を一から書くのは大変なので、**既存の Q4 から流用**します。

```powershell
ollama show qwen3.6:27b-q4_K_M --modelfile
```

出力の中で重要なのは以下の部分:

```text
FROM <長いパス>/sha256-...
TEMPLATE {{ .Prompt }}
RENDERER qwen3.5
PARSER qwen3.5
PARAMETER repeat_penalty 1
PARAMETER temperature 1
PARAMETER top_k 20
PARAMETER top_p 0.95
PARAMETER min_p 0
PARAMETER presence_penalty 1.5
```

`RENDERER` と `PARSER` が **qwen3.5** になっているのが地味に重要。Qwen3.6 はチャットテンプレートを Qwen3.5 と互換にしているので、同じパーサが使えます。

### Step 4. 自作 Modelfile を作成

`models/Modelfile.q5_K_M` を作成:

```text
FROM ./Qwen_Qwen3.6-27B-Q5_K_M.gguf
TEMPLATE {{ .Prompt }}
RENDERER qwen3.5
PARSER qwen3.5
PARAMETER repeat_penalty 1
PARAMETER temperature 1
PARAMETER top_k 20
PARAMETER top_p 0.95
PARAMETER min_p 0
PARAMETER presence_penalty 1.5
```

`FROM` を相対パスに書き換えるだけ。あとは Q4 から完全コピーで OK。

### Step 5. Ollama に登録

```powershell
cd models
ollama create qwen3.6:27b-q5_K_M -f Modelfile.q5_K_M
```

数分で完了し、`ollama list` に新しいモデルが追加されます。

```text
NAME                  ID              SIZE     MODIFIED
qwen3.6:27b-q5_K_M    2eb3ebc3706a    20 GB    15 seconds ago
qwen3.6:27b-q4_K_M    a50eda8ed977    17 GB    4 hours ago
```

これで `ollama run qwen3.6:27b-q5_K_M` が使えます。OpenAI 互換 API でも model 名にこれを指定するだけ。

---

## 📊 Q4_K_M vs Q5_K_M 実測比較

ここからが本記事の核心です。前回と同じ 6 タスクで実測しました。

### サマリー

| 指標 | Q4_K_M (17GB) | Q5_K_M (20GB) | Δ |
|---|---|---|---|
| 平均スループット | **6.0 tok/s** | **5.3 tok/s** | -12% |
| 平均 E2E レイテンシ | 33.75s | 37.32s | +11% |
| VRAM ピーク | 27.7 GB | 29.8 GB | +7.5% |
| GPU 使用率 | 78% | 77% | ほぼ同 |
| 消費電力 | 327W | 342W | +5% |

### タスク別 latency 比較

| タスク | Q4_K_M | Q5_K_M | Δ |
|---|---|---|---|
| fizzbuzz | 26.7s | 35.0s | +31% |
| fibonacci_memo | 28.8s | 28.9s | ±0% |
| bug_fix | 13.2s | 20.5s | +55% |
| refactor_smell | 45.0s | 57.0s | +27% |
| japanese_explain | 18.8s | 25.2s | +34% |
| multi_file_design | 70.0s | 57.2s | -18% |

### 品質面

両者とも **6 タスク全てで正答**。「Q5 の方が応答の語彙が豊か」「コード解説がやや詳しい」といった微細な差はあるものの、**コーディング作業の合否を分けるレベルではない**。

---

## 💔 正直な結論：Q5_K_M は「微妙な改善」に留まる

過大な期待を持って Q5_K_M を導入した私の率直な感想:

| 観点 | 評価 |
|---|---|
| 速度 | 🔻 Q4 より 12% 遅い |
| VRAM | 🔻 +2GB（32GB の 93% を占有）|
| 品質 | 🟰 体感差なし |
| セットアップ手間 | 🔻 Modelfile 自作が必要 |
| 学習効果 | 🔼 GGUF/Modelfile の理解は深まる |

**「Q4 で困ってないなら Q5 にする意味は薄い」** というのが私の結論です。

ただし、本記事の手順を覚えておくと **Q6_K (23GB) や Q5_K_S (19.4GB)** など他の量子化レベルも試せるので、覚える価値はあります。

---

## 🎓 学んだこと：Modelfile とは何か

`Modelfile` は **Docker の Dockerfile に相当**するもので、Ollama 上のモデル定義です。

| Modelfile 命令 | Dockerfile 比喩 |
|---|---|
| `FROM` | ベースイメージ（GGUF or 既存モデル） |
| `TEMPLATE` | 入力プロンプトの整形 |
| `RENDERER` / `PARSER` | チャットテンプレート処理 |
| `PARAMETER` | 推論パラメータ（温度等） |
| `LICENSE` | ライセンス情報 |

`ollama create` は **Docker build** に相当し、レイヤーをハッシュで管理して差分のみ追加します。

これを理解すると、**自分のファインチューン版** や **複数モデルの mix** など、応用が一気に広がります。

---

## ⚠️ ハマりポイント

### 1. RENDERER / PARSER を間違える

Qwen3.6 で **`RENDERER llama3`** とか書くとチャットフォーマットが壊れます。必ず `ollama show` で本家の Modelfile を確認すること。

### 2. GGUF のパスは相対 or 絶対

```text
# OK
FROM ./Qwen_Qwen3.6-27B-Q5_K_M.gguf

# NG（カレントディレクトリ依存）
FROM Qwen_Qwen3.6-27B-Q5_K_M.gguf
```

`./` を付ける、または絶対パス。

### 3. ダウンロードが途中で止まる

20GB の GGUF は時々 HF 側で接続切断されます。`curl -L --retry 3 --retry-delay 5` で再試行を入れておくと安心。

### 4. ディスク容量

GGUF (20GB) + Ollama 内部のコピー (20GB) で **40GB 必要** です。`ollama create` の後、元の GGUF は消しても OK。

---

## 📝 まとめ：今日からできる 4 ステップ

1. `bartowski/Qwen_Qwen3.6-27B-GGUF` から欲しい量子化の GGUF を curl 取得
2. `ollama show <既存モデル> --modelfile` でテンプレ取得
3. FROM だけ書き換えて Modelfile.q5_K_M を作成
4. `ollama create qwen3.6:27b-q5_K_M -f Modelfile.q5_K_M`

---

## おわりに

「Ollama にないなら作ればいい」という発想は、**ローカル LLM を本気で使い込む第一歩**です。Q5_K_M 自体の効果は限定的でしたが、この **Modelfile 自作スキル**は今後 Qwen3-Coder や DeepSeek-V3 などの新モデルでも繰り返し使うことになります。

次回は **【Q8_0 編】**で、30GB モデルを 32GB VRAM に詰め込んだら何が起きたかを正直に報告します（ネタバレ: 想像以上に酷い結果でした）。

---

**この記事が役に立ったら**:
- 🐦 X で感想シェア（[@secure_auto_lab](https://twitter.com/secure_auto_lab)）
- 💬 コメントでご質問・ご感想お待ちしています
