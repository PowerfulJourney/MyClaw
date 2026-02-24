# CONVENTION.md (v0.1)

> 目的：控制熵增、降低协作摩擦、让多 Agent 产出可追踪可复盘。

## 1. 目录结构（强制）

- `protocols/`：协议、状态机、审批规则、模型策略
- `tasks/`：任务台账、模板、每个 TASK 的记录
- `projects/<name>/`：项目实现区（仅 Builder 工作区需要；非 Builder 工作区可不创建）
- `reports/brain/`：情报与机会报告
- `reports/growth/`：增长/渠道/投放/用户反馈报告
- `reports/metrics/`：成本、预算、ROI、token 统计
- `assets/`：截图、调研附件、导出数据
- `scripts/`：校验脚本（软 RBAC / 检查器）
- `archive/`：归档（已完成/已废弃的项目与报告，避免污染活跃目录）
- `tmp/`：临时文件（默认应被 gitignore；可随时清空）

## 2. 命名规范

- 项目：`projects/<kebab-case>/`（例如 `projects/ai-translate-saas/`）
- 任务：`tasks/TASK-YYYYMMDD-XXX.md`（例如 `TASK-20260222-001.md`）
- 报告：`reports/<role>/<YYYYMMDD>-<topic>.md`

## 3. TASK 状态（有限集合）

`DRAFT` → `RESEARCHING` → `APPROVAL_NEEDED` → `BUILDING` → `SHIPPING` → `MEASURING` → `ITERATING`

可随时进入：`PAUSED`；终止：`CLOSED`

## 4. 权责（软 RBAC）

- **Aegis**：唯一调度者；唯一允许把任务从 `APPROVAL_NEEDED` → `BUILDING`。
- **Metrics**：唯一允许更新每个任务的「已花费/剩余预算」。
- **User（你）**：唯一允许 `CLOSED` 或允许销毁 Builder。
- **Builder**：只允许在 `projects/<name>/` 下文件操作（靠系统提示词 + 校验脚本实现）。

## 5. 项目最小文件集（强制）

每个 `projects/<name>/` 至少包含：
- `README.md`：目标、ICP、定价、里程碑、指标
- `CHANGELOG.md`：对外发布节奏
- `METRICS.md`：指标定义、数据源、看板/日志位置
- `SKILL_SEARCH.md`：开工前的“别造轮子”检索结果（见 TASK_PROTOCOL）

## 6. 统一消息模板（强制字段）

所有跨 Agent 交付都用以下块（可复制）：

```
TASK_ID: 
Owner: 
Input: 
Output: 
Deadline: 
Budget: 
Status: 
NextAgent: 
Blocking: 
Links/Artifacts: 
```

- `PASS_TO @AgentName`：用于明确接力人。
- 群聊噪音控制：对外尽量只由 Aegis 汇总发 1 条；其他 Agent 只在被点名或被 Aegis 派单时输出。
