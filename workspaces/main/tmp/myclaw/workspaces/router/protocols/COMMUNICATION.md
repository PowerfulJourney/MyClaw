# COMMUNICATION.md (v0.1)

## 1) 两种协作触发

### 类型1：主动指令型

`@Agent名 [动作指令] --[参数]`

### 类型2：链式接力型

`PASS_TO @Agent名 [上下文摘要]`

## 2) 输出格式（强制）

所有 Agent 输出都尽量以如下结构开头：

1. 结论（1-3 条）
2. 证据/数据（可引用链接/截图/对比表）
3. 下一步（明确到动作）
4. `PASS_TO @NextAgent`（如果需要接力）

并附上统一字段块：

```
TASK_ID:
Status:
Input:
Output:
Budget:
Deadline:
Blocking:
Links/Artifacts:
```

## 3) Telegram 群聊协作方式（方案 1：内部派单 / Worker 直接同步到群 / Router 串行门控 + 群内汇总）

目标：**不再出现 `sessions_send ... timeout`**，同时让群里看起来像“多智能体在对话”。

### 3.1 触发与派单（Router → Brain → Builder）

- 群内由用户 `@Router`（@Agent_1_Aegis_bot）触发。
- Router 派单必须使用 `sessions_send(timeoutSeconds=0)`（即发即忘，不等待回复）。
- **默认严格串行**：
  1) 先派单给 **Brain** 出完整内容/结构/分镜/指令包
  2) Brain 标记就绪后，Router 才派单给 **Builder** 执行
- 派单消息必须包含：`TASK_ID`、`Deadline`、`Deliverable`（要在群里怎么汇报）、以及 accountId 要求。

### 3.2 群内同步规则（Workers → 群）

- 每个 worker **最多 2 条消息**：
  1) `ACK`（可选：预计完成时间/是否需要澄清）
  2) `DONE`（结论 + 证据 + 下一步）
- 每条消息必须带前缀：`[Brain]` / `[Builder]` / `[Router]`（以及 Main 如需）。
- **发送必须显式指定 Telegram 账号**（否则会走默认账号并出现 `Telegram bot token missing`）：
  - Router 发群：`message(channel=telegram, accountId=aegis, target=-1003883808495, ...)`
  - Brain 发群：`message(channel=telegram, accountId=oracle, target=-1003883808495, ...)`
  - Builder 发群：`message(channel=telegram, accountId=logic, target=-1003883808495, ...)`
  - Main 发群：`message(channel=telegram, accountId=main, target=-1003883808495, ...)`
- DONE 消息末尾统一加：`PASS_TO @Agent_1_Aegis_bot (TASK_ID=...)` 用于触发 Router 进入“群内汇总 + 下一步派单”。
- Brain 的 DONE 必须追加：`READY_FOR_BUILD: true|false`，有渲染则追加 `READY_FOR_RENDER: true|false`。

### 3.3 Router 汇总与推进约束（强制）

- Router 收到 `PASS_TO` 后：
  1) **必须先在群里发 1 条汇总**（结论/产物/下一步/需要用户确认的问题）
  2) 若存在“需要确认的问题”，这些问题必须由 **责任 Agent（Brain/Builder）** 在群里直接向用户提问；Router 不展开细化讨论。
  3) 默认最多自动推进 1 步（再派单一次）。
  4) 若仍需继续：必须向用户提 1 个明确问题并等待确认（问题由责任 Agent 提问）。

### 3.4 前置条件（多 bot 真·多角色）

- 若你希望每个 agent **用自己的 Telegram bot 在群里发言**：对应 bot 的 `channels.telegram.accounts.<id>.groupPolicy` 需要为 `open` 或 `allowlist`（并允许该群）。
- 这类改动通常需要重启 Gateway 才生效；未获用户批准前不要重启。

---

（保留旧方案）

## 3B) Telegram 群聊协作方式（方案 B：内部派单 / 对外单点汇总）

- 群里对外只由 **Aegis** 输出（汇总 1 条：结论→证据→下一步）。
- 其他 Agent 默认不在群里回复（即使被 @）。
- Aegis 需要协作时：使用内部派单（agent-to-agent）把任务发给 Oracle/Logic/Metrics/Growth；收到结果后再在群里汇总。
- 群里出现 `PASS_TO @Agent_xxx_bot`：它是调度提示，不依赖 bot-to-bot @。

## 4) 争议处理

- 如果 Oracle / Growth 认为机会很大但 Logic 认为不可做：
  - 双方各写 5 行“最强论点” + 证据
  - 交给 Aegis 决策（必须给出理由）

## 5) Gateway restart 策略（强制）

- **非必要不重启 gateway**。
- 优先选择：只改文档/协议、只改任务文件、只改项目文件、或提出“需要重启才能生效”的变更建议。
- **确需重启**（例如新增/切换 Telegram bot、调整 bindings 等需要网关重载配置）：
  1) 先说明：重启原因、影响范围、预计耗时、回滚方案
  2) 等待 **User 明确批准** 后再执行
  3) 默认不主动重启
