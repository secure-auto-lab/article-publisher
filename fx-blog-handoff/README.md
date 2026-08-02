# fx-blog ハンドオフ資料（Claude Code向け）

これは fx-blog.secure-auto-lab.com（FX検証・運用記録ブログ）構築のための委譲資料一式。
このフォルダだけ読めば作業を開始できるように書いてある。

## ゴール
- 既存ブログ `../blog`（Astro 5.17 + Tailwind 3.4 + MDX/RSS/sitemap）と同等の機能を、
  **Astro 7.x（現時点最新 7.1.6）で新規スキャフォールドし直し**、デザインを本資料の
  「Claude風テーマ」（design-tokens.md）で実装する
- サブドメイン: fx-blog.secure-auto-lab.com（デプロイ先は既存blogと同じ方式を踏襲。
  ../blog のデプロイ設定を確認して同じにすること。不明なら本人に確認）

## 技術方針
- Astro 7 + MDX。Tailwind は v4 系（注意: v4では `@astrojs/tailwind` ではなく
  `@tailwindcss/vite` を使う構成が標準。@astrojs/mdx / @astrojs/rss /
  @astrojs/sitemap は最新版でそのまま）
- content collections で `src/content/posts/`（既存blogの構成を参考に）
- 日本語フォント: 見出し Noto Serif JP（またはShippori Mincho）、本文 Noto Sans JP。
  セルフホスト（@fontsource）推奨、Google Fonts直リンクでも可
- ダークモード: 初期リリースでは不要（ライトのみ）。tokensには両モード定義あり

## 必須ページ・コンポーネント
1. トップ（連載一覧・最新記事）
2. 記事ページ（MDX。figureは PNG を `<figure>` + caption で表示）
3. 連載マップページ（figures/fig2 の内容をHTML化してもよい）
4. `components/Disclaimer.astro` — 全記事末尾に自動挿入する免責定型文
   （article-template.mdx 内の文言を使用）
5. `components/AdDisclosure.astro` — アフィリエイトリンクを含む記事の冒頭に
   「本記事にはプロモーションが含まれます」表示（ステマ規制対応。景表法上必須）
6. 固定ページ: プライバシーポリシー / 運営者情報（有料販売を始める場合は特商法表記も）
7. RSS / sitemap / OGP（og:image は figures と同じ配色で1200x630を生成）

## 記事運用
- 原稿は articles/ フォルダのMDを `src/content/posts/*.mdx` に変換して投入
  （frontmatterの雛形は article-template.mdx）
- 第0部（articles/第0部_初稿.md）が最初の公開記事。[図1][図2] の位置に
  figures/ のPNGを挿入する
- 将来: 日次運用記は別リポジトリのスクリプトが MDX を自動生成してこのブログに
  コミットする想定。posts のスキーマを崩さないこと

## 図版の作り方（今後の記事用）
- figures/*.html がテンプレート。palette と組み方は design-tokens.md 参照
- 生成手順: HTML作成 → headless Chromium で .card 要素を deviceScaleFactor=2 で
  スクリーンショット → PNG
- 原則: 白カード+ヘアライン枠+セリフ見出し / データ色はアクセントのコーラル
  #CC785C を基軸に、青 #2A78D6・赤 #D03B3B を役割色として使用（3色とも
  ライト面でコントラスト3:1以上を検証済み）

## このフォルダの内容
- README.md（本書）
- design-tokens.md — 配色・タイポグラフィ・図版ルール
- article-template.mdx — 記事frontmatter雛形＋免責文言
- articles/ — 第0部初稿・連載構成案・第3部詳細構成
- figures/ — 図1・図2（PNG + 再生成用HTMLソース）

## 未決事項（本人に確認）
- デプロイ先（../blog の設定を流用するか）
- 有料販売の実装方式（当面は無料公開のみで着工してよい）
