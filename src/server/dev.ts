// ========== 本地开发服务器 ==========
// 用 Node http 模拟 CF Worker 运行环境：静态资源 + /api/* 交给 handleRequest。
// 存储使用 FsStore（JSON 文件）。启动：npm run dev
import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FsStore } from "../storage/fs-store.ts";
import { MemorySessionStore } from "../api/session.ts";
import { handleRequest } from "../api/router.ts";
import type { Env } from "../api/router.ts";
import { DATA_TABLES, TABLE_STUDENT_LIST, TABLE_SCHEMAS } from "../storage/types.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..", "..");
const PUBLIC_DIR = path.join(ROOT, "public");
const DATA_DIR = path.join(ROOT, "data");

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".txt": "text/plain; charset=utf-8",
};

async function serveStatic(reqPath: string): Promise<Response> {
  // 防止路径穿越
  const safePath = reqPath.replace(/^\/+/, "");
  let filePath = path.join(PUBLIC_DIR, safePath);
  if (safePath === "" || safePath.endsWith("/")) {
    filePath = path.join(filePath, "index.html");
  }
  try {
    const st = await stat(filePath);
    if (!st.isFile()) throw new Error("not a file");
    const data = await readFile(filePath);
    const ext = path.extname(filePath).toLowerCase();
    return new Response(data, {
      headers: { "Content-Type": MIME[ext] ?? "application/octet-stream" },
    });
  } catch {
    // 尝试返回 index.html（SPA 回退）
    try {
      const data = await readFile(path.join(PUBLIC_DIR, "index.html"));
      return new Response(data, {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    } catch {
      return new Response("Not Found", { status: 404 });
    }
  }
}

export async function startServer(port = 8787, host = "127.0.0.1"): Promise<void> {
  const store = new FsStore(DATA_DIR);
  // 初始化所有数据表
  const allTables = [...DATA_TABLES, TABLE_STUDENT_LIST];
  await store.init(allTables);
  // 学生名单：如果 data/student_list.json 为空且存在 student_list.xlsx，则自动导入
  await autoImportStudentList(store);

  const env: Env = {
    store,
    sessions: new MemorySessionStore(),
    // 本地模拟 CF Worker 环境变量注入：优先读 process.env.TEACHER_PASSWORD
    TEACHER_PASSWORD: process.env.TEACHER_PASSWORD,
  };

  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? "/", `http://${host}:${port}`);
      // 构建标准 Request 对象
      const headers = new Headers();
      for (const [k, v] of Object.entries(req.headers)) {
        if (typeof v === "string") headers.set(k, v);
        else if (Array.isArray(v)) headers.set(k, v.join(", "));
      }
      const body = req.method === "GET" || req.method === "HEAD" ? undefined : req;
      const request = new Request(url.toString(), {
        method: req.method,
        headers,
        body,
        duplex: "half",
      });

      let response: Response;
      if (url.pathname.startsWith("/api/")) {
        response = await handleRequest(request, env);
      } else {
        response = await serveStatic(url.pathname);
      }

      res.writeHead(response.status, Object.fromEntries(response.headers.entries()));
      const buf = Buffer.from(await response.arrayBuffer());
      res.end(buf);
    } catch (e) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Internal Server Error: " + (e as Error).message);
    }
  });

  server.listen(port, host, () => {
    console.log(`班级学生成长平台（TS 版）已启动: http://${host}:${port}`);
  });
}

/** 若 data/student_list.json 为空且根目录有 student_list.xlsx，则导入 */
async function autoImportStudentList(store: FsStore): Promise<void> {
  const rows = await store.readTable(TABLE_STUDENT_LIST);
  if (rows.length > 0) return;
  const xlsxPath = path.join(ROOT, "student_list.xlsx");
  try {
    await stat(xlsxPath);
    const { importStudentListFromXlsx } = await import("../scripts/seed.ts");
    const imported = await importStudentListFromXlsx(xlsxPath);
    if (imported.length > 0) {
      await store.writeTable(TABLE_STUDENT_LIST, imported);
      console.log(`已自动导入学生名单（${imported.length} 人）`);
    }
  } catch {
    // 没有 xlsx 或导入失败则忽略，保持空名单
  }
}

// 直接运行时启动（node src/server/dev.ts）
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = parseInt(process.env.PORT ?? "8787", 10);
  startServer(port).catch((e) => {
    console.error("启动失败:", e);
    process.exit(1);
  });
}