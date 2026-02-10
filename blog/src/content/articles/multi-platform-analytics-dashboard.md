---
title: "個人ブログ・Zenn・Note・Qiita＋複数LPを1つのダッシュボードで一括管理する仕組みを作った"
description: "5つのプラットフォームと複数のLPのアクセス解析を1画面に集約するReactダッシュボードを構築。GA4 Data API・Search Console・Cloudflare・各プラットフォームAPIを統合し、GitHub Actionsで毎朝自動更新する仕組みの設計と実装を解説します。"
pubDate: "2026-02-11"
updatedDate: "2026-02-11"
category: "dev-tips"
tags: ["GA4", "React", "GitHub Actions", "アクセス解析", "ダッシュボード"]
author: "tinou"
---

# 個人ブログ・Zenn・Note・Qiita＋複数LPを1つのダッシュボードで一括管理する仕組みを作った

---

## この記事で得られること

> **この記事を読むと、複数プラットフォームのアクセスデータを1つのダッシュボードに集約する方法がわかります。**
>
> - GA4 Data APIで複数サイト・LPのデータを1つのプロパティから分離取得する設計パターン
> - GitHub Actionsで毎朝自動取得→JSON→Reactダッシュボードの構築フロー
> - LP追加が「配列に1行足すだけ」で済む拡張性のある設計

---

## あなたもこんな悩みを抱えていませんか？

- 「GA4を開いて、Search Consoleを開いて、Zennのダッシュボードを見て、Qiitaのマイページを確認して…この往復が毎日地味にストレス」
- 「ブログだけでなくLPも運用し始めたけど、LP別のPV・CVRをまとめて見る場所がない」
- 「NoteはPVすら外部から取得できなくて、エンゲージメントの全体像がつかめない」

**私も以前は、まったく同じ状況でした。**

---

## 私のストーリー：バラバラの管理画面を行き来する日々からの脱出

### Before：5つのタブを開く毎朝のルーティン

正直に告白します。技術ブログを4つのプラットフォーム（個人ブログ・Zenn・Note・Qiita）に同時投稿する仕組みは以前作りました。投稿自動化は解決した。

しかし、**投稿した後の「効果測定」が完全に放置状態**でした。

毎朝やっていたことを書き出すと：

1. GA4を開いてブログのPVを確認
2. Search Consoleを開いて検索クエリをチェック
3. Zennのダッシュボードでいいね・PVを確認
4. Qiitaのマイページでストック数とPVを見る
5. Noteはダッシュボードにログインして手動確認

**5つのサービスを行き来して、頭の中で数字を合算する。** これを毎日やっていました。しかもLPを2つ追加してからは、そのPV・CVRも見たくなって、管理画面の行き来はさらに増えていきました。

「全体で今週何PVなのか」という単純な質問に答えるのに、10分以上かかっていたのです。

### 転機：「投稿自動化の次は分析自動化」という気づき

ある日、記事の投稿CLIを改修していたとき、ふと気づきました。

**「投稿を自動化したなら、分析も自動化すべきでは？」**

APIが公開されているプラットフォームならデータ取得は自動化できる。GA4にはData APIがある。Search ConsoleにもAPIがある。Cloudflareにはエッジレベルのアクセスデータがある。

これらを1つのスクリプトで毎朝取得して、JSONに書き出して、Reactダッシュボードで可視化すれば——**5つのタブを開く作業がゼロになる。**

その瞬間、頭の中で設計が組み上がりました。

### After：1画面で全データを横断比較

結果として、以下を実現しました：

| 項目 | Before | After |
|------|--------|-------|
| 毎朝の確認時間 | 10分以上（5サービス行き来） | 30秒（1画面） |
| LP追加時の作業 | GA4設定＋ダッシュボード改修 | 配列に1行追加 |
| データ更新 | 手動 | 毎朝5:51に自動取得 |
| 運用コスト | 無料 | 無料（GitHub Actions無料枠内） |

![ダッシュボード Overview](/images/dashboard-overview.png)

**8つのタブで全データを網羅するダッシュボードが、毎朝自動で更新される。** たったこれだけで、データ分析のストレスが消えました。

---

## なぜこのアプローチを選んだのか

実は、最初から今の形を思い描いていたわけではありません。

### 最初に考えた方法とその限界

まず検討したのは**Google Looker Studio（旧Data Studio）**でした。GA4やSearch Consoleとの連携が標準で、グラフも自動生成してくれる。

しかし、実際に試してみると：

- **Zenn・Note・QiitaのデータはLookerに入らない。** これらのAPIからのデータを統合するにはBigQueryを経由する必要があり、個人プロジェクトには大げさすぎる。
- **LP別のフィルタリングが柔軟でない。** LP追加のたびにLookerのレポートを手動で編集する必要がある。
- **デザインのカスタマイズが限定的。** ダッシュボードの見た目にこだわりたかった。

