# Article Publisher - Claude 作業指示

## プロジェクト概要

複数プラットフォーム（Note・Zenn・Qiita・自作ブログ）への技術記事自動投稿システム。

## 記事を書くときのルール

### 必ず参照するファイル

記事を作成・編集する際は、以下のテンプレートとガイドを**必ず参照**すること：

1. **記事テンプレート**: `articles/templates/viral-article-template.md`
2. **執筆ガイド**: `articles/templates/WRITING_GUIDE.md`

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

```
1. フック（最初の3行）→ 成果を数字で示して引き込む
2. ベネフィット → この記事で得られることを箇条書き
3. 共感 → 読者の悩みを言語化
4. Before → 自分も同じだった（失敗談）
5. 転機 → きっかけとの出会い
6. After → 成果を数字で証明
7. How → 具体的な実装（コード・画像）
8. まとめ → 今日からできるアクション
9. おわりに → 感情に訴えるクロージング
```

## スクリーンショットの撮り方

記事に画像を埋め込むときは、**必ず以下のツールを使用**すること。
**出力先は `articles/images/` に統一**する。

### 基本コマンド

```bash
cd C:\Users\tinou\Projects\article-publisher

# URLからスクリーンショット
python -m publisher screenshot http://localhost:3000 -o articles/images/app.png

# フルページキャプチャ
python -m publisher screenshot http://localhost:3000 --full-page -o articles/images/full.png

# 特定要素のみキャプチャ
python -m publisher screenshot http://localhost:3000 --selector ".dashboard" -o articles/images/dashboard.png

# モバイルサイズ
python -m publisher screenshot http://localhost:3000 --width 375 --height 812 -o articles/images/mobile.png
```

### TSX/JSXコンポーネントの画像化

```bash
# TSXコンポーネントを画像化
python -m publisher screenshot ./components/Card.tsx -o articles/images/card.png

# propsを指定してレンダリング
python -m publisher screenshot ./components/Card.tsx \
    --props '{"title": "Hello", "description": "World"}' \
    -o articles/images/card-with-props.png
```

### HTMLファイルの画像化

```bash
python -m publisher screenshot ./page.html -o articles/images/page.png
```

### 画像の保存先（統一ルール）

| 種類 | パス |
|------|------|
| 記事用画像 | `articles/images/` |
| 下書き | `articles/drafts/` |
| 投稿済み | `articles/published/` |

### 記事内での埋め込み

```markdown
![ダッシュボード画面](./images/dashboard.png)
```

## CLIコマンド一覧

```bash
# 新規記事作成（テンプレートから）
python -m publisher init --title "記事タイトル" --slug "article-slug"

# 記事の検証
python -m publisher validate articles/drafts/article-slug.md

# プレビュー（ドライラン）
python -m publisher publish articles/drafts/article-slug.md --dry-run

# 投稿
python -m publisher publish articles/drafts/article-slug.md

# 特定プラットフォームのみ
python -m publisher publish articles/drafts/article-slug.md --platforms qiita,zenn

# プラットフォーム別に変換のみ
python -m publisher convert articles/drafts/article-slug.md zenn -o output.md
```

## ディレクトリ構造

```
article-publisher/
├── articles/
│   ├── drafts/           # 下書き（ここで執筆）
│   ├── published/        # 投稿済み
│   ├── images/           # 記事用画像（スクリーンショット保存先）
│   └── templates/        # テンプレート・ガイド
├── src/
│   ├── transformer/      # 記事変換
│   ├── publishers/       # 投稿機能
│   ├── announcer/        # SNS告知
│   └── tools/            # スクリーンショット等
├── blog/                 # Astroブログ
└── zenn-content/         # Zenn連携
```

## 記事作成ワークフロー

1. `python -m publisher init` で新規記事作成
2. `articles/templates/` のテンプレートを参考に執筆
3. スクリーンショットは `python -m publisher screenshot` で取得
4. `python -m publisher validate` で検証
5. `python -m publisher publish --dry-run` でプレビュー
6. `python -m publisher publish` で投稿

## 注意事項

- 記事には必ず**ストーリー**と**感情**を入れる
- 技術的な内容だけでなく、**なぜ作ったか**の背景を書く
- 数字で成果を示す（「3日で解決」「50%削減」など）
- スクリーンショットは本プロジェクトのツールを使う
- 有料記事の場合、無料部分で「解決できそう」と確信させる
