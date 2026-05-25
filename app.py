import streamlit as st
import pandas as pd
import json
import requests
import base64
import re
from datetime import datetime

# =============================================================================
# הגדרות עיצוב ומערכת (RTL ומראה נקי)
# =============================================================================
st.set_page_config(page_title="מערכת תמחור וחיתוך - Elad Cohen Iron Art", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# חיבור מאובטח ל-GitHub
# =============================================================================
GITHUB_USERNAME = "eladccc5"
GITHUB_REPO = "metal-app"

if "GITHUB_TOKEN" in st.secrets:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
else:
    GITHUB_TOKEN = ""

def get_initial_catalog():
    return {
        "פרופיל מרובע": {"dimensions": ["20x20", "25x25", "30x30", "40x40", "50x50", "60x60", "80x80", "100x100", "120x120"], "thicknesses": ["1.5 מ\"מ", "2.0 מ\"מ", "2.5 מ\"מ", "3.0 מ\"מ"], "length": 600, "prices": {}},
        "פרופיל מלבני": {"dimensions": ["40x20", "50x20", "50x25", "60x40", "80x40", "100x40", "100x50", "150x50"], "thicknesses": ["1.5 מ\"מ", "2.0 מ\"מ", "2.5 מ\"מ", "3.0 מ\"מ"], "length": 600, "prices": {}},
        "שטוח": {"dimensions": ["20 מ\"מ", "25 מ\"מ", "30 מ\"מ", "35 מ\"מ", "40 מ\"מ", "50 מ\"מ", "60 מ\"מ", "80 מ\"מ", "100 מ\"מ"], "thicknesses": ["3 מ\"מ", "5 מ\"מ", "8 מ\"מ", "10 מ\"מ", "12 מ\"מ"], "length": 300, "prices": {}},
        "זווית": {"dimensions": ["20x20", "25x25", "30x30", "40x40", "50x50"], "thicknesses": ["3 מ\"מ", "4 מ\"מ", "5 מ\"מ"], "length": 600, "prices": {}},
        "מוט עגול מלא": {"dimensions": ["8 מ\"מ", "10 מ\"מ", "12 מ\"מ", "14 מ\"מ", "16 מ\"מ", "18 מ\"מ", "20 מ\"מ", "25 מ\"מ"], "thicknesses": ["מלא"], "length": 600, "prices": {}},
        "מוט מרובע מלא": {"dimensions": ["10x10", "12x12", "14x14", "16x16", "20x20", "25x25"], "thicknesses": ["מלא"], "length": 600, "prices": {}}
    }

def fetch_from_github(filename, default_factory):
    if not GITHUB_TOKEN: return default_factory()
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content_str = base64.b64decode(res.json().get("content")).decode("utf-8")
            return json.loads(content_str)
    except: pass
    return default_factory()

def save_to_github(filename, data_to_save, commit_message):
    if not GITHUB_TOKEN: return False
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    content_b64 = base64.b64encode(json.dumps(data_to_save, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8")
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    payload = {"message": commit_message, "content": content_b64, "branch": "main"}
    if sha: payload["sha"] = sha
    try: return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except: return False

def sort_dimensions_list(dims_list):
    def parse_key(d_str):
        nums = [float(s) for s in re.findall(r'\d+\.?\d*', d_str.replace('*', 'x'))]
        return nums if nums else [0.0]
    cleaned = list(set([d.replace('*', 'x').strip() for d in dims_list]))
    return sorted(cleaned, key=parse_key)

# טעינת נתונים
if 'dynamic_catalog' not in st.session_state:
    st.session_state.dynamic_catalog = fetch_from_github("saved_prices.json", get_initial_catalog)
if 'saved_projects' not in st.session_state:
    st.session_state.saved_projects = fetch_from_github("saved_projects.json", list)
if 'project_groups' not in st.session_state:
    first_type = list(st.session_state.dynamic_catalog.keys())[0]
    st.session_state.project_groups = [{'sel_type': first_type, 'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0], 'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0], 'cuts': [{'length': 100.0, 'qty': 1}]}]

def calculate_optimal_cutting(cuts_list, max_capacity):
    all_pieces = []
    for cut in cuts_list:
        for _ in range(int(cut['qty'])):
            if cut['length'] > max_capacity: return None, f"אורך {cut['length']} חורג מהמוט."
            all_pieces.append(cut['length'])
    all_pieces.sort(reverse=True)
    bars = []
    for piece in all_pieces:
        placed = False
        for bar in bars:
            if sum(bar) + piece <= max_capacity:
                bar.append(piece)
                placed = True
                break
        if not placed: bars.append([piece])
    return bars, None

# =============================================================================
# תפריט צדדי (Sidebar)
# =============================================================================
st.sidebar.title("🛠️ Elad Cohen Iron Art")
page = st.sidebar.radio("ניווט:", ["💰 מחירון ברזל", "📊 חישוב פרויקט", "📂 ארכיון פרויקטים"])

st.sidebar.markdown("---")
st.sidebar.subheader("👤 פרטי הלקוח והפרויקט")
client_name = st.sidebar.text_input("שם הלקוח:")
client_phone = st.sidebar.text_input("מספר טלפון:")
client_address = st.sidebar.text_input("כתובת הפרויקט:")
project_date = st.sidebar.date_input("תאריך:", datetime.now())

st.sidebar.markdown("---")
st.sidebar.subheader("👷 עלויות עבודה")
num_workers = st.sidebar.number_input("כמות עובדים:", min_value=0, value=1)
days_of_work = st.sidebar.number_input("ימי עבודה:", min_value=0, value=1)
daily_wage = st.sidebar.number_input("עלות יומית לעובד (₪):", min_value=0.0, value=0.0, step=50.0)
calculated_labor_cost = num_workers * days_of_work * daily_wage

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 הוצאות נלוות")
powder_coating_cost = st.sidebar.number_input("צביעה בתנור (₪):", min_value=0.0, value=0.0)
laser_cutting_cost = st.sidebar.number_input("חיתוך לייזר (₪):", min_value=0.0, value=0.0)
transportation_cost = st.sidebar.number_input("הובלה (₪):", min_value=0.0, value=0.0)
crane_cost = st.sidebar.number_input("מנוף (₪):", min_value=0.0, value=0.0)
carpentry_cost = st.sidebar.number_input("נגרות (₪):", min_value=0.0, value=0.0)
glazing_cost = st.sidebar.number_input("זגגות (₪):", min_value=0.0, value=0.0)
other_expenses = st.sidebar.number_input("שונות (₪):", min_value=0.0, value=0.0)
profit_multiplier = st.sidebar.slider("מכפיל רווח:", 1.0, 4.0, 1.5, 0.1)

total_external_expenses = (calculated_labor_cost + powder_coating_cost + laser_cutting_cost + 
                           transportation_cost + crane_cost + carpentry_cost + glazing_cost + other_expenses)

# =============================================================================
# פונקציית עזר להצגת המוטות (הכחולים/אדומים)
# =============================================================================
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

# =============================================================================
# עמודים
# =============================================================================
if page == "💰 מחירון ברזל":
    st.title("📋 קטלוג ומחירון ברזל")
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
    if st.button("🔴 שמור מחירון לענן", type="primary", use_container_width=True):
        if save_to_github("saved_prices.json", st.session_state.dynamic_catalog, "עדכון מחירון"): st.success("נשמר!")

elif page == "📊 חישוב פרויקט":
    st.title("📊 מחשבון פרויקטים ועלויות")
    if st.button("➕ הוסף קבוצת חומר", use_container_width=True):
        st.session_state.project_groups.append({'sel_type': 'פרופיל מרובע', 'sel_dim': '20x20', 'sel_thk': '2.0 מ"מ', 'cuts': [{'length': 100.0, 'qty': 1}]})
        st.rerun()

    total_project_iron_cost = 0.0
    for g_idx, group in enumerate(st.session_state.project_groups):
        st.markdown(f"<div class='material-block'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2,2,2,1])
        group['sel_type'] = c1.selectbox("חומר:", list(st.session_state.dynamic_catalog.keys()), key=f"t_{g_idx}")
        group['sel_dim'] = c2.selectbox("מידה:", st.session_state.dynamic_catalog[group['sel_type']]["dimensions"], key=f"d_{g_idx}")
        group['sel_thk'] = c3.selectbox("עובי:", st.session_state.dynamic_catalog[group['sel_type']]["thicknesses"], key=f"th_{g_idx}")
        if c4.button("🗑️", key=f"dg_{g_idx}"): 
            st.session_state.project_groups.pop(g_idx)
            st.rerun()
        
        for c_idx, cut in enumerate(group['cuts']):
            cc1, cc2, cc3 = st.columns([3, 3, 1])
            cut['length'] = cc1.number_input("אורך (ס\"מ):", min_value=0.1, value=float(cut['length']), key=f"l_{g_idx}_{c_idx}")
            cut['qty'] = cc2.number_input("כמות:", min_value=1, value=int(cut['qty']), key=f"q_{g_idx}_{c_idx}")
            if cc3.button("❌", key=f"dc_{g_idx}_{c_idx}"): 
                group['cuts'].pop(c_idx)
                st.rerun()
        if st.button("➕ חיתוך", key=f"ac_{g_idx}"): 
            group['cuts'].append({'length': 50.0, 'qty': 1})
            st.rerun()

        max_len = st.session_state.dynamic_catalog[group['sel_type']]['length']
        single_price = st.session_state.dynamic_catalog[group['sel_type']]["prices"].get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
        bars_plan, err = calculate_optimal_cutting(group['cuts'], max_len)
        if not err:
            total_project_iron_cost += len(bars_plan) * single_price
            display_visual_bars(bars_plan, max_len)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    total_expenses = total_project_iron_cost + total_external_expenses
    client_price = total_expenses * profit_multiplier
    st.header(f"💰 הצעת מחיר סופית: ₪ {client_price:,.2f}")

    p_name = st.text_input("שם הפרויקט לשמירה:")
    if st.button("💾 שמור פרויקט לארכיון", use_container_width=True):
        new_entry = {
            'project_name': p_name, 'client_name': client_name, 'phone': client_phone, 'address': client_address,
            'date': str(project_date), 'multiplier': profit_multiplier, 'labor_data': {'num_workers': num_workers, 'days_of_work': days_of_work, 'daily_wage': daily_wage},
            'external_expenses': {'powder': powder_coating_cost, 'laser': laser_cutting_cost, 'transport': transportation_cost, 'crane': crane_cost, 'carpentry': carpentry_cost, 'glazing': glazing_cost, 'other': other_expenses},
            'groups_data': st.session_state.project_groups
        }
        st.session_state.saved_projects.append(new_entry)
        if save_to_github("saved_projects.json", st.session_state.saved_projects, f"שמירת פרויקט {p_name}"): st.success("נשמר בארכיון!")

else:
    st.title("📂 ארכיון פרויקטים שמורים")
    if not st.session_state.saved_projects: st.info("אין פרויקטים שמורים.")
    else:
        for p_idx, project in enumerate(st.session_state.saved_projects):
            with st.expander(f"📁 פרויקט: {project.get('project_name','-')} | לקוח: {project.get('client_name','-')} | תאריך: {project.get('date','-')}"):
                st.markdown(f"""
                <div class='customer-info-box'>
                👤 <b>שם לקוח:</b> {project.get('client_name','-')} | 📞 <b>טלפון:</b> {project.get('phone','-')} <br>
                📍 <b>כתובת:</b> {project.get('address','-')} | 📅 <b>תאריך:</b> {project.get('date','-')}
                </div>
                """, unsafe_allow_html=True)
                
                # חישוב חיתוכים ועלויות בזמן אמת בתוך הארכיון
                st.subheader("🧱 פקודת חיתוך וחומרים:")
                p_iron_cost = 0.0
                for group in project.get('groups_data', []):
                    st.markdown(f"**חומר:** {group['sel_type']} | **מידה:** {group['sel_dim']} | **עובי:** {group['sel_thk']}")
                    max_len = st.session_state.dynamic_catalog[group['sel_type']]['length']
                    single_price = st.session_state.dynamic_catalog[group['sel_type']]["prices"].get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
                    bars_plan, err = calculate_optimal_cutting(group['cuts'], max_len)
                    if not err:
                        p_iron_cost += len(bars_plan) * single_price
                        display_visual_bars(bars_plan, max_len)
                
                st.markdown("---")
                ext = project.get('external_expenses', {})
                lab = project.get('labor_data', {})
                lab_total = lab.get('num_workers',0) * lab.get('days_of_work',0) * lab.get('daily_wage',0)
                ext_total = sum(ext.values()) + lab_total
                total_p_exp = p_iron_cost + ext_total
                final_quote = total_p_exp * project.get('multiplier', 1.5)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("עלות ברזל", f"₪ {p_iron_cost:,.2f}")
                c2.metric("הוצאות נלוות", f"₪ {ext_total:,.2f}")
                c3.metric("הצעת מחיר סופית", f"₪ {final_quote:,.2f}")

                if st.button("❌ מחק פרויקט", key=f"del_{p_idx}"):
                    st.session_state.saved_projects.pop(p_idx)
                    save_to_github("saved_projects.json", st.session_state.saved_projects, "מחיקת פרויקט")
                    st.rerun()
