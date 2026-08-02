"""fx-daily の設定。リポジトリルートの fx-daily.yaml で上書き可能。"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
# FX_DAILY_CONFIG 環境変数で設定ファイルを差し替え可能（テスト用）
CONFIG_PATH = Path(os.environ.get("FX_DAILY_CONFIG", REPO_ROOT / "fx-daily.yaml"))


class JudgmentThresholds(BaseModel):
    """判定レベルの閾値（開始来ドローダウン%）。運用ルールブック確定時に更新する。"""

    l1_drawdown_pct: float = 10.0
    l2_drawdown_pct: float = 20.0
    l3_drawdown_pct: float = 30.0


class LlmConfig(BaseModel):
    base_url: str = "http://localhost:11434"  # GPU調停ゲートウェイ（Ollama本体は11435）
    model: str = "qwen3.6:27b-q5_K_M"
    timeout_sec: float = 600.0  # gpu_lock 待機を考慮して長め
    max_retries: int = 3
    temperature: float = 0.4


class FxDailyConfig(BaseModel):
    # GALLERIA 側がレポート JSON を出力するディレクトリ（契約の出力先）
    input_dir: Path = Path(r"\\GALLERIA\Users\tinou\fx-ea\reports\daily")
    blog_dir: Path = REPO_ROOT / "fx-blog"
    content_dir: Path = REPO_ROOT / "fx-blog" / "src" / "content" / "daily"
    figures_dir: Path = REPO_ROOT / "fx-blog" / "public" / "figures" / "daily"
    thresholds: JudgmentThresholds = Field(default_factory=JudgmentThresholds)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    # コメントに含まれてはならない表現（投資助言・成果保証の回避。法務方針より）
    banned_phrases: list[str] = Field(
        default_factory=lambda: [
            "勝てる", "必ず", "確実に", "保証", "おすすめ", "推奨",
            "買うべき", "売るべき", "儲かる", "月利", "誰でも",
        ]
    )


def load_config() -> FxDailyConfig:
    if CONFIG_PATH.exists():
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        return FxDailyConfig.model_validate(data)
    return FxDailyConfig()
