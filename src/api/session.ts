// ========== 教师会话抽象 ==========
// 登录时校验密码，成功后颁发 token；教师接口通过 Authorization: Bearer <token> 鉴权。
// 接口设计为异步，支持无状态签名 token（多 isolate 兼容）和内存 Map 两种实现。

export interface SessionStore {
  /** 校验密码，正确则颁发并返回 token，错误返回 null */
  create(password: string, expectedPassword: string): Promise<string | null>;
  /** 校验 token 是否有效 */
  verify(token: string): Promise<boolean>;
  /** 登出 */
  revoke(token: string): void;
}

// ========== 无状态 HMAC-SHA256 签名 token ==========
// 适合生产/多 isolate 部署：token 自包含 payload + 签名，无需共享存储。
// 验证失败时（如密钥轮换）简单返回 false，不影响已有 token。

function b64urlEncode(bytes: Uint8Array): string {
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlDecode(s: string): Uint8Array {
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/");
  const pad = "=".repeat((4 - (b64.length % 4)) % 4);
  const bin = atob(b64 + pad);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

async function hmacSign(secret: string, data: string): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data)));
}

function constantTimeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

export class HmacSessionStore implements SessionStore {
  private ttlMs: number;
  private secret: string;

  constructor(secret: string, ttlMs = 12 * 3600 * 1000) {
    this.secret = secret || "dev-only-insecure-secret";
    this.ttlMs = ttlMs;
  }

  async create(password: string, expectedPassword: string): Promise<string | null> {
    if (password !== expectedPassword) return null;
    const exp = Date.now() + this.ttlMs;
    const payload = JSON.stringify({ sub: "teacher", exp });
    const payloadB64 = b64urlEncode(new TextEncoder().encode(payload));
    const sig = await hmacSign(this.secret, payloadB64);
    return payloadB64 + "." + b64urlEncode(sig);
  }

  async verify(token: string): Promise<boolean> {
    const parts = String(token).split(".");
    if (parts.length !== 2) return false;
    const [payloadB64, sigB64] = parts;
    try {
      // 校验签名
      const sig = await hmacSign(this.secret, payloadB64);
      if (!constantTimeEqual(b64urlDecode(sigB64), sig)) return false;
      // 解析 payload 并检查过期
      const data = JSON.parse(new TextDecoder().decode(b64urlDecode(payloadB64))) as { exp?: number };
      if (typeof data.exp !== "number") return false;
      return Date.now() <= data.exp;
    } catch {
      return false;
    }
  }

  revoke(_token: string): void {
    // 无状态 token 无法真正吊销
  }
}

// ========== 内存会话实现（本地开发 / 单 isolate 场景） ==========
// 注：使用全局 Web Crypto 而非 node:crypto，保证 CF Worker 兼容

export class MemorySessionStore implements SessionStore {
  private tokens = new Map<string, number>();
  private ttlMs: number;

  constructor(ttlMs = 12 * 3600 * 1000) {
    this.ttlMs = ttlMs;
  }

  async create(password: string, expectedPassword: string): Promise<string | null> {
    if (password !== expectedPassword) return null;
    const token = crypto.randomUUID();
    this.tokens.set(token, Date.now() + this.ttlMs);
    return token;
  }

  async verify(token: string): Promise<boolean> {
    const exp = this.tokens.get(token);
    if (!exp) return false;
    if (Date.now() > exp) {
      this.tokens.delete(token);
      return false;
    }
    return true;
  }

  revoke(token: string): void {
    this.tokens.delete(token);
  }
}