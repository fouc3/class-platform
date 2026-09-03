// ========== API 路由（CF Worker 标准 fetch handler） ==========
import * as XLSX from "xlsx";
import { zipSync, strToU8 } from "fflate";
import type { Store, Row } from "../storage/types.ts";
import { TABLE_SCHEMAS, DATA_TABLES } from "../storage/types.ts";
import { DEFAULT_TEACHER_PASSWORD } from "../config.ts";
import type { SessionStore } from "./session.ts";
import {
  verifyStudent,
  getStudentInfo,
  saveStudentInfo,
  getMyScores,
  addAward,
  getMyAwards,
  getActivities as getStudentActivities,
  joinActivity,
  getMyTasks,
  updateTaskStatus,
  addFeedback,
  addLeave,
  getMyLeaves,
} from "../core/student.ts";
import {
  getStudentList,
  setStudentList,
  addStudent,
  getInfoRows,
  getAwardRows,
  getInfoMetrics,
  csvFromRows,
  getScoreSummary,
  addScoreRecord,
  publishActivity,
  getActivities as getTeacherActivities,
  getAwardMetrics,
  getTasks,
  getFeedback,
  getLeaves,
  approveLeave,
  getAllTableContents,
} from "../core/teacher.ts";
import { validateIdCard, validatePhone } from "../core/validate.ts";
import { todayStr, dateTimeStr } from "../config.ts";

export interface Env {
  store: Store;
  sessions: SessionStore;
  /** 教师密码，由 CF 环境注入（wrangler secret / [vars] / 本地 process.env），未配置时用默认值 */
  TEACHER_PASSWORD?: string;
  /**
   * 学生注册模式（控制登录时未在名单中的名字的行为）
   * 未设置 / "whitelist" → 仅白名单内可登录（v9 原行为，第二模式）
   * "open"             → 任何名字自动加入名单后登录（第一模式）
   * "closed"           → 禁止新增，已有名单内学生可登录（第三模式）
   */
  ALLOW_REGISTRATION?: string;
}

/** 从请求中提取教师 token（或返回 null） */
function getTeacherToken(req: Request): string | null {
  const auth = req.headers.get("Authorization") ?? "";
  const m = auth.match(/^Bearer\s+(.+)$/);
  return m ? m[1] : null;
}

/** 返回 JSON 响应 */
function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

/** 返回错误 */
function error(msg: string, status = 400): Response {
  return json({ error: msg }, status);
}

/** 解析请求 body JSON */
async function parseBody(req: Request): Promise<unknown> {
  try {
    return await req.json();
  } catch {
    return null;
  }
}

// ======== 学生端路由 ========

/** 学生注册模式（默认白名单） */
type RegMode = "whitelist" | "open" | "closed";

function resolveRegMode(env: Env): RegMode {
  const raw = (env.ALLOW_REGISTRATION ?? "").trim().toLowerCase();
  if (raw === "open" || raw === "1" || raw === "true") return "open";
  if (raw === "closed" || raw === "0" || raw === "false") return "closed";
  return "whitelist"; // 未设置默认白名单
}

async function handleStudentLogin(req: Request, env: Env): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, unknown> | null;
  if (!body || typeof body["name"] !== "string") return error("请输入姓名");
  const name = (body["name"] as string).trim();
  if (!name) return json({ valid: false, sid: null, error: "请输入姓名" });
  const mode = resolveRegMode(env);
  // closed 模式：名单内已有学生可登录，禁止新增
  const result = await verifyStudent(env.store, name);
  if (result.valid || mode === "closed") {
    return json(result);
  }
  // 未在名单中
  if (mode === "open") {
    // 开放注册：自动加入名单（学号缺省用姓名，与 v9 verify_student 的 sid 回退一致）
    await addStudent(env.store, name, name);
    return json({ valid: true, sid: name });
  }
  // whitelist 默认：仅白名单内可登录
  return json(result);
}

async function handleStudentInfo(req: Request, store: Store): Promise<Response> {
  const url = new URL(req.url);
  const name = url.searchParams.get("name") ?? "";
  if (!name) return error("缺少 name 参数");
  const row = await getStudentInfo(store, name);
  return json({ row });
}

