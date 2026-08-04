import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import zipfile
import io
import re

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

# ========== 根据身份证计算年龄 ==========
def calculate_age(id_card):
    if not id_card or len(str(id_card)) < 18:
        return ""
    try:
        id_str = str(id_card).strip()
        if len(id_str) != 18:
            return ""
        birth_str = id_str[6:14]
        birth_date = datetime.strptime(birth_str, "%Y%m%d")
        today = datetime.now()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return str(age)
    except:
        return ""

# ========== 预设选项 ==========
def get_gender_options():
    return ["男", "女"]

def get_nation_options():
    return ["汉族", "蒙古族", "回族", "藏族", "维吾尔族", "苗族", "彝族", "壮族", "布依族", "朝鲜族", "满族", "侗族", "瑶族", "白族", "土家族", "哈尼族", "哈萨克族", "傣族", "黎族", "傈僳族", "佤族", "畲族", "高山族", "拉祜族", "水族", "东乡族", "纳西族", "景颇族", "柯尔克孜族", "土族", "达斡尔族", "仫佬族", "羌族", "布朗族", "撒拉族", "毛南族", "仡佬族", "锡伯族", "阿昌族", "普米族", "塔吉克族", "怒族", "乌孜别克族", "俄罗斯族", "鄂温克族", "德昂族", "保安族", "裕固族", "京族", "塔塔尔族", "独龙族", "鄂伦春族", "赫哲族", "门巴族", "珞巴族", "基诺族", "其他"]

def get_family_type_options():
    return ["原生家庭完整", "单亲家庭（父母离异）", "单亲家庭（父母一方去世）", "后组合家庭", "孤儿（父母去世）"]

def get_family_member_options():
    return ["爸爸", "妈妈", "爷爷", "奶奶", "外公", "外婆", "哥哥", "姐姐", "弟弟", "妹妹", "其他"]

def get_sibling_types():
    return ["哥哥", "姐姐", "弟弟", "妹妹", "其他"]

def get_education_method_options():
    return ["专制粗暴", "民主平等", "漠不关心", "非常宠爱", "无法评价"]

def get_leave_behind_options():
    return ["是", "否"]

def get_parent_work_options():
    return ["爸爸外地工作", "妈妈外地工作", "爸爸妈妈均外地工作"]

def get_future_plan_options():
    return ["升学", "就业", "其他"]

def get_disease_options():
    return [
        "精神分裂", "抑郁症", "焦虑症", "躁郁症", "强迫症", "多动症", "自闭症",
        "肺结核", "乙肝", "艾滋病", "梅毒", "其他性病",
        "癫痫", "心脏病", "哮喘", "糖尿病", "肾炎", "血液病",
        "高度近视", "脊柱侧弯", "骨折史", "脑震荡史",
        "其他重大疾病"
    ]

def get_score_directions():
    return ["学习", "纪律", "卫生", "活动", "品德", "其他"]

def get_score_sources():
    return ["班长", "副班长", "学习委员", "文体委员", "卫生防疫员"]

def get_score_periods():
    return ["日", "周", "月", "一次性"]

def get_award_levels():
    return ["班级", "校级", "区级", "市级", "省级", "国家级", "国际级"]

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
    df_info = load_data_csv("student_info_new")
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
    
    if not df_scores.empty:
        student_scores = df_scores[df_scores["当事人"].str.contains(student_name, na=False)]
    else:
        student_scores = pd.DataFrame()

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
- 姓名：{info.get('姓名', '未填')}
- 性别：{info.get('性别', '未填')}
- 民族：{info.get('民族', '未填')}
- 特长或爱好：{info.get('特长爱好', '未填')}
- 性格特点：{info.get('性格特点', '未填')}
- 身份证号码：{info.get('身份证号', '未填')}
- 年龄：{info.get('年龄', '未填')}岁
- 手机号码：{info.get('手机号', '未填')}
- 初中毕业学校：{info.get('初中毕业学校', '未填')}
- 中考总分：{info.get('中考总分', '未填')}
- 有无初中毕业证：{info.get('有无初中毕业证', '未填')}
- 常住地址：{info.get('常住地址', '未填')}
- 户籍地址：{info.get('户籍地址', '未填')}

