#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 daily 分析结果导出 dexter 深挖候选列表（Top N）。"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _pick_results(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if isinstance(payload, dict):
        for key in ("results", "analysis_results", "stocks", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

        # 兼容单条对象
        if payload.get("code") or payload.get("symbol"):
            return [payload]

    return []


def _to_candidate(item: Dict[str, Any]) -> Dict[str, Any]:
    code = str(item.get("code") or item.get("symbol") or "").strip()
    name = str(item.get("name") or f"股票{code}")

    score = item.get("sentiment_score")
    if score is None:
        score = item.get("score", 0)
    try:
        score = int(score)
    except Exception:
        score = 0

    signal = str(item.get("operation_advice") or item.get("signal") or "观望")

    anomaly_reasons: List[str] = []
    for key in ("risk_warning", "key_points", "analysis_summary"):
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            anomaly_reasons.append(val.strip().replace("\n", " ")[:120])
    if not anomaly_reasons:
        anomaly_reasons = ["评分或信号触发深挖"]

    snapshot = {
        "price": item.get("price") or item.get("current_price"),
        "change_pct": item.get("change_pct") or item.get("pct_chg"),
        "volume_ratio": item.get("volume_ratio"),
    }

    return {
        "symbol": code,
        "name": name,
        "score": score,
        "signal": signal,
        "anomaly_reasons": anomaly_reasons[:3],
        "snapshot": snapshot,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="导出 TopN 深挖候选")
    parser.add_argument("--input", required=True, help="daily 分析结果 JSON")
    parser.add_argument("--output", required=True, help="输出 candidates.json")
    parser.add_argument("--topn", type=int, default=3, help="候选数量，默认 3")
    parser.add_argument("--market-session", default="CN_CLOSE", help="市场会话标签")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = _load_json(input_path)
    results = _pick_results(payload)

    candidates = [_to_candidate(x) for x in results if (x.get("code") or x.get("symbol"))]

    # 评分高优先；同分时优先买卖信号（卖出/买入优于观望）
    signal_weight = {"卖出": 3, "减仓": 2, "买入": 2, "加仓": 2, "观望": 1, "持有": 1}
    candidates.sort(key=lambda x: (x["score"], signal_weight.get(x["signal"], 0)), reverse=True)
    top = candidates[: max(1, args.topn)]

    final = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "market_session": args.market_session,
        "top_n": args.topn,
        "candidates": top,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"[OK] 导出 {len(top)} 条候选 -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
