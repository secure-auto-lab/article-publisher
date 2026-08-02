"""日次運用記 Markdown の生成。数値・構成はすべてここ（テンプレート）が決める。"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from .derive import JUDGMENT_LABELS, DerivedMetrics

_TEMPLATE = Template(
    """---
title: "運用記 {{ date }}"
date: {{ date }}
judgment: {{ level }}
judgmentLabel: "{{ label }}"
approved: false
llmGenerated: {{ 'true' if llm_generated else 'false' }}
figure: "/figures/daily/{{ date }}-equity.png"
metrics:
  dayPips: {{ "%.1f"|format(r.pnl.day_pips) }}
  dayJpy: {{ "%.0f"|format(r.pnl.day_jpy) }}
  mtdJpy: {{ "%.0f"|format(m.mtd_jpy) }}
  totalJpy: {{ "%.0f"|format(m.total_jpy) }}
  totalPct: {{ "%.1f"|format(m.total_pct) }}
  drawdownPct: {{ "%.1f"|format(m.drawdown_pct) }}
signals:
  detected: {{ r.signals.detected }}
  skippedZ: {{ r.signals.skipped_z }}
  skippedSpread: {{ r.signals.skipped_spread }}
  entered: {{ r.signals.entered }}
{%- if r.signals.entries_by_z %}
  entriesByZ:
{%- for k, v in r.signals.entries_by_z.items() %}
    {{ k }}: {{ v }}
{%- endfor %}
{%- endif %}
slippage:
  measuredPips: {{ r.slippage.measured_avg_pips if r.slippage.measured_avg_pips is not none else 'null' }}
  assumptionPips: {{ r.slippage.backtest_assumption_pips }}
  samples: {{ r.slippage.samples }}
judgmentReasons:
{%- for reason in m.judgment_reasons %}
  - "{{ reason }}"
{%- endfor %}
---

{{ comment }}
"""
)


def render_daily_md(metrics: DerivedMetrics, comment: str, llm_generated: bool, out_dir: Path) -> Path:
    content = _TEMPLATE.render(
        date=metrics.report.date.isoformat(),
        level=metrics.judgment_level,
        label=JUDGMENT_LABELS[metrics.judgment_level],
        r=metrics.report,
        m=metrics,
        comment=comment,
        llm_generated=llm_generated,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{metrics.report.date.isoformat()}.md"
    out_path.write_text(content, encoding="utf-8", newline="\n")
    return out_path
