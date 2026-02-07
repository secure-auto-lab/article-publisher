"""Platform-specific markdown converters."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod

from .article import Article


class PlatformConverter(ABC):
    """Base class for platform-specific markdown converters."""

    @abstractmethod
    def convert(self, article: Article) -> str:
        """Convert article content to platform-specific format."""
        pass

    def _strip_platform_blocks(self, content: str, keep_platform: str) -> str:
        """Remove platform-specific blocks except for the specified platform."""
        # Pattern: <!-- platform:xxx --> ... <!-- endplatform -->
        pattern = r"<!-- platform:(\w+) -->\s*(.*?)\s*<!-- endplatform -->"

        def replacer(match):
            platform = match.group(1)
            block_content = match.group(2)
            if platform == keep_platform:
                return block_content
            return ""

        return re.sub(pattern, replacer, content, flags=re.DOTALL)


class NoteConverter(PlatformConverter):
    """Convert article to Note format."""

    def convert(self, article: Article) -> str:
        content = self._strip_platform_blocks(article.content, "note")

        # Note-specific transformations
        # Convert Mermaid to placeholder (Note doesn't support Mermaid)
        content = self._convert_mermaid(content)

        # Convert callouts to Note style
        content = self._convert_callouts(content)

        return content

    def _convert_mermaid(self, content: str) -> str:
        """Convert Mermaid diagrams to image placeholders."""
        pattern = r"```mermaid\n(.*?)\n```"
        replacement = "[Mermaid図: 画像に変換が必要です]"
        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    def _convert_callouts(self, content: str) -> str:
        """Convert callouts to Note-friendly format."""
        # :::note → Note doesn't have callouts, use bold text
        pattern = r":::\w+\n(.*?)\n:::"
        return re.sub(pattern, r"**\1**", content, flags=re.DOTALL)


class ZennConverter(PlatformConverter):
    """Convert article to Zenn format."""

    def convert(self, article: Article) -> str:
        content = self._strip_platform_blocks(article.content, "zenn")

        # Zenn-specific transformations
        content = self._convert_callouts(content)

        # Add Zenn frontmatter
        frontmatter = self._generate_frontmatter(article)

        return f"{frontmatter}\n\n{content}"

    def _generate_frontmatter(self, article: Article) -> str:
        """Generate Zenn-specific frontmatter."""
        topics_str = ", ".join(f'"{t}"' for t in article.platforms.zenn.topics[:5])
        published = "true" if article.platforms.zenn.status.value == "published" else "false"

        return f"""---
title: "{article.title}"
emoji: "{article.platforms.zenn.emoji}"
type: "{article.platforms.zenn.article_type}"
topics: [{topics_str}]
published: {published}
---"""

    def _convert_callouts(self, content: str) -> str:
        """Convert callouts to Zenn message format."""
        # :::note info → :::message
        content = re.sub(r":::note\s*(\w+)?", ":::message", content)
        return content


class QiitaConverter(PlatformConverter):
    """Convert article to Qiita format."""

    def convert(self, article: Article) -> str:
        content = self._strip_platform_blocks(article.content, "qiita")

        # Qiita-specific transformations
        content = self._convert_callouts(content)
        content = self._convert_mermaid(content)

        return content

    def _convert_callouts(self, content: str) -> str:
        """Convert callouts to Qiita note format."""
        # :::message → :::note info
        content = re.sub(r":::message", ":::note info", content)
        return content

    def _convert_mermaid(self, content: str) -> str:
        """Qiita doesn't support Mermaid, convert to image placeholders."""
        pattern = r"```mermaid\n(.*?)\n```"
        replacement = "[Mermaid図: 画像に変換が必要です]"
        return re.sub(pattern, replacement, content, flags=re.DOTALL)


class BlogConverter(PlatformConverter):
    """Convert article to blog (Astro) format."""

    def convert(self, article: Article) -> str:
        content = self._strip_platform_blocks(article.content, "blog")

        # Add Astro frontmatter
        frontmatter = self._generate_frontmatter(article)

        return f"{frontmatter}\n\n{content}"

    def _generate_frontmatter(self, article: Article) -> str:
        """Generate Astro-compatible frontmatter."""
        tags_str = ", ".join(f'"{t}"' for t in article.tags)

        return f"""---
title: "{article.title}"
description: "{article.description}"
pubDate: "{article.created_at.strftime('%Y-%m-%d')}"
updatedDate: "{article.updated_at.strftime('%Y-%m-%d')}"
tags: [{tags_str}]
author: "{article.author}"
---"""


class ConverterFactory:
    """Factory for creating platform converters."""

    _converters: dict[str, type[PlatformConverter]] = {
        "note": NoteConverter,
        "zenn": ZennConverter,
        "qiita": QiitaConverter,
        "blog": BlogConverter,
    }

    @classmethod
    def get_converter(cls, platform: str) -> PlatformConverter:
        """Get converter for specified platform."""
        converter_class = cls._converters.get(platform)
        if not converter_class:
            raise ValueError(f"Unknown platform: {platform}")
        return converter_class()

    @classmethod
    def convert_all(cls, article: Article) -> dict[str, str]:
        """Convert article to all enabled platforms."""
        results = {}
        for platform in article.get_enabled_platforms():
            converter = cls.get_converter(platform)
            results[platform] = converter.convert(article)
        return results
