---
title: "Claude Codeで開発効率を3倍にした話"
description: "AIペアプログラミングツール「Claude Code」の導入から実践活用まで。Skills・Hooks・MCP・CLAUDE.mdなど最新機能を初心者向けに解説します。"
pubDate: "2026-02-14"
updatedDate: "2026-02-14"
category: "dev-tips"
tags: ["ClaudeCode", "AI", "開発効率化", "CLI", "自動化"]
author: "secure＆autoラボ"
---

# Claude Codeで開発効率を3倍にした話

**「コードを書く時間を半分にできたら...」**

エンジニアなら一度は思ったことがあるはず。私もその一人でした。

Claude Codeを導入してから、ドキュメント調査・テスト作成・リファクタリングにかかる時間が劇的に短縮されました。この記事では、**導入方法から最新機能まで**、実際に使って分かったことを初心者向けにまとめます。

---

## 🎯 この記事で得られること

- Claude Codeのインストールと初期設定
- CLAUDE.mdによるプロジェクト設定の方法
- **Skills**と**カスタムコマンド**の違いと使い分け
- Hooks・MCP・Plan Modeなど最新機能の実践的な活用法
- VS Code / JetBrains IDEとの連携

---

## 🚀 Claude Codeとは

Claude Codeは、Anthropicが提供する**コマンドラインAIアシスタント**です。ターミナルやIDEから直接使えるAIペアプログラマーで、コードの読み書き、テスト実行、Git操作などを対話的にサポートしてくれます。

GitHub CopilotやCursorとの大きな違いは、**プロジェクト全体を理解した上で、複数ファイルにまたがる変更を自律的に行える**ことです。

---

## 📦 インストール

### macOS / Linux / WSL（推奨）

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Windows（PowerShell）

```powershell
irm https://claude.ai/install.ps1 | iex
```

### Windows（CMD）

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

### Homebrew（macOS / Linux）

```bash
brew install --cask claude-code
```

※ Homebrew版は自動更新されないため、定期的に `brew upgrade claude-code` を実行してください。

### 動作確認

```bash
claude doctor
```

インストール後、プロジェクトディレクトリで `claude` を実行すればすぐに使えます。

```bash
cd /path/to/your-project
claude
```

### 認証方法

- **Claude Pro / Max プラン**：claude.ai のアカウントでログイン（推奨）
- **Anthropic Console**：API キーでの認証。従量課金

---

## 📝 CLAUDE.md：プロジェクトの設定ファイル

CLAUDE.mdは、Claude Codeがプロジェクトのルールや構造を理解するための**設定ファイル**です。毎セッション開始時に自動で読み込まれます。

### 初期化

```bash
claude
> /init
```

これでプロジェクトルートに `CLAUDE.md` が生成されます。

### CLAUDE.mdの記述例

```markdown
# プロジェクト概要
Next.js 15 + Supabase で構築した結婚式向けインタラクティブシステム

## 技術スタック
- Next.js 15 (App Router)
- TypeScript
- Supabase (PostgreSQL + Realtime)
- Tailwind CSS

## ビルド・テストコマンド
- `npm run dev` - 開発サーバー
- `npm run build` - ビルド
- `npx playwright test` - E2Eテスト

## コーディング規約
- Server Actions を使う（API Routes は使わない）
- 日本語コメントOK
- テストは Playwright で書く
```

### 設定ファイルの優先順位

Claude Codeは**5つの階層**で設定を管理します。上から順に優先されます。

| レベル | 場所 | 用途 |
|-------|------|------|
| 組織ポリシー | `/etc/claude-code/CLAUDE.md` | 組織全体のルール |
| プロジェクト | `./CLAUDE.md` | チーム共有（Git管理） |
| プロジェクトルール | `./.claude/rules/*.md` | 機能別のモジュラールール |
| ユーザー | `~/.claude/CLAUDE.md` | 個人の全プロジェクト共通設定 |
| ローカル | `./CLAUDE.local.md` | 個人のプロジェクト固有設定（gitignore対象） |

