// ========== 教师会话（简化鉴权） ==========
// 登录时校验密码，成功后颁发随机 token；教师接口通过 Authorization: Bearer <token> 鉴权。
// 会话存储独立抽象，本地用内存实现；后续可换成 CF KV / Durable Object 等。
// 注：randomUUID 使用全局 Web Crypto（CF Worker 与 Node 26 均可用）
const randomUUID = () => crypto.randomUUID();
export interface SessionStore {
  /** 校验密码，正确则颁发并返回 token，错误返回 null */
  create(password: string, expectedPassword: string): string | null;
  /** 校验 token 是否有效 */
  verify(token: string): boolean;
  /** 登出 */
  revoke(token: string): void;
}

/** 内存会话实现（本地 dev server 使用） */
export class MemorySessionStore implements SessionStore {
  private tokens = new Map<string, number>(); // token -> 过期时间戳(ms)
  private ttlMs: number;

  constructor(ttlMs = 12 * 3600 * 1000) {
    this.ttlMs = ttlMs;
  }

  create(password: string, expectedPassword: string): string | null {
    if (password !== expectedPassword) return null;
    const token = randomUUID();
    this.tokens.set(token, Date.now() + this.ttlMs);
    return token;
  }

  verify(token: string): boolean {
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
