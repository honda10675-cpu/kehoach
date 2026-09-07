import streamlit as st
from supabase import create_client, Client
import datetime
import pytz
import html
import re
import urllib.parse
import urllib.request
import json

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Kế Hoạch & Giao Ca / 工作计划",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
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
</style>
""", unsafe_allow_html=True)

# --- BỘ TỪ ĐIỂN KỸ THUẬT NHÀ MÁY CHUYÊN SÂU ---
DICT_SPELL_TRANS = [
    (r"\bthay\b", "THAY", "更换"),
    (r"\bthao nap\b|\btháo nắp\b", "THÁO NẮP", "拆开盖子"),
    (r"\bthao\b|\btháo\b", "THÁO", "拆卸"),
    (r"\btach\b|\btách\b", "TÁCH", "拆卸"),
    (r"\bsua\b|\bsửa\b", "SỬA", "维修"),
    (r"\blech\b|\blệch\b", "LỆCH", "偏位"),
    (r"\blap\b|\blắp\b|\brap\b|\bráp\b", "RÁP", "安装"),
    (r"\bve sinh\b|\bvệ sinh\b", "VỆ SINH", "清理"),
    (r"\bcan chinh\b|\bcăn chỉnh\b", "CĂN CHỈNH", "校准"),
    (r"\bdung may\b|\bdừng máy\b", "DỪNG MÁY", "停机"),
    (r"\bxu ly\b|\bxử lý\b", "XỬ LÝ", "处理"),
    (r"\blam\b|\blàm\b", "LÀM", "做"),
    (r"\bhu\b|\bhư\b", "HƯ", "损坏"),
    (r"\bchay sai toc do\b|\bchạy sai tốc độ\b", "CHẠY SAI TỐC ĐỘ", "运行速度错误"),
    (r"\bdinh hinh\b|\bđịnh hình\b", "ĐỊNH HÌNH", "定型"),
    (r"\bkhop xoay\b|\bkhớp xoay\b", "KHỚP XOAY", "旋转接头"),
    (r"\bnuoc\b|\bnước\b", "NƯỚC", "水"),
    (r"\bao lo keo gian\b|\báo lô kéo giản\b|\báo lô kéo giãn\b", "ÁO LÔ KÉO GIÃN", "拉伸辊套"),
    (r"\bao lo\b|\báo lô\b", "ÁO LÔ", "辊套"),
    (r"\blo keo\b|\blô kéo\b", "LÔ KÉO", "牵引辊"),
    (r"\blo\b|\blô\b", "LÔ", "压辊"),
    (r"\bkeo gian\b|\bkéo giản\b|\bkéo giãn\b", "KÉO GIÃN", "拉伸"),
    (r"\bkeo\b|\bkéo\b", "KÉO", "牵引"),
    (r"\bdau khuôn\b|\bdau khuon\b|\bđầu khuôn\b", "ĐẦU KHUÔN", "模头"),
    (r"\bkhuon\b|\bkhuôn\b", "KHUÔN", "模具"),
    (r"\bvan giam ap\b|\bvan giảm áp\b", "VAN GIẢM ÁP", "减压阀"),
    (r"\bhoi nong\b|\bhơi nóng\b", "HƠI NÓNG", "热蒸汽"),
    (r"\bbon nuoc nong\b|\bbồn nước nóng\b", "BỒN NƯỚC NÓNG", "热水箱"),
    (r"\bbac dan\b|\bvong bi\b|\bbạc đạn\b|\bvòng bi\b", "BẠC ĐẠN", "轴承"),
    (r"\bcot dao\b|\bcốt dao\b|\btruc dao\b|\btrục dao\b", "CỐT DAO", "刀轴"),
    (r"\bthu cuon nhieu vi tri mat chot\b|\bthu cuộn nhiều vị trí mất chốt\b", "THU CUỘN NHIỀU VỊ TRÍ MẤT CHỐT", "收卷多处掉销/掉卡"),
    (r"\bthu cuon\b|\bthu cuộn\b|\bcuon\b|\bcuộn\b", "THU CUỘN", "收卷"),
    (r"\bmat chot\b|\bmất chốt\b", "MẤT CHỐT", "掉销"),
    (r"\bnhieu vi tri\b|\bnhiều vị trí\b", "NHIỀU VỊ TRÍ", "多处"),
    (r"\bhop so\b|\bhộp số\b", "HỘP SỐ", "齿轮箱"),
    (r"\btruc vit\b|\btrục vít\b", "TRỤC VÍT", "螺杆"),
    (r"\btruc\b|\btrục\b", "TRỤC", "轴"),
    (r"\btach nuoc\b|\btách nước\b", "TÁCH NƯỚC", "脱水"),
    (r"\bbien tan\b|\bbiến tần\b", "BIẾN TẦN", "变频器"),
    (r"\bdong co\b|\bmotor\b|\bđộng cơ\b", "ĐỘNG CƠ", "电机"),
    (r"\bxilanh\b|\bxi lanh\b", "XI LANH", "气缸"),
    (r"\bday curoa\b|\bcu roa\b", "DÂY CUROA", "皮带"),
    (r"\bcam bien\b|\bcảm biến\b", "CẢM BIẾN", "传感器"),
    (r"\bmay dun\b|\bmáy đùn\b", "MÁY ĐÙN", "挤出机"),
    (r"\bmay ben\b|\bmáy bện\b", "MÁY BỆN", "绞线机"),
]

def clean_machine_name(name):
    if not name:
        return ""
    parts = name.split('/')
    return parts[0].strip().upper()

def translate_online_mymemory(text):
    """Hệ thống dịch trực tuyến kết hợp API online và từ điển nhà máy"""
    if not text:
        return "", ""
    if "/" in text or re.search(r'[\u4e00-\u9fff]', text):
        return text.strip().upper(), ""
        
    raw_text = text.strip()
    viet_text = raw_text.upper()
    
    # Chuẩn hóa qua từ điển chuyên ngành trước
    for pattern, vi_correct, zh_word in DICT_SPELL_TRANS:
        if re.search(pattern, viet_text, flags=re.IGNORECASE):
            viet_text = re.sub(pattern, vi_correct, viet_text, flags=re.IGNORECASE)

    # Gọi dịch online MyMemory API để dịch trọn vẹn không bị thiếu chữ
    zh_translated = ""
    try:
        encoded_text = urllib.parse.quote(raw_text)
        url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=vi|zh"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get("responseStatus") == 200:
                zh_translated = res_data.get("responseData", {}).get("translatedText", "").strip()
    except Exception:
        pass

    # Nếu dịch online lỗi, dùng từ điển bổ sung
    if not zh_translated or "MYMEMORY" in zh_translated.upper():
        zh_parts = []
        for pattern, vi_correct, zh_word in DICT_SPELL_TRANS:
            if re.search(pattern, raw_text, flags=re.IGNORECASE):
                if zh_word not in zh_parts:
                    zh_parts.append(zh_word)
        numbers = re.findall(r'\b\d+\b', raw_text)
        for num in numbers:
            if num not in zh_parts:
                zh_parts.append(num)
        zh_translated = " ".join(zh_parts) if zh_parts else viet_text

    return viet_text, zh_translated

def format_bilingual_content(raw_text):
    if not raw_text:
        return ""
    vi_cor, zh_tr = translate_online_mymemory(raw_text)
    if zh_tr:
        return f"{vi_cor} / {zh_tr}"
    return vi_cor

tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
now_vn = datetime.datetime.now(tz_vn)
current_date_str = now_vn.strftime("%d/%m/%Y")
current_time_str = now_vn.strftime("%H:%M")
current_hour = now_vn.hour
current_minute = now_vn.minute

@st.cache_resource
def get_supabase_client():
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None

supabase = get_supabase_client()

def load_data():
    if supabase:
        try:
            res = supabase.table("app_data").select("*").eq("id", 1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["content"]
        except Exception:
            pass
    return {"tasks": [], "repairs": [], "handoffs": [], "last_reset": ""}

def save_data(data):
    st.session_state.db = data
    if supabase:
        try:
            supabase.table("app_data").upsert({"id": 1, "content": data}).execute()
            return True
        except Exception as e:
            st.error(f"⚠️ Lỗi lưu dữ liệu: {e}")
            return False
    return True

if "db" not in st.session_state:
    st.session_state.db = load_data()

if "page1_authenticated" not in st.session_state:
    st.session_state.page1_authenticated = False

is_after_18 = (current_hour > 18) or (current_hour == 18 and current_minute >= 0)
is_after_05 = (current_hour > 5 or (current_hour == 5 and current_minute >= 0)) and not is_after_18

if is_after_18:
    reset_key = f"{current_date_str}_18:00"
elif is_after_05:
    reset_key = f"{current_date_str}_05:00"
else:
    reset_key = f"{current_date_str}_03:00"

if st.session_state.db.get("last_reset") != reset_key:
    if ((current_hour == 5 and current_minute <= 30) or (current_hour == 18 and current_minute <= 30)):
        st.session_state.db["handoffs"] = []
        st.session_state.db["last_reset"] = reset_key
        save_data(st.session_state.db)

def check_password(pwd):
    return pwd == "230"

def get_report_text(report_type):
    if report_type in [1, 2]:
        text = f"BÁO CÁO CÔNG VIỆC BẢO TRÌ / 维修工作报告\n"
        text += f"Ngày / 日期: {current_date_str} - {current_time_str}\n\n"
        text += "KẾ HOẠCH CÔNG VIỆC (TRANG 1) / 工作计划:\n"
        
        tasks = st.session_state.db.get("tasks", [])
        if tasks:
            for i, task in enumerate(tasks, start=1):
                clean_m = clean_machine_name(task['machine'])
                st_flag = "[ĐÃ XONG / 已完成]" if task.get("status") == "done" else ("[ĐÃ GIAO CA / 已交接]" if task.get("status") == "handoff" else "[ĐANG LÀM / 进行中]")
                text += f"{i}/ {clean_m} - {task['content'].upper()} ({st_flag})\n"
        else:
            text += "(CHƯA CÓ DỮ LIỆU / 暂无数据)\n"

        text += "\nMÁY DỪNG SỬA (TRANG 2) / 停机维修:\n"
        repairs = st.session_state.db.get("repairs", [])
        if repairs:
            for i, rep in enumerate(repairs, start=1):
                clean_m = clean_machine_name(rep['machine'])
                r_flag = "[ĐÃ XONG / 已修好]" if rep.get("is_done") else "[ĐANG SỬA / 维修中]"
                text += f"{i}/ {clean_m} - {rep['content'].upper()} ({r_flag})\n"
        else:
            text += "(KHÔNG CÓ MÁY DỪNG SỬA / 无停机维修)\n"
        return text

    elif report_type == 3:
        text = f"BÁO CÁO GIAO CA (TRANG 3) / 交接班报告\n"
        text += f"Ngày / 日期: {current_date_str} - {current_time_str}\n\n"
        text += "NỘI DUNG GIAO CA / 交接事项:\n"
        
        handoffs = st.session_state.db.get("handoffs", [])
        if handoffs:
            for i, ho in enumerate(handoffs, start=1):
                clean_m = clean_machine_name(ho['machine'])
                text += f"{i}/ {clean_m}: {ho['content'].upper()}\n"
        else:
            text += "(CHƯA CÓ NỘI DUNG GIAO CA / 暂无交接事项)\n"
        return text

def render_copy_button(page_num):
    text_content = get_report_text(page_num)
    lines = [line for line in text_content.strip().split("\n") if line]
    
    items_html = ""
    for line in lines:
        escaped = html.escape(line)
        if "BÁO CÁO" in line or "KẾ HOẠCH" in line or "MÁY DỪNG" in line or "NỘI DUNG" in line:
            items_html += f'<div style="font-weight:bold; color:#1e3a8a; margin-top:8px; border-bottom:1px solid #cbd5e1; padding-bottom:2px;">{escaped}</div>'
        else:
            items_html += f'<div style="padding:4px 0; color:#1e293b; font-size:14px; font-weight:500; border-bottom:1px dashed #e2e8f0;">{escaped}</div>'

    # Thiết lập màu nền nhạt riêng cho từng trang theo yêu cầu (Xanh, Trắng, Hồng)
    if page_num == 1:
        bg_box = "#eff6ff"  # Xanh dương nhạt
        border_box = "#3b82f6"
        title_color = "#1d4ed8"
        title_box = "📋 BẢNG TIẾN ĐỘ BẢO TRÌ (TRANG 1)"
    elif page_num == 2:
        bg_box = "#f8fafc"  # Trắng / Xám nhạt
        border_box = "#64748b"
        title_color = "#334155"
        title_box = "📋 BẢNG MÁY DỪNG SỬA (TRANG 2)"
    else:
        bg_box = "#fdf2f8"  # Hồng nhạt
        border_box = "#ec4899"
        title_color = "#be185d"
        title_box = "📋 BẢNG BÁO CÁO GIAO CA (TRANG 3)"

    custom_html = f"""
    <div id="report-box-{page_num}" style="display: block; background:{bg_box}; border:2px solid {border_box}; border-radius:10px; padding:15px; margin-bottom:12px; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <div style="text-align:center; font-weight:bold; color:{title_color}; font-size:16px; margin-bottom:10px; text-transform:uppercase;">
            {title_box}
        </div>
        <div>{items_html}</div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    function downloadCanvas_{page_num}(canvas) {{
        const link = document.createElement('a');
        link.download = 'Bao_Cao_Bao_Tri_Trang_{page_num}.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
        alert('📥 ĐÃ TẢI ẢNH VỀ MÁY!\\nAnh mở Zalo hoặc WeChat bấm chọn Tệp/Hình ảnh để gửi đi nhé.');
    }}

    function generateAndCopy_{page_num}() {{
        const element = document.getElementById('report-box-{page_num}');
        html2canvas(element, {{ scale: 2 }}).then(canvas => {{
            canvas.toBlob(blob => {{
                try {{
                    const item = new ClipboardItem({{ "image/png": blob }});
                    navigator.clipboard.write([item]).then(() => {{
                        alert('✅ ĐÃ SAO CHÉP HÌNH THÀNH CÔNG!\\nMở Zalo/WeChat bấm Dán (Ctrl+V).');
                    }}).catch(err => {{
                        downloadCanvas_{page_num}(canvas);
                    }});
                }} catch (e) {{
                    downloadCanvas_{page_num}(canvas);
                }}
            }});
        }});
    }}
    </script>
    
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <button onclick="generateAndCopy_{page_num}()" style="
            flex: 1;
            min-width: 200px;
            background: #2563eb;
            color: white;
            border: none;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 10px;
        ">
            📋 SAO CHÉP HÌNH (MÁY TÍNH)
        </button>
        <button onclick="html2canvas(document.getElementById('report-box-{page_num}'), {{ scale: 2 }}).then(c => downloadCanvas_{page_num}(c))" style="
            flex: 1;
            min-width: 200px;
            background: #059669;
            color: white;
            border: none;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 10px;
        ">
            📥 TẢI HÌNH VỀ ĐIỆN THOẠI (ZALO/WECHAT)
        </button>
    </div>
    """
    comp_height = 500 if page_num in [1, 2] else 380
    st.components.v1.html(custom_html, height=comp_height, scrolling=True)

st.markdown("<h3 style='text-align: center; color: #0f172a; margin-bottom: 5px; text-transform: uppercase;'>QUẢN LÝ BẢO TRÌ MÁY / 设备维修管理</h3>", unsafe_allow_html=True)

page = st.radio(
    "",
    ["TRANG 1: KẾ HOẠCH / 1. 工作计划", "TRANG 2: DỪNG MÁY / 2. 停机维修", "TRANG 3: GIAO CA / 3. 交接班"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# TRANG 1: KẾ HOẠCH
if "TRANG 1" in page:
    if not st.session_state.page1_authenticated:
        st.subheader("🔒 YÊU CẦU MẬT KHẨU TRUY CẬP TRANG 1 / 验证密码")
        with st.form("form_pass_p1"):
            pass_in = st.text_input("Nhập Mật Khẩu / 输入密码 *", type="password")
            if st.form_submit_button("XÁC NHẬN / 确认"):
                if pass_in == "789":
                    st.session_state.page1_authenticated = True
                    st.rerun()
                else:
                    st.error("Mật khẩu không đúng / 密码错误!")
    else:
        st.subheader("GHI KẾ HOẠCH CÔNG VIỆC NGÀY / 每日工作计划登记")
        render_copy_button(1)

        st.markdown("### DANH SÁCH CÔNG VIỆC / 工作列表")
        pending_list = [t for t in st.session_state.db.get("tasks", []) if t.get("status") == "pending"]

        if not pending_list:
            st.info("Chưa có công việc nào trong danh sách / 暂无工作计划")
        else:
            for idx, t in enumerate(pending_list, start=1):
                card_style = "row-card-priority" if t.get("is_priority") else "row-card"
                prio_tag = "[ƯU TIÊN / 优先]" if t.get("is_priority") else ""

                st.markdown(f"""
                <div class="{card_style}">
                    <strong>{idx}/ {html.escape(t['machine'])}</strong> <span style="color:#d97706; font-weight:bold;">{prio_tag}</span><br>
                    <span style="color: #475569; font-size: 0.95rem;">Nội dung / 内容: <strong>{html.escape(t['content'])}</strong></span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### THAO TÁC CÔNG VIỆC / 工作操作")
            
            task_options = {f"{idx}/ {t['machine']} - {t['content']}": t for idx, t in enumerate(pending_list, start=1)}
            selected_task_label = st.selectbox("Chọn máy cần thao tác / 选择要操作的设备:", list(task_options.keys()))
            selected_task = task_options[selected_task_label]

            col_act1, col_act2, col_act3, col_act4 = st.columns(4)
            with col_act1:
                if st.button("Hoàn Thành / 完成", use_container_width=True):
                    selected_task["status"] = "done"
                    save_data(st.session_state.db)
                    st.rerun()

            with col_act2:
                if st.button("Giao Ca / 交接", use_container_width=True):
                    st.session_state["show_pop_handoff"] = True

            with col_act3:
                if st.button("Sửa / 编辑", use_container_width=True):
                    st.session_state["show_pop_edit"] = True

            with col_act4:
                if st.button("Xóa / 删除", use_container_width=True):
                    st.session_state["show_pop_del"] = True

            if st.session_state.get("show_pop_handoff", False):
                with st.form("form_pop_handoff"):
                    st.markdown(f"GIAO CA CHO MÁY / 交接设备: **{selected_task['machine']}**")
                    progress_txt = st.text_input("Tiến Độ Hiện Tại / 当前进度 *", placeholder="Ví dụ: Đã làm 80%")
                    next_task_txt = st.text_area("Kế Hoạch Ca Sau / 下班计划 *", placeholder="Ví dụ: Tiếp tục lắp ráp")
                    if st.form_submit_button("Xác Nhận Bàn Giao / 确认交接"):
                        if progress_txt.strip() and next_task_txt.strip():
                            selected_task["status"] = "handoff"
                            formatted_handoff = format_bilingual_content(f"Tiến độ: {progress_txt} - Kế hoạch tiếp: {next_task_txt}")
                            if "handoffs" not in st.session_state.db:
                                st.session_state.db["handoffs"] = []
                            st.session_state.db["handoffs"].append({
                                "id": len(st.session_state.db["handoffs"]) + 1,
                                "machine": clean_machine_name(selected_task["machine"]),
                                "content": formatted_handoff,
                                "sender": "Chuyển ca / 移交",
                                "time": current_time_str
                            })
                            save_data(st.session_state.db)
                            st.session_state["show_pop_handoff"] = False
                            st.rerun()
                        else:
                            st.error("Bắt buộc điền đầy đủ / 请填写完整")

            if st.session_state.get("show_pop_edit", False):
                with st.form("form_pop_edit"):
                    st.markdown(f"SỬA CÔNG VIỆC / 编辑工作: **{selected_task['machine']}**")
                    pwd_in = st.text_input("Mật khẩu / 密码 *", type="password")
                    e_mach = st.text_input("Tên Máy / 设备名称", value=selected_task["machine"])
                    e_cont = st.text_area("Nội dung / 内容", value=selected_task["content"])
                    e_prio = st.checkbox("Ưu tiên / 优先", value=selected_task.get("is_priority", False))
                    if st.form_submit_button("Lưu Thay Đổi / 保存"):
                        if check_password(pwd_in):
                            selected_task["machine"] = format_bilingual_content(e_mach)
                            selected_task["content"] = format_bilingual_content(e_cont)
                            selected_task["is_priority"] = e_prio
                            save_data(st.session_state.db)
                            st.session_state["show_pop_edit"] = False
                            st.rerun()
                        else:
                            st.error("Mật khẩu không đúng / 密码错误")

            if st.session_state.get("show_pop_del", False):
                with st.form("form_pop_del"):
                    st.markdown(f"XÓA CÔNG VIỆC / 删除工作: **{selected_task['machine']}**")
                    pwd_in2 = st.text_input("Mật khẩu / 密码 *", type="password")
                    if st.form_submit_button("Xác Nhận Xóa / 确认删除"):
                        if check_password(pwd_in2):
                            st.session_state.db["tasks"].remove(selected_task)
                            save_data(st.session_state.db)
                            st.session_state["show_pop_del"] = False
                            st.rerun()
                        else:
                            st.error("Mật khẩu không đúng / 密码错误")

        st.divider()
        with st.form("form_add_task", clear_on_submit=True):
            st.markdown("### NHẬP CÔNG VIỆC MỚI / 添加新工作")
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                t_machine = st.text_input("Công việc và Máy / 设备与工作 *", placeholder="Ví dụ: PE21")
            with col_t2:
                t_prio = st.checkbox("Ưu tiên / 优先")

            t_content = st.text_area("Nội dung chi tiết / 详细内容 *", placeholder="Ví dụ: Ráp áo lô kéo giản 2")
            
            if st.form_submit_button("LƯU CÔNG VIỆC / 保存工作", use_container_width=True):
                if t_machine.strip() and t_content.strip():
                    bilingual_machine = format_bilingual_content(t_machine)
                    bilingual_content = format_bilingual_content(t_content)
                    
                    new_item = {
                        "id": len(st.session_state.db.get("tasks", [])) + 1,
                        "machine": bilingual_machine,
                        "content": bilingual_content,
                        "is_priority": t_prio,
                        "status": "pending",
                        "time": current_time_str
                    }
                    if "tasks" not in st.session_state.db:
                        st.session_state.db["tasks"] = []
                    
                    st.session_state.db["tasks"].append(new_item)
                    if save_data(st.session_state.db):
                        st.rerun()
                else:
                    st.error("Vui lòng điền đầy đủ thông tin (*) / 请填写完整")

