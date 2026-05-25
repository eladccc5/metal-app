import streamlit as st
import pandas as pd
import json
import requests
import base64
import re

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
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# חיבור מאובטח ומובנה ל-GitHub (משיכת הטוקן מתוך ה-Secrets המאובטחים)
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
    if not GITHUB_TOKEN:
        return default_factory()
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content_b64 = res.json().get("content")
            content_str = base64.b64decode(content_b64).decode("utf-8")
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

def sort_dimensions_list(dims_list):
    def parse_key(d_str):
        nums = [float(s) for s in re.findall(r'\d+\.?\d*', d_str.replace('*', 'x').replace('X', 'x'))]
        return nums if nums else [0.0]
    cleaned = list(set([d.replace('*', 'x').replace('X', 'x').strip() for d in dims_list]))
    return sorted(cleaned, key=parse_key)

# טעינת נתונים מהענן
if 'dynamic_catalog' not in st.session_state:
    st.session_state.dynamic_catalog = fetch_from_github("saved_prices.json", get_initial_catalog)
    for m in st.session_state.dynamic_catalog:
        st.session_state.dynamic_catalog[m]["dimensions"] = sort_dimensions_list(st.session_state.dynamic_catalog[m]["dimensions"])

if 'saved_projects' not in st.session_state:
    st.session_state.saved_projects = fetch_from_github("saved_projects.json", list)

if 'project_groups' not in st.session_state:
    first_type = list(st.session_state.dynamic_catalog.keys())[0]
    st.session_state.project_groups = [{
        'sel_type': first_type,
        'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0],
        'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0],
        'cuts': [{'length': 100.0, 'qty': 1}]
    }]

def calculate_optimal_cutting(cuts_list, max_capacity):
    all_pieces = []
    for cut in cuts_list:
        for _ in range(int(cut['qty'])):
            if cut['length'] > max_capacity:
                return None, f"חתיכה באורך {cut['length']} ס\"מ ארוכה יותר מאורך מוט מלא ({max_capacity} ס\"מ)."
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
        if not placed:
            bars.append([piece])
    return bars, None

