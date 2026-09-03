// ========== 学生端业务逻辑 ==========
// 与 v9 student_portal() 中所有数据操作一一对应，逻辑不变
import type { Row, Store } from "../storage/types.ts";
import {
  TABLE_STUDENT_LIST,
  TABLE_STUDENT_INFO,
  TABLE_SCORES,
  TABLE_AWARDS,
  TABLE_ACTIVITIES,
  TABLE_STUDENT_ACTIVITIES,
  TABLE_TASKS,
  TABLE_FEEDBACK,
  TABLE_LEAVES,
} from "../storage/types.ts";
import {
  todayStr,
  timeStr,
  dateTimeShortStr,
  dateTimeStr,
  parseScore,
  toNum,
} from "../config.ts";
import { validateIdCard, validatePhone } from "./validate.ts";

/** 校验学生是否在名单中（与 v9 verify_student 一致） */
export async function verifyStudent(store: Store, name: string): Promise<{ valid: boolean; sid: string | null }> {
  const list = await store.readTable(TABLE_STUDENT_LIST);
  if (list.length === 0) return { valid: false, sid: null };
  const matched = list.filter((r) => r["姓名"] === name);
  if (matched.length > 0) {
    const sid = matched[0]["学号"] !== undefined && matched[0]["学号"] !== "" ? matched[0]["学号"] : name;
    return { valid: true, sid };
  }
  return { valid: false, sid: null };
}

/** 读取学生档案（与 v9 load_data_csv + 按姓名过滤一致） */
export async function getStudentInfo(store: Store, name: string): Promise<Row | null> {
  const rows = await store.readTable(TABLE_STUDENT_INFO);
  const matched = rows.filter((r) => r["姓名"] === name);
  return matched.length > 0 ? { ...matched[0] } : null;
}

export interface SaveInfoResult {
  ok: boolean;
  message: string;
}

/**
 * 保存学生档案（与 v9 「保存全部信息」逻辑一致）：
 * 身份证/手机号校验门 → upsert（按姓名更新或追加）
 */
export async function saveStudentInfo(store: Store, data: Record<string, string>): Promise<SaveInfoResult> {
  const name = data["姓名"] ?? "";
  if (!name) return { ok: false, message: "❌ 缺少姓名" };

  // 保存门校验：与 v9 一致（填了就必须合法）
  const idCardInput = data["身份证号"] ?? "";
  if (idCardInput) {
    const idRes = validateIdCard(idCardInput);
    if (!idRes.valid) return { ok: false, message: "❌ 身份证号码验证未通过，请修正后再保存" };
  }
  const phoneInput = data["手机号"] ?? "";
  if (phoneInput) {
    const pRes = validatePhone(phoneInput);
    if (!pRes.valid) return { ok: false, message: "❌ 手机号码验证未通过，请修正后再保存" };
  }

  const rows = await store.readTable(TABLE_STUDENT_INFO);
  const idx = rows.findIndex((r) => r["姓名"] === name);
  if (idx >= 0) {
    // 更新已有行（只更新存在的列）
    for (const [k, v] of Object.entries(data)) {
      rows[idx][k] = String(v ?? "");
    }
    rows[idx]["最后更新时间"] = data["最后更新时间"] ?? dateTimeStr();
  } else {
    // 追加新行
    rows.push({ ...data });
  }
  await store.writeTable(TABLE_STUDENT_INFO, rows);
  return { ok: true, message: "✅ 所有信息已保存成功！" };
}

export interface StudentScoreView {
  total: number;
  addCount: number;
  subCount: number;
  records: Row[];
}

/** 我的量化分（与 v9 Tab2 一致：当事人包含姓名即匹配） */
export async function getMyScores(store: Store, name: string): Promise<StudentScoreView> {
  const rows = await store.readTable(TABLE_SCORES);
  const mine = rows.filter((r) => (r["当事人"] ?? "").includes(name));
  let total = 0;
  let addCount = 0;
  let subCount = 0;
  const records: Row[] = [];
  for (const r of mine) {
    const add = parseScore(r["加分"]);
    const sub = parseScore(r["扣分"]);
    total += add - sub;
    if (add > 0) addCount++;
    if (sub > 0) subCount++;
    records.push({
      "时间": r["时间"] ?? "",
      "来源": r["信息来源"] ?? "",
      "方向": r["加扣分方向"] ?? "",
      "加分": r["加分"] ?? "",
      "扣分": r["扣分"] ?? "",
      "原由": r["原由"] ?? "",
    });
  }
  return { total, addCount, subCount, records };
}

