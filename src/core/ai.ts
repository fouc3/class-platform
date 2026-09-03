// ========== AI 分析函数（与 v9 一致，暂时关闭） ==========
// v9 中这些函数被硬编码为「功能已关闭」，不调用任何外部 API。

export function callDeepseekApi(_prompt: string, _context: string): string {
  return "【AI功能已关闭】系统管理员已暂时关闭智能评价系统。";
}

export function getStudentFullData(_studentName: string, _studentId: string): string {
  return "【AI功能已关闭】";
}

export function analyzeStudent(_studentName: string, _studentId: string): string {
  return "【AI功能已关闭】";
}

export function analyzeClassAll(
  _dfInfo: unknown,
  _dfAwards: unknown,
  _dfActivities: unknown,
  _dfTasks: unknown,
  _dfFeedback: unknown,
  _dfLeaves: unknown,
  _dfScores: unknown
): string {
  return "【AI功能已关闭】";
}