**ポイント**: チーム共有のルールは `CLAUDE.md`、個人的な好みは `CLAUDE.local.md` に書き分けるのがおすすめです。

---

## ⚡ Skills vs カスタムコマンド：違いと使い分け

Claude Codeでは `/` で始まるカスタムコマンドを作れますが、**2つの方法**があります。混乱しやすいので、違いを整理します。

### カスタムコマンド（従来の方法）

`.claude/commands/` にMarkdownファイルを置く方法です。

```
.claude/commands/
└── review.md      ← /review で呼び出せる
```

**review.md** の例：

```markdown
コードをレビューしてください。以下の観点でチェック：
- セキュリティ（SQLインジェクション、XSS）
- パフォーマンス（N+1クエリ、メモリリーク）
- テストカバレッジ
```

使い方：

```
> /review src/auth.ts
```

### Skills（新しい方法、推奨）

`~/.claude/skills/` にディレクトリを作る方法です。カスタムコマンドの**上位互換**です。

```
~/.claude/skills/security-review/
├── SKILL.md          ← 必須：メインの指示
├── checklist.md      ← 補助ファイル
└── examples/
    └── sample.md     ← 出力例
```

**SKILL.md** の例：

```yaml
---
name: security-review
description: コードのセキュリティレビューを行う
---

以下のチェックリストに基づいてセキュリティレビューを実施してください。

$import(checklist.md)
```

### 主な違い

| 機能 | カスタムコマンド | Skills |
|------|----------------|--------|
| 複数ファイル対応 | 不可（1ファイルのみ） | 可能（補助ファイル、テンプレート） |
| 自動呼び出し | 不可（手動 `/` のみ） | 可能（Claudeが文脈から判断） |
| サブエージェント実行 | 不可 | 可能 |
| ツール制限 | 限定的 | 柔軟に設定可能 |
| 引数の受け渡し | `$ARGUMENTS` | `$ARGUMENTS` |

**結論**：新しく作るなら**Skills**を使いましょう。カスタムコマンドは引き続き動作しますが、Skillsの方が柔軟で高機能です。

### よく使うSkillの例

**記事執筆スキル**（当ブログで実際に使用）：

```yaml
---
name: article
description: 技術記事の執筆支援
---

以下の手順で技術記事を作成してください：
1. 対象の技術を調査
2. 読者にとっての価値を明確化
3. 記事テンプレートに沿って執筆
4. article-publisher CLI で検証

$import(template.md)
```

---

## 🔧 Hooks：自動化ルール

Hooksは、Claude Codeの特定のイベントに対して**自動でシェルコマンドを実行する**仕組みです。Skillsが「Claudeに何をさせるか」なら、Hooksは「何が起きたら自動で何をするか」です。

### 設定方法

```
> /hooks
```

インタラクティブなメニューが開き、GUI的にHooksを設定できます。

### 設定例：ファイル保存後に自動フォーマット

`.claude/settings.json`：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$(jq -r '.tool_input.file_path')\""
          }
        ]
      }
    ]
  }
}
```

### 設定例：特定ファイルの編集をブロック

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

### 利用可能なイベント

| イベント | タイミング |
|---------|----------|
| `SessionStart` | セッション開始時 |
| `PreToolUse` | ツール実行前（ブロック可能） |
| `PostToolUse` | ツール実行成功後 |
| `Notification` | Claudeが入力を待っている時 |
| `Stop` | Claudeの応答完了時 |

---

## 🌐 MCP：外部ツール連携

MCP（Model Context Protocol）は、Claude Codeを**外部サービスと接続するオープン標準**です。GitHub、Sentry、Slack、データベースなど、100以上の連携が可能です。

### MCPサーバーの追加

```bash
# HTTPサーバー（リモート）
claude mcp add --transport http github https://api.githubcopilot.com/mcp/

# stdioサーバー（ローカル）
claude mcp add --transport stdio my-db -- npx -y postgres-mcp-server

# 一覧表示
claude mcp list

