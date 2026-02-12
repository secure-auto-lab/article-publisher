# 売れる技術記事の書き方ガイド

## 🎯 記事が売れる/PVが伸びる7つの法則

| 法則 | 説明 | 実践方法 |
|------|------|----------|
| **共感** | 読者の痛みを代弁する | 「あなたも〇〇で困っていませんか？」 |
| **権威** | なぜ自分が書けるのか | 実績・経験・失敗談を示す |
| **物語** | Before→転機→Afterの構造 | 自分のストーリーを語る |
| **具体** | 数字・コード・画像で証明 | 「3日で解決」「50%削減」 |
| **感情** | 喜び・驚き・怒りを喚起 | 悲しみは避ける（共有されにくい） |
| **価値** | ベネフィットを明確に | 「これを読むと〇〇ができる」 |
| **行動** | 次のステップを示す（CTA） | 「まずは〇〇してみよう」 |

---

## 📝 タイトルのパターン集

### 成果訴求型（最も効果的）
```
- 「〇〇を△日で解決した話」
- 「〇〇で月△万円稼いだ全記録」
- 「開発時間を90%削減した〇〇の導入方法」
- 「1週間で〇〇をマスターした学習法」
```

### 網羅型（SEO向き）
```
- 「【完全版】〇〇の教科書」
- 「【2026年最新】〇〇入門ガイド」
- 「〇〇の全て｜初心者から実践まで」
```

### 体験談型（共感を呼ぶ）
```
- 「エンジニア歴△年の私が〇〇した結果」
- 「〇〇で挫折した私が△△で復活した話」
- 「チーム開発で〇〇に気づいた話」
```

### 警告型（クリック率が高い）
```
- 「〇〇を知らないと損する理由」
- 「やってはいけない〇〇の落とし穴」
- 「99%のエンジニアが間違えている〇〇」
```

### 連載型（継続読者を獲得）
```
- 「【連載】〇〇を作るまでの全記録」
- 「〇〇開発日記 Day 1」
- 「〇〇シリーズ #1: 環境構築編」
```

---

## 💰 有料記事の価格設定

| 価格帯 | 向いているコンテンツ | 購入ハードル |
|--------|----------------------|--------------|
| 100-300円 | Tips・小ネタ・チートシート | 低（衝動買い） |
| 500-1000円 | チュートリアル・解説記事 | 中（最も売れやすい） |
| 1500-3000円 | 完全ガイド・ソースコード付き | やや高 |
| 5000円以上 | 書籍レベル・コンサル的価値 | 高（信頼が必要） |

### 有料化のコツ

1. **無料部分で「解決できそう」と確信させる**
   - 問題の本質を言語化
   - 解決の方向性を示す
   - 具体的な成果を見せる

2. **有料部分には「時短」の価値を**
   - 完全なソースコード
   - コピペで使えるテンプレート
   - 実際に動くデモ

3. **「時間をお金で買う」フレーミング**
   - 「この記事を読めば10時間の試行錯誤を省ける」
   - 「私が3ヶ月かけて得た知見を1記事に凝縮」

---

## 📊 バズる感情の種類

### 共有されやすい感情（積極的に使う）
- ✅ **驚き**: 「まさかの結果に…」
- ✅ **喜び**: 「ついに解決！」
- ✅ **怒り（正当な）**: 「この仕様はおかしい」
- ✅ **興味**: 「こんな方法があったのか」
- ✅ **感動**: 「チームで乗り越えた」

### 共有されにくい感情（避ける）
- ❌ **悲しみ**: 「失敗して落ち込んだ」だけで終わる
- ❌ **不安**: 解決策なしの問題提起
- ❌ **退屈**: 淡々とした技術説明のみ

---

## 📐 記事の構成テンプレート

### 基本構成（推奨）

この記事は **ブログ・Note・Zenn・Qiita** に同時投稿されます。
各プラットフォーム向けに自動変換されます。
- **Note版**: 技術セクション（🔧実装、❓FAQ、📚参考リンク）が自動除去 → ストーリー記事
- **Zenn版**: ストーリー系セクションが自動除去 → 技術記事
- **Qiita版**: `<!-- qiita-section -->` マーカー内を抽出 → 自立した実用記事
→ 「💭考え方」「🧱壁と乗り越え方」「🎓教訓」が Note版の核になります。

