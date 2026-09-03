// ========== 学生名单导入 ==========
// 读取 student_list.xlsx（姓名/学号/班级），转成 Row[]，供 seed 与 dev server 自动导入使用。
import * as XLSX from "xlsx";
import { readFile } from "node:fs/promises";
import type { Row } from "../storage/types.ts";

/**
 * 从 xlsx 文件内容导入学生名单
 * @returns [{姓名, 学号, 班级?...}]，所有值转为字符串
 */
export function parseStudentListXlsx(data: Uint8Array): Row[] {
  const wb = XLSX.read(data, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const rawRows = XLSX.utils.sheet_to_json<Record<string, unknown>>(ws, { defval: "" });
  return rawRows.map((r) => {
    const row: Row = {};
    for (const [k, v] of Object.entries(r)) {
      row[k] = String(v ?? "");
    }
    return row;
  });
}

/** 从文件路径导入（seed 脚本 / dev server 使用） */
export async function importStudentListFromXlsx(filePath: string): Promise<Row[]> {
  const data = await readFile(filePath);
  return parseStudentListXlsx(new Uint8Array(data));
}

// 直接运行时：node src/scripts/seed.ts [xlsx路径] [输出json路径]
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split(/[\\/]/).pop() ?? "")) {
  const { writeFile } = await import("node:fs/promises");
  const path = await import("node:path");
  const cwd = process.cwd();
  const xlsxPath = path.resolve(cwd, process.argv[2] ?? "student_list.xlsx");
  const outPath = path.resolve(cwd, process.argv[3] ?? "data/student_list.json");
  const rows = await importStudentListFromXlsx(xlsxPath);
  await writeFile(outPath, JSON.stringify(rows, null, 2), "utf-8");
  console.log(`已导入 ${rows.length} 条学生记录 → ${outPath}`);
}