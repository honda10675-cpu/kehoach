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

# --- BỘ CHUYỂN ĐỔI CHUYÊN NGÀNH OFFLINE (KHÔNG PHỤ THUỘC GOOGLE) ---
TELEX_FIX = [
    (r"\bddijnhj\b|\bdijnh\b|\bdinh hinh\b", "định hình"),
    (r"\braap\b|\brap\b", "Ráp"),
    (r"\bao lo\b|\bao loi\b", "áo lô"),
    (r"\bkeo gian\b|\bkeo daxn\b", "kéo giản"),
    (r"\bluoi loc hat\b|\bluoi loc\b", "lưới lọc hạt"),
    (r"\bkhop noi xoay\b|\bkhop noi\b", "khớp nối xoay"),
    (r"\bdung may\b", "dừng máy"),
    (r"\bvan giam ap\b", "van giảm áp"),
    (r"\bbon nuoc nong\b", "bồn nước nóng"),
    (r"\bhop so\b", "hộp số"),
    (r"\btruc vit\b", "trục vít"),
    (r"\btach nuoc\b", "tách nước"),
    (r"\bthu cuon\b", "thu cuộn"),
    (r"\bxi lieu\b|\bxi leiu\b", "xì liệu"),
    (r"\bkhu luoi\b", "khu lưới"),
]

DICT_TERMS = [
    (r"thay", "更换"),
    (r"sửa", "维修"),
    (r"ráp", "安装"),
    (r"vệ sinh", "清洗"),
    (r"căn chỉnh", "校准"),
    (r"làm", "制作"),
    (r"khu lưới a", "A网区"),
    (r"khu lưới b", "B网区"),
    (r"khu lưới", "网区"),
    (r"xì liệu", "漏料"),
    (r"trục tách nước", "脱水轴"),
    (r"lô kéo giản", "牵伸辊"),
    (r"lô định hình", "定型辊"),
    (r"khớp nối xoay nước", "水旋转接头"),
    (r"sai tốc độ", "速度异常"),
    (r"hư", "损坏"),
    (r"hộp số", "齿轮箱"),
    (r"trục vít", "螺杆轴"),
    (r"áo lô", "辊套"),
    (r"thu cuộn", "收卷"),
    (r"lưới lọc hạt", "颗粒过滤网"),
    (r"lỗ", "孔"),
    (r"dài", "长"),
]

def clean_vietnamese_text(text):
    if not text:
        return ""
    txt = text.strip()
    for pattern, replace_val in TELEX_FIX:
        txt = re.sub(pattern, replace_val, txt, flags=re.IGNORECASE)
    return txt

def offline_translate(text_segment):
    if not text_segment:
        return ""
    res = text_segment.lower()
    for pattern, zh_val in DICT_TERMS:
        res = re.sub(pattern, zh_val, res, flags=re.IGNORECASE)
    
    # Loại bỏ các từ tiếng Việt còn sót lại nếu dịch không hết
    res = re.sub(r'[a-zA-Zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+', '', res)
    return res.strip()

def google_translate_api(text_segment):
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=vi&tl=zh-CN&dt=t&q=" + urllib.parse.quote(text_segment)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=3)
        result = json.loads(response.read().decode('utf-8'))
        
        translated_text = ""
        for sentence in result[0]:
            if sentence[0]:
                translated_text += sentence[0]
        return translated_text.strip()
    except Exception:
        return ""

def translate_to_zh(text):
    if not text or not text.strip():
        return ""
    
    cleaned_text = clean_vietnamese_text(text)
    
    # Thử dịch bằng Google API trước
    zh_text = google_translate_api(cleaned_text)
    
    # Nếu Google bị chặn/lỗi, dùng bộ dịch Offline chuyên ngành
    if not zh_text or zh_text.lower() == cleaned_text.lower():
        parts = re.split(r'([,，;；])', cleaned_text)
        translated_parts = []
        for part in parts:
            if part in [',', '，', ';', '；']:
                translated_parts.append(part + " ")
            elif part.strip():
                zh_seg = offline_translate(part.strip())
                translated_parts.append(zh_seg if zh_seg else part.strip())
        zh_text = "".join(translated_parts).strip()
        
    return zh_text

def make_bilingual(text):
    if not text:
        return ""
    
    # Nếu chuỗi đã chứa dấu "/" tức là đã có dịch trước đó, tiến hành tách phần tiếng Việt ra dịch lại
    if "/" in text:
        text = text.split("/")[0].strip()

    clean_txt = clean_vietnamese_text(text)
    zh_txt = translate_to_zh(clean_txt)
    
    if zh_txt and zh_txt.strip() != clean_txt.strip():
        return f"{clean_txt} / {zh_txt}"
    return clean_txt

tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
now_vn = datetime.datetime.now(tz_vn)
current_date_str = now_vn.strftime("%d/%m/%Y")
current_time_str = now_vn.strftime("%H:%M")
current_hour = now_vn.hour
current_minute = now_vn.minute

# --- SUPABASE DATABASE ---
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

reset_key = f"{current_date_str}_{18 if current_hour >= 18 else (5 if current_hour >= 5 else 0)}"
if st.session_state.db.get("last_reset") != reset_key:
    if (current_hour == 5 and current_minute < 30) or (current_hour == 18 and current_minute < 30):
        st.session_state.db["handoffs"] = []
        st.session_state.db["last_reset"] = reset_key
        save_data(st.session_state.db)

def check_password(pwd):
    return pwd == "230"

# --- BÁO CÁO ---
report_text_p1_p2 = f"""BÁO CÁO CÔNG VIỆC BẢO TRÌ / 维修工作报告
Ngày / 日期: {current_date_str} - {current_time_str}

KẾ HOẠCH CÔNG VIỆC (TRANG 1) / 工作计划:
"""
if st.session_state.db.get("tasks"):
    for i, task in enumerate(st.session_state.db["tasks"], start=1):
        p_flag = "[ƯU TIÊN / 优先] " if task.get("is_priority") else ""
        st_flag = "[Đã xong / 已完成]" if task.get("status") == "done" else ("[Đã giao ca / 已交接]" if task.get("status") == "handoff" else "[Đang làm / 进行中]")
        report_text_p1_p2 += f"{i}/ {task['machine']} - {task['content']} ({st_flag})\n"
else:
    report_text_p1_p2 += "(Chưa có dữ liệu / 暂无数据)\n"

report_text_p1_p2 += f"""
MÁY DỪNG SỬA (TRANG 2) / 停机维修:
"""
if st.session_state.db.get("repairs"):
    for i, rep in enumerate(st.session_state.db["repairs"], start=1):
        r_flag = "[Đã xong / 已完成]" if rep.get("is_done") else "[Đang sửa / 维修中]"
        report_text_p1_p2 += f"{i}/ {rep['machine']} - {rep['content']} ({r_flag})\n"
else:
    report_text_p1_p2 += "(Không có máy dừng sửa / 无停机维修)\n"

report_text_p3_only = f"""BÁO CÁO GIAO CA (TRANG 3) / 交接班报告
Ngày / 日期: {current_date_str} - {current_time_str}

NỘI DUNG GIAO CA / 交接班事项:
"""
if st.session_state.db.get("handoffs"):
    for i, ho in enumerate(st.session_state.db["handoffs"], start=1):
        report_text_p3_only += f"{i}/ {ho['machine']} (Người giao / 交接人: {ho.get('sender', 'NV')}): {ho['content']}\n"
else:
    report_text_p3_only += "(Chưa có nội dung giao ca / 暂无交接事项)\n"

def render_copy_button(page_num):
    text_content = report_text_p3_only if page_num == 3 else report_text_p1_p2
    lines = [line for line in text_content.strip().split("\n") if line]
    
    items_html = ""
    for line in lines:
        escaped = html.escape(line)
        if "BÁO CÁO" in line or "KẾ HOẠCH" in line or "MÁY DỪNG" in line or "NỘI DUNG" in line:
            items_html += f'<div style="font-weight:bold; color:#1e3a8a; margin-top:8px; border-bottom:1px solid #e2e8f0; padding-bottom:2px;">{escaped}</div>'
        else:
            items_html += f'<div style="padding:4px 0; color:#334155; font-size:14px; border-bottom:1px dashed #f1f5f9;">{escaped}</div>'

    custom_html = f"""
    <div id="report-box-{page_num}" style="display: block; background:#ffffff; border:2px solid #2563eb; border-radius:10px; padding:15px; margin-bottom:12px; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <div style="text-align:center; font-weight:bold; color:#2563eb; font-size:16px; margin-bottom:10px;">
            📋 BẢNG TIẾN ĐỘ BẢO TRÌ / 维修进度表
        </div>
        <div>{items_html}</div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    function generateAndCopy_{page_num}() {{
        const element = document.getElementById('report-box-{page_num}');
        html2canvas(element, {{ scale: 2 }}).then(canvas => {{
            canvas.toBlob(blob => {{
                try {{
                    const item = new ClipboardItem({{ "image/png": blob }});
                    navigator.clipboard.write([item]).then(() => {{
                        alert('✅ ĐÃ SAO CHÉP HÌNH BẢNG THÀNH CÔNG!\\nAnh mở Zalo hoặc WeChat nhấn Dán (Ctrl+V) để gửi.');
                    }}).catch(err => {{
                        openImageWin(canvas);
                    }});
                }} catch (e) {{
                    openImageWin(canvas);
                }}
            }});
        }});
    }}

    function openImageWin(canvas) {{
        const win = window.open("");
        win.document.write('<p style="font-family:sans-serif; font-size:16px; font-weight:bold; color:#2563eb;">Ấn giữ vào hình chọn "Sao chép hình ảnh" hoặc "Tải về" để gửi Zalo/WeChat:</p>');
        win.document.write('<img src="' + canvas.toDataURL() + '" style="border:1px solid #ccc; max-width:100%;" />');
    }}
    </script>
    
    <button onclick="generateAndCopy_{page_num}()" style="
        width: 100%;
        background: #2563eb;
        color: white;
        border: none;
        padding: 12px;
        font-size: 15px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        margin-bottom: 10px;
    ">
        📷 SAO CHÉP HÌNH BẢNG GỬI ZALO/WECHAT
    </button>
    """
    comp_height = 320 if page_num == 3 else 420
    st.components.v1.html(custom_html, height=comp_height, scrolling=True)

