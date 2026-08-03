import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import zipfile
import io

# ---------- 网站标题配置 ----------
st.set_page_config(page_title="班级学生成长平台", layout="wide")

# ---------- 配置 ----------
TEACHER_PASSWORD = "123456"
DATA_FOLDER = "class_data"
STUDENT_LIST_FILE = "student_list.xlsx"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
USE_AI = True

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# ---------- CSV 数据加载保存 ----------
def load_data_csv(filename):
    filepath = os.path.join(DATA_FOLDER, f"{filename}.csv")
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig', dtype=str)
            return df.fillna("")
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data_csv(df, filename):
    if df is None or df.empty:
        df = pd.DataFrame()
    for col in df.columns:
        df[col] = df[col].astype(str).fillna("")
    filepath = os.path.join(DATA_FOLDER, f"{filename}.csv")
    df.to_csv(filepath, index=False, encoding='utf-8-sig')

def load_student_list():
    if os.path.exists(STUDENT_LIST_FILE):
        try:
            df = pd.read_excel(STUDENT_LIST_FILE, engine='openpyxl', dtype=str)
            return df.fillna("")
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def verify_student(name):
    student_list = load_student_list()
    if student_list.empty:
        return False, None
    matched = student_list[student_list['姓名'] == name]
    if len(matched) > 0:
        sid = matched.iloc[0]['学号'] if '学号' in matched.columns else name
        return True, str(sid)
    return False, None

