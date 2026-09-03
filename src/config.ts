// ========== 配置与预设选项 ==========
// 与 v9 get_*_options() 函数保持完全一致

/** 默认教师密码（仅当环境未注入 TEACHER_PASSWORD 时使用，与 v9 默认一致） */
export const DEFAULT_TEACHER_PASSWORD = "123456";

// ---------- 预设选项 ----------
export const GENDER_OPTIONS = ["男", "女"];

export const NATION_OPTIONS = [
  "汉族", "蒙古族", "回族", "藏族", "维吾尔族", "苗族", "彝族", "壮族",
  "布依族", "朝鲜族", "满族", "侗族", "瑶族", "白族", "土家族", "哈尼族",
  "哈萨克族", "傣族", "黎族", "傈僳族", "佤族", "畲族", "高山族", "拉祜族",
  "水族", "东乡族", "纳西族", "景颇族", "柯尔克孜族", "土族", "达斡尔族",
  "仫佬族", "羌族", "布朗族", "撒拉族", "毛南族", "仡佬族", "锡伯族",
  "阿昌族", "普米族", "塔吉克族", "怒族", "乌孜别克族", "俄罗斯族",
  "鄂温克族", "德昂族", "保安族", "裕固族", "京族", "塔塔尔族", "独龙族",
  "鄂伦春族", "赫哲族", "门巴族", "珞巴族", "基诺族", "其他",
];

export const FAMILY_TYPE_OPTIONS = [
  "原生家庭完整", "单亲家庭（父母离异）", "单亲家庭（父母一方去世）",
  "后组合家庭", "孤儿（父母去世）",
];

export const FAMILY_MEMBER_OPTIONS = [
  "爸爸", "妈妈", "爷爷", "奶奶", "外公", "外婆",
  "哥哥", "姐姐", "弟弟", "妹妹", "其他",
];

export const SIBLING_TYPES = ["哥哥", "姐姐", "弟弟", "妹妹", "其他"];

export const EDUCATION_METHOD_OPTIONS = [
  "专制粗暴", "民主平等", "漠不关心", "非常宠爱", "无法评价",
];

export const LEAVE_BEHIND_OPTIONS = ["是", "否"];

export const PARENT_WORK_OPTIONS = [
  "爸爸外地工作", "妈妈外地工作", "爸爸妈妈均外地工作",
];

export const FUTURE_PLAN_OPTIONS = ["升学", "就业", "其他"];

export const DISEASE_OPTIONS = [
  "精神分裂", "抑郁症", "焦虑症", "躁郁症", "强迫症", "多动症", "自闭症",
  "肺结核", "乙肝", "艾滋病", "梅毒", "其他性病",
  "癫痫", "心脏病", "哮喘", "糖尿病", "肾炎", "血液病",
  "高度近视", "脊柱侧弯", "骨折史", "脑震荡史",
  "其他重大疾病",
];

export const SCORE_DIRECTION_OPTIONS = ["学习", "纪律", "卫生", "活动", "品德", "其他"];
export const SCORE_SOURCE_OPTIONS = ["班长", "副班长", "学习委员", "文体委员", "卫生防疫员"];
export const SCORE_PERIOD_OPTIONS = ["日", "周", "月", "一次性"];

export const AWARD_LEVEL_OPTIONS = ["班级", "校级", "区级", "市级", "省级", "国家级", "国际级"];

export const TASK_STATUS_OPTIONS = ["未开始", "进行中", "已完成"];

export const FEEDBACK_MOOD_OPTIONS = ["😔很差", "😐一般", "🙂不错", "😄非常好"];
export const FEEDBACK_STUDY_OPTIONS = ["很吃力", "有点吃力", "正常", "良好", "优秀"];

export const LEAVE_PERIOD_OPTIONS = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "全天"];

export const LEAVE_APPROVE_OPTIONS = ["已批准", "已拒绝"];

// ---------- 格式化辅助 ----------
/** 当前日期 YYYY-MM-DD */
export function todayStr(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** 当前时间 HH:MM:SS */
export function timeStr(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
}

/** 当前日期时间 YYYY-MM-DD HH:MM:SS */
export function dateTimeStr(): string {
  return `${todayStr()} ${timeStr()}`;
}

/** 当前日期时间 YYYY-MM-DD HH:MM */
export function dateTimeShortStr(): string {
  const d = new Date();
  return `${todayStr()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** Python 风格浮点数转字符串（0.0→"0.0", 1.5→"1.5"） */
export function pyStr(n: number): string {
  if (Number.isInteger(n)) return `${n.toFixed(1)}`;
  return String(n);
}

/** 安全解析分数，与 v9 replace('.','').isdigit() 逻辑等价 */
export function parseScore(s: string | undefined | null): number {
  if (!s) return 0;
  const cleaned = s.replace(/\./g, "");
  if (cleaned === "" || !/^\d+$/.test(cleaned)) return 0;
  const n = parseFloat(s);
  return isNaN(n) ? 0 : n;
}

/** 解析数字，非数字→0 */
export function toNum(s: string | undefined | null): number {
  const n = parseFloat(s ?? "");
  return isNaN(n) ? 0 : n;
}