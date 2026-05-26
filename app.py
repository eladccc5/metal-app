import streamlit as st
import pandas as pd
import json
import requests
import base64
import re
from datetime import datetime

# =============================================================================
# 1. הגדרות עיצוב ומערכת (RTL ומראה נקי)
# =============================================================================
st.set_page_config(
    page_title="מערכת תמחור וחיתוך - Elad Cohen Iron Art", 
    layout="wide"
)

# החלת עיצוב CSS מותאם אישית לתמיכה מלאה בעברית (RTL) ואסתטיקה של האפליקציה + כפיית מצב בהיר
st.markdown("""
    <style>
    /* כפיית מצב בהיר (Light Mode) כפי שביקשת, ללא שינוי במבנה */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
        background-color: #f8f9fa !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div.stMarkdown, [data-testid="stWidgetLabel"] p {
        color: #111111 !important;
    }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, input, select, textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #cccccc !important;
    }
    span[data-baseweb="select"], div[role="listbox"], option, ul[role="listbox"] {
        color: #111111 !important;
        background-color: #ffffff !important;
    }

    /* הגדרות ה-CSS המקוריות שלך - ללא שינוי */
    body, .main, div.stMarkdown, div[data-testid="stWidgetLabel"] {
        direction: rtl !important;
        text-align: right !important;
    }
    div[data-testid="stDataEditor"] {
        direction: rtl !important;
        background-color: #ffffff !important;
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
    .bar-display {
        background-color: #f8f9fa;
        border-right: 5px solid #2e7d32;
        padding: 8px 12px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .admin-box {
        background-color: #fff9db;
        border: 1px solid #fab005;
        padding: 15px;
        border-radius: 8px;
        margin-top: 25px;
    }
    .expense-box {
        background-color: #f1f3f5;
        border-right: 5px solid #495057;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 10px;
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
        'cuts': [{'length': 100.0, 'qty': 1, 'angle': 'ישר / ישר (90°)'}]
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
            # נשמור גם את הזווית לשימוש עתידי או תצוגה באלגוריתם
            all_pieces.append({'length': cut['length'], 'angle': cut.get('angle', 'ישר / ישר (90°)')})
            
    all_pieces.sort(key=lambda x: x['length'], reverse=True)
    bars = []
    
    for piece in all_pieces:
        best_bar_idx = -1
        min_leftover = max_capacity + 1
        
        for idx, bar in enumerate(bars):
            rem_space = max_capacity - sum(p['length'] for p in bar)
            if rem_space >= piece['length']:
                leftover_after_placement = rem_space - piece['length']
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
        used_space = sum(p['length'] for p in bar_cuts)
        leftover = max_bar_len - used_space
        st.markdown(f"**מוט #{b_id + 1} (פחת: {leftover:.1f} ס\"מ):**")
        
        bar_html = f"<div style='display: block; width: 100%; background-color: #e0e0e0; border-radius: 6px; margin: 6px 0; font-size:12px; font-weight:bold; color:white; overflow:hidden; border:1px solid #ccc;'>"
        for part in bar_cuts:
            percentage = (part['length'] / max_bar_len) * 100
            lbl = f"{part['length']} [{part['angle']}]"
            bar_html += f"<div style='display: inline-block; width: {percentage}%; background-color: #1976d2; text-align: center; padding: 6px 0; border-left: 2px solid #fff; float: right; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;' title='{lbl}'>{lbl}</div>"
        if leftover > 0:
            left_pct = (leftover / max_bar_len) * 100
            bar_html += f"<div style='display: inline-block; width: {left_pct}%; background-color: #d32f2f; text-align: center; padding: 6px 0; float: right; overflow: hidden; white-space: nowrap;'>פחת: {leftover:.1f}</div>"
        bar_html += "<div style='clear: both;'></div></div>"
        
        st.markdown(bar_html, unsafe_allow_html=True)

def generate_html_bars_for_pdf(bars_plan, max_bar_len):
    html_str = ""
    for b_id, bar_cuts in enumerate(bars_plan):
        used_space = sum(p['length'] for p in bar_cuts)
        leftover = max_bar_len - used_space
        html_str += f"<div style='margin-top: 10px; font-weight: bold;'>מוט #{b_id + 1} (פחת: {leftover:.1f} ס\"מ):</div>"
        html_str += "<div style='width: 100%; background-color: #e0e0e0; border: 1px solid #ccc; height: 30px; border-radius: 4px; overflow: hidden; white-space: nowrap; margin-bottom: 10px;'>"
        for part in bar_cuts:
            pct = (part['length'] / max_bar_len) * 100
            lbl = f"{part['length']} [{part['angle']}]"
            html_str += f"<div style='display: inline-block; width: {pct}%; background-color: #1976d2; color: white; text-align: center; line-height: 30px; font-size: 11px; border-left: 1px solid white; box-sizing: border-box; overflow: hidden; text-overflow: ellipsis;'>{lbl}</div>"
        if leftover > 0:
            left_pct = (leftover / max_bar_len) * 100
            html_str += f"<div style='display: inline-block; width: {left_pct}%; background-color: #d32f2f; color: white; text-align: center; line-height: 30px; font-size: 11px; box-sizing: border-box; overflow: hidden;'>פחת: {leftover:.1f}</div>"
        html_str += "</div>"
    return html_str

# פונקציה גלובלית שמייצרת את קוד ה-HTML של ה-PDF (משותפת למחשבון ולארכיון)
def build_pdf_html_content(p_name, c_name, phone, addr, p_date, mult, iron_cost, ext_list, total_net, final_price, materials_html):
    return f"""
    <html dir="rtl">
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; line-height: 1.5; color: #333; direction: rtl; text-align: right; background-color: #ffffff; }}
            .header {{ text-align: center; border-bottom: 3px solid #333; padding-bottom: 10px; margin-bottom: 30px; }}
            .section {{ margin-bottom: 25px; }}
            .section-title {{ background-color: #f0f2f6; padding: 8px; font-size: 16px; border-right: 5px solid #1976d2; font-weight: bold; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
            th {{ background-color: #f8f9fa; font-weight: bold; }}
            .price-box {{ font-size: 20px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 15px; text-align: center; border: 1px solid #a5d6a7; margin-top: 20px; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="margin: 0;">Elad Cohen Iron Art ⚒️</h1>
            <h2 style="margin: 5px 0; font-weight: normal; font-size: 18px;">סיכום פרויקט והצעת מחיר סופית</h2>
            <p style="font-size: 12px; color: #666;">תאריך הפקה: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        <div class="section">
            <div class="section-title">👤 פרטי פרויקט ולקוח</div>
            <table>
                <tr><td><b>שם פרויקט / מוצר:</b></td><td>{p_name if p_name else '-'}</td></tr>
                <tr><td><b>שם הלקוח:</b></td><td>{c_name if c_name else '-'}</td></tr>
                <tr><td><b>טלפון:</b></td><td>{phone if phone else '-'}</td></tr>
                <tr><td><b>כתובת אספקה/התקנה:</b></td><td>{addr if addr else '-'}</td></tr>
                <tr><td><b>תאריך פרויקט:</b></td><td>{str(p_date)}</td></tr>
            </table>
        </div>
        <div class="section">
            <div class="section-title">🧱 פירוט חומרים ותוכניות חיתוך אופטימליות</div>
            {materials_html if materials_html else '<p>לא הוזנו חומרים לפרויקט.</p>'}
        </div>
        <div class="section">
            <div class="section-title">📊 סיכום עלויות והוצאות נלוות</div>
            <table>
                <thead>
                    <tr><th>סעיף הוצאה</th><th>עלות בש"ח (₪)</th></tr>
                </thead>
                <tbody>
                    <tr><td>סה"כ חומרי גלם (ברזל)</td><td>₪ {iron_cost:,.2f}</td></tr>
                    <tr><td>עלות עבודה עצמית (עובדים וימי עבודה)</td><td>₪ {ext_list.get('labor', 0.0):,.2f}</td></tr>
                    <tr><td>צביעה בתנור</td><td>₪ {ext_list.get('powder', 0.0):,.2f}</td></tr>
                    <tr><td>חיתוך לייזר</td><td>₪ {ext_list.get('laser', 0.0):,.2f}</td></tr>
                    <tr><td>הובלה / שינוע</td><td>₪ {ext_list.get('transport', 0.0):,.2f}</td></tr>
                    <tr><td>מנוף</td><td>₪ {ext_list.get('crane', 0.0):,.2f}</td></tr>
                    <tr><td>עבודות נגרות משולבת</td><td>₪ {ext_list.get('carpentry', 0.0):,.2f}</td></tr>
                    <tr><td>עבודות זגגות / זכוכית</td><td>₪ {ext_list.get('glazing', 0.0):,.2f}</td></tr>
                    <tr><td>הוצאות שונות אחרות</td><td>₪ {ext_list.get('other', 0.0):,.2f}</td></tr>
                    <tr style="font-weight: bold; background-color: #f8f9fa;"><td>סה"כ עלויות נטו (עלות ייצור)</td><td>₪ {total_net:,.2f}</td></tr>
                </tbody>
            </table>
        </div>
        <div class="price-box">
            💰 הצעת מחיר מומלצת וסופית ללקוח (מכפיל רווח {mult}): ₪ {final_price:,.2f}
        </div>
        <script>window.onload = function() {{ window.print(); }}</script>
    </body>
    </html>
    """

# =============================================================================
# 4. תפריט צדדי (Sidebar) - סנכרון עם ה-Session State
# =============================================================================
st.sidebar.title("🛠️ Elad Cohen Iron Art")

# שימוש בניווט מנוהל Session State
page_options = ["💰 מחירון ברזל", "📊 חישוב פרויקט", "📂 ארכיון פרויקטים"]
sidebar_page = st.sidebar.radio(
    "ניווט בין עמודים:", 
    page_options, 
    index=page_options.index(st.session_state.current_page),
    key="sidebar_navigation"
)
st.session_state.current_page = sidebar_page

st.sidebar.markdown("---")
st.sidebar.subheader("👷 עלויות עבודה עצמית")
num_workers = st.sidebar.number_input("כמות עובדים:", min_value=0, value=int(st.session_state.input_num_workers), step=1, key="num_workers_widget")
days_of_work = st.sidebar.number_input("ימי עבודה:", min_value=0, value=int(st.session_state.input_days_of_work), step=1, key="days_of_work_widget")
daily_wage = st.sidebar.number_input("עלות יומית לעובד (₪):", min_value=0.0, value=float(st.session_state.input_daily_wage), step=50.0, key="daily_wage_widget")

st.session_state.input_num_workers = num_workers
st.session_state.input_days_of_work = days_of_work
st.session_state.input_daily_wage = daily_wage
calculated_labor_cost = num_workers * days_of_work * daily_wage

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 הוצאות נלוות וקבלני משנה")
powder_coating_cost = st.sidebar.number_input("צביעה בתנור (₪):", min_value=0.0, value=float(st.session_state.input_powder), step=50.0, key="powder_widget")
laser_cutting_cost = st.sidebar.number_input("חיתוך לייזר (₪):", min_value=0.0, value=float(st.session_state.input_laser), step=50.0, key="laser_widget")
transportation_cost = st.sidebar.number_input("הובלה / שינוע (₪):", min_value=0.0, value=float(st.session_state.input_transport), step=50.0, key="transport_widget")
crane_cost = st.sidebar.number_input("מנוף (₪):", min_value=0.0, value=float(st.session_state.input_crane), step=50.0, key="crane_widget")
carpentry_cost = st.sidebar.number_input("עבודות נגרות משולבת (₪):", min_value=0.0, value=float(st.session_state.input_carpentry), step=50.0, key="carpentry_widget")
glazing_cost = st.sidebar.number_input("עבודות זגגות / זכוכית (₪):", min_value=0.0, value=float(st.session_state.input_glazing), step=50.0, key="glazing_widget")
other_expenses = st.sidebar.number_input("הוצאות שונות אחרות (₪):", min_value=0.0, value=float(st.session_state.input_other), step=50.0, key="other_widget")

st.session_state.input_powder = powder_coating_cost
st.session_state.input_laser = laser_cutting_cost
st.session_state.input_transport = transportation_cost
st.session_state.input_crane = crane_cost
st.session_state.input_carpentry = carpentry_cost
st.session_state.input_glazing = glazing_cost
st.session_state.input_other = other_expenses

st.sidebar.markdown("---")
profit_multiplier = st.sidebar.slider("מכפיל רווח גלובלי:", 1.0, 4.0, float(st.session_state.input_multiplier), 0.1, key="multiplier_widget")
st.session_state.input_multiplier = profit_multiplier

total_external_expenses = (calculated_labor_cost + powder_coating_cost + laser_cutting_cost + 
                           transportation_cost + crane_cost + carpentry_cost + glazing_cost + other_expenses)

# =============================================================================
# 5. עמוד 1: מחירון ברזל (ניהול ועדכון קטלוג)
# =============================================================================
if st.session_state.current_page == "💰 מחירון ברזל":
    st.title("📋 קטלוג ומחירון ברזל דינמי")
    st.write("עדכן את מחירי המוטות בטבלאות שלהלן, ולאחר מכן לחץ על כפתור השמירה לענן.")
    
    cat_keys = list(st.session_state.dynamic_catalog.keys())
    tabs = st.tabs([f"🔳 {t}" for t in cat_keys])
    
    for idx, mat_type in enumerate(cat_keys):
        with tabs[idx]:
            info = st.session_state.dynamic_catalog[mat_type]
            data_matrix = []
            
            for d in info["dimensions"]:
                row_dict = {"מידות": d}
                for thk in info["thicknesses"]: 
                    row_dict[thk] = info.get("prices", {}).get(d, {}).get(thk, 0.0)
                data_matrix.append(row_dict)
                
            edited_df = st.data_editor(pd.DataFrame(data_matrix), key=f"ed_{mat_type}", use_container_width=True, hide_index=True)
            
            for _, row in edited_df.iterrows():
                dim = row["מידות"]
                if dim not in info["prices"]: 
                    info["prices"][dim] = {}
                for thk in info["thicknesses"]: 
                    info["prices"][dim][thk] = float(row[thk])
                    
    st.markdown("---")
    if st.button("🔴 שמור מחירון מעודכן לענן", type="primary", use_container_width=True):
        if save_to_github("saved_prices.json", st.session_state.dynamic_catalog, "עדכון מחירון ברזל"): 
            st.success("המחירון החדש נשמר בהצלחה ב-GitHub ומעודכן במערכת!")
        else:
            st.error("שגיאה בשמירה לענן. ודא שהטוקן תקין.")

# =============================================================================
# 6. עמוד 2: חישוב פרויקט (מחשבון חיתוך, תמחור סופי וייצוא PDF)
# =============================================================================
elif st.session_state.current_page == "📊 חישוב פרויקט":
    st.title("📊 מחשבון פרויקטים, חיתוך אופטימלי ועלויות")
    
    st.markdown("<div class='top-project-box'>", unsafe_allow_html=True)
    st.subheader("👤 פרטי הפרויקט והלקוח הנוכחי")
    
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    save_project_name = row1_c1.text_input("שם הפרויקט / מוצר (למשל: סורג ליוסי):", value=st.session_state.input_project_name)
    client_name = row1_c2.text_input("שם הלקוח:", value=st.session_state.input_client_name)
    client_phone = row1_c3.text_input("מספר טלפון:", value=st.session_state.input_client_phone)
    
    row2_c1, row2_c2 = st.columns([2, 1])
    client_address = row2_c1.text_input("כתובת הפרויקט (רחוב ועיר):", value=st.session_state.input_client_address)
    
    # בדיקת סוג התאריך (לוודא שהוא אובייקט תאריך תקין)
    d_val = st.session_state.input_project_date
    if isinstance(d_val, str):
        try: d_val = datetime.strptime(d_val, "%Y-%m-%d").date()
        except: d_val = datetime.now().date()
    project_date = row2_c2.date_input("תאריך פרויקט:", value=d_val)
    
    st.session_state.input_project_name = save_project_name
    st.session_state.input_client_name = client_name
    st.session_state.input_client_phone = client_phone
    st.session_state.input_client_address = client_address
    st.session_state.input_project_date = project_date
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("➕ הוסף קבוצת חומר חדשה לפרויקט", use_container_width=True):
        first_type = list(st.session_state.dynamic_catalog.keys())[0]
        st.session_state.project_groups.append({
            'sel_type': first_type, 
            'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0], 
            'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0], 
            'cuts': [{'length': 100.0, 'qty': 1, 'angle': 'ישר / ישר (90°)'}]
        })
        st.rerun()

    total_project_iron_cost = 0.0
    pdf_materials_html = ""
    
    for g_idx, group in enumerate(st.session_state.project_groups):
        st.markdown(f"<div class='material-block'>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        
        # מניעת קריסה אם חומרים ישנים נטענו ולא תואמים לקטלוג הנוכחי
        cat_keys = list(st.session_state.dynamic_catalog.keys())
        t_idx = cat_keys.index(group['sel_type']) if group['sel_type'] in cat_keys else 0
        g_type = c1.selectbox("סוג החומר:", cat_keys, index=t_idx, key=f"t_{g_idx}")
        group['sel_type'] = g_type
        
        dims = st.session_state.dynamic_catalog[g_type]["dimensions"]
        d_idx = dims.index(group['sel_dim']) if group['sel_dim'] in dims else 0
        g_dim = c2.selectbox("מידת הפרופיל/מוט:", dims, index=d_idx, key=f"d_{g_idx}")
        group['sel_dim'] = g_dim
        
        thks = st.session_state.dynamic_catalog[g_type]["thicknesses"]
        th_idx = thks.index(group['sel_thk']) if group['sel_thk'] in thks else 0
        g_thk = c3.selectbox("עובי דופן / סוג:", thks, index=th_idx, key=f"th_{g_idx}")
        group['sel_thk'] = g_thk
        
        if c4.button("🗑️ מחק קבוצה", key=f"dg_{g_idx}"): 
            st.session_state.project_groups.pop(g_idx)
            st.rerun()
        
        st.markdown("##### רשימת חיתוכים נדרשים:")
        cuts_summary_text = ""
        for c_idx, cut in enumerate(group['cuts']):
            cc1, cc2, cc3, cc4 = st.columns([2.5, 2.5, 3, 1])
            cut['length'] = cc1.number_input("אורך מבוקש (ס\"מ):", min_value=0.1, value=float(cut['length']), key=f"l_{g_idx}_{c_idx}")
            cut['qty'] = cc2.number_input("כמות יחידות:", min_value=1, value=int(cut['qty']), key=f"q_{g_idx}_{c_idx}")
            
            # תוספת שדה הזווית לחיתוכים
            angle_opts = ["ישר / ישר (90°)", "ישר / 45°", "45° / 45°"]
            curr_angle = cut.get('angle', angle_opts[0])
            cut['angle'] = cc3.selectbox("סוג קצוות (זווית):", angle_opts, index=angle_opts.index(curr_angle) if curr_angle in angle_opts else 0, key=f"ang_{g_idx}_{c_idx}")
            
            cuts_summary_text += f"<li>{cut['qty']} יחידות x {cut['length']} ס\"מ (חיתוך: {cut['angle']})</li>"
            
            if cc4.button("❌", key=f"dc_{g_idx}_{c_idx}"): 
                group['cuts'].pop(c_idx)
                st.rerun()
                
        if st.button("➕ הוסף חיתוך נוסף לחומר זה", key=f"ac_{g_idx}"): 
            group['cuts'].append({'length': 50.0, 'qty': 1, 'angle': 'ישר / ישר (90°)'})
            st.rerun()

        max_len = st.session_state.dynamic_catalog[group['sel_type']]['length']
        single_bar_price = st.session_state.dynamic_catalog[group['sel_type']]["prices"].get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
        
        bars_plan, err = calculate_optimal_cutting(group['cuts'], max_len)
        if err:
            st.error(err)
        else:
            group_bars_count = len(bars_plan)
            group_cost = group_bars_count * single_bar_price
            total_project_iron_cost += group_cost
            
            st.markdown(f"**💡 נדרשים {group_bars_count} מוטות באורך {max_len} ס\"מ לקבוצה זו. עלות ברזל: ₪ {group_cost:,.2f}**")
            display_visual_bars(bars_plan, max_len)
            
            bars_html_for_pdf = generate_html_bars_for_pdf(bars_plan, max_len)
            pdf_materials_html += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; background-color: #fafafa; border-radius: 6px;">
                <h3 style="margin-top:0; color:#1976d2;">🛠️ חומר: {group['sel_type']} ({group['sel_dim']} | {group['sel_thk']})</h3>
                <p><b>חיתוכים שהוזנו:</b></p>
                <ul>{cuts_summary_text}</ul>
                <p><b>תוכנית אופטימיזציית חיתוך (סה"כ נדרש: {group_bars_count} מוטות של {max_len} ס"מ):</b></p>
                {bars_html_for_pdf}
            </div>
            """
            
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    total_expenses = total_project_iron_cost + total_external_expenses
    client_final_price = total_expenses * profit_multiplier
    
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("סה\"כ עלות ברזל נדרש", f"₪ {total_project_iron_cost:,.2f}")
    cc2.metric("סה\"כ הוצאות ועבודה נלווים", f"₪ {total_external_expenses:,.2f}")
    cc3.metric("סה\"כ עלויות נטו לפרויקט", f"₪ {total_expenses:,.2f}")
    
    st.markdown(f"## 💰 הצעת מחיר מומלצת ללקוח (כולל רווח): ₪ {client_final_price:,.2f}")

    # הכנת רשימת ההוצאות לקובץ ה-PDF
    ext_expenses_dict_for_pdf = {
        'labor': calculated_labor_cost, 'powder': powder_coating_cost, 'laser': laser_cutting_cost,
        'transport': transportation_cost, 'crane': crane_cost, 'carpentry': carpentry_cost,
        'glazing': glazing_cost, 'other': other_expenses
    }
    html_pdf_template = build_pdf_html_content(
        save_project_name, client_name, client_phone, client_address, project_date,
        profit_multiplier, total_project_iron_cost, ext_expenses_dict_for_pdf,
        total_expenses, client_final_price, pdf_materials_html
    )

    st.markdown("---")
    st.subheader("📥 ייצוא ושמירה")
    c_btn1, c_btn2 = st.columns(2)
    
    with c_btn1:
        clean_project_filename = re.sub(r'[\/*?:"<>|]', "", save_project_name) if save_project_name else "project_summary"
        st.download_button(
            label="📄 ייצא והורד סיכום פרויקט וחיתוכים ל-PDF",
            data=html_pdf_template,
            file_name=f"סיכום_פרויקט_{clean_project_filename}.html",
            mime="text/html",
            use_container_width=True,
            help="לחיצה תוריד קובץ. פתח אותו ולחץ במקלדת Ctrl+P כדי לשמור כ-PDF נקי."
        )
        
    with c_btn2:
        if st.button("💾 שמור פרויקט זה לארכיון הענן", type="primary", use_container_width=True):
            if not save_project_name:
                st.error("אנא מלא את שדה 'שם הפרויקט / מוצר' בראש העמוד כדי שתוכל לזהות אותו בארכיון.")
            else:
                new_project_entry = {
                    'project_name': save_project_name,
                    'client_name': client_name,
                    'phone': client_phone,
                    'address': client_address,
                    'date': str(project_date),
                    'multiplier': profit_multiplier,
                    'labor_data': {
                        'num_workers': num_workers,
                        'days_of_work': days_of_work,
                        'daily_wage': daily_wage
                    },
                    'external_expenses': {
                        'powder': powder_coating_cost,
                        'laser': laser_cutting_cost,
                        'transport': transportation_cost,
                        'crane': crane_cost,
                        'carpentry': carpentry_cost,
                        'glazing': glazing_cost,
                        'other': other_expenses
                    },
                    'groups_data': st.session_state.project_groups
                }
                
                # בדיקה אם פרויקט בשם זה כבר קיים בארכיון - אם כן נעדכן אותו במקום להכפיל
                existing_idx = -1
                for idx, p in enumerate(st.session_state.saved_projects):
                    if p.get('project_name') == save_project_name:
                        existing_idx = idx
                        break
                
                if existing_idx != -1:
                    st.session_state.saved_projects[existing_idx] = new_project_entry
                    msg = f"הפרויקט הקיים '{save_project_name}' עודכן בהצלחה בענן!"
                else:
                    st.session_state.saved_projects.append(new_project_entry)
                    msg = f"הפרויקט החדש '{save_project_name}' נשמר בהצלחה בארכיון הענן!"
                
                if save_to_github("saved_projects.json", st.session_state.saved_projects, f"שמירה/עדכון פרויקט: {save_project_name}"):
                    st.success(msg)
                else:
                    st.error("תקלה בעדכון קובץ הארכיון מול השרת.")

# =============================================================================
# 7. עמוד 3: ארכיון פרויקטים (טעינה לעריכה + הפקת PDF ישירה)
# =============================================================================
else:
    st.title("📂 ארכיון פרויקטים שמורים")
    st.write("כאן מופיעים כל הפרויקטים ששמרת בענן. באפשרותך להפיק PDF ישירות, או לטעון את הפרויקט חזרה למחשבון לצורך שינויים ועריכה.")
    
    if not st.session_state.saved_projects:
        st.info("אין פרויקטים שמורים כרגע בארכיון.")
    else:
        for p_idx, project in enumerate(list(st.session_state.saved_projects)):
            p_title = project.get('project_name', 'פרויקט ללא שם')
            c_name = project.get('client_name', '-')
            p_date = project.get('date', '-')
            
            with st.expander(f"📁 פרויקט: {p_title} | לקוח: {c_name} | תאריך: {p_date}"):
                
                # כפתורי פעולה מהירים לפרויקט
                col_actions1, col_actions2, col_actions3 = st.columns(3)
                
                # פונקציונליות 1: טעינת פרויקט לעמוד החישוב הראשי לעריכה
                if col_actions1.button("🔄 טען פרויקט זה לעמוד החישוב (עריכה)", key=f"load_{p_idx}", use_container_width=True):
                    # הזרקת הנתונים למשתני ה-Session State של המחשבון
                    st.session_state.input_project_name = project.get('project_name', '')
                    st.session_state.input_client_name = project.get('client_name', '')
                    st.session_state.input_client_phone = project.get('phone', '')
                    st.session_state.input_client_address = project.get('address', '')
                    st.session_state.input_project_date = project.get('date', str(datetime.now().date()))
                    
                    lab = project.get('labor_data', {})
                    st.session_state.input_num_workers = lab.get('num_workers', 1)
                    st.session_state.input_days_of_work = lab.get('days_of_work', 1)
                    st.session_state.input_daily_wage = lab.get('daily_wage', 0.0)
                    
                    ext = project.get('external_expenses', {})
                    st.session_state.input_powder = ext.get('powder', 0.0) if isinstance(ext, dict) else 0.0
                    st.session_state.input_laser = ext.get('laser', 0.0) if isinstance(ext, dict) else 0.0
                    st.session_state.input_transport = ext.get('transport', 0.0) if isinstance(ext, dict) else 0.0
                    st.session_state.input_crane = ext.get('crane', 0.0) if isinstance(ext, dict) else 0.0
                    st.session_state.input_carpentry = ext.get('carpentry', 0.0) if isinstance(ext, dict) else 0.0
                    st.session_state.input_glazing = ext.get('glazing', 0.0) if isinstance(ext, dict) else 0.0
                    st.session_state.input_other = ext.get('other', 0.0) if isinstance(ext, dict) else 0.0
                    
                    st.session_state.input_multiplier = project.get('multiplier', 1.5)
                    st.session_state.project_groups = project.get('groups_data', [])
                    
                    # שינוי העמוד אקטיבית ורענון המערכת
                    st.session_state.current_page = "📊 חישוב פרויקט"
                    st.rerun()

                st.markdown(f"""
                <div class='customer-info-box'>
                👤 <b>שם הלקוח:</b> {project.get('client_name','-')} | 📞 <b>מספר טלפון:</b> {project.get('phone','-')} <br>
                📍 <b>כתובת הפרויקט:</b> {project.get('address','-')} | 📅 <b>תאריך פתיחה:</b> {project.get('date','-')}
                </div>
                """, unsafe_allow_html=True)
                
                st.subheader("🧱 פקודת חיתוך וחומרים (מחושב חי לפרויקט זה):")
                archived_iron_cost = 0.0
                pdf_archive_materials_html = ""
                
                for group in project.get('groups_data', []):
                    st.markdown(f"🔹 **סוג חומר:** {group['sel_type']} | **מידה:** {group['sel_dim']} | **עובי דופן:** {group['sel_thk']}")
                    
                    max_len = st.session_state.dynamic_catalog[group['sel_type']]['length']
                    single_price = st.session_state.dynamic_catalog[group['sel_type']]["prices"].get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
                    
                    bars_plan, err = calculate_optimal_cutting(group['cuts'], max_len)
                    if not err:
                        group_bars_count = len(bars_plan)
                        group_cost = group_bars_count * single_price
                        archived_iron_cost += group_cost
                        display_visual_bars(bars_plan, max_len)
                        
                        # בניית סיכום החיתוכים לרשימה ב-PDF (כולל זווית)
                        archive_cuts_text = "".join([f"<li>{c['qty']} יחידות x {c['length']} ס\"מ (חיתוך: {c.get('angle', 'ישר / ישר (90°)')})</li>" for c in group['cuts']])
                        bars_html_archive_pdf = generate_html_bars_for_pdf(bars_plan, max_len)
                        pdf_archive_materials_html += f"""
                        <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; background-color: #fafafa; border-radius: 6px;">
                            <h3 style="margin-top:0; color:#1976d2;">🛠️ חומר: {group['sel_type']} ({group['sel_dim']} | {group['sel_thk']})</h3>
                            <p><b>חיתוכים:</b></p>
                            <ul>{archive_cuts_text}</ul>
                            {bars_html_archive_pdf}
                        </div>
                        """
                    else:
                        st.error(f"שגיאה בחישוב חיתוך לחלק מקבוצות החומר: {err}")
                
                st.markdown("---")
                ext = project.get('external_expenses', {})
                lab = project.get('labor_data', {})
                
                lab_total = lab.get('num_workers', 0) * lab.get('days_of_work', 0) * lab.get('daily_wage', 0)
                ext_total = sum(ext.values()) if isinstance(ext, dict) else 0.0
                ext_total += lab_total
                
                total_archived_expenses = archived_iron_cost + ext_total
                final_quote_archived = total_archived_expenses * project.get('multiplier', 1.5)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("עלות ברזל עדכנית", f"₪ {archived_iron_cost:,.2f}")
                c2.metric("הוצאות ועבודה נלווים", f"₪ {ext_total:,.2f}")
                c3.metric("הצעת מחיר סופית ללקוח", f"₪ {final_quote_archived:,.2f}")
                
                # הכנת קוד PDF ישיר מהארכיון
                archive_ext_pdf_dict = {
                    'labor': lab_total,
                    'powder': ext.get('powder', 0.0) if isinstance(ext, dict) else 0.0,
                    'laser': ext.get('laser', 0.0) if isinstance(ext, dict) else 0.0,
                    'transport': ext.get('transport', 0.0) if isinstance(ext, dict) else 0.0,
                    'crane': ext.get('crane', 0.0) if isinstance(ext, dict) else 0.0,
                    'carpentry': ext.get('carpentry', 0.0) if isinstance(ext, dict) else 0.0,
                    'glazing': ext.get('glazing', 0.0) if isinstance(ext, dict) else 0.0,
                    'other': ext.get('other', 0.0) if isinstance(ext, dict) else 0.0
                }
                archive_html_pdf_template = build_pdf_html_content(
                    p_title, project.get('client_name','-'), project.get('phone','-'), 
                    project.get('address','-'), project.get('date','-'), project.get('multiplier', 1.5),
                    archived_iron_cost, archive_ext_pdf_dict, total_archived_expenses, final_quote_archived,
                    pdf_archive_materials_html
                )
                
                # פונקציונליות 2: כפתור הורדת PDF ישירות מתוך הארכיון
                clean_archive_filename = re.sub(r'[\/*?:"<>|]', "", p_title)
                col_actions2.download_button(
                    label="📄 הורד מסמך PDF מהארכיון",
                    data=archive_html_pdf_template,
                    file_name=f"ארכיון_פרויקט_{clean_archive_filename}.html",
                    mime="text/html",
                    key=f"pdf_arch_{p_idx}",
                    use_container_width=True
                )
                
                # פונקציונליות 3: מחיקת פרויקט מהארכיון
                if col_actions3.button("❌ מחק פרויקט לצמיתות", key=f"del_{p_idx}", use_container_width=True):
                    st.session_state.saved_projects.pop(p_idx)
                    if save_to_github("saved_projects.json", st.session_state.saved_projects, f"מחיקת פרויקט {p_title}"):
                        st.success("הפרויקט נמחק בהצלחה מהארכיון!")
                        st.rerun()
                    else:
                        st.error("תקלה בעדכון המחיקה מול השרת.")