```
1. フック（最初の3行で心を掴む）
   ├── 成果を示す数字
   ├── 読者の悩みを言語化
   └── ベネフィットの約束

2. 導入（読む価値を伝える）
   ├── この記事で得られること（箇条書き）
   └── 想定読者

3. 共感パート（Before）
   ├── 読者の悩みを代弁
   └── 自分も同じだったエピソード

4. ストーリー（転機）
   ├── きっかけとの出会い
   └── その瞬間の思考プロセスを丁寧に

5. 成果（After）
   ├── 成果を数字で示す
   └── 感情を込めた振り返り

6. 💭 なぜこのアプローチを選んだのか ← Note版の核①
   ├── 最初に考えた方法とその限界
   ├── 発想の転換：どう視点を変えたか
   └── 決め手になったポイント

7. 🔧 具体的な実装方法 ← ブログ向け（Note版では除去）
   ├── アーキテクチャ
   ├── Step 1, 2, 3... のコード・スクリーンショット
   └── ポイント解説

7.5. 💡 実践Tips・よくあるエラーと解決法 ← Qiita版の核
     <!-- qiita-section --> で囲む
     ├── よくあるエラーメッセージと解決法
     ├── 環境構築の手順（コピペで動くレベル）
     └── パフォーマンス改善のTips

8. 🧱 壁にぶつかった瞬間と乗り越え方 ← Note版の核②
   ├── 絶望の瞬間（感情を込める）
   ├── 突破口の発見（思考プロセス）
   └── 失敗から学んだこと

9. 🎓 この経験から得た教訓 ← Note版の核③
   ├── 技術を超えた汎用的な学び
   └── 読者が自分の仕事に活かせる知見

10. まとめ（CTA）
    ├── 要点の振り返り
    ├── 今日からできるアクション
    └── シェアのお願い

11. おわりに（感情）
    └── なぜこの記事を書いたか
```

### Note版で残るセクションを意識する

以下はNote変換後も残るため、**十分な分量と感情**を込めて書くこと：

| セクション | 役割 | 目安文字数 |
|-----------|------|-----------|
| 悩み・共感 | 読者を引き込む | 300-500字 |
| Before/転機/After | メインストーリー | 800-1500字 |
| なぜこのアプローチか | 思考プロセス | 600-1000字 |
| 壁と乗り越え方 | ドラマ・感情 | 500-800字 |
| 教訓 | 持ち帰れる学び | 400-600字 |
| まとめ・おわりに | 行動喚起・感動 | 300-500字 |

**合計 3000-5000字** がNote版の目安。コードなしでも読み応えのある記事になります。

---

## ✅ 公開前チェックリスト

### タイトル
- [ ] 数字が含まれているか
- [ ] 成果・ベネフィットが伝わるか
- [ ] 30文字以内で収まっているか
- [ ] 検索されそうなキーワードが入っているか

### 導入部（最初の3行）
- [ ] 読者の悩みに触れているか
- [ ] 読み進めたくなる「フック」があるか
- [ ] ベネフィットを約束しているか

### 本文
- [ ] Before → 転機 → After の流れがあるか
- [ ] 具体的な数字・コード・画像があるか
- [ ] 自分だけの一次情報（体験）があるか

### Note向け（ストーリー・考え方）
- [ ] 「なぜこのアプローチを選んだのか」が十分に書かれているか
- [ ] 「壁にぶつかった瞬間」に感情とドラマがあるか
- [ ] 「教訓」が技術を超えた汎用的な内容になっているか
- [ ] コードを読まなくても考え方・背景が伝わるか

### Qiita向け（実践Tips）
- [ ] `<!-- qiita-section -->` マーカーで実用セクションを囲んでいるか
- [ ] マーカー内だけで自立した記事として成立するか（ブログへの誘導感がないか）
- [ ] エラー解決・手順・Tipsなど検索ユーザーに役立つ内容か
- [ ] コピペで動くコード例が含まれているか

### 感情
- [ ] 共感できるエピソードがあるか
- [ ] ポジティブな感情（喜び・驚き）で終わっているか
- [ ] 読後感が良いか

