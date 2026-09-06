import streamlit as st
from supabase import create_client, Client
import datetime
import html
import json

# --- CONFIG & STYLING ---
st.set_page_config(
    page_title="Kế Hoạch & Giao Ca / 工作计划",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Responsive & 9:16 Mobile Simulation CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f4f6f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    @media (min-width: 768px) {
        .block-container {
            max-width: 480px !important;
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            margin: auto;
            background-color: #ffffff;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-radius: 16px;
            min-height: 90vh;
        }
    }
    
    @media (max-width: 767px) {
        .block-container {
            padding: 0.8rem !important;
        }
    }

    .job-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .job-card-priority {
        background-color: #fffbeb !important;
        border: 2px solid #f59e0b !important;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(245, 158, 11, 0.15);
    }

    .badge-mech {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge-elec {
        background-color: #fef3c7;
        color: #92400e;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge-priority {
        background-color: #fef3c7;
        color: #b45309;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #f59e0b;
    }

    .stat-box {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 15px;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# Local Session State Fallback
if "local_db" not in st.session_state:
    st.session_state.local_db = {
        "daily_plan": {
            "date": str(datetime.date.today()),
            "mechanics": 17,
            "electricians": 16
        },
        "tasks": [
            {
                "id": 1,
                "machine": "Máy đùn 01 / 挤出机 01",
                "assignee": "Trần Văn A / 陈文A",
                "dept": "Cơ khí / 机械",
                "content": "Bảo trì định kỳ hộp số / 齿轮箱定期保养",
                "is_priority": True,
                "status": "pending",
                "created_at": "08:00"
            },
            {
                "id": 2,
                "machine": "Máy bện 05 / 绞线机 05",
                "assignee": "Nguyễn Văn B / 阮文B",
                "dept": "Điện / 电工",
                "content": "Kiểm tra tủ điện chính / 检查主配电柜",
                "is_priority": False,
                "status": "pending",
                "created_at": "08:30"
            }
        ],
        "repair_logs": [
            {
                "id": 101,
                "machine": "Máy kéo 02 / 拉丝机 02",
                "assignee": "Lê Văn C / 黎文C",
                "content": "Hỏng động cơ chính / 主电机故障",
                "is_done": False,
                "start_time": "09:15"
            }
        ],
        "handoffs": [
            {
                "id": 201,
                "machine": "Máy đùn 03 / 挤出机 03",
                "content": "Nhiệt độ gia nhiệt không ổn định, ca sau theo dõi / 加热温度不稳定，下班 theo dõi",
                "sender": "Ca sáng / 早上班",
                "created_at": "16:30"
            }
        ]
    }

def verify_password(pwd_input):
    return pwd_input == "230"

# --- TOP NAVIGATION ---
st.markdown("<h3 style='text-align: center; color: #0f172a; margin-bottom: 2px;'>⚙️ QUẢN LÝ BẢO TRÌ</h3>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: #64748b; margin-top: 0;'>设备维修管理系统</h5>", unsafe_allow_html=True)

page = st.radio(
    "",
    ["1. Kế Hoạch / 计划", "2. Dừng Máy / 停机维修", "3. Giao Ca / 交接班"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# ==========================================
# PAGE 1: KẾ HOẠCH CÔNG VIỆC
# ==========================================
if "1. Kế Hoạch" in page:
    st.subheader("📌 Kế Hoạch Ngày / 每日工作计划")

    with st.expander("⚙️ Nhân Lực & Tổng Số Người / 人员配置", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            mech_count = st.number_input("Cơ Khí / 机械 (Thợ)", value=st.session_state.local_db["daily_plan"]["mechanics"], step=1)
        with c2:
            elec_count = st.number_input("Thợ Điện / 电工 (Thợ)", value=st.session_state.local_db["daily_plan"]["electricians"], step=1)
        
        st.session_state.local_db["daily_plan"]["mechanics"] = mech_count
        st.session_state.local_db["daily_plan"]["electricians"] = elec_count

    total_people = st.session_state.local_db["daily_plan"]["mechanics"] + st.session_state.local_db["daily_plan"]["electricians"]

    st.markdown(f"""
    <div class="stat-box">
        <div style="font-size: 0.9rem; opacity: 0.9;">TỔNG NGUYÊN NHÂN LỰC / Tổng 人数</div>
        <div style="font-size: 1.8rem; font-weight: bold; margin: 4px 0;">{total_people} Người / 人</div>
        <div style="font-size: 0.8rem; opacity: 0.8;">Cơ Khí (机械): {st.session_state.local_db['daily_plan']['mechanics']} | Thợ Điện (电工): {st.session_state.local_db['daily_plan']['electricians']}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ Thêm Công Việc Mới / 添加新工作", expanded=False):
        with st.form("add_task_form"):
            col_m, col_p = st.columns([2, 1])
            with col_m:
                machine_input = st.text_input("Tên Máy / 设备名称", placeholder="Ví dụ: Máy đùn 01 / 挤出机 01")
            with col_p:
                dept_input = st.selectbox("Bộ phận / 部门", ["Cơ khí / 机械", "Điện / 电工"])
            
            assignee_input = st.text_input("Người phụ trách / 负责人", placeholder="Tên nhân viên / 员工姓名")
            content_input = st.text_area("Nội dung công việc / 工作内容", placeholder="Mô tả công việc cần làm...")
            is_priority = st.checkbox("⭐ Máy ưu tiên (Hiện màu vàng) / 优先设备 (显示黄色)")
            
            submit_btn = st.form_submit_button("Thêm Kế Hoạch / 保存计划", use_container_width=True)
            
            if submit_btn:
                if machine_input and content_input:
                    new_id = len(st.session_state.local_db["tasks"]) + 10
                    st.session_state.local_db["tasks"].append({
                        "id": new_id,
                        "machine": machine_input,
                        "assignee": assignee_input if assignee_input else "Chưa phân công",
                        "dept": dept_input,
                        "content": content_input,
                        "is_priority": is_priority,
                        "status": "pending",
                        "created_at": datetime.datetime.now().strftime("%H:%M")
                    })
                    st.success("Đã thêm công việc thành công! / 已成功添加工作！")
                    st.rerun()
                else:
                    st.warning("Vui lòng điền đủ Tên máy và Nội dung! / 请填写设备名称和内容！")

    st.markdown("### 📋 Danh Sách Công Việc / 工作列表")
    pending_tasks = [t for t in st.session_state.local_db["tasks"] if t["status"] == "pending"]
    
    if not pending_tasks:
        st.info("Chưa có công việc nào trong kế hoạch. / 暂无工作计划。")
    
    for task in pending_tasks:
        card_class = "job-card-priority" if task["is_priority"] else "job-card"
        dept_badge = f'<span class="badge-mech">{task["dept"]}</span>' if "Cơ khí" in task["dept"] else f'<span class="badge-elec">{task["dept"]}</span>'
        priority_tag = '<span class="badge-priority">⭐ ƯU TIÊN / 优先</span>' if task["is_priority"] else ''

        task_html = f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <strong style="font-size: 1.05rem; color: #0f172a;">🛠️ {html.escape(task['machine'])}</strong>
                <div>{priority_tag} {dept_badge}</div>
            </div>
            <div style="font-size: 0.9rem; color: #334155; margin-bottom: 6px;">
                👤 <strong>Phụ trách / 负责人:</strong> {html.escape(task['assignee'])}
            </div>
            <div style="font-size: 0.9rem; color: #475569; background: rgba(0,0,0,0.03); padding: 8px; border-radius: 6px;">
                📝 {html.escape(task['content'])}
            </div>
        </div>
        """
        st.markdown(task_html, unsafe_allow_html=True)

        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        with btn_col1:
            if st.button("✅ Hoàn Thành / 完成", key=f"done_{task['id']}", use_container_width=True):
                task["status"] = "done"
                st.success("Đã xong & Chuyển sang Trang 3! / 已完成并转到第3页！")
                st.rerun()
        with btn_col2:
            if st.button("🔄 Giao Ca / 交接", key=f"handoff_{task['id']}", use_container_width=True):
                st.session_state.local_db["handoffs"].append({
                    "id": len(st.session_state.local_db["handoffs"]) + 100,
                    "machine": task["machine"],
                    "content": f"[Chuyển từ kế hoạch] {task['content']}",
                    "sender": task["assignee"],
                    "created_at": datetime.datetime.now().strftime("%H:%M")
                })
                task["status"] = "handoff"
                st.success("Đã chuyển sang Trang 3 (Giao ca)! / 已转到第3页（交接班）！")
                st.rerun()
        with btn_col3:
            if st.button("✏️ Sửa / 编辑", key=f"edit_btn_{task['id']}", use_container_width=True):
                st.session_state[f"show_edit_{task['id']}"] = True
        with btn_col4:
            if st.button("🗑️ Xóa / 删除", key=f"del_btn_{task['id']}", use_container_width=True):
                st.session_state[f"show_del_{task['id']}"] = True

        if st.session_state.get(f"show_edit_{task['id']}", False):
            with st.form(f"form_edit_{task['id']}"):
                st.markdown("🔑 **Nhập mật khẩu (230) để Sửa / 输入密码(230)进行修改**")
                pwd = st.text_input("Mật khẩu / 密码", type="password", key=f"pwd_edit_{task['id']}")
                new_mach = st.text_input("Tên Máy / 设备", value=task["machine"], key=f"e_m_{task['id']}")
                new_assignee = st.text_input("Người phụ trách / 负责人", value=task["assignee"], key=f"e_a_{task['id']}")
                new_content = st.text_area("Nội dung / 内容", value=task["content"], key=f"e_c_{task['id']}")
                new_prio = st.checkbox("Máy ưu tiên / 优先", value=task["is_priority"], key=f"e_p_{task['id']}")
                
                if st.form_submit_button("Xác nhận Sửa / 确认修改"):
                    if verify_password(pwd):
                        task["machine"] = new_mach
                        task["assignee"] = new_assignee
                        task["content"] = new_content
                        task["is_priority"] = new_prio
                        st.session_state[f"show_edit_{task['id']}"] = False
                        st.success("Đã cập nhật! / 已更新！")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai! (Mật khẩu đúng: 230) / 密码错误！")

        if st.session_state.get(f"show_del_{task['id']}", False):
            with st.form(f"form_del_{task['id']}"):
                st.markdown("🔑 **Nhập mật khẩu (230) để Xóa / 输入密码(230)进行删除**")
                pwd_d = st.text_input("Mật khẩu / 密码", type="password", key=f"pwd_del_{task['id']}")
                if st.form_submit_button("Xác nhận Xóa / 确认删除"):
                    if verify_password(pwd_d):
                        st.session_state.local_db["tasks"].remove(task)
                        st.session_state[f"show_del_{task['id']}"] = False
                        st.success("Đã xóa! / 已删除！")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai! / 密码错误！")

        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

# ==========================================
# PAGE 2: GHI CHÚ DỪNG MÁY SỬA
# ==========================================
elif "2. Dừng Máy" in page:
    st.subheader("🚨 Ghi Chú Dừng Máy Sửa / 停机维修记录")

    with st.expander("➕ Báo Dừng Máy Sửa Mới / 登记新停机维修", expanded=True):
        with st.form("add_repair_form"):
            r_machine = st.text_input("Mã Máy / 停机设备", placeholder="Ví dụ: Máy kéo 02 / 拉丝机 02")
            r_assignee = st.text_input("Thợ sửa chữa / 维修人员", placeholder="Tên thợ / 维修人")
            r_content = st.text_area("Nội dung sự cố & Sửa chữa / 故障与维修内容")
            
            if st.form_submit_button("Báo Dừng Máy / 提交停机", use_container_width=True):
                if r_machine and r_content:
                    st.session_state.local_db["repair_logs"].append({
                        "id": len(st.session_state.local_db["repair_logs"]) + 200,
                        "machine": r_machine,
                        "assignee": r_assignee if r_assignee else "Chưa ghi nhận",
                        "content": r_content,
                        "is_done": False,
                        "start_time": datetime.datetime.now().strftime("%H:%M")
                    })
                    st.success("Đã ghi nhận dừng máy! / 已登记停机！")
                    st.rerun()

    st.markdown("### 🔧 Danh Sách Máy Đang Dừng / 正在维修列表")
    repairs = st.session_state.local_db["repair_logs"]
    if not repairs:
        st.info("Hiện không có máy nào dừng sửa. / 当前无停机维修。")

    for r in repairs:
        status_color = "#ef4444" if not r["is_done"] else "#10b981"
        status_text = "🔴 ĐANG SỬA / 正在维修" if not r["is_done"] else "🟢 ĐÃ SỬA XONG / 已修好"
        
        st.markdown(f"""
        <div style="border-left: 5px solid {status_color}; background-color: #ffffff; padding: 10px 14px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between;">
                <strong>⚠️ {html.escape(r['machine'])}</strong>
                <span style="color: {status_color}; font-weight: bold; font-size: 0.85rem;">{status_text}</span>
            </div>
            <div style="font-size: 0.85rem; color: #64748b; margin: 4px 0;">⏱️ Bắt đầu / 开始: {r['start_time']} | 👤 Thợ / 维修人: {html.escape(r['assignee'])}</div>
            <div style="font-size: 0.9rem; color: #1e293b; background: #f8fafc; padding: 6px; border-radius: 4px;">{html.escape(r['content'])}</div>
        </div>
        """, unsafe_allow_html=True)

        if not r["is_done"]:
            if st.button("☑️ Sửa Xong (Tích Hoàn Thành) / 修好点选", key=f"fix_{r['id']}", use_container_width=True):
                r["is_done"] = True
                st.session_state.local_db["handoffs"].append({
                    "id": len(st.session_state.local_db["handoffs"]) + 300,
                    "machine": r["machine"],
                    "content": f"[Đã sửa xong] {r['content']}",
                    "sender": r["assignee"],
                    "created_at": datetime.datetime.now().strftime("%H:%M")
                })
                st.success("Đã hoàn thành & Đã tự động chuyển sang Trang 3! / 已修好并转到第3页！")
                st.rerun()

# ==========================================
# PAGE 3: GIAO CA & CHỦ QUẢN QUẢN LÝ
# ==========================================
elif "3. Giao Ca" in page:
    st.subheader("📋 Giao Ca & Quản Lý / 交接班与主管查看")

    with st.expander("➕ Nhân Viên Điền Nội Dung Giao Ca / 员工填写交接内容", expanded=False):
        with st.form("add_handoff_form"):
            h_machine = st.text_input("Tên Máy / 设备", placeholder="Ví dụ: Máy đùn 03 / 挤出机 03")
            h_sender = st.text_input("Người giao ca / 交班人")
            h_content = st.text_area("Nội dung giao ca / 交接内容")
            
            if st.form_submit_button("Gửi Giao Ca / 提交交接", use_container_width=True):
                if h_machine and h_content:
                    st.session_state.local_db["handoffs"].append({
                        "id": len(st.session_state.local_db["handoffs"]) + 500,
                        "machine": h_machine,
                        "sender": h_sender if h_sender else "Nhân viên",
                        "content": h_content,
                        "created_at": datetime.datetime.now().strftime("%H:%M")
                    })
                    st.success("Đã lưu nội dung giao ca! / 已保存交接内容！")
                    st.rerun()

    st.markdown("### 👁️ Danh Sách Chủ Quản Xem / 主管查看列表")
    done_tasks = [t for t in st.session_state.local_db["tasks"] if t["status"] == "done"]
    
    if done_tasks:
        st.markdown("#### ✅ Công việc đã tích hoàn thành / 已完成的工作")
        for dt in done_tasks:
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px 12px; border-radius: 8px; margin-bottom: 6px;">
                <strong style="color: #166534;">✓ {html.escape(dt['machine'])}</strong> - <span style="font-size:0.85rem;">Phụ trách: {html.escape(dt['assignee'])}</span>
                <div style="font-size:0.85rem; color: #15803d;">{html.escape(dt['content'])}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 🔄 Nội dung giao ca & Máy đã sửa / 交接事项与已修设备")
    handoffs = st.session_state.local_db["handoffs"]
    
    if not handoffs and not done_tasks:
        st.info("Chưa có dữ liệu giao ca. / 暂无交接事项。")

    for h in handoffs:
        st.markdown(f"""
        <div class="job-card">
            <div style="display: flex; justify-content: space-between;">
                <strong>🔄 {html.escape(h['machine'])}</strong>
                <span style="font-size: 0.75rem; color: #64748b;">⏱️ {h['created_at']}</span>
            </div>
            <div style="font-size: 0.85rem; color: #475569; margin: 2px 0;">👤 <strong>Người giao / 交班人:</strong> {html.escape(h['sender'])}</div>
            <div style="font-size: 0.9rem; color: #0f172a; background: #f1f5f9; padding: 6px; border-radius: 6px;">{html.escape(h['content'])}</div>
        </div>
        """, unsafe_allow_html=True)

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            if st.button("✏️ Sửa (Điền sai) / 修改", key=f"edit_h_{h['id']}", use_container_width=True):
                st.session_state[f"show_edit_h_{h['id']}"] = True
        with col_h2:
            if st.button("🗑️ Chủ quản Xóa / 删除", key=f"del_h_{h['id']}", use_container_width=True):
                st.session_state[f"show_del_h_{h['id']}"] = True

        if st.session_state.get(f"show_edit_h_{h['id']}", False):
            with st.form(f"form_eh_{h['id']}"):
                st.markdown("🔑 **Nhập mật khẩu (230) để Sửa giao ca / 输入密码(230)修改**")
                pwd_eh = st.text_input("Mật khẩu / 密码", type="password", key=f"pwd_eh_{h['id']}")
                new_hm = st.text_input("Máy / 设备", value=h["machine"], key=f"nhm_{h['id']}")
                new_hc = st.text_area("Nội dung / 内容", value=h["content"], key=f"nhc_{h['id']}")
                if st.form_submit_button("Xác nhận / 确认"):
                    if verify_password(pwd_eh):
                        h["machine"] = new_hm
                        h["content"] = new_hc
                        st.session_state[f"show_edit_h_{h['id']}"] = False
                        st.success("Đã sửa! / 已修改！")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai! / 密码错误！")

        if st.session_state.get(f"show_del_h_{h['id']}", False):
            with st.form(f"form_dh_{h['id']}"):
                st.markdown("🔑 **Nhập mật khẩu (230) để Xóa / 输入密码(230)删除**")
                pwd_dh = st.text_input("Mật khẩu / 密码", type="password", key=f"pwd_dh_{h['id']}")
                if st.form_submit_button("Xác nhận Xóa / 确认删除"):
                    if verify_password(pwd_dh):
                        st.session_state.local_db["handoffs"].remove(h)
                        st.session_state[f"show_del_h_{h['id']}"] = False
                        st.success("Đã xóa! / 已删除！")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai! / 密码错误！")

        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

# ==========================================
# FOOTER & COPY TO CLIPBOARD BUTTON
# ==========================================
st.divider()
st.markdown("### 📸 Sao Chép Báo Cáo Gửi Nhóm / 复制报告到剪贴板")

summary_text = f"""📋 **BÁO CÁO CÔNG VIỆC VÀ GIAO CA / 工作与交接班报告**
📅 Ngày / 日期: {datetime.date.today()}
👥 Tổng số người / 总人数: {total_people} (Cơ khí/机械: {st.session_state.local_db['daily_plan']['mechanics']}, Điện/电工: {st.session_state.local_db['daily_plan']['electricians']})

1️⃣ **CÔNG VIỆC KẾ HOẠCH / 计划工作:**
"""

for t in st.session_state.local_db["tasks"]:
    prio_str = "⭐[ƯU TIÊN/优先] " if t["is_priority"] else ""
    status_str = "✅[Hoàn thành]" if t["status"] == "done" else ("🔄[Giao ca]" if t["status"] == "handoff" else "⏳[Đang làm]")
    summary_text += f"- {prio_str}{t['machine']} | {t['assignee']} | {t['content']} ({status_str})\n"

summary_text += "\n2️⃣ **MÁY DỪNG SỬA / 停机维修:**\n"
for r in st.session_state.local_db["repair_logs"]:
    r_status = "🟢[Đã xong]" if r["is_done"] else "🔴[Đang sửa]"
    summary_text += f"- {r['machine']} | Thợ: {r['assignee']} | {r['content']} ({r_status})\n"

summary_text += "\n3️⃣ **GIAO CA / 交接班事项:**\n"
for h in st.session_state.local_db["handoffs"]:
    summary_text += f"- {h['machine']} | {h['sender']}: {h['content']}\n"

st.text_area("Nội dung báo cáo văn bản / 文本报告内容", value=summary_text, height=150)

copy_html = f"""
<script>
function copyReportToClipboard() {{
    const textToCopy = {json.dumps(summary_text)};
    navigator.clipboard.writeText(textToCopy).then(function() {{
        alert('✅ Đã sao chép nội dung báo cáo! Bạn có thể dán (Ctrl+V) vào nhóm Zalo/WeChat.\\n✅ 已成功复制报告内容！您可以直接粘贴到群组。');
    }}, function(err) {{
        alert('❌ Lỗi sao chép / 复制失败: ' + err);
    }});
}}
</script>
<button onclick="copyReportToClipboard()" style="
    width: 100%;
    background-color: #2563eb;
    color: white;
    border: none;
    padding: 12px 20px;
    font-size: 1rem;
    font-weight: bold;
    border-radius: 10px;
    cursor: pointer;
    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    margin-top: 5px;
">
📋 SAO CHÉP BÁO CÁO GỬI NHÓM (BỘ NHỚ TẠM) / 复制内容发群
</button>
"""
st.components.v1.html(copy_html, height=100)
