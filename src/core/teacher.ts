// ========== 教师端业务逻辑 ==========
// 与 v9 teacher_portal() 中所有数据操作一一对应，逻辑不变
import type { Row, Store } from "../storage/types.ts";
import {
  TABLE_STUDENT_LIST,
  TABLE_STUDENT_INFO,
  TABLE_SCORES,
  TABLE_AWARDS,
  TABLE_ACTIVITIES,
  TABLE_TASKS,
  TABLE_FEEDBACK,
  TABLE_LEAVES,
  DATA_TABLES,
  TABLE_SCHEMAS,
} from "../storage/types.ts";
import { todayStr, dateTimeStr, parseScore, pyStr, toNum } from "../config.ts";

// ========== 学生名单 ==========

/** 读取学生名单 */
export async function getStudentList(store: Store): Promise<Row[]> {
  return store.readTable(TABLE_STUDENT_LIST);
}

/** 替换学生名单（上传 xlsx 或手动添加后） */
export async function setStudentList(store: Store, rows: Row[]): Promise<void> {
  await store.writeTable(TABLE_STUDENT_LIST, rows);
}

/** 手动添加一名学生（与 v9 Tab1 一致） */
export async function addStudent(store: Store, name: string, sid: string): Promise<void> {
  const rows = await store.readTable(TABLE_STUDENT_LIST);
  rows.push({ "姓名": name, "学号": sid });
  await store.writeTable(TABLE_STUDENT_LIST, rows);
}

// ========== 学生信息统计 ==========

/** 读取学生档案全表（教师端查看用） */
export async function getInfoRows(store: Store): Promise<Row[]> {
  return store.readTable(TABLE_STUDENT_INFO);
}

/** 读取荣誉全表（教师端查看用） */
export async function getAwardRows(store: Store): Promise<Row[]> {
  return store.readTable(TABLE_AWARDS);
}

export interface InfoMetrics {
  count: number;
  male: number;
  female: number;
  avgAge: number;
}

/** 学生信息统计（与 v9 Tab2 一致） */
export function getInfoMetrics(rows: Row[]): InfoMetrics {
  const count = rows.length;
  const male = rows.filter((r) => r["性别"] === "男").length;
  const female = rows.filter((r) => r["性别"] === "女").length;
  const numericAges = rows
    .filter((r) => /^\d+$/.test(r["年龄"] ?? ""))
    .map((r) => parseInt(r["年龄"]!, 10))
    .filter((n) => !isNaN(n));
  const avgAge = numericAges.length > 0 ? numericAges.reduce((a, b) => a + b, 0) / numericAges.length : 0;
  return { count, male, female, avgAge };
}

/** 生成 CSV 文本（utf-8-sig BOM），与 v9 导出一致 */
export function csvFromRows(rows: Row[], columns: string[]): string {
  // BOM 用于 Excel 正确识别 UTF-8 中文
  const bom = "\uFEFF";
  const header = columns.map(escapeCsvField).join(",");
  const lines = rows.map((row) => {
    return columns.map((col) => escapeCsvField(row[col] ?? "")).join(",");
  });
  return bom + header + "\n" + lines.join("\n");
}

function escapeCsvField(val: string): string {
  // CSV 注入防护：以 = + - @ 制表符、回车开头的字段加单引号前缀
  const safeVal = /^[=+\-@\t\r]/.test(val) ? `'${val}` : val;
  if (safeVal.includes(",") || safeVal.includes('"') || safeVal.includes("\n")) {
    return `"${safeVal.replace(/"/g, '""')}"`;
  }
  return safeVal;
}

// ========== 量化管理 ==========

export interface ScoreSummaryRow {
  当事人: string;
  加分合计: number;
  扣分合计: number;
  总分: number;
  记录数: number;
}

function parseDate(s: string | undefined | null): Date | null {
  if (!s) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const d = new Date(s + "T00:00:00");
  return isNaN(d.getTime()) ? null : d;
}

/**
 * 查询量化分摘要（与 v9 Tab3 一致）
 * @param start 起始日期 YYYY-MM-DD
 * @param end 截止日期 YYYY-MM-DD
 */
export async function getScoreSummary(
  store: Store,
  start: string,
  end: string
): Promise<{
  minDate: string;
  summary: ScoreSummaryRow[];
  detailData: Record<string, Row[]>;
  totalRecords: number;
}> {
  const rows = await store.readTable(TABLE_SCORES);
  // 解析时间（与 v9 pd.to_datetime(errors='coerce') 一致）
  const parsedDates = rows.map((r) => parseDate(r["时间"]));
  // 计算最小日期
  const validDates = parsedDates.filter((d): d is Date => d !== null);
  const minDate = validDates.length > 0
    ? validDates.reduce((a, b) => (a < b ? a : b)).toISOString().slice(0, 10)
    : todayStr();
  // 筛选日期范围
  const startD = new Date(start + "T00:00:00");
  const endD = new Date(end + "T00:00:00");
  const filtered = rows.filter((_, i) => {
    const d = parsedDates[i];
    if (!d) return false;
    return d >= startD && d <= endD;
  });
  // 展开多人行（与 v9 一致：当事人含逗号即拆分，空名过滤）
  const expanded: Row[] = [];
  for (const r of filtered) {
    if ((r["当事人"] ?? "").includes(",")) {
      const persons = (r["当事人"] ?? "").split(",").map((s) => s.trim()).filter(Boolean);
      for (const p of persons) {
        expanded.push({ ...r, "当事人": p });
      }
    } else {
      expanded.push(r);
    }
  }
  // 分组汇总
  const groupMap = new Map<string, { 加分合计: number; 扣分合计: number; 总分: number; 记录数: number }>();
  const detailMap = new Map<string, Row[]>();
  for (const r of expanded) {
    const name = r["当事人"] ?? "";
    if (!name) continue;
    const add = parseScore(r["加分"]);
    const sub = parseScore(r["扣分"]);
    const g = groupMap.get(name) ?? { 加分合计: 0, 扣分合计: 0, 总分: 0, 记录数: 0 };
    g.加分合计 += add;
    g.扣分合计 += sub;
    g.总分 = g.加分合计 - g.扣分合计;
    g.记录数 += 1;
    groupMap.set(name, g);
    const dList = detailMap.get(name) ?? [];
    dList.push(r);
    detailMap.set(name, dList);
  }
  const summary: ScoreSummaryRow[] = Array.from(groupMap.entries())
    .map(([name, g]) => ({
      当事人: name,
      ...g,
    }))
    .sort((a, b) => b.总分 - a.总分); // 按总分降序（与 v9 一致）
  // 详情按时间降序
  for (const [name, list] of detailMap) {
    list.sort((a, b) => {
      const da = parseDate(a["时间"]);
      const db = parseDate(b["时间"]);
      if (!da && !db) return 0;
      if (!da) return 1;
      if (!db) return -1;
      return db.getTime() - da.getTime();
    });
  }
  return { minDate, summary, detailData: Object.fromEntries(detailMap), totalRecords: filtered.length };
}

