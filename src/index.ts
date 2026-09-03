// ========== CF Worker 入口 ==========
// 标准 CF Worker 格式：export default { fetch(request, env, ctx) }
// 存储：env.DB（D1）→ D1Store；会话：env.sessions 或内存实现。
import { handleRequest } from "./api/router.ts";
import type { Env } from "./api/router.ts";
import { MemorySessionStore } from "./api/session.ts";
import { D1Store, type D1Database } from "./storage/d1-store.ts";
import type { Store } from "./storage/types.ts";
import { DATA_TABLES, TABLE_STUDENT_LIST } from "./storage/types.ts";

export interface WorkerEnv {
  /** D1 数据库绑定（wrangler.toml [[d1_databases]]） */
  DB?: D1Database;
  /** 可选：外部注入的存储实现（测试/替代存储时用） */
  store?: Store;
  /** 可选：外部注入的会话实现（默认内存） */
  sessions?: import("./api/session.ts").SessionStore;
  /** 教师密码（wrangler secret / [vars] 注入） */
  TEACHER_PASSWORD?: string;
}

// 模块级懒初始化：每 isolate 只建一次表、一次会话实例。
// 注意：内存会话仅适合本地/单 isolate 场景；生产多 isolate 建议改用 KV-backed 会话（通过 env.sessions 注入）。
let storePromise: Promise<Store> | null = null;
const defaultSessions = new MemorySessionStore();

function getStore(env: WorkerEnv): Promise<Store> {
  if (env.store) return Promise.resolve(env.store);
  if (!env.DB) return Promise.reject(new Error("缺少 D1 数据库绑定（env.DB）"));
  if (!storePromise) {
    storePromise = (async () => {
      const store = new D1Store(env.DB!);
      await store.init([...DATA_TABLES, TABLE_STUDENT_LIST]);
      return store;
    })();
  }
  return storePromise;
}

export default {
  async fetch(request: Request, env: WorkerEnv): Promise<Response> {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) {
      // 静态资源由 CF Workers Assets 绑定处理（wrangler.toml [assets] 配置）
      return new Response("Not Found", { status: 404 });
    }
    let store: Store;
    try {
      store = await getStore(env);
    } catch (e) {
      return new Response((e as Error).message, { status: 500 });
    }
    const fullEnv: Env = {
      store,
      sessions: env.sessions ?? defaultSessions,
      TEACHER_PASSWORD: env.TEACHER_PASSWORD,
    };
    return handleRequest(request, fullEnv);
  },
};
