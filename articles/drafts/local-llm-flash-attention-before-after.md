---
title: "【FlashAttention編】Ollamaで本当に速くなるのか？Q4/Q5/Q8で実測した意外な結論"
slug: "local-llm-flash-attention-before-after"
description: "OLLAMA_FLASH_ATTENTION=1 で本当に速くなるのか？Qwen3.6-27B Q4/Q5/Q8 全 18 タスクで Before/After 計測した結果、Q4/Q5 では逆効果という意外な事実が判明。"
tags: [LLM, Ollama, FlashAttention, ベンチマーク, パフォーマンス, Qwen3]
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
    emoji: "⚡"
    topics: [llm, ollama, performance, benchmark, qwen]
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
  theme: "green"
---

## 🎯 この記事で得られること

> **この記事を読むと、あなたは以下が分かります。**
>
> - ✅ FlashAttention は **本当に速くなるのか** の実測値
> - ✅ **どの条件でオン/オフ** すべきかの判断基準
> - ✅ ネット上の「絶対オンにしろ」を **鵜呑みにしてはいけない理由**

---

## 😰 「FlashAttention 有効化で速くなる」を信じていませんか？

ローカル LLM の最適化を調べると、必ずヒットするのが:

```bash
export OLLAMA_FLASH_ATTENTION=1
```

「これだけで速くなる」「KV cache が半分になる」「絶対オンにすべき」と紹介されていることが多い。

私もそう信じて、Q8_0 が遅すぎる問題（前回の **【Q8_0 編】** 参照）を救う **銀の弾丸**として期待しました。

**結論を先に言います: 期待は裏切られました。**

---

## 📊 検証方法：Before / After 完全実測

| 項目 | 内容 |
|---|---|
| ハードウェア | RTX 5090 (32GB VRAM) + 64GB RAM |
| モデル | Qwen3.6-27B (Q4_K_M / Q5_K_M / Q8_0 の 3 量子化) |
| タスク数 | 6 種類（FizzBuzz / フィボナッチ / バグ修正 / リファクタ / 日本語説明 / マルチファイル設計）|
| 計測項目 | TTFT / tok/s / E2E / VRAM / GPU 使用率 / 消費電力 |
| 試行 | 各 1 回（合計 18 ケース × 2 = 36 計測）|

**Before**: 設定なし（FlashAttention OFF）
**After**: `OLLAMA_FLASH_ATTENTION=1` + `OLLAMA_KV_CACHE_TYPE=q8_0`

---

## 💥 結果：Q4 / Q5 では逆効果

### Q4_K_M（17GB）

| 指標 | Before | After | Δ |
|---|---|---|---|
| TTFT (ms) | 29,284 | 32,998 | **+12.7% 遅化** |
| tok/s | **6.04** | **5.66** | **-6.3% 遅化** |
| E2E latency (s) | 33.75 | 37.63 | **+11.5% 遅化** |
| VRAM peak (MiB) | 27,682 | 26,849 | -3.0% |
| GPU util (%) | 78.1 | 77.4 | -0.9% |

VRAM はわずかに減ったが、**速度は全体的に遅くなった**。

### Q5_K_M（20GB）

| 指標 | Before | After | Δ |
|---|---|---|---|
| TTFT (ms) | 32,379 | 35,097 | **+8.4% 遅化** |
| tok/s | 5.29 | 5.01 | **-5.3% 遅化** |
| E2E latency (s) | 37.32 | 40.13 | **+7.5% 遅化** |
| VRAM peak (MiB) | 29,800 | 28,974 | -2.8% |
| GPU util (%) | 77.3 | 82.3 | +6.5% |

こちらも VRAM はわずかに減ったが、**全体は遅くなった**。

### Q8_0（30GB）← VRAM 限界突破中

| 指標 | Before | After | Δ |
|---|---|---|---|
| TTFT (ms) | 185,124 | 168,084 | **-9.2% 改善** |
| tok/s | 0.85 | 0.96 | **+12.6% 改善** |
| E2E latency (s) | 217.17 | 193.38 | **-11.0% 改善** |
| VRAM peak (MiB) | 32,407 | 32,435 | +0.1% |
| GPU util (%) | 24.1 | 24.0 | -0.3% |
| Power avg (W) | 106.6 | 118.2 | +10.8% |

**Q8_0 でもわずか 11% 改善**。VRAM もほぼ変わらず、CPU offload は解消されていない。

---

## 🔬 なぜ Q4/Q5 では逆効果だったのか？

FlashAttention の仕組みは:

1. **メリット**: KV cache をブロック単位で計算し、メモリ I/O を削減
2. **コスト**: ブロック分割・再構成のための **計算オーバーヘッド** が増える