/** 添加一条量化记录（与 v9 一致） */
export async function addScoreRecord(
  store: Store,
  data: {
    信息来源: string;
    加扣分方向: string;
    上报周期: string;
    时间: string;
    加分: number;
    扣分: number;
    当事人: string;
    原由: string;
    证明材料: string;
  }
): Promise<void> {
  const rows = await store.readTable(TABLE_SCORES);
  rows.push({
    "信息来源": data["信息来源"],
    "加扣分方向": data["加扣分方向"],
    "上报周期": data["上报周期"],
    "时间": data["时间"],
    "加分": pyStr(data["加分"]),
    "扣分": pyStr(data["扣分"]),
    "当事人": data["当事人"],
    "原由": data["原由"],
    "证明材料": data["证明材料"],
  });
  await store.writeTable(TABLE_SCORES, rows);
}

// ========== 活动发布 ==========

/** 发布活动（与 v9 Tab4 一致） */
export async function publishActivity(
  store: Store,
  data: { 活动名称: string; 活动描述: string; 截止时间: string; 状态: string }
): Promise<void> {
  const rows = await store.readTable(TABLE_ACTIVITIES);
  rows.push({
    "活动名称": data["活动名称"],
    "活动描述": data["活动描述"],
    "发布时间": todayStr(),
    "截止时间": data["截止时间"],
    "状态": data["状态"],
  });
  await store.writeTable(TABLE_ACTIVITIES, rows);
}

/** 获取所有已发布活动 */
export async function getActivities(store: Store): Promise<Row[]> {
  return store.readTable(TABLE_ACTIVITIES);
}

// ========== 学生荣誉 ==========

export interface AwardMetrics {
  total: number;
  people: number;
  maxLevel: string;
}

/** 荣誉统计（与 v9 Tab5 一致：maxLevel 为字符串最大——注：python max() 按字典序） */
export function getAwardMetrics(rows: Row[]): AwardMetrics {
  const total = rows.length;
  const people = new Set(rows.map((r) => r["姓名"])).size;
  const levels = rows.map((r) => r["奖项级别"] ?? "").filter(Boolean);
  const maxLevel = levels.length > 0 ? levels.reduce((a, b) => (a > b ? a : b)) : "无";
  return { total, people, maxLevel };
}

// ========== 任务与反馈 ==========

/** 读取所有任务 */
export async function getTasks(store: Store): Promise<Row[]> {
  return store.readTable(TABLE_TASKS);
}

/** 读取反馈（按日期筛选，与 v9 Tab6 一致：日期精确匹配） */
export async function getFeedback(store: Store, date?: string): Promise<{ rows: Row[]; dates: string[] }> {
  const rows = await store.readTable(TABLE_FEEDBACK);
  const dateSet = new Set<string>();
  for (const r of rows) {
    if (r["日期"]) dateSet.add(r["日期"]);
  }
  const dates = Array.from(dateSet).sort().reverse(); // 降序，与 v9 sorted(..., reverse=True) 一致
  const filtered = date ? rows.filter((r) => r["日期"] === date) : rows;
  return { rows: filtered, dates };
}

// ========== 请假审批 ==========

export interface LeaveWithIndex {
  index: number;
  row: Row;
}

/** 获取所有请假（含下标，与 v9 用 df index 一致） */
export async function getLeaves(store: Store): Promise<LeaveWithIndex[]> {
  const rows = await store.readTable(TABLE_LEAVES);
  return rows.map((r, i) => ({ index: i, row: { ...r } }));
}

/** 审批请假（与 v9 一致：按下标设置状态与意见） */
export async function approveLeave(store: Store, index: number, status: string, comment: string): Promise<boolean> {
  const rows = await store.readTable(TABLE_LEAVES);
  if (index < 0 || index >= rows.length) return false;
  rows[index]["预审状态"] = status;
  rows[index]["班主任意见"] = comment;
  await store.writeTable(TABLE_LEAVES, rows);
  return true;
}

// ========== 数据导出 ==========

/** 获取所有数据表的内容（用于打包 zip，包括独立管理的学生名单） */
export async function getAllTableContents(store: Store): Promise<Record<string, Row[]>> {
  const result: Record<string, Row[]> = {};
  for (const t of [TABLE_STUDENT_LIST, ...DATA_TABLES]) {
    result[t] = await store.readTable(t);
  }
  return result;
}