import streamlit as st
import pandas as pd
import json
import requests
import base64
import re

# -----------------------------------------------------------------------------
# הגדרות עיצוב ומרכוז טבלאות (CSS מיושר ותיקון סליידרים גלובלי)
# -----------------------------------------------------------------------------
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
    .stDataFrame table {
        direction: rtl !important;
        text-align: right !important;
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
    .project-card {
        border: 1px solid #e0e4ec;
        padding: 15px;
        border-radius: 8px;
        background-color: #ffffff;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
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
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# הגדרות חיבור קשיח ל-GitHub לצורך שמירה קבועה
# -----------------------------------------------------------------------------
GITHUB_USERNAME = "eladccc5"             
GITHUB_REPO = "metal-app"                
GITHUB_TOKEN = "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"     

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
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content_b64 = res.json().get("content")
            content_str = base64.b64decode(content_b64).decode("utf-8")
            loaded_data = json.loads(content_str)
            if loaded_data and (isinstance(loaded_data, dict) or isinstance(loaded_data, list)) and len(loaded_data) > 0:
                return loaded_data
    except:
        pass
    return default_factory()

def save_to_github(filename, data_to_save, commit_message):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    content_str = json.dumps(data_to_save, ensure_ascii=False, indent=4)
    content_bytes = content_str.encode("utf-8")
    content_b64 = base64.b64encode(content_bytes).decode("utf-8")
    
    res = requests.get(url, headers=headers)
    sha = None
    if res.status_code == 200:
        sha = res.json().get("sha")
        
    data = {
        "message": commit_message,
        "content": content_b64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
        
    put_res = requests.put(url, headers=headers, json=data)
    return put_res.status_code in [200, 201]

def parse_dimension_key(dim_str):
    """מחלץ מספרים מתוך הטקסט של המידה כדי למיין מהקטן לגדול בצורה נכונה"""
    # ניקוי והאחדה של סימונים נפוצים כמו כוכבית או X גדולה ל-x קטנה
    cleaned = dim_str.replace('*', 'x').replace('X', 'x')
    numbers = [float(s) for s in re.findall(r'\d+\.?\d*', cleaned)]
    return numbers if numbers else [0.0]

def sort_dimensions_list(dims_list):
    """מנקה כפילויות, מאחד פורמט וממיין את רשימת המידות מהקטן לגדול"""
    cleaned_list = []
    for d in dims_list:
        # הופך "35*35" או "35X35" ל- "35x35" באופן קבוע
        normalized = d.replace('*', 'x').replace('X', 'x')
        cleaned_list.append(normalized)
    return sorted(list(set(cleaned_list)), key=parse_dimension_key)

def load_catalog():
    current = fetch_from_github("saved_prices.json", get_initial_catalog)
    default = get_initial_catalog()
    
    # הבטחה שכל קטגוריות ברירת המחדל קיימות
    for k, v in default.items():
        if k not in current:
            current[k] = v
    
    # מיון אוטומטי של המידות בכל הפעלה
    for mat_type in current:
        current[mat_type]["dimensions"] = sort_dimensions_list(current[mat_type]["dimensions"])
    return current

def load_projects():
    return fetch_from_github("saved_projects.json", list)

# -----------------------------------------------------------------------------
# אתחול הנתונים באפליקציה
# -----------------------------------------------------------------------------
if 'dynamic_catalog' not in st.session_state:
    st.session_state.dynamic_catalog = load_catalog()

if 'saved_projects' not in st.session_state:
    st.session_state.saved_projects = load_projects()

if 'project_groups' not in st.session_state:
    all_keys = list(st.session_state.dynamic_catalog.keys())
    if all_keys:
        first_type = all_keys[0]
        dims = st.session_state.dynamic_catalog[first_type]["dimensions"]
        thks = st.session_state.dynamic_catalog[first_type]["thicknesses"]
        st.session_state.project_groups = [
            {
                'sel_type': first_type,
                'sel_dim': dims[0] if dims else "",
                'sel_thk': thks[0] if thks else "",
                'cuts': [{'length': 100.0, 'qty': 1}]
            }
        ]
    else:
        st.session_state.project_groups = []

# -----------------------------------------------------------------------------
# אלגוריתם חיתוך אופטימלי (Bin Packing)
# -----------------------------------------------------------------------------
def calculate_optimal_cutting(cuts_list, max_capacity):
    all_pieces = []
    for cut in cuts_list:
        length = cut['length']
        qty = cut['qty']
        for _ in range(int(qty)):
            if length > max_capacity:
                return None, f"שגיאה: חתיכה באורך {length} ס\"מ ארוכה יותר מהמוט ({max_capacity} ס\"מ)."
            all_pieces.append(length)
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

# -----------------------------------------------------------------------------
# סרגל צדדי (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.title("🛠️ Elad Cohen Iron Art")
page = st.sidebar.radio("ניווט בין עמודים:", [
    "💰 עמוד מחירון ומלאי ברזל", 
    "📊 חישוב פרויקט שלם ושרטוטים",
    "🗄️ ארכיון פרויקטים שמורים"
])

st.sidebar.markdown("---")
st.sidebar.subheader("📈 מכפיל רווח מבוקש")
profit_multiplier = st.sidebar.slider("גרור לבחירת מכפיל עלות (X):", min_value=1.0, max_value=4.0, value=1.5, step=0.1)

st.sidebar.subheader("👷 עלויות עבודה ופועלים")
labor_count = st.sidebar.number_input("מספר עובדים בפרויקט:", min_value=0, value=1, step=1)
project_days = st.sidebar.number_input("כמות ימי עבודה מתוכננים:", min_value=0, value=1, step=1)
daily_wage = st.sidebar.number_input("שכר יומי לעובד (₪):", min_value=0.0, value=500.0, step=50.0)
total_labor_cost = labor_count * project_days * daily_wage

st.sidebar.subheader("🔥 עלויות חיצוניות")
oven_painting_cost = st.sidebar.number_input("עלות צביעה בתנור (₪):", min_value=0.0, value=0.0, step=50.0)

# =============================================================================
# עמוד 1: עריכת מחירון + הוספת/מחיקת מידות דינמית
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון ברזל דינמי")
    st.write("עדכן את המחירים ישירות בטבלאות למטה, או נהל את המידות והקטלוג בסקשן הצהוב בתחתית.")

    cat_keys = list(st.session_state.dynamic_catalog.keys())
    if cat_keys:
        tabs = st.tabs([f"🔳 {t}" for t in cat_keys])
        
        for idx, mat_type in enumerate(cat_keys):
            with tabs[idx]:
                info = st.session_state.dynamic_catalog[mat_type]
                st.subheader(f"מחירי מוטות עבור: {mat_type}")
                
                data_matrix = []
                for dim in info["dimensions"]:
                    row = {"מידות": dim}
                    for thk in info["thicknesses"]:
                        row[thk] = info.get("prices", {}).get(dim, {}).get(thk, 0.0)
                    data_matrix.append(row)
                    
                df = pd.DataFrame(data_matrix)
                edited_df = st.data_editor(df, key=f"editor_sheet_{mat_type}", use_container_width=True, hide_index=True, disabled=["מידות"])
                
                if "prices" not in info:
                    info["prices"] = {}
                for _, row in edited_df.iterrows():
                    dim = row["מידות"]
                    if dim not in info["prices"]:
                        info["prices"][dim] = {}
                    for thk in info["thicknesses"]:
                        info["prices"][dim][thk] = float(row[thk])

        # ---------------------------------------------------------------------
        # אזור ניהול: הוספה ומחיקה של מידות מהקטלוג
        # ---------------------------------------------------------------------
        st.markdown("<div class='admin-box'>", unsafe_allow_html=True)
        st.subheader("🛠️ ניהול והרחבת הקטלוג (הוספה ומחיקה של מידות ועוביים)")
        
        admin_c1, admin_c2, admin_c3 = st.columns(3)
        
        with admin_c1:
            target_type = st.selectbox("1. בחר סוג ברזל לניהול:", cat_keys, key="admin_target_type")
            
        with admin_c2:
            st.markdown("**➕ הוספת מידה או עובי חדשים:**")
            new_dim_input = st.text_input("הוסף מידה חדשה (למשל: 45x45 או 15 מ\"מ):", key="new_dim_text")
            if st.button("➕ הוסף מידה לרשימה"):
                if new_dim_input:
                    normalized_input = new_dim_input.replace('*', 'x').replace('X', 'x')
                    if normalized_input not in st.session_state.dynamic_catalog[target_type]["dimensions"]:
                        st.session_state.dynamic_catalog[target_type]["dimensions"].append(normalized_input)
                        st.session_state.dynamic_catalog[target_type]["dimensions"] = sort_dimensions_list(st.session_state.dynamic_catalog[target_type]["dimensions"])
                        st.success(f"המידה {normalized_input} התווספה ומוינה בהצלחה! לחץ על שמירה למטה.")
                        st.rerun()
                    else:
                        st.warning("מידה זו כבר קיימת בקטלוג.")
                    
            new_thk_input = st.text_input("הוסף עובי חדש (למשל: 4.0 מ\"מ):", key="new_thk_text")
            if st.button("➕ הוסף עובי לרשימה"):
                if new_thk_input and new_thk_input not in st.session_state.dynamic_catalog[target_type]["thicknesses"]:
                    st.session_state.dynamic_catalog[target_type]["thicknesses"].append(new_thk_input)
                    st.success(f"העובי {new_thk_input} התווסף זמנית! לחץ על שמירה למטה.")
                    st.rerun()
                elif new_thk_input:
                    st.warning("עובי זה כבר קיים בקטלוג.")
                    
        with admin_c3:
            st.markdown("**❌ מחיקת מידה קיימת (אם הוספת בטעות):**")
            current_dims = st.session_state.dynamic_catalog[target_type]["dimensions"]
            if current_dims:
                dim_to_delete = st.selectbox("בחר מידה להסרה מהטבלה:", current_dims, key="dim_to_delete_select")
                if st.button("❌ מחק מידה נבחרת", type="secondary"):
                    if dim_to_delete in st.session_state.dynamic_catalog[target_type]["dimensions"]:
                        st.session_state.dynamic_catalog[target_type]["dimensions"].remove(dim_to_delete)
                        if "prices" in st.session_state.dynamic_catalog[target_type] and dim_to_delete in st.session_state.dynamic_catalog[target_type]["prices"]:
                            del st.session_state.dynamic_catalog[target_type]["prices"][dim_to_delete]
                        st.success(f"המידה {dim_to_delete} הוסרה מהטבלה. לחץ על שמירה למטה כדי לעדכן בענן.")
                        st.rerun()
            else:
                st.write("אין מידות זמינות למחיקה.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("📁 שמור את כל השינויים, המידות והמיון לתמיד", type="primary"):
            with st.spinner("שומר את הנתונים המעודכנים בשרת GitHub..."):
                if save_to_github("saved_prices.json", st.session_state.dynamic_catalog, "🔄 עדכון מחירון ומבנה גדלים ממוין"):
                    st.success("🔥 כל המחירים, המידות והעוביים נשמרו, מוינו ועודכנו בהצלחה בענן!")
                else:
                    st.error("תקלה בתקשורת עם GitHub. ודא שהרשאות ה-repo מסומנות נכון.")
                        
# =============================================================================
# עמוד 2: מחשבון פרויקט + שמירה לארכיון
# =============================================================================
elif page == "📊 חישוב פרויקט שלם ושרטוטים":
    st.title("📊 חישוב פרויקט שלם ושרטוטים")
    
    project_name = st.text_input("✍️ הכנס שם לפרויקט זה (למשל: סורגים לחנה):", value="פרויקט ללא שם")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("➕ הוסף קבוצת ברזל חדשה לפרויקט"):
            all_keys = list(st.session_state.dynamic_catalog.keys())
            if all_keys:
                first_type = all_keys[0]
                dims = st.session_state.dynamic_catalog[first_type]["dimensions"]
                thks = st.session_state.dynamic_catalog[first_type]["thicknesses"]
                st.session_state.project_groups.append({
                    'sel_type': first_type,
                    'sel_dim': dims[0] if dims else "",
                    'sel_thk': thks[0] if thks else "",
                    'cuts': [{'length': 100.0, 'qty': 1}]
                })
                st.rerun()
    with col_g2:
        if st.button("❌ מחק קבוצת ברזל אחרונה") and len(st.session_state.project_groups) > 1:
            st.session_state.project_groups.pop()
            st.rerun()
            
    for g_idx, group in enumerate(st.session_state.project_groups):
        st.markdown(f"<div class='material-block'>", unsafe_allow_html=True)
        st.subheader(f"🧱 קבוצה #{g_idx + 1}")
        
        c1, c2, c3 = st.columns(3)
        all_types = list(st.session_state.dynamic_catalog.keys())
        
        if group['sel_type'] not in all_types:
            group['sel_type'] = all_types[0]
            
        selected_type = c1.selectbox("בחר סוג ברזל:", all_types, index=all_types.index(group['sel_type']), key=f"type_select_{g_idx}")
        if selected_type != group['sel_type']:
            group['sel_type'] = selected_type
            dims = st.session_state.dynamic_catalog[selected_type]["dimensions"]
            thks = st.session_state.dynamic_catalog[selected_type]["thicknesses"]
            group['sel_dim'] = dims[0] if dims else ""
            group['sel_thk'] = thks[0] if thks else ""
            st.rerun()

        available_dims = st.session_state.dynamic_catalog[group['sel_type']]["dimensions"]
        if group['sel_dim'] not in available_dims and available_dims:
            group['sel_dim'] = available_dims[0]
        
        if available_dims:
            selected_dim = c2.selectbox("בחר מידה:", available_dims, index=available_dims.index(group['sel_dim']), key=f"dim_select_{g_idx}")
            if selected_dim != group['sel_dim']:
                group['sel_dim'] = selected_dim
                st.rerun()

        available_thks = st.session_state.dynamic_catalog[group['sel_type']]["thicknesses"]
        if group['sel_thk'] not in available_thks and available_thks:
            group['sel_thk'] = available_thks[0]
            
        if available_thks:
            selected_thk = c3.selectbox("בחר עובי:", available_thks, index=available_thks.index(group['sel_thk']), key=f"thk_select_{g_idx}")
            group['sel_thk'] = selected_thk

        catalog_info = st.session_state.dynamic_catalog[group['sel_type']]
        current_price = catalog_info.get("prices", {}).get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
        
        st.write(f"**חומר שנבחר:** {group['sel_type']} | מידה: {group['sel_dim']} | עובי: {group['sel_thk']} (עלות למוט: ₪{current_price:.2f})")
        
        st.write("**📏 מידות חיתוך מבוקשות לחומר זה:**")
        sub_c1, sub_c2 = st.columns([1, 5])
        with sub_c1:
            if st.button(f"➕ הוסף מידה", key=f"add_cut_{g_idx}"):
                group['cuts'].append({'length': 50.0, 'qty': 1})
                st.rerun()
        with sub_c2:
            if st.button(f"❌ מחק מידה", key=f"del_cut_{g_idx}") and len(group['cuts']) > 1:
                group['cuts'].pop()
                st.rerun()
                
        for c_idx, cut in enumerate(group['cuts']):
            col_l, col_q = st.columns(2)
            with col_l:
                cut['length'] = st.number_input(f"אורך (ס\"מ) - חיתוך {c_idx+1}:", min_value=1.0, value=float(cut['length']), key=f"g_{g_idx}_l_{c_idx}")
            with col_q:
                cut['qty'] = st.number_input(f"כמות יחידות:", min_value=1, value=int(cut['qty']), key=f"g_{g_idx}_q_{c_idx}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    
    total_iron_cost = 0.0
    has_errors = False
    all_plans_results = []
    
    for g_idx, group in enumerate(st.session_state.project_groups):
        catalog_info = st.session_state.dynamic_catalog[group['sel_type']]
        price = catalog_info.get("prices", {}).get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
        
        bars_plan, err = calculate_optimal_cutting(group['cuts'], catalog_info['length'])
        if err:
            st.error(f"שגיאה בקבוצה #{g_idx+1}: {err}")
            has_errors = True
        else:
            bars_count = len(bars_plan)
            material_cost = bars_count * price
            total_iron_cost += material_cost
            all_plans_results.append({
                "type": group['sel_type'], "dim": group['sel_dim'], "thk": group['sel_thk'],
                "length": catalog_info['length'], "plan": bars_plan, "count": bars_count, "cost": material_cost, "cuts": group['cuts']
            })
            
    if not has_errors and st.session_state.project_groups:
        total_expenses = total_iron_cost + total_labor_cost + oven_painting_cost
        final_client_price = total_expenses * profit_multiplier
        
        net_profit = final_client_price - total_expenses
        gross_margin_percentage = (net_profit / final_client_price * 100) if final_client_price > 0 else 0.0
        
        st.success("🔥 החישוב הושלם בהצלחה!")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("עלות ברזל כוללת", f"₪ {total_iron_cost:,.2f}")
        with c2: st.metric("עלות עבודה", f"₪ {total_labor_cost:,.2f}")
        with c3: st.metric("צביעה בתנור", f"₪ {oven_painting_cost:,.2f}")
        with c4: st.metric("סך הוצאות פרויקט", f"₪ {total_expenses:,.2f}")
        
        st.subheader("💰 סיכום רווחים והצעה ללקוח")
        res_c1, res_c2, res_c3 = st.columns(3)
        with res_c1: st.metric(label="הצעת מחיר מומלצת (לפני מע\"מ)", value=f"₪ {final_client_price:,.2f}")
        with res_c2: st.metric(label="רווח נקי שלך (₪)", value=f"₪ {net_profit:,.2f}")
        with res_c3: st.metric(label="📈 אחוז רווח גולמי", value=f"{gross_margin_percentage:.1f}%")

        st.markdown("---")
        st.subheader("🪚 תוכנית חיתוך אופטימלית לביצוע בבית המלאכה")
        st.write("פעל לפי ההנחיות הבאות כדי לחתוך את המוטות במינימום פחת ובזבוז חומר:")
        
        for plan_info in all_plans_results:
            st.markdown(f"#### 🧱 {plan_info['type']} (מידה: {plan_info['dim']} | עובי: {plan_info['thk']})")
            st.write(f"סך הכל נדרשים **{plan_info['count']} מוטות** שלמים באורך {plan_info['length']} ס\"מ.")
            
            for b_num, bar in enumerate(plan_info['plan']):
                used_length = sum(bar)
                waste = plan_info['length'] - used_length
                cuts_formatted = " + ".join([f"{x}ס\"מ" for x in bar])
                st.markdown(
                    f"<div class='bar-display'>📏 <b>מוט #{b_num+1}:</b> לחתוך את החלקים הבאים: <b>{cuts_formatted}</b> | "
                    f"ניצול מוט: {used_length} ס\"מ (שארית לפחת: {waste} ס\"מ)</div>", 
                    unsafe_allow_html=True
                )

        st.markdown("---")
        if st.button("💾 שמור פרויקט זה לארכיון הקבוע", type="primary"):
            new_project = {
                "name": project_name,
                "iron_cost": total_iron_cost,
                "labor_cost": total_labor_cost,
                "paint_cost": oven_painting_cost,
                "total_expenses": total_expenses,
                "client_price": final_client_price,
                "profit_ils": net_profit,
                "margin_percent": gross_margin_percentage,
                "details": all_plans_results
            }
            st.session_state.saved_projects.append(new_project)
            with st.spinner("שומר פרויקט בארכיון הענן..."):
                if save_to_github("saved_projects.json", st.session_state.saved_projects, f"📂 הוספת פרויקט: {project_name}"):
                    st.success(f"🎉 הפרויקט '{project_name}' נשמר בהצלחה בארכיון!")
                else:
                    st.error("תקלה בשמירת הפרויקט בענן.")

# =============================================================================
# עמוד 3: ארכיון פרויקטים
# =============================================================================
else:
    st.title("🗄️ ארכיון פרויקטים שמורים")
    st.write("כאן שמורים כל הפרויקטים ההיסטוריים שחישבת בעבר. ניתן לראות פירוט מלא של חומרים וחיתוכים או למחוק.")

    if not st.session_state.saved_projects:
        st.info("ארכיון הפרויקטים ריק כרגע. שמור פרויקט מעמוד החישובים כדי לראות אותו כאן.")
    else:
        for p_idx, project in enumerate(st.session_state.saved_projects):
            st.markdown(f"<div class='project-card'>", unsafe_allow_html=True)
            
            head_c1, head_c2, head_c3, head_c4 = st.columns([2, 1, 1, 1])
            with head_c1: st.subheader(f"📂 {project.get('name', 'פרויקט ללא שם')}")
            with head_c2: st.metric("מחיר ללקוח", f"₪ {project.get('client_price', 0.0):,.2f}")
            with head_c3: st.metric("רווח נקי", f"₪ {project.get('profit_ils', 0.0):,.2f}")
            with head_c4: st.metric("📈 רווח גולמי", f"{project.get('margin_percent', 0.0):.1f}%")
                
            with st.expander("🔍 הצג פירוט חומרים וחיתוכים מלא לפרויקט זה:"):
                st.write(f"**סך הוצאות פרויקט:** ₪ {project.get('total_expenses', 0.0):,.2f} (ברזל: ₪ {project.get('iron_cost', 0.0):,.2f}, עבודה: ₪ {project.get('labor_cost', 0.0):,.2f}, צבע: ₪ {project.get('paint_cost', 0.0):,.2f})")
                st.write("**🧱 פירוט קבוצות החומרים והמוטות שחושבו בפרויקט זה:**")
                
                for det in project.get('details', []):
                    st.markdown(f"**• {det['type']}** | מידה: {det['dim']} | עובי: {det['thk']} | כמות מוטות נדרשת: **{det['count']}** (עלות חומר: ₪ {det['cost']:.2f})")
                    st.write(f"⚙️ תוכנית חיתוך מוטות באורך {det['length']} ס\"מ:")
                    for b_num, bar in enumerate(det['plan']):
                        st.write(f"   - מוט #{b_num+1}: חיתוך חתיכות באורכים של {bar} ס\"מ (נשאר שארית לפחת: {det['length'] - sum(bar)} ס\"מ)")
            
            if st.button("❌ מחק פרויקט", key=f"del_proj_{p_idx}"):
                deleted_name = st.session_state.saved_projects[p_idx].get('name', 'פרויקט')
                st.session_state.saved_projects.pop(p_idx)
                with st.spinner("מעדכן ארכיון בענן..."):
                    if save_to_github("saved_projects.json", st.session_state.saved_projects, f"🗑️ מחיקת פרויקט: {deleted_name}"):
                        st.success(f"הפרויקט '{deleted_name}' נמחק.")
                        st.rerun()
                    else:
                        st.error("תקלה בעדכון המחיקה בענן.")
                        
            st.markdown("</div>", unsafe_allow_html=True)
