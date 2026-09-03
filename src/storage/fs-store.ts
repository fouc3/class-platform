// ========== fs 存储实现（临时方案） ==========
// 当前唯一使用 node:fs 的文件。每张表 = data 目录下一个 JSON 文件。
// 后续要换存储（CF KV/D1/R2），新增一个实现 Store 接口的类即可，业务代码零改动。
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Row, Store } from "./types.ts";

export class FsStore implements Store {
  private dir: string;

  constructor(dir: string) {
    this.dir = dir;
  }

  private filePath(name: string): string {
    // 表名即文件名，防止路径穿越
    const safe = name.replace(/[^a-zA-Z0-9_-]/g, "_");
    return path.join(this.dir, `${safe}.json`);
  }

  async readTable(name: string): Promise<Row[]> {
    try {
      const raw = await readFile(this.filePath(name), "utf-8");
      const data = JSON.parse(raw);
      return Array.isArray(data) ? data : [];
    } catch {
      // 文件不存在或损坏 → 视为空表
      return [];
    }
  }

  async writeTable(name: string, rows: Row[]): Promise<void> {
    await mkdir(this.dir, { recursive: true });
    await writeFile(this.filePath(name), JSON.stringify(rows, null, 2), "utf-8");
  }

  /** 初始化数据目录，确保所有表文件存在（对应 v9 的 init_data_files） */
  async init(tables: string[]): Promise<void> {
    await mkdir(this.dir, { recursive: true });
    for (const t of tables) {
      await this.writeTable(t, []);
    }
  }

  /** 列出数据目录下所有表文件（用于导出 zip） */
  async listTables(): Promise<string[]> {
    const { readdir } = await import("node:fs/promises");
    const files = await readdir(this.dir);
    return files.filter((f) => f.endsWith(".json")).map((f) => f.replace(/\.json$/, ""));
  }
}
