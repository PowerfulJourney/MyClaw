# TASK_PROTOCOL.md (v0.1)

## 0) 核心目标

- 让每个任务可追踪（谁做、做到哪、花了多少、下一步是谁）。
- 把“讨论”压缩成“结论 + 证据 + 下一步”。

## 1) TASK 文件模板

建议每个任务一文件：`tasks/TASK-YYYYMMDD-XXX.md`。

最低字段（必须齐全）：

```yaml
TASK_ID: TASK-YYYYMMDD-XXX
Title: 
Owner: Aegis
Status: DRAFT
Project: projects/<name>/
Goal: 
NonGoal: 
ICP: 
Pricing: 
Budget:
  cap: 
  spent: 0
  remaining: 
Deadline: 
Risks: []
Links: []
NextAgent: 
Blocking: 
```

## 2) 状态机与准入条件

- `DRAFT`：想法阶段，允许模糊。
- `RESEARCHING`：Brain/Growth 做竞品、趋势、痛点、渠道验证。
- `APPROVAL_NEEDED`：材料齐全，等待 Aegis 决策。
- `BUILDING`：进入研发；必须先完成 `SKILL_SEARCH.md`。
- `SHIPPING`：发布/上线/可卖。
- `MEASURING`：采集数据（流量/转化/付费/留存/成本）。
- `ITERATING`：基于数据迭代。
- `PAUSED`：暂挂（写明恢复条件）。
- `CLOSED`：终止（需 User 明确授权）。

## 3) 权限规则（强制）

- 仅 **Aegis** 能将任务从 `APPROVAL_NEEDED` → `BUILDING`。
- 仅 **Metrics** 能修改 `Budget.spent / Budget.remaining`（其他人只能建议）。
- 仅 **User** 能把任务置为 `CLOSED` 或允许销毁 Builder。

## 4) 开工前强制产出：SKILL_SEARCH.md

位置：`projects/<name>/SKILL_SEARCH.md`

必须包含：
- 使用 `find-skills` 搜索到的 skills（关键词 + 结果）
- GitHub 搜索关键词 + 参考仓库
- 为什么不用（缺功能/不维护/成本/许可证/不稳定）
- 结论：自研哪些部分、复用哪些部分

没有该文件：不得进入 `BUILDING`。

## 5) 交付标准（Definition of Done）

每个阶段的最低 DoD：
- Research DoD：竞品与定价表 + ICP 画像 + 明确痛点句子（用户原话或可引用证据）
- Build DoD：可运行、可部署、可 demo（README 有一键运行/部署）
- Ship DoD：有计费方式/或收款路径（哪怕是手动开票/Stripe Link 也可）
- Measure DoD：有至少 1 个可观测指标（例如 signup、activation、paid）