【家庭情况】
- 家庭基本情况：{info.get('家庭基本情况', '未填')}
- 家庭成员：{info.get('家庭成员', '未填')}
- 家庭教育方法：{info.get('家庭教育方法', '未填')}
- 兄弟姐妹信息：{info.get('兄弟姐妹信息', '无')}
- 是否留守：{info.get('是否留守', '未填')}
- 父母工作情况：{info.get('父母工作情况', '未填')}

【监护人信息】
- 爸爸姓名：{info.get('爸爸姓名', '无')}
- 爸爸身份证号码：{info.get('爸爸身份证号', '无')}
- 爸爸常用联系电话：{info.get('爸爸联系电话', '无')}
- 妈妈姓名：{info.get('妈妈姓名', '无')}
- 妈妈身份证号码：{info.get('妈妈身份证号', '无')}
- 妈妈常用联系电话：{info.get('妈妈联系电话', '无')}
- 其他监护人姓名：{info.get('其他监护人姓名', '无')}
- 其他监护人和本人关系：{info.get('其他监护人和本人关系', '无')}
- 其他监护人身份证号码：{info.get('其他监护人身份证号', '无')}
- 其他监护人联系电话：{info.get('其他监护人联系电话', '无')}

【个人发展】
- 选择农村电气技术（计算机方向）专业的原因：{info.get('选择专业原因', '未填')}
- 你对未来的打算：{info.get('未来打算', '未填')}
- 曾在班上担任什么职务：{info.get('曾任职务', '未填')}
- 曾经是否患过什么大病：{info.get('曾患疾病', '无')}
- 现在是否患过什么大病：{info.get('现患疾病', '无')}
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
            tasks_summary + score_summary + "请结合以上所有信息，对学生的综合情况进行评价和建议。")

