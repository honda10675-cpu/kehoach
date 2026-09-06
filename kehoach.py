import streamlit as st
from supabase import create_client, Client
import datetime
import pytz
import html
import json

# --- CẤU HÌNH TRANG & GIAO DIỆN ---
st.set_page_config(
    page_title="Kế Hoạch & Giao Ca / 工作计划",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Responsive Laptop Fullscreen & Mobile 9:16
st.markdown("""
<style>
    .stApp {
        background-color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    @media (min-width: 992px) {
        .main .block-container {
            max-width: 95% !important;
            padding: 1.5rem 2rem !important;
        }
    }

    @media (max-width: 991px) {
        .main .block-container {
            max-width: 480px !important;
            min-height: 90vh;
            margin: auto;
            background-color: #ffffff;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-radius: 16px;
            padding: 1rem !important;
        }
    }

    .row-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .row-card-priority {
        background-color: #fef9c3 !important;
        border: 2px solid #eab308 !important;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        box-shadow: 0 2px 6px rgba(234, 179, 8, 0.2);
    }

    .stat-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 15px;
    }

    .required-star {
        color: #ef4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Lấy thời gian thực Việt Nam (UTC+7)
tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
now_vn = datetime.datetime.now(tz_vn)
current_date_str = now_vn.strftime("%d/%m/%Y")
current_time_str = now_vn.strftime("%H:%M")

# --- SUPABASE KẾT NỐI ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# BỘ NHỚ SESSION STATE
if "db" not in st.session_state:
    st.session_state.db = {
        "mechanics": 17,
        "electricians": 16,
        "tasks": [],
        "repairs": [],
        "handoffs": []
    }

def check_password(pwd):
    return pwd == "230"

# --- TIÊU ĐỀ TRANG ---
st.markdown("<h2 style='text-align: center; color: #0f172a; margin-bottom: 2px;'>⚙️ QUẢN LÝ BẢO TRÌ MÁY / 设备维修管理</h2>", unsafe_allow_html=True)

page = st.radio(
    "",
    ["TRANG 1: KẾ HOẠCH / 1. 工作计划", "TRANG 2: DỪNG MÁY / 2. 停机维修", "TRANG 3: GIAO CA & CHỦ QUẢN / 3. 交接班与主管查看"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# ==========================================
# TRANG 1: GHI KẾ HOẠCH CÔNG VIỆC NGÀY
# ==========================================
if "TRANG 1" in page:
    st.subheader("📝 Ghi Kế Hoạch Công Việc Ngày / 每日工作计划登记")

    # Thông tin tổng quan ngày & nhân lực
    with st.expander("📊 KHAI BÁO NHÂN LỰC / 人员配置", expanded=True):
        c_m, c_e = st.columns(2)
        with c_m:
            mech_cnt = st.number_input("Cơ Khí / 机械 (Thợ/人) *", value=st.session_state.db["mechanics"], step=1)
        with c_e:
            elec_cnt = st.number_input("Thợ Điện / 电工 (Thợ/人) *", value=st.session_state.db["electricians"], step=1)
        
        st.session_state.db["mechanics"] = mech_cnt
        st.session_state.db["electricians"] = elec_cnt

    total_staff = st.session_state.db["mechanics"] + st.session_state.db["electricians"]

    st.markdown(f"""
    <div class="stat-header">
        <div style="font-size: 0.9rem; opacity: 0.85;">📅 Ngày thực tế VN / 越南实际时间: <strong>{current_date_str} - {current_time_str}</strong></div>
        <div style="font-size: 1.3rem; font-weight: bold; margin-top: 4px;">👥 Tổng nhân lực / 总人数: {total_staff} Người / 人 (Cơ khí/机械: {st.session_state.db['mechanics']} | Điện/电工: {st.session_state.db['electricians']})</div>
    </div>
    """, unsafe_allow_html=True)

    # Form nhập kế hoạch (Tự động xóa sau khi gửi)
    with st.form("form_add_task", clear_on_submit=True):
        st.markdown("### ➕ Nhập Công Việc Mới / 添加新工作")
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            t_machine = st.text_input("Công việc và Máy / 设备与工作 *", placeholder="Ví dụ: Máy đùn 01 - Thay vòng bi / 挤出机 01")
        with col_t2:
            t_prio = st.checkbox("⭐ Máy ưu tiên (Trưởng ca tích màu vàng) / 优先设备")

        t_content = st.text_area("Nội dung chi tiết / 详细内容 *", placeholder="Mô tả chi tiết công việc cần làm...")
        
        btn_task_submit = st.form_submit_button("💾 LƯU CÔNG VIỆC / 保存工作", use_container_width=True)

        if btn_task_submit:
            if t_machine.strip() and t_content.strip():
                new_item = {
                    "id": len(st.session_state.db["tasks"]) + 1,
                    "machine": t_machine,
                    "content": t_content,
                    "is_priority": t_prio,
                    "status": "pending",
                    "time": current_time_str
                }
                st.session_state.db["tasks"].append(new_item)
                st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG! / 成功提交！ Nội dung đã tự xóa cho người khác nhập.")
                st.rerun()
            else:
                st.error("❌ Vui lòng điền đầy đủ các mục bắt buộc (*)! / 请填写所有必填项！")

    st.divider()
    st.markdown("### 📋 DANH SÁCH CÔNG VIỆC (1 HÀNG NGANG) / 工作列表")

    pending_list = [t for t in st.session_state.db["tasks"] if t["status"] == "pending"]

    if not pending_list:
        st.info("Chưa có công việc nào trong danh sách. / 暂无工作列表。")
    
    for idx, t in enumerate(pending_list, start=1):
        card_style = "row-card-priority" if t["is_priority"] else "row-card"
        prio_tag = "⭐ [ƯU TIÊN / 优先]" if t["is_priority"] else ""

        # Hiển thị 1 hàng ngang
        st.markdown(f"""
        <div class="{card_style}">
            <div style="flex: 1;">
                <strong>{idx}/ {html.escape(t['machine'])}</strong> {prio_tag}<br>
                <span style="color: #475569; font-size: 0.9rem;">📝 Nội dung: {html.escape(t['content'])} ({t['time']})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c_act1, c_act2, c_act3, c_act4 = st.columns([1, 1, 1, 1])
        with c_act1:
            if st.button("✅ Hoàn thành", key=f"done_{t['id']}", use_container_width=True):
                t["status"] = "done"
                st.success("Đã hoàn thành! Đã chuyển sang Trang 3 cho Chủ quản.")
                st.rerun()
        with c_act2:
            if st.button("🔄 Giao Ca", key=f"ho_{t['id']}", use_container_width=True):
                st.session_state[f"pop_handoff_{t['id']}"] = True
        with c_act3:
            if st.button("✏️ Sửa", key=f"ed_{t['id']}", use_container_width=True):
                st.session_state[f"pop_edit_{t['id']}"] = True
        with c_act4:
            if st.button("🗑️ Xóa", key=f"del_{t['id']}", use_container_width=True):
                st.session_state[f"pop_del_{t['id']}"] = True

        # Modal Giao ca bổ sung Tiến độ & Công việc tiếp theo
        if st.session_state.get(f"pop_handoff_{t['id']}", False):
            with st.form(f"f_ho_{t['id']}", clear_on_submit=True):
                st.markdown("👉 **ĐIỀN TIẾN ĐỘ & CÔNG VIỆC TIẾP THEO / 填写进度与下一步工作**")
                progress_txt = st.text_input("Cột Tiến Độ / 进度 *", placeholder="Ví dụ: Đã làm được 70%")
                next_task_txt = st.text_area("Công Việc Tiếp Theo / 下一步工作 *", placeholder="Ví dụ: Ca sau tiếp tục siết ốc và chạy thử")
                
                if st.form_submit_button("Xác Nhận Chuyển Giao Ca"):
                    if progress_txt.strip() and next_task_txt.strip():
                        t["status"] = "handoff"
                        st.session_state.db["handoffs"].append({
                            "id": len(st.session_state.db["handoffs"]) + 1,
                            "machine": t["machine"],
                            "content": f"[Tiến độ: {progress_txt}] - Kế hoạch tiếp: {next_task_txt}",
                            "sender": "Kế hoạch chuyển sang",
                            "time": current_time_str
                        })
                        st.session_state[f"pop_handoff_{t['id']}"] = False
                        st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG! Đã chuyển sang Trang 3.")
                        st.rerun()
                    else:
                        st.error("❌ Bắt buộc điền đầy đủ Tiến độ và Công việc tiếp theo (*)")

        # Modal Sửa (Yêu cầu mật khẩu 230)
        if st.session_state.get(f"pop_edit_{t['id']}", False):
            with st.form(f"f_ed_{t['id']}"):
                pwd_in = st.text_input("Nhập mật khẩu (230) / 输入密码 *", type="password")
                e_mach = st.text_input("Máy & Công việc", value=t["machine"])
                e_cont = st.text_area("Nội dung", value=t["content"])
                e_prio = st.checkbox("Máy ưu tiên", value=t["is_priority"])
                
                if st.form_submit_button("Lưu Thay Đổi"):
                    if check_password(pwd_in):
                        t["machine"] = e_mach
                        t["content"] = e_cont
                        t["is_priority"] = e_prio
                        st.session_state[f"pop_edit_{t['id']}"] = False
                        st.success("Đã sửa thành công!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai! (Mật khẩu chuẩn: 230)")

        # Modal Xóa (Yêu cầu mật khẩu 230)
        if st.session_state.get(f"pop_del_{t['id']}", False):
            with st.form(f"f_dl_{t['id']}"):
                pwd_in2 = st.text_input("Nhập mật khẩu (230) để Xóa / 输入密码 *", type="password")
                if st.form_submit_button("Xác Nhận Xóa"):
                    if check_password(pwd_in2):
                        st.session_state.db["tasks"].remove(t)
                        st.session_state[f"pop_del_{t['id']}"] = False
                        st.success("Đã xóa thành công!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai!")

        st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

# ==========================================
# TRANG 2: GHI CHÚ DỪNG MÁY SỬA
# ==========================================
elif "TRANG 2" in page:
    st.subheader("🛠️ Ghi Chú Dừng Máy Sửa / 停机维修记录")

    with st.form("form_repair", clear_on_submit=True):
        st.markdown("### ➕ Báo Dừng Máy Sửa Mới / 登记停机维修")
        r_machine = st.text_input("Tên Máy Dừng / 停机设备 *", placeholder="Ví dụ: Máy bện 05 / 绞线机 05")
        r_content = st.text_area("Sự cố & Nội dung sửa / 故障与维修内容 *", placeholder="Mô tả nguyên nhân và cách khắc phục...")
        
        if st.form_submit_button("🚨 BÁO DỪNG MÁY / 提交停机", use_container_width=True):
            if r_machine.strip() and r_content.strip():
                st.session_state.db["repairs"].append({
                    "id": len(st.session_state.db["repairs"]) + 1,
                    "machine": r_machine,
                    "content": r_content,
                    "is_done": False,
                    "time": current_time_str
                })
                st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG! Form đã tự xóa nội dung.")
                st.rerun()
            else:
                st.error("❌ Bắt buộc điền tên máy và nội dung sự cố (*)")

    st.divider()
    st.markdown("### 🔧 DANH SÁCH MÁY ĐANG DỪNG SỬA / 停机维修列表")

    repairs_list = st.session_state.db["repairs"]
    if not repairs_list:
        st.info("Hiện tại không có máy nào dừng sửa. / 当前无停机设备。")

    for r in repairs_list:
        st_color = "#10b981" if r["is_done"] else "#ef4444"
        st_text = "🟢 ĐÃ SỬA XONG / 已修好" if r["is_done"] else "🔴 ĐANG SỬA / 正在维修"

        st.markdown(f"""
        <div style="border-left: 5px solid {st_color}; background: #ffffff; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between;">
                <strong>⚠️ {html.escape(r['machine'])}</strong>
                <span style="color: {st_color}; font-weight: bold;">{st_text}</span>
            </div>
            <div style="font-size: 0.9rem; color: #475569; margin-top: 4px;">⏱️ Thời gian báo / 时间: {r['time']}</div>
            <div style="font-size: 0.95rem; color: #0f172a; margin-top: 4px;">📝 {html.escape(r['content'])}</div>
        </div>
        """, unsafe_allow_html=True)

        if not r["is_done"]:
            if st.button("☑️ Tích Hoàn Thành (Sửa Xong) / 修好点选", key=f"fix_{r['id']}", use_container_width=True):
                r["is_done"] = True
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": r["machine"],
                    "content": f"[Đã sửa xong dừng máy] {r['content']}",
                    "sender": "Thợ sửa máy",
                    "time": current_time_str
                })
                st.success("✅ Đã sửa xong! Tự động chuyển dữ liệu sang Trang 3 cho Chủ quản xem.")
                st.rerun()

