# Dexter 融合 MVP 交付说明

## 新增内容

- `scripts/export_topn_candidates.py`
  - 输入 daily 结果 JSON
  - 输出 `candidates.json`（Top N）
- `scripts/merge_report.py`
  - 合并 `daily_report.md` + `deep_dive_result.json`
  - 输出统一 `final_report.md`
- `scripts/orchestrator.sh`
  - 串联执行：daily → TopN → dexter → merge
  - 支持 dexter 失败降级（空 deep dive）

## 建议目录

```text
outputs/
  daily_result.json
  daily_report.md
  candidates.json
  deep_dive_result.json
  final_report.md
```

## 快速试跑

```bash
# 1) 导出候选
python3 scripts/export_topn_candidates.py \
  --input outputs/daily_result.json \
  --output outputs/candidates.json \
  --topn 3

# 2) 合并报告
python3 scripts/merge_report.py \
  --daily outputs/daily_report.md \
  --deep outputs/deep_dive_result.json \
  --out outputs/final_report.md

# 3) 一键编排（需先准备 daily 的输出文件）
DEXTER_BATCH_CMD='bun run src/index.tsx --batch {candidates} --out {deep}' \
bash scripts/orchestrator.sh
```

## 环境变量（orchestrator）

- `TOPN`：默认 3
- `OUT_DIR`：默认 `outputs`
- `DAILY_RESULT_JSON`：默认 `outputs/daily_result.json`
- `DAILY_REPORT_MD`：默认 `outputs/daily_report.md`
- `DEXTER_BATCH_CMD`：dexter 批量命令模板
  - 占位符：`{candidates}`、`{deep}`

## 注意事项

1. 当前已在 `main.py` 中新增自动导出：默认会生成 `outputs/daily_result.json` 和 `outputs/daily_report.md`。可通过 `EXPORT_INTEGRATION_OUTPUTS=false` 关闭；可通过 `INTEGRATION_OUTPUT_DIR` 改目录。
2. `DEXTER_BATCH_CMD` 需要与你本地 dexter 实际 CLI 对齐。
3. 本 MVP 目标是“可跑通编排”，不改动既有分析核心逻辑。
