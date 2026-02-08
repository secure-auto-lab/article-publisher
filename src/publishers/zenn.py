"""Zenn publisher using Git-based workflow."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ..transformer.article import Article
from .base import Publisher, PublishResult


class ZennPublisher(Publisher):
    """Publisher for Zenn using GitHub repository integration.

    Zenn articles are published by pushing markdown files to a connected
    GitHub repository. This publisher manages the local zenn-content
    directory and handles git operations.
    OGP images are copied to zenn-content/images/ and embedded at the
    top of the article content.
    """

    platform_name = "zenn"

    def __init__(self, zenn_content_path: str | None = None):
        self.content_path = Path(
            zenn_content_path or os.getenv("ZENN_CONTENT_PATH", "./zenn-content")
        )
        self.articles_path = self.content_path / "articles"
        self.images_path = self.content_path / "images"

    async def publish(
        self, article: Article, content: str, ogp_path: str | None = None
    ) -> PublishResult:
        """Publish article by writing to zenn-content and pushing to GitHub."""
        try:
            # Ensure directories exist
            self.articles_path.mkdir(parents=True, exist_ok=True)

            # Copy OGP image and embed in content
            git_files = [f"articles/{article.slug}.md"]
            if ogp_path and Path(ogp_path).exists():
                self.images_path.mkdir(parents=True, exist_ok=True)
                img_filename = f"{article.slug}-ogp.png"
                dest = self.images_path / img_filename
                shutil.copy2(ogp_path, dest)
                git_files.append(f"images/{img_filename}")

                # Insert OGP image after frontmatter
                content = self._insert_ogp_image(content, img_filename)

            # Write article file
            article_file = self.articles_path / f"{article.slug}.md"
            article_file.write_text(content, encoding="utf-8")

            # Git operations
            git_result = await self._git_push(
                git_files, f"Add article: {article.title}"
            )

            if git_result:
                # Zenn URL pattern
                url = f"https://zenn.dev/{os.getenv('ZENN_USERNAME', 'tinou')}/articles/{article.slug}"
                return PublishResult.success_result(
                    platform=self.platform_name,
                    url=url,
                )
            else:
                return PublishResult.failure_result(
                    platform=self.platform_name,
                    error="Git push failed",
                )

        except Exception as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=str(e),
            )

    def _insert_ogp_image(self, content: str, img_filename: str) -> str:
        """Insert OGP image reference after frontmatter."""
        # Find end of frontmatter (second ---)
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = f"---{parts[1]}---"
            body = parts[2]
            return f"{frontmatter}\n\n![OGP](/images/{img_filename})\n{body}"
        # No frontmatter found, prepend image
        return f"![OGP](/images/{img_filename})\n\n{content}"

    async def update(self, article: Article, content: str, article_id: str) -> PublishResult:
        """Update existing article (same as publish for Git-based workflow)."""
        try:
            article_file = self.articles_path / f"{article_id}.md"
            article_file.write_text(content, encoding="utf-8")

            git_result = await self._git_push(
                [f"articles/{article_id}.md"], f"Update article: {article.title}"
            )

            if git_result:
                url = f"https://zenn.dev/{os.getenv('ZENN_USERNAME', 'tinou')}/articles/{article_id}"
                return PublishResult.success_result(
                    platform=self.platform_name,
                    url=url,
                )
            else:
                return PublishResult.failure_result(
                    platform=self.platform_name,
                    error="Git push failed",
                )

        except Exception as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=str(e),
            )

    async def delete(self, article_id: str) -> PublishResult:
        """Delete article by removing file and pushing."""
        try:
            article_file = self.articles_path / f"{article_id}.md"

            if article_file.exists():
                article_file.unlink()
                git_result = await self._git_push(
                    [f"articles/{article_id}.md"], f"Delete article: {article_id}"
                )

                if git_result:
                    return PublishResult.success_result(
                        platform=self.platform_name,
                        url="",
                    )
                else:
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error="Git push failed",
                    )
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

    async def validate(self, article: Article) -> list[str]:
        """Validate article for Zenn-specific requirements."""
        errors = await super().validate(article)

        # Slug validation (Zenn requirements)
        if not article.slug:
            errors.append("Slug is required for Zenn")
        elif len(article.slug) < 12 or len(article.slug) > 50:
            errors.append("Slug must be 12-50 characters for Zenn")
        elif not article.slug.replace("-", "").replace("_", "").isalnum():
            errors.append("Slug must contain only alphanumeric characters, hyphens, and underscores")

        # Topics validation
        if not article.platforms.zenn.topics:
            errors.append("At least one topic is required for Zenn")
        elif len(article.platforms.zenn.topics) > 5:
            errors.append("Maximum 5 topics allowed for Zenn")

        return errors

    async def _git_push(self, files: list[str], commit_message: str) -> bool:
        """Execute git add, commit, and push.

        Args:
            files: List of file paths relative to zenn-content root
            commit_message: Git commit message
        """
        try:
            cwd = str(self.content_path)

            # Git add all files
            subprocess.run(
                ["git", "add"] + files,
                cwd=cwd,
                check=True,
                capture_output=True,
            )

            # Git commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

            # Git push
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

            return True

        except subprocess.CalledProcessError:
            return False