# ==========================================
# TRANG 3: MỤC GIAO CA & CHỦ QUẢN QUẢN LÝ
# ==========================================
elif "TRANG 3" in page:
    st.subheader("📋 Giao Ca & Chủ Quản Xem / 交接班与主管查看")

    # Form nhân viên điền nội dung giao ca
    with st.form("form_handoff", clear_on_submit=True):
        st.markdown("### ✍️ Nhân Viên Điền Nội Dung Giao Ca / 员工填写交接")
        col_h1, col_h2 = st.columns([1, 2])
        with col_h1:
            h_sender = st.text_input("Tên người giao / 交班人 *", placeholder="Tên nhân viên")
            h_machine = st.text_input("Tên máy / 设备 *", placeholder="Tên máy")
        with col_h2:
            h_content = st.text_area("Nội dung giao ca / 交接内容 *", placeholder="Điền nội dung cần bàn giao...")

        if st.form_submit_button("📤 GỬI NỘI DUNG GIAO CA / 提交交接", use_container_width=True):
            if h_sender.strip() and h_machine.strip() and h_content.strip():
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": h_machine,
                    "sender": h_sender,
                    "content": h_content,
                    "time": current_time_str
                })
                st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG! Form đã tự xóa nội dung.")
                st.rerun()
            else:
                st.error("❌ Bắt buộc nhập đầy đủ tất cả thông tin giao ca (*)")

    st.divider()
    st.markdown("### 👁️ NỘI DUNG GIAO CA TRONG NGÀY (CHỦ QUẢN XEM) / 主管查看")

    # Danh sách các công việc hoàn thành từ Trang 1
    done_tasks = [t for t in st.session_state.db["tasks"] if t["status"] == "done"]
    if done_tasks:
        st.markdown("#### ✅ Các máy/công việc đã hoàn thành / 已完成的工作")
        for dt in done_tasks:
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;">
                <strong style="color: #166534;">✓ {html.escape(dt['machine'])}</strong>
                <div style="font-size: 0.9rem; color: #15803d;">{html.escape(dt['content'])}</div>
            </div>
            """, unsafe_allow_html=True)

    # Danh sách giao ca hiển thị 1 hàng ngang, nếu có người thứ 2 điền thì xuống hàng
    st.markdown("#### 🔄 Chi tiết nội dung bàn giao / 详细交接事项")
    h_list = st.session_state.db["handoffs"]

    if not h_list and not done_tasks:
        st.info("Chưa có nội dung giao ca nào. / 暂无交接数据。")

    for idx, h in enumerate(h_list, start=1):
        st.markdown(f"""
        <div class="row-card">
            <div style="flex: 1;">
                <strong>{idx}/ {html.escape(h['machine'])}</strong> (Người giao: {html.escape(h.get('sender', 'NV'))}) - <span style="color: #64748b; font-size: 0.85rem;">⏱️ {h['time']}</span><br>
                <span style="color: #1e293b; font-size: 0.95rem;">📝 {html.escape(h['content'])}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_he, col_hd = st.columns(2)
        with col_he:
            if st.button("✏️ Sửa (Cần 230)", key=f"he_{h['id']}", use_container_width=True):
                st.session_state[f"pop_he_{h['id']}"] = True
        with col_hd:
            if st.button("🗑️ Xóa (Cần 230)", key=f"hd_{h['id']}", use_container_width=True):
                st.session_state[f"pop_hd_{h['id']}"] = True

        if st.session_state.get(f"pop_he_{h['id']}", False):
            with st.form(f"fh_e_{h['id']}"):
                pw_e = st.text_input("Nhập mật khẩu (230) / 输入密码 *", type="password")
                nh_m = st.text_input("Tên máy", value=h["machine"])
                nh_c = st.text_area("Nội dung", value=h["content"])
                if st.form_submit_button("Xác nhận sửa"):
                    if check_password(pw_e):
                        h["machine"] = nh_m
                        h["content"] = nh_c
                        st.session_state[f"pop_he_{h['id']}"] = False
                        st.success("Đã sửa!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai!")

        if st.session_state.get(f"pop_hd_{h['id']}", False):
            with st.form(f"fh_d_{h['id']}"):
                pw_d = st.text_input("Nhập mật khẩu (230) để Xóa / 输入密码 *", type="password")
                if st.form_submit_button("Xác nhận xóa"):
                    if check_password(pw_d):
                        st.session_state.db["handoffs"].remove(h)
                        st.session_state[f"pop_hd_{h['id']}"] = False
                        st.success("Đã xóa!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu sai!")

        st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

