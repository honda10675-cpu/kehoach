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

# CSS Tối ưu cho Mobile & Máy tính
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    @media (max-width: 991px) {
        .main .block-container {
            max-width: 100% !important;
            padding: 0.8rem !important;
        }
    }

    .row-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 6px;
    }
    
    .row-card-priority {
        background-color: #fef9c3 !important;
        border: 2px solid #eab308 !important;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 6px;
    }

    .stat-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Lấy thời gian thực Việt Nam (UTC+7)
tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
now_vn = datetime.datetime.now(tz_vn)
current_date_str = now_vn.strftime("%d/%m/%Y")
current_time_str = now_vn.strftime("%H:%M")
current_hour = now_vn.hour
current_minute = now_vn.minute

# --- KẾT NỐI SUPABASE & BỘ NHỚ ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

if "db" not in st.session_state:
    st.session_state.db = {
        "mechanics": 0,
        "electricians": 0,
        "tasks": [],
        "repairs": [],
        "handoffs": [],
        "last_reset": ""
    }

# TỰ ĐỘNG XÓA TRANG 3 VÀO LÚC 05:00 VÀ 18:00
reset_key = f"{current_date_str}_{18 if current_hour >= 18 else (5 if current_hour >= 5 else 0)}"
if st.session_state.db["last_reset"] != reset_key:
    if (current_hour == 5 and current_minute < 30) or (current_hour == 18 and current_minute < 30):
        st.session_state.db["handoffs"] = []
        st.session_state.db["last_reset"] = reset_key

def check_password(pwd):
    return pwd == "230"

total_staff = st.session_state.db["mechanics"] + st.session_state.db["electricians"]

# --- TẠO VĂN BẢN BÁO CÁO TỔNG HỢP ---
report_text = f"""📋 **BÁO CÁO CÔNG VIỆC BẢO TRÌ / 维修工作报告**
📅 Ngày / 日期: {current_date_str} - {current_time_str}
👥 Tổng số người / 总人数: {total_staff} (Cơ khí/机械: {st.session_state.db['mechanics']}, Điện/电工: {st.session_state.db['electricians']})

1️⃣ **KẾ HOẠCH CÔNG VIỆC (TRANG 1) / 工作计划:**
"""

if st.session_state.db["tasks"]:
    for i, task in enumerate(st.session_state.db["tasks"], start=1):
        p_flag = "⭐[ƯU TIÊN/优先] " if task["is_priority"] else ""
        st_flag = "✅[Xong/完成]" if task["status"] == "done" else ("🔄[Giao ca/交接]" if task["status"] == "handoff" else "⏳[Đang làm/进行中]")
        report_text += f"{i}/ {p_flag}{task['machine']} - {task['content']} ({st_flag})\n"
else:
    report_text += "(Chưa có dữ liệu / 暂无数据)\n"

report_text += "\n2️⃣ **MÁY DỪNG SỬA (TRANG 2) / 停机维修:**\n"
if st.session_state.db["repairs"]:
    for i, rep in enumerate(st.session_state.db["repairs"], start=1):
        r_flag = "🟢[Đã xong/已完成]" if rep["is_done"] else "🔴[Đang sửa/维修中]"
        report_text += f"{i}/ {rep['machine']} - {rep['content']} ({r_flag})\n"
else:
    report_text += "(Không có máy dừng sửa / 无停机维修)\n"

report_text += "\n3️⃣ **NỘI DUNG GIAO CA (TRANG 3) / 交接班事项:**\n"
if st.session_state.db["handoffs"]:
    for i, ho in enumerate(st.session_state.db["handoffs"], start=1):
        report_text += f"{i}/ {ho['machine']} ({ho.get('sender', 'NV')}): {ho['content']}\n"
else:
    report_text += "(Chưa có nội dung giao ca / 暂无交接事项)\n"

