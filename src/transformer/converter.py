"""Platform-specific markdown converters."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod

from ..config import resolve_category
from .article import Article


class PlatformConverter(ABC):
    """Base class for platform-specific markdown converters."""

    @abstractmethod
    def convert(self, article: Article) -> str:
        """Convert article content to platform-specific format."""
        pass

    def _strip_platform_blocks(self, content: str, keep_platform: str) -> str:
        """Remove platform-specific blocks except for the specified platform."""
        # Pattern: <!-- platform:xxx --> ... <!-- endplatform -->
        pattern = r"<!-- platform:(\w+) -->\s*(.*?)\s*<!-- endplatform -->"

        def replacer(match):
            platform = match.group(1)
            block_content = match.group(2)
            if platform == keep_platform:
                return block_content
            return ""

        return re.sub(pattern, replacer, content, flags=re.DOTALL)


class NoteConverter(PlatformConverter):
    """Note形式に変換するコンバーター。

    非エンジニア層向けにストーリー・感情重視の内容に変換する。
    - 技術的な実装セクション（コード、FAQ、参考リンク等）を自動除去
    - ASCII図やテクニカルテーブルを除去
    - インラインコードをプレーンテキスト化
    - 末尾にブログへの誘導リンクを追加
    """

    BLOG_BASE_URL = "https://blog.secure-auto-lab.com/articles"

    # 技術的な実装セクションと判定する見出しキーワード
    _TECHNICAL_KEYWORDS = [
        "具体的な実装", "実装方法", "実装手順", "実装詳細",
        "アーキテクチャ", "全体構成",
        "環境構築", "セットアップ", "インストール",
        "FAQ", "よくある質問",
        "参考リンク", "参考文献", "参考資料",
        "ハマりポイント", "トラブルシューティング",
        "コマンド一覧", "API仕様", "エンドポイント",
    ]

    def convert(self, article: Article) -> str:
        content = self._strip_platform_blocks(article.content, "note")

        # 技術的なセクションを見出し単位で除去
        content = self._remove_technical_sections(content)

        # コードブロックを除去（Mermaid含む）
        content = self._remove_code_blocks(content)

        # ASCII図（ボックス描画文字）を除去
        content = self._remove_ascii_diagrams(content)

        # インラインコードのバッククォートを除去（テキストは残す）
        content = self._remove_inline_code(content)

        # Calloutを変換
        content = self._convert_callouts(content)

        # 元記事末尾のシェア促進テキストを除去
        content = self._remove_share_cta(content)

        # 連続空行を整理
        content = self._clean_empty_lines(content)

        # 末尾にブログ誘導リンクとNote用CTAを追加
        content = self._add_blog_link(content, article.slug)

        return content

    def _remove_technical_sections(self, content: str) -> str:
        """技術的なセクションを見出し単位で除去する。

        技術キーワードを含む##/###見出しを検出し、
        次の同レベル以上の見出しまでの内容を丸ごとスキップする。
        """
        lines = content.split("\n")
        result = []
        skip = False
        skip_level = 0

        for line in lines:
            heading_match = re.match(r"^(#{2,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)

                if self._is_technical_heading(text):
                    # 技術セクション開始 → スキップ
                    skip = True
                    skip_level = level
                    continue
                elif skip and level <= skip_level:
                    # 同レベル以上の非技術見出し → スキップ解除
                    skip = False

            if not skip:
                result.append(line)

        return "\n".join(result)

    def _is_technical_heading(self, text: str) -> bool:
        """見出しが技術的な実装セクションかどうかを判定する。"""
        # 絵文字を除去して判定
        clean = re.sub(r"[\U0001f300-\U0001f9ff\u2600-\u27bf\u2700-\u27bf]", "", text).strip()
        # キーワードマッチ
        if any(kw in clean for kw in self._TECHNICAL_KEYWORDS):
            return True
        # "Step N" パターン
        if re.match(r"Step\s*\d", clean, re.IGNORECASE):
            return True
        return False

    def _remove_code_blocks(self, content: str) -> str:
        """フェンスコードブロックを除去する。"""
        return re.sub(r"```[\w]*\n.*?\n```", "", content, flags=re.DOTALL)

    def _remove_ascii_diagrams(self, content: str) -> str:
        """ASCII図（ボックス描画文字を含む行）を除去する。"""
        return re.sub(
            r"^.*[┌┐└┘│├┤┬┴┼─═║╔╗╚╝╠╣╦╩╬▶▼►◆→←↑↓].*$",
            "",
            content,
            flags=re.MULTILINE,
        )

    def _remove_inline_code(self, content: str) -> str:
        """インラインコードのバッククォートを除去する（テキストは残す）。"""
        return re.sub(r"`([^`]+)`", r"\1", content)

    def _convert_callouts(self, content: str) -> str:
        """Calloutをテキストに変換する。"""
        pattern = r":::\w+\n(.*?)\n:::"
        return re.sub(pattern, r"**\1**", content, flags=re.DOTALL)

    def _clean_empty_lines(self, content: str) -> str:
        """連続する空行を2行までに整理する。"""
        return re.sub(r"\n{3,}", "\n\n", content)

    def _remove_share_cta(self, content: str) -> str:
        """元記事末尾のシェア促進テキストを除去する（Note用フッターに置換するため）。"""
        # HTMLコメント + シェア促進の定型文を除去
        content = re.sub(r"<!-- SNS共有の促進 -->\s*", "", content)
        content = re.sub(
            r"\*\*この記事が役に立ったら、ぜひシェアをお願いします.*?\*\*\s*",
            "",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(r"あなたのシェアが、同じ悩みを持つ誰かの助けになります。\s*", "", content)
        return content

    def _add_blog_link(self, content: str, slug: str) -> str:
        """末尾にブログ誘導リンクとNote用CTAを追加する。"""
        blog_url = f"{self.BLOG_BASE_URL}/{slug}"
        # 末尾の余分な区切り線を除去してからフッターを付ける
        content = re.sub(r"(\n---\s*)+$", "", content.rstrip())
        return content + f"""