# TRANG 2: DỪNG MÁY SỬA
elif "TRANG 2" in page:
    st.subheader("GHI CHÚ DỪNG MÁY SỬA / 停机维修记录")
    render_copy_button(2)

    with st.form("form_repair", clear_on_submit=True):
        st.markdown("### BÁO DỪNG MÁY SỬA MỚI / 登记停机维修")
        r_machine = st.text_input("Tên Máy Dừng / 停机设备 *", placeholder="Ví dụ: PE66")
        r_content = st.text_area("Sự cố & Nội dung sửa / 故障与维修内容 *", placeholder="Ví dụ: Thay van giảm áp hơi nóng")
        
        if st.form_submit_button("BÁO DỪNG MÁY / 提交停机", use_container_width=True):
            if r_machine.strip() and r_content.strip():
                if "repairs" not in st.session_state.db:
                    st.session_state.db["repairs"] = []
                bilingual_r_machine = format_bilingual_content(r_machine)
                bilingual_r_content = format_bilingual_content(r_content)
                st.session_state.db["repairs"].append({
                    "id": len(st.session_state.db["repairs"]) + 1,
                    "machine": bilingual_r_machine,
                    "content": bilingual_r_content,
                    "is_done": False,
                    "time": current_time_str
                })
                if save_data(st.session_state.db):
                    st.rerun()
            else:
                st.error("Bắt buộc điền thông tin (*) / 请填写完整")

    st.divider()
    st.markdown("### DANH SÁCH MÁY DỪNG SỬA / 停机维修列表")
    repairs_list = st.session_state.db.get("repairs", [])
    if not repairs_list:
        st.info("Hiện không có máy dừng sửa / 暂无停机维修")

    for r in repairs_list:
        st_color = "#10b981" if r.get("is_done") else "#ef4444"
        st_text = "ĐÃ SỬA XONG / 已修好" if r.get("is_done") else "ĐANG SỬA / 维修中"

        st.markdown(f"""
        <div style="border-left: 5px solid {st_color}; background: #ffffff; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between;">
                <strong>{html.escape(r['machine'])}</strong>
                <span style="color: {st_color}; font-weight: bold;">{st_text}</span>
            </div>
            <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">{r['time']}</div>
            <div style="font-size: 0.95rem; color: #0f172a; margin-top: 4px;">Nội dung / 内容: <strong>{html.escape(r['content'])}</strong></div>
        </div>
        """, unsafe_allow_html=True)

        if not r.get("is_done"):
            if st.button("Tích Hoàn Thành (Đã Sửa Xong) / 完成", key=f"fix_{r['id']}", use_container_width=True):
                r["is_done"] = True
                if "handoffs" not in st.session_state.db:
                    st.session_state.db["handoffs"] = []
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": clean_machine_name(r["machine"]),
                    "content": f"[ĐÃ SỬA XONG / 已修好] {r['content']}",
                    "sender": "Thợ sửa / 维修工",
                    "time": current_time_str
                })
                save_data(st.session_state.db)
                st.rerun()

