# BUILDER_BRIEF (Phase-1)

## 范围限制（强制）
- 仅允许修改 `projects/local-macro-recorder/`。
- 不得修改 `tasks/`、`reports/`、`protocols/`。

## 开工目标（24h）
交付可运行的浏览器扩展骨架，跑通：录制 -> 回放 -> CSV变量填充 -> 日志。

## 文件建议
- extension/manifest.json
- extension/background.js
- extension/content.js
- extension/popup.html
- extension/popup.js
- extension/core/recorder.js
- extension/core/player.js
- extension/core/csv-map.js
- extension/core/logger.js

## 验收
1. 可录制 20 步以内流程并保存 JSON
2. 同域回放成功率可演示
3. CSV 映射至少 3 字段
4. 日志可定位失败步骤与错误类型

## 交付说明（必须）
- 修改文件列表
- 本地运行步骤
- 一个 demo 流程说明
- 当前风险与下一步建议
