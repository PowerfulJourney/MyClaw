# METRICS

## 北极星指标
- D14 新付费激活用户数（Paid Activated Accounts）

## 漏斗定义
- install: app_install_success
- activate: activation_complete（account_ready + core_action_success）
- paid: first_payment_success

## 阈值
- D7：激活率 >=35%，激活到付费 >=8%
- D14：激活率 >=42%，激活到付费 >=12%，安装到付费 >=5%

## 预算护栏
- 总预算：$500
- 软上限：$30/天
- 硬上限：$36/天
- 熔断：$43/天
