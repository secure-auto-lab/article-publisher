"""Note publisher using Playwright browser automation."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from ..transformer.article import Article
from .base import Publisher, PublishResult

# Playwright is optional - only import when needed
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
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
        headless: bool = True,
    ):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for Note publishing. "
                "Install with: pip install playwright && playwright install chromium"
            )

        self.email = email or os.getenv("NOTE_EMAIL")
        self.password = password or os.getenv("NOTE_PASSWORD")
        self.cookies_path = Path(cookies_path or os.getenv("NOTE_COOKIES_PATH", "./.note_cookies.json"))
        self.headless = headless

        if not self.email or not self.password:
            raise ValueError("NOTE_EMAIL and NOTE_PASSWORD are required")

    async def publish(self, article: Article, content: str) -> PublishResult:
        """Publish article to Note using browser automation."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()

                # Load cookies if available
                if self.cookies_path.exists():
                    cookies = self._load_cookies()
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

                if url and "/n/" in url:
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

    async def test_login(self) -> bool:
        """Test login to Note. Returns True if successful."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()

                # Load cookies if available
                if self.cookies_path.exists():
                    cookies = self._load_cookies()
                    if cookies:
                        await context.add_cookies(cookies)

                page = await context.new_page()

                # Check if already logged in
                if await self._is_logged_in(page):
                    print("Already logged in (from cookies)")
                    await browser.close()
                    return True

                # Try to login
                await self._login(page)
                await self._save_cookies(context)

                # Verify login
                success = await self._is_logged_in(page)
                await browser.close()

                return success

        except Exception as e:
            print(f"Login test failed: {e}")
            return False

    async def update(self, article: Article, content: str, article_id: str) -> PublishResult:
        """Update existing Note article."""
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
        await asyncio.sleep(3)

        # Check for elements that indicate logged-in state
        try:
            # Look for new post button, profile menu, or dashboard
            logged_in_selectors = [
                'a[href*="/notes/new"]',  # New post button
                'a[href*="/dashboard"]',   # Dashboard link
                '[class*="Profile"]',      # Profile menu
                '[class*="avatar"]',       # Avatar image
            ]

            for selector in logged_in_selectors:
                element = await page.query_selector(selector)
                if element:
                    return True

            # Also check if login button is NOT present
            login_button = await page.query_selector('a[href="/login"]')
            if not login_button:
                # No login button means likely logged in
                return True

            return False
        except Exception:
            return False

    async def _login(self, page: Page) -> None:
        """Login to Note."""
        await page.goto("https://note.com/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Find email/ID input (first input field)
        inputs = await page.query_selector_all('input')
        if len(inputs) >= 2:
            # Email field
            await inputs[0].fill(self.email)
            await asyncio.sleep(0.5)

            # Password field
            await inputs[1].fill(self.password)
            await asyncio.sleep(0.5)

        # Find and click login button
        buttons = await page.query_selector_all('button')
        for button in buttons:
            text = await button.text_content()
            if text and 'ログイン' in text:
                await button.click()
                break

        # Wait for redirect
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")

    async def _create_article(self, page: Page, article: Article, content: str, publish: bool = False) -> str | None:
        """Create new article on Note."""
        # Navigate to new text article page
        await page.goto("https://note.com/notes/new")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        # Enter title - Note uses textarea for title
        title_input = await page.query_selector('textarea')
        if title_input:
            await title_input.fill(article.title)

        await asyncio.sleep(1)

        # Enter content - find contenteditable editor
        editor = await page.query_selector('[contenteditable="true"]')
        if editor:
            await editor.click()
            # Type content line by line for proper formatting
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    await page.keyboard.type(line)
                if i < len(lines) - 1:
                    await page.keyboard.press('Enter')
                await asyncio.sleep(0.05)  # Small delay for stability

        await asyncio.sleep(2)

        if publish:
            # Click "公開に進む" button
            publish_button = await page.query_selector('button:has-text("公開に進む")')
            if publish_button:
                await publish_button.click()
                await asyncio.sleep(3)
                # Need to handle publish settings dialog here
                # For now, just return draft URL
        else:
            # Save as draft
            draft_button = await page.query_selector('button:has-text("下書き保存")')
            if draft_button:
                await draft_button.click()
                await asyncio.sleep(3)

        return page.url

    async def _set_price(self, page: Page, price: int) -> None:
        """Set article price for paid content."""
        # This needs to be updated based on Note's actual UI
        pass

    async def _save_cookies(self, context: BrowserContext) -> None:
        """Save cookies for session persistence."""
        cookies = await context.cookies()
        self.cookies_path.write_text(json.dumps(cookies))

    def _load_cookies(self) -> list | None:
        """Load saved cookies."""
        try:
            return json.loads(self.cookies_path.read_text())
        except Exception:
            return None
