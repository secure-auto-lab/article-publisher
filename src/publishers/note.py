"""Note publisher using Playwright browser automation."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from ..transformer.article import Article
from .base import Publisher, PublishResult

# Playwright is optional - only import when needed
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class NotePublisher(Publisher):
    """Publisher for Note using Playwright browser automation.

    Note does not provide a public API, so we use browser automation
    to publish articles. This is inherently fragile and may break
    if Note changes their UI.
    """

    platform_name = "note"

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        cookies_path: str | None = None,
    ):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for Note publishing. "
                "Install with: pip install playwright && playwright install chromium"
            )

        self.email = email or os.getenv("NOTE_EMAIL")
        self.password = password or os.getenv("NOTE_PASSWORD")
        self.cookies_path = Path(cookies_path or os.getenv("NOTE_COOKIES_PATH", "./.note_cookies.json"))

        if not self.email or not self.password:
            raise ValueError("NOTE_EMAIL and NOTE_PASSWORD are required")

    async def publish(self, article: Article, content: str) -> PublishResult:
        """Publish article to Note using browser automation."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()

                # Load cookies if available
                if self.cookies_path.exists():
                    cookies = await self._load_cookies()
                    if cookies:
                        await context.add_cookies(cookies)

                page = await context.new_page()

                # Login if needed
                if not await self._is_logged_in(page):
                    await self._login(page)
                    # Save cookies for next time
                    await self._save_cookies(context)

                # Create new article
                url = await self._create_article(page, article, content)

                await browser.close()

                if url:
                    return PublishResult.success_result(
                        platform=self.platform_name,
                        url=url,
                    )
                else:
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error="Failed to get published URL",
                    )

        except Exception as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=str(e),
            )

    async def update(self, article: Article, content: str, article_id: str) -> PublishResult:
        """Update existing Note article."""
        # Note doesn't have a simple update flow, would need to navigate to edit page
        return PublishResult.failure_result(
            platform=self.platform_name,
            error="Update not yet implemented for Note",
        )

    async def delete(self, article_id: str) -> PublishResult:
        """Delete Note article."""
        return PublishResult.failure_result(
            platform=self.platform_name,
            error="Delete not yet implemented for Note",
        )

    async def validate(self, article: Article) -> list[str]:
        """Validate article for Note-specific requirements."""
        errors = await super().validate(article)

        # Note price validation
        price = article.platforms.note.price
        if price != 0 and (price < 100 or price > 50000):
            errors.append("Note price must be 0 (free) or between 100-50000 yen")

        return errors

    async def _is_logged_in(self, page: Page) -> bool:
        """Check if already logged in to Note."""
        await page.goto("https://note.com/")
        await page.wait_for_load_state("networkidle")

        # Check for user menu or login button
        try:
            await page.wait_for_selector('[data-testid="user-menu"]', timeout=3000)
            return True
        except Exception:
            return False

    async def _login(self, page: Page) -> None:
        """Login to Note."""
        await page.goto("https://note.com/login")
        await page.wait_for_load_state("networkidle")

        # Fill login form
        await page.fill('input[name="email"]', self.email)
        await page.fill('input[name="password"]', self.password)

        # Click login button
        await page.click('button[type="submit"]')

        # Wait for redirect
        await page.wait_for_url("https://note.com/**", timeout=30000)
        await asyncio.sleep(2)  # Extra wait for session to establish

    async def _create_article(self, page: Page, article: Article, content: str) -> str | None:
        """Create new article on Note."""
        # Navigate to new article page
        await page.goto("https://note.com/new")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Enter title
        title_input = await page.wait_for_selector('[data-testid="title-input"]')
        if title_input:
            await title_input.fill(article.title)

        # Enter content - Note uses a rich text editor
        # We'll try to paste markdown content
        editor = await page.wait_for_selector('[data-testid="body-editor"]')
        if editor:
            await editor.click()
            await page.keyboard.type(content, delay=10)

        await asyncio.sleep(1)

        # Set price if paid article
        if article.platforms.note.price > 0:
            await self._set_price(page, article.platforms.note.price)

        # Save as draft or publish
        if article.platforms.note.status.value == "draft":
            save_button = await page.query_selector('[data-testid="save-draft"]')
            if save_button:
                await save_button.click()
        else:
            publish_button = await page.query_selector('[data-testid="publish"]')
            if publish_button:
                await publish_button.click()

        await asyncio.sleep(3)

        # Get the published URL
        return page.url if "note.com" in page.url else None

    async def _set_price(self, page: Page, price: int) -> None:
        """Set article price for paid content."""
        # Click price setting button
        price_button = await page.query_selector('[data-testid="price-setting"]')
        if price_button:
            await price_button.click()
            await asyncio.sleep(1)

            # Enter price
            price_input = await page.query_selector('[data-testid="price-input"]')
            if price_input:
                await price_input.fill(str(price))

    async def _save_cookies(self, context) -> None:
        """Save cookies for session persistence."""
        cookies = await context.cookies()
        import json
        self.cookies_path.write_text(json.dumps(cookies))

    async def _load_cookies(self) -> list | None:
        """Load saved cookies."""
        try:
            import json
            return json.loads(self.cookies_path.read_text())
        except Exception:
            return None
