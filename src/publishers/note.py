"""Note publisher using internal API.

Note's editor uses these internal API endpoints:
- POST /api/v1/text_notes          - Create new blank draft
- POST /api/v1/text_notes/draft_save?id={id}&is_temp_saved=true - Save draft content
- GET  /api/v3/notes/{key}         - Get note details
- GET  /api/v2/current_user        - Get current user info

Authentication is via session cookie (_note_session_v5).
Playwright is only used for initial login to obtain the session cookie.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from pathlib import Path

import httpx

from ..transformer.article import Article
from .base import Publisher, PublishResult

# Playwright is optional - only needed for login
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class NoteHtmlConverter:
    """Convert Markdown to Note-compatible HTML.

    Note uses <p> tags with UUID name/id attributes for paragraphs,
    and standard HTML tags for headings, code, etc.
    """

    def convert(self, markdown: str) -> tuple[str, int]:
        """Convert markdown to Note HTML.

        Returns:
            Tuple of (html_body, body_length)
        """
        lines = markdown.split("\n")
        html_parts = []
        text_length = 0
        i = 0

        while i < len(lines):
            line = lines[i]

            # Code block
            if line.startswith("```"):
                lang = line[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # skip closing ```
                code_text = "\n".join(code_lines)
                p_id = str(uuid.uuid4())
                if lang:
                    html_parts.append(
                        f'<code-block name="{p_id}" id="{p_id}" '
                        f'data-lang="{lang}">{self._escape_html(code_text)}</code-block>'
                    )
                else:
                    html_parts.append(
                        f'<code-block name="{p_id}" id="{p_id}">'
                        f'{self._escape_html(code_text)}</code-block>'
                    )
                text_length += len(code_text)
                continue

            # Heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                p_id = str(uuid.uuid4())
                html_parts.append(
                    f'<h{level} name="{p_id}" id="{p_id}">{self._inline(text)}</h{level}>'
                )
                text_length += len(text)
                i += 1
                continue

            # Horizontal rule
            if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line.strip()):
                html_parts.append("<hr>")
                i += 1
                continue

            # Empty line (skip)
            if not line.strip():
                i += 1
                continue

            # Image
            img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
            if img_match:
                alt = img_match.group(1)
                src = img_match.group(2)
                p_id = str(uuid.uuid4())
                html_parts.append(
                    f'<figure name="{p_id}" id="{p_id}">'
                    f'<img src="{self._escape_attr(src)}" alt="{self._escape_attr(alt)}">'
                    f'</figure>'
                )
                i += 1
                continue

            # Unordered list
            if re.match(r"^[-*+]\s", line):
                list_items = []
                while i < len(lines) and re.match(r"^[-*+]\s", lines[i]):
                    item_text = re.sub(r"^[-*+]\s+", "", lines[i])
                    list_items.append(item_text)
                    i += 1
                p_id = str(uuid.uuid4())
                items_html = "".join(
                    f"<li>{self._inline(item)}</li>" for item in list_items
                )
                html_parts.append(
                    f'<ul name="{p_id}" id="{p_id}">{items_html}</ul>'
                )
                text_length += sum(len(item) for item in list_items)
                continue

            # Ordered list
            if re.match(r"^\d+\.\s", line):
                list_items = []
                while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                    item_text = re.sub(r"^\d+\.\s+", "", lines[i])
                    list_items.append(item_text)
                    i += 1
                p_id = str(uuid.uuid4())
                items_html = "".join(
                    f"<li>{self._inline(item)}</li>" for item in list_items
                )
                html_parts.append(
                    f'<ol name="{p_id}" id="{p_id}">{items_html}</ol>'
                )
                text_length += sum(len(item) for item in list_items)
                continue

            # Blockquote
            if line.startswith("> "):
                quote_lines = []
                while i < len(lines) and lines[i].startswith("> "):
                    quote_lines.append(lines[i][2:])
                    i += 1
                p_id = str(uuid.uuid4())
                quote_text = "<br>".join(self._inline(ql) for ql in quote_lines)
                html_parts.append(
                    f'<blockquote name="{p_id}" id="{p_id}">'
                    f'<p>{quote_text}</p></blockquote>'
                )
                text_length += sum(len(ql) for ql in quote_lines)
                continue

            # Regular paragraph (may span multiple lines)
            para_lines = []
            while i < len(lines) and lines[i].strip() and not self._is_block_start(lines[i]):
                para_lines.append(lines[i])
                i += 1
            if para_lines:
                p_id = str(uuid.uuid4())
                para_text = "<br>".join(self._inline(pl) for pl in para_lines)
                html_parts.append(
                    f'<p name="{p_id}" id="{p_id}">{para_text}</p>'
                )
                text_length += sum(len(pl) for pl in para_lines)

        return "".join(html_parts), text_length

    def _is_block_start(self, line: str) -> bool:
        """Check if a line starts a block element."""
        if line.startswith("```"):
            return True
        if re.match(r"^#{1,6}\s", line):
            return True
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line.strip()):
            return True
        if re.match(r"^!\[", line):
            return True
        if re.match(r"^[-*+]\s", line):
            return True
        if re.match(r"^\d+\.\s", line):
            return True
        if line.startswith("> "):
            return True
        return False

    def _inline(self, text: str) -> str:
        """Convert inline markdown (bold, italic, code, links)."""
        # Inline code
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Italic
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # Links
        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            r'<a href="\2">\1</a>',
            text,
        )
        return text

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _escape_attr(self, text: str) -> str:
        """Escape HTML attribute value."""
        return (
            text.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


class NotePublisher(Publisher):
    """Publisher for Note using internal API.

    Uses Note's internal REST API for creating and saving drafts.
    Playwright is only used for initial login to obtain session cookies.
    """

    platform_name = "note"
    BASE_URL = "https://note.com"

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        cookies_path: str | None = None,
        urlname: str | None = None,
    ):
        self.email = email or os.getenv("NOTE_EMAIL")
        self.password = password or os.getenv("NOTE_PASSWORD")
        self.cookies_path = Path(
            cookies_path or os.getenv("NOTE_COOKIES_PATH", "./.note_cookies.json")
        )
        self.urlname = urlname or os.getenv("NOTE_URLNAME", "")
        self.html_converter = NoteHtmlConverter()

    def _load_cookies(self) -> dict[str, str] | None:
        """Load session cookies from file."""
        if not self.cookies_path.exists():
            return None
        try:
            cookies_list = json.loads(self.cookies_path.read_text())
            return {c["name"]: c["value"] for c in cookies_list}
        except Exception:
            return None

    def _get_headers(self, cookies: dict[str, str]) -> dict[str, str]:
        """Build request headers with session cookie."""
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            ),
            "Origin": "https://editor.note.com",
            "Referer": "https://editor.note.com/",
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": cookie_header,
        }

    async def _ensure_urlname(self, headers: dict[str, str]) -> str:
        """Get urlname from API if not set."""
        if self.urlname:
            return self.urlname
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/api/v2/current_user",
                headers=headers,
                timeout=15.0,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                self.urlname = data.get("urlname", "")
                return self.urlname
        return ""

    BLOG_BASE_URL = "https://blog.secure-auto-lab.com"

    async def publish(
        self, article: Article, content: str, ogp_path: str | None = None
    ) -> PublishResult:
        """Publish article to Note as a draft via API.

        Flow:
        1. Create blank draft via POST /api/v1/text_notes
        2. Convert markdown to Note HTML
        3. Prepend OGP image (if available, referencing blog URL)
        4. Save content via POST /api/v1/text_notes/draft_save
        """
        cookies = self._load_cookies()
        if not cookies or "_note_session_v5" not in cookies:
            if not await self._login_and_save_cookies():
                return PublishResult.failure_result(
                    platform=self.platform_name,
                    error="Not logged in. Run 'publisher note-login' first.",
                )
            cookies = self._load_cookies()
            if not cookies:
                return PublishResult.failure_result(
                    platform=self.platform_name,
                    error="Failed to load cookies after login.",
                )

        headers = self._get_headers(cookies)

        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Create blank draft
                resp = await client.post(
                    f"{self.BASE_URL}/api/v1/text_notes",
                    headers=headers,
                    json={"template_key": None},
                    timeout=15.0,
                )

                if resp.status_code != 201:
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error=f"Failed to create draft: HTTP {resp.status_code}",
                    )

                note_data = resp.json()["data"]
                note_id = note_data["id"]
                note_key = note_data["key"]

                # Step 2: Convert markdown to Note HTML
                body_html, body_length = self.html_converter.convert(content)

                # Step 3: Prepend OGP image referencing blog URL
                if ogp_path and Path(ogp_path).exists():
                    img_url = (
                        f"{self.BLOG_BASE_URL}/images/{article.slug}-ogp.png"
                    )
                    p_id = str(uuid.uuid4())
                    ogp_html = (
                        f'<figure name="{p_id}" id="{p_id}">'
                        f'<img src="{img_url}" alt="{article.title}">'
                        f'</figure>'
                    )
                    body_html = ogp_html + body_html
                    body_length += len(article.title)

                # Step 4: Save content
                save_payload = {
                    "body": body_html,
                    "body_length": body_length,
                    "name": article.title,
                    "index": False,
                    "is_lead_form": False,
                }

                resp = await client.post(
                    f"{self.BASE_URL}/api/v1/text_notes/draft_save"
                    f"?id={note_id}&is_temp_saved=true",
                    headers=headers,
                    json=save_payload,
                    timeout=30.0,
                )

                if resp.status_code == 201:
                    urlname = await self._ensure_urlname(headers)
                    draft_url = f"{self.BASE_URL}/{urlname}/n/{note_key}"
                    return PublishResult.success_result(
                        platform=self.platform_name,
                        url=draft_url,
                    )
                else:
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error=f"Failed to save draft: HTTP {resp.status_code}",
                    )

        except httpx.RequestError as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=f"Request failed: {str(e)}",
            )

    async def update(self, article: Article, content: str, article_id: str) -> PublishResult:
        """Update existing Note article.

        article_id should be the note numeric ID.
        """
        cookies = self._load_cookies()
        if not cookies or "_note_session_v5" not in cookies:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error="Not logged in. Run 'publisher note-login' first.",
            )

        headers = self._get_headers(cookies)

        try:
            async with httpx.AsyncClient() as client:
                body_html, body_length = self.html_converter.convert(content)

                save_payload = {
                    "body": body_html,
                    "body_length": body_length,
                    "name": article.title,
                    "index": False,
                    "is_lead_form": False,
                }

                resp = await client.post(
                    f"{self.BASE_URL}/api/v1/text_notes/draft_save"
                    f"?id={article_id}&is_temp_saved=true",
                    headers=headers,
                    json=save_payload,
                    timeout=30.0,
                )

                if resp.status_code == 201:
                    return PublishResult.success_result(
                        platform=self.platform_name,
                        url=f"{self.BASE_URL}/n/{article_id}",
                    )
                else:
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error=f"Update failed: HTTP {resp.status_code}",
                    )

        except httpx.RequestError as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=f"Request failed: {str(e)}",
            )

    async def delete(self, article_id: str) -> PublishResult:
        """Delete Note article."""
        return PublishResult.failure_result(
            platform=self.platform_name,
            error="Delete not implemented for Note",
        )

    async def validate(self, article: Article) -> list[str]:
        """Validate article for Note-specific requirements."""
        errors = await super().validate(article)

        price = article.platforms.note.price
        if price != 0 and (price < 100 or price > 50000):
            errors.append("Note price must be 0 (free) or between 100-50000 yen")

        return errors

    async def test_login(self) -> bool:
        """Test if current cookies are valid."""
        cookies = self._load_cookies()
        if not cookies or "_note_session_v5" not in cookies:
            return False

        headers = self._get_headers(cookies)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}/api/v2/current_user",
                    headers=headers,
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    self.urlname = data.get("urlname", "")
                    return True
        except Exception:
            pass
        return False

    async def _login_and_save_cookies(self) -> bool:
        """Login to Note via Playwright and save session cookies."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        if not self.email or not self.password:
            return False

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto("https://note.com/login")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                inputs = await page.query_selector_all("input")
                if len(inputs) >= 2:
                    await inputs[0].fill(self.email)
                    await asyncio.sleep(0.5)
                    await inputs[1].fill(self.password)
                    await asyncio.sleep(0.5)

                buttons = await page.query_selector_all("button")
                for button in buttons:
                    text = await button.text_content()
                    if text and "ログイン" in text:
                        await button.click()
                        break

                await asyncio.sleep(5)
                await page.wait_for_load_state("networkidle")

                # Save cookies
                cookies = await context.cookies()
                self.cookies_path.write_text(json.dumps(cookies))

                # Verify login
                session_cookie = next(
                    (c for c in cookies if c["name"] == "_note_session_v5"), None
                )
                await browser.close()
                return session_cookie is not None

        except Exception:
            return False