async function handleStudentInfoSave(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, unknown> | null;
  if (!body) return error("无效请求体");
  // 字符串化所有字段
  const data: Record<string, string> = {};
  for (const [k, v] of Object.entries(body)) {
    data[k] = String(v ?? "");
  }
  // 校验身份证（与 v9 保存门一致）
  const idCard = data["身份证号"] ?? "";
  if (idCard) {
    const idRes = validateIdCard(idCard);
    if (!idRes.valid) return error("❌ 身份证号码验证未通过，请修正后再保存");
  }
  const phone = data["手机号"] ?? "";
  if (phone) {
    const pRes = validatePhone(phone);
    if (!pRes.valid) return error("❌ 手机号码验证未通过，请修正后再保存");
  }
  data["最后更新时间"] = dateTimeStr();
  const result = await saveStudentInfo(store, data);
  return json(result);
}

async function handleStudentScores(req: Request, store: Store): Promise<Response> {
  const name = new URL(req.url).searchParams.get("name") ?? "";
  if (!name) return error("缺少 name");
  const result = await getMyScores(store, name);
  return json(result);
}

async function handleStudentAward(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, string> | null;
  if (!body || !body["姓名"] || !body["奖项名称"]) return error("缺少必要字段");
  await addAward(store, {
    姓名: body["姓名"],
    学号: body["学号"] ?? "",
    奖项名称: body["奖项名称"],
    奖项级别: body["奖项级别"] ?? "班级",
    获奖时间: body["获奖时间"] ?? todayStr(),
    备注: body["备注"] ?? "",
  });
  return json({ ok: true });
}

async function handleStudentAwards(req: Request, store: Store): Promise<Response> {
  const name = new URL(req.url).searchParams.get("name") ?? "";
  if (!name) return error("缺少 name");
  const rows = await getMyAwards(store, name);
  return json({ rows });
}

async function handleStudentActivities(req: Request, store: Store): Promise<Response> {
  const name = new URL(req.url).searchParams.get("name") ?? "";
  if (!name) return error("缺少 name");
  const result = await getStudentActivities(store, name);
  return json(result);
}

async function handleStudentActivityJoin(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, string> | null;
  if (!body || !body["姓名"] || !body["活动名称"]) return error("缺少必要字段");
  await joinActivity(store, {
    姓名: body["姓名"],
    学号: body["学号"] ?? "",
    活动名称: body["活动名称"],
  });
  return json({ ok: true });
}

async function handleStudentTasks(req: Request, store: Store): Promise<Response> {
  const name = new URL(req.url).searchParams.get("name") ?? "";
  if (!name) return error("缺少 name");
  const tasks = await getMyTasks(store, name);
  return json({ tasks });
}

async function handleStudentTaskUpdate(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, unknown> | null;
  if (!body || typeof body["index"] !== "number" || typeof body["status"] !== "string") {
    return error("缺少 index 或 status");
  }
  const ok = await updateTaskStatus(store, body["index"] as number, body["status"] as string);
  return ok ? json({ ok: true }) : error("下标越界");
}

async function handleStudentFeedback(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, string> | null;
  if (!body || !body["姓名"]) return error("缺少姓名");
  await addFeedback(store, {
    姓名: body["姓名"],
    学号: body["学号"] ?? "",
    心情: body["心情"] ?? "😐一般",
    学习状态: body["学习状态"] ?? "正常",
    反馈内容: body["反馈内容"] ?? "",
  });
  return json({ ok: true });
}

async function handleStudentLeave(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, unknown> | null;
  if (!body || !body["姓名"] || !body["请假日期"]) return error("缺少必要字段");
  await addLeave(store, {
    姓名: body["姓名"] as string,
    学号: body["学号"] as string ?? "",
    请假日期: body["请假日期"] as string,
    节次: Array.isArray(body["节次"]) ? (body["节次"] as string[]).join(",") : (body["节次"] as string ?? ""),
    事由: body["事由"] as string ?? "",
  });
  return json({ ok: true });
}

async function handleStudentLeaves(req: Request, store: Store): Promise<Response> {
  const name = new URL(req.url).searchParams.get("name") ?? "";
  if (!name) return error("缺少 name");
  const rows = await getMyLeaves(store, name);
  return json({ rows });
}

// ======== 教师端路由 ========

async function handleTeacherLogin(req: Request, env: Env): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, unknown> | null;
  const pwd = typeof body?.password === "string" ? body.password : "";
  const expected = env.TEACHER_PASSWORD ?? DEFAULT_TEACHER_PASSWORD;
  const token = await env.sessions.create(pwd, expected);
  if (!token) return json({ ok: false }, 401);
  return json({ ok: true, token });
}

async function requireTeacher(req: Request, env: Env): Promise<Response | null> {
  const token = getTeacherToken(req);
  if (!token || !(await env.sessions.verify(token))) {
    return json({ ok: false, error: "未授权" }, 401);
  }
  return null;
}