# ==========================================
# TỰ ĐỘNG TẠO BÁO CÁO & SAO CHÉP
# ==========================================
st.divider()
st.markdown("### 📸 BÁO CÁO TỔNG HỢP GỬI NHÓM / 综合报告发群")

report_text = f"""📋 **BÁO CÁO CÔNG VIỆC BẢO TRÌ / 维修工作报告**
📅 Ngày / 日期: {current_date_str} - {current_time_str}
👥 Tổng số người / 总人数: {total_staff} (Cơ khí/机械: {st.session_state.db['mechanics']}, Điện/电工: {st.session_state.db['electricians']})

1️⃣ **KẾ HOẠCH CÔNG VIỆC / 工作计划:**
"""

for i, task in enumerate(st.session_state.db["tasks"], start=1):
    p_flag = "⭐[ƯU TIÊN/优先] " if task["is_priority"] else ""
    st_flag = "✅[Xong]" if task["status"] == "done" else ("🔄[Giao ca]" if task["status"] == "handoff" else "⏳[Đang làm]")
    report_text += f"{i}/ {p_flag}{task['machine']} - {task['content']} ({st_flag})\n"

report_text += "\n2️⃣ **MÁY DỪNG SỬA / 停机维修:**\n"
for i, rep in enumerate(st.session_state.db["repairs"], start=1):
    r_flag = "🟢[Đã xong]" if rep["is_done"] else "🔴[Đang sửa]"
    report_text += f"{i}/ {rep['machine']} - {rep['content']} ({r_flag})\n"

