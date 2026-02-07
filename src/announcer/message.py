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

    def _generate_twitter(self, article: Article, urls: dict[str, str]) -> str:
        """Generate Twitter-optimized message (280 char limit)."""
        # Priority: blog > note > zenn > qiita
        url = urls.get("blog") or urls.get("note") or urls.get("zenn") or urls.get("qiita") or ""

        # Short hashtags
        hashtags = " ".join(f"#{tag}" for tag in article.tags[:2])

        # Build message with length limit
        base = f"新記事公開\n\n{article.title}\n\n{url}"

        if len(base) + len(hashtags) + 2 <= self.TWITTER_MAX_LENGTH:
            return f"{base}\n\n{hashtags}"

        return base[:self.TWITTER_MAX_LENGTH]

    def _generate_bluesky(self, article: Article, urls: dict[str, str]) -> str:
        """Generate Bluesky message."""
        url = urls.get("blog") or urls.get("note") or urls.get("zenn") or urls.get("qiita") or ""

        return f"""新記事を公開しました

{article.title}

{article.description[:100]}{"..." if len(article.description) > 100 else ""}

{url}"""

    def _generate_misskey(self, article: Article, urls: dict[str, str]) -> str:
        """Generate Misskey message (supports Markdown)."""
        url = urls.get("blog") or urls.get("note") or urls.get("zenn") or urls.get("qiita") or ""
        hashtags = " ".join(f"#{tag}" for tag in article.tags)

        return f"""**新記事を公開しました**

**{article.title}**

{article.description}

{url}

{hashtags}"""

    def _generate_default(self, article: Article, urls: dict[str, str]) -> str:
        """Generate default message."""
        url = urls.get("blog") or list(urls.values())[0] if urls else ""

        return f"新記事公開: {article.title}\n{url}"