async function handleTeacherStudents(req: Request, store: Store): Promise<Response> {
  if (req.method === "GET") {
    const rows = await getStudentList(store);
    return json({ rows });
  }
  return error("不支持的方法", 405);
}

async function handleTeacherStudentsUpload(req: Request, store: Store): Promise<Response> {
  try {
    const formData = await req.formData();
    const file = formData.get("file");
    if (!file || !(file instanceof File)) return error("请上传文件");
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(new Uint8Array(buf), { type: "array" });
    const ws = wb.Sheets[wb.SheetNames[0]];
    const rawRows = XLSX.utils.sheet_to_json<Record<string, unknown>>(ws, { defval: "" });
    const rows = rawRows.map((r) => {
      const row: Row = {};
      for (const [k, v] of Object.entries(r)) {
        row[k] = String(v ?? "");
      }
      return row;
    });
    await setStudentList(store, rows);
    return json({ ok: true, count: rows.length });
  } catch (e) {
    return error("文件解析失败: " + (e as Error).message);
  }
}

async function handleTeacherStudentsAdd(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, string> | null;
  if (!body || !body["name"] || !body["sid"]) return error("缺少 name 或 sid");
  await addStudent(store, body["name"], body["sid"]);
  return json({ ok: true });
}

async function handleTeacherInfo(req: Request, store: Store): Promise<Response> {
  const rows = await getInfoRows(store);
  const metrics = getInfoMetrics(rows);
  return json({ metrics, rows });
}

/** 生成 CSV 响应（UTF-8 BOM） */
function csvResponse(csv: string, filename: string): Response {
  const encoder = new TextEncoder();
  const bytes = encoder.encode(csv);
  return new Response(bytes, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename*=UTF-8''${encodeURIComponent(filename)}`,
    },
  });
}

async function handleTeacherInfoExport(req: Request, store: Store): Promise<Response> {
  const rows = await getInfoRows(store);
  const columns = TABLE_SCHEMAS["student_info_new"] ?? Object.keys(rows[0] ?? {});
  const csv = csvFromRows(rows, columns);
  return csvResponse(csv, "学生基本信息.csv");
}

async function handleTeacherScores(req: Request, store: Store): Promise<Response> {
  const url = new URL(req.url);
  const start = url.searchParams.get("start") ?? "";
  const end = url.searchParams.get("end") ?? "";
  const result = await getScoreSummary(store, start, end);
  return json(result);
}

async function handleTeacherScoreAdd(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, unknown> | null;
  if (!body) return error("无效请求体");
  const students = String(body["students"] ?? "").trim();
  const addScore = Number(body["add"] ?? 0);
  const subScore = Number(body["sub"] ?? 0);
  const reason = String(body["reason"] ?? "").trim();
  if (!students || (addScore <= 0 && subScore <= 0) || !reason) {
    return error("请填写完整信息（当事人、分数、原由）");
  }
  await addScoreRecord(store, {
    信息来源: String(body["source"] ?? ""),
    加扣分方向: String(body["direction"] ?? ""),
    上报周期: String(body["period"] ?? "一次性"),
    时间: String(body["date"] ?? todayStr()),
    加分: addScore,
    扣分: subScore,
    当事人: students,
    原由: reason,
    证明材料: String(body["proof"] ?? ""),
  });
  return json({ ok: true });
}

async function handleTeacherActivities(req: Request, store: Store): Promise<Response> {
  const rows = await getTeacherActivities(store);
  return json({ rows });
}

async function handleTeacherActivityPublish(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, string> | null;
  if (!body || !body["name"]) return error("缺少活动名称");
  await publishActivity(store, {
    活动名称: body["name"],
    活动描述: body["desc"] ?? "",
    截止时间: body["deadline"] ?? todayStr(),
    状态: body["status"] ?? "进行中",
  });
  return json({ ok: true });
}

async function handleTeacherAwards(req: Request, store: Store): Promise<Response> {
  const rows = await getAwardRows(store);
  const metrics = getAwardMetrics(rows);
  return json({ metrics, rows });
}

async function handleTeacherTasks(req: Request, store: Store): Promise<Response> {
  const rows = await getTasks(store);
  return json({ rows });
}

async function handleTeacherFeedback(req: Request, store: Store): Promise<Response> {
  const date = new URL(req.url).searchParams.get("date") ?? undefined;
  const result = await getFeedback(store, date);
  return json(result);
}

async function handleTeacherLeaves(req: Request, store: Store): Promise<Response> {
  const leaves = await getLeaves(store);
  return json({ leaves });
}

async function handleTeacherLeaveApprove(req: Request, store: Store): Promise<Response> {
  const body = (await parseBody(req)) as Record<string, unknown> | null;
  if (!body || typeof body["index"] !== "number") return error("缺少 index");
  const ok = await approveLeave(
    store,
    body["index"] as number,
    String(body["status"] ?? "已批准"),
    String(body["comment"] ?? "")
  );
  return ok ? json({ ok: true }) : error("下标越界");
}

async function handleExport(req: Request, store: Store): Promise<Response> {
  const contents = await getAllTableContents(store);
  const files: Record<string, Uint8Array> = {};
  for (const [name, rows] of Object.entries(contents)) {
    files[`${name}.json`] = strToU8(JSON.stringify(rows, null, 2));
  }
  const zip = zipSync(files, { level: 6 });
  const filename = `班级数据_${todayStr().replace(/-/g, "")}_${new Date().toISOString().slice(11, 19).replace(/:/g, "")}.zip`;
  return new Response(zip, {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename*=${encodeURIComponent(filename)}`,
    },
  });
}