「全プラットフォームのデータを1つに統合する」という要件に対して、Looker Studioは「Google系データの可視化」に特化しすぎていたのです。

### 発想の転換：JSON＋Reactというシンプルな選択

行き詰まった時、視点を変えました。

**「データを集める部分」と「表示する部分」を完全に分離すればいい。**

- データ取得：Node.jsスクリプトで各APIからJSONに集約（1日1回）
- 表示：そのJSONを読むだけのReactダッシュボード

この構成なら、**新しいプラットフォームを追加する＝JSONのフィールドを1つ増やす＋Reactに表示コンポーネントを足す**だけ。GoogleのエコシステムにもAWSにも依存しない。

そしてデータ取得を**GitHub Actionsで毎朝実行→JSON commitでGitに蓄積**すれば、データの履歴もGit logで追える。インフラコストはゼロ。

### 決め手になった3つのポイント

1. **拡張性**: LP追加が「配列に1行追加」で済む設計にできる
2. **コスト**: GitHub Actionsの無料枠（月2,000分）で十分に収まる
3. **可搬性**: JSONファイルとReact JSXだけなので、将来AstroやNext.jsに組み込むのも容易

**「最小の構成で最大の柔軟性」** を実現できる——これが決め手でした。

---

## 具体的な実装方法

### 全体アーキテクチャ

```
┌─ Google APIs ───────────────────────────┐
│  GA4 Data API (Blog)                    │
│  GA4 Data API (LP×N) ← pagePath/hostname│
│  GA4 Data API (Zenn)  ← トラッキングID  │
│  Search Console API                     │
└─────────────────────────────────────────┘
           ↓
┌─ Platform APIs ─────────────────────────┐
│  Zenn API     (非公式・認証不要)         │
│  Note API     (非公式・認証不要)         │
│  Qiita API v2 (公式・トークン必要)       │
└─────────────────────────────────────────┘
           ↓
┌─ Infrastructure ────────────────────────┐
│  Cloudflare GraphQL API                 │
│  Sitemap.xml                            │
└─────────────────────────────────────────┘
           ↓
   fetch-analytics-v2.mjs (Node.js)
           ↓
   analytics-data.json
           ↓
   dashboard-v2.1.jsx (React)
```

GitHub Actionsで毎朝5:51 JSTにデータ取得→JSON出力→commit & push。ダッシュボードはそのJSONを読むだけなので、静的ホスティングでも動きます。

### Step 1: LP追加が1行で済む設計 — LP_SITES配列

最も工夫したのが、LP定義の配列パターンです。新しいLPを追加するとき、コードのあちこちを修正するのは絶対に避けたかった。

```javascript
// fetch-analytics-v2.mjs — LP定義
const LP_SITES = [
  {
    key: "lp_b2b",
    name: "B2Bサービス LP",
    pagePathFilter: "/services/",       // パスで分離
  },
  {
    key: "lp_lilith",
    name: "毒舌メイド・リリス LP",
    hostnameFilter: "project-lilith.secure-auto-lab.com",  // ホスト名で分離
  },
  {
    key: "lp_nami",
    name: "七海なみ LP",
    hostnameFilter: "nami.secure-auto-lab.com",
  },
  // ↑ ここに足すだけ。ダッシュボード側も同じ配列構造。
];
```

データ取得スクリプトはこの配列をループして、LP1つにつきGA4 APIを1回呼びます。ダッシュボード側も同じ`LP_SITES`配列をベースにタブ・チャート・比較テーブルを動的生成します。

**3つ目のLPを追加する作業はコピペ3行で終わりました。**

### Step 2: GA4の`dimensionFilter`で同一プロパティからLP分離

LPごとに別のGA4プロパティを立てるのは管理が面倒すぎます。代わりに、Blog・LP群をすべて同じGA4プロパティに入れて、GA4 Data APIの`dimensionFilter`で分離する方式を採りました。

```javascript
// GA4 API呼び出し時にフィルタを注入
async function fetchGA4(auth, propertyId, label, pagePathFilter, hostnameFilter) {
  let dimensionFilter;
  if (pagePathFilter) {
    dimensionFilter = {
      filter: {
        fieldName: "pagePath",
        stringFilter: { matchType: "CONTAINS", value: pagePathFilter },
      },
    };
  } else if (hostnameFilter) {
    dimensionFilter = {
      filter: {
        fieldName: "hostName",
        stringFilter: { matchType: "EXACT", value: hostnameFilter },
      },
    };
  }
  // ...以降、dimensionFilterを使ってrunReportを実行
}
```

LPが同一ドメインのサブディレクトリなら`pagePath`フィルタ、別サブドメインなら`hostName`フィルタ。**API側のクエリだけでLPを分離できる**ので、GA4の管理画面で何か設定する必要はありません。

