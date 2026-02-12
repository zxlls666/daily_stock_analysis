#!/usr/bin/env bash
set -euo pipefail

# daily + dexter MVP 编排脚本（最小改造版）
# 用法:
#   bash scripts/orchestrator.sh
# 可配环境变量:
#   TOPN=3
#   OUT_DIR=outputs
#   DAILY_RESULT_JSON=outputs/daily_result.json
#   DAILY_REPORT_MD=outputs/daily_report.md
#   DEXTER_BATCH_CMD='bun run src/index.tsx --batch {candidates} --out {deep}'

TOPN="${TOPN:-3}"
OUT_DIR="${OUT_DIR:-outputs}"
DAILY_RESULT_JSON="${DAILY_RESULT_JSON:-$OUT_DIR/daily_result.json}"
DAILY_REPORT_MD="${DAILY_REPORT_MD:-$OUT_DIR/daily_report.md}"
CANDIDATES_JSON="$OUT_DIR/candidates.json"
DEEP_JSON="$OUT_DIR/deep_dive_result.json"
FINAL_REPORT="$OUT_DIR/final_report.md"

mkdir -p "$OUT_DIR"

echo "[1/5] 运行 daily 主流程（请按你当前项目参数调整）"
python3 main.py || true

echo "[2/5] 导出 TopN 候选"
python3 scripts/export_topn_candidates.py \
  --input "$DAILY_RESULT_JSON" \
  --output "$CANDIDATES_JSON" \
  --topn "$TOPN"

echo "[3/5] 调用 dexter 批量深挖"
if [[ -n "${DEXTER_BATCH_CMD:-}" ]]; then
  CMD="${DEXTER_BATCH_CMD//\{candidates\}/$CANDIDATES_JSON}"
  CMD="${CMD//\{deep\}/$DEEP_JSON}"
  echo "[INFO] 执行: $CMD"
  bash -lc "$CMD" || {
    echo "[WARN] dexter 深挖失败，写入降级结果"
    TODAY="$(date +%F)"
    printf '{"date":"%s","results":[]}\n' "$TODAY" > "$DEEP_JSON"
  }
else
  echo "[WARN] 未设置 DEXTER_BATCH_CMD，写入空深挖结果（降级）"
  TODAY="$(date +%F)"
  printf '{"date":"%s","results":[]}\n' "$TODAY" > "$DEEP_JSON"
fi

echo "[4/5] 合并统一报告"
python3 scripts/merge_report.py \
  --daily "$DAILY_REPORT_MD" \
  --deep "$DEEP_JSON" \
  --out "$FINAL_REPORT"

echo "[5/5] 完成"
echo "[OK] 最终报告: $FINAL_REPORT"
