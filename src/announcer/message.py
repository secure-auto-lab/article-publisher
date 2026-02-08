"""Message generator for SNS announcements."""
from __future__ import annotations

from ..transformer.article import Article


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
        """Generate Twitter-optimized message (280 char limit)."""
        url = self._get_primary_url(urls)
        hashtags = " ".join(f"#{tag}" for tag in article.tags[:3])

        msg = f"{article.title}\n\n{article.description[:120]}"

        if url:
            msg += f"\n\n{url}"

        if len(msg) + len(hashtags) + 2 <= self.TWITTER_MAX_LENGTH:
            msg += f"\n\n{hashtags}"

        return msg[:self.TWITTER_MAX_LENGTH]

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
