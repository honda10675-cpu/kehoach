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

# CSS Responsive cho Mobile & Máy tính
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
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .row-card-priority {
        background-color: #fef9c3 !important;
        border: 2px solid #eab308 !important;
        border-radius: 10px;
        padding: 12px 14px;
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
</style>
""", unsafe_allow_html=True)

# Lấy thời gian thực Việt Nam (UTC+7)
tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
now_vn = datetime.datetime.now(tz_vn)
current_date_str = now_vn.strftime("%d/%m/%Y")
current_time_str = now_vn.strftime("%H:%M")
current_hour = now_vn.hour
current_minute = now_vn.minute

# --- KẾT NỐI SUPABASE & LƯU DỮ LIỆU CỐ ĐỊNH ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# Quản lý bộ nhớ tạm
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

# --- TIÊU ĐỀ CHÍNH ---
st.markdown("<h2 style='text-align: center; color: #0f172a; margin-bottom: 2px;'>⚙️ QUẢN LÝ BẢO TRÌ MÁY / 设备维修管理</h2>", unsafe_allow_html=True)

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
        <div style="font-size: 0.9rem; opacity: 0.85;">📅 Ngày thực tế VN: <strong>{current_date_str} - {current_time_str}</strong></div>
        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 4px;">👥 Tổng nhân lực: {total_staff} Người (Cơ khí: {st.session_state.db['mechanics']} | Điện: {st.session_state.db['electricians']})</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_add_task", clear_on_submit=True):
        st.markdown("### ➕ Nhập Công Việc Mới / 添加新工作")
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            t_machine = st.text_input("Công việc và Máy / 设备与工作 *", placeholder="Ví dụ: DKW2 - Tách hộp số trục vít")
        with col_t2:
            t_prio = st.checkbox("⭐ Máy ưu tiên (Màu vàng)")

        t_content = st.text_area("Nội dung chi tiết / 详细内容 *", placeholder="Mô tả công việc...")
        
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
                st.success("✅ THÔNG BÁO GỬI THÀNH CÔNG!")
                st.rerun()
            else:
                st.error("❌ Vui lòng điền đầy đủ thông tin (*)")

    st.divider()
    st.markdown("### 📋 DANH SÁCH CÔNG VIỆC / 工作列表")

    pending_list = [t for t in st.session_state.db["tasks"] if t["status"] == "pending"]

    if not pending_list:
        st.info("Chưa có công việc nào trong danh sách.")
    
    for idx, t in enumerate(pending_list, start=1):
        card_style = "row-card-priority" if t["is_priority"] else "row-card"
        prio_tag = "⭐ [ƯU TIÊN / 优先]" if t["is_priority"] else ""

        # Ô CHỌN MÁY TÍCH CHỌN
        chk_selected = st.checkbox(f"Chọn máy này / 选择此设备", key=f"select_{t['id']}")

        st.markdown(f"""
        <div class="{card_style}">
            <div>
                <strong>{idx}/ {html.escape(t['machine'])}</strong> {prio_tag}<br>
                <span style="color: #475569; font-size: 0.9rem;">📝 Nội dung: {html.escape(t['content'])} ({t['time']})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # CÁC NÚT THAO TÁC XẾP NẰM Ở CUỐI TRANG/CUỐI THẺ
        c_act1, c_act2, c_act3, c_act4 = st.columns([1, 1, 1, 1])
        with c_act1:
            if st.button("✅ Hoàn thành", key=f"done_{t['id']}", use_container_width=True):
                t["status"] = "done"
                st.success("Đã hoàn thành! Đã chuyển sang Trang 3.")
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

        if st.session_state.get(f"pop_handoff_{t['id']}", False):
            with st.form(f"f_ho_{t['id']}", clear_on_submit=True):
                st.markdown("👉 **ĐIỀN TIẾN ĐỘ & CÔNG VIỆC TIẾP THEO**")
                progress_txt = st.text_input("Cột Tiến Độ *", placeholder="Ví dụ: Đã làm 80%")
                next_task_txt = st.text_area("Công Việc Tiếp Theo *", placeholder="Ví dụ: Ca sau tiếp tục lắp ráp")
                
                if st.form_submit_button("Xác Nhận Bàn Giao"):
                    if progress_txt.strip() and next_task_txt.strip():
                        t["status"] = "handoff"
                        st.session_state.db["handoffs"].append({
                            "id": len(st.session_state.db["handoffs"]) + 1,
                            "machine": t["machine"],
                            "content": f"[Tiến độ: {progress_txt}] - Kế hoạch tiếp: {next_task_txt}",
                            "sender": "Chuyển ca",
                            "time": current_time_str
                        })
                        st.session_state[f"pop_handoff_{t['id']}"] = False
                        st.success("✅ Đã chuyển sang Trang 3.")
                        st.rerun()
                    else:
                        st.error("❌ Bắt buộc điền đầy đủ các mục (*)")

        if st.session_state.get(f"pop_edit_{t['id']}", False):
            with st.form(f"f_ed_{t['id']}"):
                pwd_in = st.text_input("Mật khẩu (230) *", type="password")
                e_mach = st.text_input("Tên Máy", value=t["machine"])
                e_cont = st.text_area("Nội dung", value=t["content"])
                e_prio = st.checkbox("Ưu tiên", value=t["is_priority"])
                
                if st.form_submit_button("Lưu Thay Đổi"):
                    if check_password(pwd_in):
                        t["machine"] = e_mach
                        t["content"] = e_cont
                        t["is_priority"] = e_prio
                        st.session_state[f"pop_edit_{t['id']}"] = False
                        st.success("Đã sửa!")
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")

        if st.session_state.get(f"pop_del_{t['id']}", False):
            with st.form(f"f_dl_{t['id']}"):
                pwd_in2 = st.text_input("Mật khẩu (230) *", type="password")
                if st.form_submit_button("Xác Nhận Xóa"):
                    if check_password(pwd_in2):
                        st.session_state.db["tasks"].remove(t)
                        st.session_state[f"pop_del_{t['id']}"] = False
                        st.success("Đã xóa!")
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")

        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

# ==========================================
# TRANG 2: DỪNG MÁY SỬA
# ==========================================
elif "TRANG 2" in page:
    st.subheader("🛠️ Ghi Chú Dừng Máy Sửa / 停机维修记录")

    with st.form("form_repair", clear_on_submit=True):
        st.markdown("### ➕ Báo Dừng Máy Sửa Mới / 登记停机维修")
        r_machine = st.text_input("Tên Máy Dừng *", placeholder="Ví dụ: PE5")
        r_content = st.text_area("Sự cố & Nội dung sửa *", placeholder="Nhập sự cố...")
        
        if st.form_submit_button("🚨 BÁO DỪNG MÁY", use_container_width=True):
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
    st.markdown("### 🔧 DANH SÁCH MÁY DỪNG SỬA / 停机维修列表")

    repairs_list = st.session_state.db["repairs"]
    if not repairs_list:
        st.info("Hiện không có máy dừng sửa.")

    for r in repairs_list:
        st_color = "#10b981" if r["is_done"] else "#ef4444"
        st_text = "🟢 ĐÃ SỬA XONG" if r["is_done"] else "🔴 ĐANG SỬA"

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
            if st.button("☑️ Tích Hoàn Thành (Đã Sửa Xong)", key=f"fix_{r['id']}", use_container_width=True):
                r["is_done"] = True
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": r["machine"],
                    "content": f"[Đã sửa xong dừng máy] {r['content']}",
                    "sender": "Thợ sửa",
                    "time": current_time_str
                })
                st.success("✅ Đã sửa xong! Đã chuyển dữ liệu sang Trang 3.")
                st.rerun()

        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

