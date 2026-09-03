# 班级学生成长平台（TypeScript 版）

基于 `class_platform_v9.py` 的 TypeScript 复刻版，业务逻辑不变，采用 **Cloudflare Worker 标准** 架构，
**D1 数据库存储**，以**网站形式**提供服务（含学生端 + 教师后台）。

## 快速开始

```bash
npm install                 # 安装依赖（xlsx、fflate）
npm run db:init             # 初始化本地 D1：v9 数据 → d1.sql → 导入本地库
npm run dev                 # 启动本地开发服务器（wrangler dev --local）→ http://127.0.0.1:8787
```

- `npm run db:init` 会自动扫描 `class_data/*.csv`（v9 的数据文件）+ 根目录 `student_list.xlsx`，
  生成 `d1.sql` 并导入本地 D1 数据库（`.wrangler/state/`，已 gitignore）。
- 学生端入口：输入姓名登录（必须是名单上的学生）。
- 教师后台：默认密码 `123456`（可通过环境变量 `TEACHER_PASSWORD` 覆盖）。
- 生产部署：先 `wrangler d1 create class-platform-db` 拿到真实 database_id 填入 `wrangler.toml`，
  再 `wrangler d1 execute class-platform-db --remote --file=d1.sql` 导入数据，最后 `wrangler deploy`。

## 架构

```
src/
├── index.ts              # CF Worker 入口（export default { fetch }，env.DB → D1Store）
├── api/
│   ├── router.ts         # API 路由（/api/student/*、/api/teacher/*）
│   └── session.ts        # 教师会话（登录颁发 token，MemorySessionStore）
├── core/
│   ├── student.ts        # 学生端业务逻辑（登录/档案/量化分/荣誉/活动/任务/反馈/请假）
│   ├── teacher.ts        # 教师端业务逻辑（名单/统计/量化/活动/审批/导出）
│   ├── validate.ts       # 身份证校验/年龄计算/手机号校验
│   └── ai.ts             # AI 分析函数（与 v9 一致：功能关闭占位）
├── storage/
│   ├── types.ts          # 存储抽象：Store 接口 + 统一 readTable/writeTable
│   ├── d1-store.ts       # D1 实现（每张业务表 = id 自增主键 + data JSON 列）
│   └── (可扩展其他实现：KV / R2 / 内存等，业务代码零改动)
└── scripts/
    └── migrate-v9-d1.ts  # v9 CSV/xlsx → D1 SQL 迁移脚本

public/                   # 前端（原生 HTML/CSS/JS，重建自 v9 页面结构）
├── index.html            # 学生 7 tab + 教师 8 tab 单页应用
├── style.css
└── app.js
```

## D1 存储格式（自定）

每张业务表对应 D1 一张表，两列：

| 列 | 类型 | 说明 |
|----|------|------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | 行序稳定（对应 v9 的 df index，任务/请假按下标更新依赖它） |
| `data` | TEXT | 整行 JSON（业务层 Row 全量写入） |

理由：业务层 `Store` 接口语义是「整表读写」+ 内存过滤，无 SQL 查询需求；
JSON 列可规避中文列名 / student_list 动态列问题；后续需要按列查询时再加真实列即可。

## 迁移脚本用法

```bash
node src/scripts/migrate-v9-d1.ts                       # 默认：class_data/ + student_list.xlsx → d1.sql
node src/scripts/migrate-v9-d1.ts --csv-dir <dir> --xlsx <file> --out <file>
```

输出 `d1.sql`：`CREATE TABLE IF NOT EXISTS` + `INSERT` 语句，兼容 `wrangler d1 execute --file`。

## 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 本地启动网站（wrangler dev --local，D1 存储） |
| `npm run migrate` | v9 数据 → 生成 d1.sql |
| `npm run db:init` | 生成 d1.sql 并导入本地 D1 |
| `npm run typecheck` | TypeScript 类型检查 |

## 说明

- 教师密码通过环境变量 `TEACHER_PASSWORD` 注入（CF Worker 标准 —— `wrangler secret put` 或 `[vars]`），本地未设置时默认 `123456`。
- `class_platform_v9.py` 为原版参考，`class_platform_v9.html` 为原前端渲染快照（不可交互）。