report_text += "\n3️⃣ **NỘI DUNG GIAO CA / 交接班事项:**\n"
for i, ho in enumerate(st.session_state.db["handoffs"], start=1):
    report_text += f"{i}/ {ho['machine']} ({ho.get('sender', 'NV')}): {ho['content']}\n"

st.text_area("Văn bản báo cáo / 报告文本", value=report_text, height=140)

copy_js = f"""
<script>
function copyTextToClip() {{
    const text = {json.dumps(report_text)};
    navigator.clipboard.writeText(text).then(function() {{
        alert('✅ ĐÃ SAO CHÉP BÁO CÁO THÀNH CÔNG!\\nBây giờ bạn có thể mở Zalo/WeChat và dán (Ctrl+V) vào nhóm.\\n\\n✅ 成功复制报告！可以直接粘贴到群组。');
    }}, function(err) {{
        alert('❌ Lỗi sao chép: ' + err);
    }});
}}
</script>
<button onclick="copyTextToClip()" style="
    width: 100%;
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    color: white;
    border: none;
    padding: 14px 20px;
    font-size: 1.05rem;
    font-weight: bold;
    border-radius: 10px;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
">
📋 SAO CHÉP BÁO CÁO GỬI NHÓM (BỘ NHỚ TẠM) / 复制内容发群
</button>
"""
st.components.v1.html(copy_js, height=80)
