# 度量与预算卡（P0）

TASK_ID: P0-GTM-METRICS-20260222
Status: READY
Budget.cap: $500
Budget.spent: $0
Budget.remaining: $500
Progress(%): 100
StopLoss: 任一硬阈值触发即 PAUSED（暂停投放/采购，复盘后再放量）
Blocking: 无
Links/Artifacts: /home/administrator/.openclaw/workspace/reports/metrics/20260222-metric-budget-card.md

---

## 1) 北极星指标（North Star）
**NSM = D14 新付费激活用户数（D14 PAA: Paid Activated Accounts）**

定义：
- 在安装后 14 天内完成“激活”且完成首笔成功支付的去重账号数。
- 选择理由：同时约束“有效获取（安装）+产品价值感知（激活）+商业化（付费）”，避免只拉安装量造成虚高。

辅助监控：
- A/I（激活率）= Activated / Installed
- P/A（激活到付费转化）= Paid / Activated
- P/I（安装到付费转化）= Paid / Installed

---

## 2) 安装→激活→付费 漏斗口径（统一事件定义）

### Install（安装）
- 事件：`app_install_success`
- 去重键：`user_id`（无 user_id 时临时用 `device_id`，后续并表）
- 时间窗：按 cohort_day（安装自然日）

### Activate（激活）
- 事件：`activation_complete`
- 判定条件（需同时满足）：
  1. 完成账号创建/登录（`account_ready`）
  2. 完成 1 次核心价值动作（`core_action_success`）
- 时间窗：安装后 24h 内

### Paid（付费）
- 事件：`first_payment_success`
- 判定条件：首笔成功扣款，金额 > 0，状态 `succeeded`
- 时间窗：安装后 14 天内（用于 D14 主评估）

### 核心漏斗公式
- `ActivationRate = Activated24h / Installed`
- `PayFromActivation = Paid14d / Activated24h`
- `PayFromInstall = Paid14d / Installed`

---

## 3) D7 / D14 目标阈值

> 说明：D7 用于早期方向校验；D14 作为主决策门槛。

### D7（预警阈值）
- ActivationRate（24h）≥ **35%**
- PayFromActivation（7d）≥ **8%**
- PayFromInstall（7d）≥ **2.8%**

### D14（达标阈值）
- ActivationRate（24h）≥ **42%**
- PayFromActivation（14d）≥ **12%**
- PayFromInstall（14d）≥ **5.0%**

### 决策规则
- 满足 D14 全部阈值：允许小幅放量（+20%/周）。
- D7 连续 2 天低于任一阈值：进入黄灯整改（仅保留高意图渠道）。
- D14 任一核心阈值低于目标 20% 以上：红灯止损，进入 `PAUSED`。

---

## 4) 预算上限 $500 的日燃烧上限与超限预警

### 日燃烧上限（按 14 天窗口）
- `DailyCap = $500 / 14 = $35.71`
- 执行口径：
  - **软上限（预警）**：$30/天（约 84% DailyCap）
  - **硬上限（禁止超发）**：$36/天
  - **熔断线（强停）**：$43/天（120% DailyCap）

### 累计节奏控制（防前期透支）
- `CumulativePlan(day_n) = n * 35.71`
- 预警：累计花费 > 110% 计划值
- 强停：累计花费 > 125% 计划值

### 预警分级与动作
- **Yellow（黄灯）**：
  - 条件：单日 > $30 或累计 > 110% 计划
  - 动作：当日降 30% 出价/预算，冻结低转化素材
- **Orange（橙灯）**：
  - 条件：单日 ≥ $36 或 D7 阈值触发 2 项下滑
  - 动作：仅保留 Top 渠道；新实验暂停 24h
- **Red（红灯）**：
  - 条件：单日 ≥ $43 或累计 > 125% 计划 或 D14 未达标且差距>20%
  - 动作：`PAUSED`，提交复盘与修正方案后再恢复

---

## 5) 报表最小字段（每日 23:00 更新）
- Spend_today
- Spend_cumulative
- Installed
- Activated24h
- Paid7d / Paid14d
- ActivationRate / PayFromActivation / PayFromInstall
- StatusLight（Green/Yellow/Orange/Red）
- NextAction（次日动作）

---

## 6) 本卡执行备注
- 本卡由 Metrics 维护预算口径与止损规则。
- 若目录/命名/埋点口径不一致，优先整改再继续 BUILDING。