---

**この記事が気に入ったら「スキ」をお願いします！**

技術的な実装の詳細やソースコードに興味がある方は、ブログで全文を公開しています。

**[>> 詳しい実装はこちら]({blog_url})**
"""


class ZennConverter(PlatformConverter):
    """Zenn形式に変換するコンバーター。

    技術者向けにコード・実装重視の内容に変換する。
    - ストーリー・感情セクション（悩み、体験談、教訓等）を自動除去
    - コードブロック・技術解説はそのまま保持
    - 末尾にブログ全文への誘導リンクを追加
    """

    BLOG_BASE_URL = "https://blog.secure-auto-lab.com/articles"

    # ストーリー・感情セクションと判定する見出しキーワード
    _STORY_KEYWORDS = [
        "悩み", "抱えていませんか",
        "ストーリー", "道のり",
        "なぜこのアプローチ", "アプローチを選んだ",
        "壁にぶつかった", "乗り越え方",
        "教訓", "学んだ", "学び",
        "おわりに", "伝えたかった",
        "この記事で得られること",
        "Before", "After", "転機",
        "どん底", "絶望", "突破口",
        "発想の転換",
    ]

    def convert(self, article: Article) -> str:
        content = self._strip_platform_blocks(article.content, "zenn")

        # ストーリー・感情セクションを見出し単位で除去
        content = self._remove_story_sections(content)

        # 元記事末尾のシェア促進テキストを除去
        content = self._remove_share_cta(content)

        # Zenn固有の変換
        content = self._convert_callouts(content)

        # 連続空行を整理
        content = self._clean_empty_lines(content)

        # 末尾にブログ全文への誘導リンクを追加
        content = self._add_blog_link(content, article.slug)

        # Zenn用frontmatterを追加
        frontmatter = self._generate_frontmatter(article)

        return f"{frontmatter}\n\n{content}"

    def _generate_frontmatter(self, article: Article) -> str:
        """Zenn用frontmatterを生成する。canonical URLでブログを正規URLに指定。"""
        topics_str = ", ".join(f'"{t}"' for t in article.platforms.zenn.topics[:5])
        published = "true" if article.platforms.zenn.status.value == "published" else "false"
        canonical_url = f"{self.BLOG_BASE_URL}/{article.slug}"

        return f"""---
