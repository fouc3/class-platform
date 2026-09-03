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
