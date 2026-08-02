# fx_daily — FX日次運用記の自動生成パイプライン

GALLERIA 側（EA/ロガー）が出力する日次レポート JSON を読み、ローカル LLM で
「一言コメント」だけを生成して、fx-blog の運用記ドラフト（`approved: false`）を
自動コミットする。公開は必ず人の承認（`approve`）を経る。

## 設計原則（細分化による破綻防止）

1. **数値と記事構成に LLM は一切関与しない。** 派生指標（月初来・開始来・DD・判定）は
   Python が決定的に計算し、テンプレートに流し込む。
2. **LLM の仕事は「一言コメント」1つだけ**（JSON in → JSON out の最小タスク）。
3. コメントは二段検査:
   - 決定的バリデーション: 禁止表現（勝てる/必ず/保証 等）・数値整合（コメント中の
     数値が事実データに由来するか）・120字以内
   - LLM 自己検証: 別呼び出しで事実との矛盾を検査
   リトライ上限到達で**定型文にフォールバック**（記事は必ず成立する）。
4. 実績は良くても悪くても改変しない。生成後の数値編集は禁止（編集方針より）。

## 入力契約（GALLERIA 側が出力するもの）

- 出力先: `\\GALLERIA\Users\tinou\fx-ea\reports\daily\YYYY-MM-DD.json`
  （= GALLERIA ローカルの `C:\Users\tinou\fx-ea\reports\daily\`。変更する場合は
  リポジトリルートに `fx-daily.yaml` を置いて `input_dir` を上書き）
- 1営業日1ファイル。**一度書いたファイルは変更しない**（追記・修正は翌日分で）
- スキーマ: [schema.py](schema.py) が正。サンプル: [sample/](sample/)

```json
{
  "schema_version": 1,
  "date": "2026-08-01",
  "account": {
    "balance_jpy": 202100,          // 当日終了時残高
    "equity_jpy": 202100,           // 当日終了時有効証拠金
    "start_balance_jpy": 200000,    // 運用開始時資金
    "month_start_balance_jpy": 200300  // 月初残高（省略可）
  },
  "signals": {
    "detected": 1,                  // シグナル発生数
    "skipped_z": 0,                 // z不足で見送り
    "skipped_spread": 0,            // スプレッドガードで見送り
    "entered": 1,                   // エントリー数
    "entries_by_z": {"z3": 1}       // z階層別内訳
  },
  "pnl": {"day_pips": 18.0, "day_jpy": 1800},
  "slippage": {
    "measured_avg_pips": 0.5,       // 実測平均（約定なしの日は null）
    "backtest_assumption_pips": 0.6,
    "samples": 1
  },
  "judgment": {"level": "normal", "reasons": ["..."]},  // 省略可。無ければDD閾値から自動判定
  "notes": "z3シグナル1件、順行。"     // 任意。LLMコメントの参考情報
}
```

## 使い方

```sh
# 未生成の新規レポートをすべてドラフト化（コミットのみ）
python -m src.fx_daily generate

# push まで行う（日次スケジューラはこれ）
python -m src.fx_daily generate --push

# サンプルでテスト（コミットしない）
python -m src.fx_daily generate --input-dir src/fx_daily/sample --no-commit

# 承認して公開（approved: true → commit & push → 自動デプロイ）
python -m src.fx_daily approve 2026-08-01
```

## 日次スケジューラ登録（EA稼働開始時に実行）

データが無い日は静かに終了するので、先に登録しても害はない。

```powershell
schtasks /Create /TN "fx-daily-article" /SC DAILY /ST 06:30 /TR ^
  "cmd /c cd /d C:\Users\rdp\Projects\article-publisher && python -m src.fx_daily generate --push >> fx-daily.log 2>&1"
```

## 出力

- 記事: `fx-blog/src/content/daily/YYYY-MM-DD.md`（frontmatter に全数値、本文はコメントのみ）
- 図版: `fx-blog/public/figures/daily/YYYY-MM-DD-equity.png`（エクイティカーブ、
  design-tokens 準拠の HTML → headless Chromium 撮影）
- サイト側: `/daily/` に一覧、`approved: true` のみビルド対象

## 設定の上書き（fx-daily.yaml、リポジトリルート・任意）

```yaml
input_dir: '\\GALLERIA\Users\tinou\fx-ea\reports\daily'
thresholds:
  l1_drawdown_pct: 10.0   # 運用ルールブック確定時に必ず見直す
  l2_drawdown_pct: 20.0
  l3_drawdown_pct: 30.0
llm:
  model: qwen3.6:27b-q5_K_M
```
