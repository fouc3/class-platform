# 班级学生成长平台（TypeScript 版）

基于 `class_platform_v9.py` 的 TypeScript 复刻版，业务逻辑不变，采用 **Cloudflare Worker 标准** 架构，以**网站形式**提供服务（含学生端 + 教师后台）。

## 快速开始

```bash
npm install          # 安装依赖（xlsx、fflate）
npm run dev          # 启动本地开发服务器 → http://127.0.0.1:8787
```

- 首次启动自动读取根目录 `student_list.xlsx` 导入学生名单（姓名/学号/班级）。
- 学生端入口：输入姓名登录（必须是名单上的学生）。
- 教师后台：默认密码 `123456`（侧边栏切到「👩‍🏫 教师后台」登录）。
- 运行数据保存在 `data/`（每张表一个 JSON 文件），已 gitignore。

## 架构

```
src/
├── index.ts            # CF Worker 入口（export default { fetch }，标准格式）
├── api/
│   ├── router.ts       # API 路由（/api/student/*、/api/teacher/*）
│   └── session.ts      # 教师会话（登录颁发 token，MemorySessionStore）
├── core/
│   ├── student.ts      # 学生端业务逻辑（登录/档案/量化分/荣誉/活动/任务/反馈/请假）
│   ├── teacher.ts      # 教师端业务逻辑（名单/统计/量化/活动/审批/导出）
│   ├── validate.ts     # 身份证校验/年龄计算/手机号校验
│   └── ai.ts           # AI 分析函数（与 v9 一致：功能关闭占位）
├── storage/
│   ├── types.ts        # 存储抽象：Store 接口 + 统一 readTable/writeTable
│   └── fs-store.ts     # fs 实现（唯一触碰 node:fs 的文件）
├── server/dev.ts       # 本地开发服务器（Node http 模拟 CF Worker 环境）
└── scripts/seed.ts     # 学生名单 xlsx → JSON 导入

public/                 # 前端（原生 HTML/CSS/JS，重建自 v9 页面结构）
├── index.html          # 学生 7 tab + 教师 8 tab 单页应用
├── style.css
└── app.js
```

## 关键设计

1. **存储抽象（换存储零改动）**：所有数据读写只通过 `Store` 接口的统一函数
   `readTable(name)` / `writeTable(name, rows)`。目前 `FsStore` 用 JSON 文件实现；
   后续换 Cloudflare KV / D1 / R2 只需新增一个实现类，业务代码不动。
2. **业务逻辑与 v9 一致**：身份证 18 位加权校验、年龄推算、手机号校验、档案 upsert、
   量化分按"当事人包含姓名"匹配 + 多人拆行汇总、请假审批、zip 导出等规则逐一复刻。
3. **CF Worker 标准**：`src/index.ts` 是标准 `export default { fetch }` 入口，
   不含 Node 特有 API；部署到 Cloudflare 时静态资源走 Workers Assets（见 `wrangler.toml`），
   存储/会话替换为云端实现即可。

## 部署到 Cloudflare（可选）

```bash
# 1. 实现 Store 接口的云端版本（如 KV/D1），在 wrangler.toml 中绑定
# 2. 会话改为 KV-backed
npx wrangler deploy
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 本地启动网站（fs 存储） |
| `npm run typecheck` | TypeScript 类型检查 |
| `npm run seed` | 手动重新导入 student_list.xlsx → data/student_list.json |

## 说明

- 教师密码通过环境变量 `TEACHER_PASSWORD` 注入（CF Worker 标准 —— `wrangler secret put` 或 `[vars]`），本地未设置时默认 `123456`。
- `class_platform_v9.py` 为原版参考，`class_platform_v9.html` 为原前端渲染快照（不可交互）。
