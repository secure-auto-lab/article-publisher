---
title: "B2Bサービスサイトを Astro 5 + Tailwind CSS v4 で構築した設計と実装"
description: "Astro 5の静的出力とTailwind CSS v4のデザインシステムで、ダークテーマのB2Bサービスサイトを12ページ構築。技術選定からデプロイまでの全工程を解説。"
pubDate: "2026-02-11"
updatedDate: "2026-02-11"
category: "web"
tags: ["Astro", "Tailwind CSS", "TypeScript", "Cloudflare Pages", "Web制作"]
author: "tinou"
---

# B2Bサービスサイトを Astro 5 + Tailwind CSS v4 で構築した設計と実装

---

## この記事で得られること

> **この記事を読むと、Astro 5 + Tailwind CSS v4 で本格的なB2Bサービスサイトを設計・構築する方法がわかります。**
>
> - Astro 5 の静的出力で「ゼロJS」の高速サイトを構築する手法
> - Tailwind CSS v4 の `@theme` ディレクティブでデザインシステムを一元管理する方法
> - IntersectionObserver + CSS keyframes で軽量なスクロールアニメーションを実装するパターン
> - Cloudflare Pages へのデプロイと SEO 対策の実践

---

## あなたもこんな悩みを抱えていませんか？

- 「フリーランスとしてサービスサイトを作りたいけど、WordPressは重いし管理が面倒…」
- 「ダークテーマで高級感のあるサイトを作りたいが、デザインシステムの設計がわからない…」
- 「React で SPA を作ると SEO が心配。でも静的サイトジェネレーターだと動きが出せない…」

**私もまさに同じ壁にぶつかっていました。**

---

## 私のストーリー：「とりあえず作る」から「設計して作る」へ

### Before：散らかったポートフォリオ

正直に言うと、これまで自分のサービスサイトを「ちゃんと」作ったことがありませんでした。

実績は6つ以上あるのに、それを見せる場所がない。技術力を示したいのに、技術力が伝わるサイトがない。

- GitHubのREADMEだけが「ポートフォリオ」だった
- デザインに自信がなく、テンプレートを探しては合わなくてやめる繰り返し
- 「サイトを作る時間があるなら、プロダクトを作りたい」と後回しにし続けた

**「いつか作る」は「永遠に作らない」と同義だ。**

そう気づいたのは、問い合わせの機会を何度か逃してからでした。

### 転機：Astro 5 + Tailwind CSS v4 の組み合わせ

転機になったのは、Astro 5 と Tailwind CSS v4 を個別のプロジェクトで使い始めたことです。

Astro のゼロJSアーキテクチャと Tailwind v4 の `@theme` ディレクティブが組み合わさると、**デザインシステムの定義からビルドまで一気通貫でシンプルになる**ことに気づきました。

「これなら、設計に時間をかけても実装が速い。」

その確信が、重い腰を上げるきっかけになりました。

### After：12ページ、1.46秒ビルド

結果として、以下のサイトを構築しました：

| 項目 | 数値 |
|------|------|
| 総ページ数 | 12ページ |
| ビルド時間 | 1.46秒 |
| クライアントJS | ほぼゼロ（React island のみ） |
| 構築期間 | 設計含め1日 |

<img src="/images/sal-hero.png" alt="Secure Auto Lab - Hero" />

**ダークテーマ + ゴールドアクセントの "Midnight Authority" というデザインコンセプトで、信頼感と専門性を表現するサイトが完成しました。**

---

## なぜこのアプローチを選んだのか

### 最初に考えた方法とその限界

まず検討したのは Next.js でした。普段のプロダクト開発で使い慣れていて、App Router + Server Components なら SEO も問題ない。

しかし、よく考えると：

- **サービスサイトに SSR は不要** — コンテンツはほぼ静的。更新頻度は月1回あるかないか
- **Next.js の機能が過剰** — ルーティング、ミドルウェア、API Routes...使わない機能のほうが多い
- **Vercel への依存** — Cloudflare Pages でホストしたいのに、Next.js は Vercel 最適化が進みすぎている

「フレームワークの都合に合わせるのではなく、要件に合ったツールを選ぶべきだ。」

この当たり前のことを、自分のサイトだからこそ意識的に実践しようと思いました。

### 発想の転換：「何を送らないか」で考える

Web パフォーマンスの本質は「何を送るか」ではなく **「何を送らないか」** です。

サービスサイトに必要なインタラクティブ要素を棚卸しすると：

- スクロールアニメーション → CSS + IntersectionObserver（フレームワーク不要）
- 数字カウンター → React island 1つで十分
- フォーム送信 → バニラJSで完結
- ページ遷移 → Astro View Transitions API

