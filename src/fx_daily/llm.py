"""ローカル LLM（Ollama / GPU調停ゲートウェイ経由）による自由文の小タスク生成。

方針（細分化による破綻防止）:
- LLM には数値計算・記事構成をさせない。JSON in → JSON out の最小タスクのみ。
- 出力は (1) 決定的バリデーション（禁止表現・数値整合・長さ）
        (2) LLM 自己検証（事実との矛盾チェック）
  の二段で検査し、max_retries 回失敗したら定型文にフォールバックする。
"""

from __future__ import annotations

import json
import re

import httpx

from .config import FxDailyConfig
from .derive import JUDGMENT_LABELS, DerivedMetrics

FALLBACK_COMMENT = "本日の数値は上表の通り。運用ルールに基づき淡々と継続する。"


def _facts(metrics: DerivedMetrics) -> dict:
    r = metrics.report
    return {
        "date": r.date.isoformat(),
        "judgment": JUDGMENT_LABELS[metrics.judgment_level],
        "judgment_reasons": metrics.judgment_reasons,
        "signals_detected": r.signals.detected,
        "signals_skipped_z": r.signals.skipped_z,
        "signals_skipped_spread": r.signals.skipped_spread,
        "entries": r.signals.entered,
        "day_pips": r.pnl.day_pips,
        "day_jpy": r.pnl.day_jpy,
        "mtd_jpy": round(metrics.mtd_jpy),
        "total_jpy": round(metrics.total_jpy),
        "total_pct": round(metrics.total_pct, 1),
        "drawdown_pct": round(metrics.drawdown_pct, 1),
        "slippage_measured": r.slippage.measured_avg_pips,
        "slippage_assumption": r.slippage.backtest_assumption_pips,
        "ea_notes": r.notes,
    }


def _chat_json(config: FxDailyConfig, system: str, user: str, schema: dict) -> dict:
    resp = httpx.post(
        f"{config.llm.base_url}/api/chat",
        json={
            "model": config.llm.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "format": schema,
            "stream": False,
            "options": {"temperature": config.llm.temperature},
        },
        timeout=config.llm.timeout_sec,
    )
    resp.raise_for_status()
    return json.loads(resp.json()["message"]["content"])


_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def _numbers_consistent(text: str, facts: dict) -> bool:
    """コメント中の数値が facts に由来するか検査（丸め・桁区切り・万円換算を許容）。"""
    allowed: set[str] = set()
    for v in facts.values():
        if isinstance(v, (int, float)):
            for cand in {v, abs(v), round(v), round(abs(v)), round(v, 1), round(abs(v), 1),
                         round(v / 10000, 1), round(abs(v) / 10000, 1), round(abs(v) / 10000)}:
                s = f"{cand:g}"
                allowed.add(s)
                if s.endswith(".0"):
                    allowed.add(s[:-2])
    for m in _NUM_RE.finditer(text):
        if m.group().replace(",", "") not in allowed:
            return False
    return True


def _validate_deterministic(comment: str, facts: dict, config: FxDailyConfig) -> str | None:
    if not comment.strip():
        return "empty"
    if len(comment) > 120:
        return f"too long ({len(comment)} chars)"
    for phrase in config.banned_phrases:
        if phrase in comment:
            return f"banned phrase: {phrase}"
    if not _numbers_consistent(comment, facts):
        return "number not in facts"
    return None


def _self_check(comment: str, facts: dict, config: FxDailyConfig) -> bool:
    """別呼び出しの LLM に事実との矛盾を検査させる（細分化の二段目）。"""
    result = _chat_json(
        config,
        system=(
            "あなたはFX運用記録の校閲者。コメントが事実データと矛盾していないか、"
            "断定的な投資助言表現がないかだけを検査する。"
        ),
        user=f"事実データ:\n{json.dumps(facts, ensure_ascii=False)}\n\n検査対象コメント:\n{comment}",
        schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}, "reason": {"type": "string"}},
            "required": ["ok", "reason"],
        },
    )
    return bool(result.get("ok"))


def generate_comment(metrics: DerivedMetrics, config: FxDailyConfig) -> tuple[str, bool]:
    """一言コメントを生成。戻り値は (コメント, LLM生成か否か)。失敗時は定型文。"""
    facts = _facts(metrics)
    system = (
        "あなたはFX自動売買の運用記録を書く本人。与えられた事実データだけを根拠に、"
        "その日の一言コメントを日本語で書く。制約: 2文以内・120字以内・だ/である調・"
        "感情は控えめに事実ベース・データにない数値や出来事を書かない・"
        "投資助言や成果の断定（勝てる/必ず/保証など）は禁止。"
    )
    user = f"本日の事実データ:\n{json.dumps(facts, ensure_ascii=False)}\n\n一言コメントを書いてください。"
    schema = {
        "type": "object",
        "properties": {"comment": {"type": "string"}},
        "required": ["comment"],
    }

    last_error = ""
    for attempt in range(config.llm.max_retries):
        try:
            comment = _chat_json(config, system, user, schema)["comment"].strip()
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
            last_error = f"llm call failed: {e}"
            continue
        error = _validate_deterministic(comment, facts, config)
        if error:
            last_error = error
            user += f"\n\n（前回の出力は却下: {error}。制約を守って書き直してください）"
            continue
        try:
            if not _self_check(comment, facts, config):
                last_error = "self-check rejected"
                continue
        except (httpx.HTTPError, KeyError, json.JSONDecodeError):
            pass  # 自己検証が落ちても決定的検査は通過しているので採用
        return comment, True

    print(f"  [warn] コメント生成が {config.llm.max_retries} 回失敗（{last_error}）。定型文を使用")
    return FALLBACK_COMMENT, False
