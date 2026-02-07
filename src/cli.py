"""CLI interface for article-publisher."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .transformer.parser import ArticleParser
from .transformer.converter import ConverterFactory
from .publishers.qiita import QiitaPublisher
from .publishers.zenn import ZennPublisher
from .announcer.service import AnnouncementService

app = typer.Typer(
    name="publisher",
    help="Multi-platform article publishing system",
    add_completion=False,
)
console = Console()


@app.command()
def publish(
    article_path: str = typer.Argument(..., help="Path to the article markdown file"),
    platforms: Optional[str] = typer.Option(
        None,
        "--platforms", "-p",
        help="Comma-separated list of platforms (note,zenn,qiita,blog). If not specified, uses frontmatter config."
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Preview without actually publishing"
    ),
    no_announce: bool = typer.Option(
        False,
        "--no-announce",
        help="Skip SNS announcements"
    ),
):
    """Publish an article to configured platforms."""
    asyncio.run(_publish_async(article_path, platforms, dry_run, no_announce))


async def _publish_async(
    article_path: str,
    platforms: Optional[str],
    dry_run: bool,
    no_announce: bool,
):
    """Async implementation of publish command."""
    parser = ArticleParser()

    # Parse article
    with console.status("Parsing article..."):
        try:
            article = parser.parse_file(article_path)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Article not found: {article_path}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error parsing article:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"\n[bold]Article:[/bold] {article.title}")
    console.print(f"[dim]Slug:[/dim] {article.slug}")
    console.print(f"[dim]Tags:[/dim] {', '.join(article.tags)}")

    # Determine target platforms
    if platforms:
        target_platforms = [p.strip() for p in platforms.split(",")]
    else:
        target_platforms = article.get_enabled_platforms()

    console.print(f"\n[bold]Target platforms:[/bold] {', '.join(target_platforms)}")

    if dry_run:
        console.print("\n[yellow]Dry run mode - no changes will be made[/yellow]")
        _show_preview(article, target_platforms)
        return

    # Convert and publish
    published_urls = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for platform in target_platforms:
            task = progress.add_task(f"Publishing to {platform}...", total=None)

            try:
                # Convert content
                converter = ConverterFactory.get_converter(platform)
                content = converter.convert(article)

                # Publish
                result = await _publish_to_platform(platform, article, content)

                if result.success:
                    published_urls[platform] = result.url
                    progress.update(task, description=f"[green]Published to {platform}[/green]")
                else:
                    progress.update(task, description=f"[red]Failed: {platform} - {result.error}[/red]")

            except Exception as e:
                progress.update(task, description=f"[red]Error: {platform} - {e}[/red]")

    # Show results
    _show_results(published_urls)

    # SNS announcements
    if not no_announce and published_urls:
        console.print("\n[bold]Announcing to SNS...[/bold]")
        announcement_service = AnnouncementService()
        results = await announcement_service.announce_all(article, published_urls)

        for result in results:
            if result.success:
                console.print(f"  [green]✓[/green] {result.platform}: {result.url}")
            else:
                console.print(f"  [red]✗[/red] {result.platform}: {result.error}")


async def _publish_to_platform(platform: str, article, content: str):
    """Publish to a specific platform."""
    from .publishers.base import PublishResult

    if platform == "qiita":
        try:
            publisher = QiitaPublisher()
            return await publisher.publish(article, content)
        except ValueError as e:
            return PublishResult.failure_result("qiita", str(e))

    elif platform == "zenn":
        try:
            publisher = ZennPublisher()
            return await publisher.publish(article, content)
        except Exception as e:
            return PublishResult.failure_result("zenn", str(e))

    elif platform == "note":
        try:
            from .publishers.note import NotePublisher
            publisher = NotePublisher()
            return await publisher.publish(article, content)
        except (ImportError, ValueError) as e:
            return PublishResult.failure_result("note", str(e))

    elif platform == "blog":
        # Blog is handled via git push (similar to Zenn)
        return PublishResult.failure_result("blog", "Blog publishing requires Astro setup")

    else:
        return PublishResult.failure_result(platform, f"Unknown platform: {platform}")


def _show_preview(article, platforms: list[str]):
    """Show preview of converted content."""
    console.print("\n[bold]Preview:[/bold]")

    for platform in platforms:
        console.print(f"\n[cyan]--- {platform.upper()} ---[/cyan]")
        try:
            converter = ConverterFactory.get_converter(platform)
            content = converter.convert(article)
            # Show first 500 chars
            preview = content[:500] + "..." if len(content) > 500 else content
            console.print(preview)
        except Exception as e:
            console.print(f"[red]Error converting: {e}[/red]")


def _show_results(published_urls: dict[str, str]):
    """Show publishing results in a table."""
    if not published_urls:
        console.print("\n[yellow]No articles were published.[/yellow]")
        return

    table = Table(title="\nPublished URLs")
    table.add_column("Platform", style="cyan")
    table.add_column("URL", style="green")

    for platform, url in published_urls.items():
        table.add_row(platform, url)

    console.print(table)


@app.command()
def convert(
    article_path: str = typer.Argument(..., help="Path to the article markdown file"),
    platform: str = typer.Argument(..., help="Target platform (note, zenn, qiita, blog)"),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output file path. If not specified, prints to stdout."
    ),
):
    """Convert article to platform-specific format."""
    parser = ArticleParser()

    try:
        article = parser.parse_file(article_path)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Article not found: {article_path}")
        raise typer.Exit(1)

    try:
        converter = ConverterFactory.get_converter(platform)
        content = converter.convert(article)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"[green]Saved to:[/green] {output}")
    else:
        console.print(content)


@app.command()
def validate(
    article_path: str = typer.Argument(..., help="Path to the article markdown file"),
):
    """Validate article frontmatter and content."""
    parser = ArticleParser()

    try:
        article = parser.parse_file(article_path)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Article not found: {article_path}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Parse error:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[bold]Article:[/bold] {article.title}")
    console.print(f"[dim]Slug:[/dim] {article.slug}")

    # Show enabled platforms
    console.print(f"\n[bold]Enabled platforms:[/bold]")
    for platform in article.get_enabled_platforms():
        console.print(f"  • {platform}")

    console.print("\n[green]✓ Article is valid[/green]")


@app.command()
def screenshot(
    source: str = typer.Argument(..., help="URL, HTML file path, or TSX/JSX file path"),
    output: str = typer.Option(
        "./screenshot.png",
        "--output", "-o",
        help="Output PNG file path"
    ),
    full_page: bool = typer.Option(
        False,
        "--full-page",
        help="Capture full scrollable page"
    ),
    width: int = typer.Option(
        1280,
        "--width", "-w",
        help="Viewport width"
    ),
    height: int = typer.Option(
        720,
        "--height", "-h",
        help="Viewport height"
    ),
    selector: Optional[str] = typer.Option(
        None,
        "--selector", "-s",
        help="CSS selector to capture specific element"
    ),
    delay: int = typer.Option(
        0,
        "--delay", "-d",
        help="Wait time in ms before capture"
    ),
    props: Optional[str] = typer.Option(
        None,
        "--props",
        help="JSON props for TSX/JSX component (e.g., '{\"title\": \"Hello\"}')"
    ),
):
    """Capture screenshot from URL, HTML file, or TSX/JSX component."""
    import json as json_module

    async def _screenshot():
        from .tools.screenshot import ScreenshotTool

        # Parse props if provided
        props_dict = None
        if props:
            try:
                props_dict = json_module.loads(props)
            except json_module.JSONDecodeError as e:
                console.print(f"[red]Error parsing props JSON:[/red] {e}")
                raise typer.Exit(1)

        tool = ScreenshotTool()

        with console.status(f"Capturing screenshot from {source}..."):
            try:
                result = await tool.capture(
                    source=source,
                    output=output,
                    full_page=full_page,
                    width=width,
                    height=height,
                    selector=selector,
                    delay=delay,
                    props=props_dict,
                )
                console.print(f"[green]Screenshot saved:[/green] {result}")
            except FileNotFoundError as e:
                console.print(f"[red]File not found:[/red] {e}")
                raise typer.Exit(1)
            except ValueError as e:
                console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1)
            except Exception as e:
                console.print(f"[red]Screenshot failed:[/red] {e}")
                raise typer.Exit(1)

    asyncio.run(_screenshot())


@app.command()
def init(
    title: str = typer.Option(..., "--title", "-t", help="Article title"),
    slug: str = typer.Option(..., "--slug", "-s", help="Article slug"),
    output_dir: str = typer.Option(
        "./articles/drafts",
        "--output", "-o",
        help="Output directory"
    ),
):
    """Create a new article from template."""
    from datetime import datetime

    template = f"""---