# セッション内で管理
> /mcp
```

### スコープ

| スコープ | 保存先 | 共有範囲 |
|---------|--------|---------|
| local（デフォルト） | `~/.claude.json` | 自分だけ |
| project | `.mcp.json` | チーム（Git管理） |
| user | `~/.claude.json` | 自分の全プロジェクト |

### 活用例

```
> GitHub の未レビューPRを一覧表示して
> Sentry の最新エラーを調べて原因を分析して
> このSQLをデータベースで実行して結果を教えて
```

---

## 🗺️ Plan Mode：安全な設計モード

Plan Modeは、Claude Codeを**読み取り専用**にして、実装計画を立ててから実行する安全なモードです。

### いつ使うか

- 複数ファイルにまたがる大きな変更
- 知らないコードベースの調査
- リファクタリングの影響範囲を把握したい時

### 使い方

セッション中に `Shift+Tab` を押すとモード切替できます：

```
Normal → Auto-Accept → Plan Mode → Normal
```

または起動時に指定：

```bash
claude --permission-mode plan
```

Plan Modeでは：
1. Claudeがコードを読み取り専用で調査
2. 実装計画を提示
3. あなたが承認してから初めてコード変更を実行

---

## 💻 IDE連携

### VS Code

VS Code拡張をインストールすると、エディタ内でClaude Codeが使えます。

- **起動**: `Cmd+Esc`（Mac） / `Ctrl+Esc`（Windows/Linux）
- **ファイル参照**: `@ファイル名` で自動補完
- **行指定**: `@auth.ts#5-10` で特定の行範囲を参照
- **画像貼り付け**: `Ctrl+V` でスクリーンショットを共有

### JetBrains（IntelliJ, WebStorm, PyCharm 等）

Settings → Plugins → 「Claude Code」で検索してインストール。

- **起動**: `Ctrl+Esc`（Windows/Linux） / `Cmd+Esc`（Mac）
- **ファイル参照**: `Ctrl+Alt+K` でファイルパス挿入
- **診断情報**: IDEのlintエラーを自動共有

---

## 🔑 よく使うキーボードショートカット

| ショートカット | 動作 |
|-------------|------|
| `Ctrl+C` | 生成を中断 |
| `Ctrl+D` | Claude Code を終了 |
| `Shift+Tab` | モード切替（Normal / Auto-Accept / Plan） |
| `Ctrl+G` | テキストエディタで入力を編集 |
| `Ctrl+R` | コマンド履歴を検索 |
| `Ctrl+L` | 画面クリア |

### よく使うスラッシュコマンド

| コマンド | 用途 |
|---------|------|
| `/init` | CLAUDE.md を初期化 |
| `/clear` | 会話履歴をクリア |
| `/compact` | コンテキストを圧縮 |
| `/cost` | トークン使用量を表示 |
| `/memory` | メモリファイルを編集 |
| `/mcp` | MCPサーバーを管理 |
| `/model` | AIモデルを変更 |
| `/skills` | Skillsを管理 |
| `/hooks` | Hooksを管理 |

---

## 📊 Before / After：実際の変化

| 作業 | Before | After |
|------|--------|-------|
| ドキュメント調査 | 1時間 | 10分 |
| テストコード作成 | 面倒で後回し | Claudeと一緒に楽しく |
| 知らないコードベースの把握 | 半日 | 30分 |
| リファクタリング | 慎重に手作業 | Plan Modeで安全に |
| 総開発時間 | 100% | **約33%** |

---

## 🏁 まとめ：今日から始める3ステップ

**Step 1**: インストールして `/init` でCLAUDE.mdを作る

```bash
curl -fsSL https://claude.ai/install.sh | bash
cd /your-project
claude
> /init
```

**Step 2**: よく使うタスクをSkillにする

```bash
mkdir -p ~/.claude/skills/my-review
# SKILL.md にレビュー手順を書く
```

**Step 3**: MCPで外部ツールをつなぐ

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
```

Claude Codeは使い込むほど、CLAUDE.md・Skills・自動メモリを通じて**あなたのプロジェクトを深く理解するパートナー**に成長します。まずは小さなタスクから試してみてください。
