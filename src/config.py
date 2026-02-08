"""Shared configuration for article-publisher.

This file is the single source of truth for blog categories.
When adding a new category:
1. Add it to BLOG_CATEGORIES below
2. Run: python -m src.config sync
   This updates blog/src/content/config.ts automatically.
"""
from __future__ import annotations

# Blog categories - single source of truth
# Key: category slug, Value: description (for documentation/CLI help)
BLOG_CATEGORIES: dict[str, str] = {
    "automation": "自動化ツール・ワークフロー・CI/CD",
    "ai": "AI・機械学習・LLM活用",
    "security": "セキュリティ・認証・暗号化",
    "dev-tips": "開発Tips・技術解説・API調査",
    "projects": "プロジェクト紹介・ツール紹介",
    "web": "Web開発・フロントエンド・バックエンド",
    "infrastructure": "インフラ・クラウド・DevOps",
}

DEFAULT_CATEGORY = "dev-tips"

# Mapping from common aliases to valid categories
CATEGORY_ALIASES: dict[str, str] = {
    "tech": "dev-tips",
    "tutorial": "dev-tips",
    "tool": "projects",
    "tools": "projects",
    "project": "projects",
    "ml": "ai",
    "llm": "ai",
    "frontend": "web",
    "backend": "web",
    "devops": "infrastructure",
    "cloud": "infrastructure",
    "cicd": "automation",
    "ci/cd": "automation",
    "workflow": "automation",
    "auth": "security",
    "crypto": "security",
}


def resolve_category(category: str) -> str:
    """Resolve a category string to a valid blog category."""
    if category in BLOG_CATEGORIES:
        return category
    return CATEGORY_ALIASES.get(category, DEFAULT_CATEGORY)


def sync_blog_config() -> None:
    """Sync BLOG_CATEGORIES to blog/src/content/config.ts."""
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "blog" / "src" / "content" / "config.ts"
    if not config_path.exists():
        print(f"Blog config not found: {config_path}")
        return

    content = config_path.read_text(encoding="utf-8")

    # Replace the categories array
    categories_str = ", ".join(f"'{c}'" for c in BLOG_CATEGORIES)
    new_line = f"const categories = [{categories_str}] as const;"

    import re
    updated = re.sub(
        r"const categories = \[.*?\] as const;",
        new_line,
        content,
    )

    if updated != content:
        config_path.write_text(updated, encoding="utf-8")
        print(f"Updated: {config_path}")
        print(f"Categories: {list(BLOG_CATEGORIES.keys())}")
    else:
        print("Blog config already up to date.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        sync_blog_config()
    else:
        print("Blog categories:")
        for slug, desc in BLOG_CATEGORIES.items():
            print(f"  {slug:20s} {desc}")
        print(f"\nDefault: {DEFAULT_CATEGORY}")
        print("\nRun 'python -m src.config sync' to sync to blog/src/content/config.ts")