### Step 3: プラットフォームごとの「取れるデータ」差分への対処

各プラットフォームのAPI状況を整理すると、取得できるデータに大きな差があります。

| プラットフォーム | PV | いいね系 | フォロワー | API認証 |
|---|---|---|---|---|
| Blog | GA4 | — | — | サービスアカウント |
| LP | GA4 | — | — | サービスアカウント |
| Zenn | GA4連携 | API | API | 不要 |
| Note | 取得不可 | API | API | 不要 |
| Qiita | API | API | API | トークン |

**NoteだけPVが取れない**のが痛いポイントです。Noteのダッシュボードはログイン後にしか見られず、公式・非公式APIともにPVを返しません。

対策として、Noteではいいね数・コメント数・フォロワー数を「エンゲージメント指標」として扱い、PV欄は表示しない設計にしました。

**ZennのGA4連携がキーポイント**で、Zennのアカウント設定画面からGA4の測定IDを入力するだけで、BlogのGA4と同じプロパティにZennのPVが流れ込みます。`pagePath`が`/username/articles/...`形式になるので、Blog本体のデータとは混ざりません。

### Step 4: GitHub Actionsで毎朝自動取得

リアルタイムダッシュボードも検討しましたが、以下の理由でやめました。

- GA4 Data APIはリアルタイムデータを返さない（数時間遅延）
- Search Consoleは3日遅れ
- 毎日1回で十分な更新頻度
- **GitHub Actionsなら無料枠で収まる**
- JSONをGitに入れておけばデータの履歴がGit logで追える

```yaml
# .github/workflows/fetch-analytics.yml
name: Fetch Multi-Platform Analytics

on:
  schedule:
    - cron: '51 20 * * *'  # 05:51 JST
  workflow_dispatch:

jobs:
  fetch:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm install googleapis node-fetch
      - run: echo '${{ secrets.GA4_SERVICE_ACCOUNT_KEY_JSON }}' > sa-key.json
      - run: node fetch-analytics-v2.mjs
        env:
          GA4_PROPERTY_ID: ${{ secrets.GA4_PROPERTY_ID }}
          GA4_SERVICE_ACCOUNT_KEY: ./sa-key.json
          # ... その他の環境変数
      - run: rm -f sa-key.json
      - run: |
          git config user.name "github-actions[bot]"
          git add analytics-data.json
          git diff --staged --quiet || git commit -m "chore: update analytics $(date -u +%Y-%m-%d)"
          git push
```

毎朝5:51 JSTにデータ取得→`analytics-data.json`をcommit & push。ダッシュボードはこのJSONを読むだけです。

### Step 5: Reactダッシュボードの8タブ構成

ダッシュボードは8つのタブで全データを網羅します。

| タブ | 見ているもの |
|---|---|
| **Overview** | 全プラットフォーム合計KPI、LP別サマリーカード、クロスプラットフォームPV推移、PV構成比ドーナツ、記事PVランキング |
| **Blog** | GA4のPV・ユーザー数・滞在時間・直帰率、記事別PV |
| **LP (N)** | LP切り替えサブタブ、LP別PV・CV・CVR、ページ別パフォーマンス、LP横断比較テーブル |
| **Zenn** | GA4 PV + Zenn API（いいね・ブックマーク・フォロワー）、記事一覧 |
| **Note** | Note API（いいね・コメント・フォロワー）、記事一覧 |
| **Qiita** | Qiita API v2（PV・LGTM・ストック・フォロワー）、記事一覧 |
| **SEO** | Search Console。検索クエリ・クリック数・表示回数・CTR・掲載順位 |
| **Infra** | Cloudflare Human/Bot内訳、脅威ブロック数、データソース接続状態 |

UIはグラスモーフィズムベースのダークテーマで、Rechartsを使ったグラフ表示、SVGのスパークラインやサークルゲージなどのカスタムコンポーネントを組み合わせています。

---

## 壁にぶつかった瞬間と乗り越え方

### Cloudflareの「本当のPV」で気づいた盲点

GA4のPVは信頼できる数字だと思っていました。しかしCloudflareのエッジデータを並べてみると、**GA4のPVはCloudflareの約60〜80%しかない**ことがわかりました。

原因は広告ブロッカーです。GA4はクライアントサイドJavaScriptで計測するため、広告ブロッカーを使っているユーザーのアクセスは一切カウントされません。一方、Cloudflareはエッジサーバーでリクエストをカウントするので、広告ブロッカーの影響を受けません。

Infraタブに両方のデータを並べることで「実際にはもう少し読まれている」という感覚を数字で裏付けられるようになりました。これはダッシュボードを作らなければ気づかなかった発見です。

### NoteのPV取得不可は「割り切り」で解決

