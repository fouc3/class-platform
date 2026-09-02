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
USE_AI = False

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

# ---------- AI 分析函数（暂时关闭） ----------
def call_deepseek_api(prompt, context):
    return "【AI功能已关闭】系统管理员已暂时关闭智能评价系统。"

def get_student_full_data(student_name, student_id):
    return "【AI功能已关闭】"

def analyze_student(student_name, student_id):
    return "【AI功能已关闭】"

def analyze_class_all(df_info, df_awards, df_activities, df_tasks, df_feedback, df_leaves, df_scores):
    return "【AI功能已关闭】"

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
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 基本信息", "📊 我的量化分", "🏆 我的荣誉", 
        "📋 参加活动", "✅ 我的任务", "📝 每日反馈", "📋 请假申请"
    ])
    
    # ==================== Tab1: 学生基本信息 ====================
    with tab1:
        st.subheader("📋 学生基本信息档案")
        st.info("请认真填写以下信息，所有信息仅班主任可见，严格保密")
        
        df_info = load_data_csv("student_info_new")
        existing = df_info[df_info["姓名"] == student_name] if not df_info.empty else pd.DataFrame()
        
        existing_data = {}
        if not existing.empty:
            for col in existing.columns:
                existing_data[col] = existing.iloc[0][col] if pd.notna(existing.iloc[0][col]) else ""
        
        if f"f1_name_{student_name}" not in st.session_state:
            st.session_state[f"f1_name_{student_name}"] = student_name
        if f"f6_idcard_{student_name}" not in st.session_state:
            st.session_state[f"f6_idcard_{student_name}"] = existing_data.get("身份证号", "")
        if f"f7_age_{student_name}" not in st.session_state:
            st.session_state[f"f7_age_{student_name}"] = existing_data.get("年龄", "")
        if f"f8_phone_{student_name}" not in st.session_state:
            st.session_state[f"f8_phone_{student_name}"] = existing_data.get("手机号", "")
        
        st.markdown("---")
        st.markdown("### 📌 基本信息")
        
        st.text_input("1. 姓名", value=student_name, disabled=True, key=f"f1_name_{student_name}")
        
        gender_idx = get_gender_options().index(existing_data.get("性别", "男")) if existing_data.get("性别") in get_gender_options() else 0
        st.selectbox("2. 性别", get_gender_options(), index=gender_idx, key=f"f2_gender_{student_name}")
        
        nation_idx = get_nation_options().index(existing_data.get("民族", "汉族")) if existing_data.get("民族") in get_nation_options() else 0
        st.selectbox("3. 民族", get_nation_options(), index=nation_idx, key=f"f3_nation_{student_name}")
        
        st.text_input("4. 特长或爱好", value=existing_data.get("特长爱好", ""), key=f"f4_hobby_{student_name}")
        st.text_input("5. 性格特点", value=existing_data.get("性格特点", ""), key=f"f5_personality_{student_name}")
        
        st.markdown("**6. 身份证号码**")
        current_id = st.session_state.get(f"f6_idcard_{student_name}", existing_data.get("身份证号", ""))
        
        def update_age():
            id_val = st.session_state.get(f"f6_idcard_{student_name}", "")
            if id_val:
                id_clean = id_val.strip().upper()
                if len(id_clean) == 18 and id_clean[:17].isdigit() and id_clean[17] in "0123456789X":
                    try:
                        weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
                        check_code = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
                        total = 0
                        for i in range(17):
                            total += int(id_clean[i]) * weight[i]
                        if check_code[total % 11] == id_clean[17]:
                            birth_str = id_clean[6:14]
                            birth_date = datetime.strptime(birth_str, "%Y%m%d")
                            today = datetime.now()
                            age = today.year - birth_date.year
                            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                                age -= 1
                            st.session_state[f"f7_age_{student_name}"] = str(age)
                            return
                    except:
                        pass
            st.session_state[f"f7_age_{student_name}"] = ""
        
        id_card_input = st.text_input(
            "身份证号码", 
            value=current_id, 
            key=f"f6_idcard_{student_name}", 
            placeholder="请输入18位身份证号码（最后一位可能是数字或X）",
            label_visibility="collapsed",
            on_change=update_age
        )
        
        if id_card_input:
            id_card_clean = id_card_input.strip().upper()
            id_len = len(id_card_clean)
            if id_len < 18:
                st.error(f"⚠️ 当前已输入 {id_len} 位，身份证号码需要18位")
            elif id_len > 18:
                st.error(f"⚠️ 当前已输入 {id_len} 位，身份证号码只能18位")
            elif not id_card_clean[:17].isdigit():
                st.error("❌ 身份证号码前17位必须为数字")
            elif id_card_clean[17] not in "0123456789X":
                st.error("❌ 身份证号码最后一位只能为数字或字母X")
            else:
                try:
                    weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
                    check_code = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
                    total = 0
                    for i in range(17):
                        total += int(id_card_clean[i]) * weight[i]
                    if check_code[total % 11] != id_card_clean[17]:
                        st.error("❌ 身份证号码校验位错误，请核对")
                    else:
                        st.success("✅ 身份证号码验证通过")
                except:
                    st.error("❌ 身份证号码格式错误")
        else:
            st.caption("💡 请填写18位身份证号码，填写后自动计算年龄")
        
        st.markdown("**7. 年龄（自动计算）**")
        age_value = st.session_state.get(f"f7_age_{student_name}", existing_data.get("年龄", ""))
        st.text_input("年龄", value=age_value, disabled=True, key=f"f7_age_{student_name}", label_visibility="collapsed")
        
        st.markdown("**8. 手机号码**")
        phone_input = st.text_input(
            "手机号码", 
            value=existing_data.get("手机号", ""), 
            key=f"f8_phone_{student_name}",
            placeholder="请输入11位手机号码",
            label_visibility="collapsed"
        )
        
        if phone_input:
            phone_clean = phone_input.strip()
            phone_len = len(phone_clean)
            if phone_len < 11:
                st.warning(f"⚠️ 当前已输入 {phone_len} 位，手机号码需要11位")
            elif phone_len > 11:
                st.warning(f"⚠️ 当前已输入 {phone_len} 位，手机号码只能11位")
            elif not phone_clean.isdigit():
                st.error("❌ 手机号码必须为数字")
            elif phone_clean.startswith(('1', '9')):
                st.success("✅ 手机号码格式正确")
            else:
                st.error("❌ 手机号码格式错误，请以1或9开头")
        else:
            st.caption("💡 请填写11位手机号码")
        
        st.text_input("9. 初中毕业学校", value=existing_data.get("初中毕业学校", ""), key=f"f9_middle_{student_name}")
        st.text_input("10. 中考总分", value=existing_data.get("中考总分", ""), key=f"f10_exam_{student_name}")
        cert_idx = 0 if existing_data.get("有无初中毕业证", "有") == "有" else 1
        st.selectbox("11. 有无初中毕业证", ["有", "无"], index=cert_idx, key=f"f11_cert_{student_name}")
        st.text_area("12. 常住地址", value=existing_data.get("常住地址", ""), key=f"f12_address_{student_name}", height=68)
        st.text_area("13. 户籍地址（身份证或户口本地址）", value=existing_data.get("户籍地址", ""), key=f"f13_hometown_{student_name}", height=68)
        
        st.markdown("---")
        st.markdown("### 👨‍👩‍👧‍👦 家庭情况")
        
        family_type_idx = get_family_type_options().index(existing_data.get("家庭基本情况", "原生家庭完整")) if existing_data.get("家庭基本情况") in get_family_type_options() else 0
        st.radio("14. 家庭基本情况", get_family_type_options(), index=family_type_idx, key=f"f14_family_type_{student_name}")
        
        default_members = existing_data.get("家庭成员", "").split(",") if existing_data.get("家庭成员") else []
        st.caption("💡 请在下拉框中选择家庭成员（可多选）")
        family_members = st.multiselect(
            "15. 家庭成员", 
            get_family_member_options(), 
            default=default_members, 
            key=f"f15_family_members_{student_name}",
            placeholder="请选择家庭成员"
        )
        family_members_str = ",".join(family_members) if family_members else ""
        
        default_edu = existing_data.get("家庭教育方法", "").split(",") if existing_data.get("家庭教育方法") else []
        st.caption("💡 请在下拉框中选择家庭教育方法（可多选）")
        edu_methods = st.multiselect(
            "16. 家庭教育方法", 
            get_education_method_options(), 
            default=default_edu, 
            key=f"f16_edu_methods_{student_name}",
            placeholder="请选择家庭教育方法"
        )
        edu_methods_str = ",".join(edu_methods) if edu_methods else ""
        
        sibling_types = ["哥哥", "姐姐", "弟弟", "妹妹", "其他"]
        has_siblings = any(m in family_members for m in sibling_types)
        if has_siblings:
            st.text_input(
                "17. 兄弟姐妹信息（姓名|关系|年龄，多条用逗号分隔）", 
                value=existing_data.get("兄弟姐妹信息", ""), 
                key=f"f17_sibling_{student_name}",
                placeholder="例如：张三|哥哥|18,李四|妹妹|15"
            )
        else:
            st.text_input("17. 兄弟姐妹信息", value="无兄弟姐妹", disabled=True, key=f"f17_sibling_disabled_{student_name}")
            st.info("💡 未选择兄弟姐妹，此项不可编辑")
        
        leave_idx = 0 if existing_data.get("是否留守", "否") == "否" else 1
        leave_behind = st.radio("18. 是否留守", get_leave_behind_options(), index=leave_idx, key=f"f18_leave_{student_name}")
        
        has_father_or_mother = "爸爸" in family_members or "妈妈" in family_members
        if leave_behind == "是" and has_father_or_mother:
            work_idx = get_parent_work_options().index(existing_data.get("父母工作情况", "爸爸外地工作")) if existing_data.get("父母工作情况") in get_parent_work_options() else 0
            st.selectbox("19. 父母工作情况", get_parent_work_options(), index=work_idx, key=f"f19_parent_work_{student_name}")
        else:
            if leave_behind == "是" and not has_father_or_mother:
                st.text_input("19. 父母工作情况", value="请先在家庭成员中选择爸爸或妈妈", disabled=True, key=f"f19_parent_work_disabled_{student_name}")
                st.warning("⚠️ 您选择了留守，但家庭成员中未选择爸爸或妈妈")
            else:
                st.text_input("19. 父母工作情况", value="未选择留守，此项不可编辑", disabled=True, key=f"f19_parent_work_disabled2_{student_name}")
        
        st.markdown("---")
        st.markdown("### 📞 监护人信息")
        
        if "爸爸" in family_members:
            st.markdown("**👨 爸爸信息**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.text_input("20. 爸爸姓名", value=existing_data.get("爸爸姓名", ""), key=f"f20_dad_name_{student_name}")
            with col2:
                st.text_input("21. 爸爸身份证号码", value=existing_data.get("爸爸身份证号", ""), key=f"f21_dad_id_{student_name}")
            with col3:
                st.text_input("22. 爸爸常用联系电话", value=existing_data.get("爸爸联系电话", ""), key=f"f22_dad_phone_{student_name}")
        else:
            st.text_input("20. 爸爸姓名", value="未选择爸爸", disabled=True, key=f"f20_dad_name_dis_{student_name}")
            st.text_input("21. 爸爸身份证号码", value="未选择爸爸", disabled=True, key=f"f21_dad_id_dis_{student_name}")
            st.text_input("22. 爸爸常用联系电话", value="未选择爸爸", disabled=True, key=f"f22_dad_phone_dis_{student_name}")
            st.info("💡 未选择爸爸，此项不可编辑")
        
        if "妈妈" in family_members:
            st.markdown("**👩 妈妈信息**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.text_input("23. 妈妈姓名", value=existing_data.get("妈妈姓名", ""), key=f"f23_mom_name_{student_name}")
            with col2:
                st.text_input("24. 妈妈身份证号码", value=existing_data.get("妈妈身份证号", ""), key=f"f24_mom_id_{student_name}")
            with col3:
                st.text_input("25. 妈妈常用联系电话", value=existing_data.get("妈妈联系电话", ""), key=f"f25_mom_phone_{student_name}")
        else:
            st.text_input("23. 妈妈姓名", value="未选择妈妈", disabled=True, key=f"f23_mom_name_dis_{student_name}")
            st.text_input("24. 妈妈身份证号码", value="未选择妈妈", disabled=True, key=f"f24_mom_id_dis_{student_name}")
            st.text_input("25. 妈妈常用联系电话", value="未选择妈妈", disabled=True, key=f"f25_mom_phone_dis_{student_name}")
            st.info("💡 未选择妈妈，此项不可编辑")
        
        has_other = any(m not in ["爸爸", "妈妈"] for m in family_members)
        if has_other:
            st.markdown("**👤 其他监护人信息**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.text_input("26. 其他监护人姓名", value=existing_data.get("其他监护人姓名", ""), key=f"f26_other_name_{student_name}")
            with col2:
                st.text_input("27. 其他监护人和本人关系", value=existing_data.get("其他监护人和本人关系", ""), key=f"f27_other_relation_{student_name}")
            with col3:
                st.text_input("28. 其他监护人身份证号码", value=existing_data.get("其他监护人身份证号", ""), key=f"f28_other_id_{student_name}")
            with col4:
                st.text_input("29. 其他监护人联系电话", value=existing_data.get("其他监护人联系电话", ""), key=f"f29_other_phone_{student_name}")
        else:
            st.text_input("26. 其他监护人姓名", value="无其他监护人", disabled=True, key=f"f26_other_name_dis_{student_name}")
            st.text_input("27. 其他监护人和本人关系", value="无其他监护人", disabled=True, key=f"f27_other_relation_dis_{student_name}")
            st.text_input("28. 其他监护人身份证号码", value="无其他监护人", disabled=True, key=f"f28_other_id_dis_{student_name}")
            st.text_input("29. 其他监护人联系电话", value="无其他监护人", disabled=True, key=f"f29_other_phone_dis_{student_name}")
            st.info("💡 未选择除父母外的其他监护人，此项不可编辑")
        
        st.markdown("---")
        st.markdown("### 🎯 个人发展")
        
        st.text_area("30. 选择农村电气技术（计算机方向）专业的原因", 
                     value=existing_data.get("选择专业原因", ""), 
                     key=f"f30_reason_{student_name}", height=68)
        
        future_idx = get_future_plan_options().index(existing_data.get("未来打算", "升学")) if existing_data.get("未来打算") in get_future_plan_options() else 0
        st.radio("31. 你对未来的打算", get_future_plan_options(), index=future_idx, key=f"f31_future_{student_name}")
        
        st.text_input("32. 曾在班上担任什么职务", value=existing_data.get("曾任职务", ""), key=f"f32_position_{student_name}")
        
        default_past = existing_data.get("曾患疾病", "").split(",") if existing_data.get("曾患疾病") else []
        st.caption("💡 请在下拉框中选择曾患疾病（可多选）")
        st.markdown("**⚠️ 重要提醒：如有隐瞒，后果自负！**")
        past_diseases = st.multiselect(
            "33. 曾经是否患过什么大病", 
            get_disease_options(), 
            default=default_past, 
            key=f"f33_past_diseases_{student_name}",
            placeholder="请选择曾患疾病"
        )
        past_diseases_str = ",".join(past_diseases) if past_diseases else ""
        
        default_now = existing_data.get("现患疾病", "").split(",") if existing_data.get("现患疾病") else []
        st.caption("💡 请在下拉框中选择现患疾病（可多选）")
        st.markdown("**⚠️ 重要提醒：如有隐瞒，后果自负！**")
        now_diseases = st.multiselect(
            "34. 现在是否患过什么大病", 
            get_disease_options(), 
            default=default_now, 
            key=f"f34_now_diseases_{student_name}",
            placeholder="请选择现患疾病"
        )
        now_diseases_str = ",".join(now_diseases) if now_diseases else ""
        
        st.markdown("---")
        
        if st.button("💾 保存全部信息", key=f"save_all_{student_name}"):
            id_valid = False
            if id_card_input:
                id_clean = id_card_input.strip().upper()
                if len(id_clean) == 18 and id_clean[:17].isdigit() and id_clean[17] in "0123456789X":
                    try:
                        weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
                        check_code = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
                        total = 0
                        for i in range(17):
                            total += int(id_clean[i]) * weight[i]
                        if check_code[total % 11] == id_clean[17]:
                            id_valid = True
                    except:
                        pass
            
            phone_valid = False
            if phone_input:
                phone_clean = phone_input.strip()
                if len(phone_clean) == 11 and phone_clean.isdigit() and phone_clean.startswith(('1', '9')):
                    phone_valid = True
            
            if id_card_input and not id_valid:
                st.error("❌ 身份证号码验证未通过，请修正后再保存")
            elif phone_input and not phone_valid:
                st.error("❌ 手机号码验证未通过，请修正后再保存")
            else:
                data = {
                    "姓名": student_name,
                    "性别": st.session_state.get(f"f2_gender_{student_name}", ""),
                    "民族": st.session_state.get(f"f3_nation_{student_name}", ""),
                    "特长爱好": st.session_state.get(f"f4_hobby_{student_name}", ""),
                    "性格特点": st.session_state.get(f"f5_personality_{student_name}", ""),
                    "身份证号": st.session_state.get(f"f6_idcard_{student_name}", ""),
                    "年龄": st.session_state.get(f"f7_age_{student_name}", ""),
                    "手机号": st.session_state.get(f"f8_phone_{student_name}", ""),
                    "初中毕业学校": st.session_state.get(f"f9_middle_{student_name}", ""),
                    "中考总分": st.session_state.get(f"f10_exam_{student_name}", ""),
                    "有无初中毕业证": st.session_state.get(f"f11_cert_{student_name}", ""),
                    "常住地址": st.session_state.get(f"f12_address_{student_name}", ""),
                    "户籍地址": st.session_state.get(f"f13_hometown_{student_name}", ""),
                    "家庭基本情况": st.session_state.get(f"f14_family_type_{student_name}", ""),
                    "家庭成员": family_members_str,
                    "家庭教育方法": edu_methods_str,
                    "兄弟姐妹信息": st.session_state.get(f"f17_sibling_{student_name}", "") if has_siblings else "无兄弟姐妹",
                    "是否留守": st.session_state.get(f"f18_leave_{student_name}", ""),
                    "父母工作情况": st.session_state.get(f"f19_parent_work_{student_name}", "") if (leave_behind == "是" and has_father_or_mother) else "",
                    "爸爸姓名": st.session_state.get(f"f20_dad_name_{student_name}", "") if "爸爸" in family_members else "",
                    "爸爸身份证号": st.session_state.get(f"f21_dad_id_{student_name}", "") if "爸爸" in family_members else "",
                    "爸爸联系电话": st.session_state.get(f"f22_dad_phone_{student_name}", "") if "爸爸" in family_members else "",
                    "妈妈姓名": st.session_state.get(f"f23_mom_name_{student_name}", "") if "妈妈" in family_members else "",
                    "妈妈身份证号": st.session_state.get(f"f24_mom_id_{student_name}", "") if "妈妈" in family_members else "",
                    "妈妈联系电话": st.session_state.get(f"f25_mom_phone_{student_name}", "") if "妈妈" in family_members else "",
                    "其他监护人姓名": st.session_state.get(f"f26_other_name_{student_name}", "") if has_other else "",
                    "其他监护人和本人关系": st.session_state.get(f"f27_other_relation_{student_name}", "") if has_other else "",
                    "其他监护人身份证号": st.session_state.get(f"f28_other_id_{student_name}", "") if has_other else "",
                    "其他监护人联系电话": st.session_state.get(f"f29_other_phone_{student_name}", "") if has_other else "",
                    "选择专业原因": st.session_state.get(f"f30_reason_{student_name}", ""),
                    "未来打算": st.session_state.get(f"f31_future_{student_name}", ""),
                    "曾任职务": st.session_state.get(f"f32_position_{student_name}", ""),
                    "曾患疾病": past_diseases_str,
                    "现患疾病": now_diseases_str,
                    "最后更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if not existing.empty:
                    idx = df_info[df_info["姓名"] == student_name].index[0]
                    for key, value in data.items():
                        if key in df_info.columns:
                            df_info.at[idx, key] = str(value)
                else:
                    new_row = pd.DataFrame([data])
                    df_info = pd.concat([df_info, new_row], ignore_index=True)
                
                save_data_csv(df_info, "student_info_new")
                st.success("✅ 所有信息已保存成功！")
                st.rerun()
        
        if not existing.empty:
            st.info("📌 已保存的基本信息可以在此修改，修改后点击保存即可更新。")
    
    # ==================== Tab2: 量化分 ====================
    with tab2:
        st.subheader("📊 我的量化管理分")
        df_scores = load_data_csv("score_records")
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
    
    # ==================== Tab3: 我的荣誉 ====================
    with tab3:
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
    
    # ==================== Tab4: 参加活动 ====================
    with tab4:
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
    
    # ==================== Tab5: 我的任务 ====================
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
    
    # ==================== Tab6: 每日反馈 ====================
    with tab6:
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
    
    # ==================== Tab7: 请假申请 ====================
    with tab7:
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
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "👥 学生名单", "📋 学生信息", "📊 量化管理", "📋 发布活动", 
        "🏆 学生荣誉", "📊 任务与反馈", "📋 请假审批", "📥 数据导出"
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
        df_info = load_data_csv("student_info_new")
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
    
    with tab5:
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
    
    with tab6:
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
    
    with tab7:
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
    
    with tab8:
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
