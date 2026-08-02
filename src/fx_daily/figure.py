"""エクイティカーブ図の生成。

design-tokens.md の図版ルールに従い、HTML カードを headless Chromium で
deviceScaleFactor=2 スクリーンショットして PNG 化する（fig1/fig2 と同一方式）。
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from .derive import DerivedMetrics

_TEMPLATE = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<style>
  :root{{
    --page:#F0EEE6; --surface:#FCFCFB; --ink:#191919; --ink2:#52514E; --muted:#898781;
    --accent:#CC785C; --grid:#E1E0D9; --axis:#C3C2B7; --border:rgba(11,11,11,.10);
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--page);font-family:"Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif;padding:28px;width:fit-content}}
  .card{{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:32px 40px;width:860px}}
  h1{{font-family:"Noto Serif CJK JP","Noto Serif JP",Georgia,serif;font-size:26px;color:var(--ink);font-weight:600}}
  .sub{{font-size:14px;color:var(--ink2);margin:6px 0 20px}}
  .foot{{font-size:12px;color:var(--muted);margin-top:14px}}
  text{{font-family:"Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif;font-size:12px;fill:var(--muted);
       font-variant-numeric:tabular-nums}}
</style></head><body>
<div class="card">
  <h1>図｜エクイティカーブ（開始来）</h1>
  <div class="sub">{sub}</div>
  <svg width="780" height="300" viewBox="0 0 780 300">
    {gridlines}
    <line x1="50" y1="270" x2="770" y2="270" stroke="var(--axis)" stroke-width="1.5"/>
    <polyline points="{points}" fill="none" stroke="var(--accent)" stroke-width="2.5"
      stroke-linejoin="round" stroke-linecap="round"/>
    {labels}
    {last_dot}
  </svg>
  <div class="foot">実測値。将来の成果を保証するものではない。</div>
</div>
</body></html>"""


def _scale(values: list[float], lo: float, hi: float, out_lo: float, out_hi: float) -> list[float]:
    span = (hi - lo) or 1.0
    return [out_lo + (v - lo) / span * (out_hi - out_lo) for v in values]


def render_equity_figure(metrics: DerivedMetrics, out_path: Path) -> None:
    curve = metrics.equity_curve
    equities = [p.equity_jpy for p in curve]
    start = metrics.report.account.start_balance_jpy
    lo = min(equities + [start])
    hi = max(equities + [start])
    pad = (hi - lo) * 0.1 or max(hi * 0.05, 1.0)
    lo, hi = lo - pad, hi + pad

    xs = _scale(list(range(len(curve))), 0, max(len(curve) - 1, 1), 60, 760)
    ys = _scale(equities, lo, hi, 260, 30)
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))

    # 横罫線 3 本 + 金額ラベル
    gridlines, labels = [], []
    for gy in _scale([0, 1, 2], 0, 2, 250, 40):
        gridlines.append(
            f'<line x1="50" y1="{gy:.0f}" x2="770" y2="{gy:.0f}" stroke="var(--grid)" stroke-width="1"/>'
        )
    for frac in (0.0, 0.5, 1.0):
        val = lo + (hi - lo) * (0.15 + 0.7 * frac)
        y = _scale([val], lo, hi, 260, 30)[0]
        labels.append(f'<text x="6" y="{y + 4:.0f}">{val / 10000:.1f}万</text>')
    # 始点・終点の日付ラベル
    labels.append(f'<text x="52" y="290">{curve[0].date.isoformat()}</text>')
    labels.append(f'<text x="690" y="290">{curve[-1].date.isoformat()}</text>')

    last_dot = f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="5" fill="var(--accent)"/>'
    sub = (
        f"開始 {start / 10000:.0f}万円 → 現在 {equities[-1] / 10000:.1f}万円"
        f"（開始来 {metrics.total_jpy:+,.0f}円 / {metrics.total_pct:+.1f}%）"
    )

    html = _TEMPLATE.format(
        sub=sub, points=points, gridlines="".join(gridlines), labels="".join(labels), last_dot=last_dot
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=2)
        page.set_content(html)
        page.wait_for_timeout(300)  # フォント描画待ち
        page.locator(".card").screenshot(path=str(out_path))
        browser.close()