Note APIからPVを取得する方法を何日も調査しましたが、結論は**取得不可能**でした。Noteのダッシュボードはログインセッション必須で、公開APIにPVエンドポイントは存在しません。

最初はPlaywrightでログインしてスクレイピングする方法を検討しましたが、GitHub Actionsでの安定稼働に不安がありました。結局「NoteはエンゲージメントKPI（いいね・フォロワー）で評価する」という割り切りが最適解でした。

### この経験から学んだこと

**完璧を目指すより、「取れるデータで何ができるか」を考える方が建設的。** プラットフォームごとにAPIの充実度は違います。全プラットフォームで同じ指標を揃えることに固執するより、それぞれの強みの指標を活かす設計の方が実用的でした。

---

## この経験から得た3つの教訓

### 教訓1：データ収集と表示は分離せよ

JSONを挟んで「取得」と「表示」を完全分離したことが、このシステムの拡張性を担保しています。新しいデータソースを追加するとき、ダッシュボードのコードに手を入れる必要はありません。JSONのスキーマを拡張するだけ。

この分離パターンは、個人開発に限らず、チーム開発でも有効です。データの取得ロジックが変わっても、UIには影響しない。逆も然り。

### 教訓2：「配列に足すだけ」設計は初期投資の価値がある

LP_SITES配列のパターンを設計するのに半日かかりました。しかしその後、3つ目のLPを追加するのにかかった時間は5分です。

**「将来何かを追加するたびに3行で済む」設計を最初に作っておけば、トータルの工数は激減する。** これは抽象化のための抽象化ではなく、具体的なユースケース（LP追加）に対する実用的な投資です。

### 教訓3：「無料で動く」は継続の最大の味方

GitHub Actionsの無料枠で毎朝のデータ取得が動き、JSONをGitに保存するだけでインフラ不要。**継続コストがゼロだから、飽きても放置しても壊れない。**

個人プロジェクトで最も重要なのは「動き続けること」です。月額課金のサービスに依存すると、使わなくなったときに解約する手間が発生し、データも失われる。GitHubに全部入っていれば、いつでも復活できます。

---

## セットアップの概要

1. **Google Cloud Console**: プロジェクト作成→GA4 Data API・Search Console API有効化→サービスアカウント作成
2. **GA4**: サービスアカウントを閲覧者として追加
3. **Zenn**: アカウント設定でGA4の測定IDを入力（1分で完了）
4. **Qiita**: アクセストークン発行（`read_qiita`スコープ）
5. **Cloudflare**: APIトークン発行（Zone Analytics Read権限）
6. **GitHub Secrets**: 環境変数を登録
7. **GitHub Actions**: ワークフローファイルを配置

全コード（ダッシュボードJSX・取得スクリプト・GitHub Actionsワークフロー）はGitHubリポジトリで公開しています。

---

## まとめ：今日からできるアクションプラン

「マルチプラットフォーム投稿」の次のステップは「マルチプラットフォーム分析」です。投稿を自動化しても、効果測定がバラバラでは改善サイクルが回りません。

このダッシュボードで実現できたこと：

1. **5プラットフォーム＋複数LPのデータを1画面で横断比較**
2. **LP追加が配列1行で済む拡張性**
3. **GA4のdimensionFilterによるLP分離**（別プロパティ不要）
4. **GitHub Actionsで毎朝自動更新**（サーバー不要・コスト無料）
5. **検索クエリの流入先可視化**でSEO戦略を支援

> まずはGA4 Data APIのサービスアカウントを作成して、ブログのPVデータを取得するスクリプトを1本書いてみてください。JSONに書き出すところまでできれば、あとは足し算です。

---

## おわりに

最後まで読んでいただき、ありがとうございました。

この記事を書いたのは、「複数プラットフォーム運用のデータ管理がつらい」という同じ悩みを持つ人の役に立てればと思ったからです。

GA4のData APIは敷居が高く感じるかもしれませんが、サービスアカウントさえ作れば、あとは`googleapis`パッケージがほとんどやってくれます。Search ConsoleもCloudflareも同じです。

**「全部自動で集まって、1画面で見れる」**という状態を一度体験すると、もう元のタブ行き来には戻れません。

質問や感想があれば、ぜひコメントやSNSでお知らせください。

---

## 参考リンク

- [GA4 Data API リファレンス](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [Search Console API リファレンス](https://developers.google.com/webmaster-tools/v1/api_reference_index)
- [Cloudflare GraphQL Analytics API](https://developers.cloudflare.com/analytics/graphql-api/)
- [Qiita API v2 ドキュメント](https://qiita.com/api/v2/docs)
- [Recharts (React chart library)](https://recharts.org/)

---

**この記事が役に立ったら、ぜひシェアをお願いします！**

あなたのシェアが、同じ悩みを持つ誰かの助けになります。