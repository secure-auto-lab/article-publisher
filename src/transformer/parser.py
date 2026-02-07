"""Article parser for unified markdown format."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import frontmatter

from .article import (
    AnnouncementConfig,
    Article,
    BlogPlatformConfig,
    NotePlatformConfig,
    PlatformConfig,
    PublishStatus,
    QiitaPlatformConfig,
    SeriesConfig,
    ZennPlatformConfig,
)


class ArticleParser:
    """Parse markdown files with frontmatter into Article objects."""

    def parse_file(self, file_path: str | Path) -> Article:
        """Parse a markdown file into an Article object."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Article file not found: {file_path}")

        with open(path, encoding="utf-8") as f:
            post = frontmatter.load(f)

        return self._parse_frontmatter(post.metadata, post.content, str(path))

    def parse_content(self, content: str) -> Article:
        """Parse markdown content string into an Article object."""
        post = frontmatter.loads(content)
        return self._parse_frontmatter(post.metadata, post.content)

    def _parse_frontmatter(
        self, metadata: dict, content: str, source_path: str | None = None
    ) -> Article:
        """Parse frontmatter metadata into Article object."""
        # Parse platform configs
        platforms_data = metadata.get("platforms", {})
        platforms = PlatformConfig(
            note=self._parse_note_config(platforms_data.get("note", {})),
            zenn=self._parse_zenn_config(platforms_data.get("zenn", {})),
            qiita=self._parse_qiita_config(platforms_data.get("qiita", {})),
            blog=self._parse_blog_config(platforms_data.get("blog", {})),
        )

        # Parse announcement config
        announcement_data = metadata.get("announcement", {})
        announcement = AnnouncementConfig(
            enabled=announcement_data.get("enabled", True),
            platforms=announcement_data.get("platforms", ["twitter", "bluesky", "misskey"]),
            message_template=announcement_data.get("message_template"),
        )

        # Parse series config
        series_data = metadata.get("series", {})
        series = SeriesConfig(
            name=series_data.get("name"),
            part=series_data.get("part"),
            total=series_data.get("total"),
        )

        # Parse dates
        created_at = self._parse_date(metadata.get("created_at", datetime.now()))
        updated_at = self._parse_date(metadata.get("updated_at", datetime.now()))

        return Article(
            title=metadata.get("title", "Untitled"),
            slug=metadata.get("slug", "untitled"),
            description=metadata.get("description", ""),
            content=content,
            tags=metadata.get("tags", []),
            category=metadata.get("category", "tech"),
            author=metadata.get("author", "tinou"),
            created_at=created_at,
            updated_at=updated_at,
            platforms=platforms,
            announcement=announcement,
            series=series,
            canonical_url=metadata.get("canonical_url"),
            source_path=source_path,
        )

    def _parse_note_config(self, data: dict) -> NotePlatformConfig:
        """Parse Note platform configuration."""
        return NotePlatformConfig(
            enabled=data.get("enabled", True),
            status=PublishStatus(data.get("status", "draft")),
            price=data.get("price", 0),
            scheduled_at=self._parse_date(data.get("scheduled_at")) if data.get("scheduled_at") else None,
            published_url=data.get("published_url"),
        )

    def _parse_zenn_config(self, data: dict) -> ZennPlatformConfig:
        """Parse Zenn platform configuration."""
        return ZennPlatformConfig(
            enabled=data.get("enabled", True),
            status=PublishStatus(data.get("status", "draft")),
            emoji=data.get("emoji", "📝"),
            topics=data.get("topics", []),
            article_type=data.get("type", "tech"),
            published_url=data.get("published_url"),
        )

    def _parse_qiita_config(self, data: dict) -> QiitaPlatformConfig:
        """Parse Qiita platform configuration."""
        return QiitaPlatformConfig(
            enabled=data.get("enabled", True),
            status=PublishStatus(data.get("status", "draft")),
            private=data.get("private", False),
            published_url=data.get("published_url"),
        )

    def _parse_blog_config(self, data: dict) -> BlogPlatformConfig:
        """Parse Blog platform configuration."""
        return BlogPlatformConfig(
            enabled=data.get("enabled", True),
            status=PublishStatus(data.get("status", "draft")),
            published_url=data.get("published_url"),
        )

    def _parse_date(self, value) -> datetime:
        """Parse date from various formats."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
            # Try date-only format
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                pass
        return datetime.now()

    def save_article(self, article: Article, file_path: str | Path) -> None:
        """Save an Article object back to a markdown file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        post = frontmatter.Post(article.content, **article.to_frontmatter_dict())

        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