つまり以下のトレードオフ:

```text
利得 = (削減できたメモリ I/O) - (追加の計算コスト)
```

- **VRAM に余裕がある場合（Q4/Q5）**: メモリ I/O はもともとボトルネックではない
  → 削減利得 < オーバーヘッド → **逆効果**
- **VRAM 限界の場合（Q8）**: メモリ I/O がボトルネック
  → 削減利得 > オーバーヘッド → **多少改善**
- **VRAM オーバーの場合（CPU offload 中）**: PCIe 経由の転送が支配的
  → FlashAttention では PCIe を減らせない → **大した改善なし**

これが今回の実測で見えた **真の構造**です。

---

## ✅ 判断フローチャート

```text
                         Q. VRAM 残量は?
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
   3GB 以上 余裕         1GB 以下 ギリギリ         オーバー中
       │                      │                      │
       ▼                      ▼                      ▼
   FA OFF 推奨            FA ON 推奨             FA は気休め
   (速度優先)            (10% 改善)         (根本対策が必要)
                                                     │
                                                     ▼
                                              モデルを 1段下げる
```

---

## 🎓 学んだこと：「みんなが言ってる」を信じない

ローカル LLM コミュニティでは、**SNS で広まる「定番チューニング」を鵜呑みにしてしまいがち**です。

- 「FlashAttention は絶対オン」← 今回検証した通り、条件次第
- 「Speculative Decoding は速い」← 小さなドラフトモデルが必要、品質も変わる
- 「num_ctx は大きい方がいい」← KV cache が爆発する

**「自分のハードウェアで Before/After を計測する」**ことが、唯一信頼できる判断材料です。

今回のような単純な比較も、わずか 30 分で全 18 タスクが回せます。これからローカル LLM の最適化を試すなら、まず計測基盤を作ってから設定を変えるのがおすすめです。

---

## 🛠 実測コード（GitHub）

検証に使ったコード一式は MIT 公開しています:

→ [secure-auto-lab/local-coder](https://github.com/secure-auto-lab/local-coder)

主要ファイル:
- `qwen-coder/bench/run.py` ─ ベンチマーク実行
- `qwen-coder/bench/metrics.py` ─ NVML で GPU 計測（1秒サンプリング）
- `qwen-coder/bench/compare.py` ─ Before/After 比較レポート生成
- `qwen-coder/bench/tasks/*.json` ─ 6 タスク定義

```powershell
# Before
python -m bench.run --variants q4,q5,q8 --out bench/results/before

# 環境変数を切り替え
$env:OLLAMA_FLASH_ATTENTION = "1"
$env:OLLAMA_KV_CACHE_TYPE = "q8_0"
# Ollama を再起動

# After
python -m bench.run --variants q4,q5,q8 --out bench/results/after

# 比較レポート
python -m bench.compare bench/results/before bench/results/after \
    --label-a "FA OFF" --label-b "FA ON"
```

---

## ⚠️ 注意点

### 1. KV cache 量子化の影響

`OLLAMA_KV_CACHE_TYPE=q8_0` は KV cache を 8bit に量子化します。長文脈での品質に微妙な影響が出る可能性あり（今回の 6 タスクでは差は確認できず）。

### 2. モデル / GPU で結果が変わる

Llama 3.3 や Mixtral では別の傾向の可能性あり。**自分のモデルで計測すること**を推奨。

### 3. Ollama のバージョン依存

検証は Ollama 0.22.1。バージョンアップで FlashAttention 実装が変わる可能性あり。

---

## 📝 まとめ：FlashAttention は「条件付きの薬」

| 状況 | 推奨設定 |
|---|---|
| VRAM 余裕あり（Q4/Q5）| **OFF**（オーバーヘッドの方が大きい） |
| VRAM ギリギリ（Q8 が VRAM内）| ON（KV cache 削減効果大） |
| VRAM オーバー（CPU offload 中）| **ON でも限定的**、量子化を下げるべき |

**「とりあえずオンにしておけば速くなる」は嘘。** 必ず計測してから判断しましょう。

---

## おわりに

このシリーズの最終回 **【完全比較編】** では、Q4/Q5/Q8 + FlashAttention の全データを横断的に比較し、**「結局あなたはどれを選ぶべきか」** を **コスト・品質・速度の3軸**で結論付けます。

検証コード一式は [secure-auto-lab/local-coder](https://github.com/secure-auto-lab/local-coder) に公開しています。Star いただけると励みになります 🌟

---

**この記事が役に立ったら**:
- 🐦 X で感想シェア（[@secure_auto_lab](https://twitter.com/secure_auto_lab)）
- 💬 「うちの環境でも同じ傾向だった!」「逆だった!」という体験談、コメントでぜひ
