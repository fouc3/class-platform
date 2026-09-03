// ========== D1 存储实现 ==========
// 每张业务表 = D1 一张表，两列：
//   id   INTEGER PRIMARY KEY AUTOINCREMENT   —— 行序稳定（对应 v9 的 df index）
//   data TEXT                                —— 整行 JSON（业务层 Row 全量写入）
// 业务层 Store 接口语义为「整表读写」，本实现完全适配；后续如需按列查询可加真实列。
// 不含任何 Node 特有 API，可直接在 Cloudflare Workers 上运行。

import type { Row, Store } from "./types.ts";

// ---------- D1 最小接口类型（不依赖 @cloudflare/workers-types） ----------
export interface D1Result {
  results?: unknown[];
  meta: {
    changes: number;
    last_row_id: number;
    duration: number;
    size_after: number;
    rows_read: number;
    rows_written: number;
  };
}

export interface D1PreparedStatement {
  bind(...values: unknown[]): D1PreparedStatement;
  all(): Promise<D1Result>;
  run(): Promise<D1Result>;
  first<T = Record<string, unknown>>(): Promise<T | null>;
}

export interface D1Database {
  prepare(sql: string): D1PreparedStatement;
  batch(statements: D1PreparedStatement[]): Promise<D1Result[]>;
  exec(sql: string): Promise<void>;
}

/** 表名消毒：只允许字母数字下划线（表名来自内部常量，防御性处理） */
function safeTable(name: string): string {
  return `"${name.replace(/[^a-zA-Z0-9_]/g, "_")}"`;
}

export class D1Store implements Store {
  private db: D1Database;

  constructor(db: D1Database) {
    this.db = db;
  }

  /** 初始化：确保所有表存在（对应 v9 init_data_files） */
  async init(tables: string[]): Promise<void> {
    for (const t of tables) {
      const tq = safeTable(t);
      await this.db
        .prepare(
          `CREATE TABLE IF NOT EXISTS ${tq} (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)`
        )
        .run();
    }
  }

  async readTable(name: string): Promise<Row[]> {
    const tq = safeTable(name);
    const res = await this.db.prepare(`SELECT id, data FROM ${tq} ORDER BY id`).all();
    const rows: Row[] = [];
    for (const item of res.results ?? []) {
      const rec = item as Record<string, unknown>;
      try {
        const parsed = JSON.parse(String(rec.data ?? ""));
        if (parsed && typeof parsed === "object") rows.push(parsed as Row);
      } catch {
        // 单行损坏则跳过，保持与其他实现一致的容错
      }
    }
    return rows;
  }

  /** 整表覆盖写入（先清空再按序插入，id 自增保持行序） */
  async writeTable(name: string, rows: Row[]): Promise<void> {
    const tq = safeTable(name);
    // 确保表存在（首次写入时）
    await this.db
      .prepare(
        `CREATE TABLE IF NOT EXISTS ${tq} (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)`
      )
      .run();
    const stmts: D1PreparedStatement[] = [
      this.db.prepare(`DELETE FROM ${tq}`),
    ];
    for (const row of rows) {
      stmts.push(
        this.db
          .prepare(`INSERT INTO ${tq} (data) VALUES (?)`)
          .bind(JSON.stringify(row))
      );
    }
    await this.db.batch(stmts);
  }
}
