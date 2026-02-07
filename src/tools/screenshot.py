"""Screenshot tool for capturing URLs, HTML files, and TSX components."""
from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class ScreenshotTool:
    """Capture screenshots from URLs, HTML files, or TSX/JSX components."""

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for screenshots. "
                "Install with: pip install playwright && playwright install chromium"
            )

    async def capture(
        self,
        source: str,
        output: str,
        full_page: bool = False,
        width: int = 1280,
        height: int = 720,
        selector: str | None = None,
        delay: int = 0,
        props: dict[str, Any] | None = None,
    ) -> str:
        """Capture screenshot from various sources.

        Args:
            source: URL, HTML file path, or TSX/JSX file path
            output: Output PNG file path
            full_page: Capture full scrollable page
            width: Viewport width
            height: Viewport height
            selector: CSS selector to capture specific element
            delay: Wait time in ms before capture
            props: Props for TSX/JSX component rendering

        Returns:
            Path to the saved screenshot
        """
        source_path = Path(source)

        # Determine source type
        if source.startswith(("http://", "https://")):
            return await self._capture_url(
                source, output, full_page, width, height, selector, delay
            )
        elif source_path.suffix in (".tsx", ".jsx"):
            return await self._capture_tsx(
                source, output, width, height, props
            )
        elif source_path.suffix in (".html", ".htm"):
            return await self._capture_html(
                source, output, full_page, width, height, selector, delay
            )
        else:
            raise ValueError(f"Unsupported source type: {source}")

    async def _capture_url(
        self,
        url: str,
        output: str,
        full_page: bool,
        width: int,
        height: int,
        selector: str | None,
        delay: int,
    ) -> str:
        """Capture screenshot from URL."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})

            await page.goto(url, wait_until="networkidle")

            if delay:
                await page.wait_for_timeout(delay)

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if selector:
                element = await page.query_selector(selector)
                if element:
                    await element.screenshot(path=str(output_path))
                else:
                    raise ValueError(f"Selector not found: {selector}")
            else:
                await page.screenshot(path=str(output_path), full_page=full_page)

            await browser.close()

        return str(output_path)

    async def _capture_html(
        self,
        html_path: str,
        output: str,
        full_page: bool,
        width: int,
        height: int,
        selector: str | None,
        delay: int,
    ) -> str:
        """Capture screenshot from HTML file."""
        html_content = Path(html_path).read_text(encoding="utf-8")

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})

            await page.set_content(html_content, wait_until="networkidle")

            if delay:
                await page.wait_for_timeout(delay)

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if selector:
                element = await page.query_selector(selector)
                if element:
                    await element.screenshot(path=str(output_path))
                else:
                    raise ValueError(f"Selector not found: {selector}")
            else:
                await page.screenshot(path=str(output_path), full_page=full_page)

            await browser.close()

        return str(output_path)

    async def _capture_tsx(
        self,
        tsx_path: str,
        output: str,
        width: int,
        height: int,
        props: dict[str, Any] | None,
    ) -> str:
        """Capture screenshot from TSX/JSX component."""
        # Bundle TSX with esbuild
        bundled_js = await self._bundle_tsx(tsx_path)

        # Generate props script
        props_json = json.dumps(props or {})

        # Create HTML with React and the bundled component
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={width}, initial-scale=1.0">
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ margin: 0; padding: 16px; background: white; }}
        #root {{ display: inline-block; }}
    </style>
</head>
<body>
    <div id="root"></div>
    <script>
        window.__COMPONENT_PROPS__ = {props_json};
    </script>
    <script type="module">
{bundled_js}
    </script>
</body>
</html>"""

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})

            await page.set_content(html_content)

            # Wait for component to render
            try:
                await page.wait_for_selector("#root > *", timeout=10000)
            except Exception:
                # Component might be empty or not rendered
                pass

            # Small delay for any async rendering
            await page.wait_for_timeout(500)

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Capture just the root element for tighter bounds
            root = await page.query_selector("#root")
            if root:
                await root.screenshot(path=str(output_path))
            else:
                await page.screenshot(path=str(output_path))

            await browser.close()

        return str(output_path)

    async def _bundle_tsx(self, tsx_path: str) -> str:
        """Bundle TSX/JSX file with esbuild."""
        tsx_file = Path(tsx_path)
        if not tsx_file.exists():
            raise FileNotFoundError(f"TSX file not found: {tsx_path}")

        # Read the original TSX content
        original_content = tsx_file.read_text(encoding="utf-8")

        # Create a wrapper that renders the component
        component_name = self._extract_component_name(original_content)

        wrapper_content = f"""{original_content}

// Auto-generated wrapper for screenshot
const props = window.__COMPONENT_PROPS__ || {{}};
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement({component_name}, props));
"""

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".tsx",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(wrapper_content)
            temp_path = f.name

        try:
            # Bundle with esbuild
            result = subprocess.run(
                [
                    "npx", "esbuild", temp_path,
                    "--bundle",
                    "--format=esm",
                    "--loader:.tsx=tsx",
                    "--loader:.jsx=jsx",
                    "--external:react",
                    "--external:react-dom",
                    "--define:process.env.NODE_ENV=\"production\"",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"esbuild failed: {result.stderr}")

            # Replace React imports with global references
            bundled = result.stdout
            bundled = bundled.replace(
                'from "react"',
                'from "https://esm.sh/react@18"'
            ).replace(
                'from "react-dom/client"',
                'from "https://esm.sh/react-dom@18/client"'
            )

            # Use global React/ReactDOM
            bundled = f"""
const React = window.React;
const ReactDOM = window.ReactDOM;
{bundled}
"""
            return bundled

        finally:
            # Cleanup temp file
            Path(temp_path).unlink(missing_ok=True)

    def _extract_component_name(self, tsx_content: str) -> str:
        """Extract the main component name from TSX content."""
        import re

        # Look for export default function ComponentName
        match = re.search(r"export\s+default\s+function\s+(\w+)", tsx_content)
        if match:
            return match.group(1)

        # Look for export default ComponentName
        match = re.search(r"export\s+default\s+(\w+)", tsx_content)
        if match:
            return match.group(1)

        # Look for function ComponentName (with capital letter)
        match = re.search(r"function\s+([A-Z]\w+)", tsx_content)
        if match:
            return match.group(1)

        # Look for const ComponentName = (
        match = re.search(r"const\s+([A-Z]\w+)\s*=", tsx_content)
        if match:
            return match.group(1)

        raise ValueError("Could not find component name in TSX file")


async def capture_screenshot(
    source: str,
    output: str = "./screenshot.png",
    full_page: bool = False,
    width: int = 1280,
    height: int = 720,
    selector: str | None = None,
    delay: int = 0,
    props: dict[str, Any] | None = None,
) -> str:
    """Convenience function to capture a screenshot."""
    tool = ScreenshotTool()
    return await tool.capture(
        source=source,
        output=output,
        full_page=full_page,
        width=width,
        height=height,
        selector=selector,
        delay=delay,
        props=props,
    )
