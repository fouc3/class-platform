// ========== 身份证 / 年龄 / 手机号校验逻辑 ==========
// 与 v9 完全一致：18 位校验 + 加权因子 + 校验码表 + 出生日期推算年龄

const WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2];
const CHECK_CODES = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"];

/** 根据身份证计算年龄（与 v9 calculate_age 一致） */
export function calculateAge(idCard: unknown): string {
  if (!idCard || String(idCard).length < 18) return "";
  try {
    const idStr = String(idCard).trim();
    if (idStr.length !== 18) return "";
    const birthStr = idStr.slice(6, 14); // 第7~14位
    const year = parseInt(birthStr.slice(0, 4), 10);
    const month = parseInt(birthStr.slice(4, 6), 10);
    const day = parseInt(birthStr.slice(6, 8), 10);
    const birth = new Date(year, month - 1, day);
    if (isNaN(birth.getTime())) return "";
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    if (
      today.getMonth() + 1 < birth.getMonth() + 1 ||
      (today.getMonth() + 1 === birth.getMonth() + 1 && today.getDate() < birth.getDate())
    ) {
      age -= 1;
    }
    return String(age);
  } catch {
    return "";
  }
}

/** 身份证校验码是否正确（与 v9 加权算法一致） */
export function idCheckCodeValid(idClean: string): boolean {
  let total = 0;
  for (let i = 0; i < 17; i++) {
    total += parseInt(idClean[i], 10) * WEIGHTS[i];
  }
  return CHECK_CODES[total % 11] === idClean[17];
}

/**
 * 身份证完整校验（与 v9 表单实时校验一致）
 * @returns { valid, message, age } message 与 v9 文案一致
 */
export function validateIdCard(raw: string | undefined | null): { valid: boolean; message: string; age: string } {
  if (!raw) {
    return { valid: true, message: "", age: "" };
  }
  const idClean = raw.trim().toUpperCase();
  const len = idClean.length;
  if (len < 18) {
    return { valid: false, message: `⚠️ 当前已输入 ${len} 位，身份证号码需要18位`, age: "" };
  }
  if (len > 18) {
    return { valid: false, message: `⚠️ 当前已输入 ${len} 位，身份证号码只能18位`, age: "" };
  }
  if (!/^\d{17}$/.test(idClean.slice(0, 17))) {
    return { valid: false, message: "❌ 身份证号码前17位必须为数字", age: "" };
  }
  if (!/^[0-9X]$/.test(idClean[17])) {
    return { valid: false, message: "❌ 身份证号码最后一位只能为数字或字母X", age: "" };
  }
  if (!idCheckCodeValid(idClean)) {
    return { valid: false, message: "❌ 身份证号码校验位错误，请核对", age: "" };
  }
  return { valid: true, message: "✅ 身份证号码验证通过", age: calculateAge(idClean) };
}

/**
 * 手机号校验（与 v9 一致）
 * @returns { valid, message } message 与 v9 文案一致
 */
export function validatePhone(raw: string | undefined | null): { valid: boolean; message: string } {
  if (!raw) {
    return { valid: true, message: "" };
  }
  const phone = raw.trim();
  const len = phone.length;
  if (len < 11) {
    return { valid: false, message: `⚠️ 当前已输入 ${len} 位，手机号码需要11位` };
  }
  if (len > 11) {
    return { valid: false, message: `⚠️ 当前已输入 ${len} 位，手机号码只能11位` };
  }
  if (!/^\d+$/.test(phone)) {
    return { valid: false, message: "❌ 手机号码必须为数字" };
  }
  if (phone.startsWith("1") || phone.startsWith("9")) {
    return { valid: true, message: "✅ 手机号码格式正确" };
  }
  return { valid: false, message: "❌ 手机号码格式错误，请以1或9开头" };
}

// ========== 通用字段校验（后端合法性验证） ==========
// 所有表单提交的字段都在这里统一校验，返回错误文案或 null（通过）。

export interface FieldCheckOpts {
  /** 必填（去掉首尾空格后非空） */
  required?: boolean;
  /** 最大长度（含多字节，按字符数） */
  maxLen?: number;
  /** 必须是指定枚举之一 */
  options?: readonly string[];
  /** 逗号分隔的多选值，每一项都必须属于 subsetOf */
  subsetOf?: readonly string[];
  /** 必须是 YYYY-MM-DD 日期 */
  date?: boolean;
  /** 必须是纯数字 */
  digits?: boolean;
  /** 必须是数字（可小数），可配合 min/max */
  number?: boolean;
  min?: number;
  max?: number;
  /** 禁止 CSV 注入前缀（= + - @ 开头） */
  noCsvInject?: boolean;
}

const CSV_INJECT_RE = /^[=+\-@\t\r]/;

export function checkField(label: string, value: string | undefined | null, opts: FieldCheckOpts = {}): string | null {
  const v = String(value ?? "");
  if (opts.required && !v.trim()) return `请填写${label}`;
  const has = v.trim().length > 0;
  if (has && opts.maxLen !== undefined && v.length > opts.maxLen) {
    return `${label}不能超过 ${opts.maxLen} 字`;
  }
  if (has && opts.options && !opts.options.includes(v)) {
    return `${label}取值不合法`;
  }
  if (has && opts.subsetOf) {
    const parts = v.split(",").map((s) => s.trim()).filter(Boolean);
    for (const p of parts) {
      if (!opts.subsetOf.includes(p)) return `${label}包含不合法项：${p}`;
    }
  }
  if (has && opts.date && !/^\d{4}-\d{2}-\d{2}$/.test(v)) {
    return `${label}格式不正确（应为 YYYY-MM-DD）`;
  }
  if (has && opts.digits && !/^\d+$/.test(v)) {
    return `${label}必须为数字`;
  }
  if (has && opts.number) {
    const n = Number(v);
    if (isNaN(n)) return `${label}必须为数字`;
    if (opts.min !== undefined && n < opts.min) return `${label}不能小于 ${opts.min}`;
    if (opts.max !== undefined && n > opts.max) return `${label}不能大于 ${opts.max}`;
  }
  if (has && opts.noCsvInject && CSV_INJECT_RE.test(v)) {
    return `${label}不能以 =、+、-、@ 等字符开头`;
  }
  return null;
}

/** 对任意未知键做长度兜底校验（防止超长字段） */
export function checkTableRow(row: Record<string, string>, maxLen = 20000): string | null {
  for (const [k, v] of Object.entries(row)) {
    if (v.length > maxLen) return `${k}长度不能超过 ${maxLen} 字`;
  }
  return null;
}
