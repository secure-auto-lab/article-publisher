"""Base publisher interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from ..transformer.article import Article


@dataclass
class PublishResult:
    """Result of a publish operation."""

    success: bool
    platform: str
    url: str | None = None
    error: str | None = None
    published_at: datetime | None = None

    @classmethod
    def success_result(cls, platform: str, url: str) -> "PublishResult":
        return cls(
            success=True,
            platform=platform,
            url=url,
            published_at=datetime.now(),
        )

    @classmethod
    def failure_result(cls, platform: str, error: str) -> "PublishResult":
        return cls(
            success=False,
            platform=platform,
            error=error,
        )


class Publisher(ABC):
    """Abstract base class for platform publishers."""

    platform_name: str = "base"

    @abstractmethod
    async def publish(self, article: Article, content: str) -> PublishResult:
        """Publish article content to the platform.

        Args:
            article: The article metadata
            content: Platform-specific converted content

        Returns:
            PublishResult with success status and URL or error
        """
        pass

    @abstractmethod
    async def update(self, article: Article, content: str, article_id: str) -> PublishResult:
        """Update an existing article on the platform.

        Args:
            article: The article metadata
            content: Platform-specific converted content
            article_id: The platform-specific article identifier

        Returns:
            PublishResult with success status and URL or error
        """
        pass

    @abstractmethod
    async def delete(self, article_id: str) -> PublishResult:
        """Delete an article from the platform.

        Args:
            article_id: The platform-specific article identifier

        Returns:
            PublishResult with success status or error
        """
        pass

    async def validate(self, article: Article) -> list[str]:
        """Validate article before publishing.

        Returns list of validation errors (empty if valid).
        """
        errors = []
        if not article.title:
            errors.append("Title is required")
        if not article.content:
            errors.append("Content is required")
        return errors
