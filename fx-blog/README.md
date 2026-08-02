# fx-blog — secure-auto-lab FXラボ

fx-blog.secure-auto-lab.com（FX検証・運用記録ブログ）。
仕様・デザイントークン・原稿は [`../fx-blog-handoff/`](../fx-blog-handoff/) を参照。

## 構成

- Astro 7 + MDX + Tailwind v4（`@tailwindcss/vite`）+ RSS + sitemap
- テーマ: Claude風（`../fx-blog-handoff/design-tokens.md`）。トークンは `src/styles/global.css` の `@theme` に定義
- フォント: Noto Serif JP（見出し）/ Noto Sans JP（本文）— @fontsource でセルフホスト
- 記事: `src/content/posts/*.mdx`（frontmatter スキーマは `src/content.config.ts`）
- 免責文（Disclaimer）は `PostLayout` が全記事末尾に自動挿入。文言変更は `src/components/Disclaimer.astro`
- `hasPromotion: true` の記事は冒頭に AdDisclosure（プロモーション表示）が自動で付く

## コマンド

```sh
npm install
npm run dev      # 開発サーバー
npm run build    # dist/ に静的ビルド
npm run preview
```

## OGP 画像

`public/og-default.png`（1200x630）。再生成するときは `og/og-default.html` を
ビューポート 1200x630 の headless Chromium で開いてスクリーンショットを撮る。

## デプロイ（設定済み）

Cloudflare Pages プロジェクト `fx-blog`（wrangler 直接アップロード方式）。

- 本番: https://fx-blog.secure-auto-lab.com （pages.dev: https://fx-blog-4zk.pages.dev）
- `fx-blog/**` に変更を push すると `.github/workflows/deploy-fx-blog.yml` が
  ビルド・デプロイし、カスタムドメインと CNAME レコードも冪等に確保する
- 手動デプロイ: `npm run build && npx wrangler pages deploy dist --project-name fx-blog --branch main`
- 注意: 既存 blog と違いダッシュボードの GitHub 連携ではないため、
  デプロイ設定の変更はワークフローファイル側で行う
