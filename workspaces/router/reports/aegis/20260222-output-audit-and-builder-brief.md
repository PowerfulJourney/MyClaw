# 产出审查与 Builder 开工指令（Aegis）

## 1) 审查结论
- Oracle：方向正确（Top1成立），但定价证据仍有区间推断，需要补齐直接价格页截图/链接证据。
- Growth：结构完整，但当前文案偏“Browser Relay”，需收敛到“Local Macro Recorder”单一叙事。
- Metrics：口径完整，可直接作为预算与止损规则。
- Logic：未按时落盘 D1 执行包，视为延迟交付；由 Aegis 先行下发 Builder 开工包。

## 2) 必调项（先修正再放量）
1. 品牌与叙事统一：统一产品名为 `Local Macro Recorder`。
2. 功能边界冻结：仅做 MVP 五项，不接受额外需求插入。
3. 证据补齐：Oracle 在 D+1 补齐 5 个竞品价格页证据。
4. 增长素材修正：Growth 在 D+1 提交与产品名一致的商店文案 A/B。

## 3) Builder 开工范围（Phase-1 Scaffold）
目标：在 24h 内交付可运行脚手架和关键流程闭环。

### 交付物
- `projects/local-macro-recorder/extension/` 基础扩展结构
- 录制 click/type/scroll/wait 事件（最小可用）
- 回放引擎（同域名重放）
- CSV 变量映射（至少支持 3 个字段）
- 基础日志（成功/失败原因）
- README 运行说明

### 验收标准
- 能录制并回放一个 20 步以内流程
- CSV 可成功填充 3 个输入框
- 失败日志可定位步骤号和错误类型
- 本地运行说明可被他人复现

### 止损条件
- 24h 仍无法跑通“录制→回放”闭环：立即降级，仅保留录制+导出JSON
- 48h 无法实现 CSV 变量映射：拆分成后续版本

## 4) 状态
TASK_ID: TASK-20260222-001
Status: BUILDING
NextAgent: Builder
