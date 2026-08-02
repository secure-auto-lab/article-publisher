"""fx-daily 入力契約（GALLERIA 側 EA/ロガーが出力する日次レポート JSON のスキーマ）。

契約の詳細・サンプルは src/fx_daily/README.md を参照。
このスキーマがバリデーションの唯一の正であり、変更時は schema_version を上げる。
"""

from __future__ import annotations

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

JudgmentLevel = Literal["normal", "L1", "L2", "L3"]


class Account(BaseModel):
    balance_jpy: float = Field(description="当日終了時の残高（円）")
    equity_jpy: float = Field(description="当日終了時の有効証拠金（円）")
    start_balance_jpy: float = Field(description="運用開始時の資金（円）")
    month_start_balance_jpy: float | None = Field(
        default=None, description="月初残高（円）。無ければ履歴から補完"
    )


class Judgment(BaseModel):
    level: JudgmentLevel = Field(description="ルールブック準拠の総合判定")
    reasons: list[str] = Field(default_factory=list, description="判定根拠（EA側で判定した場合）")


class Signals(BaseModel):
    detected: int = Field(ge=0, description="シグナル発生数")
    skipped_z: int = Field(ge=0, description="z不足による見送り数")
    skipped_spread: int = Field(ge=0, description="スプレッドガードによる見送り数")
    entered: int = Field(ge=0, description="エントリー数")
    entries_by_z: dict[str, int] = Field(
        default_factory=dict, description="z階層別エントリー数（例: {'z2': 1, 'z3': 0}）"
    )


class Pnl(BaseModel):
    day_pips: float = Field(description="当日損益（pips）")
    day_jpy: float = Field(description="当日損益（円）")


class Slippage(BaseModel):
    measured_avg_pips: float | None = Field(default=None, description="実測平均スリッページ（pips）")
    backtest_assumption_pips: float = Field(description="バックテスト前提スリッページ（pips）")
    samples: int = Field(ge=0, default=0, description="実測サンプル数（約定数）")


class DailyReport(BaseModel):
    """1営業日分のレポート。ファイル名は YYYY-MM-DD.json。"""

    schema_version: int = Field(description="契約バージョン。現行は 1")
    date: Date = Field(description="対象営業日")
    account: Account
    signals: Signals
    pnl: Pnl
    slippage: Slippage
    judgment: Judgment | None = Field(
        default=None, description="EA側判定。無ければ生成側が閾値設定から導出"
    )
    notes: str = Field(default="", description="EA側からの生メモ（任意。LLMコメントの参考情報）")

    @field_validator("schema_version")
    @classmethod
    def _supported_version(cls, v: int) -> int:
        if v != 1:
            raise ValueError(f"unsupported schema_version: {v}")
        return v
