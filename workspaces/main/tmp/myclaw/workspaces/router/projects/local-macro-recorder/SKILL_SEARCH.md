# SKILL_SEARCH

## 结论
本项目先**复用现有能力 + 自研核心录制回放逻辑**，不新增外部 skill 依赖作为开工前置。

## 已检索技能（本地可用）
- coding-agent：可用于并行编码执行（用于 Builder 阶段）
- github：用于后续 PR/CI 流程
- find-skills：可在需要扩展能力时追加检索

## GitHub 关键词（用于后续补证）
- chrome extension macro recorder
- browser automation extension local first
- csv form autofill chrome extension

## 不直接复用现成项目的原因（当前）
- 现成宏录制插件多为闭源或重平台化，难以满足“低价 + 本地优先 + 极简MVP”
- 直接 fork 带来许可证/维护耦合风险

## 自研/复用边界
- 自研：录制事件模型、回放引擎、CSV变量映射、模板系统
- 复用：构建脚手架、埋点SDK、基础UI组件
