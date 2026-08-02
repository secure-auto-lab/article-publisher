"""入力レポート群から派生指標を決定的に算出する（LLM 不使用）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path

from .config import FxDailyConfig
from .schema import DailyReport, JudgmentLevel

JUDGMENT_LABELS: dict[JudgmentLevel, str] = {
    "normal": "正常",
    "L1": "L1（注意）",
    "L2": "L2（警戒）",
    "L3": "L3（停止）",
}


@dataclass
class EquityPoint:
    date: Date
    equity_jpy: float


@dataclass
class DerivedMetrics:
    report: DailyReport
    judgment_level: JudgmentLevel
    judgment_reasons: list[str]
    mtd_jpy: float
    total_jpy: float
    total_pct: float
    drawdown_pct: float  # 開始来ピークからのドローダウン
    slippage_delta_pips: float | None  # 実測 − バックテスト前提（+が悪化）
    equity_curve: list[EquityPoint]


def load_reports(input_dir: Path) -> list[DailyReport]:
    """input_dir の YYYY-MM-DD.json を全件読み、日付順に返す。不正ファイルは例外。"""
    reports = []
    for path in sorted(input_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        report = DailyReport.model_validate(data)
        if path.stem != report.date.isoformat():
            raise ValueError(f"{path.name}: ファイル名と date が不一致 ({report.date})")
        reports.append(report)
    reports.sort(key=lambda r: r.date)
    return reports


def derive(target: DailyReport, history: list[DailyReport], config: FxDailyConfig) -> DerivedMetrics:
    """target 日の派生指標を、その日までの履歴から算出する。"""
    upto = [r for r in history if r.date <= target.date]
    if not any(r.date == target.date for r in upto):
        upto.append(target)
        upto.sort(key=lambda r: r.date)

    curve = [EquityPoint(r.date, r.account.equity_jpy) for r in upto]

    start = target.account.start_balance_jpy
    total_jpy = target.account.equity_jpy - start
    total_pct = (total_jpy / start * 100.0) if start else 0.0

    # 月初来: month_start_balance_jpy があれば優先、無ければ当月レポートの day_jpy 合算
    if target.account.month_start_balance_jpy is not None:
        mtd_jpy = target.account.equity_jpy - target.account.month_start_balance_jpy
    else:
        mtd_jpy = sum(
            r.pnl.day_jpy for r in upto if (r.date.year, r.date.month) == (target.date.year, target.date.month)
        )

    peak = max(start, max(p.equity_jpy for p in curve))
    drawdown_pct = (peak - target.account.equity_jpy) / peak * 100.0 if peak else 0.0

    if target.judgment is not None:
        level: JudgmentLevel = target.judgment.level
        reasons = target.judgment.reasons
    else:
        t = config.thresholds
        if drawdown_pct >= t.l3_drawdown_pct:
            level, reasons = "L3", [f"開始来ドローダウン {drawdown_pct:.1f}% ≥ {t.l3_drawdown_pct}%"]
        elif drawdown_pct >= t.l2_drawdown_pct:
            level, reasons = "L2", [f"開始来ドローダウン {drawdown_pct:.1f}% ≥ {t.l2_drawdown_pct}%"]
        elif drawdown_pct >= t.l1_drawdown_pct:
            level, reasons = "L1", [f"開始来ドローダウン {drawdown_pct:.1f}% ≥ {t.l1_drawdown_pct}%"]
        else:
            level, reasons = "normal", ["ドローダウン・運用ルールとも基準内"]

    slippage_delta = None
    if target.slippage.measured_avg_pips is not None:
        slippage_delta = target.slippage.measured_avg_pips - target.slippage.backtest_assumption_pips

    return DerivedMetrics(
        report=target,
        judgment_level=level,
        judgment_reasons=reasons,
        mtd_jpy=mtd_jpy,
        total_jpy=total_jpy,
        total_pct=total_pct,
        drawdown_pct=drawdown_pct,
        slippage_delta_pips=slippage_delta,
        equity_curve=curve,
    )