# TRANG 3: GIAO CA
elif "TRANG 3" in page:
    st.subheader("GIAO CA / 交接班")
    st.caption("Dữ liệu Trang 3 sẽ tự động xoá sạch vào lúc 05:00 và 18:00 hằng ngày / 数据将在每天 05:00 和 18:00 自动清空。")

    render_copy_button(3)

    col_r1, col_r2 = st.columns([2, 1])
    with col_r2:
        if st.button("🔄 RESET LÀM SẠCH BẢNG GIAO CA", use_container_width=True):
            st.session_state["show_pop_reset_ho"] = True

    if st.session_state.get("show_pop_reset_ho", False):
        with st.form("form_reset_ho"):
            st.markdown("⚠️ **Xác nhận làm sạch toàn bộ Trang 3 để điền ca mới:**")
            pw_reset = st.text_input("Mật khẩu quản lý / 密码 *", type="password")
            if st.form_submit_button("XÁC NHẬN RESET LÀM SẠCH / 确认清空"):
                if check_password(pw_reset):
                    st.session_state.db["handoffs"] = []
                    save_data(st.session_state.db)
                    st.session_state["show_pop_reset_ho"] = False
                    st.success("Đã làm sạch Trang 3 thành công!")
                    st.rerun()
                else:
                    st.error("Sai mật khẩu / 密码错误!")

    with st.form("form_handoff", clear_on_submit=True):
        st.markdown("### NHẬP NỘI DUNG BÀN GIAO CA / 填写交接内容")
        col_h1, col_h2 = st.columns([1, 2])
        with col_h1:
            h_sender = st.text_input("Người giao / 交接人 *", placeholder="Tên NV")
            h_machine = st.text_input("Tên máy / 设备 *", placeholder="Tên máy")
        with col_h2:
            h_content = st.text_area("Nội dung bàn giao / 交接内容 *", placeholder="Ví dụ: Thay bạc đạn cốt dao")

        if st.form_submit_button("GỬI BÀN GIAO CA / 提交交接", use_container_width=True):
            if h_sender.strip() and h_machine.strip() and h_content.strip():
                if "handoffs" not in st.session_state.db:
                    st.session_state.db["handoffs"] = []
                bilingual_h_machine = clean_machine_name(h_machine)
                bilingual_h_content = format_bilingual_content(h_content)
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": bilingual_h_machine,
                    "sender": h_sender.strip(),
                    "content": bilingual_h_content,
                    "time": current_time_str
                })
                if save_data(st.session_state.db):
                    st.rerun()
            else:
                st.error("Vui lòng nhập đầy đủ (*) / 请填写完整")

    st.divider()
    st.markdown("### DỮ LIỆU GIAO CA TRONG NGÀY / 当天交接数据")

    done_tasks = [t for t in st.session_state.db.get("tasks", []) if t.get("status") == "done"]
    if done_tasks:
        st.markdown("#### Công việc đã hoàn thành / 已完成工作")
        for dt in done_tasks:
            clean_dt_m = clean_machine_name(dt['machine'])
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;">
                <strong style="color: #166534;">{html.escape(clean_dt_m)}</strong>
                <div style="font-size: 0.9rem; color: #15803d;">{html.escape(dt['content'])}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### Chi tiết danh sách bàn giao ca / 交接明细")
    h_list = st.session_state.db.get("handoffs", [])

    if not h_list and not done_tasks:
        st.info("Chưa có nội dung bàn giao ca / 暂无交接内容")
    else:
        for idx, h in enumerate(h_list, start=1):
            clean_h_m = clean_machine_name(h['machine'])
            st.markdown(f"""
            <div class="row-card">
                <strong>{idx}/ {html.escape(clean_h_m)}</strong> (Người giao / 交接人: {html.escape(h.get('sender', 'NV'))}) - <span style="color: #64748b; font-size: 0.85rem;">{h['time']}</span><br>
                <span style="color: #1e293b; font-size: 0.95rem;">Nội dung / 内容: <strong>{html.escape(h['content'])}</strong></span>
            </div>
            """, unsafe_allow_html=True)

        if h_list:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### THAO TÁC GIAO CA / 交接操作")
            ho_options = {f"{idx}/ {clean_machine_name(h['machine'])} - {h['content']}": h for idx, h in enumerate(h_list, start=1)}
            selected_ho_label = st.selectbox("Chọn mục giao ca cần thao tác / 选择交接项:", list(ho_options.keys()))
            selected_ho = ho_options[selected_ho_label]

            col_he, col_hd = st.columns(2)
            with col_he:
                if st.button("Sửa / 编辑", use_container_width=True):
                    st.session_state["show_pop_ho_edit"] = True
            with col_hd:
                if st.button("Xóa / 删除", use_container_width=True):
                    st.session_state["show_pop_ho_del"] = True

            if st.session_state.get("show_pop_ho_edit", False):
                with st.form("form_ho_edit"):
                    pw_e = st.text_input("Mật khẩu / 密码 *", type="password")
                    nh_m = st.text_input("Tên máy / 设备", value=selected_ho["machine"])
                    nh_c = st.text_area("Nội dung / 内容", value=selected_ho["content"])
                    if st.form_submit_button("Lưu sửa / 保存"):
                        if check_password(pw_e):
                            selected_ho["machine"] = clean_machine_name(nh_m)
                            selected_ho["content"] = format_bilingual_content(nh_c)
                            save_data(st.session_state.db)
                            st.session_state["show_pop_ho_edit"] = False
                            st.rerun()
                        else:
                            st.error("Sai mật khẩu / 密码错误!")

            if st.session_state.get("show_pop_ho_del", False):
                with st.form("form_ho_del"):
                    pw_d = st.text_input("Mật khẩu / 密码 *", type="password")
                    if st.form_submit_button("Xác nhận xóa / 确认删除"):
                        if check_password(pw_d):
                            st.session_state.db["handoffs"].remove(selected_ho)
                            save_data(st.session_state.db)
                            st.session_state["show_pop_ho_del"] = False
                            st.rerun()
                        else:
                            st.error("Sai mật khẩu / 密码错误!")