# ==========================================
# TRANG 3: GIAO CA (TỰ ĐỘNG XÓA 18:00 & 05:00)
# ==========================================
elif "TRANG 3" in page:
    st.subheader("📋 Giao Ca & Chủ Quản Xem / 交接班与主管查看")
    st.caption("🕒 Dữ liệu Trang 3 sẽ tự động xoá sạch vào giờ thực tế 18:00 và 05:00 hằng ngày.")

    with st.form("form_handoff", clear_on_submit=True):
        st.markdown("### ✍️ Nhập Nội Dung Bàn Giao Ca / 填写交接")
        col_h1, col_h2 = st.columns([1, 2])
        with col_h1:
            h_sender = st.text_input("Người giao *", placeholder="Tên NV")
            h_machine = st.text_input("Tên máy *", placeholder="Tên máy")
        with col_h2:
            h_content = st.text_area("Nội dung bàn giao *", placeholder="Nội dung...")

        if st.form_submit_button("📤 GỬI BÀN GIAO CA", use_container_width=True):
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
    st.markdown("### 👁️ DỮ LIỆU GIAO CA TRONG NGÀY")

    done_tasks = [t for t in st.session_state.db["tasks"] if t["status"] == "done"]
    if done_tasks:
        st.markdown("#### ✅ Công việc đã hoàn thành trong ca")
        for dt in done_tasks:
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;">
                <strong style="color: #166534;">✓ {html.escape(dt['machine'])}</strong>
                <div style="font-size: 0.9rem; color: #15803d;">{html.escape(dt['content'])}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 🔄 Chi tiết danh sách bàn giao ca")
    h_list = st.session_state.db["handoffs"]

    if not h_list and not done_tasks:
        st.info("Chưa có nội dung bàn giao ca.")

    for idx, h in enumerate(h_list, start=1):
        st.markdown(f"""
        <div class="row-card">
            <div>
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
                pw_e = st.text_input("Mật khẩu (230) *", type="password")
                nh_m = st.text_input("Tên máy", value=h["machine"])
                nh_c = st.text_area("Nội dung", value=h["content"])
                if st.form_submit_button("Lưu sửa"):
                    if check_password(pw_e):
                        h["machine"] = nh_m
                        h["content"] = nh_c
                        st.session_state[f"pop_he_{h['id']}"] = False
                        st.success("Đã sửa!")
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")

        if st.session_state.get(f"pop_hd_{h['id']}", False):
            with st.form(f"fh_d_{h['id']}"):
                pw_d = st.text_input("Mật khẩu (230) *", type="password")
                if st.form_submit_button("Xác nhận xóa"):
                    if check_password(pw_d):
                        st.session_state.db["handoffs"].remove(h)
                        st.session_state[f"pop_hd_{h['id']}"] = False
                        st.success("Đã xóa!")
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")

        st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

# ==========================================
# BÁO CÁO TỔNG HỢP HIỆN Ở TẤT CẢ CÁC TRANG
# ==========================================
st.divider()
st.markdown("### 📸 BÁO CÁO TỔNG HỢP GỬI NHÓM / 综合报告发群")

report_text = f"""📋 **BÁO CÁO CÔNG VIỆC BẢO TRÌ / 维修工作报告**
📅 Ngày / 日期: {current_date_str} - {current_time_str}
👥 Tổng số người / 总人数: {total_staff} (Cơ khí/机械: {st.session_state.db['mechanics']}, Điện/电工: {st.session_state.db['electricians']})

1️⃣ **KẾ HOẠCH CÔNG VIỆC (TRANG 1) / 工作计划:**
"""

if st.session_state.db["tasks"]:
    for i, task in enumerate(st.session_state.db["tasks"], start=1):
        p_flag = "⭐[ƯU TIÊN] " if task["is_priority"] else ""
        st_flag = "✅[Xong]" if task["status"] == "done" else ("🔄[Giao ca]" if task["status"] == "handoff" else "⏳[Đang làm]")
        report_text += f"{i}/ {p_flag}{task['machine']} - {task['content']} ({st_flag})\n"
else:
    report_text += "(Khởi tạo / Chưa có dữ liệu)\n"

report_text += "\n2️⃣ **MÁY DỪNG SỬA (TRANG 2) / 停机维修:**\n"
if st.session_state.db["repairs"]:
    for i, rep in enumerate(st.session_state.db["repairs"], start=1):
        r_flag = "🟢[Đã xong]" if rep["is_done"] else "🔴[Đang sửa]"
        report_text += f"{i}/ {rep['machine']} - {rep['content']} ({r_flag})\n"
else:
    report_text += "(Không có máy dừng sửa)\n"

report_text += "\n3️⃣ **NỘI DUNG GIAO CA (TRANG 3) / 交接班事项:**\n"
if st.session_state.db["handoffs"]:
    for i, ho in enumerate(st.session_state.db["handoffs"], start=1):
        report_text += f"{i}/ {ho['machine']} ({ho.get('sender', 'NV')}): {ho['content']}\n"
else:
    report_text += "(Chưa có nội dung giao ca)\n"

st.text_area("Văn bản báo cáo tổng hợp / 报告文本", value=report_text, height=180)

copy_js = f"""
<script>
function copyTextToClip() {{
    const text = {json.dumps(report_text)};
    navigator.clipboard.writeText(text).then(function() {{
        alert('✅ ĐÃ SAO CHÉP BÁO CÁO THÀNH CÔNG!\\nBây giờ bạn có thể mở Zalo/WeChat và dán (Ctrl+V) vào nhóm.');
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
