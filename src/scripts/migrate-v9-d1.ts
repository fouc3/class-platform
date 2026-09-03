// ========== v9 数据 → D1 SQL 迁移脚本 ==========
// 用法：node src/scripts/migrate-v9-d1.ts [--csv-dir class_data] [--xlsx student_list.xlsx] [--out d1.sql]
// 输出：CREATE TABLE IF NOT EXISTS + INSERT 语句，可直接用 wrangler d1 execute --local --file 导入
import { readFile, readdir, stat, writeFile } from "node:fs/promises";
import * as XLSX from "xlsx";
import { TABLE_SCHEMAS, DATA_TABLES, TABLE_STUDENT_LIST } from "../storage/types.ts";

// ---------- RFC4180 CSV 解析器 ----------
function parseCsv(text: string): string[][] {
  // 移除 BOM
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
  // 标准化换行（\r\n → \n，裸 \r → \n）
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    const next = text[i + 1];
    if (inQuotes) {
      if (c === '"' && next === '"') {
        field += '"';
        i++;
      } else if (c === '"') {
        inQuotes = false;
      } else {
        field += c;
      }
    } else {
      if (c === '"') {
        inQuotes = true;
      } else if (c === ",") {
        row.push(field);
        field = "";
      } else if (c === "\n") {
        row.push(field);
        rows.push(row);
        row = [];
        field = "";
      } else {
        field += c;
      }
    }
  }
  // 处理最后一行
  if (field || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

// ---------- SQL 值转义 ----------
function escSql(val: string): string {
  // 单引号 → ''，空值 → ''（TEXT 字段）
  return `'${val.replace(/'/g, "''")}'`;
}

// ---------- 生成 CREATE TABLE ----------
function genCreateTable(table: string): string {
  const tq = safeName(table);
  return `CREATE TABLE IF NOT EXISTS ${tq} (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL);`;
}

function safeName(name: string): string {
  return `"${name.replace(/[^a-zA-Z0-9_]/g, "_")}"`;
}

// ---------- 生成 INSERT ----------
function genInsert(table: string, rows: Record<string, string>[]): string[] {
  if (rows.length === 0) return [];
  const tq = safeName(table);
  return rows.map((r) => {
    const json = JSON.stringify(r);
    return `INSERT INTO ${tq} (data) VALUES (${escSql(json)});`;
  });
}

// ---------- 从 CSV 文件解析表 ----------
function parseTableFromCsv(text: string): { columns: string[]; rows: Record<string, string>[] } {
  const parsed = parseCsv(text);
  if (parsed.length < 1) return { columns: [], rows: [] };
  const columns = parsed[0].map((c) => c.trim());
  const rows = parsed.slice(1).map((row) => {
    const rec: Record<string, string> = {};
    columns.forEach((col, i) => {
      rec[col] = row[i] ?? "";
    });
    return rec;
  });
  return { columns, rows };
}

// ---------- 从 xlsx 解析学生名单 ----------
function parseStudentListFromXlsx(data: Uint8Array): Record<string, string>[] {
  const wb = XLSX.read(data, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const raw = XLSX.utils.sheet_to_json<Record<string, unknown>>(ws, { defval: "" });
  return raw.map((r) => {
    const rec: Record<string, string> = {};
    for (const [k, v] of Object.entries(r)) rec[k] = String(v ?? "");
    return rec;
  });
}

// ========== 主流程 ==========
export interface MigrateOptions {
  csvDir: string;     // class_data/ 目录（v9 的 CSV 文件）
  xlsxPath: string;   // student_list.xlsx 路径
  outPath: string;    // 输出 SQL 文件路径
}

export async function migrateV9ToD1(opts: MigrateOptions): Promise<void> {
  const lines: string[] = [
    "-- 班级学生成长平台 D1 迁移脚本",
    "-- 由 scripts/migrate-v9-d1.ts 自动生成",
    "-- 注意：D1 不支持事务关键字（BEGIN/COMMIT），按单语句执行",
    "PRAGMA foreign_keys=OFF;",
    "",
  ];

  // 1. 处理 9 张数据表
  for (const table of DATA_TABLES) {
    lines.push(`-- ${table}`);
    lines.push(genCreateTable(table));
    const csvPath = `${opts.csvDir}/${table}.csv`;
    try {
      await stat(csvPath);
      const raw = await readFile(csvPath, "utf-8");
      const { rows } = parseTableFromCsv(raw);
      if (rows.length > 0) {
        lines.push(...genInsert(table, rows));
        console.log(`  ${table}: ${rows.length} 行`);
      } else {
        console.log(`  ${table}: 空表`);
      }
    } catch {
      console.log(`  ${table}: 文件不存在，仅建表`);
    }
    lines.push("");
  }

  // 2. 处理学生名单
  lines.push(`-- ${TABLE_STUDENT_LIST}`);
  lines.push(genCreateTable(TABLE_STUDENT_LIST));
  try {
    await stat(opts.xlsxPath);
    const data = await readFile(opts.xlsxPath);
    const rows = parseStudentListFromXlsx(new Uint8Array(data));
    if (rows.length > 0) {
      lines.push(...genInsert(TABLE_STUDENT_LIST, rows));
      console.log(`  ${TABLE_STUDENT_LIST}: ${rows.length} 行`);
    }
  } catch {
    console.log(`  ${TABLE_STUDENT_LIST}: 文件不存在，仅建表`);
  }
  lines.push("");
  await writeFile(opts.outPath, lines.join("\n"), "utf-8");
  console.log(`\n已写入: ${opts.outPath}`);
}

// ========== CLI 入口 ==========
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split(/[\\/]/).pop() ?? "")) {
  const args = process.argv.slice(2);
  const csvDir = args.find((a, i) => a === "--csv-dir" && args[i + 1]) ? args[args.indexOf("--csv-dir") + 1] : "class_data";
  const xlsxPath = args.find((a, i) => a === "--xlsx" && args[i + 1]) ? args[args.indexOf("--xlsx") + 1] : "student_list.xlsx";
  const outPath = args.find((a, i) => a === "--out" && args[i + 1]) ? args[args.indexOf("--out") + 1] : "d1.sql";
  migrateV9ToD1({ csvDir, xlsxPath, outPath }).catch((e) => {
    console.error("迁移失败:", e.message);
    process.exit(1);
  });
}