// ======== 主路由 ========

export async function handleRequest(req: Request, env: Env): Promise<Response> {
  const url = new URL(req.url);
  const path = url.pathname;

  // ---- 学生端 ----
  if (path === "/api/student/login" && req.method === "POST") return handleStudentLogin(req, env);
  if (path === "/api/student/info" && req.method === "GET") return handleStudentInfo(req, env.store);
  if (path === "/api/student/info/save" && req.method === "POST") return handleStudentInfoSave(req, env.store);
  if (path === "/api/student/scores" && req.method === "GET") return handleStudentScores(req, env.store);
  if (path === "/api/student/award" && req.method === "POST") return handleStudentAward(req, env.store);
  if (path === "/api/student/awards" && req.method === "GET") return handleStudentAwards(req, env.store);
  if (path === "/api/student/activities" && req.method === "GET") return handleStudentActivities(req, env.store);
  if (path === "/api/student/activity/join" && req.method === "POST") return handleStudentActivityJoin(req, env.store);
  if (path === "/api/student/tasks" && req.method === "GET") return handleStudentTasks(req, env.store);
  if (path === "/api/student/task/update" && req.method === "POST") return handleStudentTaskUpdate(req, env.store);
  if (path === "/api/student/feedback" && req.method === "POST") return handleStudentFeedback(req, env.store);
  if (path === "/api/student/leave" && req.method === "POST") return handleStudentLeave(req, env.store);
  if (path === "/api/student/leaves" && req.method === "GET") return handleStudentLeaves(req, env.store);

  // ---- 教师端 ----
  if (path === "/api/teacher/login" && req.method === "POST") return handleTeacherLogin(req, env);
  // 以下接口需要教师 token
  const authErr = await requireTeacher(req, env);
  if (authErr) return authErr;

  if (path === "/api/teacher/students" && req.method === "GET") return handleTeacherStudents(req, env.store);
  if (path === "/api/teacher/students/upload" && req.method === "POST") return handleTeacherStudentsUpload(req, env.store);
  if (path === "/api/teacher/students/add" && req.method === "POST") return handleTeacherStudentsAdd(req, env.store);
  if (path === "/api/teacher/info" && req.method === "GET") return handleTeacherInfo(req, env.store);
  if (path === "/api/teacher/info/export" && req.method === "GET") return handleTeacherInfoExport(req, env.store);
  if (path === "/api/teacher/scores" && req.method === "GET") return handleTeacherScores(req, env.store);
  if (path === "/api/teacher/score" && req.method === "POST") return handleTeacherScoreAdd(req, env.store);
  if (path === "/api/teacher/activities" && req.method === "GET") return handleTeacherActivities(req, env.store);
  if (path === "/api/teacher/activity" && req.method === "POST") return handleTeacherActivityPublish(req, env.store);
  if (path === "/api/teacher/awards" && req.method === "GET") return handleTeacherAwards(req, env.store);
  if (path === "/api/teacher/tasks" && req.method === "GET") return handleTeacherTasks(req, env.store);
  if (path === "/api/teacher/feedback" && req.method === "GET") return handleTeacherFeedback(req, env.store);
  if (path === "/api/teacher/leaves" && req.method === "GET") return handleTeacherLeaves(req, env.store);
  if (path === "/api/teacher/leave/approve" && req.method === "POST") return handleTeacherLeaveApprove(req, env.store);
  if (path === "/api/export" && req.method === "GET") return handleExport(req, env.store);

  return new Response("Not Found", { status: 404 });
}