# =============================================================================
# תפריט וניווט צדדי + תפריט הוצאות מפורט
# =============================================================================
st.sidebar.title("🛠️ Elad Cohen Iron Art")
page = st.sidebar.radio("ניווט בין עמודים:", ["💰 עמוד מחירון ומלאי ברזל", "📊 חישוב פרויקט ושרטוטים", "📂 ארכיון פרויקטים שמורים"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ הגדרות רווח ועלויות פרויקט")
profit_multiplier = st.sidebar.slider("מכפיל רווח (עבור הצעת מחיר):", 1.0, 4.0, 1.5, 0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("👷 פירוט עלויות עבודה וכוח אדם")
num_workers = st.sidebar.number_input("כמות עובדים בפרויקט:", min_value=0, value=1, step=1)
days_of_work = st.sidebar.number_input("ימי עבודה נדרשים:", min_value=0, value=1, step=1)
daily_wage = st.sidebar.number_input("עלות יומית לעובד (₪):", min_value=0.0, value=0.0, step=50.0)

# חישוב אוטומטי של סעיף כוח האדם
calculated_labor_cost = num_workers * days_of_work * daily_wage
st.sidebar.caption(f"סך עלות עבודה מחושבת: ₪ {calculated_labor_cost:,.2f}")

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 עלויות נלוות והוצאות חיצוניות")
powder_coating_cost = st.sidebar.number_input("צביעה בתנור (₪):", min_value=0.0, value=0.0, step=50.0)
laser_cutting_cost = st.sidebar.number_input("חיתוך לייזר (₪):", min_value=0.0, value=0.0, step=50.0)
transportation_cost = st.sidebar.number_input("הובלה (₪):", min_value=0.0, value=0.0, step=50.0)
crane_cost = st.sidebar.number_input("מנוף (₪):", min_value=0.0, value=0.0, step=50.0)
carpentry_cost = st.sidebar.number_input("נגרות (₪):", min_value=0.0, value=0.0, step=50.0)
glazing_cost = st.sidebar.number_input("זגגות / זכוכית (₪):", min_value=0.0, value=0.0, step=50.0)
other_expenses = st.sidebar.number_input("הוצאות שונות (₪):", min_value=0.0, value=0.0, step=50.0)

# סך כל ההוצאות החיצוניות והנלוות (ללא הברזל)
total_external_expenses = (calculated_labor_cost + powder_coating_cost + laser_cutting_cost + 
                           transportation_cost + crane_cost + carpentry_cost + glazing_cost + other_expenses)

# =============================================================================
# עמוד 1: ניהול קטלוג ומחירון דינמי
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון ברזל דינמי")
    st.write("עדכן את מחירי המוטות בטבלאות למטה. בסיום, לחץ על כפתור השמירה האדום בתחתית העמוד.")
    
    cat_keys = list(st.session_state.dynamic_catalog.keys())
    tabs = st.tabs([f"🔳 {t}" for t in cat_keys])
    
    for idx, mat_type in enumerate(cat_keys):
        with tabs[idx]:
            info = st.session_state.dynamic_catalog[mat_type]
            st.write(f"**אורך מוט סטנדרטי ביחידות אלו:** {info['length']} ס\"מ")
            
            data_matrix = []
            for d in info["dimensions"]:
                row_dict = {"מידות": d}
                for thk in info["thicknesses"]:
                    row_dict[thk] = info.get("prices", {}).get(d, {}).get(thk, 0.0)
                data_matrix.append(row_dict)
            
            df = pd.DataFrame(data_matrix)
            edited_df = st.data_editor(df, key=f"editor_{mat_type}", use_container_width=True, hide_index=True, disabled=["מידות"])
            
            if "prices" not in info:
                info["prices"] = {}
            for _, row in edited_df.iterrows():
                dim = row["מידות"]
                if dim not in info["prices"]:
                    info["prices"][dim] = {}
                for thk in info["thicknesses"]:
                    info["prices"][dim][thk] = float(row[thk])

    st.markdown("<div class='admin-box'>", unsafe_allow_html=True)
    st.subheader("⚙️ ניהול ועריכת רשימת המידות")
    
    col_add1, col_add2 = st.columns([2, 1])
    target_type = col_add1.selectbox("בחר סוג ברזל לניהול המידות:", cat_keys)
    new_dim = col_add2.text_input("הקלד מידה חדשה להוספה (למשל: 45x45):")
    
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("➕ הוסף מידה זו לרשימה", use_container_width=True):
        if new_dim:
            clean_name = new_dim.replace('*', 'x').replace('X', 'x').strip()
            if clean_name not in st.session_state.dynamic_catalog[target_type]["dimensions"]:
                st.session_state.dynamic_catalog[target_type]["dimensions"].append(clean_name)
                st.session_state.dynamic_catalog[target_type]["dimensions"] = sort_dimensions_list(st.session_state.dynamic_catalog[target_type]["dimensions"])
                st.success(f"המידה {clean_name} התווספה בהצלחה! לחץ על כפתור השמירה האדום למטה כדי לקבע אותה.")
                st.rerun()
            else:
                st.warning("המידה הזו כבר קיימת בקטלוג.")
        else:
            st.error("אנא הכנס ערך תקין בשדה המידה.")
            
    dim_to_delete = col_btn2.selectbox("בחר מידה קיימת למחיקה מהקטלוג:", st.session_state.dynamic_catalog[target_type]["dimensions"])
    if col_btn2.button("❌ מחק מידה נבחרת מהרשימה", use_container_width=True):
        if dim_to_delete in st.session_state.dynamic_catalog[target_type]["dimensions"]:
            st.session_state.dynamic_catalog[target_type]["dimensions"].remove(dim_to_delete)
            if dim_to_delete in st.session_state.dynamic_catalog[target_type].get("prices", {}):
                del st.session_state.dynamic_catalog[target_type]["prices"][dim_to_delete]
            st.success(f"המידה {dim_to_delete} הוסרה מהרשימה הזמנית! לחץ על כפתור השמירה האדום למטה לעדכון סופי.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔴 שמור את כל השינויים, המידות והמיון לתמיד", type="primary", use_container_width=True):
        if not GITHUB_TOKEN:
            st.error("לא נמצא מפתח גישה (Token) מוגדר ב-Secrets של האפליקציה. אנא הגדר אותו תחילה.")
        else:
            with st.spinner("שומר את השינויים ומסנכרן מול השרת..."):
                if save_to_github("saved_prices.json", st.session_state.dynamic_catalog, "🔄 עדכון מחירון ומיון מידות"):
                    st.success("🔥 כל המחירים עודכנו, המידות הכפולות אוחדו והכל נשמר בבטחה בענן!")
                else:
                    st.error("תקלה בתקשורת עם GitHub. ודא שההרשאות ב-Token והחיבור ב-Secrets תקינים.")

# =============================================================================
# עמוד 2: מחשבון פרויקטים, אופטימיזציית חיתוך ועלויות מפורטות
# =============================================================================
elif page == "📊 חישוב פרויקט ושרטוטים":
    st.title("📊 מחשבון פרויקטים, אופטימיזציית חיתוך ועלויות")
    
    col_actions = st.columns(2)
    if col_actions[0].button("➕ הוסף קבוצת חומר חדשה לפרויקט", use_container_width=True):
        first_type = list(st.session_state.dynamic_catalog.keys())[0]
        st.session_state.project_groups.append({
            'sel_type': first_type,
            'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0],
            'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0],
            'cuts': [{'length': 100.0, 'qty': 1}]
        })
        st.rerun()
        
    if col_actions[1].button("🗑️ איפוס וניקוי כל הפרויקט הנוכחי", use_container_width=True):
        first_type = list(st.session_state.dynamic_catalog.keys())[0]
        st.session_state.project_groups = [{
            'sel_type': first_type,
            'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0],
            'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0],
            'cuts': [{'length': 100.0, 'qty': 1}]
        }]
        st.rerun()

    st.markdown("---")
    total_project_iron_cost = 0.0
    all_groups_valid = True
    
    for g_idx, group in enumerate(st.session_state.project_groups):
        st.markdown(f"<div class='material-block'>", unsafe_allow_html=True)
        col_g1, col_g2, col_g3, col_g4 = st.columns([2, 2, 2, 1])
        
        group['sel_type'] = col_g1.selectbox("סוג חומר:", list(st.session_state.dynamic_catalog.keys()), key=f"type_{g_idx}")
        
        available_dims = st.session_state.dynamic_catalog[group['sel_type']]["dimensions"]
        if group['sel_dim'] not in available_dims:
            group['sel_dim'] = available_dims[0]
        group['sel_dim'] = col_g2.selectbox("מידה:", available_dims, key=f"dim_{g_idx}")
        
        available_thks = st.session_state.dynamic_catalog[group['sel_type']]["thicknesses"]
        if group['sel_thk'] not in available_thks:
            group['sel_thk'] = available_thks[0]
        group['sel_thk'] = col_g3.selectbox("עובי דופן / סוג:", available_thks, key=f"thk_{g_idx}")
        
        if col_g4.button("🗑️ מחק קבוצה", key=f"del_g_{g_idx}"):
            if len(st.session_state.project_groups) > 1:
                st.session_state.project_groups.pop(g_idx)
                st.rerun()
            else:
                st.warning("חובה להשאיר לפחות קבוצת חומר אחת בפרויקט.")

        st.markdown("##### 📏 רשימת אכיפת אורך וחיתוכים לחומר זה:")
        
        cuts_to_delete = []
        for c_idx, cut in enumerate(group['cuts']):
            c_col1, c_col2, c_col3 = st.columns([3, 3, 1])
            cut['length'] = c_col1.number_input("אורך חתיכה דרוש (בס\"מ):", min_value=0.1, value=float(cut['length']), step=1.0, key=f"len_{g_idx}_{c_idx}")
            cut['qty'] = c_col2.number_input("כמות חתיכות באורך זה:", min_value=1, value=int(cut['qty']), step=1, key=f"qty_{g_idx}_{c_idx}")
            if c_col3.button("🗑️", key=f"del_c_{g_idx}_{c_idx}"):
                cuts_to_delete.append(c_idx)
                
        for index in sorted(cuts_to_delete, reverse=True):
            group['cuts'].pop(index)
            st.rerun()
            
        if st.button("➕ הוסף מידת חיתוך נוספת לחומר זה", key=f"add_cut_{g_idx}"):
            group['cuts'].append({'length': 50.0, 'qty': 1})
            st.rerun()

        max_bar_len = st.session_state.dynamic_catalog[group['sel_type']]['length']
        single_bar_price = st.session_state.dynamic_catalog[group['sel_type']]["prices"].get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
        
        bars_plan, error_msg = calculate_optimal_cutting(group['cuts'], max_bar_len)
        
        if error_msg:
            st.error(error_msg)
            all_groups_valid = False
        else:
            num_bars_needed = len(bars_plan)
            group_iron_cost = num_bars_needed * single_bar_price
            total_project_iron_cost += group_iron_cost
            
            st.markdown(f"<div style='margin-top:15px;'>", unsafe_allow_html=True)
            st.success(f"📊 **תוצאת אופטימיזציה:** נדרשים **{num_bars_needed}** מוטות מלאים. עלות הברזל לקבוצה זו: **₪ {group_iron_cost:,.2f}**")
            
            for b_id, bar_cuts in enumerate(bars_plan):
                used_space = sum(bar_cuts)
                leftover = max_bar_len - used_space
                st.markdown(f"**מוט #{b_id + 1} (נשאר פחת של {leftover:.1f} ס\"מ):**")
                
                bar_html = f"<div style='display: block; width: 100%; background-color: #e0e0e0; border-radius: 6px; margin: 6px 0; font-size:12px; font-weight:bold; color:white; overflow:hidden; border:1px solid #ccc;'>"
                for part in bar_cuts:
                    percentage = (part / max_bar_len) * 100
                    bar_html += f"<div style='display: inline-block; width: {percentage}%; background-color: #1976d2; text-align: center; padding: 6px 0; border-left: 2px solid #fff; float: right;'>{part} ס\"מ</div>"
                if leftover > 0:
                    left_pct = (leftover / max_bar_len) * 100
                    bar_html += f"<div style='display: inline-block; width: {left_pct}%; background-color: #d32f2f; text-align: center; padding: 6px 0; float: right;'>פחת: {leftover:.1f}</div>"
                bar_html += "<div style='clear: both;'></div></div>"
                st.markdown(bar_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if all_groups_valid:
        st.markdown("---")
        st.header("🔍 פירוט עלויות הפרויקט (נטו)")
        
        # תצוגת פירוט ההוצאות לנוחות המשתמש
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        with col_exp1:
            st.markdown(f"<div class='expense-box'>🧱 **ברזל וחומרי גלם:** ₪ {total_project_iron_cost:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='expense-box'>👷 **כוח אדם ומסגרות:** ₪ {calculated_labor_cost:,.2f}<br><small>({num_workers} עובדים × {days_of_work} ימים)</small></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='expense-box'>🎨 **צביעה בתנור:** ₪ {powder_coating_cost:,.2f}</div>", unsafe_allow_html=True)
        with col_exp2:
            st.markdown(f"<div class='expense-box'>⚡ **חיתוך לייזר:** ₪ {laser_cutting_cost:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='expense-box'>🚚 **הובלה:** ₪ {transportation_cost:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='expense-box'>🏗️ **מנוף:** ₪ {crane_cost:,.2f}</div>", unsafe_allow_html=True)
        with col_exp3:
            st.markdown(f"<div class='expense-box'>🪵 **נגרות:** ₪ {carpentry_cost:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='expense-box'>🔮 **זגגות / זכוכית:** ₪ {glazing_cost:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='expense-box'>📦 **הוצאות שונות:** ₪ {other_expenses:,.2f}</div>", unsafe_allow_html=True)

        # סך ההוצאות הסופי
        total_project_expenses = total_project_iron_cost + total_external_expenses
        recommended_client_price = total_project_expenses * profit_multiplier
        net_project_profit = recommended_client_price - total_project_expenses
        
        st.markdown("### 💰 שורה תחתונה והצעת מחיר")
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("📉 סך כל הוצאות הפרויקט (נטו)", f"₪ {total_project_expenses:,.2f}")
        m_col2.metric("💎 הצעת מחיר מומלצת ללקוח", f"₪ {recommended_client_price:,.2f}")
        m_col3.metric("📈 רווח נקי משוער בפרויקט", f"₪ {net_project_profit:,.2f}")

        st.markdown("---")
        st.subheader("💾 שמירת פרויקט חדש לארכיון")
        
        col_s1, _ = st.columns(2)
        p_name_to_save = col_s1.text_input("הקלד שם לפרויקט הנוכחי כדי לשמור אותו:")
        
        if col_s1.button("💾 שמור פרויקט זה לארכיון הענן באפליקציה", use_container_width=True):
            if not GITHUB_TOKEN:
                st.error("לא נמצא מפתח גישה (Token) מוגדר ב-Secrets של האפליקציה. אננא הגדר אותו תחילה.")
            elif p_name_to_save:
                new_project_entry = {
                    'project_name': p_name_to_save,
                    'multiplier': profit_multiplier,
                    'labor_data': {
                        'num_workers': num_workers,
                        'days_of_work': days_of_work,
                        'daily_wage': daily_wage,
                        'calculated_labor_cost': calculated_labor_cost
                    },
                    'external_expenses': {
                        'powder_coating': powder_coating_cost,
                        'laser_cutting': laser_cutting_cost,
                        'transportation': transportation_cost,
                        'crane': crane_cost,
                        'carpentry': carpentry_cost,
                        'glazing': glazing_cost,
                        'other': other_expenses
                    },
                    'groups_data': st.session_state.project_groups
                }
                st.session_state.saved_projects = [p for p in st.session_state.saved_projects if p['project_name'] != p_name_to_save]
                st.session_state.saved_projects.append(new_project_entry)
                
                with st.spinner("שומר פרויקט בארכיון..."):
                    if save_to_github("saved_projects.json", st.session_state.saved_projects, f"📂 שמירת פרויקט מפורט: {p_name_to_save}"):
                        st.success(f"🎉 הפרויקט '{p_name_to_save}' נשמר בהצלחה עם כל פירוט ההוצאות!")
                    else:
                        st.error("תקלה בשמירה מול השרת. ודא שההרשאות ב-Token והחיבור ב-Secrets תקינים.")
            else:
                st.error("אנא הכנס שם לפרויקט לפני השמירה.")

# =============================================================================
# עמוד 3: ארכיון פרויקטים שמורים
# =============================================================================
else:
    st.title("📂 ארכיון הפרויקטים השמורים של Elad Cohen Iron Art")
    st.write("כאן שמורים כל הפרויקטים שסנכרנת מול הענן.")
    
    if not st.session_state.saved_projects:
        st.info("הארכיון ריק כרגע או שלא נשמרו פרויקטים בענן.")
    else:
        for p_idx, project in enumerate(st.session_state.saved_projects):
            with st.expander(f"📁 פרויקט: {project['project_name']}", expanded=False):
                col_p1, col_p2 = st.columns(2)
                col_p1.markdown(f"**מכפיל רווח שהוגדר:** {project.get('multiplier', 1.5)}")
                
                # תצוגת נתוני עבודה אם קיימים
                l_data = project.get('labor_data', {})
                if l_data:
                    col_p2.markdown(f"**עלות עבודה:** ₪ {l_data.get('calculated_labor_cost', 0.0):,.2f} ({l_data.get('num_workers', 1)} עובדים × {l_data.get('days_of_work', 1)} ימים)")
                else:
                    col_p2.markdown(f"**עלות עבודה (פורמט ישן):** ₪ {project.get('labor_cost', 0.0):,.2f}")
                
                # הצגת עלויות נלוות
                ext = project.get('external_expenses', {})
                if ext:
                    st.markdown("##### 🚚 הוצאות וספקי חוץ:")
                    ext_list = []
                    if ext.get('powder_coating', 0) > 0: ext_list.append(f"צביעה: ₪ {ext['powder_coating']:,.2f}")
                    if ext.get('laser_cutting', 0) > 0: ext_list.append(f"לייזר: ₪ {ext['laser_cutting']:,.2f}")
                    if ext.get('transportation', 0) > 0: ext_list.append(f"הובלה: ₪ {ext['transportation']:,.2f}")
                    if ext.get('crane', 0) > 0: ext_list.append(f"מנוף: ₪ {ext['crane']:,.2f}")
                    if ext.get('carpentry', 0) > 0: ext_list.append(f"נגרות: ₪ {ext['carpentry']:,.2f}")
                    if ext.get('glazing', 0) > 0: ext_list.append(f"זגגות: ₪ {ext['glazing']:,.2f}")
                    if ext.get('other', 0) > 0: ext_list.append(f"שונות: ₪ {ext['other']:,.2f}")
                    if ext_list:
                        st.markdown(" | ".join(ext_list))
                
                st.markdown("##### 🧱 חומרים וחיתוכים שנשמרו:")
                for group in project.get('groups_data', []):
                    st.markdown(f"• **{group['sel_type']}** — מידה: `{group['sel_dim']}` | עובי דופן: `{group['sel_thk']}`")
                    for cut in group.get('cuts', []):
                        st.markdown(f"  └── 📏 כמות: **{cut['qty']}** חתיכות | אורך: **{cut['length']} ס\"מ**")
                
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.button("📂 טען פרויקט זה למחשבון הראשי", key=f"load_p_page_{p_idx}", use_container_width=True):
                    st.session_state.project_groups = project['groups_data']
                    st.success(f"הפרויקט '{project['project_name']}' נטען! עבור לעמוד '📊 חישוב פרויקט ושרטוטים' כדי לראות את החישובים המלאים.")
                    st.rerun()
                    
                if col_btn2.button("❌ מחק פרויקט זה לצמיתות מהארכיון", key=f"del_p_page_{p_idx}", use_container_width=True):
                    if not GITHUB_TOKEN:
                        st.error("לא ניתן למחוק ללא מפתח גישה (Token) תקין ב-Secrets.")
                    else:
                        st.session_state.saved_projects.pop(p_idx)
                        with st.spinner("מוחק ומעדכן את הארכיון בענן..."):
                            if save_to_github("saved_projects.json", st.session_state.saved_projects, f"🗑️ מחיקת פרויקט מהארכיון"):
                                st.success("הפרויקט נמחק בהצלחה מהענן!")
                                st.rerun()
                            else:
                                st.error("תקלה בעדכון המחיקה מול השרת.")
