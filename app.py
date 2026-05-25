import streamlit as st
import pandas as pd
import json
import requests
import base64
import re
from datetime import datetime
from io import BytesIO
from xhtml2pdf import pisa  # ספרייה להפקת PDF אמיתי

# =============================================================================
# 1. הגדרות עיצוב ומערכת (RTL ומראה נקי)
# =============================================================================
st.set_page_config(
    page_title="מערכת תמחור וחיתוך - Elad Cohen Iron Art", 
    layout="wide"
)

# החלת עיצוב CSS מותאם אישית לתמיכה מלאה בעברית (RTL) ואסתטיקה של האפליקציה
st.markdown("""
    <style>
    body, .main, div.stMarkdown, div[data-testid="stWidgetLabel"] {
        direction: rtl !important;
        text-align: right !important;
    }
    div[data-testid="stDataEditor"] {
        direction: rtl !important;
    }
    div[data-baseweb="slider"] {
        direction: ltr !important;
    }
    .material-block {
        border: 2px solid #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        background-color: #fafbfc;
        margin-bottom: 20px;
        direction: rtl;
    }
    .customer-info-box {
        background-color: #e9fac8;
        border: 1px solid #a0d911;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .top-project-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. חיבור מאובטח ל-GitHub API
# =============================================================================
GITHUB_USERNAME = "eladccc5"
GITHUB_REPO = "metal-app"

if "GITHUB_TOKEN" in st.secrets:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
else:
    GITHUB_TOKEN = ""

def get_initial_catalog():
    return {
        "פרופיל מרובע": {
            "dimensions": ["20x20", "25x25", "30x30", "40x40", "50x50", "60x60", "80x80", "100x100", "120x120"], 
            "thicknesses": ["1.5 מ\"מ", "2.0 מ\"מ", "2.5 מ\"מ", "3.0 מ\"מ"], 
            "length": 600, 
            "prices": {}
        },
        "פרופיל מלבני": {
            "dimensions": ["40x20", "50x20", "50x25", "60x40", "80x40", "100x40", "100x50", "150x50"], 
            "thicknesses": ["1.5 מ\"מ", "2.0 מ\"מ", "2.5 מ\"מ", "3.0 מ\"מ"], 
            "length": 600, 
            "prices": {}
        },
        "שטוח": {
            "dimensions": ["20 מ\"מ", "25 מ\"מ", "30 מ\"מ", "35 מ\"מ", "40 מ\"מ", "50 מ\"מ", "60 מ\"מ", "80 מ\"מ", "100 מ\"מ"], 
            "thicknesses": ["3 מ\"מ", "5 מ\"מ", "8 מ\"מ", "10 מ\"מ", "12 מ\"מ"], 
            "length": 300, 
            "prices": {}
        },
        "זווית": {
            "dimensions": ["20x20", "25x25", "30x30", "40x40", "50x50"], 
            "thicknesses": ["3 מ\"מ", "4 מ\"מ", "5 מ\"מ"], 
            "length": 600, 
            "prices": {}
        },
        "מוט עגול מלא": {
            "dimensions": ["8 מ\"מ", "10 מ\"מ", "12 מ\"מ", "14 מ\"מ", "16 מ\"מ", "18 מ\"מ", "20 מ\"מ", "25 מ\"מ"], 
            "thicknesses": ["מלא"], 
            "length": 600, 
            "prices": {}
        },
        "מוט מרובע מלא": {
            "dimensions": ["10x10", "12x12", "14x14", "16x16", "20x20", "25x25"], 
            "thicknesses": ["מלא"], 
            "length": 600, 
            "prices": {}
        }
    }

def fetch_from_github(filename, default_factory):
    if not GITHUB_TOKEN: 
        return default_factory()
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content_str = base64.b64decode(res.json().get("content")).decode("utf-8")
            return json.loads(content_str)
    except: 
        pass
    return default_factory()

def save_to_github(filename, data_to_save, commit_message):
    if not GITHUB_TOKEN: 
        return False
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    content_b64 = base64.b64encode(json.dumps(data_to_save, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8")
    
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    payload = {"message": commit_message, "content": content_b64, "branch": "main"}
    if sha: 
        payload["sha"] = sha
        
    try: 
        return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except: 
        return False

# -----------------------------------------------------------------------------
# טעינת נתונים ראשונית מהענן לתוך ה-Session State
# -----------------------------------------------------------------------------
if 'dynamic_catalog' not in st.session_state:
    st.session_state.dynamic_catalog = fetch_from_github("saved_prices.json", get_initial_catalog)
if 'saved_projects' not in st.session_state:
    st.session_state.saved_projects = fetch_from_github("saved_projects.json", list)

# ניהול ניווט אקטיבי בין עמודים (בשביל לאפשר טעינה אוטומטית לעמוד המחשבון)
if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 חישוב פרויקט"

# משתני ברירת מחדל לשדות הלקוח בראש עמוד החישוב
if 'input_project_name' not in st.session_state: st.session_state.input_project_name = ""
if 'input_client_name' not in st.session_state: st.session_state.input_client_name = ""
if 'input_client_phone' not in st.session_state: st.session_state.input_client_phone = ""
if 'input_client_address' not in st.session_state: st.session_state.input_client_address = ""
if 'input_project_date' not in st.session_state: st.session_state.input_project_date = datetime.now().date()

# משתני ברירת מחדל עבור ה-Sidebar
if 'input_num_workers' not in st.session_state: st.session_state.input_num_workers = 1
if 'input_days_of_work' not in st.session_state: st.session_state.input_days_of_work = 1
if 'input_daily_wage' not in st.session_state: st.session_state.input_daily_wage = 0.0
if 'input_powder' not in st.session_state: st.session_state.input_powder = 0.0
if 'input_laser' not in st.session_state: st.session_state.input_laser = 0.0
if 'input_transport' not in st.session_state: st.session_state.input_transport = 0.0
if 'input_crane' not in st.session_state: st.session_state.input_crane = 0.0
if 'input_carpentry' not in st.session_state: st.session_state.input_carpentry = 0.0
if 'input_glazing' not in st.session_state: st.session_state.input_glazing = 0.0
if 'input_other' not in st.session_state: st.session_state.input_other = 0.0
if 'input_multiplier' not in st.session_state: st.session_state.input_multiplier = 1.5

if 'project_groups' not in st.session_state:
    first_type = list(st.session_state.dynamic_catalog.keys())[0]
    st.session_state.project_groups = [{
        'sel_type': first_type, 
        'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0], 
        'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0], 
        'cuts': [{'length': 100.0, 'qty': 1}]
    }]

# =============================================================================
# 3. אלגוריתם חיתוך משודרג ואופטימלי (Best-Fit Decreasing)
# =============================================================================
def calculate_optimal_cutting(cuts_list, max_capacity):
    all_pieces = []
    for cut in cuts_list:
        for _ in range(int(cut['qty'])):
            if cut['length'] > max_capacity: 
                return None, f"אורך {cut['length']} חורג מאורך מוט מקסימלי ({max_capacity} ס\"מ)."
            all_pieces.append(cut['length'])
            
    all_pieces.sort(reverse=True)
    bars = []
    
    for piece in all_pieces:
        best_bar_idx = -1
        min_leftover = max_capacity + 1
        
        for idx, bar in enumerate(bars):
            rem_space = max_capacity - sum(bar)
            if rem_space >= piece:
                leftover_after_placement = rem_space - piece
                if leftover_after_placement < min_leftover:
                    min_leftover = leftover_after_placement
                    best_bar_idx = idx
                    
        if best_bar_idx != -1:
            bars[best_bar_idx].append(piece)
        else:
            bars.append([piece])
            
    return bars, None

def display_visual_bars(bars_plan, max_bar_len):
    for b_id, bar_cuts in enumerate(bars_plan):
        used_space = sum(bar_cuts)
        leftover = max_bar_len - used_space
        st.markdown(f"**מוט #{b_id + 1} (פחת: {leftover:.1f} ס\"מ):**")
        
        bar_html = f"<div style='display: block; width: 100%; background-color: #e0e0e0; border-radius: 6px; margin: 6px 0; font-size:12px; font-weight:bold; color:white; overflow:hidden; border:1px solid #ccc;'>"
        for part in bar_cuts:
            percentage = (part / max_bar_len) * 100
            bar_html += f"<div style='display: inline-block; width: {percentage}%; background-color: #1976d2; text-align: center; padding: 6px 0; border-left: 2px solid #fff; float: right;'>{part}</div>"
        if leftover > 0:
            left_pct = (leftover / max_bar_len) * 100
            bar_html += f"<div style='display: inline-block; width: {left_pct}%; background-color: #d32f2f; text-align: center; padding: 6px 0; float: right;'>פחת: {leftover:.1f}</div>"
        bar_html += "<div style='clear: both;'></div></div>"
        
        st.markdown(bar_html, unsafe_allow_html=True)

def generate_html_bars_for_pdf(bars_plan, max_bar_len):
    html_str = ""
    for b_id, bar_cuts in enumerate(bars_plan):
        used_space = sum(bar_cuts)
        leftover = max_bar_len - used_space
        html_str += f"<p style='font-size: 11px; margin: 2px 0;'><b>מוט #{b_id + 1}:</b> {', '.join([str(p)+'cm' for p in bar_cuts])} | <b>פחת:</b> {leftover:.1f}cm</p>"
    return html_str

# פונקציה לייצור קובץ PDF בינארי אמיתי ישירות בזיכרון האפליקציה
def generate_pdf_file_bytes(p_name, c_name, phone, addr, p_date, mult, iron_cost, ext_list, total_net, final_price, materials_html):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: a4; margin: 1.5cm; }}
            body {{ font-family: Helvetica, Arial, sans-serif; direction: rtl; text-align: right; color: #333; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 8px; margin-bottom: 20px; }}
            .section {{ margin-bottom: 20px; }}
            .title {{ background-color: #f0f2f6; padding: 6px; font-size: 14px; font-weight: bold; border-right: 4px solid #1976d2; margin-bottom: 8px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 8px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; font-size: 12px; }}
            th {{ background-color: #f8f9fa; font-weight: bold; }}
            .price-box {{ font-size: 16px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 12px; text-align: center; border: 1px solid #a5d6a7; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Elad Cohen Iron Art ⚒️</h1>
            <h2>סיכום פרויקט והצעת מחיר סופית</h2>
            <p>תאריך הפקה: {datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
        <div class="section">
            <div class="title">👤 פרטי פרויקט ולקוח</div>
            <table>
                <tr><td><b>שם פרויקט / מוצר:</b></td><td>{p_name if p_name else '-'}</td></tr>
                <tr><td><b>שם הלקוח:</b></td><td>{c_name if c_name else '-'}</td></tr>
                <tr><td><b>טלפון:</b></td><td>{phone if phone else '-'}</td></tr>
                <tr><td><b>כתובת:</b></td><td>{addr if addr else '-'}</td></tr>
                <tr><td><b>תאריך פרויקט:</b></td><td>{str(p_date)}</td></tr>
            </table>
        </div>
        <div class="section">
            <div class="title">🧱 פירוט חומרי גלם ותוכניות חיתוך</div>
            {materials_html if materials_html else '<p style="font-size:12px;">לא הוזנו חומרי גלם לפרויקט זה או שהופק מהארכיון המהיר.</p>'}
        </div>
        <div class="section">
            <div class="title">📊 פירוט עלויות והוצאות נלוות</div>
            <table>
                <tr><th>סעיף הוצאה</th><th>עלות בש"ח (₪)</th></tr>
                <tr><td>סה"כ חומרי גלם (ברזל)</td><td>{iron_cost:,.2f} NIS</td></tr>
                <tr><td>עלות עבודה עצמית (עובדים)</td><td>{ext_list.get('labor', 0.0):,.2f} NIS</td></tr>
                <tr><td>צביעה בתנור</td><td>{ext_list.get('powder', 0.0):,.2f} NIS</td></tr>
                <tr><td>חיתוך לייזר</td><td>{ext_list.get('laser', 0.0):,.2f} NIS</td></tr>
                <tr><td>הובלה / שינוע</td><td>{ext_list.get('transport', 0.0):,.2f} NIS</td></tr>
                <tr><td>מנוף</td><td>{ext_list.get('crane', 0.0):,.2f} NIS</td></tr>
                <tr><td>עבודות נגרות משולבת</td><td>{ext_list.get('carpentry', 0.0):,.2f} NIS</td></tr>
                <tr><td>עבודות זגגות / זכוכית</td><td>{ext_list.get('glazing', 0.0):,.2f} NIS</td></tr>
                <tr><td>הוצאות שונות אחרות</td><td>{ext_list.get('other', 0.0):,.2f} NIS</td></tr>
                <tr style="font-weight: bold; background-color: #f8f9fa;"><td>סה"כ עלויות נטו (ייצור)</td><td>{total_net:,.2f} NIS</td></tr>
            </table>
        </div>
        <div class="price-box">
            💰 מחיר סופי מומלץ ללקוח (מכפיל רווח {mult}): {final_price:,.2f} ₪
        </div>
    </body>
    </html>
    """
    pdf_buffer = BytesIO()
    pisa.CreatePDF(BytesIO(html_content.encode("utf-8")), pdf_buffer, encoding='utf-8')
    return pdf_buffer.getvalue()

# =============================================================================
# 4. תפריט צדדי (Sidebar)
# =============================================================================
st.sidebar.title("🛠️ Elad Cohen Iron Art")
page_options = ["💰 מחירון ברזל", "📊 חישוב פרויקט", "📂 ארכיון פרויקטים"]
sidebar_page = st.sidebar.radio("ניווט בין עמודים:", page_options, index=page_options.index(st.session_state.current_page))
st.session_state.current_page = sidebar_page

st.sidebar.markdown("---")
st.sidebar.subheader("👷 עלויות עבודה עצמית")
num_workers = st.sidebar.number_input("כמות עובדים:", min_value=0, value=int(st.session_state.input_num_workers), step=1)
days_of_work = st.sidebar.number_input("ימי עבודה:", min_value=0, value=int(st.session_state.input_days_of_work), step=1)
daily_wage = st.sidebar.number_input("עלות יומית לעובד (₪):", min_value=0.0, value=float(st.session_state.input_daily_wage), step=50.0)
st.session_state.input_num_workers, st.session_state.input_days_of_work, st.session_state.input_daily_wage = num_workers, days_of_work, daily_wage
calculated_labor_cost = num_workers * days_of_work * daily_wage

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 הוצאות נלוות")
powder_coating_cost = st.sidebar.number_input("צביעה בתנור (₪):", min_value=0.0, value=float(st.session_state.input_powder), step=50.0)
laser_cutting_cost = st.sidebar.number_input("חיתוך לייזר (₪):", min_value=0.0, value=float(st.session_state.input_laser), step=50.0)
transportation_cost = st.sidebar.number_input("הובלה / שינוע (₪):", min_value=0.0, value=float(st.session_state.input_transport), step=50.0)
crane_cost = st.sidebar.number_input("מנוף (₪):", min_value=0.0, value=float(st.session_state.input_crane), step=50.0)
carpentry_cost = st.sidebar.number_input("עבודות נגרות משולבת (₪):", min_value=0.0, value=float(st.session_state.input_carpentry), step=50.0)
glazing_cost = st.sidebar.number_input("עבודות זגגות / זכוכית (₪):", min_value=0.0, value=float(st.session_state.input_glazing), step=50.0)
other_expenses = st.sidebar.number_input("הוצאות שונות אחרות (₪):", min_value=0.0, value=float(st.session_state.input_other), step=50.0)

st.session_state.input_powder, st.session_state.input_laser, st.session_state.input_transport, st.session_state.input_crane, st.session_state.input_carpentry, st.session_state.input_glazing, st.session_state.input_other = powder_coating_cost, laser_cutting_cost, transportation_cost, crane_cost, carpentry_cost, glazing_cost, other_expenses

st.sidebar.markdown("---")
profit_multiplier = st.sidebar.slider("מכפיל רווח גלובלי:", 1.0, 4.0, float(st.session_state.input_multiplier), 0.1)
st.session_state.input_multiplier = profit_multiplier
total_external_expenses = (calculated_labor_cost + powder_coating_cost + laser_cutting_cost + transportation_cost + crane_cost + carpentry_cost + glazing_cost + other_expenses)

# =============================================================================
# 5. עמוד 1: מחירון ברזל
# =============================================================================
if st.session_state.current_page == "💰 מחירון ברזל":
    st.title("📋 קטלוג ומחירון ברזל דינמי")
    cat_keys = list(st.session_state.dynamic_catalog.keys())
    tabs = st.tabs([f"🔳 {t}" for t in cat_keys])
    for idx, mat_type in enumerate(cat_keys):
        with tabs[idx]:
            info = st.session_state.dynamic_catalog[mat_type]
            data_matrix = []
            for d in info["dimensions"]:
                row_dict = {"מידות": d}
                for thk in info["thicknesses"]: row_dict[thk] = info.get("prices", {}).get(d, {}).get(thk, 0.0)
                data_matrix.append(row_dict)
            edited_df = st.data_editor(pd.DataFrame(data_matrix), key=f"ed_{mat_type}", use_container_width=True, hide_index=True)
            for _, row in edited_df.iterrows():
                dim = row["מידות"]
                if dim not in info["prices"]: info["prices"][dim] = {}
                for thk in info["thicknesses"]: info["prices"][dim][thk] = float(row[thk])
    if st.button("🔴 שמור מחירון מעודכן לענן", type="primary", use_container_width=True):
        if save_to_github("saved_prices.json", st.session_state.dynamic_catalog, "עדכון מחירון ברזל"): st.success("נשמר בהצלחה!")
        else: st.error("שגיאה בשמירה.")

# =============================================================================
# 6. עמוד 2: חישוב פרויקט
# =============================================================================
elif st.session_state.current_page == "📊 חישוב פרויקט":
    st.title("📊 מחשבון פרויקטים, חיתוך אופטימלי ועלויות")
    st.markdown("<div class='top-project-box'>", unsafe_allow_html=True)
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    save_project_name = row1_c1.text_input("שם הפרויקט / מוצר:", value=st.session_state.input_project_name)
    client_name = row1_c2.text_input("שם הלקוח:", value=st.session_state.input_client_name)
    client_phone = row1_c3.text_input("מספר טלפון:", value=st.session_state.input_client_phone)
    row2_c1, row2_c2 = st.columns([2, 1])
    client_address = row2_c1.text_input("כתובת הפרויקט (רחוב ועיר):", value=st.session_state.input_client_address)
    d_val = st.session_state.input_project_date
    if isinstance(d_val, str):
        try: d_val = datetime.strptime(d_val, "%Y-%m-%d").date()
        except: d_val = datetime.now().date()
    project_date = row2_c2.date_input("תאריך פרויקט:", value=d_val)
    st.session_state.input_project_name, st.session_state.input_client_name, st.session_state.input_client_phone, st.session_state.input_client_address, st.session_state.input_project_date = save_project_name, client_name, client_phone, client_address, project_date
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("➕ הוסף קבוצת חומר חדשה לפרויקט", use_container_width=True):
        first_type = list(st.session_state.dynamic_catalog.keys())[0]
        st.session_state.project_groups.append({'sel_type': first_type, 'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0], 'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0], 'cuts': [{'length': 100.0, 'qty': 1}]})
        st.rerun()

    total_project_iron_cost = 0.0
    pdf_materials_html = ""
    
    for g_idx, group in enumerate(st.session_state.project_groups):
        st.markdown(f"<div class='material-block'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        cat_keys = list(st.session_state.dynamic_catalog.keys())
        t_idx = cat_keys.index(group['sel_type']) if group['sel_type'] in cat_keys else 0
        group['sel_type'] = c1.selectbox("סוג החומר:", cat_keys, index=t_idx, key=f"t_{g_idx}")
        dims = st.session_state.dynamic_catalog[group['sel_type']]["dimensions"]
        group['sel_dim'] = c2.selectbox("מידת הפרופיל/מוט:", dims, index=dims.index(group['sel_dim']) if group['sel_dim'] in dims else 0, key=f"d_{g_idx}")
        thks = st.session_state.dynamic_catalog[group['sel_type']]["thicknesses"]
        group['sel_thk'] = c3.selectbox("עובי דופן / סוג:", thks, index=thks.index(group['sel_thk']) if group['sel_thk'] in thks else 0, key=f"th_{g_idx}")
        if c4.button("🗑️ מחק קבוצה", key=f"dg_{g_idx}"):
            st.session_state.project_groups.pop(g_idx)
            st.rerun()
        
        cuts_summary_text = ""
        for c_idx, cut in enumerate(group['cuts']):
            cc1, cc2, cc3 = st.columns([3, 3, 1])
            cut['length'] = cc1.number_input("אורך מבוקש (ס\"מ):", min_value=0.1, value=float(cut['length']), key=f"l_{g_idx}_{c_idx}")
            cut['qty'] = cc2.number_input("כמות יחידות:", min_value=1, value=int(cut['qty']), key=f"q_{g_idx}_{c_idx}")
            cuts_summary_text += f"{cut['qty']} יחידות x {cut['length']} ס\"מ | "
            if cc3.button("❌", key=f"dc_{g_idx}_{c_idx}"):
                group['cuts'].pop(c_idx)
                st.rerun()
        if st.button("➕ הוסף חיתוך נוסף לחומר זה", key=f"ac_{g_idx}"):
            group['cuts'].append({'length': 50.0, 'qty': 1})
            st.rerun()

        max_len = st.session_state.dynamic_catalog[group['sel_type']]['length']
        single_bar_price = st.session_state.dynamic_catalog[group['sel_type']]["prices"].get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
        bars_plan, err = calculate_optimal_cutting(group['cuts'], max_len)
        if err: st.error(err)
        else:
            g_bars_count = len(bars_plan)
            g_cost = g_bars_count * single_bar_price
            total_project_iron_cost += g_cost
            st.markdown(f"**💡 נדרשים {g_bars_count} מוטות. עלות ברזל: ₪ {g_cost:,.2f}**")
            display_visual_bars(bars_plan, max_len)
            
            # הכנת מקטע ה-HTML של החומר הנוכחי לתוך ה-PDF
            bars_pdf_text = generate_html_bars_for_pdf(bars_plan, max_len)
            pdf_materials_html += f"""
            <div style="margin-bottom: 10px; padding: 5px; border-bottom: 1px dashed #ccc;">
                <p style="font-size:12px; margin:0 0 4px 0;"><b>🛠️ {group['sel_type']} ({group['sel_dim']} | {group['sel_thk']})</b></p>
                <p style="font-size:11px; margin:0 0 4px 0; color:#555;">מידות שהוזנו: {cuts_summary_text}</p>
                <p style="font-size:11px; margin:0 0 2px 0;"><b>תוכנית חיתוך (נדרש {g_bars_count} מוטות):</b></p>
                {bars_pdf_text}
            </div>
            """
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    total_expenses = total_project_iron_cost + total_external_expenses
    client_final_price = total_expenses * profit_multiplier
    
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("סה\"כ עלות ברזל", f"₪ {total_project_iron_cost:,.2f}")
    cc2.metric("הוצאות נלוות", f"₪ {total_external_expenses:,.2f}")
    cc3.metric("עלויות נטו לפרויקט", f"₪ {total_expenses:,.2f}")
    st.markdown(f"## 💰 הצעת מחיר מומלצת ללקוח: ₪ {client_final_price:,.2f}")

    # יצירת קובץ ה-PDF הבינארי האמיתי להורדה עם רשימת החומרים
    ext_pdf_dict = {'labor': calculated_labor_cost, 'powder': powder_coating_cost, 'laser': laser_cutting_cost, 'transport': transportation_cost, 'crane': crane_cost, 'carpentry': carpentry_cost, 'glazing': glazing_cost, 'other': other_expenses}
    pdf_bytes = generate_pdf_file_bytes(save_project_name, client_name, client_phone, client_address, project_date, profit_multiplier, total_project_iron_cost, ext_pdf_dict, total_expenses, client_final_price, pdf_materials_html)

    st.markdown("---")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        clean_name = re.sub(r'[\/*?:"<>|]', "", save_project_name) if save_project_name else "project"
        st.download_button(
            label="📄 הורד סיכום פרויקט כקובץ PDF אמיתי",
            data=pdf_bytes,
            file_name=f"Project_Summary_{clean_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with c_btn2:
        if st.button("💾 שמור פרויקט לארכיון הענן", type="primary", use_container_width=True):
            if not save_project_name: st.error("אנא מלא שם פרויקט.")
            else:
                entry = {'project_name': save_project_name, 'client_name': client_name, 'phone': client_phone, 'address': client_address, 'date': str(project_date), 'multiplier': profit_multiplier, 'labor_data': {'num_workers': num_workers, 'days_of_work': days_of_work, 'daily_wage': daily_wage}, 'external_expenses': {'powder': powder_coating_cost, 'laser': laser_cutting_cost, 'transport': transportation_cost, 'crane': crane_cost, 'carpentry': carpentry_cost, 'glazing': glazing_cost, 'other': other_expenses}, 'groups_data': st.session_state.project_groups}
                idx_exist = next((i for i, p in enumerate(st.session_state.saved_projects) if p.get('project_name') == save_project_name), -1)
                if idx_exist != -1: st.session_state.saved_projects[idx_exist] = entry
                else: st.session_state.saved_projects.append(entry)
                if save_to_github("saved_projects.json", st.session_state.saved_projects, f"שמירת פרויקט: {save_project_name}"): st.success("נשמר בארכיון!")

# =============================================================================
# 7. עמוד 3: ארכיון פרויקטים
# =============================================================================
else:
    st.title("📂 ארכיון פרויקטים שמורים")
    if not st.session_state.saved_projects: st.info("אין פרויקטים שמורים.")
    else:
        for p_idx, project in enumerate(list(st.session_state.saved_projects)):
            p_title, c_name, p_date = project.get('project_name', 'ללא שם'), project.get('client_name', '-'), project.get('date', '-')
            with st.expander(f"📁 פרויקט: {p_title} | לקוח: {c_name} | תאריך: {p_date}"):
                c_actions1, c_actions2, c_actions3 = st.columns(3)
                
                if c_actions1.button("🔄 טען פרויקט זה לעמוד החישוב (עריכה)", key=f"load_{p_idx}", use_container_width=True):
                    st.session_state.input_project_name, st.session_state.input_client_name, st.session_state.input_client_phone, st.session_state.input_client_address, st.session_state.input_project_date = project.get('project_name', ''), project.get('client_name', ''), project.get('phone', ''), project.get('address', ''), project.get('date', str(datetime.now().date()))
                    lab = project.get('labor_data', {})
                    st.session_state.input_num_workers, st.session_state.input_days_of_work, st.session_state.input_daily_wage = lab.get('num_workers', 1), lab.get('days_of_work', 1), lab.get('daily_wage', 0.0)
                    ext = project.get('external_expenses', {})
                    st.session_state.input_powder, st.session_state.input_laser, st.session_state.input_transport, st.session_state.input_crane, st.session_state.input_carpentry, st.session_state.input_glazing, st.session_state.input_other = ext.get('powder', 0.0), ext.get('laser', 0.0), ext.get('transport', 0.0), ext.get('crane', 0.0), ext.get('carpentry', 0.0), ext.get('glazing', 0.0), ext.get('other', 0.0)
                    st.session_state.input_multiplier, st.session_state.project_groups = project.get('multiplier', 1.5), project.get('groups_data', [])
                    st.session_state.current_page = "📊 חישוב פרויקט"
                    st.rerun()

                st.markdown(f"<div class='customer-info-box'>👤 <b>לקוח:</b> {project.get('client_name','-')} | 📞 <b>טלפון:</b> {project.get('phone','-')} <br>📍 <b>כתובת:</b> {project.get('address','-')}</div>", unsafe_allow_html=True)
                
                archived_iron_cost = 0.0
                pdf_archive_materials_html = ""
                
                for group in project.get('groups_data', []):
                    st.markdown(f"🔹 **חומר:** {group['sel_type']} ({group['sel_dim']} | {group['sel_thk']})")
                    max_len = st.session_state.dynamic_catalog[group['sel_type']]['length']
                    s_price = st.session_state.dynamic_catalog[group['sel_type']]["prices"].get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
                    bars_plan, err = calculate_optimal_cutting(group['cuts'], max_len)
                    if not err:
                        g_bars_cnt = len(bars_plan)
                        archived_iron_cost += g_bars_cnt * s_price
                        display_visual_bars(bars_plan, max_len)
                        
                        # בניית מקטע החומרים לפרויקט מהארכיון
                        arch_cuts_summary = "".join([f"{c['qty']} יחידות x {c['length']} ס\"מ | " for c in group['cuts']])
                        arch_bars_pdf_text = generate_html_bars_for_pdf(bars_plan, max_len)
                        pdf_archive_materials_html += f"""
                        <div style="margin-bottom: 10px; padding: 5px; border-bottom: 1px dashed #ccc;">
                            <p style="font-size:12px; margin:0 0 4px 0;"><b>🛠️ {group['sel_type']} ({group['sel_dim']} | {group['sel_thk']})</b></p>
                            <p style="font-size:11px; margin:0 0 4px 0; color:#555;">מידות: {arch_cuts_summary}</p>
                            <p style="font-size:11px; margin:0 0 2px 0;"><b>תוכנית חיתוך (נדרש {g_bars_cnt} מוטות):</b></p>
                            {arch_bars_pdf_text}
                        </div>
                        """
                
                ext, lab = project.get('external_expenses', {}), project.get('labor_data', {})
                lab_total = lab.get('num_workers', 0) * lab.get('days_of_work', 0) * lab.get('daily_wage', 0)
                ext_total = sum(ext.values()) if isinstance(ext, dict) else 0.0
                ext_total += lab_total
                total_archived_expenses = archived_iron_cost + ext_total
                final_quote_archived = total_archived_expenses * project.get('multiplier', 1.5)
                
                st.markdown("---")
                c1, c2, c3 = st.columns(3)
                c1.metric("עלות ברזל", f"₪ {archived_iron_cost:,.2f}")
                c2.metric("הוצאות ועבודה", f"₪ {ext_total:,.2f}")
                c3.metric("מחיר סופי ללקוח", f"₪ {final_quote_archived:,.2f}")
                
                # בניית קובץ ה-PDF עבור הפרויקט בארכיון עם רשימת החומרים המלאה
                arch_ext_dict = {'labor': lab_total, 'powder': ext.get('powder', 0.0), 'laser': ext.get('laser', 0.0), 'transport': ext.get('transport', 0.0), 'crane': ext.get('crane', 0.0), 'carpentry': ext.get('carpentry', 0.0), 'glazing': ext.get('glazing', 0.0), 'other': ext.get('other', 0.0)}
                arch_pdf_bytes = generate_pdf_file_bytes(p_title, project.get('client_name','-'), project.get('phone','-'), project.get('address','-'), project.get('date','-'), project.get('multiplier', 1.5), archived_iron_cost, arch_ext_dict, total_archived_expenses, final_quote_archived, pdf_archive_materials_html)
                
                clean_arch_title = re.sub(r'[\/*?:"<>|]', "", p_title)
                c_actions2.download_button(
                    label="📄 הורד קובץ PDF מהארכיון",
                    data=arch_pdf_bytes,
                    file_name=f"Archive_Project_{clean_arch_title}.pdf",
                    mime="application/pdf",
                    key=f"pdf_arch_{p_idx}",
                    use_container_width=True
                )
                
                if c_actions3.button("❌ מחק פרויקט לצמיתות", key=f"del_{p_idx}", use_container_width=True):
                    st.session_state.saved_projects.pop(p_idx)
                    if save_to_github("saved_projects.json", st.session_state.saved_projects, f"מחיקת פרויקט {p_title}"):
                        st.success("נמחק!")
                        st.rerun()
