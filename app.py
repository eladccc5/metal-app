import streamlit as st
import pandas as pd
import json
import requests
import base64

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
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# הגדרות חיבור קשיח ל-GitHub לצורך שמירה קבועה - מעודכן עבורך!
# -----------------------------------------------------------------------------
GITHUB_USERNAME = "eladccc5"             
GITHUB_REPO = "metal-app"                
GITHUB_TOKEN ="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"    

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
        }
    }

# פונקציה שטוענת את המחירים ישירות מ-GitHub בזמן עלייה
def load_catalog():
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/saved_prices.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content_b64 = res.json().get("content")
            content_str = base64.b64decode(content_b64).decode("utf-8")
            return json.loads(content_str)
    except:
        pass
    return get_initial_catalog()

# פונקציה שמעדכנת את ה-GitHub שלך בלחיצת כפתור מהאתר
def save_catalog_to_github(catalog_data):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/saved_prices.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    content_str = json.dumps(catalog_data, ensure_ascii=False, indent=4)
    content_bytes = content_str.encode("utf-8")
    content_b64 = base64.b64encode(content_bytes).decode("utf-8")
    
    res = requests.get(url, headers=headers)
    sha = None
    if res.status_code == 200:
        sha = res.json().get("sha")
        
    data = {
        "message": "🔄 עדכון מחירון אוטומטי מהאפליקציה",
        "content": content_b64,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
        
    put_res = requests.put(url, headers=headers, json=data)
    return put_res.status_code in [200, 201]

# -----------------------------------------------------------------------------
# אתחול הנתונים באפליקציה
# -----------------------------------------------------------------------------
if 'dynamic_catalog' not in st.session_state:
    st.session_state.dynamic_catalog = load_catalog()

if 'project_groups' not in st.session_state:
    first_type = list(st.session_state.dynamic_catalog.keys())[0]
    st.session_state.project_groups = [
        {
            'sel_type': first_type,
            'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0],
            'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0],
            'cuts': [{'length': 100.0, 'qty': 1}]
        }
    ]

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
st.sidebar.title("🛠️ הגדרות ותמחור פרויקט")
page = st.sidebar.radio("ניווט בין עמודים:", ["💰 עמוד מחירון ומלאי ברזל", "📊 חישוב פרויקט שלם ושרטוטים"])

st.sidebar.markdown("---")
st.sidebar.subheader("📈 מכפיל רווח מבוקש")
profit_multiplier = st.sidebar.slider("גרור לבחירת מכפיל עלות (X):", min_value=1.0, max_value=4.0, value=1.5, step=0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("👷 עלויות עבודה ופועלים")
labor_count = st.sidebar.number_input("מספר עובדים בפרויקט:", min_value=0, value=1, step=1)
project_days = st.sidebar.number_input("כמות ימי עבודה מתוכננים:", min_value=0, value=1, step=1)
daily_wage = st.sidebar.number_input("שכר יומי לעובד (₪):", min_value=0.0, value=500.0, step=50.0)
total_labor_cost = labor_count * project_days * daily_wage

st.sidebar.markdown("---")
st.sidebar.subheader("🔥 עלויות חיצוניות")
oven_painting_cost = st.sidebar.number_input("עלות צביעה בתנור (₪):", min_value=0.0, value=0.0, step=50.0)

# =============================================================================
# עמוד 1: עריכת מחירון ישירות באפליקציה + שמירה קבועה ל-GitHub
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון ברזל דינמי")
    st.write("עדכן את המחירים ישירות בטבלאות למטה. בסיום, לחץ על כפתור השמירה בתחתית העמוד כדי לשמור אותם לתמיד בשרת.")

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
                
                edited_df = st.data_editor(
                    df,
                    key=f"editor_sheet_{mat_type}",
                    use_container_width=True,
                    hide_index=True,
                    disabled=["מידות"]
                )
                
                if "prices" not in info:
                    info["prices"] = {}
                for _, row in edited_df.iterrows():
                    dim = row["מידות"]
                    if dim not in info["prices"]:
                        info["prices"][dim] = {}
                    for thk in info["thicknesses"]:
                        info["prices"][dim][thk] = float(row[thk])

        st.markdown("---")
        st.subheader("💾 שמירה קבועה לענן")
        
        if st.button("📁 שמור את כל המחירים החדשים לתמיד", type="primary"):
            with st.spinner("שומר את הנתונים בשרת GitHub..."):
                success = save_catalog_to_github(st.session_state.dynamic_catalog)
                if success:
                    st.success("🔥 כל המחירים נשמרו בהצלחה בתוך השרת! הם לא יימחקו יותר לעולם.")
                else:
                    st.error("תקלה בתקשורת עם GitHub. ודא שהרשאות ה-repo מסומנות נכון.")
                        
# =============================================================================
# עמוד 2: מחשבון פרויקט
# =============================================================================
else:
    st.title("📊 חישוב פרויקט שלם ושרטוטים")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("➕ הוסף קבוצת ברזל חדשה לפרויקט"):
            first_type = list(st.session_state.dynamic_catalog.keys())[0]
            st.session_state.project_groups.append({
                'sel_type': first_type,
                'sel_dim': st.session_state.dynamic_catalog[first_type]["dimensions"][0],
                'sel_thk': st.session_state.dynamic_catalog[first_type]["thicknesses"][0],
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
        
        selected_type = c1.selectbox("בחר סוג ברזל:", all_types, index=all_types.index(group['sel_type']), key=f"type_select_{g_idx}")
        if selected_type != group['sel_type']:
            group['sel_type'] = selected_type
            group['sel_dim'] = st.session_state.dynamic_catalog[selected_type]["dimensions"][0]
            group['sel_thk'] = st.session_state.dynamic_catalog[selected_type]["thicknesses"][0]
            st.rerun()

        available_dims = st.session_state.dynamic_catalog[group['sel_type']]["dimensions"]
        selected_dim = c2.selectbox("בחר מידה:", available_dims, index=available_dims.index(group['sel_dim']), key=f"dim_select_{g_idx}")
        if selected_dim != group['sel_dim']:
            group['sel_dim'] = selected_dim
            st.rerun()

        available_thks = st.session_state.dynamic_catalog[group['sel_type']]["thicknesses"]
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
    if st.button("🚀 חשב ותמחר פרויקט שלם", type="primary"):
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
                    "length": catalog_info['length'], "plan": bars_plan, "count": bars_count, "cost": material_cost, "group_num": g_idx + 1
                })
                
        if not has_errors:
            total_expenses = total_iron_cost + total_labor_cost + oven_painting_cost
            final_client_price = total_expenses * profit_multiplier
            
            st.success("🔥 החישוב הושלם בהצלחה!")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("עלות ברזל כוללת", f"₪ {total_iron_cost:,.2f}")
            with c2: st.metric("עלות עבודה", f"₪ {total_labor_cost:,.2f}")
            with c3: st.metric("צביעה בתנור", f"₪ {oven_painting_cost:,.2f}")
            with c4: st.metric("סך הוצאות פרויקט", f"₪ {total_expenses:,.2f}")
            
            st.subheader("💰 מחיר סופי ללקוח (לפני מע\"מ)")
            st.metric(label="הצעת מחיר מומלצת", value=f"₪ {final_client_price:,.2f}", delta=f"רווח נקי שלך: ₪ {final_client_price - total_expenses:,.2f}")
