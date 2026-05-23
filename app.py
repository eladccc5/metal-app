import streamlit as st
import pandas as pd

# -----------------------------------------------------------------------------
# הגדרות עיצוב ומרכוז טבלאות (CSS מיושר ותיקון סליידרים גלובלי)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="מערכת תמחור וחיתוך - Elad Cohen Iron Art", layout="wide")

st.markdown("""
    <style>
    /* כיווניות כללית מימין לשמאל */
    body, .main, div.stMarkdown, div[data-testid="stWidgetLabel"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* היפוך וכיווניות של טבלאות st.data_editor */
    div[data-testid="stDataEditor"] {
        direction: rtl !important;
    }
    .stDataFrame table {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* תיקון סליידרים גלובלי כדי שלא יתהפכו */
    div[data-baseweb="slider"] {
        direction: ltr !important;
    }
    
    /* עיצוב תיבות הקבוצה לפרויקט */
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
# חיבור קבוע ומאובטח ל-Google Sheets (פרסיסטנטיות מלאה)
# -----------------------------------------------------------------------------
# פונקציה פשוטה לחיבור דרך קישור ציבורי/עריכה פתוחה
def load_catalog_from_sheets():
    # קטלוג ברירת מחדל אם הגיליון ריק
    base_catalog = get_initial_catalog()
    
    # החלף את הקישור הבא בקישור של הגיליון שפתחת בגוגל (כולל ה-Editor)
    sheet_url = "YOUR_GOOGLE_SHEET_URL_HERE"
    
    if sheet_url == "YOUR_GOOGLE_SHEET_URL_HERE":
        return base_catalog

    try:
        # הפיכת קישור השיתוף לקישור הורדת CSV ישיר
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=', '/export?format=csv&gid=')
        if '/edit' in csv_url and '/export' not in csv_url:
            csv_url = csv_url.split('/edit')[0] + '/export?format=csv'
            
        df_sheet = pd.read_csv(csv_url)
        
        # בניית המחירון מתוך הגיליון בענן
        for _, row in df_sheet.iterrows():
            cat = str(row['Category'])
            dim = str(row['Dimension'])
            thk = str(row['Thickness'])
            price = float(row['Price'])
            
            if cat in base_catalog:
                if "prices" not in base_catalog[cat]:
                    base_catalog[cat]["prices"] = {}
                if dim not in base_catalog[cat]["prices"]:
                    base_catalog[cat]["prices"][dim] = {}
                base_catalog[cat]["prices"][dim][thk] = price
        return base_catalog
    except Exception as e:
        # במקרה של תקלה ברשת, המערכת תעלה עם ערכי ברירת המחדל ולא תקרוס
        return base_catalog

def save_catalog_to_sheets_trigger():
    # פונקציה שמזכירה לך שהשמירה מבוצעת ישירות אוטומטית או מנחה לעדכן
    pass

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

# -----------------------------------------------------------------------------
# אתחול Session State מהענן
# -----------------------------------------------------------------------------
if 'dynamic_catalog' not in st.session_state:
    st.session_state.dynamic_catalog = load_catalog_from_sheets()

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
# עמוד 1: מחירון דינמי לחלוטין 
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון ברזל דינמי")
    st.write("על מנת שהמחירים יישמרו לצמיתות גם כשהאתר הולך לישון, מומלץ להזין אותם ישירות בגיליון ה-Google Sheets שלך המקושר לענן.")
    
    sheet_url = "YOUR_GOOGLE_SHEET_URL_HERE"
    if sheet_url != "YOUR_GOOGLE_SHEET_URL_HERE":
        st.markdown(f"[🔗 לחץ כאן לפתיחת גיליון המחירים שלך בגוגל שייטס]({sheet_url})")

    st.markdown("---")

    cat_keys = list(st.session_state.dynamic_catalog.keys())
    if cat_keys:
        tabs = st.tabs([f"🔳 {t}" for t in cat_keys])
        
        for idx, mat_type in enumerate(cat_keys):
            with tabs[idx]:
                info = st.session_state.dynamic_catalog[mat_type]
                st.subheader(f"מחירי מוטות עבור: {mat_type} (אורך מוט בסיס: {info.get('length', 600)} ס\"מ)")
                
                data_matrix = []
                for dim in info["dimensions"]:
                    row = {"מידות": dim}
                    for thk in info["thicknesses"]:
                        row[thk] = info.get("prices", {}).get(dim, {}).get(thk, 0.0)
                    data_matrix.append(row)
                    
                df = pd.DataFrame(data_matrix)
                
                # תצוגת קריאה בלבד מהענן כדי למנוע דריסות בזמן שינה
                st.dataframe(df, use_container_width=True, hide_index=True)
                        
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
        if group.get('sel_type') not in all_types:
            group['sel_type'] = all_types[0]
            
        selected_type = c1.selectbox(
            "בחר סוג ברזל:", 
            all_types, 
            index=all_types.index(group['sel_type']), 
            key=f"type_select_{g_idx}"
        )
        
        if selected_type != group['sel_type']:
            group['sel_type'] = selected_type
            group['sel_dim'] = st.session_state.dynamic_catalog[selected_type]["dimensions"][0]
            group['sel_thk'] = st.session_state.dynamic_catalog[selected_type]["thicknesses"][0]
            st.rerun()

        available_dims = st.session_state.dynamic_catalog[group['sel_type']]["dimensions"]
        if group.get('sel_dim') not in available_dims:
            group['sel_dim'] = available_dims[0]
            
        selected_dim = c2.selectbox(
            "בחר מידה:", 
            available_dims, 
            index=available_dims.index(group['sel_dim']), 
            key=f"dim_select_{g_idx}"
        )
        
        if selected_dim != group['sel_dim']:
            group['sel_dim'] = selected_dim
            st.rerun()

        available_thks = st.session_state.dynamic_catalog[group['sel_type']]["thicknesses"]
        if group.get('sel_thk') not in available_thks:
            group['sel_thk'] = available_thks[0]
            
        selected_thk = c3.selectbox(
            "בחר עובי:", 
            available_thks, 
            index=available_thks.index(group['sel_thk']), 
            key=f"thk_select_{g_idx}"
        )
        group['sel_thk'] = selected_thk

        catalog_info = st.session_state.dynamic_catalog[group['sel_type']]
        current_price = catalog_info.get("prices", {}).get(group['sel_dim'], {}).get(group['sel_thk'], 0.0)
        
        st.write(f"**חומר שנבחר:** {group['sel_type']} | מידה: {group['sel_dim']} | עובי: {group['sel_thk']} (עלות למוט: ₪{current_price:.2f}, אורך: {catalog_info.get('length', 600)} ס\"מ)")
        
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
