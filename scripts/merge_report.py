#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并 daily 报告 + dexter 深挖结果，输出统一 Markdown 报告。"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _normalize_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    if isinstance(payload, list):
        return payload
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="合并报告")
    parser.add_argument("--daily", required=True, help="daily 报告 markdown")
    parser.add_argument("--deep", required=True, help="dexter 深挖结果 json")
    parser.add_argument("--out", required=True, help="输出 markdown")
    args = parser.parse_args()

    daily_path = Path(args.daily)
    deep_path = Path(args.deep)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    daily_md = _load_text(daily_path)
    deep_payload = _load_json(deep_path) if deep_path.exists() else {"results": []}
    results = _normalize_results(deep_payload)

    lines: List[str] = []
    lines.append(f"# 融合分析报告（daily + dexter）")
    lines.append("")
    lines.append(f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- deep dive 数量: {len(results)}")
    lines.append("")

    lines.append("## 一、Daily 决策仪表盘")
    lines.append("")
    lines.append(daily_md.strip() if daily_md.strip() else "（未提供 daily 报告正文）")
    lines.append("")

    lines.append("## 二、Dexter 深挖卡片")
    lines.append("")

    if not results:
        lines.append("- 本次无可用深挖结果（可能超时/失败/未触发）。")
    else:
        for idx, item in enumerate(results, 1):
            symbol = item.get("symbol") or item.get("code") or "UNKNOWN"
            thesis = item.get("thesis") or item.get("analysis_summary") or "（无）"
            risk_points = item.get("risk_points") or []
            catalysts = item.get("catalysts") or []
            watchlist = item.get("watchlist_next_day") or []
            invalid = item.get("invalid_conditions") or []
            scenarios = item.get("scenarios") or {}

            lines.append(f"### {idx}. {symbol}")
            lines.append(f"- Thesis: {thesis}")

            if risk_points:
                lines.append("- 风险点:")
                lines.extend([f"  - {x}" for x in risk_points])
            if catalysts:
                lines.append("- 催化点:")
                lines.extend([f"  - {x}" for x in catalysts])
            if scenarios:
                lines.append("- 情景推演:")
                for k in ("bull", "base", "bear"):
                    if scenarios.get(k):
                        lines.append(f"  - {k}: {scenarios[k]}")
            if watchlist:
                lines.append("- 次日观察点:")
                lines.extend([f"  - {x}" for x in watchlist])
            if invalid:
                lines.append("- 失效条件:")
                lines.extend([f"  - {x}" for x in invalid])
            lines.append("")

    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"[OK] 合并报告输出 -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
