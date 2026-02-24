# MODEL_POLICY.md (v0.1)

> 模型策略：经济化 + 关键环节用高配。

- Oracle / Growth：`openai-codex/gpt-5.2`
- Logic / Builder：`openai-codex/gpt-5.3-codex`
- Metrics：`openai-codex/gpt-5.3-codex`

规则：
- 进入 `BUILDING/SHIPPING` 才允许 Logic/Builder 使用高配长上下文。
- Oracle/Growth 报告尽量引用链接 + 提炼要点，减少长贴全文。
- Metrics 输出尽量结构化（表格/要点/可计算口径）。