**JavaScript を「足す」のではなく、「必要な場所にだけ島のように置く」。** Astro のアイランドアーキテクチャは、まさにこの思想そのものでした。

### 決め手になった3つのポイント

最終的に Astro 5 + Tailwind CSS v4 に決めた理由：

1. **ゼロJSがデフォルト**: `.astro` ファイルはサーバーでHTMLに変換され、クライアントにJSを送らない。必要な部分だけ React island で hydrate できる
2. **Tailwind CSS v4 の `@theme`**: CSS カスタムプロパティベースのデザイントークンを CSS ファイル1つで定義。JavaScript の設定ファイルが不要になった
3. **Cloudflare Pages との親和性**: `output: 'static'` で dist/ を丸ごとデプロイ。CDNエッジから配信されるので世界中で高速

**「使わない技術を選ばない」という判断が、結果的に最もパフォーマンスの良いサイトを生んだ** — これが今回の最大の学びでした。

---

## 具体的な実装方法

### 全体アーキテクチャ

```
secure-auto-lab-portfolio/
├── src/
│   ├── layouts/BaseLayout.astro    ← 共通レイアウト（SEO, Fonts, JSON-LD）
│   ├── components/                 ← Astro コンポーネント（9個）
│   │   └── react/                  ← React islands（カウンター）
│   ├── data/                       ← TypeScript データファイル
│   ├── pages/
│   │   ├── index.astro             ← メインページ（9セクション）
│   │   ├── services/               ← サービス詳細（3ページ）
│   │   ├── works/                  ← 実績詳細（6ページ）
│   │   ├── contact.astro
│   │   └── privacy.astro
│   └── styles/global.css           ← デザインシステム（Tailwind v4）
├── public/images/works/            ← プロジェクトスクリーンショット
└── astro.config.mjs
```

12ページを生成するが、ルーティングの設定は一切不要。`pages/` ディレクトリにファイルを置くだけでAstroがファイルベースルーティングを処理する。

### Step 1: Tailwind CSS v4 によるデザインシステム

Tailwind CSS v4 最大の変更点は、設定ファイル（`tailwind.config.ts`）が不要になったこと。`@theme` ディレクティブで CSS ファイル内にデザイントークンを直接定義できる。

```css
/* src/styles/global.css */
@import "tailwindcss";

@theme {
  /* Midnight Authority palette */
  --color-bg: #0A0A0F;
  --color-bg-card: #111118;
  --color-bg-hover: #1A1A24;
  --color-gold: #C9A96E;
  --color-gold-light: #E8D5A8;
  --color-gold-dim: #C9A96E40;
  --color-text: #F0F0F2;
  --color-text-sub: #9898A8;
  --color-text-muted: #5A5A6E;
  --color-border: #2A2A38;

  /* Fonts */
  --font-heading: "Shippori Mincho B1", serif;
  --font-body: "Noto Sans JP", "Inter", sans-serif;
  --font-english: "Inter", sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* Animation easing */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
}
```

このアプローチの利点：

- **CSS カスタムプロパティ**なので、Tailwind のクラスからも `var()` からも参照可能
- **1ファイルで完結** — デザイントークンの変更はここだけ
- **`@theme` 内の変数は Tailwind のユーティリティクラスとして自動的に使える**（例: `text-[var(--color-gold)]`、`bg-[var(--color-bg-card)]`）

### Step 2: BaseLayout — SEO と構造化データ

全12ページで共有する BaseLayout に、SEO の基盤を集約した。

```astro
---
// src/layouts/BaseLayout.astro
import '../styles/global.css';
import Header from '../components/Header.astro';
import Footer from '../components/Footer.astro';

interface Props {
  title: string;
  description?: string;
  ogImage?: string;
}

const {
  title,
  description = 'AI統合・業務自動化・セキュアなシステム構築。',
  ogImage = '/og-image.png',
} = Astro.props;

const canonicalURL = new URL(Astro.url.pathname, Astro.site);
---

<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content={description} />
  <link rel="canonical" href={canonicalURL} />

  <!-- OGP -->
  <meta property="og:type" content="website" />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:image" content={new URL(ogImage, Astro.site)} />

  <!-- JSON-LD 構造化データ -->
  <script type="application/ld+json" set:html={JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Secure Auto Lab",
    "url": "https://secure-auto-lab.com",
    "service": [
      { "@type": "Service", "name": "業務自動化・AI統合" },
      { "@type": "Service", "name": "セキュアなシステム開発" },
      { "@type": "Service", "name": "アプリ・サービス開発" },
    ],
  })} />

  <title>{title}</title>
</head>
<body class="min-h-screen">
  <Header />
  <main><slot /></main>
  <Footer />
</body>
</html>
```