/** 添加荣誉（与 v9 Tab3 一致） */
export async function addAward(
  store: Store,
  data: { 姓名: string; 学号: string; 奖项名称: string; 奖项级别: string; 获奖时间: string; 备注: string }
): Promise<void> {
  const rows = await store.readTable(TABLE_AWARDS);
  rows.push({
    "姓名": data["姓名"],
    "学号": data["学号"],
    "奖项名称": data["奖项名称"],
    "奖项级别": data["奖项级别"],
    "获奖时间": data["获奖时间"],
    "备注": data["备注"] ?? "",
  });
  await store.writeTable(TABLE_AWARDS, rows);
}

/** 我的荣誉（按姓名过滤） */
export async function getMyAwards(store: Store, name: string): Promise<Row[]> {
  const rows = await store.readTable(TABLE_AWARDS);
  return rows.filter((r) => r["姓名"] === name);
}

export interface ActivityView {
  available: Row[];
  mine: Row[];
}

/** 可报名活动 + 我已报名的活动（与 v9 Tab4 一致） */
export async function getActivities(store: Store, name: string): Promise<ActivityView> {
  const all = await store.readTable(TABLE_ACTIVITIES);
  const myRows = await store.readTable(TABLE_STUDENT_ACTIVITIES);
  const myNames = new Set(myRows.filter((r) => r["姓名"] === name).map((r) => r["活动名称"]));
  const available = all.filter((a) => !myNames.has(a["活动名称"]));
  const mine = myRows.filter((r) => r["姓名"] === name);
  return { available, mine };
}

/** 报名活动（与 v9 一致：追加已报名记录） */
export async function joinActivity(
  store: Store,
  data: { 姓名: string; 学号: string; 活动名称: string }
): Promise<void> {
  const rows = await store.readTable(TABLE_STUDENT_ACTIVITIES);
  rows.push({
    "姓名": data["姓名"],
    "学号": data["学号"],
    "活动名称": data["活动名称"],
    "报名时间": dateTimeShortStr(),
    "参与状态": "已报名",
    "备注": "",
  });
  await store.writeTable(TABLE_STUDENT_ACTIVITIES, rows);
}

/** 我的任务（携带数组下标供更新，与 v9 用 df index 一致） */
export async function getMyTasks(store: Store, name: string): Promise<{ index: number; row: Row }[]> {
  const rows = await store.readTable(TABLE_TASKS);
  const out: { index: number; row: Row }[] = [];
  rows.forEach((r, i) => {
    if (r["姓名"] === name) out.push({ index: i, row: { ...r } });
  });
  return out;
}

/**
 * 更新任务状态（与 v9 一致：按下标更新，完成时记录完成时间）
 * @param index 任务在表中的数组下标
 */
export async function updateTaskStatus(store: Store, index: number, status: string): Promise<boolean> {
  const rows = await store.readTable(TABLE_TASKS);
  if (index < 0 || index >= rows.length) return false;
  rows[index]["完成状态"] = status;
  if (status === "已完成") {
    rows[index]["完成时间"] = dateTimeShortStr();
  }
  await store.writeTable(TABLE_TASKS, rows);
  return true;
}

/** 提交每日反馈（与 v9 Tab6 一致） */
export async function addFeedback(
  store: Store,
  data: { 姓名: string; 学号: string; 心情: string; 学习状态: string; 反馈内容: string }
): Promise<void> {
  const rows = await store.readTable(TABLE_FEEDBACK);
  rows.push({
    "姓名": data["姓名"],
    "学号": data["学号"],
    "心情": data["心情"],
    "学习状态": data["学习状态"],
    "反馈内容": data["反馈内容"] ?? "",
    "日期": todayStr(),
    "时间": timeStr(),
  });
  await store.writeTable(TABLE_FEEDBACK, rows);
}

/** 提交请假（与 v9 Tab7 一致） */
export async function addLeave(
  store: Store,
  data: { 姓名: string; 学号: string; 请假日期: string; 节次: string; 事由: string }
): Promise<void> {
  const rows = await store.readTable(TABLE_LEAVES);
  rows.push({
    "姓名": data["姓名"],
    "学号": data["学号"],
    "请假日期": data["请假日期"],
    "节次": data["节次"],
    "事由": data["事由"] ?? "",
    "申请时间": dateTimeShortStr(),
    "预审状态": "待审批",
    "班主任意见": "",
  });
  await store.writeTable(TABLE_LEAVES, rows);
}

/** 我的请假记录 */
export async function getMyLeaves(store: Store, name: string): Promise<Row[]> {
  const rows = await store.readTable(TABLE_LEAVES);
  return rows.filter((r) => r["姓名"] === name);
}

/** 供教师端使用的数值工具（复用） */
export { toNum };
