/* ========== 班级学生成长平台（TS 版）前端 ==========
 * 完整复刻 v9 的交互逻辑：学生端 7 个 tab + 教师端 8 个 tab
 * 所有数据操作通过 /api/* 调用后端，业务规则与 v9 一致
 */
(function () {
  "use strict";

  // ---------- 会话状态（模拟 v9 的 st.session_state） ----------
  const S = {
    role: "student",
    studentLoggedIn: false,
    studentName: "",
    studentId: "",
    teacherLoggedIn: false,
    teacherToken: "",
    currentStudentTab: "s1",
    currentTeacherTab: "t1",
  };

  // ---------- API 辅助 ----------
  async function api(path, opts = {}) {
    const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
    if (S.teacherToken) headers["Authorization"] = "Bearer " + S.teacherToken;
    const res = await fetch(path, { ...opts, headers });
    let data = null;
    try { data = await res.json(); } catch { /* ignore */ }
    if (!res.ok) throw new Error((data && data.error) || "请求失败(" + res.status + ")");
    return data;
  }

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  // ---------- 工具 ----------
  function h(str) {
    return String(str ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function nowShort() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  function nowTimeHM() {
    const d = new Date();
    return `${nowShort()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }
  function todayStr() { return nowShort(); }

  function esc(s) { return h(s); }

  // ---------- 预设选项（与后端 config.ts 一致） ----------
  const GENDERS = ["男", "女"];
  const NATIONS = ["汉族","蒙古族","回族","藏族","维吾尔族","苗族","彝族","壮族","布依族","朝鲜族","满族","侗族","瑶族","白族","土家族","哈尼族","哈萨克族","傣族","黎族","傈僳族","佤族","畲族","高山族","拉祜族","水族","东乡族","纳西族","景颇族","柯尔克孜族","土族","达斡尔族","仫佬族","羌族","布朗族","撒拉族","毛南族","仡佬族","锡伯族","阿昌族","普米族","塔吉克族","怒族","乌孜别克族","俄罗斯族","鄂温克族","德昂族","保安族","裕固族","京族","塔塔尔族","独龙族","鄂伦春族","赫哲族","门巴族","珞巴族","基诺族","其他"];
  const FAMILY_TYPES = ["原生家庭完整","单亲家庭（父母离异）","单亲家庭（父母一方去世）","后组合家庭","孤儿（父母去世）"];
  const FAMILY_MEMBERS = ["爸爸","妈妈","爷爷","奶奶","外公","外婆","哥哥","姐姐","弟弟","妹妹","其他"];
  const SIBLING_TYPES = ["哥哥","姐姐","弟弟","妹妹","其他"];
  const EDU_METHODS = ["专制粗暴","民主平等","漠不关心","非常宠爱","无法评价"];
  const LEAVE_BEHIND = ["是","否"];
  const PARENT_WORK = ["爸爸外地工作","妈妈外地工作","爸爸妈妈均外地工作"];
  const FUTURE_PLANS = ["升学","就业","其他"];
  const DISEASES = ["精神分裂","抑郁症","焦虑症","躁郁症","强迫症","多动症","自闭症","肺结核","乙肝","艾滋病","梅毒","其他性病","癫痫","心脏病","哮喘","糖尿病","肾炎","血液病","高度近视","脊柱侧弯","骨折史","脑震荡史","其他重大疾病"];
  const SCORE_DIRECTIONS = ["学习","纪律","卫生","活动","品德","其他"];
  const SCORE_SOURCES = ["班长","副班长","学习委员","文体委员","卫生防疫员"];
  const SCORE_PERIODS = ["日","周","月","一次性"];
  const AWARD_LEVELS = ["班级","校级","区级","市级","省级","国家级","国际级"];
  const TASK_STATUS = ["未开始","进行中","已完成"];
  const FEEDBACK_MOODS = ["😔很差","😐一般","🙂不错","😄非常好"];
  const FEEDBACK_STUDY = ["很吃力","有点吃力","正常","良好","优秀"];
  const LEAVE_PERIODS = ["第1节","第2节","第3节","第4节","第5节","第6节","全天"];
  const LEAVE_APPROVE = ["已批准","已拒绝"];

  // ---------- 身份证 / 手机号校验（与后端一致） ----------
  const WEIGHTS = [7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2];
  const CHECK_CODES = ["1","0","X","9","8","7","6","5","4","3","2"];

  function validateIdCard(raw) {
    if (!raw) return { valid: true, message: "", age: "" };
    const id = raw.trim().toUpperCase();
    const len = id.length;
    if (len < 18) return { valid: false, message: `⚠️ 当前已输入 ${len} 位，身份证号码需要18位`, age: "" };
    if (len > 18) return { valid: false, message: `⚠️ 当前已输入 ${len} 位，身份证号码只能18位`, age: "" };
    if (!/^\d{17}$/.test(id.slice(0, 17))) return { valid: false, message: "❌ 身份证号码前17位必须为数字", age: "" };
    if (!/^[0-9X]$/.test(id[17])) return { valid: false, message: "❌ 身份证号码最后一位只能为数字或字母X", age: "" };
    let total = 0;
    for (let i = 0; i < 17; i++) total += parseInt(id[i], 10) * WEIGHTS[i];
    if (CHECK_CODES[total % 11] !== id[17]) return { valid: false, message: "❌ 身份证号码校验位错误，请核对", age: "" };
    return { valid: true, message: "✅ 身份证号码验证通过", age: calcAge(id) };
  }

  function calcAge(idStr) {
    try {
      const birthStr = idStr.slice(6, 14);
      const year = parseInt(birthStr.slice(0, 4), 10);
      const month = parseInt(birthStr.slice(4, 6), 10);
      const day = parseInt(birthStr.slice(6, 8), 10);
      const now = new Date();
      let age = now.getFullYear() - year;
      if (now.getMonth() + 1 < month || (now.getMonth() + 1 === month && now.getDate() < day)) age -= 1;
      return String(age);
    } catch { return ""; }
  }

  function validatePhone(raw) {
    if (!raw) return { valid: true, message: "" };
    const p = raw.trim();
    const len = p.length;
    if (len < 11) return { valid: false, message: `⚠️ 当前已输入 ${len} 位，手机号码需要11位` };
    if (len > 11) return { valid: false, message: `⚠️ 当前已输入 ${len} 位，手机号码只能11位` };
    if (!/^\d+$/.test(p)) return { valid: false, message: "❌ 手机号码必须为数字" };
    if (p.startsWith("1") || p.startsWith("9")) return { valid: true, message: "✅ 手机号码格式正确" };
    return { valid: false, message: "❌ 手机号码格式错误，请以1或9开头" };
  }

  // ============================================================
  //  视图切换
  // ============================================================
  function switchRole(role) {
    S.role = role;
    $("#student-view").classList.toggle("hidden", role !== "student");
    $("#teacher-view").classList.toggle("hidden", role !== "teacher");
    if (role === "student") renderStudentView();
    else renderTeacherView();
  }

  // ============================================================
  //  学生端
  // ============================================================
  async function studentLogin() {
    const input = $("#login-name");
    const name = input.value.trim();
    const msg = $("#login-msg");
    if (!name) { msg.className = "msg warning"; msg.textContent = "请输入姓名"; return; }
    try {
      const res = await api("/api/student/login", { method: "POST", body: JSON.stringify({ name }) });
      if (res.valid) {
        S.studentLoggedIn = true;
        S.studentName = name;
        S.studentId = res.sid;
        saveSession();
        renderStudentView();
      } else {
        msg.className = "msg error";
        msg.textContent = "验证失败：你不在本班学生名单中";
      }
    } catch (e) { msg.className = "msg error"; msg.textContent = e.message; }
  }

  function studentLogout() {
    S.studentLoggedIn = false;
    S.studentName = "";
    S.studentId = "";
    saveSession();
    renderStudentView();
  }

  function renderStudentView() {
    $("#student-login").classList.toggle("hidden", S.studentLoggedIn);
    $("#student-portal").classList.toggle("hidden", !S.studentLoggedIn);
    if (S.studentLoggedIn) {
      $("#student-welcome").textContent = `欢迎 ${S.studentName} 同学`;
      activateTab("student", S.currentStudentTab);
    } else {
      $("#login-name").value = "";
      $("#login-msg").textContent = "";
    }
  }

  function renderTeacherView() {
    $("#teacher-login").classList.toggle("hidden", S.teacherLoggedIn);
    $("#teacher-portal").classList.toggle("hidden", !S.teacherLoggedIn);
    if (S.teacherLoggedIn) {
      activateTab("teacher", S.currentTeacherTab);
    } else {
      $("#teacher-pwd").value = "";
      $("#teacher-login-msg").textContent = "";
    }
  }

  async function teacherLogin() {
    const pwd = $("#teacher-pwd").value;
    const msg = $("#teacher-login-msg");
    try {
      const res = await api("/api/teacher/login", { method: "POST", body: JSON.stringify({ password: pwd }) });
      if (res.ok) {
        S.teacherLoggedIn = true;
        S.teacherToken = res.token;
        saveSession();
        renderTeacherView();
      } else {
        msg.className = "msg error";
        msg.textContent = "密码错误";
      }
    } catch (e) { msg.className = "msg error"; msg.textContent = e.message; }
  }

  function teacherLogout() {
    S.teacherLoggedIn = false;
    S.teacherToken = "";
    saveSession();
    renderTeacherView();
  }

  // ---------- Tab 切换 ----------
  function activateTab(role, tabId) {
    if (role === "student") {
      S.currentStudentTab = tabId;
      $$("#student-tabs .tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tabId));
      $$("#student-portal .tab-content").forEach((c) => c.classList.toggle("active", c.id === tabId));
      renderStudentTab(tabId);
    } else {
      S.currentTeacherTab = tabId;
      $$("#teacher-tabs .tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tabId));
      $$("#teacher-portal .tab-content").forEach((c) => c.classList.toggle("active", c.id === tabId));
      renderTeacherTab(tabId);
    }
  }

  const studentTabRenderers = {
    s1: renderInfoTab, s2: renderScoreTab, s3: renderAwardTab, s4: renderActivityTab,
    s5: renderTaskTab, s6: renderFeedbackTab, s7: renderLeaveTab,
  };
  const teacherTabRenderers = {
    t1: renderStudentListTab, t2: renderTeacherInfoTab, t3: renderScoreManageTab,
    t4: renderActivityManageTab, t5: renderAwardManageTab, t6: renderTaskFeedbackTab,
    t7: renderLeaveApproveTab, t8: renderExportTab,
  };

  function renderStudentTab(id) { studentTabRenderers[id] && studentTabRenderers[id](); }
  function renderTeacherTab(id) { teacherTabRenderers[id] && teacherTabRenderers[id](); }

  // ---------- 通用小组件 ----------
  function radioGroup(name, options, selected) {
    return options.map((opt) => `
      <label style="margin-right:16px;cursor:pointer">
        <input type="radio" name="${name}" value="${esc(opt)}" ${opt === selected ? "checked" : ""}> ${esc(opt)}
      </label>`).join("");
  }

  function checkboxGroup(name, options, selected) {
    const sel = new Set(selected || []);
    return options.map((opt) => `
      <label style="margin-right:14px;cursor:pointer;display:inline-block">
        <input type="checkbox" name="${name}" value="${esc(opt)}" ${sel.has(opt) ? "checked" : ""}> ${esc(opt)}
      </label>`).join("");
  }

  function checkedValues(name, root) {
    return $$(`input[name="${name}"]:checked`, root).map((i) => i.value);
  }

  function field(label, innerHtml, hint) {
    return `<div class="field"><label>${label}${hint ? ` <span class="optional">${hint}</span>` : ""}</label>${innerHtml}</div>`;
  }

  function tableHtml(headers, rows) {
    if (!rows || rows.length === 0) return `<div class="info-box">暂无数据</div>`;
    return `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  function msgBox(kind, text) {
    return `<div class="msg ${kind}">${esc(text)}</div>`;
  }

  // ============================================================
  //  Tab1 学生基本信息
  // ============================================================
  async function renderInfoTab() {
    const el = $("#s1");
    const name = S.studentName;
    let existing = {};
    try {
      const res = await api(`/api/student/info?name=${encodeURIComponent(name)}`);
      if (res.row) existing = res.row;
    } catch { /* ignore */ }

    const genderSel = (existing["性别"] && GENDERS.includes(existing["性别"])) ? existing["性别"] : "男";
    const nationSel = (existing["民族"] && NATIONS.includes(existing["民族"])) ? existing["民族"] : "汉族";
    const certSel = existing["有无初中毕业证"] === "无" ? "无" : "有";
    const familyTypeSel = (existing["家庭基本情况"] && FAMILY_TYPES.includes(existing["家庭基本情况"])) ? existing["家庭基本情况"] : "原生家庭完整";
    const members = existing["家庭成员"] ? existing["家庭成员"].split(",") : [];
    const eduMethods = existing["家庭教育方法"] ? existing["家庭教育方法"].split(",") : [];
    const leaveSel = existing["是否留守"] === "是" ? "是" : "否";
    const parentWorkSel = (existing["父母工作情况"] && PARENT_WORK.includes(existing["父母工作情况"])) ? existing["父母工作情况"] : "爸爸外地工作";
    const futureSel = (existing["未来打算"] && FUTURE_PLANS.includes(existing["未来打算"])) ? existing["未来打算"] : "升学";
    const pastDiseases = existing["曾患疾病"] ? existing["曾患疾病"].split(",") : [];
    const nowDiseases = existing["现患疾病"] ? existing["现患疾病"].split(",") : [];

    const hasSiblings = SIBLING_TYPES.some((m) => members.includes(m));
    const hasFatherMother = members.includes("爸爸") || members.includes("妈妈");
    const hasFather = members.includes("爸爸");
    const hasMother = members.includes("妈妈");
    const hasOther = members.some((m) => !["爸爸", "妈妈"].includes(m));

    el.innerHTML = `
      <div class="info-box">请认真填写以下信息，所有信息仅班主任可见，严格保密</div>
      <div class="form-section">📌 基本信息</div>
      <div class="form-grid">
        ${field("1. 姓名", `<input type="text" value="${esc(name)}" disabled>`)}
        ${field("2. 性别", `<select id="f2_gender">${GENDERS.map((g) => `<option ${g === genderSel ? "selected" : ""}>${g}</option>`).join("")}</select>`)}
        ${field("3. 民族", `<select id="f3_nation">${NATIONS.map((n) => `<option ${n === nationSel ? "selected" : ""}>${n}</option>`).join("")}</select>`)}
        ${field("4. 特长或爱好", `<input type="text" id="f4_hobby" value="${esc(existing["特长爱好"] || "")}">`)}
        ${field("5. 性格特点", `<input type="text" id="f5_personality" value="${esc(existing["性格特点"] || "")}">`)}
        ${field("6. 身份证号码", `<input type="text" id="f6_idcard" value="${esc(existing["身份证号"] || "")}" placeholder="请输入18位身份证号码（最后一位可能是数字或X）" autocomplete="off">
          <div class="caption" id="f6_msg"></div>`)}
        ${field("7. 年龄（自动计算）", `<input type="text" id="f7_age" value="${esc(existing["年龄"] || "")}" disabled>`)}
        ${field("8. 手机号码", `<input type="text" id="f8_phone" value="${esc(existing["手机号"] || "")}" placeholder="请输入11位手机号码" autocomplete="off">
          <div class="caption" id="f8_msg"></div>`)}
        ${field("9. 初中毕业学校", `<input type="text" id="f9_middle" value="${esc(existing["初中毕业学校"] || "")}">`)}
        ${field("10. 中考总分", `<input type="text" id="f10_exam" value="${esc(existing["中考总分"] || "")}">`)}
        ${field("11. 有无初中毕业证", `<select id="f11_cert">${["有", "无"].map((c) => `<option ${c === certSel ? "selected" : ""}>${c}</option>`).join("")}</select>`)}
      </div>
      ${field("12. 常住地址", `<textarea id="f12_address" height="68">${esc(existing["常住地址"] || "")}</textarea>`)}
      ${field("13. 户籍地址（身份证或户口本地址）", `<textarea id="f13_hometown" height="68">${esc(existing["户籍地址"] || "")}</textarea>`)}

      <div class="form-section">👨‍👩‍👧‍👦 家庭情况</div>
      ${field("14. 家庭基本情况", `<div>${radioGroup("f14_family_type", FAMILY_TYPES, familyTypeSel)}</div>`)}
      <div class="caption">💡 请在下拉框中选择家庭成员（可多选）</div>
      ${field("15. 家庭成员", `<div id="f15_members">${checkboxGroup("f15_member", FAMILY_MEMBERS, members)}</div>`)}
      <div class="caption">💡 请在下拉框中选择家庭教育方法（可多选）</div>
      ${field("16. 家庭教育方法", `<div id="f16_methods">${checkboxGroup("f16_edu", EDU_METHODS, eduMethods)}</div>`)}
      ${field("17. 兄弟姐妹信息（姓名|关系|年龄，多条用逗号分隔）",
        `<input type="text" id="f17_sibling" value="${esc(existing["兄弟姐妹信息"] || (hasSiblings ? "" : "无兄弟姐妹"))}" placeholder="例如：张三|哥哥|18,李四|妹妹|15">
         <div class="caption" id="f17_hint"></div>`, hasSiblings ? "" : "未选择兄弟姐妹，此项不可编辑")}
      ${field("18. 是否留守", `<div>${radioGroup("f18_leave", LEAVE_BEHIND, leaveSel)}</div>`)}
      ${field("19. 父母工作情况", `<select id="f19_parent_work">${PARENT_WORK.map((p) => `<option ${p === parentWorkSel ? "selected" : ""}>${p}</option>`).join("")}</select>
         <div class="caption" id="f19_hint"></div>`)}
      </div>

      <div class="form-section">📞 监护人信息</div>
      <div class="form-grid">
        ${field("20. 爸爸姓名", `<input type="text" id="f20_dad_name" value="${esc(existing["爸爸姓名"] || "")}">`)}
        ${field("21. 爸爸身份证号码", `<input type="text" id="f21_dad_id" value="${esc(existing["爸爸身份证号"] || "")}">`)}
        ${field("22. 爸爸常用联系电话", `<input type="text" id="f22_dad_phone" value="${esc(existing["爸爸联系电话"] || "")}">`)}
        ${field("23. 妈妈姓名", `<input type="text" id="f23_mom_name" value="${esc(existing["妈妈姓名"] || "")}">`)}
        ${field("24. 妈妈身份证号码", `<input type="text" id="f24_mom_id" value="${esc(existing["妈妈身份证号"] || "")}">`)}
        ${field("25. 妈妈常用联系电话", `<input type="text" id="f25_mom_phone" value="${esc(existing["妈妈联系电话"] || "")}">`)}
        ${field("26. 其他监护人姓名", `<input type="text" id="f26_other_name" value="${esc(existing["其他监护人姓名"] || "")}">`)}
        ${field("27. 其他监护人和本人关系", `<input type="text" id="f27_other_relation" value="${esc(existing["其他监护人和本人关系"] || "")}">`)}
        ${field("28. 其他监护人身份证号码", `<input type="text" id="f28_other_id" value="${esc(existing["其他监护人身份证号"] || "")}">`)}
        ${field("29. 其他监护人联系电话", `<input type="text" id="f29_other_phone" value="${esc(existing["其他监护人联系电话"] || "")}">`)}
      </div>

      <div class="form-section">🎯 个人发展</div>
      ${field("30. 选择农村电气技术（计算机方向）专业的原因", `<textarea id="f30_reason" height="68">${esc(existing["选择专业原因"] || "")}</textarea>`)}
      ${field("31. 你对未来的打算", `<div>${radioGroup("f31_future", FUTURE_PLANS, futureSel)}</div>`)}
      ${field("32. 曾在班上担任什么职务", `<input type="text" id="f32_position" value="${esc(existing["曾任职务"] || "")}">`)}
      <div class="caption">💡 请在下拉框中选择曾患疾病（可多选）</div>
      <div class="warn-box">⚠️ 重要提醒：如有隐瞒，后果自负！</div>
      ${field("33. 曾经是否患过什么大病", `<div>${checkboxGroup("f33_past", DISEASES, pastDiseases)}</div>`)}
      <div class="caption">💡 请在下拉框中选择现患疾病（可多选）</div>
      <div class="warn-box">⚠️ 重要提醒：如有隐瞒，后果自负！</div>
      ${field("34. 现在是否患过什么大病", `<div>${checkboxGroup("f34_now", DISEASES, nowDiseases)}</div>`)}

      <div style="margin-top:20px">
        <button class="btn primary" id="save_info_btn">💾 保存全部信息</button>
        <div class="msg" id="save_info_msg"></div>
      </div>
      ${existing && existing["姓名"] ? `<div class="info-box">📌 已保存的基本信息可以在此修改，修改后点击保存即可更新。</div>` : ""}
    `;

    // ---------- 身份证实时校验 ----------
    const idInput = $("#f6_idcard", el);
    const idMsg = $("#f6_msg", el);
    function updateAge() {
      const res = validateIdCard(idInput.value);
      if (res.age) $("#f7_age", el).value = res.age;
    }
    function renderIdMsg() {
      const v = idInput.value.trim();
      if (!v) { idMsg.textContent = "💡 请填写18位身份证号码，填写后自动计算年龄"; idMsg.className = "caption"; return; }
      const res = validateIdCard(v);
      idMsg.textContent = res.message;
      idMsg.className = res.valid ? "msg success" : "msg error";
      if (res.valid) $("#f7_age", el).value = res.age;
    }
    idInput.addEventListener("input", () => { updateAge(); renderIdMsg(); });

    // ---------- 手机号实时校验 ----------
    const phoneInput = $("#f8_phone", el);
    const phoneMsg = $("#f8_msg", el);
    function renderPhoneMsg() {
      const v = phoneInput.value.trim();
      if (!v) { phoneMsg.textContent = "💡 请填写11位手机号码"; phoneMsg.className = "caption"; return; }
      const res = validatePhone(v);
      phoneMsg.textContent = res.message;
      phoneMsg.className = res.valid ? "msg success" : "msg error";
    }
    phoneInput.addEventListener("input", renderPhoneMsg);

    // ---------- 家庭成员联动 ----------
    function currentMembers() {
      return checkedValues("f15_member", el);
    }
    function updateConditional() {
      const members = currentMembers();
      const hasSib = SIBLING_TYPES.some((m) => members.includes(m));
      const hasFm = members.includes("爸爸") || members.includes("妈妈");
      const hasF = members.includes("爸爸");
      const hasM = members.includes("妈妈");
      const hasO = members.some((m) => !["爸爸", "妈妈"].includes(m));
      const leave = $('input[name="f18_leave"]:checked', el)?.value || "否";

      // 兄弟姐妹信息
      const sibInput = $("#f17_sibling", el);
      if (!hasSib) {
        sibInput.disabled = true;
        sibInput.value = "无兄弟姐妹";
        $("#f17_hint", el).textContent = "💡 未选择兄弟姐妹，此项不可编辑";
      } else {
        sibInput.disabled = false;
        if (sibInput.value === "无兄弟姐妹") sibInput.value = "";
        $("#f17_hint", el).textContent = "";
      }
      // 父母工作情况
      const pw = $("#f19_parent_work", el);
      const pwHint = $("#f19_hint", el);
      if (leave === "是" && hasFm) {
        pw.disabled = false;
        pwHint.textContent = "";
      } else if (leave === "是" && !hasFm) {
        pw.disabled = true;
        pwHint.textContent = "⚠️ 您选择了留守，但家庭成员中未选择爸爸或妈妈";
      } else {
        pw.disabled = true;
        pwHint.textContent = "未选择留守，此项不可编辑";
      }
      // 爸爸/妈妈/其他监护人
      toggleEnabled("#f20_dad_name", hasF, "未选择爸爸", el);
      toggleEnabled("#f21_dad_id", hasF, "未选择爸爸", el);
      toggleEnabled("#f22_dad_phone", hasF, "未选择爸爸", el);
      toggleEnabled("#f23_mom_name", hasM, "未选择妈妈", el);
      toggleEnabled("#f24_mom_id", hasM, "未选择妈妈", el);
      toggleEnabled("#f25_mom_phone", hasM, "未选择妈妈", el);
      toggleEnabled("#f26_other_name", hasO, "无其他监护人", el);
      toggleEnabled("#f27_other_relation", hasO, "无其他监护人", el);
      toggleEnabled("#f28_other_id", hasO, "无其他监护人", el);
      toggleEnabled("#f29_other_phone", hasO, "无其他监护人", el);
    }
    function toggleEnabled(sel, enabled, placeholder, root) {
      const input = $(sel, root);
      if (!input) return;
      input.disabled = !enabled;
      if (!enabled && !input.value) input.value = placeholder;
    }
    $("#f15_members", el).addEventListener("change", updateConditional);
    $$('input[name="f18_leave"]', el).forEach((i) => i.addEventListener("change", updateConditional));
    updateConditional();

    // ---------- 保存 ----------
    $("#save_info_btn", el).addEventListener("click", async () => {
      const msgEl = $("#save_info_msg", el);
      const idVal = idInput.value.trim();
      const phoneVal = phoneInput.value.trim();
      if (idVal && !validateIdCard(idVal).valid) {
        msgEl.className = "msg error";
        msgEl.textContent = "❌ 身份证号码验证未通过，请修正后再保存";
        return;
      }
      if (phoneVal && !validatePhone(phoneVal).valid) {
        msgEl.className = "msg error";
        msgEl.textContent = "❌ 手机号码验证未通过，请修正后再保存";
        return;
      }
      const members = currentMembers();
      const hasSib = SIBLING_TYPES.some((m) => members.includes(m));
      const hasFm = members.includes("爸爸") || members.includes("妈妈");
      const hasF = members.includes("爸爸");
      const hasM = members.includes("妈妈");
      const hasO = members.some((m) => !["爸爸", "妈妈"].includes(m));
      const leave = $('input[name="f18_leave"]:checked', el)?.value || "否";

      const data = {
        "姓名": name,
        "性别": $("#f2_gender", el).value,
        "民族": $("#f3_nation", el).value,
        "特长爱好": $("#f4_hobby", el).value,
        "性格特点": $("#f5_personality", el).value,
        "身份证号": idVal,
        "年龄": $("#f7_age", el).value,
        "手机号": phoneVal,
        "初中毕业学校": $("#f9_middle", el).value,
        "中考总分": $("#f10_exam", el).value,
        "有无初中毕业证": $("#f11_cert", el).value,
        "常住地址": $("#f12_address", el).value,
        "户籍地址": $("#f13_hometown", el).value,
        "家庭基本情况": $('input[name="f14_family_type"]:checked', el)?.value || "",
        "家庭成员": members.join(","),
        "家庭教育方法": checkedValues("f16_edu", el).join(","),
        "兄弟姐妹信息": hasSib ? $("#f17_sibling", el).value : "无兄弟姐妹",
        "是否留守": leave,
        "父母工作情况": leave === "是" && hasFm ? $("#f19_parent_work", el).value : "",
        "爸爸姓名": hasF ? $("#f20_dad_name", el).value : "",
        "爸爸身份证号": hasF ? $("#f21_dad_id", el).value : "",
        "爸爸联系电话": hasF ? $("#f22_dad_phone", el).value : "",
        "妈妈姓名": hasM ? $("#f23_mom_name", el).value : "",
        "妈妈身份证号": hasM ? $("#f24_mom_id", el).value : "",
        "妈妈联系电话": hasM ? $("#f25_mom_phone", el).value : "",
        "其他监护人姓名": hasO ? $("#f26_other_name", el).value : "",
        "其他监护人和本人关系": hasO ? $("#f27_other_relation", el).value : "",
        "其他监护人身份证号": hasO ? $("#f28_other_id", el).value : "",
        "其他监护人联系电话": hasO ? $("#f29_other_phone", el).value : "",
        "选择专业原因": $("#f30_reason", el).value,
        "未来打算": $('input[name="f31_future"]:checked', el)?.value || "",
        "曾任职务": $("#f32_position", el).value,
        "曾患疾病": checkedValues("f33_past", el).join(","),
        "现患疾病": checkedValues("f34_now", el).join(","),
      };
      try {
        const res = await api("/api/student/info/save", { method: "POST", body: JSON.stringify(data) });
        msgEl.className = "msg success";
        msgEl.textContent = res.message || "✅ 所有信息已保存成功！";
        // 表单已是最新数据，保持显示；重新加载会丢失消息
      } catch (e) {
        msgEl.className = "msg error";
        msgEl.textContent = e.message;
      }
    });
  }

  // ============================================================
  //  Tab2 我的量化分
  // ============================================================
  async function renderScoreTab() {
    const el = $("#s2");
    el.innerHTML = `<div class="caption">加载中...</div>`;
    try {
      const res = await api(`/api/student/scores?name=${encodeURIComponent(S.studentName)}`);
      const total = res.total.toFixed(1);
      el.innerHTML = `
        <h3>📊 我的量化管理分</h3>
        <div class="metrics">
          <div class="metric-card"><div class="metric-value">${total}</div><div class="metric-label">当前总分</div></div>
          <div class="metric-card"><div class="metric-value">${res.addCount}</div><div class="metric-label">加分总次数</div></div>
          <div class="metric-card"><div class="metric-value">${res.subCount}</div><div class="metric-label">扣分总次数</div></div>
        </div>
        <h3>📋 详细记录</h3>
        ${tableHtml(["时间", "来源", "方向", "加分", "扣分", "原由"], res.records.map((r) => [r["时间"], r["来源"], r["方向"], r["加分"], r["扣分"], r["原由"]]))}
      `;
    } catch (e) {
      el.innerHTML = msgBox("error", e.message);
    }
  }

  // ============================================================
  //  Tab3 我的荣誉
  // ============================================================
  async function renderAwardTab() {
    const el = $("#s3");
    el.innerHTML = `
      <h3>🏆 我的荣誉墙</h3>
      <form id="award_form" class="panel" style="max-width:none;margin:0 0 16px">
        <div class="form-grid">
          ${field("荣誉/奖项名称", `<input type="text" id="award_name" required>`)}
          ${field("荣誉级别", `<select id="award_level">${AWARD_LEVELS.map((l) => `<option>${l}</option>`).join("")}</select>`)}
          ${field("获奖日期", `<input type="date" id="award_date" value="${todayStr()}">`)}
          ${field("备注（可选）", `<input type="text" id="award_remark">`)}
        </div>
        <button class="btn primary" type="submit">➕ 添加荣誉</button>
        <div class="msg" id="award_msg"></div>
      </form>
      <h3>📋 我的荣誉记录</h3>
      <div id="my_awards"></div>
    `;
    $("#award_form", el).addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = $("#award_name", el).value.trim();
      if (!name) return;
      const msg = $("#award_msg", el);
      try {
        await api("/api/student/award", {
          method: "POST",
          body: JSON.stringify({
            姓名: S.studentName, 学号: S.studentId, 奖项名称: name,
            奖项级别: $("#award_level", el).value,
            获奖时间: $("#award_date", el).value,
            备注: $("#award_remark", el).value,
          }),
        });
        msg.className = "msg success";
        msg.textContent = `已添加：${name}`;
        // 不刷新 tab，保持消息可见
      } catch (err) { msg.className = "msg error"; msg.textContent = err.message; }
    });
    try {
      const res = await api(`/api/student/awards?name=${encodeURIComponent(S.studentName)}`);
      $("#my_awards", el).innerHTML = tableHtml(
        ["奖项名称", "奖项级别", "获奖时间", "备注"],
        res.rows.map((r) => [r["奖项名称"], r["奖项级别"], r["获奖时间"], r["备注"]])
      );
    } catch (e) {
      $("#my_awards", el).innerHTML = msgBox("error", e.message);
    }
  }

  // ============================================================
  //  Tab4 参加活动
  // ============================================================
  async function renderActivityTab() {
    const el = $("#s4");
    el.innerHTML = `<div class="caption">加载中...</div>`;
    try {
      const res = await api(`/api/student/activities?name=${encodeURIComponent(S.studentName)}`);
      let html = `<h3>📋 可报名的活动</h3>`;
      if (res.available.length === 0) {
        html += `<div class="info-box">暂无可报名的活动</div>`;
      } else {
        res.available.forEach((a, i) => {
          html += `
            <div class="activity-row">
              <div style="flex:1">
                <div class="act-name">${esc(a["活动名称"])}</div>
                <div class="act-desc">${esc(a["活动描述"] || "")}</div>
              </div>
              <div class="act-meta">截止：${esc(a["截止时间"] || "无")}</div>
              <div class="act-action"><button class="btn primary" data-join="${i}">报名</button></div>
            </div>`;
        });
      }
      html += `<details class="expander" open>
        <summary>📋 我已报名的活动</summary>
        <div class="expander-body">
          ${res.mine.length === 0 ? `<div class="info-box">暂无已报名活动</div>` :
            tableHtml(["活动名称", "报名时间", "参与状态"], res.mine.map((r) => [r["活动名称"], r["报名时间"], r["参与状态"]]))}
        </div>
      </details>`;
      el.innerHTML = html;
      $$("[data-join]", el).forEach((btn) => {
        btn.addEventListener("click", async () => {
          const act = res.available[parseInt(btn.dataset.join, 10)];
          try {
            await api("/api/student/activity/join", {
              method: "POST",
              body: JSON.stringify({ 姓名: S.studentName, 学号: S.studentId, 活动名称: act["活动名称"] }),
            });
            renderActivityTab();
          } catch (e) { alert(e.message); }
        });
      });
    } catch (e) {
      el.innerHTML = msgBox("error", e.message);
    }
  }

  // ============================================================
  //  Tab5 我的任务
  // ============================================================
  async function renderTaskTab() {
    const el = $("#s5");
    el.innerHTML = `<div class="caption">加载中...</div>`;
    try {
      const res = await api(`/api/student/tasks?name=${encodeURIComponent(S.studentName)}`);
      let html = `<h3>✅ 我的任务</h3>`;
      if (res.tasks.length === 0) {
        html += `<div class="info-box">暂无任务安排</div>`;
      } else {
        res.tasks.forEach(({ index, row }) => {
          const current = row["完成状态"];
          const selOpts = TASK_STATUS.map((s) => `<option ${s === current ? "selected" : ""}>${s}</option>`).join("");
          html += `
            <div class="task-row" data-idx="${index}">
              <div style="flex:1">
                <div class="task-name">📌 ${esc(row["任务名称"])}</div>
                <div class="task-note">${esc(row["备注"] || "")}</div>
              </div>
              <div class="task-action">
                <select data-status>${selOpts}</select>
                <button class="btn" data-update>更新</button>
              </div>
            </div>`;
        });
      }
      el.innerHTML = html;
      $$("[data-update]", el).forEach((btn) => {
        btn.addEventListener("click", async () => {
          const rowEl = btn.closest(".task-row");
          const index = parseInt(rowEl.dataset.idx, 10);
          const status = $("[data-status]", rowEl).value;
          try {
            await api("/api/student/task/update", { method: "POST", body: JSON.stringify({ index, status }) });
            renderTaskTab();
          } catch (e) { alert(e.message); }
        });
      });
    } catch (e) {
      el.innerHTML = msgBox("error", e.message);
    }
  }

  // ============================================================
  //  Tab6 每日反馈
  // ============================================================
  async function renderFeedbackTab() {
    const el = $("#s6");
    el.innerHTML = `
      <h3>📝 每日反馈</h3>
      <form id="feedback_form" class="panel" style="max-width:none;margin:0">
        ${field("今天心情", `<div style="display:flex;gap:6px;flex-wrap:wrap">${FEEDBACK_MOODS.map((m, i) =>
          `<label style="cursor:pointer;padding:6px 12px;border:1px solid var(--border);border-radius:20px" class="mood-opt">
            <input type="radio" name="mood" value="${esc(m)}" ${i === 0 ? "checked" : ""} style="display:none"> ${esc(m)}
          </label>`).join("")}</div>`)}
        ${field("学习状态", `<select id="fb_study">${FEEDBACK_STUDY.map((s) => `<option>${s}</option>`).join("")}</select>`)}
        ${field("想对老师说的话", `<textarea id="fb_text"></textarea>`)}
        <button class="btn primary" type="submit">提交反馈</button>
        <div class="msg" id="fb_msg"></div>
      </form>
    `;
    $$(".mood-opt input", el).forEach((i) => {
      i.addEventListener("change", () => {
        $$(".mood-opt", el).forEach((o) => o.style.borderColor = "var(--border)");
        i.closest(".mood-opt").style.borderColor = "var(--primary)";
      });
    });
    $("#feedback_form", el).addEventListener("submit", async (e) => {
      e.preventDefault();
      const mood = $('input[name="mood"]:checked', el)?.value || FEEDBACK_MOODS[0];
      const msg = $("#fb_msg", el);
      try {
        await api("/api/student/feedback", {
          method: "POST",
          body: JSON.stringify({ 姓名: S.studentName, 学号: S.studentId, 心情: mood, 学习状态: $("#fb_study", el).value, 反馈内容: $("#fb_text", el).value }),
        });
        msg.className = "msg success";
        msg.textContent = "反馈已提交";
        $("#fb_text", el).value = "";
      } catch (err) { msg.className = "msg error"; msg.textContent = err.message; }
    });
  }

  // ============================================================
  //  Tab7 请假申请
  // ============================================================
  async function renderLeaveTab() {
    const el = $("#s7");
    el.innerHTML = `
      <h3>📋 请假申请</h3>
      <form id="leave_form" class="panel" style="max-width:none;margin:0 0 16px">
        <div class="form-grid">
          ${field("请假日期", `<input type="date" id="leave_date" value="${todayStr()}">`)}
          ${field("请假节次", `<div>${checkboxGroup("leave_period", LEAVE_PERIODS, [])}</div>`)}
          ${field("请假事由", `<textarea id="leave_reason"></textarea>`)}
        </div>
        <button class="btn primary" type="submit">提交申请</button>
        <div class="msg" id="leave_msg"></div>
      </form>
      <details class="expander" open>
        <summary>我的请假记录</summary>
        <div class="expander-body" id="my_leaves"></div>
      </details>
    `;
    $("#leave_form", el).addEventListener("submit", async (e) => {
      e.preventDefault();
      const periods = checkedValues("leave_period", el);
      const msg = $("#leave_msg", el);
      if (periods.length === 0) { msg.className = "msg warning"; msg.textContent = "请选择请假节次"; return; }
      try {
        await api("/api/student/leave", {
          method: "POST",
          body: JSON.stringify({ 姓名: S.studentName, 学号: S.studentId, 请假日期: $("#leave_date", el).value, 节次: periods, 事由: $("#leave_reason", el).value }),
        });
        msg.className = "msg success";
        msg.textContent = "请假已提交";
        // 不刷新 tab，保持消息可见
      } catch (err) { msg.className = "msg error"; msg.textContent = err.message; }
    });
    try {
      const res = await api(`/api/student/leaves?name=${encodeURIComponent(S.studentName)}`);
      $("#my_leaves", el).innerHTML = tableHtml(
        ["请假日期", "节次", "事由", "预审状态"],
        res.rows.map((r) => [r["请假日期"], r["节次"], r["事由"], r["预审状态"]])
      );
    } catch (err) {
      $("#my_leaves", el).innerHTML = msgBox("error", err.message);
    }
  }

  // ============================================================
  //  教师端
  // ============================================================

  // ---------- Tab1 学生名单 ----------
  async function renderStudentListTab() {
    const el = $("#t1");
    el.innerHTML = `
      <h3>👥 学生名单管理</h3>
      <div class="info-box">上传或手动添加学生名单，只有名单上的学生才能登录</div>
      <div class="upload-area">
        <input type="file" id="list_file" accept=".xlsx,.xls">
        <button class="btn primary" id="upload_btn" style="margin-left:8px">上传学生名单（Excel：姓名、学号两列）</button>
        <div class="msg" id="upload_msg"></div>
      </div>
      <details class="expander">
        <summary>➕ 手动添加</summary>
        <div class="expander-body">
          <div class="form-grid">
            ${field("姓名", `<input type="text" id="add_name">`)}
            ${field("学号", `<input type="text" id="add_sid">`)}
          </div>
          <button class="btn primary" id="add_btn">添加</button>
          <div class="msg" id="add_msg"></div>
        </div>
      </details>
      <div id="list_table"></div>
    `;
    $("#upload_btn", el).addEventListener("click", async () => {
      const file = $("#list_file", el).files[0];
      const msg = $("#upload_msg", el);
      if (!file) { msg.className = "msg warning"; msg.textContent = "请先选择文件"; return; }
      const fd = new FormData();
      fd.append("file", file);
      try {
        const res = await fetch("/api/teacher/students/upload", {
          method: "POST", headers: { Authorization: "Bearer " + S.teacherToken }, body: fd,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "上传失败");
        msg.className = "msg success";
        msg.textContent = `已更新，共${data.count}人`;
        renderStudentListTab();
      } catch (e) { msg.className = "msg error"; msg.textContent = e.message; }
    });
    $("#add_btn", el).addEventListener("click", async () => {
      const name = $("#add_name", el).value.trim();
      const sid = $("#add_sid", el).value.trim();
      const msg = $("#add_msg", el);
      if (!name || !sid) { msg.className = "msg warning"; msg.textContent = "请填写姓名和学号"; return; }
      try {
        await api("/api/teacher/students/add", { method: "POST", body: JSON.stringify({ name, sid }) });
        msg.className = "msg success";
        msg.textContent = "已添加";
        renderStudentListTab();
      } catch (e) { msg.className = "msg error"; msg.textContent = e.message; }
    });
    try {
      const res = await api("/api/teacher/students");
      const rows = res.rows;
      $("#list_table", el).innerHTML = rows.length === 0
        ? `<div class="warn-box">暂无学生名单</div>`
        : tableHtml(Object.keys(rows[0]), rows.map((r) => Object.values(r).map((v) => esc(v))));
    } catch (e) {
      $("#list_table", el).innerHTML = msgBox("error", e.message);
    }
  }

  // ---------- Tab2 学生信息 ----------
  async function renderTeacherInfoTab() {
    const el = $("#t2");
    el.innerHTML = `<div class="caption">加载中...</div>`;
    try {
      const res = await api("/api/teacher/info");
      const m = res.metrics;
      el.innerHTML = `
        <h3>📋 学生基本信息</h3>
        <div class="metrics">
          <div class="metric-card"><div class="metric-value">${m.count}</div><div class="metric-label">已填写人数</div></div>
          <div class="metric-card"><div class="metric-value">${m.male}</div><div class="metric-label">男生</div></div>
          <div class="metric-card"><div class="metric-value">${m.female}</div><div class="metric-label">女生</div></div>
          <div class="metric-card"><div class="metric-value">${m.avgAge.toFixed(1)}</div><div class="metric-label">平均年龄</div></div>
        </div>
        <button class="btn" id="export_info_btn">📥 导出</button>
        <div class="table-wrap">${tableHtml(
          res.rows.length ? Object.keys(res.rows[0]) : ["暂无数据"],
          res.rows.map((r) => Object.keys(res.rows[0]).map((k) => esc(r[k] ?? "")))
        )}</div>
      `;
      $("#export_info_btn", el).addEventListener("click", async () => {
        const resp = await fetch("/api/teacher/info/export", { headers: { Authorization: "Bearer " + S.teacherToken } });
        const blob = await resp.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "学生基本信息.csv";
        a.click();
        URL.revokeObjectURL(a.href);
      });
    } catch (e) {
      el.innerHTML = msgBox("error", e.message);
    }
  }

  // ---------- Tab3 量化管理 ----------
  async function renderScoreManageTab() {
    const el = $("#t3");
    // 获取学生名单用于当事人多选
    let studentNames = [];
    try {
      const res = await api("/api/teacher/students");
      studentNames = res.rows.map((r) => r["姓名"]).filter(Boolean);
    } catch { /* ignore */ }

    el.innerHTML = `
      <h3>📊 量化管理</h3>
      <div class="info-box">添加加扣分记录，按时间段筛选查看汇总</div>
      <details class="expander">
        <summary>➕ 添加记录</summary>
        <div class="expander-body">
          <div class="form-grid">
            ${field("信息来源", `<select id="q_src">${SCORE_SOURCES.map((s) => `<option>${s}</option>`).join("")}</select>`)}
            ${field("方向", `<select id="q_dir">${SCORE_DIRECTIONS.map((s) => `<option>${s}</option>`).join("")}</select>`)}
            ${field("上报周期", `<select id="q_per">${SCORE_PERIODS.map((s) => `<option>${s}</option>`).join("")}</select>`)}
            ${field("时间", `<input type="date" id="q_date" value="${todayStr()}">`)}
            ${field("加分", `<input type="number" id="q_add" min="0" max="100" step="0.5" value="0">`)}
            ${field("扣分", `<input type="number" id="q_sub" min="0" max="100" step="0.5" value="0">`)}
          </div>
          ${studentNames.length > 0
            ? `<div class="field"><label>当事人（可选择多个学生）</label>
               <div id="q_students">${checkboxGroup("q_stu", ["【全班】", ...studentNames], [])}</div>
               <div class="caption" id="q_stu_hint"></div></div>`
            : `<div class="field"><label>当事人（请先上传学生名单）</label>
               <input type="text" id="q_stu_text"><div class="warn-box">⚠️ 请先在「学生名单」Tab 上传学生名单</div></div>`}
          ${field("原由", `<textarea id="q_reason"></textarea>`)}
          ${field("证明材料(可选)", `<input type="text" id="q_proof">`)}
          <button class="btn primary" id="q_add_btn">添加记录</button>
          <div class="msg" id="q_add_msg"></div>
        </div>
      </details>
      <div id="q_summary_area"></div>
    `;
    // 当事人选择联动提示
    const stuBox = $("#q_students", el);
    if (stuBox) {
      stuBox.addEventListener("change", () => {
        const sel = checkedValues("q_stu", el);
        const hint = $("#q_stu_hint", el);
        if (sel.includes("【全班】")) {
          hint.textContent = `✅ 已选择全班同学：共 ${studentNames.length} 人`;
        } else if (sel.length > 0) {
          hint.textContent = `已选择 ${sel.length} 位同学`;
        } else {
          hint.textContent = "";
        }
      });
    }
    $("#q_add_btn", el).addEventListener("click", async () => {
      const msg = $("#q_add_msg", el);
      let students = "";
      if (studentNames.length > 0) {
        const sel = checkedValues("q_stu", el);
        if (sel.includes("【全班】")) students = studentNames.join(",");
        else students = sel.join(",");
      } else {
        students = $("#q_stu_text", el).value.trim();
      }
      const add = parseFloat($("#q_add", el).value) || 0;
      const sub = parseFloat($("#q_sub", el).value) || 0;
      const reason = $("#q_reason", el).value.trim();
      if (!students || (add <= 0 && sub <= 0) || !reason) {
        msg.className = "msg error";
        msg.textContent = "请填写完整信息（当事人、分数、原由）";
        return;
      }
      try {
        await api("/api/teacher/score", {
          method: "POST",
          body: JSON.stringify({
            source: $("#q_src", el).value, direction: $("#q_dir", el).value,
            period: $("#q_per", el).value, date: $("#q_date", el).value,
            add, sub, students, reason, proof: $("#q_proof", el).value,
          }),
        });
        msg.className = "msg success";
        msg.textContent = `已添加记录，当事人：${students}`;
        // 仅刷新摘要区，不清空表单、保留消息
        renderScoreSummaryArea(el);
      } catch (e) { msg.className = "msg error"; msg.textContent = e.message; }
    });
    renderScoreSummaryArea(el);
  }

  async function renderScoreSummaryArea(el) {
    const area = $("#q_summary_area", el);
    try {
      const res = await api(`/api/teacher/scores?start=${encodeURIComponent("1970-01-01")}&end=${encodeURIComponent("2999-12-31")}`);
      const today = todayStr();
      area.innerHTML = `
        <div class="form-grid" style="margin:16px 0">
          ${field("开始日期", `<input type="date" id="q_start" value="${esc(res.minDate)}">`)}
          ${field("结束日期", `<input type="date" id="q_end" value="${esc(today)}">`)}
        </div>
        <button class="btn" id="q_filter_btn">筛选</button>
        <div class="caption" id="q_count"></div>
        <div id="q_summary"></div>
        <div id="q_detail_area"></div>
      `;
      $("#q_filter_btn", area).addEventListener("click", () => {
        loadScoreSummary(area);
      });
      loadScoreSummary(area);
    } catch (e) {
      area.innerHTML = msgBox("error", e.message);
    }
  }

  async function loadScoreSummary(area) {
    const start = $("#q_start", area).value;
    const end = $("#q_end", area).value;
    const summaryEl = $("#q_summary", area);
    const countEl = $("#q_count", area);
    try {
      const res = await api(`/api/teacher/scores?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
      countEl.textContent = `共 ${res.totalRecords} 条记录`;
      summaryEl.innerHTML = tableHtml(
        ["当事人", "加分合计", "扣分合计", "总分", "记录数"],
        res.summary.map((s) => [esc(s["当事人"]), s["加分合计"], s["扣分合计"], s["总分"], s["记录数"]])
      );
      const detailArea = $("#q_detail_area", area);
      if (res.summary.length > 0) {
        detailArea.innerHTML = `
          ${field("查看明细", `<select id="q_detail_sel">${res.summary.map((s) => `<option value="${esc(s["当事人"])}">${esc(s["当事人"])}</option>`).join("")}</select>`)}
          <div id="q_detail_table"></div>
        `;
        $("#q_detail_sel", area).addEventListener("change", () => showDetail(area, res));
        showDetail(area, res);
      } else {
        detailArea.innerHTML = "";
      }
    } catch (e) {
      summaryEl.innerHTML = msgBox("error", e.message);
    }
  }

  function showDetail(area, res) {
    const sel = $("#q_detail_sel", area);
    if (!sel) return;
    const name = sel.value;
    const rows = res.detailData[name] || [];
    $("#q_detail_table", area).innerHTML = tableHtml(
      ["时间", "信息来源", "加扣分方向", "加分", "扣分", "原由"],
      rows.map((r) => [esc(r["时间"]), esc(r["信息来源"]), esc(r["加扣分方向"]), esc(r["加分"]), esc(r["扣分"]), esc(r["原由"])])
    );
  }

  // ---------- Tab4 发布活动 ----------
  async function renderActivityManageTab() {
    const el = $("#t4");
    el.innerHTML = `
      <h3>📋 发布活动</h3>
      <form id="pub_form" class="panel" style="max-width:none;margin:0 0 16px">
        <div class="form-grid">
          ${field("活动名称", `<input type="text" id="act_name">`)}
          ${field("描述", `<textarea id="act_desc"></textarea>`)}
          ${field("截止日期", `<input type="date" id="act_deadline" value="${todayStr()}">`)}
          ${field("状态", `<select id="act_status"><option>进行中</option><option>已结束</option></select>`)}
        </div>
        <button class="btn primary" type="submit">发布</button>
        <div class="msg" id="pub_msg"></div>
      </form>
      <div id="pub_list"></div>
    `;
    $("#pub_form", el).addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = $("#act_name", el).value.trim();
      const msg = $("#pub_msg", el);
      if (!name) return;
      try {
        await api("/api/teacher/activity", {
          method: "POST",
          body: JSON.stringify({
            name, desc: $("#act_desc", el).value,
            deadline: $("#act_deadline", el).value, status: $("#act_status", el).value,
          }),
        });
        msg.className = "msg success";
        msg.textContent = "已发布";
        renderActivityManageTab();
      } catch (err) { msg.className = "msg error"; msg.textContent = err.message; }
    });
    try {
      const res = await api("/api/teacher/activities");
      $("#pub_list", el).innerHTML = tableHtml(
        ["活动名称", "活动描述", "发布时间", "截止时间", "状态"],
        res.rows.map((r) => [esc(r["活动名称"]), esc(r["活动描述"]), esc(r["发布时间"]), esc(r["截止时间"]), esc(r["状态"])])
      );
    } catch (e) {
      $("#pub_list", el).innerHTML = msgBox("error", e.message);
    }
  }

  // ---------- Tab5 学生荣誉 ----------
  async function renderAwardManageTab() {
    const el = $("#t5");
    el.innerHTML = `<div class="caption">加载中...</div>`;
    try {
      const res = await api("/api/teacher/awards");
      const m = res.metrics;
      el.innerHTML = `
        <h3>🏆 学生荣誉</h3>
        <div class="metrics">
          <div class="metric-card"><div class="metric-value">${m.total}</div><div class="metric-label">总荣誉数</div></div>
          <div class="metric-card"><div class="metric-value">${m.people}</div><div class="metric-label">获奖人数</div></div>
          <div class="metric-card"><div class="metric-value">${esc(m.maxLevel)}</div><div class="metric-label">最高级别</div></div>
        </div>
        ${tableHtml(
          ["姓名", "学号", "奖项名称", "奖项级别", "获奖时间", "备注"],
          res.rows.map((r) => [esc(r["姓名"]), esc(r["学号"]), esc(r["奖项名称"]), esc(r["奖项级别"]), esc(r["获奖时间"]), esc(r["备注"])])
        )}
      `;
    } catch (e) {
      el.innerHTML = msgBox("error", e.message);
    }
  }

  // ---------- Tab6 任务与反馈 ----------
  async function renderTaskFeedbackTab() {
    const el = $("#t6");
    el.innerHTML = `<div class="caption">加载中...</div>`;
    try {
      const [tasks, fb] = await Promise.all([
        api("/api/teacher/tasks"),
        api("/api/teacher/feedback"),
      ]);
      el.innerHTML = `
        <h3>📊 任务完成情况</h3>
        ${tableHtml(
          tasks.rows.length ? Object.keys(tasks.rows[0]) : ["暂无数据"],
          tasks.rows.map((r) => Object.keys(tasks.rows[0]).map((k) => esc(r[k] ?? "")))
        )}
        <hr style="margin:20px 0;border:none;border-top:1px solid var(--border)">
        <h3>📝 每日反馈</h3>
        <div class="field" style="max-width:300px">
          <label>筛选日期</label>
          <select id="fb_date_sel">
            <option value="">全部</option>
            ${fb.dates.map((d) => `<option value="${esc(d)}">${esc(d)}</option>`).join("")}
          </select>
        </div>
        <div id="fb_table">${tableHtml(
          fb.rows.length ? Object.keys(fb.rows[0]) : ["暂无数据"],
          fb.rows.map((r) => Object.keys(fb.rows[0]).map((k) => esc(r[k] ?? "")))
        )}</div>
      `;
      $("#fb_date_sel", el).addEventListener("change", async () => {
        const date = $("#fb_date_sel", el).value;
        const res = await api(`/api/teacher/feedback${date ? "?date=" + encodeURIComponent(date) : ""}`);
        $("#fb_table", el).innerHTML = tableHtml(
          res.rows.length ? Object.keys(res.rows[0]) : ["暂无数据"],
          res.rows.map((r) => Object.keys(res.rows[0]).map((k) => esc(r[k] ?? "")))
        );
      });
    } catch (e) {
      el.innerHTML = msgBox("error", e.message);
    }
  }

  // ---------- Tab7 请假审批 ----------
  async function renderLeaveApproveTab() {
    const el = $("#t7");
    el.innerHTML = `<div class="caption">加载中...</div>`;
    try {
      const res = await api("/api/teacher/leaves");
      const leaves = res.leaves;
      const pending = leaves.filter((l) => l.row["预审状态"] === "待审批");
      let html = `<h3>📋 请假审批</h3>`;
      if (pending.length === 0) {
        html += `<div class="info-box">暂无待审批记录</div>`;
      } else {
        pending.forEach(({ index, row }) => {
          html += `
            <div class="approve-item" data-idx="${index}">
              <div class="app-title">${esc(row["姓名"])} - ${esc(row["请假日期"])}</div>
              <div class="app-body">事由：${esc(row["事由"] || "")}（节次：${esc(row["节次"] || "")}）</div>
              <div class="app-actions">
                <select data-status>${LEAVE_APPROVE.map((s) => `<option>${s}</option>`).join("")}</select>
                <input type="text" placeholder="意见" data-comment>
                <button class="btn primary" data-confirm>确认</button>
              </div>
            </div>`;
        });
      }
      html += `<hr style="margin:20px 0;border:none;border-top:1px solid var(--border)">`;
      html += tableHtml(
        ["姓名", "学号", "请假日期", "节次", "事由", "申请时间", "预审状态", "班主任意见"],
        leaves.map(({ row }) => [esc(row["姓名"]), esc(row["学号"]), esc(row["请假日期"]), esc(row["节次"]), esc(row["事由"]), esc(row["申请时间"]), esc(row["预审状态"]), esc(row["班主任意见"])])
      );
      el.innerHTML = html;
      $$("[data-confirm]", el).forEach((btn) => {
        btn.addEventListener("click", async () => {
          const item = btn.closest(".approve-item");
          const index = parseInt(item.dataset.idx, 10);
          try {
            await api("/api/teacher/leave/approve", {
              method: "POST",
              body: JSON.stringify({
                index, status: $("[data-status]", item).value, comment: $("[data-comment]", item).value,
              }),
            });
            renderLeaveApproveTab();
          } catch (e) { alert(e.message); }
        });
      });
    } catch (e) {
      el.innerHTML = msgBox("error", e.message);
    }
  }

  // ---------- Tab8 数据导出 ----------
  async function renderExportTab() {
    const el = $("#t8");
    el.innerHTML = `
      <h3>📥 数据导出</h3>
      <button class="btn primary" id="export_all_btn">📦 一键导出全部数据</button>
      <div class="msg" id="export_msg"></div>
      <div class="info-box" style="margin-top:12px">建议每周备份一次</div>
    `;
    $("#export_all_btn", el).addEventListener("click", async () => {
      const msg = $("#export_msg", el);
      try {
        const resp = await fetch("/api/export", { headers: { Authorization: "Bearer " + S.teacherToken } });
        if (!resp.ok) throw new Error("导出失败");
        const blob = await resp.blob();
        const d = new Date();
        const stamp = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}_${String(d.getHours()).padStart(2, "0")}${String(d.getMinutes()).padStart(2, "0")}${String(d.getSeconds()).padStart(2, "0")}`;
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `班级数据_${stamp}.zip`;
        a.click();
        URL.revokeObjectURL(a.href);
        msg.className = "msg success";
        msg.textContent = "导出成功";
      } catch (e) {
        msg.className = "msg error";
        msg.textContent = e.message;
      }
    });
  }

  // ============================================================
  //  会话持久化（刷新后保持登录）
  // ============================================================
  function saveSession() {
    try {
      const st = sessionStorage;
      st.setItem("cp_role", S.role);
      st.setItem("cp_student", JSON.stringify({ loggedIn: S.studentLoggedIn, name: S.studentName, id: S.studentId }));
      st.setItem("cp_teacher", JSON.stringify({ loggedIn: S.teacherLoggedIn, token: S.teacherToken }));
    } catch { /* ignore */ }
  }

  function restoreSession() {
    try {
      const st = sessionStorage;
      const role = st.getItem("cp_role");
      if (role === "teacher" || role === "student") S.role = role;
      const stu = JSON.parse(st.getItem("cp_student") || "null");
      if (stu) {
        S.studentLoggedIn = !!stu.loggedIn;
        S.studentName = stu.name || "";
        S.studentId = stu.id || "";
      }
      const tea = JSON.parse(st.getItem("cp_teacher") || "null");
      if (tea) {
        S.teacherLoggedIn = !!tea.loggedIn;
        S.teacherToken = tea.token || "";
      }
    } catch { /* ignore */ }
  }

  // ============================================================
  //  初始化
  // ============================================================
  function init() {
    restoreSession();
    // 登录按钮
    $("#login-btn").addEventListener("click", studentLogin);
    $("#login-name").addEventListener("keydown", (e) => { if (e.key === "Enter") studentLogin(); });
    $("#student-logout").addEventListener("click", studentLogout);
    $("#teacher-login-btn").addEventListener("click", teacherLogin);
    $("#teacher-pwd").addEventListener("keydown", (e) => { if (e.key === "Enter") teacherLogin(); });
    $("#teacher-logout").addEventListener("click", teacherLogout);
    // Tab 切换
    $$("#student-tabs .tab").forEach((t) => t.addEventListener("click", () => activateTab("student", t.dataset.tab)));
    $$("#teacher-tabs .tab").forEach((t) => t.addEventListener("click", () => activateTab("teacher", t.dataset.tab)));
    // 初始渲染
    switchRole(S.role);
  }

  document.addEventListener("DOMContentLoaded", init);

  // 暴露给 HTML 内联事件
  window.App = { switchRole };
})();
