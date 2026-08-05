    # ==================== Tab1: 学生基本信息（35项，全中文，身份证/手机号实时验证） ====================
    with tab1:
        st.subheader("📋 学生基本信息档案")
        st.info("请认真填写以下信息，所有信息仅班主任可见，严格保密")
        
        df_info = load_data_csv("student_info_new")
        existing = df_info[df_info["姓名"] == student_name] if not df_info.empty else pd.DataFrame()
        
        existing_data = {}
        if not existing.empty:
            for col in existing.columns:
                existing_data[col] = existing.iloc[0][col] if pd.notna(existing.iloc[0][col]) else ""
        
        # 用于存储验证状态
        id_card_valid = False
        phone_valid = False
        auto_age = ""
        
        with st.form("student_info_form_final", clear_on_submit=False):
            st.markdown("---")
            st.markdown("### 📌 基本信息")
            
            # 1. 姓名
            st.text_input("1. 姓名", value=student_name, disabled=True, key="f1_name")
            
            # 2. 性别（下拉框）
            gender_idx = get_gender_options().index(existing_data.get("性别", "男")) if existing_data.get("性别") in get_gender_options() else 0
            st.selectbox("2. 性别", get_gender_options(), index=gender_idx, key="f2_gender")
            
            # 3. 民族（下拉框）
            nation_idx = get_nation_options().index(existing_data.get("民族", "汉族")) if existing_data.get("民族") in get_nation_options() else 0
            st.selectbox("3. 民族", get_nation_options(), index=nation_idx, key="f3_nation")
            
            # 4. 特长或爱好
            st.text_input("4. 特长或爱好", value=existing_data.get("特长爱好", ""), key="f4_hobby")
            
            # 5. 性格特点
            st.text_input("5. 性格特点", value=existing_data.get("性格特点", ""), key="f5_personality")
            
            # 6. 身份证号码（带验证）
            st.markdown("**6. 身份证号码**")
            id_card_input = st.text_input(
                "身份证号码", 
                value=existing_data.get("身份证号", ""), 
                key="f6_idcard", 
                placeholder="请输入18位身份证号码（最后一位可能是数字或X）",
                label_visibility="collapsed"
            )
            
            # 身份证验证逻辑（实时）
            id_card_error = ""
            id_card_valid = False
            auto_age = ""
            
            if id_card_input:
                id_card_clean = id_card_input.strip().upper()
                id_len = len(id_card_clean)
                
                # 位数提醒
                if id_len < 18:
                    id_card_error = f"⚠️ 当前已输入 {id_len} 位，身份证号码需要18位"
                elif id_len > 18:
                    id_card_error = f"⚠️ 当前已输入 {id_len} 位，身份证号码只能18位"
                elif not id_card_clean[:17].isdigit():
                    id_card_error = "❌ 身份证号码前17位必须为数字"
                elif id_card_clean[17] not in "0123456789X":
                    id_card_error = "❌ 身份证号码最后一位只能为数字或字母X"
                else:
                    # 校验位验证
                    try:
                        weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
                        check_code = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
                        total = 0
                        for i in range(17):
                            total += int(id_card_clean[i]) * weight[i]
                        if check_code[total % 11] != id_card_clean[17]:
                            id_card_error = "❌ 身份证号码校验位错误，请核对"
                        else:
                            id_card_valid = True
                            # 计算年龄
                            birth_str = id_card_clean[6:14]
                            birth_date = datetime.strptime(birth_str, "%Y%m%d")
                            today = datetime.now()
                            age = today.year - birth_date.year
                            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                                age -= 1
                            auto_age = str(age)
                    except:
                        id_card_error = "❌ 身份证号码格式错误"
            
            # 显示身份证验证结果
            if id_card_input:
                if id_card_valid:
                    st.success("✅ 身份证号码验证通过")
                else:
                    st.error(id_card_error)
            else:
                st.caption("💡 请填写18位身份证号码，填写后自动计算年龄")
            
            # 7. 年龄（自动计算，显示在框里）
            st.markdown("**7. 年龄（自动计算）**")
            if auto_age:
                age_display = auto_age
                st.text_input("年龄", value=age_display, disabled=True, key="f7_age", label_visibility="collapsed")
                st.success(f"✅ 根据身份证计算年龄为：{auto_age}岁")
            else:
                existing_age = existing_data.get("年龄", "")
                age_display = existing_age
                st.text_input("年龄", value=age_display, disabled=True, key="f7_age", label_visibility="collapsed")
                if id_card_input and not id_card_valid:
                    st.warning("⚠️ 请先输入正确的身份证号码")
                elif not id_card_input:
                    st.caption("💡 填写身份证号码后将自动显示年龄")
            
            # 8. 手机号码（带验证）
            st.markdown("**8. 手机号码**")
            phone_input = st.text_input(
                "手机号码", 
                value=existing_data.get("手机号", ""), 
                key="f8_phone",
                placeholder="请输入11位手机号码",
                label_visibility="collapsed"
            )
            
            # 手机号验证（实时）
            if phone_input:
                phone_clean = phone_input.strip()
                phone_len = len(phone_clean)
                
                # 位数提醒
                if phone_len < 11:
                    st.warning(f"⚠️ 当前已输入 {phone_len} 位，手机号码需要11位")
                elif phone_len > 11:
                    st.warning(f"⚠️ 当前已输入 {phone_len} 位，手机号码只能11位")
                elif not phone_clean.isdigit():
                    st.error("❌ 手机号码必须为数字")
                elif phone_clean.startswith(('1', '9')):
                    phone_valid = True
                    st.success("✅ 手机号码格式正确")
                else:
                    st.error("❌ 手机号码格式错误，请以1或9开头")
            else:
                st.caption("💡 请填写11位手机号码")
            
            # 9. 初中毕业学校
            st.text_input("9. 初中毕业学校", value=existing_data.get("初中毕业学校", ""), key="f9_middle")
            
            # 10. 中考总分
            st.text_input("10. 中考总分", value=existing_data.get("中考总分", ""), key="f10_exam")
            
            # 11. 有无初中毕业证
            cert_idx = 0 if existing_data.get("有无初中毕业证", "有") == "有" else 1
            st.selectbox("11. 有无初中毕业证", ["有", "无"], index=cert_idx, key="f11_cert")
            
            # 12. 常住地址
            st.text_area("12. 常住地址", value=existing_data.get("常住地址", ""), key="f12_address", height=68)
            
            # 13. 户籍地址
            st.text_area("13. 户籍地址（身份证或户口本地址）", value=existing_data.get("户籍地址", ""), key="f13_hometown", height=68)
            
            st.markdown("---")
            st.markdown("### 👨‍👩‍👧‍👦 家庭情况")
            
            # 14. 家庭基本情况
            family_type_idx = get_family_type_options().index(existing_data.get("家庭基本情况", "原生家庭完整")) if existing_data.get("家庭基本情况") in get_family_type_options() else 0
            st.radio("14. 家庭基本情况", get_family_type_options(), index=family_type_idx, key="f14_family_type")
            
            # 15. 家庭成员（多选 - 已配置中文提示）
            default_members = existing_data.get("家庭成员", "").split(",") if existing_data.get("家庭成员") else []
            st.caption("💡 请在下拉框中选择家庭成员（可多选）")
            family_members = st.multiselect(
                "15. 家庭成员", 
                get_family_member_options(), 
                default=default_members, 
                key="f15_family_members",
                placeholder="请选择家庭成员",
                help="可以选择多个家庭成员"
            )
            family_members_str = ",".join(family_members) if family_members else ""
            
            # 16. 家庭教育方法（多选）
            default_edu = existing_data.get("家庭教育方法", "").split(",") if existing_data.get("家庭教育方法") else []
            st.caption("💡 请在下拉框中选择家庭教育方法（可多选）")
            st.multiselect(
                "16. 家庭教育方法", 
                get_education_method_options(), 
                default=default_edu, 
                key="f16_edu_methods",
                placeholder="请选择家庭教育方法",
                help="可以选择多个选项"
            )
            
            # 17. 兄弟姐妹信息
            sibling_types = ["哥哥", "姐姐", "弟弟", "妹妹", "其他"]
            has_siblings = any(m in family_members for m in sibling_types)
            if has_siblings:
                st.text_input("17. 兄弟姐妹信息（姓名|关系|年龄，多条用逗号分隔）", 
                             value=existing_data.get("兄弟姐妹信息", ""), 
                             key="f17_sibling",
                             placeholder="例如：张三|哥哥|18,李四|妹妹|15")
            else:
                st.text_input("17. 兄弟姐妹信息", value="无兄弟姐妹", disabled=True, key="f17_sibling_disabled")
                st.info("💡 未选择兄弟姐妹，此项不可编辑")
            
            # 18. 是否留守
            leave_idx = 0 if existing_data.get("是否留守", "否") == "否" else 1
            leave_behind = st.radio("18. 是否留守", get_leave_behind_options(), index=leave_idx, key="f18_leave")
            
            # 19. 父母工作情况
            has_father_or_mother = "爸爸" in family_members or "妈妈" in family_members
            if leave_behind == "是" and has_father_or_mother:
                work_idx = get_parent_work_options().index(existing_data.get("父母工作情况", "爸爸外地工作")) if existing_data.get("父母工作情况") in get_parent_work_options() else 0
                st.selectbox("19. 父母工作情况", get_parent_work_options(), index=work_idx, key="f19_parent_work")
            else:
                if leave_behind == "是" and not has_father_or_mother:
                    st.text_input("19. 父母工作情况", value="请先在家庭成员中选择爸爸或妈妈", disabled=True, key="f19_parent_work_disabled")
                    st.warning("⚠️ 您选择了留守，但家庭成员中未选择爸爸或妈妈")
                else:
                    st.text_input("19. 父母工作情况", value="未选择留守，此项不可编辑", disabled=True, key="f19_parent_work_disabled2")
            
            st.markdown("---")
            st.markdown("### 📞 监护人信息")
            
            # 20-22. 爸爸信息
            if "爸爸" in family_members:
                st.markdown("**👨 爸爸信息**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("20. 爸爸姓名", value=existing_data.get("爸爸姓名", ""), key="f20_dad_name")
                with col2:
                    st.text_input("21. 爸爸身份证号码", value=existing_data.get("爸爸身份证号", ""), key="f21_dad_id")
                with col3:
                    st.text_input("22. 爸爸常用联系电话", value=existing_data.get("爸爸联系电话", ""), key="f22_dad_phone")
            else:
                st.text_input("20. 爸爸姓名", value="未选择爸爸", disabled=True, key="f20_dad_name_dis")
                st.text_input("21. 爸爸身份证号码", value="未选择爸爸", disabled=True, key="f21_dad_id_dis")
                st.text_input("22. 爸爸常用联系电话", value="未选择爸爸", disabled=True, key="f22_dad_phone_dis")
                st.info("💡 未选择爸爸，此项不可编辑")
            
            # 23-25. 妈妈信息
            if "妈妈" in family_members:
                st.markdown("**👩 妈妈信息**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("23. 妈妈姓名", value=existing_data.get("妈妈姓名", ""), key="f23_mom_name")
                with col2:
                    st.text_input("24. 妈妈身份证号码", value=existing_data.get("妈妈身份证号", ""), key="f24_mom_id")
                with col3:
                    st.text_input("25. 妈妈常用联系电话", value=existing_data.get("妈妈联系电话", ""), key="f25_mom_phone")
            else:
                st.text_input("23. 妈妈姓名", value="未选择妈妈", disabled=True, key="f23_mom_name_dis")
                st.text_input("24. 妈妈身份证号码", value="未选择妈妈", disabled=True, key="f24_mom_id_dis")
                st.text_input("25. 妈妈常用联系电话", value="未选择妈妈", disabled=True, key="f25_mom_phone_dis")
                st.info("💡 未选择妈妈，此项不可编辑")
            
            # 26-29. 其他监护人信息
            has_other = any(m not in ["爸爸", "妈妈"] for m in family_members)
            if has_other:
                st.markdown("**👤 其他监护人信息**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.text_input("26. 其他监护人姓名", value=existing_data.get("其他监护人姓名", ""), key="f26_other_name")
                with col2:
                    st.text_input("27. 其他监护人和本人关系", value=existing_data.get("其他监护人和本人关系", ""), key="f27_other_relation")
                with col3:
                    st.text_input("28. 其他监护人身份证号码", value=existing_data.get("其他监护人身份证号", ""), key="f28_other_id")
                with col4:
                    st.text_input("29. 其他监护人联系电话", value=existing_data.get("其他监护人联系电话", ""), key="f29_other_phone")
            else:
                st.text_input("26. 其他监护人姓名", value="无其他监护人", disabled=True, key="f26_other_name_dis")
                st.text_input("27. 其他监护人和本人关系", value="无其他监护人", disabled=True, key="f27_other_relation_dis")
                st.text_input("28. 其他监护人身份证号码", value="无其他监护人", disabled=True, key="f28_other_id_dis")
                st.text_input("29. 其他监护人联系电话", value="无其他监护人", disabled=True, key="f29_other_phone_dis")
                st.info("💡 未选择除父母外的其他监护人，此项不可编辑")
            
            st.markdown("---")
            st.markdown("### 🎯 个人发展")
            
            # 30. 选择专业原因
            st.text_area("30. 选择农村电气技术（计算机方向）专业的原因", 
                         value=existing_data.get("选择专业原因", ""), 
                         key="f30_reason", height=68)
            
            # 31. 未来打算
            future_idx = get_future_plan_options().index(existing_data.get("未来打算", "升学")) if existing_data.get("未来打算") in get_future_plan_options() else 0
            st.radio("31. 你对未来的打算", get_future_plan_options(), index=future_idx, key="f31_future")
            
            # 32. 曾任职务
            st.text_input("32. 曾在班上担任什么职务", value=existing_data.get("曾任职务", ""), key="f32_position")
            
            # 33. 曾患疾病（多选）
            default_past = existing_data.get("曾患疾病", "").split(",") if existing_data.get("曾患疾病") else []
            st.caption("💡 请在下拉框中选择曾患疾病（可多选）")
            st.multiselect(
                "33. 曾经是否患过什么大病", 
                get_disease_options(), 
                default=default_past, 
                key="f33_past_diseases",
                placeholder="请选择曾患疾病",
                help="可以选择多个选项"
            )
            
            # 34. 现患疾病（多选）
            default_now = existing_data.get("现患疾病", "").split(",") if existing_data.get("现患疾病") else []
            st.caption("💡 请在下拉框中选择现患疾病（可多选）")
            st.multiselect(
                "34. 现在是否患过什么大病", 
                get_disease_options(), 
                default=default_now, 
                key="f34_now_diseases",
                placeholder="请选择现患疾病",
                help="可以选择多个选项"
            )
            
            st.markdown("---")
            submitted = st.form_submit_button("💾 保存全部信息")
            
            if submitted:
                # 如果身份证验证不通过，阻止保存
                if id_card_input and not id_card_valid:
                    st.error("❌ 身份证号码验证未通过，请修正后再保存")
                elif phone_input and not phone_valid:
                    st.error("❌ 手机号码验证未通过，请修正后再保存")
                else:
                    # 收集所有数据
                    data = {
                        "姓名": student_name,
                        "性别": st.session_state.get("f2_gender", ""),
                        "民族": st.session_state.get("f3_nation", ""),
                        "特长爱好": st.session_state.get("f4_hobby", ""),
                        "性格特点": st.session_state.get("f5_personality", ""),
                        "身份证号": st.session_state.get("f6_idcard", ""),
                        "年龄": st.session_state.get("f7_age", ""),
                        "手机号": st.session_state.get("f8_phone", ""),
                        "初中毕业学校": st.session_state.get("f9_middle", ""),
                        "中考总分": st.session_state.get("f10_exam", ""),
                        "有无初中毕业证": st.session_state.get("f11_cert", ""),
                        "常住地址": st.session_state.get("f12_address", ""),
                        "户籍地址": st.session_state.get("f13_hometown", ""),
                        "家庭基本情况": st.session_state.get("f14_family_type", ""),
                        "家庭成员": family_members_str,
                        "家庭教育方法": ",".join(st.session_state.get("f16_edu_methods", [])) if st.session_state.get("f16_edu_methods") else "",
                        "兄弟姐妹信息": st.session_state.get("f17_sibling", "") if has_siblings else "无兄弟姐妹",
                        "是否留守": st.session_state.get("f18_leave", ""),
                        "父母工作情况": st.session_state.get("f19_parent_work", "") if (leave_behind == "是" and has_father_or_mother) else "",
                        "爸爸姓名": st.session_state.get("f20_dad_name", "") if "爸爸" in family_members else "",
                        "爸爸身份证号": st.session_state.get("f21_dad_id", "") if "爸爸" in family_members else "",
                        "爸爸联系电话": st.session_state.get("f22_dad_phone", "") if "爸爸" in family_members else "",
                        "妈妈姓名": st.session_state.get("f23_mom_name", "") if "妈妈" in family_members else "",
                        "妈妈身份证号": st.session_state.get("f24_mom_id", "") if "妈妈" in family_members else "",
                        "妈妈联系电话": st.session_state.get("f25_mom_phone", "") if "妈妈" in family_members else "",
                        "其他监护人姓名": st.session_state.get("f26_other_name", "") if has_other else "",
                        "其他监护人和本人关系": st.session_state.get("f27_other_relation", "") if has_other else "",
                        "其他监护人身份证号": st.session_state.get("f28_other_id", "") if has_other else "",
                        "其他监护人联系电话": st.session_state.get("f29_other_phone", "") if has_other else "",
                        "选择专业原因": st.session_state.get("f30_reason", ""),
                        "未来打算": st.session_state.get("f31_future", ""),
                        "曾任职务": st.session_state.get("f32_position", ""),
                        "曾患疾病": ",".join(st.session_state.get("f33_past_diseases", [])) if st.session_state.get("f33_past_diseases") else "",
                        "现患疾病": ",".join(st.session_state.get("f34_now_diseases", [])) if st.session_state.get("f34_now_diseases") else "",
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