title: "{article.title}"
emoji: "{article.platforms.zenn.emoji}"
type: "{article.platforms.zenn.article_type}"
topics: [{topics_str}]
published: {published}
canonical: "{canonical_url}"
---"""

    def _remove_story_sections(self, content: str) -> str:
        """ストーリー・感情セクションを見出し単位で除去する。

        ストーリーキーワードを含む##/###見出しを検出し、
        次の同レベル以上の見出しまでの内容を丸ごとスキップする。
        """
        lines = content.split("\n")
        result = []
        skip = False
        skip_level = 0

        for line in lines:
            heading_match = re.match(r"^(#{2,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)

                if self._is_story_heading(text):
                    # ストーリーセクション開始 → スキップ
                    skip = True
                    skip_level = level
                    continue
                elif skip and level <= skip_level:
                    # 同レベル以上の非ストーリー見出し → スキップ解除
                    skip = False

            if not skip:
                result.append(line)

        return "\n".join(result)

    def _is_story_heading(self, text: str) -> bool:
        """見出しがストーリー・感情セクションかどうかを判定する。"""
        # 絵文字を除去して判定
        clean = re.sub(r"[\U0001f300-\U0001f9ff\u2600-\u27bf\u2700-\u27bf]", "", text).strip()
        return any(kw in clean for kw in self._STORY_KEYWORDS)

    def _remove_share_cta(self, content: str) -> str:
        """元記事末尾のシェア促進テキストを除去する。"""
        content = re.sub(r"<!-- SNS共有の促進 -->\s*", "", content)
        content = re.sub(
            r"\*\*この記事が役に立ったら、ぜひシェアをお願いします.*?\*\*\s*",
            "",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(r"あなたのシェアが、同じ悩みを持つ誰かの助けになります。\s*", "", content)
        return content

    def _clean_empty_lines(self, content: str) -> str:
        """連続する空行を2行までに整理する。"""
        return re.sub(r"\n{3,}", "\n\n", content)

    def _add_blog_link(self, content: str, slug: str) -> str:
        """末尾にブログ全文への誘導リンクを追加する。"""
        blog_url = f"{self.BLOG_BASE_URL}/{slug}"
        # 末尾の余分な区切り線を除去してからフッターを付ける
        content = re.sub(r"(\n---\s*)+$", "", content.rstrip())
        return content + f"""

---

**この記事の全文（ストーリー・背景解説を含む完全版）はブログで公開しています。**

**[>> ブログで全文を読む]({blog_url})**
"""

    def _convert_callouts(self, content: str) -> str:
        """CalloutをZennメッセージ形式に変換する。"""
        # :::note info → :::message
        content = re.sub(r":::note\s*(\w+)?", ":::message", content)
        return content


class QiitaConverter(PlatformConverter):
    """Convert article to Qiita format.

    Qiita is non-monetizable, so content is a summary with a link
    to the full article on the blog (similar to SNS announcements).
    """

    BLOG_BASE_URL = "https://blog.secure-auto-lab.com/articles"

    def convert(self, article: Article) -> str:
        blog_url = f"{self.BLOG_BASE_URL}/{article.slug}"
        tags_str = " / ".join(article.tags[:5])

        return f"""# {article.title}

{article.description}

## この記事について

本記事の全文は以下のブログで公開しています。

**[>> 全文を読む: {article.title}]({blog_url})**

### タグ

{tags_str}

---

> この記事は [secure-auto-lab.com]({blog_url}) からの要約です。
> 全文・ソースコード・詳細解説はブログ本文をご覧ください。
"""


class BlogConverter(PlatformConverter):
    """Convert article to blog (Astro) format."""

    def convert(self, article: Article) -> str:
        content = self._strip_platform_blocks(article.content, "blog")

        # Add Astro frontmatter
        frontmatter = self._generate_frontmatter(article)

        return f"{frontmatter}\n\n{content}"

    def _generate_frontmatter(self, article: Article) -> str:
        """Generate Astro-compatible frontmatter."""
        tags_str = ", ".join(f'"{t}"' for t in article.tags)
        category = resolve_category(article.category)

        return f"""---
title: "{article.title}"
description: "{article.description}"
pubDate: "{article.created_at.strftime('%Y-%m-%d')}"
updatedDate: "{article.updated_at.strftime('%Y-%m-%d')}"
category: "{category}"
tags: [{tags_str}]
author: "{article.author}"
---"""


class ConverterFactory:
    """Factory for creating platform converters."""

    _converters: dict[str, type[PlatformConverter]] = {
        "note": NoteConverter,
        "zenn": ZennConverter,
        "qiita": QiitaConverter,
        "blog": BlogConverter,
    }

    @classmethod
    def get_converter(cls, platform: str) -> PlatformConverter:
        """Get converter for specified platform."""
        converter_class = cls._converters.get(platform)
        if not converter_class:
            raise ValueError(f"Unknown platform: {platform}")
        return converter_class()

    @classmethod
    def convert_all(cls, article: Article) -> dict[str, str]:
        """Convert article to all enabled platforms."""
        results = {}
        for platform in article.get_enabled_platforms():
            converter = cls.get_converter(platform)
            results[platform] = converter.convert(article)
        return results
