"""Blog publisher using Astro content directory."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..transformer.article import Article
from .base import Publisher, PublishResult


class BlogPublisher(Publisher):
    """Publisher for Astro blog.

    Publishes articles by writing markdown files to the Astro
    blog content directory (blog/src/content/articles/).
    OGP images are copied to blog/public/images/ for public serving.
    """

    platform_name = "blog"
    BLOG_BASE_URL = "https://blog.secure-auto-lab.com"

    def __init__(self, blog_path: str | None = None):
        self.blog_path = Path(
            blog_path or os.getenv("BLOG_PATH", "./blog")
        )
        self.articles_path = self.blog_path / "src" / "content" / "articles"
        self.images_path = self.blog_path / "public" / "images"

    async def publish(
        self, article: Article, content: str, ogp_path: str | None = None
    ) -> PublishResult:
        """Publish article by writing to Astro blog content directory."""
        try:
            self.articles_path.mkdir(parents=True, exist_ok=True)

            article_file = self.articles_path / f"{article.slug}.md"
            article_file.write_text(content, encoding="utf-8")

            # Copy OGP image to public/images/
            if ogp_path and Path(ogp_path).exists():
                self.images_path.mkdir(parents=True, exist_ok=True)
                dest = self.images_path / f"{article.slug}-ogp.png"
                shutil.copy2(ogp_path, dest)

            url = f"{self.BLOG_BASE_URL}/articles/{article.slug}"
            return PublishResult.success_result(
                platform=self.platform_name,
                url=url,
            )

        except Exception as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=str(e),
            )

    async def update(self, article: Article, content: str, article_id: str) -> PublishResult:
        """Update existing blog article."""
        return await self.publish(article, content)

    async def delete(self, article_id: str) -> PublishResult:
        """Delete blog article."""
        try:
            article_file = self.articles_path / f"{article_id}.md"
            if article_file.exists():
                article_file.unlink()
                return PublishResult.success_result(platform=self.platform_name, url="")
            else:
                return PublishResult.failure_result(
                    platform=self.platform_name,
                    error="Article not found",
                )
        except Exception as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=str(e),
            )
