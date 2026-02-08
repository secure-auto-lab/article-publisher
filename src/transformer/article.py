"""Article data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PublishStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class NotePlatformConfig:
    enabled: bool = True
    status: PublishStatus = PublishStatus.DRAFT
    price: int = 0  # 0 = free, 100-50000 = paid
    scheduled_at: datetime | None = None
    published_url: str | None = None


@dataclass
class ZennPlatformConfig:
    enabled: bool = True
    status: PublishStatus = PublishStatus.DRAFT
    emoji: str = "📝"
    topics: list[str] = field(default_factory=list)
    article_type: str = "tech"  # tech or idea
    published_url: str | None = None


@dataclass
class QiitaPlatformConfig:
    enabled: bool = True
    status: PublishStatus = PublishStatus.DRAFT
    private: bool = False
    published_url: str | None = None


@dataclass
class BlogPlatformConfig:
    enabled: bool = True
    status: PublishStatus = PublishStatus.DRAFT
    published_url: str | None = None


@dataclass
class PlatformConfig:
    note: NotePlatformConfig = field(default_factory=NotePlatformConfig)
    zenn: ZennPlatformConfig = field(default_factory=ZennPlatformConfig)
    qiita: QiitaPlatformConfig = field(default_factory=QiitaPlatformConfig)
    blog: BlogPlatformConfig = field(default_factory=BlogPlatformConfig)


@dataclass
class AnnouncementConfig:
    enabled: bool = True
    platforms: list[str] = field(default_factory=lambda: ["twitter", "bluesky", "misskey"])
    message_template: str | None = None


@dataclass
class SeriesConfig:
    name: str | None = None
    part: int | None = None
    total: int | None = None


@dataclass
class Article:
    """Unified article model with platform-specific configurations."""

    # Basic info
    title: str
    slug: str
    description: str
    content: str  # Raw markdown content (without frontmatter)

    # Metadata
    tags: list[str] = field(default_factory=list)
    category: str = "dev-tips"
    author: str = "tinou"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Platform configs
    platforms: PlatformConfig = field(default_factory=PlatformConfig)

    # Announcement
    announcement: AnnouncementConfig = field(default_factory=AnnouncementConfig)

    # Series (optional)
    series: SeriesConfig = field(default_factory=SeriesConfig)

    # Canonical URL (usually the blog URL)
    canonical_url: str | None = None

    # Source file path
    source_path: str | None = None

    def get_enabled_platforms(self) -> list[str]:
        """Return list of enabled platform names."""
        enabled = []
        if self.platforms.note.enabled:
            enabled.append("note")
        if self.platforms.zenn.enabled:
            enabled.append("zenn")
        if self.platforms.qiita.enabled:
            enabled.append("qiita")
        if self.platforms.blog.enabled:
            enabled.append("blog")
        return enabled

    def to_frontmatter_dict(self) -> dict[str, Any]:
        """Convert article to frontmatter dictionary for saving."""
        return {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "tags": self.tags,
            "category": self.category,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "platforms": {
                "note": {
                    "enabled": self.platforms.note.enabled,
                    "status": self.platforms.note.status.value,
                    "price": self.platforms.note.price,
                    "published_url": self.platforms.note.published_url,
                },
                "zenn": {
                    "enabled": self.platforms.zenn.enabled,
                    "status": self.platforms.zenn.status.value,
                    "emoji": self.platforms.zenn.emoji,
                    "topics": self.platforms.zenn.topics,
                    "published_url": self.platforms.zenn.published_url,
                },
                "qiita": {
                    "enabled": self.platforms.qiita.enabled,
                    "status": self.platforms.qiita.status.value,
                    "private": self.platforms.qiita.private,
                    "published_url": self.platforms.qiita.published_url,
                },
                "blog": {
                    "enabled": self.platforms.blog.enabled,
                    "status": self.platforms.blog.status.value,
                    "published_url": self.platforms.blog.published_url,
                },
            },
            "announcement": {
                "enabled": self.announcement.enabled,
                "platforms": self.announcement.platforms,
                "message_template": self.announcement.message_template,
            },
            "series": {
                "name": self.series.name,
                "part": self.series.part,
                "total": self.series.total,
            },
            "canonical_url": self.canonical_url,
        }
