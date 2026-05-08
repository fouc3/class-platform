import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="班级学生成长平台", layout="wide")

# ---------- 配置 ----------
TEACHER_PASSWORD = "123456"
DATA_FOLDER = "class_data"
STUDENT_LIST_FILE = "student_list.xlsx"

# 创建数据文件夹
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# ---------- CSV 数据保存/加载函数 ----------
def load_data_csv(filename):
    """从CSV加载数据，确保所有列都是字符串类型"""
    filepath = os.path.join(DATA_FOLDER, f"{filename}.csv")
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig', dtype=str)  # 关键：dtype=str 确保所有列都是文本
            df = df.fillna("")  # 填充空值
            return df
        except Exception as e:
            print(f"加载{filename}出错: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def save_data_csv(df, filename):
    """保存数据到CSV，确保所有列都是字符串"""
    if df is None or df.empty:
        df = pd.DataFrame()
    
    # 将所有列转换为字符串类型（避免类型冲突）
    for col in df.columns:
        df[col] = df[col].astype(str).fillna("")
    
    filepath = os.path.join(DATA_FOLDER, f"{filename}.csv")
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    return True

def load_student_list():
    """加载学生名单"""
    if os.path.exists(STUDENT_LIST_FILE):
        try:
            df = pd.read_excel(STUDENT_LIST_FILE, engine='openpyxl', dtype=str)
            df = df.fillna("")
            return df
        except:
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def verify_student(name):
    """验证学生姓名"""
    student_list = load_student_list()
    if student_list.empty:
        return False, None
    matched = student_list[student_list['姓名'] == name]
    if len(matched) > 0:
        sid = matched.iloc[0]['学号'] if '学号' in matched.columns else name
        return True, str(sid)
    return False, None

# 初始化数据文件
def init_data_files():
    files = {
        'daily_feedback': ['姓名', '学号', '心情', '学习状态', '反馈内容', '日期', '时间'],
        'activities': ['姓名', '学号', '活动名称', '角色', '日期'],
        'achievements': ['姓名', '学号', '成绩荣誉', '级别', '日期'],
        'tasks': ['姓名', '任务名称', '截止日期', '任务描述', '完成状态', '完成时间'],
        'leaves': ['姓名', '学号', '请假日期', '节次', '事由', '申请时间', '预审状态', '班主任意见']
    }
    
    for filename, columns in files.items():
        filepath = os.path.join(DATA_FOLDER, f"{filename}.csv")
        if not os.path.exists(filepath):
            empty_df = pd.DataFrame(columns=columns)
            empty_df.to_csv(filepath, index=False, encoding='utf-8-sig')

init_data_files()

# ---------- 学生端 ----------
def student_portal():
    st.header("👨‍🎓 学生成长中心")
    st.info("请输入你的姓名进行登录（仅限本班学生）")
    
    if 'student_logged_in' not in st.session_state:
        st.session_state.student_logged_in = False
        st.session_state.student_name = ""
        st.session_state.student_id = ""
    
    if not st.session_state.student_logged_in:
        student_name = st.text_input("姓名", key="login_name").strip()
        if st.button("登录"):
            if student_name:
                valid, sid = verify_student(student_name)
                if valid:
                    st.session_state.student_logged_in = True
                    st.session_state.student_name = student_name
                    st.session_state.student_id = str(sid)
                    st.success(f"欢迎，{student_name}同学！")
                    st.rerun()
                else:
                    st.error("验证失败：你不在本班学生名单中，请联系老师添加")
            else:
                st.warning("请输入姓名")
        return
    
    student_name = st.session_state.student_name
    student_id = st.session_state.student_id
    
    st.success(f"当前登录：{student_name}")
    if st.button("退出登录"):
        st.session_state.student_logged_in = False
        st.rerun()
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 每日反馈", "🏆 活动与成绩", "✅ 我的任务", "📋 请假申请"])
    
    with tab1:
        st.subheader("今日反馈")
        with st.form("daily_feedback"):
            mood = st.select_slider("今天心情", ["😔很差", "😐一般", "🙂不错", "😄非常好"])
            study_status = st.selectbox("学习状态", ["很吃力", "有点吃力", "正常", "良好", "优秀"])
            feedback = st.text_area("想对老师说的话")
            submitted = st.form_submit_button("提交反馈")
            if submitted:
                df = load_data_csv("daily_feedback")
                new_row = pd.DataFrame([{
                    "姓名": student_name,
                    "学号": student_id,
                    "心情": mood,
                    "学习状态": study_status,
                    "反馈内容": feedback,
                    "日期": date.today().strftime("%Y-%m-%d"),
                    "时间": datetime.now().strftime("%H:%M:%S")
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "daily_feedback")
                st.success("反馈已提交！")
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            with st.form("new_activity"):
                activity_name = st.text_input("活动名称")
                role = st.selectbox("角色", ["参与者", "组织者", "志愿者", "获奖者"])
                activity_date = st.date_input("日期", value=date.today())
                if st.form_submit_button("记录活动") and activity_name:
                    df = load_data_csv("activities")
                    new_row = pd.DataFrame([{
                        "姓名": student_name, "学号": student_id,
                        "活动名称": activity_name, "角色": role,
                        "日期": activity_date.strftime("%Y-%m-%d")
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data_csv(df, "activities")
                    st.success("已记录")
        with col2:
            with st.form("new_achievement"):
                achievement = st.text_input("取得的成绩")
                level = st.selectbox("级别", ["班级", "校级", "区级", "市级", "省级", "国家级"])
                ach_date = st.date_input("日期", value=date.today())
                if st.form_submit_button("记录成绩") and achievement:
                    df = load_data_csv("achievements")
                    new_row = pd.DataFrame([{
                        "姓名": student_name, "学号": student_id,
                        "成绩荣誉": achievement, "级别": level,
                        "日期": ach_date.strftime("%Y-%m-%d")
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data_csv(df, "achievements")
                    st.success("已记录")
    
    with tab3:
        st.subheader("我的任务")
        df_tasks = load_data_csv("tasks")
        if not df_tasks.empty:
            my_tasks = df_tasks[df_tasks["姓名"] == student_name]
            if not my_tasks.empty:
                for idx in my_tasks.index:
                    task = my_tasks.loc[idx]
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"📌 **{task['任务名称']}**")
                        st.caption(f"截止：{task['截止日期']}")
                    with col2:
                        current = task["完成状态"]
                        options = ["未开始", "进行中", "已完成"]
                        new_status = st.selectbox("状态", options, index=options.index(current) if current in options else 0, key=f"task_{idx}")
                    with col3:
                        if new_status != current:
                            if st.button("更新", key=f"update_{idx}"):
                                df_tasks.at[idx, "完成状态"] = new_status
                                if new_status == "已完成":
                                    df_tasks.at[idx, "完成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                save_data_csv(df_tasks, "tasks")
                                st.success("已更新")
                                st.rerun()
            else:
                st.info("暂无任务")
        else:
            st.info("暂无任务")
    
    with tab4:
        st.subheader("请假申请")
        with st.form("leave_form"):
            col1, col2 = st.columns(2)
            with col1:
                leave_date = st.date_input("请假日期", value=date.today())
                periods = st.multiselect("请假节次", ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "全天"])
            with col2:
                reason = st.text_area("事由")
            if st.form_submit_button("提交申请") and periods:
                df = load_data_csv("leaves")
                new_row = pd.DataFrame([{
                    "姓名": student_name,
                    "学号": student_id,
                    "请假日期": leave_date.strftime("%Y-%m-%d"),
                    "节次": ",".join(periods),
                    "事由": reason,
                    "申请时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "预审状态": "待审批",
                    "班主任意见": ""
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data_csv(df, "leaves")
                st.success("请假已提交")
        
        with st.expander("我的请假记录"):
            df_leave = load_data_csv("leaves")
            if not df_leave.empty:
                my_leaves = df_leave[df_leave["姓名"] == student_name]
                if not my_leaves.empty:
                    st.dataframe(my_leaves[["请假日期", "节次", "事由", "预审状态", "班主任意见"]], use_container_width=True)

# ---------- 教师后台 ----------
def teacher_login():
    st.header("🔐 教师后台")
    password = st.text_input("管理员密码", type="password")
    if password == TEACHER_PASSWORD:
        st.session_state.teacher_logged_in = True
        st.rerun()
    elif password:
        st.error("密码错误")

def teacher_portal():
    st.header("📊 教师后台管理")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "学生名单", "每日反馈", "活动记录", "成绩记录", "任务管理", "请假审批"
    ])
    
    with tab1:
        st.subheader("👥 学生名单管理")
        uploaded = st.file_uploader("上传学生名单Excel（列：姓名、学号）", type=["xlsx"])
        if uploaded:
            df_new = pd.read_excel(uploaded, engine='openpyxl', dtype=str)
            df_new = df_new.fillna("")
            df_new.to_excel(STUDENT_LIST_FILE, index=False)
            st.success(f"已更新，共{len(df_new)}人")
            st.rerun()
        
        if os.path.exists(STUDENT_LIST_FILE):
            df = pd.read_excel(STUDENT_LIST_FILE, engine='openpyxl', dtype=str)
            df = df.fillna("")
            st.dataframe(df, use_container_width=True)
            
            with st.expander("手动添加"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("姓名")
                with col2:
                    new_id = st.text_input("学号")
                if st.button("添加") and new_name and new_id:
                    new_row = pd.DataFrame([{"姓名": new_name, "学号": new_id}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_excel(STUDENT_LIST_FILE, index=False)
                    st.success("已添加")
                    st.rerun()
    
    with tab2:
        st.subheader("每日反馈")
        df = load_data_csv("daily_feedback")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("下载反馈", csv, "daily_feedback.csv", "text/csv")
        else:
            st.info("暂无数据")
    
    with tab3:
        st.subheader("活动记录")
        df = load_data_csv("activities")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("下载活动", df.to_csv(index=False).encode('utf-8-sig'), "activities.csv")
        else:
            st.info("暂无数据")
    
    with tab4:
        st.subheader("成绩记录")
        df = load_data_csv("achievements")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("下载成绩", df.to_csv(index=False).encode('utf-8-sig'), "achievements.csv")
        else:
            st.info("暂无数据")
    
    with tab5:
        st.subheader("任务管理")
        df_tasks = load_data_csv("tasks")
        
        with st.form("new_task"):
            col1, col2 = st.columns(2)
            with col1:
                target = st.text_input("学生姓名（留空则全员）")
                task_name = st.text_input("任务名称")
            with col2:
                due = st.date_input("截止日期")
                desc = st.text_area("描述")
            if st.form_submit_button("发布") and task_name:
                if target:
                    new = pd.DataFrame([{"姓名": target, "任务名称": task_name, "截止日期": due.strftime("%Y-%m-%d"), "任务描述": desc, "完成状态": "未开始", "完成时间": ""}])
                    df_tasks = pd.concat([df_tasks, new], ignore_index=True)
                else:
                    student_list = load_student_list()
                    for _, s in student_list.iterrows():
                        new = pd.DataFrame([{"姓名": s["姓名"], "任务名称": task_name, "截止日期": due.strftime("%Y-%m-%d"), "任务描述": desc, "完成状态": "未开始", "完成时间": ""}])
                        df_tasks = pd.concat([df_tasks, new], ignore_index=True)
                save_data_csv(df_tasks, "tasks")
                st.success("已发布")
                st.rerun()
        
        if not df_tasks.empty:
            st.dataframe(df_tasks, use_container_width=True)
            st.download_button("下载任务", df_tasks.to_csv(index=False).encode('utf-8-sig'), "tasks.csv")
    
    with tab6:
        st.subheader("请假审批")
        df = load_data_csv("leaves")
        
        if not df.empty:
            # 显示待审批列表
            pending = df[df["预审状态"] == "待审批"]
            if not pending.empty:
                st.write(f"📋 待审批：{len(pending)}条")
                for idx in pending.index:
                    row = df.loc[idx]
                    with st.expander(f"{row['姓名']} - {row['请假日期']} 请假{row['节次']}"):
                        st.write(f"**事由：** {row['事由']}")
                        st.write(f"**申请时间：** {row['申请时间']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            new_status = st.selectbox("审批结果", ["已批准", "已拒绝"], key=f"status_{idx}")
                        with col2:
                            comment = st.text_input("班主任意见", value="", key=f"comment_{idx}")
                        
                        if st.button("确认审批", key=f"approve_{idx}"):
                            # 关键修复：使用正确的赋值方式
                            df.loc[idx, "预审状态"] = str(new_status)
                            df.loc[idx, "班主任意见"] = str(comment)
                            save_data_csv(df, "leaves")
                            st.success(f"已{new_status}，意见：{comment if comment else '无'}")
                            st.rerun()
            else:
                st.info("✅ 暂无待审批请假")
            
            # 全部记录
            with st.expander("📜 全部请假记录"):
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("下载请假记录", csv, "leaves.csv", "text/csv")
        else:
            st.info("暂无请假记录")

def main():
    st.sidebar.title("导航")
    
    if "teacher_logged_in" not in st.session_state:
        st.session_state.teacher_logged_in = False
    
    role = st.sidebar.radio("登录身份", ["学生入口", "教师后台"])
    
    if role == "学生入口":
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