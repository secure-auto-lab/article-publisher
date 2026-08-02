# design-tokens — Claude風テーマ（fx-blog）

## 配色（ライトモード＝初期リリース対象）

| ロール | 値 | 用途 |
|---|---|---|
| page | `#F0EEE6` | ページ背景（クリーム） |
| surface | `#FCFCFB` | カード・記事本文面 |
| ink | `#191919` | 本文・見出し |
| ink-secondary | `#52514E` | リード文・キャプション |
| muted | `#898781` | 軸ラベル・注記 |
| border | `rgba(11,11,11,.10)` | ヘアライン枠 |
| grid | `#E1E0D9` | 図の罫線 |
| axis | `#C3C2B7` | 図の軸線 |
| **accent** | `#CC785C` | ブランドアクセント（コーラル）。リンク・バッジ・主系列 |
| accent-blue | `#2A78D6` | 第2系列・情報 |
| critical | `#D03B3B` | 損失・警告の意味色（意味以外に使わない） |
| good | `#0CA30C` | 利益・正常の意味色（同上） |

ダークモード用（将来）: page `#0D0D0D` / surface `#1A1A19` / ink `#FFFFFF` /
ink-secondary `#C3C2B7` / grid `#2C2C2A` / axis `#383835`。

検証: accent/blue/critical の3色はライト面 `#FCFCFB` 上でコントラスト3:1以上・
色覚多様性ΔE基準クリアを検証済み（2026-08-02）。4色以上を同一チャートに
載せる場合は再検証すること。

## タイポグラフィ

| 用途 | フォント |
|---|---|
| 見出し（h1-h2・図タイトル） | `"Noto Serif JP", Georgia, serif`（weight 600） |
| 本文・UI | `"Noto Sans JP", system-ui, sans-serif` |
| 数値（表・軸） | 本文と同じ + `font-variant-numeric: tabular-nums` |

本文: 16-17px / line-height 1.9 / 段落間 1.5em。記事幅 max 720px。
見出しは字間 +0.01em。英数字は和文より半段細く見えるので混植時は注意。

## 図版ルール（figures/*.html がリファレンス実装）

- 白カード `#FCFCFB`・角丸16px・ヘアライン枠・外側はpage色の余白28px
- タイトルはセリフ26px「図N｜タイトル」、リード14px、注記12px muted
- データマークは細く（線2-3px・点r7）。ラベルは選択的に（全点に数字を付けない）
- 意味色の規律: コーラル=主対象 / 青=対比・情報 / 赤=損失のみ / 緑=利益のみ。
  系列色を状態色として流用しない
- 出力: headless Chromium で `.card` を deviceScaleFactor=2 撮影 → PNG
- 1系列なら凡例不要（タイトルが名を担う）。2系列以上は凡例＋直接ラベル

## コンポーネントのトーン

- バッジ: 角丸999px。無料=accent塗り+白文字 / 有料=ヘアライン枠+ink-secondary
- リンク: accent色・下線はhover時のみ
- 引用・免責: surface上に page色の面 + 左ボーダー3px accent
- 表: ヘッダ下1.5px axis色、行間ヘアライン grid色、数値右揃えtabular