### 行動喚起
- [ ] 次のステップが明確か
- [ ] シェアのお願いがあるか
- [ ] コメント・質問の受付を示しているか

### SEO
- [ ] descriptionが魅力的か
- [ ] タグが適切か
- [ ] 見出し（h2, h3）が論理的か

---

## 📚 参考になる記事の特徴

### Zenn で人気の記事
- 技術的に深い内容
- 図解・コード例が豊富
- 結論が明確

### Note で売れる記事
- ストーリーがある
- 読者の悩みへの共感
- 「時短」「効率化」の価値

### Qiita でバズる記事
- トレンド技術のキャッチアップ
- エラー解決の詳細記録
- ベストプラクティスの共有

---

## 🚀 投稿方法

### 対応プラットフォーム

| プラットフォーム | 方式 | アカウント | 収益化 |
|-----------------|------|-----------|--------|
| **Blog** | Astro + Cloudflare Pages | blog.secure-auto-lab.com | Amazon Associate / AdSense |
| **Note** | 内部API (httpx) | engineer@secure-auto-lab.com | 有料記事販売 |
| **Zenn** | GitHub連携（自動デプロイ） | secure_auto_lab | バッジ（投げ銭） |
| **Qiita** | REST API v2 | secure-auto-lab | 集客（自立した実用記事） |
| **X** | Twitter API v2 (Free Tier) | @secure_auto_lab | 集客（直接収益なし） |
| **Bluesky** | AT Protocol | @secure-auto-lab | 集客 |
| **Misskey** | REST API | @secure_auto_lab | 集客 |

### CLIコマンド

```bash
cd C:\Users\tinou\Projects\article-publisher

# 1. 新規記事作成
python -m src.cli init --title "記事タイトル" --slug "article-slug"

# 2. 検証
python -m src.cli validate articles/drafts/article-slug.md

# 3. プレビュー（dry-run）
python -m src.cli publish articles/drafts/article-slug.md --dry-run

# 4. 全プラットフォームに投稿（Note/Zenn投稿時はOGP画像を自動生成）
python -m src.cli publish articles/drafts/article-slug.md

# 5. OGPテーマを指定して投稿
python -m src.cli publish articles/drafts/article-slug.md --ogp-theme purple

# 6. 特定プラットフォームのみ
python -m src.cli publish articles/drafts/article-slug.md -p note,zenn

# 7. OGP画像のみ生成
python -m src.cli generate-ogp articles/drafts/article-slug.md --theme green

# 8. SNS告知のみ（既存記事）
python -m src.cli announce articles/drafts/article-slug.md --urls '{"blog": "https://blog.secure-auto-lab.com/..."}'

# 9. X投稿テスト
python -m src.cli test-announce twitter -m "テスト投稿"

# 10. Noteログインテスト
python -m src.cli note-login

# 11. スクリーンショット取得
python -m src.cli screenshot http://localhost:3000 -o articles/images/app.png
```

### 投稿フロー

```
記事執筆（Markdown）
  ↓
python -m src.cli validate → 検証
  ↓
python -m src.cli publish --dry-run → プレビュー
  ↓
python -m src.cli publish → 一括投稿
  │
  ├── OGP画像自動生成 (1200x630, 4テーマ: default/purple/green/orange)
  │     → articles/images/{slug}-ogp.png
  │
  ├── Blog: 記事 → blog/src/content/articles/
  │         OGP画像 → blog/public/images/{slug}-ogp.png
  │         ※ blog/ で git push → Cloudflare Pages デプロイ
  │
  ├── Note: 内部API → 下書き保存
  │         OGP画像はブログURL参照 (<figure><img>)
  │
  ├── Zenn: 記事 → zenn-content/articles/
  │         OGP画像 → zenn-content/images/{slug}-ogp.png
  │         → 自動 git push → Zenn デプロイ
  │
  ├── Qiita: REST API → 実践Tips抽出（自立した技術記事）
  │
  └── SNS告知: X → Bluesky → Misskey (時間差)
```

### OGP画像の自動添付

Note・Zenn投稿時は **OGP画像が自動生成** され、各プラットフォームに配信されます。

