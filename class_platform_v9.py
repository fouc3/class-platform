import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import zipfile
import io
import json

st.set_page_config(page_title="班级学生成长平台", layout="wide")

# ---------- 配置 ----------
TEACHER_PASSWORD = "123456"
DATA_FOLDER = "class_data"
STUDENT_LIST_FILE = "student_list.xlsx"

# ---------- AI 配置（DeepSeek）----------
# 请到 https://platform.deepseek.com/ 注册获取 API Key
DEEPSEEK_API_KEY = ""  # 改用环境变量，不要写在这里
USE_AI = True  # 是否启用AI分析

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
    """调用 DeepSeek API 进行分析"""
    if not USE_AI or DEEPSEEK_API_KEY == "你的API密钥":
        return "【AI未启用】请配置 DeepSeek API Key 后使用"
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一位经验丰富的班主任和成长导师，擅长分析学生数据，给出温暖、专业、可操作的建议。请用中文回复，语言亲切自然。"},
                {"role": "user", "content": f"{prompt}\n\n学生数据：\n{context}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI分析调用失败：{str(e)}"

def get_student_full_data(student_name, student_id):
    """获取某个学生的所有数据，用于AI分析"""
    # 加载所有相关数据
    df_info = load_data_csv("student_info")
    df_awards = load_data_csv("student_awards")
    df_activities = load_data_csv("student_activities")
    df_tasks = load_data_csv("student_tasks")
    df_feedback = load_data_csv("daily_feedback")
    df_leaves = load_data_csv("leaves")
    
    # 提取该学生的数据
    student_info = df_info[df_info["姓名"] == student_name] if not df_info.empty else pd.DataFrame()
    student_awards = df_awards[df_awards["姓名"] == student_name] if not df_awards.empty else pd.DataFrame()
    student_activities = df_activities[df_activities["姓名"] == student_name] if not df_activities.empty else pd.DataFrame()
    student_tasks = df_tasks[df_tasks["姓名"] == student_name] if not df_tasks.empty else pd.DataFrame()
    student_feedback = df_feedback[df_feedback["姓名"] == student_name] if not df_feedback.empty else pd.DataFrame()
    student_leaves = df_leaves[df_leaves["姓名"] == student_name] if not df_leaves.empty else pd.DataFrame()
    
    # ========== 1. 基本信息 ==========
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
- 家庭成员人数：{info.get('家庭成员人数', '未填')}人
- 文化课情况：{info.get('文化课情况', '未填')}
- 专业课情况：{info.get('专业课情况', '未填')}
"""
    else:
        info_summary = "【基本信息】尚未填写\n"
    
    # ========== 2. 荣誉记录（重点修复）==========
    awards_summary = ""
    if not student_awards.empty:
        awards_list = []
        for _, award in student_awards.iterrows():
            award_name = award.get('奖项名称', '未知')
            award_level = award.get('奖项级别', '未知')
            award_date = award.get('获奖时间', '未知')
            awards_list.append(f"  - {award_date}：获得{award_level}级【{award_name}】")
        
        awards_summary = f"""
【荣誉奖项】（共{len(student_awards)}项）
{chr(10).join(awards_list)}
"""
    else:
        awards_summary = "【荣誉奖项】暂无记录\n"
    
    # ========== 3. 活动参与记录 ==========
    activities_summary = ""
    if not student_activities.empty:
        activities_list = []
        for _, act in student_activities.iterrows():
            act_name = act.get('活动名称', '未知')
            act_time = act.get('报名时间', '未知')
            activities_list.append(f"  - {act_time}：报名参加【{act_name}】")
        
        activities_summary = f"""
【活动参与】（共{len(student_activities)}次）
{chr(10).join(activities_list)}
"""
        # 计算活动参与积极性
        act_count = len(student_activities)
        if act_count >= 5:
            activities_summary += "\n**活动积极性评价**：非常高，该生非常活跃，积极参加各类活动。\n"
        elif act_count >= 3:
            activities_summary += "\n**活动积极性评价**：较高，该生乐于参加集体活动。\n"
        elif act_count >= 1:
            activities_summary += "\n**活动积极性评价**：一般，建议鼓励多参与活动。\n"
        else:
            activities_summary += "\n**活动积极性评价**：较低，需要关注并鼓励参与。\n"
    else:
        activities_summary = "【活动参与】暂无记录。该生活动积极性较低，建议鼓励参与。\n"
    
    # ========== 4. 任务完成情况 ==========
    tasks_summary = ""
    if not student_tasks.empty:
        completed = len(student_tasks[student_tasks['完成状态'] == '已完成'])
        pending = len(student_tasks[student_tasks['完成状态'] == '未开始'])
        in_progress = len(student_tasks[student_tasks['完成状态'] == '进行中'])
        total = len(student_tasks)
        
        tasks_summary = f"""
【任务完成情况】
- 总任务数：{total}项
- 已完成：{completed}项
- 进行中：{in_progress}项
- 未开始：{pending}项
- 完成率：{completed/total*100:.0f}%
"""
        if completed == total:
            tasks_summary += "\n**任务完成评价**：非常优秀，该生责任心强，能按时完成所有任务。\n"
        elif completed >= total * 0.7:
            tasks_summary += "\n**任务完成评价**：良好，大部分任务都能完成。\n"
        elif completed >= total * 0.5:
            tasks_summary += "\n**任务完成评价**：一般，需要加强执行力。\n"
        else:
            tasks_summary += "\n**任务完成评价**：较差，需要重点关注和督促。\n"
    else:
        tasks_summary = "【任务完成情况】暂无任务记录\n"
    
    # ========== 5. 近期反馈 ==========
    feedback_summary = ""
    if not student_feedback.empty:
        recent_feedback = student_feedback.tail(5)
        feedback_list = []
        mood_map = {"😔很差": "情绪低落", "😐一般": "情绪一般", "🙂不错": "情绪不错", "😄非常好": "情绪很好"}
        for _, fb in recent_feedback.iterrows():
            mood = fb.get('心情', '')
            mood_text = mood_map.get(mood, mood)
            study = fb.get('学习状态', '')
            content = fb.get('反馈内容', '')[:50]
            date_val = fb.get('日期', '')
            feedback_list.append(f"  - {date_val}：心情{mood_text}，学习状态{study}，说：{content}")
        
        feedback_summary = f"""
【近期反馈】（最近5条）
{chr(10).join(feedback_list)}
"""
    else:
        feedback_summary = "【近期反馈】暂无记录\n"
    
    # ========== 6. 请假情况 ==========
    leave_summary = ""
    if not student_leaves.empty:
        leave_count = len(student_leaves)
        approved = len(student_leaves[student_leaves['预审状态'] == '已批准'])
        leave_summary = f"【请假情况】共请假{leave_count}次，其中已批准{approved}次\n"
        if leave_count >= 5:
            leave_summary += "**提醒**：请假次数较多，建议关注出勤情况。\n"
    else:
        leave_summary = "【请假情况】无请假记录，出勤良好\n"
    
    # ========== 7. 综合分析与建议 ==========
    # 生成额外的分析提示
    extra_analysis = "\n【AI分析任务】\n"
    extra_analysis += "请综合以上所有信息，包括：\n"
    extra_analysis += "1. 学生的个人特质（性格、爱好）\n"
    extra_analysis += "2. 家庭背景情况\n"
    extra_analysis += "3. 学习情况（文化课+专业课）\n"
    extra_analysis += "4. 获得的各类荣誉奖项（特别重要）\n"
    extra_analysis += "5. 活动参与积极性\n"
    extra_analysis += "6. 任务完成率和责任心\n"
    extra_analysis += "7. 近期反馈中的情绪和状态\n"
    extra_analysis += "8. 请假出勤情况\n\n"
    extra_analysis += "请给出全面、个性化的成长画像和建议。对于学生的荣誉和成绩，一定要在分析中体现和表扬。"
    
    # 汇总所有信息
    full_data = (info_summary + awards_summary + activities_summary + 
                 tasks_summary + feedback_summary + leave_summary + extra_analysis)
    
    return full_data
def analyze_student(student_name, student_id):
    """调用 AI 分析单个学生"""
    data_summary = get_student_full_data(student_name, student_id)
    
    prompt = """请根据以上学生数据，进行全面的成长分析。请按以下格式输出：

## 📊 学生画像总览
（一句话概括这个学生的特点，要包含他的闪光点和荣誉）

## 🌟 优势与闪光点
- 请特别列出该生获得过的荣誉奖项（如三好学生、竞赛获奖等）
- 列出其他3-5个优势（性格、爱好、活动参与、任务完成等）

## 📈 成长建议
- 列出3-5条具体可操作的建议

## 💡 特别关注
（如果有需要特别关注的情况，如家庭特殊、学习困难、情绪问题等，请指出；如果没有则写"暂无"）

## 🎯 近期发展目标
- 建议1-2个近期可达成的目标

## 💌 老师的鼓励
（写一段温暖、鼓励的话，肯定该生的成绩和努力）

**重要**：请务必将该生获得的荣誉奖项在分析中体现出来，这是对他努力的肯定。"""
    
    return call_deepseek_api(prompt, data_summary)

def analyze_class_all(df_info, df_awards, df_activities, df_tasks, df_feedback, df_leaves):
    """分析全班整体情况"""
    
    # 计算任务完成率（修复语法错误）
    task_completion_rate = 0
    if len(df_tasks) > 0:
        task_completion_rate = len(df_tasks[df_tasks['完成状态'] == '已完成']) / len(df_tasks) * 100
    
    # 计算平均年龄（处理非数字情况）
    age_sum = 0
    age_count = 0
    for age_val in df_info['年龄']:
        if age_val and str(age_val).isdigit():
            age_sum += int(age_val)
            age_count += 1
    avg_age = age_sum / age_count if age_count > 0 else 0
    
    context = f"""
【班级概况】
- 总人数：{len(df_info)}人
- 男生：{len(df_info[df_info['性别']=='男'])}人，女生：{len(df_info[df_info['性别']=='女'])}人
- 平均年龄：{avg_age:.1f}岁

【家庭情况统计】
{df_info['家庭性质'].value_counts().to_dict()}

【荣誉统计】
- 总荣誉数：{len(df_awards)}项
- 获得荣誉人数：{df_awards['姓名'].nunique() if not df_awards.empty else 0}人
- 各级别荣誉分布：{df_awards['奖项级别'].value_counts().to_dict() if not df_awards.empty else '无'}

【活动参与统计】
- 总参与人次：{len(df_activities)}次
- 参与活动人数：{df_activities['姓名'].nunique() if not df_activities.empty else 0}人

【任务完成统计】
- 总任务数：{len(df_tasks)}项
- 完成率：{task_completion_rate:.1f}%

【请假统计】
- 总请假次数：{len(df_leaves)}次
"""
    
    prompt = """请根据以上班级数据，进行班级整体分析。请按以下格式输出：

## 🏫 班级整体画像
（一句话概括班级特点）

## ✅ 班级亮点
- 列出3-5个班级做得好的方面

## ⚠️ 需要关注的问题
- 列出2-3个需要改进的方面

## 💡 班主任工作建议
- 列出3-5条具体建议

## 🎯 本周班级目标
- 建议1-2个班级近期目标"""
    
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
        'ai_analysis': ['姓名', '学号', '分析时间', '分析结果']
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
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 基本信息", "🤖 AI成长画像", "🏆 我的荣誉", "📋 参加活动", "✅ 我的任务", "📝 每日反馈", "📋 请假申请"
    ])
    
    # ---------- Tab1: 学生基本信息 ----------
    with tab1:
        st.subheader("📋 我的基本信息")
        st.info("请认真填写以下信息，所有信息仅班主任可见，严格保密")
        
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
                family_type = st.selectbox("家庭性质", get_family_types(), 
                                          index=get_family_types().index(existing["家庭性质"].iloc[0]) if not existing.empty and existing["家庭性质"].iloc[0] in get_family_types() else 0, 
                                          key="info_familytype")
                family_members = st.number_input("家庭成员人数", min_value=1, max_value=20, value=existing_family_members, key="info_familymembers")
            
            with col2:
                st.markdown("**个人特质**")
                personality = st.selectbox("性格", get_personality_types(), 
                                          index=get_personality_types().index(existing["性格"].iloc[0]) if not existing.empty and existing["性格"].iloc[0] in get_personality_types() else 0,
                                          key="info_personality")
                hobby = st.text_area("爱好（可多项，用逗号分隔）", value=existing["爱好"].iloc[0] if not existing.empty else "", placeholder="例如：篮球, 阅读, 编程, 绘画", key="info_hobby")
                
                st.markdown("**学习情况**")
                academic_status = st.selectbox("文化课情况", get_academic_status(), 
                                              index=get_academic_status().index(existing["文化课情况"].iloc[0]) if not existing.empty and existing["文化课情况"].iloc[0] in get_academic_status() else 0,
                                              key="info_academic")
                professional_status = st.selectbox("专业课情况", get_professional_status(), 
                                                   index=get_professional_status().index(existing["专业课情况"].iloc[0]) if not existing.empty and existing["专业课情况"].iloc[0] in get_professional_status() else 0,
                                                   key="info_professional")
            
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
                        "姓名": student_name,
                        "学号": student_id,
                        "年龄": str(age),
                        "性别": gender,
                        "身份证号": id_card,
                        "电话号码": phone,
                        "户口本家庭地址": hometown_addr,
                        "实际常住家庭地址": current_addr,
                        "家庭性质": family_type,
                        "家庭成员人数": str(family_members),
                        "性格": personality,
                        "爱好": hobby,
                        "文化课情况": academic_status,
                        "专业课情况": professional_status,
                        "最后更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    df_info = pd.concat([df_info, new_row], ignore_index=True)
                
                save_data_csv(df_info, "student_info")
                st.success("基本信息已保存！")
        
        if not existing.empty:
            st.info("✅ 已填写基本信息，如需修改请直接修改后再次保存")
    
    # ---------- Tab2: AI成长画像 ----------
    with tab2:
        st.subheader("🤖 AI 成长画像分析")
        st.info("基于你填写的所有信息，AI 会为你生成个性化的成长分析报告")
        
        # 检查是否有足够的数据
        df_info = load_data_csv("student_info")
        has_info = not df_info[df_info["姓名"] == student_name].empty
        
        if not has_info:
            st.warning("⚠️ 请先在「基本信息」中填写你的个人资料，AI 才能为你生成精准的分析报告")
        else:
            # 检查是否有缓存的 AI 分析
            df_analysis = load_data_csv("ai_analysis")
            existing_analysis = df_analysis[df_analysis["姓名"] == student_name] if not df_analysis.empty else pd.DataFrame()
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 重新生成分析报告", key="refresh_analysis"):
                    st.session_state.analysis_trigger = True
            
            with col1:
                if not existing_analysis.empty and "analysis_trigger" not in st.session_state:
                    st.success(f"最近分析时间：{existing_analysis['分析时间'].iloc[0]}")
            
            if "analysis_trigger" in st.session_state and st.session_state.analysis_trigger:
                with st.spinner("AI 正在分析你的数据，请稍候..."):
                    analysis_result = analyze_student(student_name, student_id)
                    
                    # 保存分析结果
                    if not existing_analysis.empty:
                        idx = df_analysis[df_analysis["姓名"] == student_name].index[0]
                        df_analysis.at[idx, "分析时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        df_analysis.at[idx, "分析结果"] = analysis_result
                    else:
                        new_row = pd.DataFrame([{
                            "姓名": student_name,
                            "学号": student_id,
                            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "分析结果": analysis_result
                        }])
                        df_analysis = pd.concat([df_analysis, new_row], ignore_index=True)
                    
                    save_data_csv(df_analysis, "ai_analysis")
                    st.session_state.analysis_done = True
                    del st.session_state.analysis_trigger
                    st.rerun()
            
            # 显示分析结果
            if not existing_analysis.empty:
                analysis_result = existing_analysis["分析结果"].iloc[0]
                st.markdown(analysis_result)
            elif "analysis_done" in st.session_state:
                df_analysis = load_data_csv("ai_analysis")
                existing_analysis = df_analysis[df_analysis["姓名"] == student_name]
                if not existing_analysis.empty:
                    st.markdown(existing_analysis["分析结果"].iloc[0])
            else:
                st.info("点击「重新生成分析报告」按钮，AI 将为你生成专属成长分析")
    
    # ---------- Tab3: 我的荣誉 ----------
    with tab3:
        st.subheader("🏆 我的荣誉墙")
        st.info("记录你在学校、区、市、省等各级获得的奖项和荣誉")
        
        with st.form("add_award_form"):
            col1, col2 = st.columns(2)
            with col1:
                award_name = st.text_input("荣誉/奖项名称", placeholder="例如：数学竞赛一等奖、三好学生...", key="award_name")
                award_level = st.selectbox("荣誉级别", get_award_levels(), key="award_level")
            with col2:
                award_date = st.date_input("获奖日期", value=date.today(), key="award_date")
                remark = st.text_input("备注（可选）", placeholder="获奖说明或证书编号", key="award_remark")
            
            submitted = st.form_submit_button("➕ 添加荣誉")
            if submitted and award_name:
                df = load_data_csv("student_awards")
                new_row = pd.DataFrame([{
                    "姓名": student_name, 
                    "学号": student_id,
                    "奖项名称": award_name, 
                    "奖项级别": award_level,
                    "获奖时间": award_date.strftime("%Y-%m-%d"),
                    "备注": remark
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "student_awards")
                st.success(f"已添加荣誉：{award_name}")
                st.rerun()
        
        st.markdown("---")
        st.subheader("📜 我的荣誉记录")
        df_awards = load_data_csv("student_awards")
        if not df_awards.empty:
            my_awards = df_awards[df_awards["姓名"] == student_name]
            if not my_awards.empty:
                level_counts = my_awards.groupby("奖项级别").size()
                for level, count in level_counts.items():
                    st.write(f"• {level}：{count}项")
                st.dataframe(my_awards[["奖项名称", "奖项级别", "获奖时间", "备注"]], use_container_width=True)
            else:
                st.info("暂无荣誉记录")
        else:
            st.info("暂无荣誉记录")
    
    # ---------- Tab4: 参加活动 ----------
    with tab4:
        st.subheader("📋 可报名的活动")
        df_activities = load_data_csv("activities_published")
        df_my_activities = load_data_csv("student_activities")
        my_activity_names = df_my_activities[df_my_activities["姓名"] == student_name]["活动名称"].tolist() if not df_my_activities.empty else []
        
        if not df_activities.empty:
            has_available = False
            for idx, act in df_activities.iterrows():
                if act['活动名称'] in my_activity_names:
                    continue
                has_available = True
                with st.container():
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
            if not has_available:
                st.info("所有活动都已报名或暂无进行中的活动")
        else:
            st.info("暂无可报名的活动")
        
        with st.expander("📋 我已报名的活动"):
            if not df_my_activities.empty:
                my_acts = df_my_activities[df_my_activities["姓名"] == student_name]
                if not my_acts.empty:
                    st.dataframe(my_acts[["活动名称", "报名时间", "参与状态"]], use_container_width=True)
    
    # ---------- Tab5: 我的任务 ----------
    with tab5:
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
    
    # ---------- Tab6: 每日反馈 ----------
    with tab6:
        with st.form("daily_feedback_form"):
            mood = st.select_slider("今天心情", ["😔很差", "😐一般", "🙂不错", "😄非常好"], key="feedback_mood")
            study_status = st.selectbox("学习状态", ["很吃力", "有点吃力", "正常", "良好", "优秀"], key="feedback_study")
            feedback = st.text_area("想对老师说的话", placeholder="可以分享今天的收获、遇到的困难、需要的帮助...", key="feedback_text")
            submitted = st.form_submit_button("提交反馈")
            if submitted:
                df = load_data_csv("daily_feedback")
                new_row = pd.DataFrame([{
                    "姓名": student_name, "学号": student_id,
                    "心情": mood, "学习状态": study_status, "反馈内容": feedback,
                    "日期": date.today().strftime("%Y-%m-%d"), "时间": datetime.now().strftime("%H:%M:%S")
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "daily_feedback")
                st.success("反馈已提交")
    
    # ---------- Tab7: 请假申请 ----------
    with tab7:
        with st.form("leave_form_student"):
            col1, col2 = st.columns(2)
            with col1:
                leave_date = st.date_input("请假日期", value=date.today(), key="leave_date")
                periods = st.multiselect("请假节次", ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "全天"], key="leave_periods")
            with col2:
                reason = st.text_area("请假事由", key="leave_reason")
            submitted = st.form_submit_button("提交申请")
            if submitted and periods:
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
    st.header("📊 教师成长平台管理")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "👥 学生名单", "📋 学生基本信息", "🤖 AI综合分析", "📋 发布活动", "🏆 学生荣誉", "📊 任务与反馈", "📋 请假审批", "📥 数据导出"
    ])
    
    # Tab1: 学生名单
    with tab1:
        st.subheader("学生名单管理（登录凭证）")
        uploaded = st.file_uploader("上传学生名单（Excel：姓名、学号两列）", type=["xlsx"], key="upload_list")
        if uploaded:
            df = pd.read_excel(uploaded, engine='openpyxl', dtype=str).fillna("")
            df.to_excel(STUDENT_LIST_FILE, index=False)
            st.success(f"已更新，共{len(df)}人")
            st.rerun()
        
        if os.path.exists(STUDENT_LIST_FILE):
            df = pd.read_excel(STUDENT_LIST_FILE, engine='openpyxl', dtype=str).fillna("")
            st.dataframe(df, use_container_width=True)
            
            with st.expander("手动添加"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("姓名", key="add_name")
                with col2:
                    new_id = st.text_input("学号", key="add_id")
                if st.button("添加", key="add_btn"):
                    if new_name and new_id:
                        new_row = pd.DataFrame([{"姓名": new_name, "学号": new_id}])
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_excel(STUDENT_LIST_FILE, index=False)
                        st.rerun()
    
    # Tab2: 学生基本信息
    with tab2:
        st.subheader("📋 学生基本信息档案")
        st.info("学生自主填写的基本信息，请妥善保管，严格保密")
        
        df_info = load_data_csv("student_info")
        if not df_info.empty:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("已填写学生数", len(df_info))
            col2.metric("男生", len(df_info[df_info["性别"] == "男"]))
            col3.metric("女生", len(df_info[df_info["性别"] == "女"]))
            avg_age = df_info[df_info["年龄"].str.isdigit()]["年龄"].astype(float).mean() if len(df_info[df_info["年龄"].str.isdigit()]) > 0 else 0
            col4.metric("平均年龄", f"{avg_age:.1f}")
            
            st.subheader("家庭性质分布")
            family_counts = df_info["家庭性质"].value_counts()
            st.bar_chart(family_counts)
            
            st.subheader("详细信息")
            st.dataframe(df_info, use_container_width=True)
            
            csv_data = df_info.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出学生基本信息", csv_data, "学生基本信息.csv", "text/csv", key="export_info")
        else:
            st.info("暂无学生填写基本信息")
    
    # Tab3: AI 综合分析
    with tab3:
        st.subheader("🤖 AI 班级综合分析")
        st.info("AI 会根据全班学生的所有数据，生成班级整体画像和分析建议")
        
        # 加载所有数据
        df_info = load_data_csv("student_info")
        df_awards = load_data_csv("student_awards")
        df_activities = load_data_csv("student_activities")
        df_tasks = load_data_csv("student_tasks")
        df_feedback = load_data_csv("daily_feedback")
        df_leaves = load_data_csv("leaves")
        
        if df_info.empty:
            st.warning("暂无学生基本信息，请等待学生填写后进行分析")
        else:
            # 生成班级整体分析
            if st.button("🔍 生成班级综合分析报告", key="class_analysis_btn"):
                with st.spinner("AI 正在分析班级整体情况，请稍候..."):
                    class_analysis = analyze_class_all(df_info, df_awards, df_activities, df_tasks, df_feedback, df_leaves)
                    st.session_state.class_analysis_result = class_analysis
            
            if "class_analysis_result" in st.session_state:
                st.markdown(st.session_state.class_analysis_result)
            else:
                st.info("点击「生成班级综合分析报告」按钮，AI 将分析全班数据")
        
        st.divider()
        st.subheader("👤 学生个人 AI 画像（可点开展开查看）")
        
        # 显示每个学生的 AI 分析
        df_analysis = load_data_csv("ai_analysis")
        student_list = load_student_list()
        
        if not student_list.empty:
            for _, student in student_list.iterrows():
                name = student["姓名"]
                student_analysis = df_analysis[df_analysis["姓名"] == name] if not df_analysis.empty else pd.DataFrame()
                
                with st.expander(f"📊 {name} 的 AI 成长画像"):
                    if not student_analysis.empty:
                        st.markdown(student_analysis["分析结果"].iloc[0])
                        st.caption(f"分析时间：{student_analysis['分析时间'].iloc[0]}")
                    else:
                        st.info(f"{name} 尚未生成 AI 分析，请该学生登录后点击「生成分析报告」")
                        
                        # 教师可以手动触发生成
                        if st.button(f"为 {name} 生成分析报告", key=f"gen_{name}"):
                            with st.spinner(f"正在为 {name} 生成分析报告..."):
                                # 获取学生ID
                                sid = student["学号"] if "学号" in student else name
                                analysis = analyze_student(name, str(sid))
                                
                                # 保存
                                if not df_analysis.empty:
                                    existing = df_analysis[df_analysis["姓名"] == name]
                                    if not existing.empty:
                                        idx = df_analysis[df_analysis["姓名"] == name].index[0]
                                        df_analysis.at[idx, "分析结果"] = analysis
                                        df_analysis.at[idx, "分析时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    else:
                                        new_row = pd.DataFrame([{
                                            "姓名": name, "学号": str(sid),
                                            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            "分析结果": analysis
                                        }])
                                        df_analysis = pd.concat([df_analysis, new_row], ignore_index=True)
                                else:
                                    new_row = pd.DataFrame([{
                                        "姓名": name, "学号": str(sid),
                                        "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "分析结果": analysis
                                    }])
                                    df_analysis = pd.concat([df_analysis, new_row], ignore_index=True)
                                
                                save_data_csv(df_analysis, "ai_analysis")
                                st.success(f"已为 {name} 生成分析报告")
                                st.rerun()
    
    # Tab4: 发布活动
    with tab4:
        st.subheader("发布活动（学生可选择报名参加）")
        df = load_data_csv("activities_published")
        
        with st.form("publish_activity_form"):
            col1, col2 = st.columns(2)
            with col1:
                act_name = st.text_input("活动名称", key="act_name")
                act_desc = st.text_area("活动描述", key="act_desc")
            with col2:
                deadline = st.date_input("报名截止日期", value=date.today(), key="act_deadline")
                status = st.selectbox("状态", ["进行中", "已结束"], key="act_status")
            if st.form_submit_button("发布活动") and act_name:
                new_row = pd.DataFrame([{
                    "活动名称": act_name, "活动描述": act_desc,
                    "发布时间": datetime.now().strftime("%Y-%m-%d"),
                    "截止时间": deadline.strftime("%Y-%m-%d"), "状态": status
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "activities_published")
                st.success(f"已发布：{act_name}")
                st.rerun()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            df_signups = load_data_csv("student_activities")
            if not df_signups.empty:
                with st.expander("📋 报名情况"):
                    for act in df['活动名称']:
                        signups = df_signups[df_signups['活动名称'] == act]
                        if not signups.empty:
                            st.write(f"**{act}**：{len(signups)}人报名")
                            st.dataframe(signups[["姓名", "报名时间"]], use_container_width=True)
    
    # Tab5: 学生荣誉
    with tab5:
        st.subheader("🏆 学生荣誉墙")
        df_awards = load_data_csv("student_awards")
        if not df_awards.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("总荣誉数", len(df_awards))
            col2.metric("获得荣誉学生数", df_awards["姓名"].nunique())
            col3.metric("最高级别", df_awards["奖项级别"].max() if not df_awards.empty else "无")
            
            level_counts = df_awards["奖项级别"].value_counts()
            st.bar_chart(level_counts)
            
            student_counts = df_awards.groupby("姓名").size().sort_values(ascending=False).head(10)
            st.bar_chart(student_counts)
            
            st.dataframe(df_awards, use_container_width=True)
        else:
            st.info("暂无学生荣誉记录")
    
    # Tab6: 任务与反馈
    with tab6:
        st.subheader("任务完成情况")
        df_tasks = load_data_csv("student_tasks")
        if not df_tasks.empty:
            task_stats = df_tasks.groupby(["任务名称", "完成状态"]).size().reset_index(name='人数')
            st.dataframe(task_stats, use_container_width=True)
            st.dataframe(df_tasks, use_container_width=True)
        else:
            st.info("暂无任务数据")
        
        st.divider()
        st.subheader("每日反馈")
        df_feedback = load_data_csv("daily_feedback")
        if not df_feedback.empty:
            dates = sorted(df_feedback["日期"].unique(), reverse=True)
            selected_date = st.selectbox("筛选日期", ["全部"] + list(dates), key="feedback_date")
            if selected_date != "全部":
                df_feedback = df_feedback[df_feedback["日期"] == selected_date]
            st.dataframe(df_feedback, use_container_width=True)
        else:
            st.info("暂无反馈数据")
    
    # Tab7: 请假审批
    with tab7:
        st.subheader("请假审批")
        df = load_data_csv("leaves")
        if not df.empty:
            pending = df[df["预审状态"] == "待审批"]
            if not pending.empty:
                for idx in pending.index:
                    row = df.loc[idx]
                    with st.expander(f"{row['姓名']} - {row['请假日期']} 请假{row['节次']}"):
                        st.write(f"**事由：** {row['事由']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            new_status = st.selectbox("审批结果", ["已批准", "已拒绝"], key=f"leave_status_{idx}")
                        with col2:
                            comment = st.text_input("班主任意见", key=f"leave_comment_{idx}")
                        if st.button("确认审批", key=f"leave_approve_{idx}"):
                            df.loc[idx, "预审状态"] = str(new_status)
                            df.loc[idx, "班主任意见"] = str(comment)
                            save_data_csv(df, "leaves")
                            st.success("已处理")
                            st.rerun()
            else:
                st.info("暂无待审批请假")
            
            with st.expander("全部请假记录"):
                st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无请假记录")
    
    # Tab8: 数据导出
    with tab8:
        st.subheader("📥 数据导出")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename in os.listdir(DATA_FOLDER):
                if filename.endswith('.csv'):
                    filepath = os.path.join(DATA_FOLDER, filename)
                    zip_file.write(filepath, filename)
        
        zip_buffer.seek(0)
        st.download_button(
            label="📦 一键导出全部数据 (ZIP压缩包)",
            data=zip_buffer,
            file_name=f"班级数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="export_all"
        )
        
        st.info("导出后可用Excel打开CSV文件查看所有数据")

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