# ---------- AI 分析函数 ----------
def call_deepseek_api(prompt, context):
    if not USE_AI or not DEEPSEEK_API_KEY:
        return "【AI未启用】请配置 DeepSeek API Key"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一位经验丰富的班主任，擅长分析学生数据，给出温暖、专业、可操作的建议。请用中文回复。"},
                {"role": "user", "content": f"{prompt}\n\n学生数据：\n{context}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI分析调用失败：{str(e)}"

def get_student_full_data(student_name, student_id):
    df_info = load_data_csv("student_info")
    df_awards = load_data_csv("student_awards")
    df_activities = load_data_csv("student_activities")
    df_tasks = load_data_csv("student_tasks")
    df_feedback = load_data_csv("daily_feedback")
    df_leaves = load_data_csv("leaves")
    df_scores = load_data_csv("score_records")
    
    student_info = df_info[df_info["姓名"] == student_name] if not df_info.empty else pd.DataFrame()
    student_awards = df_awards[df_awards["姓名"] == student_name] if not df_awards.empty else pd.DataFrame()
    student_activities = df_activities[df_activities["姓名"] == student_name] if not df_activities.empty else pd.DataFrame()
    student_tasks = df_tasks[df_tasks["姓名"] == student_name] if not df_tasks.empty else pd.DataFrame()
    student_feedback = df_feedback[df_feedback["姓名"] == student_name] if not df_feedback.empty else pd.DataFrame()
    student_leaves = df_leaves[df_leaves["姓名"] == student_name] if not df_leaves.empty else pd.DataFrame()
    student_scores = df_scores[df_scores["当事人"].str.contains(student_name) if not df_scores.empty else pd.Series()] if not df_scores.empty else pd.DataFrame()

    total_score = 0
    if not student_scores.empty:
        for _, row in student_scores.iterrows():
            add = float(row.get("加分", "0")) if row.get("加分", "0").replace('.', '').isdigit() else 0
            sub = float(row.get("扣分", "0")) if row.get("扣分", "0").replace('.', '').isdigit() else 0
            total_score += add - sub

    info_summary = ""
    if not student_info.empty:
        info = student_info.iloc[0]
        info_summary = f"""
【基本信息】
- 年龄：{info.get('年龄', '未填')}岁
- 性别：{info.get('性别', '未填')}
- 性格：{info.get('性格', '未填')}
- 爱好：{info.get('爱好', '未填')}
- 家庭性质：{info.get('家庭性质', '未填')}
- 文化课：{info.get('文化课情况', '未填')}
- 专业课：{info.get('专业课情况', '未填')}
"""

    awards_summary = f"- 荣誉总数：{len(student_awards)}项\n"
    if not student_awards.empty:
        for _, a in student_awards.iterrows():
            awards_summary += f"  - {a.get('奖项名称')}（{a.get('奖项级别')}）\n"

    activities_summary = f"- 参加活动：{len(student_activities)}次\n"
    
    if not student_tasks.empty and '完成状态' in student_tasks.columns:
        completed_count = len(student_tasks[student_tasks['完成状态'] == '已完成'])
        tasks_summary = f"- 任务完成：{completed_count}/ {len(student_tasks)}项\n"
    else:
        tasks_summary = "- 任务完成：暂无任务数据\n"
    
    score_summary = f"""
【量化管理】（总分：{total_score:.1f}分）
- 加分记录：{len(student_scores[student_scores['加分'].astype(float) > 0]) if not student_scores.empty else 0}条
- 扣分记录：{len(student_scores[student_scores['扣分'].astype(float) > 0]) if not student_scores.empty else 0}条
"""
    if not student_scores.empty:
        for _, s in student_scores.iterrows():
            add = float(s.get("加分", "0")) if s.get("加分", "0").replace('.','').isdigit() else 0
            sub = float(s.get("扣分", "0")) if s.get("扣分", "0").replace('.','').isdigit() else 0
            if add > 0:
                score_summary += f"  - {s.get('时间')} +{add}分（{s.get('原由')}）\n"
            elif sub > 0:
                score_summary += f"  - {s.get('时间')} -{sub}分（{s.get('原由')}）\n"

    return (info_summary + awards_summary + activities_summary + 
            tasks_summary + score_summary + "请结合量化分，对学生的行为表现进行评价和建议。")

def analyze_student(student_name, student_id):
    data_summary = get_student_full_data(student_name, student_id)
    prompt = """请根据以上数据，按以下格式生成学生成长画像：
## 📊 学生画像总览
## 🌟 优势与闪光点（特别列出荣誉和加分项）
## 📈 成长建议
## 💡 特别关注
## 🎯 近期目标
## 💌 老师的鼓励
请务必将量化加分情况纳入分析。"""
    return call_deepseek_api(prompt, data_summary)

def analyze_class_all(df_info, df_awards, df_activities, df_tasks, df_feedback, df_leaves, df_scores):
    total_score = 0
    if not df_scores.empty:
        for _, row in df_scores.iterrows():
            add = float(row.get("加分", "0")) if row.get("加分", "0").replace('.','').isdigit() else 0
            sub = float(row.get("扣分", "0")) if row.get("扣分", "0").replace('.','').isdigit() else 0
            total_score += add - sub
    task_completion_rate = 0
    if len(df_tasks) > 0 and '完成状态' in df_tasks.columns:
        task_completion_rate = len(df_tasks[df_tasks['完成状态']=='已完成']) / len(df_tasks) * 100
    context = f"""
【班级概况】总人数：{len(df_info)}人
【荣誉统计】总荣誉数：{len(df_awards)}项
【活动参与】总人次：{len(df_activities)}次
【任务完成】总任务数：{len(df_tasks)}项，完成率：{task_completion_rate:.1f}%
【量化管理】班级总量化分：{total_score:.1f}分，加分记录{len(df_scores[df_scores['加分'].astype(float)>0]) if not df_scores.empty else 0}条，扣分记录{len(df_scores[df_scores['扣分'].astype(float)>0]) if not df_scores.empty else 0}条
"""
    prompt = """根据以上数据，按以下格式生成班级分析报告：
## 🏫 班级整体画像
## ✅ 班级亮点
## ⚠️ 需要关注的问题
## 💡 班主任工作建议
## 🎯 本周班级目标"""
    return call_deepseek_api(prompt, context)

# ---------- 初始化数据文件 ----------
def init_data_files():
    files = {
        'student_info': ['姓名', '学号', '年龄', '性别', '身份证号', '电话号码', 
                         '户口本家庭地址', '实际常住家庭地址', '家庭性质', '家庭成员人数',
                         '性格', '爱好', '文化课情况', '专业课情况', '最后更新时间'],
        'activities_published': ['活动名称', '活动描述', '发布时间', '截止时间', '状态'],
        'student_activities': ['姓名', '学号', '活动名称', '报名时间', '参与状态', '备注'],
        'student_awards': ['姓名', '学号', '奖项名称', '奖项级别', '获奖时间', '备注'],
        'daily_feedback': ['姓名', '学号', '心情', '学习状态', '反馈内容', '日期', '时间'],
        'student_tasks': ['姓名', '学号', '任务名称', '完成状态', '完成时间', '备注'],
        'leaves': ['姓名', '学号', '请假日期', '节次', '事由', '申请时间', '预审状态', '班主任意见'],
        'ai_analysis': ['姓名', '学号', '分析时间', '分析结果'],
        'score_records': ['信息来源', '加扣分方向', '上报周期', '时间', '加分', '扣分', '当事人', '原由', '证明材料']
    }
    for filename, cols in files.items():
        filepath = os.path.join(DATA_FOLDER, f"{filename}.csv")
        if not os.path.exists(filepath):
            pd.DataFrame(columns=cols).to_csv(filepath, index=False, encoding='utf-8-sig')

init_data_files()

# ---------- 预设选项 ----------
def get_award_levels():
    return ["班级", "校级", "区级", "市级", "省级", "国家级", "国际级"]

def get_family_types():
    return ["正常家庭", "单亲离异", "单亲去世", "单亲其他", "孤儿", "其他"]

def get_personality_types():
    return ["内向", "外向", "开朗", "文静", "活泼", "沉稳", "敏感", "乐观", "其他"]

def get_academic_status():
    return ["优秀", "良好", "中等", "及格", "需努力", "不稳定"]

def get_professional_status():
    return ["优秀", "良好", "中等", "及格", "需努力", "基础薄弱"]

def get_score_directions():
    return ["晨会","晚自习纪律","储备人才库","综合管理人才库","专业技能库人才","文体宣传人才库","黑板报","教室/公区/绿化带/楼道卫生","寝室卫生","志愿服务库人才"]


def get_score_sources():
    return ["班长", "副班长", "学习委员", "文体委员", "卫生防疫员"]

def get_score_periods():
    return ["日", "周", "月", "一次性"]

# ---------- 学生端 ----------
def student_portal():
    st.header("👨‍🎓 学生成长中心")
    if 'student_logged_in' not in st.session_state:
        st.session_state.student_logged_in = False
        st.session_state.student_name = ""
        st.session_state.student_id = ""
    if not st.session_state.student_logged_in:
        student_name = st.text_input("请输入你的姓名登录", key="login_name").strip()
        if st.button("登录", key="login_btn"):
            if student_name:
                valid, sid = verify_student(student_name)
                if valid:
                    st.session_state.student_logged_in = True
                    st.session_state.student_name = student_name
                    st.session_state.student_id = str(sid)
                    st.rerun()
                else:
                    st.error("验证失败：你不在本班学生名单中")
            else:
                st.warning("请输入姓名")
        return
    student_name = st.session_state.student_name
    student_id = st.session_state.student_id
    st.success(f"欢迎 {student_name} 同学")
    if st.button("退出登录", key="student_logout"):
        st.session_state.student_logged_in = False
        st.rerun()
    st.divider()
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 基本信息", "📊 我的量化分", "🤖 AI成长画像", "🏆 我的荣誉", 
        "📋 参加活动", "✅ 我的任务", "📝 每日反馈", "📋 请假申请"
    ])
    
    with tab1:
        st.subheader("📋 我的基本信息")
        st.info("请认真填写以下信息，所有信息仅班主任可见")
        df_info = load_data_csv("student_info")
        existing = df_info[df_info["姓名"] == student_name] if not df_info.empty else pd.DataFrame()
        existing_age = 10
        if not existing.empty and existing["年龄"].iloc[0] != "" and existing["年龄"].iloc[0].isdigit():
            existing_age = int(existing["年龄"].iloc[0])
        existing_family_members = 3
        if not existing.empty and existing["家庭成员人数"].iloc[0] != "" and existing["家庭成员人数"].iloc[0].isdigit():
            existing_family_members = int(existing["家庭成员人数"].iloc[0])
        with st.form("student_info_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**基本信息**")
                st.text_input("姓名", value=student_name, disabled=True, key="info_name")
                age = st.number_input("年龄", min_value=5, max_value=30, value=existing_age, key="info_age")
                gender = st.selectbox("性别", ["男", "女"], index=0 if existing.empty or existing["性别"].iloc[0] != "女" else 1, key="info_gender")
                id_card = st.text_input("身份证号", value=existing["身份证号"].iloc[0] if not existing.empty else "", key="info_idcard")
                phone = st.text_input("电话号码（多个用逗号分隔）", value=existing["电话号码"].iloc[0] if not existing.empty else "", placeholder="例如：138****0000, 139****1111", key="info_phone")
                st.markdown("**家庭信息**")
                hometown_addr = st.text_area("户口本家庭地址", value=existing["户口本家庭地址"].iloc[0] if not existing.empty else "", height=68, key="info_hometown")
                current_addr = st.text_area("实际常住家庭住址", value=existing["实际常住家庭地址"].iloc[0] if not existing.empty else "", height=68, key="info_current")
                family_type = st.selectbox("家庭性质", get_family_types(), index=get_family_types().index(existing["家庭性质"].iloc[0]) if not existing.empty and existing["家庭性质"].iloc[0] in get_family_types() else 0, key="info_familytype")
                family_members = st.number_input("家庭成员人数", min_value=1, max_value=20, value=existing_family_members, key="info_familymembers")
            with col2:
                st.markdown("**个人特质**")
                personality = st.selectbox("性格", get_personality_types(), index=get_personality_types().index(existing["性格"].iloc[0]) if not existing.empty and existing["性格"].iloc[0] in get_personality_types() else 0, key="info_personality")
                hobby = st.text_area("爱好（可多项，用逗号分隔）", value=existing["爱好"].iloc[0] if not existing.empty else "", placeholder="例如：篮球, 阅读, 编程", key="info_hobby")
                st.markdown("**学习情况**")
                academic_status = st.selectbox("文化课情况", get_academic_status(), index=get_academic_status().index(existing["文化课情况"].iloc[0]) if not existing.empty and existing["文化课情况"].iloc[0] in get_academic_status() else 0, key="info_academic")
                professional_status = st.selectbox("专业课情况", get_professional_status(), index=get_professional_status().index(existing["专业课情况"].iloc[0]) if not existing.empty and existing["专业课情况"].iloc[0] in get_professional_status() else 0, key="info_professional")
            submitted = st.form_submit_button("💾 保存基本信息")
            if submitted:
                if not existing.empty:
                    idx = df_info[df_info["姓名"] == student_name].index[0]
                    df_info.at[idx, "年龄"] = str(age)
                    df_info.at[idx, "性别"] = gender
                    df_info.at[idx, "身份证号"] = id_card
                    df_info.at[idx, "电话号码"] = phone
                    df_info.at[idx, "户口本家庭地址"] = hometown_addr
                    df_info.at[idx, "实际常住家庭地址"] = current_addr
                    df_info.at[idx, "家庭性质"] = family_type
                    df_info.at[idx, "家庭成员人数"] = str(family_members)
                    df_info.at[idx, "性格"] = personality
                    df_info.at[idx, "爱好"] = hobby
                    df_info.at[idx, "文化课情况"] = academic_status
                    df_info.at[idx, "专业课情况"] = professional_status
                    df_info.at[idx, "最后更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    new_row = pd.DataFrame([{
                        "姓名": student_name, "学号": student_id, "年龄": str(age), "性别": gender,
                        "身份证号": id_card, "电话号码": phone, "户口本家庭地址": hometown_addr,
                        "实际常住家庭地址": current_addr, "家庭性质": family_type, "家庭成员人数": str(family_members),
                        "性格": personality, "爱好": hobby, "文化课情况": academic_status,
                        "专业课情况": professional_status, "最后更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    df_info = pd.concat([df_info, new_row], ignore_index=True)
                save_data_csv(df_info, "student_info")
                st.success("基本信息已保存！")
        if not existing.empty:
            st.info("✅ 已填写基本信息，如需修改请直接修改后再次保存")
    
    with tab2:
        st.subheader("📊 我的量化管理分")
        df_scores = load_data_csv("score_records")
        # 筛选包含该学生姓名的记录（支持多个当事人用逗号分隔）
        if not df_scores.empty:
            my_scores = df_scores[df_scores["当事人"].str.contains(student_name, na=False)]
        else:
            my_scores = pd.DataFrame()
        
        total_score = 0
        if not my_scores.empty:
            for _, row in my_scores.iterrows():
                add = float(row.get("加分", "0")) if row.get("加分", "0").replace('.','').isdigit() else 0
                sub = float(row.get("扣分", "0")) if row.get("扣分", "0").replace('.','').isdigit() else 0
                total_score += add - sub
        
        col1, col2, col3 = st.columns(3)
        col1.metric("当前总分", f"{total_score:.1f}")
        col2.metric("加分总次数", len(my_scores[my_scores['加分'].astype(float) > 0]) if not my_scores.empty else 0)
        col3.metric("扣分总次数", len(my_scores[my_scores['扣分'].astype(float) > 0]) if not my_scores.empty else 0)
        
        if not my_scores.empty:
            st.subheader("📋 详细记录")
            display_df = my_scores[["时间", "信息来源", "加扣分方向", "加分", "扣分", "原由"]].copy()
            display_df.columns = ["时间", "来源", "方向", "加分", "扣分", "原由"]
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("暂无量化记录，继续努力！")
    
    with tab3:
        st.subheader("🤖 AI 成长画像分析")
        df_info = load_data_csv("student_info")
        has_info = not df_info[df_info["姓名"] == student_name].empty
        if not has_info:
            st.warning("⚠️ 请先在「基本信息」中填写你的个人资料")
        else:
            df_analysis = load_data_csv("ai_analysis")
            existing_analysis = df_analysis[df_analysis["姓名"] == student_name] if not df_analysis.empty else pd.DataFrame()
            if st.button("🔄 重新生成分析报告", key="refresh_analysis"):
                with st.spinner("AI 正在分析..."):
                    analysis_result = analyze_student(student_name, student_id)
                    if not existing_analysis.empty:
                        idx = df_analysis[df_analysis["姓名"] == student_name].index[0]
                        df_analysis.at[idx, "分析结果"] = analysis_result
                        df_analysis.at[idx, "分析时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        new_row = pd.DataFrame([{
                            "姓名": student_name, "学号": student_id,
                            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "分析结果": analysis_result
                        }])
                        df_analysis = pd.concat([df_analysis, new_row], ignore_index=True)
                    save_data_csv(df_analysis, "ai_analysis")
                    st.success("分析完成！")
                    st.rerun()
            if not existing_analysis.empty:
                st.markdown(existing_analysis["分析结果"].iloc[0])
                st.caption(f"分析时间：{existing_analysis['分析时间'].iloc[0]}")
            else:
                st.info("点击按钮生成专属成长画像")
    
    with tab4:
        st.subheader("🏆 我的荣誉墙")
        with st.form("add_award_form"):
            col1, col2 = st.columns(2)
            with col1:
                award_name = st.text_input("荣誉/奖项名称", key="award_name")
                award_level = st.selectbox("荣誉级别", get_award_levels(), key="award_level")
            with col2:
                award_date = st.date_input("获奖日期", value=date.today(), key="award_date")
                remark = st.text_input("备注（可选）", key="award_remark")
            if st.form_submit_button("➕ 添加荣誉") and award_name:
                df = load_data_csv("student_awards")
                new_row = pd.DataFrame([{
                    "姓名": student_name, "学号": student_id,
                    "奖项名称": award_name, "奖项级别": award_level,
                    "获奖时间": award_date.strftime("%Y-%m-%d"), "备注": remark
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "student_awards")
                st.success(f"已添加：{award_name}")
                st.rerun()
        df_awards = load_data_csv("student_awards")
        if not df_awards.empty:
            my_awards = df_awards[df_awards["姓名"] == student_name]
            if not my_awards.empty:
                st.dataframe(my_awards[["奖项名称", "奖项级别", "获奖时间", "备注"]], use_container_width=True)
    
    with tab5:
        st.subheader("📋 可报名的活动")
        df_activities = load_data_csv("activities_published")
        df_my_activities = load_data_csv("student_activities")
        my_activity_names = df_my_activities[df_my_activities["姓名"] == student_name]["活动名称"].tolist() if not df_my_activities.empty else []
        if not df_activities.empty:
            for idx, act in df_activities.iterrows():
                if act['活动名称'] in my_activity_names:
                    continue
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{act['活动名称']}**")
                    st.caption(act.get('活动描述', ''))
                with col2:
                    st.caption(f"截止：{act.get('截止时间', '无')}")
                with col3:
                    if st.button("报名", key=f"join_act_{idx}"):
                        new_row = pd.DataFrame([{
                            "姓名": student_name, "学号": student_id,
                            "活动名称": act['活动名称'], "报名时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "参与状态": "已报名", "备注": ""
                        }])
                        df_my = load_data_csv("student_activities")
                        df_my = pd.concat([df_my, new_row], ignore_index=True)
                        save_data_csv(df_my, "student_activities")
                        st.success(f"已报名：{act['活动名称']}")
                        st.rerun()
        else:
            st.info("暂无可报名的活动")
        with st.expander("📋 我已报名的活动"):
            if not df_my_activities.empty:
                my_acts = df_my_activities[df_my_activities["姓名"] == student_name]
                if not my_acts.empty:
                    st.dataframe(my_acts[["活动名称", "报名时间", "参与状态"]], use_container_width=True)
    
    with tab6:
        st.subheader("✅ 我的任务")
        df_tasks = load_data_csv("student_tasks")
        my_tasks = df_tasks[df_tasks["姓名"] == student_name] if not df_tasks.empty else pd.DataFrame()
        if not my_tasks.empty:
            for idx in my_tasks.index:
                task = my_tasks.loc[idx]
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📌 **{task['任务名称']}**")
                    st.caption(task.get('备注', ''))
                with col2:
                    current = task["完成状态"]
                    options = ["未开始", "进行中", "已完成"]
                    new_status = st.selectbox("状态", options, index=options.index(current) if current in options else 0, key=f"task_status_{idx}")
                with col3:
                    if new_status != current:
                        if st.button("更新", key=f"task_update_{idx}"):
                            df_tasks.at[idx, "完成状态"] = new_status
                            if new_status == "已完成":
                                df_tasks.at[idx, "完成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            save_data_csv(df_tasks, "student_tasks")
                            st.success("已更新")
                            st.rerun()
        else:
            st.info("暂无任务安排")
    
    with tab7:
        with st.form("daily_feedback_form"):
            mood = st.select_slider("今天心情", ["😔很差", "😐一般", "🙂不错", "😄非常好"], key="feedback_mood")
            study_status = st.selectbox("学习状态", ["很吃力", "有点吃力", "正常", "良好", "优秀"], key="feedback_study")
            feedback = st.text_area("想对老师说的话", key="feedback_text")
            if st.form_submit_button("提交反馈"):
                df = load_data_csv("daily_feedback")
                new_row = pd.DataFrame([{
                    "姓名": student_name, "学号": student_id,
                    "心情": mood, "学习状态": study_status, "反馈内容": feedback,
                    "日期": date.today().strftime("%Y-%m-%d"), "时间": datetime.now().strftime("%H:%M:%S")
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "daily_feedback")
                st.success("反馈已提交")
    
    with tab8:
        with st.form("leave_form_student"):
            col1, col2 = st.columns(2)
            with col1:
                leave_date = st.date_input("请假日期", value=date.today(), key="leave_date")
                periods = st.multiselect("请假节次", ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "全天"], key="leave_periods")
            with col2:
                reason = st.text_area("请假事由", key="leave_reason")
            if st.form_submit_button("提交申请") and periods:
                df = load_data_csv("leaves")
                new_row = pd.DataFrame([{
                    "姓名": student_name, "学号": student_id,
                    "请假日期": leave_date.strftime("%Y-%m-%d"), "节次": ",".join(periods),
                    "事由": reason, "申请时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "预审状态": "待审批", "班主任意见": ""
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "leaves")
                st.success("请假已提交")
        with st.expander("我的请假记录"):
            df_leave = load_data_csv("leaves")
            if not df_leave.empty:
                my_leaves = df_leave[df_leave["姓名"] == student_name]
                if not my_leaves.empty:
                    st.dataframe(my_leaves[["请假日期", "节次", "事由", "预审状态"]], use_container_width=True)

# ---------- 教师后台 ----------
def teacher_login():
    st.header("🔐 教师后台")
    pwd = st.text_input("管理员密码", type="password", key="teacher_pwd")
    if pwd == TEACHER_PASSWORD:
        st.session_state.teacher_logged_in = True
        st.rerun()
    elif pwd:
        st.error("密码错误")

def teacher_portal():
    st.header("📊 教师管理平台")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "👥 学生名单", "📋 学生信息", "📊 量化管理", "🤖 AI分析", 
        "📋 发布活动", "🏆 学生荣誉", "📊 任务与反馈", "📋 请假审批", "📥 数据导出"
    ])
    
    with tab1:
        st.subheader("👥 学生名单管理")
        st.info("上传或手动添加学生名单，只有名单上的学生才能登录")
        uploaded = st.file_uploader("上传学生名单（Excel：姓名、学号两列）", type=["xlsx"], key="upload_list")
        if uploaded:
            df = pd.read_excel(uploaded, engine='openpyxl', dtype=str).fillna("")
            df.to_excel(STUDENT_LIST_FILE, index=False)
            st.success(f"已更新，共{len(df)}人")
            st.rerun()
        if os.path.exists(STUDENT_LIST_FILE):
            df = pd.read_excel(STUDENT_LIST_FILE, engine='openpyxl', dtype=str).fillna("")
            st.dataframe(df, use_container_width=True)
            with st.expander("➕ 手动添加"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("姓名", key="add_name")
                with col2:
                    new_id = st.text_input("学号", key="add_id")
                if st.button("添加", key="add_btn") and new_name and new_id:
                    new_row = pd.DataFrame([{"姓名": new_name, "学号": new_id}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_excel(STUDENT_LIST_FILE, index=False)
                    st.rerun()
        else:
            st.warning("暂无学生名单")
    
    with tab2:
        st.subheader("📋 学生基本信息")
        df_info = load_data_csv("student_info")
        if not df_info.empty:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("已填写人数", len(df_info))
            col2.metric("男生", len(df_info[df_info["性别"] == "男"]))
            col3.metric("女生", len(df_info[df_info["性别"] == "女"]))
            avg_age = df_info[df_info["年龄"].str.isdigit()]["年龄"].astype(float).mean() if len(df_info[df_info["年龄"].str.isdigit()]) > 0 else 0
            col4.metric("平均年龄", f"{avg_age:.1f}")
            st.dataframe(df_info, use_container_width=True)
            csv_data = df_info.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出", csv_data, "学生基本信息.csv", "text/csv", key="export_info")
        else:
            st.info("暂无数据")
    
    # ===== Tab3: 量化管理（修复版） =====
    with tab3:
        st.subheader("📊 量化管理")
        st.info("添加加扣分记录，按时间段筛选查看汇总")
        
        student_list = load_student_list()
        student_names = student_list["姓名"].tolist() if not student_list.empty else []
        
        with st.expander("➕ 添加记录", expanded=False):
            with st.form("add_score_form_quant"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    source = st.selectbox("信息来源", get_score_sources(), key="q_src")
                    direction = st.selectbox("方向", get_score_directions(), key="q_dir")
                    period = st.selectbox("上报周期", get_score_periods(), key="q_per")
                with col2:
                    score_date = st.date_input("时间", value=date.today(), key="q_date")
                    add_score = st.number_input("加分", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="q_add")
                    sub_score = st.number_input("扣分", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="q_sub")
                with col3:
                    if student_names:
                        all_options = ["【全班】"] + student_names
                        selected_students = st.multiselect(
                            "当事人（可选择多个学生）",
                            options=all_options,
                            key="q_stu_multi",
                            placeholder="请选择一名或多名学生..."
                        )
                        if "【全班】" in selected_students:
                            student_input = ",".join(student_names)
                            st.info(f"✅ 已选择全班同学：共 {len(student_names)} 人")
                        else:
                            student_input = ",".join(selected_students) if selected_students else ""
                            if selected_students:
                                st.success(f"已选择 {len(selected_students)} 位同学")
                    else:
                        student_input = st.text_input("当事人（请先上传学生名单）", key="q_stu")
                        st.warning("⚠️ 请先在「学生名单」Tab 上传学生名单")
                    
                    reason = st.text_area("原由", key="q_reason")
                    proof = st.text_input("证明材料(可选)", key="q_proof")
                
                if st.form_submit_button("添加记录"):
                    if student_input and (add_score > 0 or sub_score > 0) and reason:
                        df = load_data_csv("score_records")
                        new_row = pd.DataFrame([{
                            "信息来源": source, "加扣分方向": direction, "上报周期": period,
                            "时间": score_date.strftime("%Y-%m-%d"), "加分": str(add_score),
                            "扣分": str(sub_score), "当事人": student_input, "原由": reason,
                            "证明材料": proof
                        }])
                        df = pd.concat([df, new_row], ignore_index=True)
                        save_data_csv(df, "score_records")
                        st.success(f"已添加记录，当事人：{student_input}")
                        st.rerun()
                    else:
                        st.error("请填写完整信息（当事人、分数、原由）")
        
        df_scores = load_data_csv("score_records")
        if not df_scores.empty:
            df_scores["加分"] = df_scores["加分"].astype(float)
            df_scores["扣分"] = df_scores["扣分"].astype(float)
            df_scores["时间"] = pd.to_datetime(df_scores["时间"], errors='coerce')
            
            col1, col2 = st.columns(2)
            with col1:
                min_date = df_scores["时间"].min().date() if not df_scores["时间"].isna().all() else date.today()
                start = st.date_input("开始日期", value=min_date, key="q_start")
            with col2:
                end = st.date_input("结束日期", value=date.today(), key="q_end")
            
            mask = (df_scores["时间"] >= pd.Timestamp(start)) & (df_scores["时间"] <= pd.Timestamp(end))
            filtered = df_scores[mask].copy()
            st.caption(f"共 {len(filtered)} 条记录")
            
            if not filtered.empty:
                # 展开多个当事人
                expanded_rows = []
                for _, row in filtered.iterrows():
                    if pd.notna(row["当事人"]) and "," in str(row["当事人"]):
                        for name in str(row["当事人"]).split(","):
                            name = name.strip()
                            if name:
                                new_row = row.copy()
                                new_row["当事人"] = name
                                expanded_rows.append(new_row)
                    else:
                        expanded_rows.append(row)
                expanded_df = pd.DataFrame(expanded_rows) if expanded_rows else filtered
                
                summary = expanded_df.groupby("当事人").apply(lambda x: pd.Series({
                    "加分合计": x["加分"].sum(), 
                    "扣分合计": x["扣分"].sum(),
                    "总分": x["加分"].sum() - x["扣分"].sum(), 
                    "记录数": len(x)
                })).reset_index().sort_values("总分", ascending=False)
                st.dataframe(summary, use_container_width=True)
                
                if not summary.empty:
                    stu = st.selectbox("查看明细", summary["当事人"].tolist(), key="q_detail")
                    if stu:
                        detail = expanded_df[expanded_df["当事人"] == stu].sort_values("时间", ascending=False)
                        st.dataframe(detail[["时间", "信息来源", "加扣分方向", "加分", "扣分", "原由"]], use_container_width=True)
        else:
            st.info("暂无记录")
    
    with tab4:
        st.subheader("🤖 AI 综合分析")
        df_info = load_data_csv("student_info")
        if df_info.empty:
            st.warning("请等待学生填写基本信息")
        else:
            if st.button("生成班级综合分析报告", key="class_ai"):
                with st.spinner("AI分析中..."):
                    df_awards = load_data_csv("student_awards")
                    df_activities = load_data_csv("student_activities")
                    df_tasks = load_data_csv("student_tasks")
                    df_feedback = load_data_csv("daily_feedback")
                    df_leaves = load_data_csv("leaves")
                    df_scores = load_data_csv("score_records")
                    result = analyze_class_all(df_info, df_awards, df_activities, df_tasks, df_feedback, df_leaves, df_scores)
                    st.markdown(result)
            stu = st.selectbox("选择学生查看个人画像", df_info["姓名"].tolist(), key="ai_stu")
            if stu and st.button("生成个人画像", key="stu_ai"):
                with st.spinner("生成中..."):
                    sid = df_info[df_info["姓名"] == stu]["学号"].iloc[0] if not df_info.empty else ""
                    result = analyze_student(stu, str(sid))
                    st.markdown(result)
    
    with tab5:
        st.subheader("📋 发布活动")
        df = load_data_csv("activities_published")
        with st.form("pub_act"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("活动名称", key="act_n")
                desc = st.text_area("描述", key="act_d")
            with col2:
                deadline = st.date_input("截止日期", value=date.today(), key="act_dl")
                status = st.selectbox("状态", ["进行中", "已结束"], key="act_st")
            if st.form_submit_button("发布") and name:
                new = pd.DataFrame([{"活动名称": name, "活动描述": desc, "发布时间": datetime.now().strftime("%Y-%m-%d"), "截止时间": deadline.strftime("%Y-%m-%d"), "状态": status}])
                df = pd.concat([df, new], ignore_index=True)
                save_data_csv(df, "activities_published")
                st.success("已发布")
                st.rerun()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
    
    with tab6:
        st.subheader("🏆 学生荣誉")
        df = load_data_csv("student_awards")
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("总荣誉数", len(df))
            col2.metric("获奖人数", df["姓名"].nunique())
            col3.metric("最高级别", df["奖项级别"].max() if not df.empty else "无")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无数据")
    
    with tab7:
        st.subheader("📊 任务完成情况")
        df = load_data_csv("student_tasks")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无数据")
        st.divider()
        st.subheader("📝 每日反馈")
        df = load_data_csv("daily_feedback")
        if not df.empty:
            dates = sorted(df["日期"].unique(), reverse=True)
            sel = st.selectbox("筛选日期", ["全部"] + list(dates), key="fb_date")
            if sel != "全部":
                df = df[df["日期"] == sel]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无数据")
    
    with tab8:
        st.subheader("📋 请假审批")
        df = load_data_csv("leaves")
        if not df.empty:
            pending = df[df["预审状态"] == "待审批"]
            for idx in pending.index:
                row = df.loc[idx]
                with st.expander(f"{row['姓名']} - {row['请假日期']}"):
                    st.write(f"事由：{row['事由']}")
                    status = st.selectbox("审批", ["已批准", "已拒绝"], key=f"lv_st_{idx}")
                    comment = st.text_input("意见", key=f"lv_cm_{idx}")
                    if st.button("确认", key=f"lv_ap_{idx}"):
                        df.loc[idx, "预审状态"] = status
                        df.loc[idx, "班主任意见"] = comment
                        save_data_csv(df, "leaves")
                        st.success("已处理")
                        st.rerun()
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无记录")
    
    with tab9:
        st.subheader("📥 数据导出")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(DATA_FOLDER):
                if f.endswith('.csv'):
                    zf.write(os.path.join(DATA_FOLDER, f), f)
        zip_buffer.seek(0)
        st.download_button(
            label="📦 一键导出全部数据",
            data=zip_buffer,
            file_name=f"班级数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="export_all"
        )
        st.info("建议每周备份一次")

# ---------- 主入口 ----------
def main():
    st.sidebar.title("导航")
    if "teacher_logged_in" not in st.session_state:
        st.session_state.teacher_logged_in = False
    role = st.sidebar.radio("登录身份", ["👨‍🎓 学生入口", "👩‍🏫 教师后台"])
    if role == "👨‍🎓 学生入口":
        student_portal()
    else:
        if st.session_state.teacher_logged_in:
            teacher_portal()
            if st.sidebar.button("退出登录"):
                st.session_state.teacher_logged_in = False
                st.rerun()
        else:
            teacher_login()

if __name__ == "__main__":
    main()
