"""OGP/Title image generator for articles.

Generates stylish 1200x630 OGP images from article metadata
using an HTML template + Playwright screenshot.
"""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# Color themes for variety
THEMES = {
    "default": {
        "bg_from": "#0f172a",
        "bg_via": "#1e293b",
        "bg_to": "#334155",
        "accent": "#38bdf8",
        "title_color": "#f8fafc",
        "tag_bg": "rgba(56, 189, 248, 0.15)",
        "tag_border": "rgba(56, 189, 248, 0.4)",
        "tag_color": "#7dd3fc",
        "sub_color": "#94a3b8",
        "pattern_color": "rgba(56, 189, 248, 0.06)",
    },
    "purple": {
        "bg_from": "#1a0533",
        "bg_via": "#2d1b4e",
        "bg_to": "#44337a",
        "accent": "#a78bfa",
        "title_color": "#f5f3ff",
        "tag_bg": "rgba(167, 139, 250, 0.15)",
        "tag_border": "rgba(167, 139, 250, 0.4)",
        "tag_color": "#c4b5fd",
        "sub_color": "#a5b4c8",
        "pattern_color": "rgba(167, 139, 250, 0.06)",
    },
    "green": {
        "bg_from": "#022c22",
        "bg_via": "#064e3b",
        "bg_to": "#065f46",
        "accent": "#34d399",
        "title_color": "#ecfdf5",
        "tag_bg": "rgba(52, 211, 153, 0.15)",
        "tag_border": "rgba(52, 211, 153, 0.4)",
        "tag_color": "#6ee7b7",
        "sub_color": "#94b8a8",
        "pattern_color": "rgba(52, 211, 153, 0.06)",
    },
    "orange": {
        "bg_from": "#1c1108",
        "bg_via": "#431407",
        "bg_to": "#7c2d12",
        "accent": "#fb923c",
        "title_color": "#fff7ed",
        "tag_bg": "rgba(251, 146, 60, 0.15)",
        "tag_border": "rgba(251, 146, 60, 0.4)",
        "tag_color": "#fdba74",
        "sub_color": "#b8a894",
        "pattern_color": "rgba(251, 146, 60, 0.06)",
    },
}


def _build_html(
    title: str,
    tags: list[str],
    author: str = "secure_auto_lab",
    theme_name: str = "default",
) -> str:
    """Build HTML for OGP image."""
    t = THEMES.get(theme_name, THEMES["default"])
    escaped_title = html.escape(title)

    # タイトル文字数に応じてフォントサイズを自動調整
    if len(title) <= 15:
        font_size = "72px"
        line_height = "1.25"
    elif len(title) <= 25:
        font_size = "62px"
        line_height = "1.3"
    elif len(title) <= 40:
        font_size = "52px"
        line_height = "1.35"
    elif len(title) <= 55:
        font_size = "44px"
        line_height = "1.4"
    else:
        font_size = "38px"
        line_height = "1.4"

    tags_html = "".join(
        f'<span class="tag">{html.escape(tag)}</span>' for tag in tags[:5]
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Inter:wght@400;600;800&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    width: 1200px;
    height: 630px;
    overflow: hidden;
    font-family: 'Inter', 'Noto Sans JP', sans-serif;
}}

.card {{
    width: 1200px;
    height: 630px;
    background: linear-gradient(135deg, {t['bg_from']} 0%, {t['bg_via']} 50%, {t['bg_to']} 100%);
    position: relative;
    display: flex;
    flex-direction: column;
    padding: 0 80px;
}}

/* Geometric pattern overlay */
.card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        radial-gradient(circle at 20% 80%, {t['accent']}22 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, {t['accent']}18 0%, transparent 50%),
        repeating-linear-gradient(
            45deg,
            transparent,
            transparent 40px,
            {t['pattern_color']} 40px,
            {t['pattern_color']} 41px
        );
    pointer-events: none;
}}

/* タイトル領域：カード中央に配置 */
.title-area {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    position: relative;
    z-index: 1;
    padding-top: 20px;
}}

/* アクセントライン */
.accent-line {{
    width: 80px;
    height: 4px;
    background: {t['accent']};
    border-radius: 2px;
    margin-bottom: 24px;
}}

.title {{
    font-size: {font_size};
    font-weight: 900;
    color: {t['title_color']};
    line-height: {line_height};
    letter-spacing: -0.02em;
    text-align: center;
    text-shadow: 0 2px 16px rgba(0,0,0,0.4);
    max-width: 1040px;
}}

/* 下部エリア：タグ+フッター */
.bottom-area {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    z-index: 1;
    padding-bottom: 32px;
}}

.tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}}

.tag {{
    background: {t['tag_bg']};
    border: 1px solid {t['tag_border']};
    color: {t['tag_color']};
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.02em;
}}

.footer {{
    display: flex;
    align-items: center;
    gap: 16px;
}}

.author {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.author-icon {{
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, {t['accent']}, {t['accent']}88);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 800;
    color: {t['bg_from']};
}}

.author-name {{
    color: {t['sub_color']};
    font-size: 16px;
    font-weight: 600;
}}

/* Corner decoration */
.corner-tl, .corner-br {{
    position: absolute;
    width: 120px;
    height: 120px;
    border: 2px solid {t['accent']}20;
    z-index: 0;
}}
.corner-tl {{
    top: 24px;
    left: 24px;
    border-right: none;
    border-bottom: none;
}}
.corner-br {{
    bottom: 24px;
    right: 24px;
    border-left: none;
    border-top: none;
}}
</style>
</head>
<body>
<div class="card">
    <div class="corner-tl"></div>
    <div class="corner-br"></div>
    <div class="title-area">
        <div class="accent-line"></div>
        <div class="title">{escaped_title}</div>
    </div>
    <div class="bottom-area">
        <div class="tags">{tags_html}</div>
        <div class="footer">
            <div class="author">
                <div class="author-icon">S</div>
                <div class="author-name">@{html.escape(author)}</div>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""


class OgpGenerator:
    """Generate OGP/title images for articles."""

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required. "
                "Install with: pip install playwright && playwright install chromium"
            )

    async def generate(
        self,
        title: str,
        tags: list[str],
        output: str,
        author: str = "secure_auto_lab",
        theme: str = "default",
    ) -> str:
        """Generate OGP image.

        Args:
            title: Article title
            tags: List of tags
            output: Output PNG file path
            author: Author name
            theme: Color theme (default, purple, green, orange)

        Returns:
            Path to the saved image
        """
        html_content = _build_html(title, tags, author, theme)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": 1200, "height": 630}
            )
            await page.set_content(html_content, wait_until="networkidle")
            # Wait for Google Fonts to load
            await page.wait_for_timeout(1500)

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            await page.screenshot(path=str(output_path))
            await browser.close()

        return str(output_path)

    async def generate_from_article(
        self,
        article: Any,
        output_dir: str = "./articles/images",
        theme: str = "default",
    ) -> str:
        """Generate OGP image from Article object.

        Returns:
            Path to the saved image
        """
        output = str(Path(output_dir) / f"{article.slug}-ogp.png")
        return await self.generate(
            title=article.title,
            tags=article.tags,
            output=output,
            author=article.author,
            theme=theme,
        )
