"""SNS announcement service."""
from __future__ import annotations

import asyncio
import os
import logging
from dataclasses import dataclass
from datetime import datetime

from ..transformer.article import Article
from .message import MessageGenerator

logger = logging.getLogger(__name__)

# Optional imports for SNS clients
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class AnnounceResult:
    """Result of an announcement operation."""

    success: bool
    platform: str
    url: str | None = None
    error: str | None = None


class TwitterAnnouncer:
    """Twitter/X announcement handler."""

    def __init__(self):
        if not TWEEPY_AVAILABLE:
            raise ImportError("tweepy is required for Twitter announcements")

        self.consumer_key = os.getenv("X_API_KEY")
        self.consumer_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

        self._client: tweepy.Client | None = None

    def _ensure_client(self) -> bool:
        if not all([
            self.consumer_key,
            self.consumer_secret,
            self.access_token,
            self.access_token_secret
        ]):
            return False

        if self._client is None:
            self._client = tweepy.Client(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
        return True

    async def post(self, message: str) -> AnnounceResult:
        if not self._ensure_client():
            return AnnounceResult(
                success=False,
                platform="twitter",
                error="Twitter credentials not configured"
            )

        try:
            response = self._client.create_tweet(text=message)
            tweet_id = response.data["id"]
            return AnnounceResult(
                success=True,
                platform="twitter",
                url=f"https://twitter.com/i/web/status/{tweet_id}"
            )
        except Exception as e:
            logger.error(f"Twitter post failed: {e}")
            return AnnounceResult(
                success=False,
                platform="twitter",
                error=str(e)
            )


class BlueskyAnnouncer:
    """Bluesky announcement handler using AT Protocol."""

    def __init__(self):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for Bluesky announcements")

        self.handle = os.getenv("BLUESKY_HANDLE")
        self.password = os.getenv("BLUESKY_PASSWORD")
        self._session: dict | None = None

    async def _create_session(self) -> bool:
        if not self.handle or not self.password:
            return False

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                json={"identifier": self.handle, "password": self.password}
            )
            if response.status_code == 200:
                self._session = response.json()
                return True
        return False

    async def post(self, message: str) -> AnnounceResult:
        if not self._session and not await self._create_session():
            return AnnounceResult(
                success=False,
                platform="bluesky",
                error="Bluesky credentials not configured"
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                    headers={"Authorization": f"Bearer {self._session['accessJwt']}"},
                    json={
                        "repo": self._session["did"],
                        "collection": "app.bsky.feed.post",
                        "record": {
                            "$type": "app.bsky.feed.post",
                            "text": message,
                            "createdAt": datetime.utcnow().isoformat() + "Z"
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    uri = data.get("uri", "")
                    # Convert AT URI to web URL
                    parts = uri.split("/")
                    if len(parts) >= 5:
                        rkey = parts[-1]
                        web_url = f"https://bsky.app/profile/{self.handle}/post/{rkey}"
                        return AnnounceResult(success=True, platform="bluesky", url=web_url)

                return AnnounceResult(
                    success=False,
                    platform="bluesky",
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Bluesky post failed: {e}")
            return AnnounceResult(success=False, platform="bluesky", error=str(e))


class MisskeyAnnouncer:
    """Misskey announcement handler."""

    def __init__(self):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for Misskey announcements")

        self.instance = os.getenv("MISSKEY_INSTANCE", "misskey.io")
        self.token = os.getenv("MISSKEY_TOKEN")

    async def post(self, message: str) -> AnnounceResult:
        if not self.token:
            return AnnounceResult(
                success=False,
                platform="misskey",
                error="Misskey token not configured"
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.instance}/api/notes/create",
                    json={
                        "i": self.token,
                        "text": message,
                        "visibility": "public"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    note_id = data.get("createdNote", {}).get("id")
                    if note_id:
                        return AnnounceResult(
                            success=True,
                            platform="misskey",
                            url=f"https://{self.instance}/notes/{note_id}"
                        )

                return AnnounceResult(
                    success=False,
                    platform="misskey",
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Misskey post failed: {e}")
            return AnnounceResult(success=False, platform="misskey", error=str(e))


class AnnouncementService:
    """Orchestrates announcements across multiple SNS platforms."""

    # Delay between platform posts (seconds)
    POST_INTERVAL = 300  # 5 minutes

    def __init__(self):
        self.message_generator = MessageGenerator()
        self._announcers: dict = {}

        # Initialize available announcers
        try:
            self._announcers["twitter"] = TwitterAnnouncer()
        except ImportError:
            logger.warning("Twitter announcer not available (tweepy not installed)")

        try:
            self._announcers["bluesky"] = BlueskyAnnouncer()
            self._announcers["misskey"] = MisskeyAnnouncer()
        except ImportError:
            logger.warning("Bluesky/Misskey announcers not available (httpx not installed)")

    async def announce_all(
        self,
        article: Article,
        published_urls: dict[str, str],
    ) -> list[AnnounceResult]:
        """Announce article publication to all configured platforms.

        Args:
            article: The published article
            published_urls: Dict of platform -> published URL

        Returns:
            List of AnnounceResult for each platform
        """
        if not article.announcement.enabled:
            logger.info("Announcements disabled for this article")
            return []

        results = []
        platforms = article.announcement.platforms

        for i, platform in enumerate(platforms):
            if platform not in self._announcers:
                logger.warning(f"Announcer not available for {platform}")
                continue

            # Generate platform-specific message
            message = self.message_generator.generate(article, platform, published_urls)

            # Post with delay between platforms
            if i > 0:
                await asyncio.sleep(self.POST_INTERVAL)

            result = await self._announcers[platform].post(message)
            results.append(result)

            if result.success:
                logger.info(f"Announced to {platform}: {result.url}")
            else:
                logger.error(f"Failed to announce to {platform}: {result.error}")

        return results

    async def announce_single(
        self,
        article: Article,
        platform: str,
        published_urls: dict[str, str],
    ) -> AnnounceResult:
        """Announce to a single platform."""
        if platform not in self._announcers:
            return AnnounceResult(
                success=False,
                platform=platform,
                error=f"Announcer not available for {platform}"
            )

        message = self.message_generator.generate(article, platform, published_urls)
        return await self._announcers[platform].post(message)
