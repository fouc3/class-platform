import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import zipfile
import io

st.set_page_config(page_title="班级学生成长平台", layout="wide")

# ---------- 配置 ----------
TEACHER_PASSWORD = "123456"
DATA_FOLDER = "class_data"
STUDENT_LIST_FILE = "student_list.xlsx"

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
        'leaves': ['姓名', '学号', '请假日期', '节次', '事由', '申请时间', '预审状态', '班主任意见']
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
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 基本信息", "🏆 我的荣誉", "📋 参加活动", "✅ 我的任务", "📝 每日反馈", "📋 请假申请"
    ])
    
    # ---------- Tab1: 学生基本信息 ----------
    with tab1:
        st.subheader("📋 我的基本信息")
        st.info("请认真填写以下信息，所有信息仅班主任可见，严格保密")
        
        df_info = load_data_csv("student_info")
        existing = df_info[df_info["姓名"] == student_name] if not df_info.empty else pd.DataFrame()
        
        # 获取已有数据，处理空值
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
    
    # ---------- Tab2: 我的荣誉 ----------
    with tab2:
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
    
    # ---------- Tab3: 参加活动 ----------
    with tab3:
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
    
    # ---------- Tab4: 我的任务 ----------
    with tab4:
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
    
    # ---------- Tab5: 每日反馈 ----------
    with tab5:
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
    
    # ---------- Tab6: 请假申请 ----------
    with tab6:
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
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 学生名单", "📋 学生基本信息", "📋 发布活动", "🏆 学生荣誉", "📊 任务与反馈", "📋 请假审批", "📥 数据导出"
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
    
    # Tab3: 发布活动
    with tab3:
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
    
    # Tab4: 学生荣誉
    with tab4:
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
    
    # Tab5: 任务与反馈
    with tab5:
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
    
    # Tab6: 请假审批
    with tab6:
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
    
    # Tab7: 数据导出
    with tab7:
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