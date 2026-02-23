# SKILL_SEARCH.md

Project: demo-20260223-01  
Task: 交付“可用 Demo 最小闭环”（能跑、能看、能复现）

## Reuse Scan (No reinvention)

### Option candidates
1. **纯静态前端 + 浏览器原生能力（推荐）**
   - Reuse: HTML/CSS/Vanilla JS + localStorage
   - 启动方式: `python3 -m http.server`
   - 依赖: 0（系统自带 Python）
   - 风险: 极低

2. React/Vite 脚手架
   - Reuse: npm ecosystem
   - 依赖安装慢，环境差异风险更高
   - 对本次“最短路径 Demo”过重

3. Flask/FastAPI 后端 + 前端
   - 适合 API demo，但本任务未要求后端
   - 工期和复杂度高于必要值

## Decision
采用 **Option 1（纯静态前端）**，以最短路径完成“可跑、可看、可复现”。

## Demo closed-loop scenario (<=3 steps)
1. 打开 Demo 页面
2. 输入一条任务并点击“添加”
3. 刷新页面后仍可看到任务（localStorage 持久化）

## Out-of-scope lock
- 不引入框架
- 不做非关键 UI 优化
- 不扩展认证/多用户/云端存储