| プラットフォーム | OGP画像の扱い |
|-----------------|--------------|
| **Blog** | `blog/public/images/{slug}-ogp.png` にコピー（公開URL提供元） |
| **Note** | ブログURL参照: `<figure><img src="https://blog.secure-auto-lab.com/images/{slug}-ogp.png">` |
| **Zenn** | `zenn-content/images/{slug}-ogp.png` にコピー → 記事先頭に `![OGP](/images/{slug}-ogp.png)` |
| **Qiita** | 自立した技術記事のため不要（canonical URLでSEO重複回避） |

OGPテーマ: `default`(ブルー), `purple`, `green`, `orange`

### Blog記事内の画像パス（重要）

Astro のコンテンツコレクションでは、Markdown 内の画像パス（`![](path)`）をローカルファイルとして解決しようとします。
**相対パス（`./images/foo.png`）や絶対パス（`/images/foo.png`）を使うと、ファイルが見つからない場合にビルドエラーになります。**

```markdown
# NG - 画像が blog/public/images/ に存在しないとビルドエラー
![screenshot](./images/sal-hero.png)

# OK - blog/public/images/ に画像を配置し、/images/ パスで参照
![screenshot](/images/sal-hero.png)
```

**手順:**
1. 画像を `blog/public/images/` に配置する（gitignore されている場合は `git add -f`）
2. 記事内では `/images/ファイル名.png` パスで参照する（`./` 相対パスは NG）
3. **画像が `public/images/` に存在しないとビルドエラーになる** — 必ず画像を先に配置すること
4. OGP画像は BlogPublisher が自動コピーするが、記事内画像は手動コピーが必要

### Blogのデプロイ

```bash
cd C:\Users\tinou\Projects\article-publisher\blog

# publishコマンドで記事・OGP画像が配置された後
git add src/content/articles/{slug}.md public/images/{slug}-ogp.png
git commit -m "Add article: タイトル"
git push origin main
# → Cloudflare Pages が自動デプロイ
```

### プラットフォーム別の注意事項

**Blog**
- Astroの `blog/src/content/articles/` に記事を配置
- OGP画像は `blog/public/images/` に自動コピー
- Amazon Associateリンクは `{{affiliate:ASIN}}` 記法で埋め込み

**Note**
- 内部API方式（httpx直接呼び出し、Playwrightはログインのみ）
- 有料記事は `price: 500` で設定（500-1000円が売れ筋）
- `:::note-only` で有料部分を囲む
- 初回は `python -m src.cli note-login` でログインテスト
- OGP画像はブログの公開URLから参照

**Zenn**
- slugは12-50文字（英数字・ハイフン・アンダースコア）
- topicsは1-5個
- リポジトリ: `secure-auto-lab/zenn-content`
- publishコマンドが自動でgit pushしてデプロイ
- OGP画像は `zenn-content/images/` に自動コピー

**Qiita**
- `<!-- qiita-section -->` マーカー内の実用Tipsを抽出し、自立した技術記事として投稿
- 末尾にブログへの控えめな関連情報リンク + canonical URLでSEO重複回避
- マーカーがない場合はストーリー系を除去した技術内容をフォールバック
- 検索経由の初級〜中級エンジニア向け：エラー解決・備忘録・入門記事が効果的
- REST API v2使用、アクセストークンは `.env` に設定

**X (@secure_auto_lab)**
- Free Tier: 投稿のみ（月間制限あり）
- 280文字制限
- 共有アプリ（nami-auto-posts）のOAuth認証
- トークン再発行: `python x_auth.py`

### Zenn単独投稿（Git直接）

```bash
cd C:\Users\tinou\Projects\zenn-content

# 記事ファイルを articles/ に作成（Zennフォーマット）
# OGP画像がある場合は images/ にも配置
git add articles/slug-name.md images/slug-name-ogp.png
git commit -m "Add article: タイトル"
git push origin main
# → Zennが自動デプロイ（1-2分）
```

---

## 🔗 Sources

- [note有料記事での稼ぎ方](https://www.sungrove.co.jp/note-paid-article/)
- [トレンド入りする記事を書く技術](https://zenn.dev/collabostyle/articles/858875b235cdd6)
- [バズる記事の書き方｜シェアしたくなる5つの心理](https://medifund.jp/marketing/buzz-article/)
- [なぜバズるのか？成功コンテンツの解説](https://tinect.jp/blog/contents-why-the-buzz/)