ポイント：

- `Astro.site` と `Astro.url` でカノニカルURLとOGP URLを自動生成
- `set:html` で JSON-LD を安全にインライン化
- `@astrojs/sitemap` との組み合わせで `sitemap-index.xml` も自動生成

### Step 3: スクロールアニメーション（ゼロ依存）

Framer Motion や GSAP を使わず、**IntersectionObserver + CSS keyframes** だけで実装した。

```css
/* CSS keyframes */
@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-on-scroll {
  opacity: 0;
}

.animate-on-scroll.visible {
  animation: fade-up 0.6s var(--ease-out-expo) forwards;
}

/* 子要素のスタガー（時差）アニメーション */
.animate-on-scroll.visible > .stagger:nth-child(1) { animation-delay: 0ms; }
.animate-on-scroll.visible > .stagger:nth-child(2) { animation-delay: 100ms; }
.animate-on-scroll.visible > .stagger:nth-child(3) { animation-delay: 200ms; }
```

```html
<!-- 使い方：親に animate-on-scroll、子に stagger -->
<div class="grid md:grid-cols-3 gap-8 animate-on-scroll">
  <div class="stagger">カード1</div>
  <div class="stagger">カード2</div>
  <div class="stagger">カード3</div>
</div>
```

```javascript
// BaseLayout.astro 内の script タグ（全ページで共有）
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.1 }
);

document.querySelectorAll('.animate-on-scroll').forEach((el) => {
  observer.observe(el);
});
```

この方式の利点：

- **ライブラリ依存ゼロ** — バンドルサイズへの影響なし
- **GPU アクセラレーション** — `transform` と `opacity` のみ使用で60fps
- **一度だけ発火** — `unobserve` で再アニメーションを防止

### Step 4: データ駆動のページ生成

実績やサービスのデータを TypeScript ファイルに分離し、複数のページから参照する設計にした。

```typescript
// src/data/projects.ts
export interface Project {
  slug: string;
  title: string;
  subtitle: string;
  tags: string[];
  image: string;
}

export const projects: Project[] = [
  {
    slug: 'event-platform',
    title: 'リアルタイムイベント体験基盤',
    subtitle: '40人規模イベントでAI顔認識・即時報酬・P2P送金を実現',
    tags: ['Next.js 15', 'Supabase', 'AWS Rekognition', 'QR/NFC'],
    image: '/images/works/event-platform.png',
  },
  // ... 他5件
];
```

このデータは、メインページの実績グリッド、サービス詳細ページの関連実績、個別の実績詳細ページの3箇所から参照される。データの変更が即座に全ページに反映される。

<img src="/images/sal-works-detail.png" alt="実績詳細ページ" />

