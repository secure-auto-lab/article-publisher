"""Qiita API publisher."""
from __future__ import annotations

import os
from typing import Any

import httpx

from ..transformer.article import Article
from .base import Publisher, PublishResult


class QiitaPublisher(Publisher):
    """Qiita REST API v2を使用したパブリッシャー。"""

    platform_name = "qiita"
    BASE_URL = "https://qiita.com/api/v2"
    BLOG_BASE_URL = "https://blog.secure-auto-lab.com/articles"

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token or os.getenv("QIITA_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("QIITA_ACCESS_TOKEN is required")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def publish(self, article: Article, content: str) -> PublishResult:
        """Publish a new article to Qiita."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/items",
                    headers=self.headers,
                    json=self._build_payload(article, content),
                    timeout=30.0,
                )

                if response.status_code == 201:
                    data = response.json()
                    return PublishResult.success_result(
                        platform=self.platform_name,
                        url=data["url"],
                    )
                else:
                    error_msg = self._parse_error(response)
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error=f"HTTP {response.status_code}: {error_msg}",
                    )

        except httpx.RequestError as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=f"Request failed: {str(e)}",
            )

    async def update(self, article: Article, content: str, article_id: str) -> PublishResult:
        """Update an existing article on Qiita."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.BASE_URL}/items/{article_id}",
                    headers=self.headers,
                    json=self._build_payload(article, content),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return PublishResult.success_result(
                        platform=self.platform_name,
                        url=data["url"],
                    )
                else:
                    error_msg = self._parse_error(response)
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error=f"HTTP {response.status_code}: {error_msg}",
                    )

        except httpx.RequestError as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=f"Request failed: {str(e)}",
            )

    async def delete(self, article_id: str) -> PublishResult:
        """Delete an article from Qiita."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.BASE_URL}/items/{article_id}",
                    headers=self.headers,
                    timeout=30.0,
                )

                if response.status_code == 204:
                    return PublishResult.success_result(
                        platform=self.platform_name,
                        url="",
                    )
                else:
                    error_msg = self._parse_error(response)
                    return PublishResult.failure_result(
                        platform=self.platform_name,
                        error=f"HTTP {response.status_code}: {error_msg}",
                    )

        except httpx.RequestError as e:
            return PublishResult.failure_result(
                platform=self.platform_name,
                error=f"Request failed: {str(e)}",
            )

    async def validate(self, article: Article) -> list[str]:
        """Validate article for Qiita-specific requirements."""
        errors = await super().validate(article)

        # Qiita requires at least one tag
        if not article.tags:
            errors.append("At least one tag is required for Qiita")

        # Title length limit
        if len(article.title) > 100:
            errors.append("Title must be 100 characters or less")

        # Tag count limit
        if len(article.tags) > 5:
            errors.append("Maximum 5 tags allowed")

        # Tags must not contain spaces (Qiita API rejects them with 403)
        for tag in article.tags:
            if " " in tag:
                errors.append(
                    f"Tag '{tag}' contains spaces. "
                    "Qiita tags must not contain spaces (e.g. 'TailwindCSS' not 'Tailwind CSS')"
                )

        return errors

    def _build_payload(self, article: Article, content: str) -> dict[str, Any]:
        """Qiita APIペイロードを構築する。canonical_urlでブログを正規URLに指定。"""
        canonical_url = f"{self.BLOG_BASE_URL}/{article.slug}"
        return {
            "title": article.title,
            "body": content,
            "tags": [{"name": tag} for tag in article.tags[:5]],
            "private": article.platforms.qiita.private,
            "tweet": False,  # SNS告知は別途実行
            "canonical_url": canonical_url,
        }

    def _parse_error(self, response: httpx.Response) -> str:
        """Parse error message from Qiita API response."""
        try:
            data = response.json()
            if "message" in data:
                return data["message"]
            if "error" in data:
                return data["error"]
            return str(data)
        except Exception:
            return response.text