title: "{title}"
slug: "{slug}"
description: ""
tags: []
category: "tech"
author: "tinou"
created_at: {datetime.now().strftime("%Y-%m-%d")}
updated_at: {datetime.now().strftime("%Y-%m-%d")}

platforms:
  note:
    enabled: true
    price: 0
  zenn:
    enabled: true
    emoji: "📝"
    topics: []
  qiita:
    enabled: true
  blog:
    enabled: true

announcement:
  enabled: true
  platforms:
    - twitter
    - bluesky
    - misskey
---

# {title}

Write your article content here.

## Introduction

...

## Conclusion

...
"""

    output_path = Path(output_dir) / f"{slug}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template, encoding="utf-8")

    console.print(f"[green]Created:[/green] {output_path}")


@app.command()
def announce(
    article_path: str = typer.Argument(..., help="Path to the article markdown file"),
    platforms: Optional[str] = typer.Option(
        None,
        "--platforms", "-p",
        help="Comma-separated list of platforms (twitter, bluesky, misskey). If not specified, uses frontmatter config."
    ),
    urls: Optional[str] = typer.Option(
        None,
        "--urls", "-u",
        help="Published URLs as JSON (e.g., '{\"blog\": \"https://...\"}')"
    ),
):
    """Announce an already-published article to SNS."""
    import json as json_module

    async def _announce():
        parser = ArticleParser()

        try:
            article = parser.parse_file(article_path)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Article not found: {article_path}")
            raise typer.Exit(1)

        console.print(f"[bold]Article:[/bold] {article.title}")

        # Parse URLs
        published_urls = {}
        if urls:
            try:
                published_urls = json_module.loads(urls)
            except json_module.JSONDecodeError as e:
                console.print(f"[red]Error parsing URLs JSON:[/red] {e}")
                raise typer.Exit(1)

        # Determine target platforms
        if platforms:
            target_platforms = [p.strip() for p in platforms.split(",")]
            # Override article announcement platforms
            article.announcement.platforms = target_platforms

        console.print(f"[bold]Announcing to:[/bold] {', '.join(article.announcement.platforms)}")

        service = AnnouncementService()
        results = await service.announce_all(article, published_urls)

        for result in results:
            if result.success:
                console.print(f"  [green]✓[/green] {result.platform}: {result.url}")
            else:
                console.print(f"  [red]✗[/red] {result.platform}: {result.error}")

    asyncio.run(_announce())


@app.command(name="note-login")
def note_login(
    headless: bool = typer.Option(
        False,
        "--headless",
        help="Run browser in headless mode"
    ),
):
    """Test login to Note using Playwright."""
    async def _test():
        try:
            from .publishers.note import NotePublisher

            console.print("[bold]Testing Note login...[/bold]")

            publisher = NotePublisher(headless=headless)
            success = await publisher.test_login()

            if success:
                console.print("[green]✓ Login successful![/green]")
            else:
                console.print("[red]✗ Login failed[/red]")
                raise typer.Exit(1)

        except ImportError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        except ValueError as e:
            console.print(f"[red]Configuration error:[/red] {e}")
            raise typer.Exit(1)

    asyncio.run(_test())


@app.command(name="test-announce")
def test_announce(
    platform: str = typer.Argument(..., help="Platform to test (twitter, bluesky, misskey)"),
    message: str = typer.Option(
        "テスト投稿です。article-publisherからの自動投稿テスト。",
        "--message", "-m",
        help="Test message to post"
    ),
):
    """Test announcement to a single platform."""
    async def _test():
        service = AnnouncementService()

        if platform not in service._announcers:
            console.print(f"[red]Error:[/red] Announcer not available for {platform}")
            console.print(f"[dim]Available: {', '.join(service._announcers.keys())}[/dim]")
            raise typer.Exit(1)

        console.print(f"[bold]Testing {platform}...[/bold]")
        console.print(f"[dim]Message: {message}[/dim]")

        result = await service._announcers[platform].post(message)

        if result.success:
            console.print(f"[green]✓ Success![/green] {result.url}")
        else:
            console.print(f"[red]✗ Failed:[/red] {result.error}")
            raise typer.Exit(1)

    asyncio.run(_test())


if __name__ == "__main__":
    app()
