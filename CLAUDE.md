# Article Publisher

## プロジェクトの目的

1つのMarkdown記事から **Note・Zenn・Qiita・自作ブログ** に自動投稿し、**SNS告知**（X・Bluesky・Misskey）で収益化を支援するCLIツール。

- **Note**: 内部API（httpx）で下書き作成。有料記事販売に対応
- **Zenn**: GitHubリポジトリ同期で自動デプロイ
- **Qiita**: REST API v2。収益化不可のため要約+ブログ誘導リンクのみ
- **Blog**: Astro + Cloudflare Pages。AdSense / Amazon Associate で収益化
- **OGP画像**: HTML+Playwrightで自動生成（4テーマ: default/purple/green/orange）

## 必須ルール

- **ソースコードのコメントは全て日本語で記載すること**
- **回答・解析情報も全て日本語で出力すること**
- Python 3.11+、ruff でフォーマット（line-length=100）
- Windows環境（cp932）を考慮する。Richのスピナーは `spinner="line"` を使用

## ディレクトリ構成

```
article-publisher/
├── articles/
│   ├── drafts/              # 下書き（ここで執筆）
│   ├── published/           # 投稿済み
│   ├── images/              # 記事用画像・OGP画像
│   └── templates/           # テンプレート・執筆ガイド
├── src/
│   ├── cli.py               # CLIエントリポイント（typer）
│   ├── config.py            # カテゴリ一元管理（単一ソース）
│   ├── transformer/         # 記事解析・プラットフォーム別変換
│   │   ├── article.py       # Articleデータクラス
│   │   └── converter.py     # プラットフォーム別コンバーター
│   ├── publishers/          # プラットフォーム別投稿
│   │   ├── note.py          # Note内部API（httpx）
│   │   ├── zenn.py          # Zenn（Git push）
│   │   ├── qiita.py         # Qiita REST API
│   │   └── blog.py          # Blog（ファイルコピー）
│   ├── announcer/           # SNS告知（X・Bluesky・Misskey）
│   └── tools/
│       └── ogp_generator.py # OGP画像生成（Playwright screenshot）
├── blog/                    # Astroブログ（Cloudflare Pages）
│   └── src/content/
│       ├── config.ts        # カテゴリ定義（src/config.pyから同期）
│       └── articles/        # ブログ記事（BlogConverterが配置）
└── zenn-content/            # Zenn用リポジトリ（自動git push）
```

## CLIコマンド

```bash
# 新規記事作成
python -m src.cli init --title "記事タイトル" --slug "article-slug"

# 検証
python -m src.cli validate articles/drafts/article-slug.md

# 全プラットフォームに投稿（OGP自動生成）
python -m src.cli publish articles/drafts/article-slug.md

# 特定プラットフォームのみ
python -m src.cli publish articles/drafts/article-slug.md -p note,zenn

# OGP画像のみ生成
python -m src.cli generate-ogp articles/drafts/article-slug.md --theme green

# カテゴリ一覧
python -m src.config

# カテゴリをblog config.tsに同期
python -m src.config sync

# スクリーンショット取得
python -m src.cli screenshot http://localhost:3000 -o articles/images/app.png
```

## カテゴリ管理

`src/config.py` が単一ソース。カテゴリ追加時は:
1. `src/config.py` の `BLOG_CATEGORIES` に追加
2. `python -m src.config sync` で `blog/src/content/config.ts` に自動反映

エイリアス対応あり（例: `tech` → `dev-tips`、`frontend` → `web`）。

## Note内部API

- ドラフト作成: `POST /api/v1/text_notes`
- 保存: `POST /api/v1/text_notes/draft_save?id={id}`
- アイキャッチ: `POST /api/v1/image_upload/note_eyecatch`（multipart: file, note_id, width=1920, height=1005）
- 必須ヘッダー: `X-Requested-With: XMLHttpRequest`
- HTML形式: `<pre><code>` でコードブロック、`<strong>` のみインライン。`<code>` / `<em>` / `<table>` / LaTeX は非対応

## 記事の執筆ルール

記事作成時は必ず以下を参照:
- `articles/templates/viral-article-template.md` - テンプレート
- `articles/templates/WRITING_GUIDE.md` - 執筆ガイド

### 売れる記事の7つの法則

| 法則 | 実践方法 |
|------|----------|
| 共感 | 読者の悩みを「あなたも〇〇で困っていませんか？」と代弁 |
| 権威 | 自分の実績・経験・失敗談を示す |
| 物語 | Before → 転機 → After のストーリー構造 |
| 具体 | 数字・コード・スクリーンショットで証明 |
| 感情 | 喜び・驚き・怒りを喚起（悲しみは避ける） |
| 価値 | 「これを読むと〇〇ができる」とベネフィットを明確に |
| 行動 | 「まずは〇〇してみよう」と次のステップを示す |

### 記事の必須構成

1. フック（最初の3行）→ 成果を数字で示して引き込む
2. ベネフィット → この記事で得られることを箇条書き
3. 共感 → 読者の悩みを言語化
4. Before → 自分も同じだった（失敗談）
5. 転機 → きっかけとの出会い
6. After → 成果を数字で証明
7. How → 具体的な実装（コード・画像）
8. まとめ → 今日からできるアクション
9. おわりに → 感情に訴えるクロージング

## スクリーンショット

画像の出力先は `articles/images/` に統一する。

```bash
# URLからスクリーンショット
python -m src.cli screenshot http://localhost:3000 -o articles/images/app.png

# フルページキャプチャ
python -m src.cli screenshot http://localhost:3000 --full-page -o articles/images/full.png

# 特定要素のみ
python -m src.cli screenshot http://localhost:3000 --selector ".dashboard" -o articles/images/dashboard.png
```

## デプロイ

- **Blog**: publishコマンド後、`blog/` で手動 `git push` → Cloudflare Pages 自動デプロイ
- **Zenn**: publishコマンドが自動 `git push` → Zenn 自動デプロイ
- **Note**: publishコマンドが内部APIで下書き保存（手動で公開）
- **Qiita**: publishコマンドがREST APIで投稿

## 注意事項

- 記事には必ず**ストーリー**と**感情**を入れる
- 技術的な内容だけでなく、**なぜ作ったか**の背景を書く
- 数字で成果を示す（「3日で解決」「50%削減」など）
- スクリーンショットは本プロジェクトのツールを使う
- 有料記事の場合、無料部分で「解決できそう」と確信させる
