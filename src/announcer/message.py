"""Message generator for SNS announcements."""
from __future__ import annotations

import re
import unicodedata

from ..transformer.article import Article


def twitter_weighted_len(text: str) -> int:
    """Calculate Twitter's weighted character count.

    Twitter counts CJK/full-width characters as 2 and URLs as 23.
    """
    text_no_urls = re.sub(r"https?://\S+", "x" * 23, text)
    count = 0
    for ch in text_no_urls:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            count += 2
        else:
            count += 1
    return count


def twitter_weighted_truncate(text: str, max_len: int) -> str:
    """Truncate text to fit within Twitter's weighted character limit."""
    if twitter_weighted_len(text) <= max_len:
        return text
    result = []
    count = 0
    i = 0
    while i < len(text):
        # Detect URL start
        if text[i:].startswith("http://") or text[i:].startswith("https://"):
            url_match = re.match(r"https?://\S+", text[i:])
            if url_match:
                url = url_match.group(0)
                if count + 23 > max_len:
                    break
                result.append(url)
                count += 23
                i += len(url)
                continue
        ch = text[i]
        w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if count + w > max_len:
            break
        result.append(ch)
        count += w
        i += 1
    return "".join(result)


class MessageGenerator:
    """Generate platform-optimized announcement messages."""

    # Platform-specific constraints
    TWITTER_MAX_LENGTH = 280
    BLUESKY_MAX_LENGTH = 300
    MISSKEY_MAX_LENGTH = 3000

    def generate(
        self,
        article: Article,
        platform: str,
        urls: dict[str, str],
    ) -> str:
        """Generate announcement message for specific platform.

        Args:
            article: The article being announced
            platform: Target SNS platform (twitter, bluesky, misskey)
            urls: Dict of platform -> published URL
        """
        if platform == "twitter":
            return self._generate_twitter(article, urls)
        elif platform == "bluesky":
            return self._generate_bluesky(article, urls)
        elif platform == "misskey":
            return self._generate_misskey(article, urls)
        else:
            return self._generate_default(article, urls)

    def _get_primary_url(self, urls: dict[str, str]) -> str:
        """Get the primary URL for SNS (blog only)."""
        return urls.get("blog") or urls.get("zenn") or urls.get("qiita") or ""

    def _generate_twitter(self, article: Article, urls: dict[str, str]) -> str:
        """Generate Twitter-optimized message (280 weighted char limit).

        Twitter counts CJK/full-width characters as 2 and URLs as 23.
        """
        url = self._get_primary_url(urls)
        hashtags = " ".join(f"#{tag}" for tag in article.tags[:3])

        msg = f"{article.title}\n\n{article.description[:120]}"

        if url:
            msg += f"\n\n{url}"

        if twitter_weighted_len(msg) + twitter_weighted_len(hashtags) + 2 <= self.TWITTER_MAX_LENGTH:
            msg += f"\n\n{hashtags}"

        return twitter_weighted_truncate(msg, self.TWITTER_MAX_LENGTH)

    def _generate_bluesky(self, article: Article, urls: dict[str, str]) -> str:
        """Generate Bluesky message."""
        url = self._get_primary_url(urls)

        msg = f"{article.title}\n\n{article.description[:150]}"

        if url:
            msg += f"\n\n{url}"

        return msg[:self.BLUESKY_MAX_LENGTH]

    def _generate_misskey(self, article: Article, urls: dict[str, str]) -> str:
        """Generate Misskey message (supports Markdown)."""
        url = self._get_primary_url(urls)
        hashtags = " ".join(f"#{tag}" for tag in article.tags[:5])

        msg = f"**{article.title}**\n\n{article.description}"

        if url:
            msg += f"\n\n{url}"

        msg += f"\n\n{hashtags}"
        return msg[:self.MISSKEY_MAX_LENGTH]

    def _generate_default(self, article: Article, urls: dict[str, str]) -> str:
        """Generate default message."""
        url = urls.get("blog") or list(urls.values())[0] if urls else ""

        return f"新記事公開: {article.title}\n{url}"
