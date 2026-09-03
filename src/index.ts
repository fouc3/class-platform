// ========== CF Worker 入口 ==========
// 标准 CF Worker 格式：export default { fetch(request, env, ctx) }
// 本文件不含 Node 特有 API，可部署到 Cloudflare Workers。
// 注意：部署时需提供 env.store（KV/D1/R2 实现 Store 接口）和 env.sessions。
import { handleRequest } from "./api/router.ts";
import type { Env } from "./api/router.ts";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      return handleRequest(request, env);
    }
    // 静态资源由 CF Workers Assets 绑定处理（wrangler.toml [assets] 配置）
    return new Response("Not Found", { status: 404 });
  },
};