### Step 5: Astro 設定とデプロイ

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://secure-auto-lab.com',
  output: 'static',
  integrations: [react(), sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
});
```

Tailwind CSS v4 は `@astrojs/tailwind` ではなく `@tailwindcss/vite` を使う。Astro 5 は内部で Vite を使っているため、Vite プラグインとして直接登録する。

Cloudflare Pages へのデプロイは、GitHub リポジトリを接続するだけ：

- **ビルドコマンド**: `npm run build`
- **出力ディレクトリ**: `dist`
- **フレームワーク**: Astro

push するたびに自動ビルド・デプロイが走る。

---

## 壁にぶつかった瞬間と乗り越え方

### 「フォントが変わらない…」最初の罠

Tailwind CSS v4 で `@theme` にフォントを定義したのに、見出しのフォントが適用されない。

原因は Tailwind v4 のフォント参照方法が v3 と異なること。v3 では `font-heading` のようなユーティリティクラスが自動生成されたが、v4 では CSS カスタムプロパティを直接参照する必要がある。

**解決策**: `font-[family-name:var(--font-heading)]` という書き方で、CSS のカスタムプロパティを Tailwind のクラスから直接参照する。

これは Tailwind v4 への移行で多くの人がハマるポイントだと思う。公式ドキュメントにも明確な移行ガイドがなく、試行錯誤が必要だった。

### スクリーンショット取得の戦い

各プロジェクトのスクリーンショットを取得する作業が予想以上に困難だった。

- **Vercel の認証壁** — チームデプロイメントに認証がかかっていて、Playwright でスクリーンショットが撮れない。カスタムドメイン経由でようやく解決
- **SPAの file:// プロトコル問題** — ローカルの `dist/index.html` を直接開いても React アプリが動かない。Vite の preview サーバーを立てて解決
- **GitHub Pages 未設定** — デプロイされていないプロジェクトはローカルサーバーで代替

自動化ツールを作っていても、環境の違いで動かないことはある。**「手元で動く」と「どこでも動く」は別物**だという教訓を改めて得た。

### この失敗から学んだこと

スクリーンショットの件で痛感したのは、**プロジェクトのデプロイ状態を普段から整理しておくことの大切さ**。

ポートフォリオを作る段階になって初めて「あのプロジェクト、どこにデプロイしてたっけ？」と調べ始めるのは非効率すぎる。

---

## この経験から得た3つの教訓

### 教訓1：「引き算の設計」が最強の武器

最初は「あの機能も入れたい、このアニメーションも」と足し算で考えがち。しかし、最終的に品質を左右したのは**何を入れないか**の判断だった。

- パララックス → 入れない（スクロールジャックは UX を損ねる）
- Lottie アニメーション → 入れない（バンドルサイズが増える）
- ダークモード切替 → 不要（サイト全体がダークモード）
- 価格表 → 入れない（問い合わせベースのほうがB2Bに合う）

引き算で残ったものが、本当に必要なものだった。

### 教訓2：デザインシステムは最初に決める

色・フォント・間隔のルールを最初に CSS の `@theme` で定義したことで、個別ページの実装が驚くほど速くなった。

「この見出しの色は何だっけ？」と迷う時間がゼロ。`var(--color-gold)` と書くだけ。デザイントークンへの投資は、ページ数が増えるほどリターンが大きくなる。

### 教訓3：Astro の「退屈さ」は美徳

Astro には Next.js のような Server Actions も、Remix のような Loader パターンもない。`.astro` ファイルに HTML を書き、必要ならデータを渡す。それだけ。

この「退屈さ」が、B2Bサービスサイトには最適だった。凝った仕組みがないからバグも少ない。ビルドが速い。デプロイが簡単。**フレームワークの都合に振り回されず、コンテンツと向き合える。**

---

## よくある質問（FAQ）

### Q1: Tailwind CSS v4 で v3 の `tailwind.config.ts` は使えますか？

A: 互換モードがありますが、新規プロジェクトなら `@theme` ディレクティブへの移行をお勧めします。CSS ファイル内で完結するため、設定ファイルの管理が不要になります。

### Q2: Astro で React コンポーネントを使う場合、SSR はどうなりますか？

A: `@astrojs/react` を追加すると、`.tsx` ファイルをインポートできます。`client:visible` ディレクティブを付けると、要素がビューポートに入った時に hydrate されます。今回はカウンターアニメーションだけ React island にしました。

### Q3: Cloudflare Pages のビルド設定は？

A: フレームワーク「Astro」を選択、ビルドコマンド `npm run build`、出力ディレクトリ `dist` だけです。カスタムドメインの設定も Cloudflare DNS と連携するので数クリックで完了します。

---

## まとめ：今日からできるアクションプラン

この記事で解説した内容をまとめます：

1. **技術選定**: B2Bサービスサイトには Astro 5 の静的出力が最適。必要な部分だけ React island で hydrate
2. **デザインシステム**: Tailwind CSS v4 の `@theme` で色・フォント・間隔を CSS 1ファイルに集約
3. **アニメーション**: IntersectionObserver + CSS keyframes でライブラリ不要の軽量アニメーション
4. **デプロイ**: Cloudflare Pages で GitHub 連携の自動デプロイ

**今日からできる具体的なアクション：**

> まずは `npm create astro@latest` で新規プロジェクトを作成し、`@tailwindcss/vite` を導入してみてください。`@theme` でカラーパレットを定義するだけで、デザインシステムの基盤が完成します。

---

## おわりに：伝えたかったこと

最後まで読んでいただき、ありがとうございました。

この記事を書いたのは、「サービスサイトを作りたいけど腰が重い」という過去の自分と同じ悩みを持つエンジニアの助けになりたかったからです。

正直、サービスサイトは「技術的に面白い」仕事ではありません。でも、自分の技術力と実績を世の中に見せる場所がなければ、機会は向こうからやってきません。

Astro 5 と Tailwind CSS v4 の組み合わせなら、設計に時間をかけても実装は速い。コンテンツに集中できる。そして何より、**自分が誇れるクオリティのサイトが作れる。**

あなたの挑戦を、心から応援しています。

---

## 参考リンク

- [Astro 5 公式ドキュメント](https://docs.astro.build/)
- [Tailwind CSS v4 ドキュメント](https://tailwindcss.com/docs)
- [Cloudflare Pages ドキュメント](https://developers.cloudflare.com/pages/)
- [Secure Auto Lab](https://secure-auto-lab.com)

---

**この記事が役に立ったら、ぜひシェアをお願いします！**

あなたのシェアが、同じ悩みを持つ誰かの助けになります。