def analyze_student(student_name, student_id):
    data_summary = get_student_full_data(student_name, student_id)
    prompt = """请根据以上数据，按以下格式生成学生成长画像：
## 📊 学生画像总览
## 🌟 优势与闪光点
## 📈 成长建议
## 💡 特别关注
## 🎯 近期目标
## 💌 老师的鼓励
请重点关注学生的家庭背景、心理健康状况和个人发展规划。"""
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
【量化管理】班级总量化分：{total_score:.1f}分
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
        'student_info_new': ['姓名', '性别', '民族', '特长爱好', '性格特点', '身份证号', '年龄', '手机号',
                            '初中毕业学校', '中考总分', '有无初中毕业证', '常住地址', '户籍地址',
                            '家庭基本情况', '家庭成员', '家庭教育方法', '兄弟姐妹信息', '是否留守',
                            '父母工作情况', '爸爸姓名', '爸爸身份证号', '爸爸联系电话',
                            '妈妈姓名', '妈妈身份证号', '妈妈联系电话',
                            '其他监护人姓名', '其他监护人和本人关系', '其他监护人身份证号', '其他监护人联系电话',
                            '选择专业原因', '未来打算', '曾任职务', '曾患疾病', '现患疾病', '最后更新时间'],
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
    
    # ==================== Tab1: 学生基本信息（35项完整版） ====================
    with tab1:
        st.subheader("📋 学生基本信息档案")
        st.info("请认真填写以下信息，所有信息仅班主任可见，严格保密")
        
        df_info = load_data_csv("student_info_new")
        existing = df_info[df_info["姓名"] == student_name] if not df_info.empty else pd.DataFrame()
        
        existing_data = {}
        if not existing.empty:
            for col in existing.columns:
                existing_data[col] = existing.iloc[0][col] if pd.notna(existing.iloc[0][col]) else ""
        
        # 用于存储表单数据
        form_data = {}
        
        with st.form("student_info_form_35", clear_on_submit=False):
            st.markdown("---")
            st.markdown("### 📌 基本信息")
            
            # 1. 姓名
            name = st.text_input("1. 姓名", value=student_name, disabled=True, key="f1_name")
            form_data["姓名"] = name
            
            # 2. 性别（下拉框）
            gender = st.selectbox("2. 性别", get_gender_options(), 
                                 index=get_gender_options().index(existing_data.get("性别", "男")) if existing_data.get("性别") in get_gender_options() else 0,
                                 key="f2_gender")
            form_data["性别"] = gender
            
            # 3. 民族（下拉框）
            nation_idx = get_nation_options().index(existing_data.get("民族", "汉族")) if existing_data.get("民族") in get_nation_options() else 0
            nation = st.selectbox("3. 民族", get_nation_options(), index=nation_idx, key="f3_nation")
            form_data["民族"] = nation
            
            # 4. 特长或爱好
            hobby = st.text_input("4. 特长或爱好", value=existing_data.get("特长爱好", ""), key="f4_hobby")
            form_data["特长爱好"] = hobby
            
            # 5. 性格特点
            personality = st.text_input("5. 性格特点", value=existing_data.get("性格特点", ""), key="f5_personality")
            form_data["性格特点"] = personality
            
            # 6. 身份证号码
            id_card = st.text_input("6. 身份证号码", value=existing_data.get("身份证号", ""), key="f6_idcard", placeholder="请输入18位身份证号码")
            form_data["身份证号"] = id_card
            
            # 7. 年龄（自动计算，灰色不可编辑）
            if id_card and len(str(id_card)) >= 18:
                auto_age = calculate_age(id_card)
                age = st.text_input("7. 年龄（自动计算）", value=auto_age, disabled=True, key="f7_age")
                if auto_age and auto_age != existing_data.get("年龄", ""):
                    st.info(f"✅ 根据身份证计算年龄为：{auto_age}岁")
            else:
                age = st.text_input("7. 年龄（自动计算）", value=existing_data.get("年龄", ""), disabled=True, key="f7_age")
                if id_card and len(str(id_card)) < 18:
                    st.warning("⚠️ 请输入完整的18位身份证号以自动计算年龄")
            form_data["年龄"] = age
            
            # 8. 手机号码
            phone = st.text_input("8. 手机号码", value=existing_data.get("手机号", ""), key="f8_phone")
            form_data["手机号"] = phone
            
            # 9. 初中毕业学校
            middle_school = st.text_input("9. 初中毕业学校", value=existing_data.get("初中毕业学校", ""), key="f9_middle")
            form_data["初中毕业学校"] = middle_school
            
            # 10. 中考总分
            exam_score = st.text_input("10. 中考总分", value=existing_data.get("中考总分", ""), key="f10_exam")
            form_data["中考总分"] = exam_score
            
            # 11. 有无初中毕业证
            cert = st.selectbox("11. 有无初中毕业证", ["有", "无"], 
                               index=0 if existing_data.get("有无初中毕业证", "有") == "有" else 1,
                               key="f11_cert")
            form_data["有无初中毕业证"] = cert
            
            # 12. 常住地址
            address = st.text_area("12. 常住地址", value=existing_data.get("常住地址", ""), key="f12_address", height=68)
            form_data["常住地址"] = address
            
            # 13. 户籍地址
            hometown = st.text_area("13. 户籍地址（身份证或户口本地址）", value=existing_data.get("户籍地址", ""), key="f13_hometown", height=68)
            form_data["户籍地址"] = hometown
            
            st.markdown("---")
            st.markdown("### 👨‍👩‍👧‍👦 家庭情况")
            
            # 14. 家庭基本情况（单选）
            family_type = st.radio("14. 家庭基本情况", get_family_type_options(),
                                   index=get_family_type_options().index(existing_data.get("家庭基本情况", "原生家庭完整")) if existing_data.get("家庭基本情况") in get_family_type_options() else 0,
                                   key="f14_family_type")
            form_data["家庭基本情况"] = family_type
            
            # 15. 家庭成员（多选）
            family_members = st.multiselect("15. 家庭成员", get_family_member_options(),
                                           default=existing_data.get("家庭成员", "").split(",") if existing_data.get("家庭成员") else [],
                                           key="f15_family_members")
            form_data["家庭成员"] = ",".join(family_members) if family_members else ""
            
            # 16. 家庭教育方法（多选）
            edu_methods = st.multiselect("16. 家庭教育方法", get_education_method_options(),
                                        default=existing_data.get("家庭教育方法", "").split(",") if existing_data.get("家庭教育方法") else [],
                                        key="f16_edu_methods")
            form_data["家庭教育方法"] = ",".join(edu_methods) if edu_methods else ""
            
            # 17. 兄弟姐妹信息（条件显示）
            sibling_types = ["哥哥", "姐姐", "弟弟", "妹妹", "其他"]
            has_siblings = any(m in family_members for m in sibling_types)
            
            sibling_info = ""
            if has_siblings:
                st.info("📌 您选择了有兄弟姐妹，请填写以下信息：")
                sibling_data = existing_data.get("兄弟姐妹信息", "")
                sibling_list = []
                if sibling_data:
                    try:
                        for item in sibling_data.split(","):
                            if "|" in item:
                                parts = item.split("|")
                                if len(parts) == 3:
                                    sibling_list.append({"姓名": parts[0].strip(), "关系": parts[1].strip(), "年龄": parts[2].strip()})
                    except:
                        pass
                
                if sibling_list:
                    st.write("已记录的兄弟姐妹：")
                    for i, sib in enumerate(sibling_list):
                        st.write(f"  - {sib['姓名']}（{sib['关系']}，{sib['年龄']}岁）")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    sib_name = st.text_input("姓名", key="sib_name")
                with col2:
                    sib_relation = st.selectbox("关系", get_sibling_types(), key="sib_relation")
                with col3:
                    sib_age = st.text_input("年龄", key="sib_age")
                
                if st.button("➕ 添加兄弟姐妹", key="add_sibling"):
                    if sib_name and sib_relation and sib_age:
                        new_sib = f"{sib_name}|{sib_relation}|{sib_age}"
                        sibling_list.append({"姓名": sib_name, "关系": sib_relation, "年龄": sib_age})
                        st.success(f"已添加：{sib_name}（{sib_relation}，{sib_age}岁）")
                        st.rerun()
                
                if sibling_list:
                    sibling_info = ",".join([f"{s['姓名']}|{s['关系']}|{s['年龄']}" for s in sibling_list])
            else:
                sibling_info = "无兄弟姐妹"
                st.info("未选择兄弟姐妹，跳过此项")
            form_data["兄弟姐妹信息"] = sibling_info
            
            # 18. 是否留守（单选）
            leave_behind = st.radio("18. 是否留守", get_leave_behind_options(),
                                   index=0 if existing_data.get("是否留守", "否") == "否" else 1,
                                   key="f18_leave")
            form_data["是否留守"] = leave_behind
            
            # 19. 父母工作情况（条件显示）
            parent_work = ""
            if leave_behind == "是":
                has_father = "爸爸" in family_members
                has_mother = "妈妈" in family_members
                if has_father or has_mother:
                    parent_work = st.selectbox("19. 父母工作情况", get_parent_work_options(),
                                              index=get_parent_work_options().index(existing_data.get("父母工作情况", "爸爸外地工作")) if existing_data.get("父母工作情况") in get_parent_work_options() else 0,
                                              key="f19_parent_work")
                else:
                    st.warning("⚠️ 您选择了留守，但家庭成员中未选择爸爸或妈妈，请补充家庭成员信息")
                    parent_work = st.selectbox("19. 父母工作情况", get_parent_work_options(), disabled=True, key="f19_parent_work_disabled")
            else:
                parent_work = st.selectbox("19. 父母工作情况", get_parent_work_options(), disabled=True, key="f19_parent_work_disabled")
                st.info("未选择留守，此项不可编辑")
            form_data["父母工作情况"] = parent_work
            
            st.markdown("---")
            st.markdown("### 📞 监护人信息")
            
            # 20-22. 爸爸信息（条件显示）
            if "爸爸" in family_members:
                st.markdown("**👨 爸爸信息**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    dad_name = st.text_input("20. 爸爸姓名", value=existing_data.get("爸爸姓名", ""), key="f20_dad_name")
                with col2:
                    dad_id = st.text_input("21. 爸爸身份证号码", value=existing_data.get("爸爸身份证号", ""), key="f21_dad_id")
                with col3:
                    dad_phone = st.text_input("22. 爸爸常用联系电话", value=existing_data.get("爸爸联系电话", ""), key="f22_dad_phone")
            else:
                dad_name = st.text_input("20. 爸爸姓名", value="", disabled=True, key="f20_dad_name_disabled")
                dad_id = st.text_input("21. 爸爸身份证号码", value="", disabled=True, key="f21_dad_id_disabled")
                dad_phone = st.text_input("22. 爸爸常用联系电话", value="", disabled=True, key="f22_dad_phone_disabled")
                st.info("未选择爸爸，此项不可编辑")
            form_data["爸爸姓名"] = dad_name
            form_data["爸爸身份证号"] = dad_id
            form_data["爸爸联系电话"] = dad_phone
            
            # 23-25. 妈妈信息（条件显示）
            if "妈妈" in family_members:
                st.markdown("**👩 妈妈信息**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    mom_name = st.text_input("23. 妈妈姓名", value=existing_data.get("妈妈姓名", ""), key="f23_mom_name")
                with col2:
                    mom_id = st.text_input("24. 妈妈身份证号码", value=existing_data.get("妈妈身份证号", ""), key="f24_mom_id")
                with col3:
                    mom_phone = st.text_input("25. 妈妈常用联系电话", value=existing_data.get("妈妈联系电话", ""), key="f25_mom_phone")
            else:
                mom_name = st.text_input("23. 妈妈姓名", value="", disabled=True, key="f23_mom_name_disabled")
                mom_id = st.text_input("24. 妈妈身份证号码", value="", disabled=True, key="f24_mom_id_disabled")
                mom_phone = st.text_input("25. 妈妈常用联系电话", value="", disabled=True, key="f25_mom_phone_disabled")
                st.info("未选择妈妈，此项不可编辑")
            form_data["妈妈姓名"] = mom_name
            form_data["妈妈身份证号"] = mom_id
            form_data["妈妈联系电话"] = mom_phone
            
            # 26-29. 其他监护人信息（条件显示）
            has_other_guardian = any(m not in ["爸爸", "妈妈"] for m in family_members)
            if has_other_guardian:
                st.markdown("**👤 其他监护人信息**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    other_name = st.text_input("26. 其他监护人姓名", value=existing_data.get("其他监护人姓名", ""), key="f26_other_name")
                with col2:
                    other_relation = st.text_input("27. 其他监护人和本人关系", value=existing_data.get("其他监护人和本人关系", ""), key="f27_other_relation")
                with col3:
                    other_id = st.text_input("28. 其他监护人身份证号码", value=existing_data.get("其他监护人身份证号", ""), key="f28_other_id")
                with col4:
                    other_phone = st.text_input("29. 其他监护人联系电话", value=existing_data.get("其他监护人联系电话", ""), key="f29_other_phone")
            else:
                other_name = st.text_input("26. 其他监护人姓名", value="", disabled=True, key="f26_other_name_disabled")
                other_relation = st.text_input("27. 其他监护人和本人关系", value="", disabled=True, key="f27_other_relation_disabled")
                other_id = st.text_input("28. 其他监护人身份证号码", value="", disabled=True, key="f28_other_id_disabled")
                other_phone = st.text_input("29. 其他监护人联系电话", value="", disabled=True, key="f29_other_phone_disabled")
                st.info("未选择除父母外的其他监护人，此项不可编辑")
            form_data["其他监护人姓名"] = other_name
            form_data["其他监护人和本人关系"] = other_relation
            form_data["其他监护人身份证号"] = other_id
            form_data["其他监护人联系电话"] = other_phone
            
            st.markdown("---")
            st.markdown("### 🎯 个人发展")
            
            # 30. 选择农村电气技术（计算机方向）专业的原因
            reason = st.text_area("30. 选择农村电气技术（计算机方向）专业的原因", 
                                  value=existing_data.get("选择专业原因", ""), 
                                  key="f30_reason", height=68)
            form_data["选择专业原因"] = reason
            
            # 31. 你对未来的打算（单选）
            future_plan = st.radio("31. 你对未来的打算", get_future_plan_options(),
                                  index=get_future_plan_options().index(existing_data.get("未来打算", "升学")) if existing_data.get("未来打算") in get_future_plan_options() else 0,
                                  key="f31_future")
            form_data["未来打算"] = future_plan
            
            # 32. 曾在班上担任什么职务
            position = st.text_input("32. 曾在班上担任什么职务", value=existing_data.get("曾任职务", ""), key="f32_position")
            form_data["曾任职务"] = position
            
            # 33. 曾经是否患过什么大病（多选）
            st.caption("💡 可选择多项，选中的疾病表示曾经患过")
            past_diseases = st.multiselect("33. 曾经是否患过什么大病", get_disease_options(),
                                          default=existing_data.get("曾患疾病", "").split(",") if existing_data.get("曾患疾病") else [],
                                          key="f33_past_diseases")
            form_data["曾患疾病"] = ",".join(past_diseases) if past_diseases else ""
            
            # 34. 现在是否患过什么大病