# --- TIÊU ĐỀ ---
st.markdown("<h3 style='text-align: center; color: #0f172a; margin-bottom: 5px;'>QUẢN LÝ BẢO TRÌ MÁY / 设备维修管理</h3>", unsafe_allow_html=True)

page = st.radio(
    "",
    ["TRANG 1: KẾ HOẠCH / 1. 工作计划", "TRANG 2: DỪNG MÁY / 2. 停机维修", "TRANG 3: GIAO CA / 3. 交接班"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# --- TRANG 1 ---
if "TRANG 1" in page:
    if not st.session_state.page1_authenticated:
        st.subheader("🔒 Yêu cầu mật khẩu truy cập Trang 1 / 验证密码")
        with st.form("form_pass_p1"):
            pass_in = st.text_input("Nhập Mật Khẩu / 输入密码 *", type="password")
            if st.form_submit_button("XÁC NHẬN / 确认"):
                if pass_in == "789":
                    st.session_state.page1_authenticated = True
                    st.rerun()
                else:
                    st.error("Mật khẩu không đúng / 密码错误!")
    else:
        st.subheader("Ghi Kế Hoạch Công Việc Ngày / 每日工作计划登记")
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
                            combined = f"[Tiến độ: {progress_txt}] - Kế hoạch tiếp: {next_task_txt}"
                            formatted_handoff = make_bilingual(combined)
                            if "handoffs" not in st.session_state.db:
                                st.session_state.db["handoffs"] = []
                            st.session_state.db["handoffs"].append({
                                "id": len(st.session_state.db["handoffs"]) + 1,
                                "machine": selected_task["machine"],
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
                    
                    # Tách lấy phần tiếng Việt ban đầu để hiển thị trong ô nhập
                    raw_content = selected_task["content"].split("/")[0].strip() if "/" in selected_task["content"] else selected_task["content"]
                    
                    e_mach = st.text_input("Tên Máy / 设备名称", value=selected_task["machine"])
                    e_cont = st.text_area("Nội dung / 内容", value=raw_content)
                    e_prio = st.checkbox("Ưu tiên / 优先", value=selected_task.get("is_priority", False))
                    if st.form_submit_button("Lưu Thay Đổi / 保存"):
                        if check_password(pwd_in):
                            selected_task["machine"] = e_mach
                            selected_task["content"] = make_bilingual(e_cont)
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
            st.markdown("### Nhập Công Việc Mới / 添加新工作")
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                t_machine = st.text_input("Công việc và Máy / 设备与工作 *", placeholder="Ví dụ: DKW2")
            with col_t2:
                t_prio = st.checkbox("Ưu tiên / 优先")

            t_content = st.text_area("Nội dung chi tiết / 详细内容 *", placeholder="Ví dụ: thay dau khuon PE1")
            
            if st.form_submit_button("LƯU CÔNG VIỆC / 保存工作", use_container_width=True):
                if t_machine.strip() and t_content.strip():
                    with st.spinner("Đang xử lý dịch song ngữ..."):
                        bilingual_content = make_bilingual(t_content)
                    new_item = {
                        "id": len(st.session_state.db.get("tasks", [])) + 1,
                        "machine": t_machine.strip(),
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

# --- TRANG 2 ---
elif "TRANG 2" in page:
    st.subheader("Ghi Chú Dừng Máy Sửa / 停机维修记录")
    render_copy_button(2)

    with st.form("form_repair", clear_on_submit=True):
        st.markdown("### Báo Dừng Máy Sửa Mới / 登记停机维修")
        r_machine = st.text_input("Tên Máy Dừng / 停机设备 *", placeholder="Ví dụ: PE66")
        r_content = st.text_area("Sự cố & Nội dung sửa / 故障与维修内容 *", placeholder="Ví dụ: dung may thay van giam ap hoi nong bon nuoc nong")
        
        if st.form_submit_button("BÁO DỪNG MÁY / 提交停机", use_container_width=True):
            if r_machine.strip() and r_content.strip():
                with st.spinner("Đang xử lý dịch song ngữ..."):
                    bilingual_r_content = make_bilingual(r_content)
                if "repairs" not in st.session_state.db:
                    st.session_state.db["repairs"] = []
                st.session_state.db["repairs"].append({
                    "id": len(st.session_state.db["repairs"]) + 1,
                    "machine": r_machine.strip(),
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
                    "machine": r["machine"],
                    "content": f"[Đã sửa xong / 已修好] {r['content']}",
                    "sender": "Thợ sửa / 维修工",
                    "time": current_time_str
                })
                save_data(st.session_state.db)
                st.rerun()

# --- TRANG 3 ---
elif "TRANG 3" in page:
    st.subheader("Giao Ca / 交接班")
    st.caption("Dữ liệu Trang 3 sẽ tự động xoá sạch vào 18:00 và 05:00 hằng ngày / 数据将在每天 18:00 和 05:00 自动清空。")

    render_copy_button(3)

    with st.form("form_handoff", clear_on_submit=True):
        st.markdown("### Nhập Nội Dung Bàn Giao Ca / 填写交接内容")
        col_h1, col_h2 = st.columns([1, 2])
        with col_h1:
            h_sender = st.text_input("Người giao / 交接人 *", placeholder="Tên NV")
            h_machine = st.text_input("Tên máy / 设备 *", placeholder="Tên máy")
        with col_h2:
            h_content = st.text_area("Nội dung bàn giao / 交接内容 *", placeholder="Ví dụ: thay bac dan cot dao")

        if st.form_submit_button("GỬI BÀN GIAO CA / 提交交接", use_container_width=True):
            if h_sender.strip() and h_machine.strip() and h_content.strip():
                with st.spinner("Đang xử lý dịch song ngữ..."):
                    bilingual_h_content = make_bilingual(h_content)
                if "handoffs" not in st.session_state.db:
                    st.session_state.db["handoffs"] = []
                st.session_state.db["handoffs"].append({
                    "id": len(st.session_state.db["handoffs"]) + 1,
                    "machine": h_machine.strip(),
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
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px;">
                <strong style="color: #166534;">{html.escape(dt['machine'])}</strong>
                <div style="font-size: 0.9rem; color: #15803d;">{html.escape(dt['content'])}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### Chi tiết danh sách bàn giao ca / 交接明细")
    h_list = st.session_state.db.get("handoffs", [])

    if not h_list and not done_tasks:
        st.info("Chưa có nội dung bàn giao ca / 暂无交接内容")
    else:
        for idx, h in enumerate(h_list, start=1):
            st.markdown(f"""
            <div class="row-card">
                <strong>{idx}/ {html.escape(h['machine'])}</strong> (Người giao / 交接人: {html.escape(h.get('sender', 'NV'))}) - <span style="color: #64748b; font-size: 0.85rem;">{h['time']}</span><br>
                <span style="color: #1e293b; font-size: 0.95rem;">Nội dung / 内容: <strong>{html.escape(h['content'])}</strong></span>
            </div>
            """, unsafe_allow_html=True)

        if h_list:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### THAO TÁC GIAO CA / 交接操作")
            ho_options = {f"{idx}/ {h['machine']} - {h['content']}": h for idx, h in enumerate(h_list, start=1)}
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
                    
                    raw_ho_content = selected_ho["content"].split("/")[0].strip() if "/" in selected_ho["content"] else selected_ho["content"]
                    
                    nh_m = st.text_input("Tên máy / 设备", value=selected_ho["machine"])
                    nh_c = st.text_area("Nội dung / 内容", value=raw_ho_content)
                    if st.form_submit_button("Lưu sửa / 保存"):
                        if check_password(pw_e):
                            with st.spinner("Đang xử lý dịch song ngữ..."):
                                selected_ho["machine"] = nh_m
                                selected_ho["content"] = make_bilingual(nh_c)
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
