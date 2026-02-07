# article-publisher

複数プラットフォーム（Note、Zenn、Qiita、自作ブログ）への記事自動投稿システム。

## 機能

- **統一フォーマット**: 1つのMarkdownファイルから全プラットフォームへ変換・投稿
- **プラットフォーム対応**:
  - Qiita (REST API)
  - Zenn (GitHub連携)
  - Note (Playwright ブラウザ自動化)
  - 自作ブログ (Astro + Cloudflare)
- **SNS告知**: 投稿後にX/Bluesky/Misskeyへ自動告知
- **収益化**: AdSense、アフィリエイト、有料記事対応

## インストール

```bash
# プロジェクトをクローン
git clone https://github.com/tinou/article-publisher.git
cd article-publisher

# Python依存関係をインストール
pip install -e .

# Playwright をインストール（Note投稿用）
playwright install chromium

# ブログ依存関係をインストール
cd blog && npm install && cd ..
```

## 設定

1. `.env.example` を `.env` にコピー
2. 各プラットフォームのAPIキー/認証情報を設定

```bash
cp .env.example .env
# .env を編集
```

## 使い方

### 新規記事を作成

```bash
python -m publisher init --title "記事タイトル" --slug "article-slug"
```

### 記事を検証

```bash
python -m publisher validate articles/drafts/article-slug.md
```

### 記事をプレビュー（ドライラン）

```bash
python -m publisher publish articles/drafts/article-slug.md --dry-run
```

### 記事を投稿

```bash
# 全プラットフォームに投稿
python -m publisher publish articles/drafts/article-slug.md

# 特定のプラットフォームのみ
python -m publisher publish articles/drafts/article-slug.md --platforms qiita,zenn

# SNS告知なしで投稿
python -m publisher publish articles/drafts/article-slug.md --no-announce
```

### プラットフォーム別に変換のみ

```bash
python -m publisher convert articles/drafts/article-slug.md zenn -o output.md
```

## ブログ開発

```bash
cd blog

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview
```

## ディレクトリ構造

```
article-publisher/
├── articles/
│   ├── published/      # 投稿済み記事
│   ├── drafts/         # 下書き
│   └── templates/      # Jinja2テンプレート
├── src/
│   ├── transformer/    # 記事変換ロジック
│   ├── publishers/     # プラットフォーム別投稿
│   ├── announcer/      # SNS告知
│   └── cli.py          # CLIインターフェース
├── blog/               # Astroブログ
└── zenn-content/       # Zenn用リポジトリ
```

## 記事フォーマット

```yaml
---
title: "記事タイトル"
slug: "article-slug"
description: "記事の説明"
tags: [tag1, tag2]
created_at: 2026-02-07

platforms:
  note:
    enabled: true
    price: 0          # 0=無料, 100-50000=有料
  zenn:
    enabled: true
    emoji: "📝"
    topics: [nextjs, typescript]
  qiita:
    enabled: true
  blog:
    enabled: true

announcement:
  enabled: true
  platforms: [twitter, bluesky, misskey]
---

# 記事本文

ここに記事を書きます。
```

## ライセンス

MIT