def render_copy_button():
    copy_js = f"""
    <script>
    function copyTextToClip() {{
        const text = {json.dumps(report_text)};
        navigator.clipboard.writeText(text).then(function() {{
            alert('✅ ĐÃ SAO CHÉP BÁO CÁO THÀNH CÔNG!\\n已成功复制报告内容！');
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
        padding: 12px 16px;
        font-size: 1rem;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        box-shadow: 0 3px 8px rgba(37, 99, 235, 0.3);
        margin-bottom: 12px;
    ">
    📋 SAO CHÉP BÁO CÁO GỬI NHÓM / 复制报告发群
    </button>
    """
    st.components.v1.html(copy_js, height=65)

# --- TIÊU ĐỀ CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #0f172a; margin-bottom: 5px;'>⚙️ QUẢN LÝ BẢO TRÌ MÁY / 设备维修管理</h3>", unsafe_allow_html=True)

page = st.radio(
    "",
    ["TRANG 1: KẾ HOẠCH / 1. 工作计划", "TRANG 2: DỪNG MÁY / 2. 停机维修", "TRANG 3: GIAO CA & CHỦ QUẢN / 3. 交接班与主管查看"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# ==========================================
# TRANG 1: KẾ HOẠCH CÔNG VIỆC
# ==========================================
if "TRANG 1" in page:
    st.subheader("📝 Ghi Kế Hoạch Công Việc Ngày / 每日工作计划登记")

    with st.expander("📊 KHAI BÁO NHÂN LỰC (TRƯỜNG CA GHI) / 人员配置", expanded=True):
        c_m, c_e = st.columns(2)
        with c_m:
            mech_cnt = st.number_input("Cơ Khí / 机械 (Thợ/人) *", value=st.session_state.db["mechanics"], step=1, min_value=0)
        with c_e:
            elec_cnt = st.number_input("Thợ Điện / 电工 (Thợ/人) *", value=st.session_state.db["electricians"], step=1, min_value=0)
        
        st.session_state.db["mechanics"] = mech_cnt
        st.session_state.db["electricians"] = elec_cnt
        total_staff = mech_cnt + elec_cnt

    st.markdown(f"""
    <div class="stat-header">
        <div style="font-size: 0.85rem; opacity: 0.85;">📅 VN: <strong>{current_date_str} - {current_time_str}</strong></div>
        <div style="font-size: 1.1rem; font-weight: bold; margin-top: 2px;">👥 Tổng / 总人数: {total_staff} Người/人 (Cơ khí/机械: {st.session_state.db['mechanics']} | Điện/电工: {st.session_state.db['electricians']})</div>
    </div>
    """, unsafe_allow_html=True)

    # NÚT COPY ĐẶT TRÊN Ô KHOANH ĐỎ TRANG 1
    render_copy_button()

    # DANH SÁCH CÔNG VIỆC NHẢY LÊN PHÍA TRÊN
    st.markdown("### 📋 DANH SÁCH CÔNG VIỆC / 工作列表")

    pending_list = [t for t in st.session_state.db["tasks"] if t["status"] == "pending"]

    if not pending_list:
        st.info("Chưa có công việc nào trong danh sách / 暂无工作计划")
    else:
        for idx, t in enumerate(pending_list, start=1):
            card_style = "row-card-priority" if t["is_priority"] else "row-card"
            prio_tag = "⭐ [ƯU TIÊN / 优先]" if t["is_priority"] else ""

            st.markdown(f"""
            <div class="{card_style}">
                <strong>{idx}/ {html.escape(t['machine'])}</strong> {prio_tag}<br>
                <span style="color: #475569; font-size: 0.9rem;">📝 Nội dung / 内容: {html.escape(t['content'])} ({t['time']})</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🛠️ THAO TÁC CÔNG VIỆC / 工作操作")
        
        task_options = {f"{idx}/ {t['machine']} - {t['content']}": t for idx, t in enumerate(pending_list, start=1)}
        selected_task_label = st.selectbox("📌 Chọn máy cần thao tác / 选择要操作的设备:", list(task_options.keys()))
        selected_task = task_options[selected_task_label]

        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        with col_act1:
            if st.button("✅ Hoàn Thành / 完成", use_container_width=True):
                selected_task["status"] = "done"
                st.success("Đã hoàn thành! Chuyển sang Trang 3.")
                st.rerun()

        with col_act2:
            if st.button("🔄 Giao Ca / 交接", use_container_width=True):
                st.session_state["show_pop_handoff"] = True

        with col_act3:
            if st.button("✏️ Sửa / 编辑", use_container_width=True):
                st.session_state["show_pop_edit"] = True

        with col_act4:
            if st.button("🗑️ Xóa / 删除", use_container_width=True):
                st.session_state["show_pop_del"] = True

        if st.session_state.get("show_pop_handoff", False):
            with st.form("form_pop_handoff"):
                st.markdown(f"👉 **GIAO CA CHO MÁY / 交接设备: {selected_task['machine']}**")
                progress_txt = st.text_input("Tiến Độ Hiện Tại / 当前进度 *", placeholder="Ví dụ: Đã làm 80%")
                next_task_txt = st.text_area("Kế Hoạch Ca Sau / 下班计划 *", placeholder="Ví dụ: Tiếp tục lắp ráp")
                if st.form_submit_button("Xác Nhận Bàn Giao / 确认交接"):
                    if progress_txt.strip() and next_task_txt.strip():
                        selected_task["status"] = "handoff"
                        st.session_state.db["handoffs"].append({
                            "id": len(st.session_state.db["handoffs"]) + 1,
                            "machine": selected_task["machine"],
                            "content": f"[Tiến độ: {progress_txt}] - Kế hoạch tiếp: {next_task_txt}",
                            "sender": "Chuyển ca",
                            "time": current_time_str
                        })
                        st.session_state["show_pop_handoff"] = False
                        st.success("✅ Đã bàn giao sang Trang 3!")
                        st.rerun()
                    else:
                        st.error("Bắt buộc điền đầy đủ / 请填写完整")

        if st.session_state.get("show_pop_edit", False):
            with st.form("form_pop_edit"):
                st.markdown(f"✏️ **SỬA CÔNG VIỆC / 编辑工作: {selected_task['machine']}**")
                pwd_in = st.text_input("Mật khẩu / 密码 (230) *", type="password")
                e_mach = st.text_input("Tên Máy / 设备名称", value=selected_task["machine"])
                e_cont = st.text_area("Nội dung / 内容", value=selected_task["content"])
                e_prio = st.checkbox("Ưu tiên / 优先", value=selected_task["is_priority"])
                if st.form_submit_button("Lưu Thay Đổi / 保存"):
                    if check_password(pwd_in):
                        selected_task["machine"] = e_mach
                        selected_task["content"] = e_cont
                        selected_task["is_priority"] = e_prio
                        st.session_state["show_pop_edit"] = False
                        st.success("Đã cập nhật!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu không đúng / 密码错误")

        if st.session_state.get("show_pop_del", False):
            with st.form("form_pop_del"):
                st.markdown(f"🗑️ **XÓA CÔNG VIỆC / 删除工作: {selected_task['machine']}**")
                pwd_in2 = st.text_input("Mật khẩu / 密码 (230) *", type="password")
                if st.form_submit_button("Xác Nhận Xóa / 确认删除"):
                    if check_password(pwd_in2):
                        st.session_state.db["tasks"].remove(selected_task)
                        st.session_state["show_pop_del"] = False
                        st.success("Đã xóa!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu không đúng / 密码错误")

    st.divider()
    with st.form("form_add_task", clear_on_submit=True):
        st.markdown("### ➕ Nhập Công Việc Mới / 添加新工作")
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            t_machine = st.text_input("Công việc và Máy / 设备与工作 *", placeholder="Ví dụ: DKW2 - Tách hộp số trục vít")
        with col_t2:
            t_prio = st.checkbox("⭐ Ưu tiên / 优先 (Màu vàng)")

        t_content = st.text_area("Nội dung chi tiết / 详细内容 *", placeholder="Mô tả...")
        
        if st.form_submit_button("💾 LƯU CÔNG VIỆC / 保存工作", use_container_width=True):
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
                st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG!")
                st.rerun()
            else:
                st.error("❌ Vui lòng điền đầy đủ thông tin (*)")

# ==========================================
# TRANG 2: DỪNG MÁY SỬA
# ==========================================
elif "TRANG 2" in page:
    st.subheader("🛠️ Ghi Chú Dừng Máy Sửa / 停机维修记录")

    with st.form("form_repair", clear_on_submit=True):
        st.markdown("### ➕ Báo Dừng Máy Sửa Mới / 登记停机维修")
        r_machine = st.text_input("Tên Máy Dừng / 停机设备 *", placeholder="Ví dụ: PE5")
        r_content = st.text_area("Sự cố & Nội dung sửa / 故障与维修内容 *", placeholder="Nhập sự cố...")
        
        if st.form_submit_button("🚨 BÁO DỪNG MÁY / 提交停机", use_container_width=True):
            if r_machine.strip() and r_content.strip():
                st.session_state.db["repairs"].append({
                    "id": len(st.session_state.db["repairs"]) + 1,
                    "machine": r_machine,
                    "content": r_content,
                    "is_done": False,
                    "time": current_time_str
                })
                st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG!")
                st.rerun()
            else:
                st.error("❌ Bắt buộc điền thông tin (*)")

    st.divider()
    # NÚT COPY ĐẶT TRÊN Ô KHOANH ĐỎ TRANG 2
    render_copy_button()

    st.markdown("### 🔧 DANH SÁCH MÁY DỪNG SỬA / 停机维修列表")

    repairs_list = st.session_state.db["repairs"]
    if not repairs_list:
        st.info("Hiện không có máy dừng sửa / 暂无停机维修")

    for r in repairs_list:
        st_color = "#10b981" if r["is_done"] else "#ef4444"
        st_text = "🟢 ĐÃ SỬA XONG / 已修好" if r["is_done"] else "🔴 ĐANG SỬA / 维修中"

        st.markdown(f"""
        <div style="border-left: 5px solid {st_color}; background: #ffffff; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between;">
                <strong>⚠️ {html.escape(r['machine'])}</strong>
                <span style="color: {st_color}; font-weight: bold;">{st_text}</span>
            </div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">⏱️ {r['time']}</div>
            <div style="font-size: 0.95rem; color: #0f172a; margin-top: 4px;">📝 {html.escape(r['content'])}</div>
        </div>
        """, unsafe_allow_html=True)

        if not r["is_done"]:
            if st.button("☑️ Tích Hoàn Thành (Đã Sửa Xong) / 完成", key=f"fix_{r['id']}", use_container_width=True):
                r["is_done"] = True
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": r["machine"],
                    "content": f"[Đã sửa xong/已完成] {r['content']}",
                    "sender": "Thợ sửa",
                    "time": current_time_str
                })
                st.success("✅ Đã sửa xong! Chuyển sang Trang 3.")
                st.rerun()

# ==========================================
# TRANG 3: GIAO CA
# ==========================================
elif "TRANG 3" in page:
    st.subheader("📋 Giao Ca & Chủ Quản Xem / 交接班与主管查看")
    st.caption("🕒 Dữ liệu Trang 3 sẽ tự động xoá sạch vào giờ thực tế 18:00 và 05:00 hằng ngày.")

    with st.form("form_handoff", clear_on_submit=True):
        st.markdown("### ✍️ Nhập Nội Dung Bàn Giao Ca / 填写交接")
        col_h1, col_h2 = st.columns([1, 2])
        with col_h1:
            h_sender = st.text_input("Người giao / 交接人 *", placeholder="Tên NV")
            h_machine = st.text_input("Tên máy / 设备 *", placeholder="Tên máy")
        with col_h2:
            h_content = st.text_area("Nội dung bàn giao / 交接内容 *", placeholder="Nội dung...")

        if st.form_submit_button("📤 GỬI BÀN GIAO CA / 提交交接", use_container_width=True):
            if h_sender.strip() and h_machine.strip() and h_content.strip():
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": h_machine,
                    "sender": h_sender,
                    "content": h_content,
                    "time": current_time_str
                })
                st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG!")
                st.rerun()
            else:
                st.error("❌ Vui lòng nhập đầy đủ (*)")

    st.divider()
    # NÚT COPY ĐẶT TRÊN Ô KHOANH ĐỎ TRANG 3
    render_copy_button()

    st.markdown("### 👁️ DỮ LIỆU GIAO CA TRONG NGÀY / 当天交接数据")

    done_tasks = [t for t in st.session_state.db["tasks"] if t["status"] == "done"]
    if done_tasks:
        st.markdown("#### ✅ Công việc đã hoàn thành / 已完成工作")
        for dt in done_tasks:
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;">
                <strong style="color: #166534;">✓ {html.escape(dt['machine'])}</strong>
                <div style="font-size: 0.9rem; color: #15803d;">{html.escape(dt['content'])}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 🔄 Chi tiết danh sách bàn giao ca / 交接明细")
    h_list = st.session_state.db["handoffs"]

    if not h_list and not done_tasks:
        st.info("Chưa có nội dung bàn giao ca / 暂无交接内容")
    else:
        for idx, h in enumerate(h_list, start=1):
            st.markdown(f"""
            <div class="row-card">
                <strong>{idx}/ {html.escape(h['machine'])}</strong> (Người giao/交接人: {html.escape(h.get('sender', 'NV'))}) - <span style="color: #64748b; font-size: 0.85rem;">⏱️ {h['time']}</span><br>
                <span style="color: #1e293b; font-size: 0.95rem;">📝 {html.escape(h['content'])}</span>
            </div>
            """, unsafe_allow_html=True)

        if h_list:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🛠️ THAO TÁC GIAO CA / 交接操作")
            
            ho_options = {f"{idx}/ {h['machine']} - {h['content']}": h for idx, h in enumerate(h_list, start=1)}
            selected_ho_label = st.selectbox("📌 Chọn mục giao ca cần thao tác / 选择交接项:", list(ho_options.keys()))
            selected_ho = ho_options[selected_ho_label]

            col_he, col_hd = st.columns(2)
            with col_he:
                if st.button("✏️ Sửa / 编辑 (Mật khẩu 230)", use_container_width=True):
                    st.session_state["show_pop_ho_edit"] = True
            with col_hd:
                if st.button("🗑️ Xóa / 删除 (Mật khẩu 230)", use_container_width=True):
                    st.session_state["show_pop_ho_del"] = True

            if st.session_state.get("show_pop_ho_edit", False):
                with st.form("form_ho_edit"):
                    pw_e = st.text_input("Mật khẩu / 密码 (230) *", type="password")
                    nh_m = st.text_input("Tên máy / 设备", value=selected_ho["machine"])
                    nh_c = st.text_area("Nội dung / 内容", value=selected_ho["content"])
                    if st.form_submit_button("Lưu sửa / 保存"):
                        if check_password(pw_e):
                            selected_ho["machine"] = nh_m
                            selected_ho["content"] = nh_c
                            st.session_state["show_pop_ho_edit"] = False
                            st.success("Đã cập nhật!")
                            st.rerun()
                        else:
                            st.error("Sai mật khẩu!")

            if st.session_state.get("show_pop_ho_del", False):
                with st.form("form_ho_del"):
                    pw_d = st.text_input("Mật khẩu / 密码 (230) *", type="password")
                    if st.form_submit_button("Xác nhận xóa / 确认删除"):
                        if check_password(pw_d):
                            st.session_state.db["handoffs"].remove(selected_ho)
                            st.session_state["show_pop_ho_del"] = False
                            st.success("Đã xóa!")
                            st.rerun()
                        else:
                            st.error("Sai mật khẩu!")

# ==========================================
# KHU VỰC HIỂN THỊ VĂN BẢN VÀ BÁO CÁO TOÀN BỘ
# ==========================================
st.divider()
st.markdown("### 📸 BÁO CÁO TỔNG HỢP GỬI NHÓM / 综合报告发群")
st.text_area("Văn bản báo cáo đầy đủ / 完整报告内容:", value=report_text, height=200)
