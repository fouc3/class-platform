// ========== 存储抽象层 ==========
// 业务代码只依赖 Store 接口，不直接触碰 fs / 具体存储实现。
// 后续换存储（Cloudflare KV / D1 / R2 等）只需新增一个实现类。

export type Row = Record<string, string>;

/** 所有数据表统一通过这两个函数读写（表名即文件名，不含扩展名） */
export interface Store {
  /** 读取整张表，返回行数组（每行均为字符串键值对） */
  readTable(name: string): Promise<Row[]>;
  /** 整表覆盖写入 */
  writeTable(name: string, rows: Row[]): Promise<void>;
}

// ---------- 表名常量 ----------
export const TABLE_STUDENT_LIST = "student_list";
export const TABLE_STUDENT_INFO = "student_info_new";
export const TABLE_ACTIVITIES = "activities_published";
export const TABLE_STUDENT_ACTIVITIES = "student_activities";
export const TABLE_AWARDS = "student_awards";
export const TABLE_FEEDBACK = "daily_feedback";
export const TABLE_TASKS = "student_tasks";
export const TABLE_LEAVES = "leaves";
export const TABLE_AI = "ai_analysis";
export const TABLE_SCORES = "score_records";

/** 初始化时保证存在的表及其列结构（与 v9 init_data_files 一致） */
export const TABLE_SCHEMAS: Record<string, string[]> = {
  [TABLE_STUDENT_INFO]: [
    "姓名", "性别", "民族", "特长爱好", "性格特点", "身份证号", "年龄", "手机号",
    "初中毕业学校", "中考总分", "有无初中毕业证", "常住地址", "户籍地址",
    "家庭基本情况", "家庭成员", "家庭教育方法", "兄弟姐妹信息", "是否留守",
    "父母工作情况", "爸爸姓名", "爸爸身份证号", "爸爸联系电话",
    "妈妈姓名", "妈妈身份证号", "妈妈联系电话",
    "其他监护人姓名", "其他监护人和本人关系", "其他监护人身份证号", "其他监护人联系电话",
    "选择专业原因", "未来打算", "曾任职务", "曾患疾病", "现患疾病", "最后更新时间",
  ],
  [TABLE_ACTIVITIES]: ["活动名称", "活动描述", "发布时间", "截止时间", "状态"],
  [TABLE_STUDENT_ACTIVITIES]: ["姓名", "学号", "活动名称", "报名时间", "参与状态", "备注"],
  [TABLE_AWARDS]: ["姓名", "学号", "奖项名称", "奖项级别", "获奖时间", "备注"],
  [TABLE_FEEDBACK]: ["姓名", "学号", "心情", "学习状态", "反馈内容", "日期", "时间"],
  [TABLE_TASKS]: ["姓名", "学号", "任务名称", "完成状态", "完成时间", "备注"],
  [TABLE_LEAVES]: ["姓名", "学号", "请假日期", "节次", "事由", "申请时间", "预审状态", "班主任意见"],
  [TABLE_AI]: ["姓名", "学号", "分析时间", "分析结果"],
  [TABLE_SCORES]: ["信息来源", "加扣分方向", "上报周期", "时间", "加分", "扣分", "当事人", "原由", "证明材料"],
};

/** 需要初始化的数据表（student_list 由上传/seed 生成） */
export const DATA_TABLES = Object.keys(TABLE_SCHEMAS);
