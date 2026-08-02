"""fx-daily CLI。

使い方:
  python -m src.fx_daily generate            # 未生成の新規レポートをすべて記事化（approved: false）
  python -m src.fx_daily generate --date 2026-08-03 --force
  python -m src.fx_daily approve 2026-08-03  # 承認して公開（commit & push）
"""

from __future__ import annotations

import subprocess
from datetime import date as Date
from pathlib import Path

import typer

from .config import REPO_ROOT, FxDailyConfig, load_config
from .derive import derive, load_reports
from .figure import render_equity_figure
from .llm import generate_comment
from .render import render_daily_md

app = typer.Typer(help="FX日次運用記の自動生成")


def _git(*args: str) -> None:
    subprocess.run(["git", "-C", str(REPO_ROOT), *args], check=True)


def _commit_and_maybe_push(paths: list[Path], message: str, push: bool) -> None:
    _git("add", *[str(p) for p in paths])
    _git("commit", "-m", message + "\n\nCo-Authored-By: fx-daily pipeline <noreply@secure-auto-lab.com>")
    if push:
        _git("push", "origin", "main")


@app.command()
def generate(
    date: str = typer.Option(None, help="対象日 YYYY-MM-DD（省略時は未生成の全レポート）"),
    input_dir: Path = typer.Option(None, help="レポートJSONのディレクトリ（既定は設定値）"),
    force: bool = typer.Option(False, help="生成済みでも上書き"),
    push: bool = typer.Option(False, help="コミット後に push する"),
    no_commit: bool = typer.Option(False, "--no-commit", help="ファイル生成のみ（テスト用）"),
) -> None:
    """新規レポートを記事化する。生成物は approved: false（未公開ドラフト）。"""
    config = load_config()
    src_dir = input_dir or config.input_dir
    if not src_dir.exists():
        typer.echo(f"入力ディレクトリなし: {src_dir}（データ未出力のため終了）")
        raise typer.Exit(0)

    reports = load_reports(src_dir)
    if not reports:
        typer.echo("レポートなし。終了")
        raise typer.Exit(0)

    targets = [r for r in reports if date is None or r.date == Date.fromisoformat(date)]
    if date is not None and not targets:
        typer.echo(f"{date} のレポートが見つからない")
        raise typer.Exit(1)

    generated: list[Path] = []
    for report in targets:
        md_path = config.content_dir / f"{report.date.isoformat()}.md"
        if md_path.exists() and not force:
            continue
        typer.echo(f"生成中: {report.date}")
        metrics = derive(report, reports, config)
        fig_path = config.figures_dir / f"{report.date.isoformat()}-equity.png"
        render_equity_figure(metrics, fig_path)
        comment, llm_ok = generate_comment(metrics, config)
        out = render_daily_md(metrics, comment, llm_ok, config.content_dir)
        typer.echo(f"  -> {out.relative_to(REPO_ROOT)} (LLMコメント: {'採用' if llm_ok else '定型文'})")
        generated.extend([out, fig_path])

    if not generated:
        typer.echo("新規生成なし")
        raise typer.Exit(0)

    if not no_commit:
        dates = sorted({p.stem.split("-equity")[0] for p in generated})
        _commit_and_maybe_push(
            generated, f"fx-daily: 運用記ドラフト生成 {', '.join(dates)}", push
        )
        typer.echo(f"コミット完了（push: {push}）。approve コマンドで公開されます")


@app.command()
def approve(
    date: str = typer.Argument(help="承認する日 YYYY-MM-DD"),
    push: bool = typer.Option(True, help="コミット後に push する（既定で有効）"),
) -> None:
    """ドラフトを承認して公開する（approved: true に書き換え）。"""
    config = load_config()
    md_path = config.content_dir / f"{date}.md"
    if not md_path.exists():
        typer.echo(f"ドラフトなし: {md_path}")
        raise typer.Exit(1)
    text = md_path.read_text(encoding="utf-8")
    if "approved: true" in text:
        typer.echo("すでに承認済み")
        raise typer.Exit(0)
    md_path.write_text(text.replace("approved: false", "approved: true", 1), encoding="utf-8", newline="\n")
    _commit_and_maybe_push([md_path], f"fx-daily: 運用記 {date} を承認・公開", push)
    typer.echo(f"承認完了。push により自動デプロイされます（push: {push}）")


if __name__ == "__main__":
    app()
