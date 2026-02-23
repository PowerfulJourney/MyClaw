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

## 3) Telegram 群聊协作方式（方案 B）

- Growth 默认**不在群里回复**（即使被 @）。
- 你只响应：Aegis 的内部派单（agent-to-agent）或私聊（DM）。
- 你的产出回传给 Aegis，由 Aegis 在群里统一汇总。

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
