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
# פונקציית טעינת בסיס הנתונים ההתחלתי (על פי טבלאות האקסל המקוריות שלך)
# -----------------------------------------------------------------------------
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
        "ברזל עגול מלא": {
            "dimensions": ["8 מ\"מ", "10 מ\"מ", "12 מ\"מ", "14 מ\"מ", "16 מ\"מ", "18 מ\"מ", "20 מ\"מ"],
            "thicknesses": ["מלא"],
            "length": 600,
            "prices": {}
        },
        "ברזל מרובע מלא": {
            "dimensions": ["10x10", "12x12", "14x14", "16x16", "20x20", "25x25"],
            "thicknesses": ["מלא"],
            "length": 600,
            "prices": {}
        }
    }

# -----------------------------------------------------------------------------
# אתחול Session State (ניהול זיכרון חי ודינמי לחלוטין)
# -----------------------------------------------------------------------------
if 'dynamic_catalog' not in st.session_state:
    st.session_state.dynamic_catalog = get_initial_catalog()

if 'project_groups' not in st.session_state:
    st.session_state.project_groups = [
        {
            'sel_idx': 0,
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
# עמוד 1: מחירון דינמי לחלוטין (הוספה/הורדה של סוגים, מידות ועוביים)
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון ברזל דינמי")
    st.write("נהל את סוגי הברזל, המידות והעוביים בטבלאות מימין לשמאל. הזן מחיר בשקלים לכל מוט. פריט עם מחיר 0 לא יופיע במחשבון הפרויקטים.")

    # -------------------------------------------------------------------------
    # קטע ניהול: הוספה והסרה של סוגי ברזל (לשוניות), מידות ועוביים
    # -------------------------------------------------------------------------
    with st.expander("🛠️ כלי ניהול קטלוג מתקדם: הוספה/מחיקה של סוגי ברזל, מידות ועוביים"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ➕ הוספת רכיבים חדשים")
            new_type = st.text_input("שם סוג ברזל חדש (לשונית חדשה):", key="add_new_type")
            default_len = st.number_input("אורך מוט ברירת מחדל (ס\"מ):", min_value=100, value=600, step=100)
            if st.button("צור לשונית סוג ברזל חדשה"):
                if new_type and new_type not in st.session_state.dynamic_catalog:
                    st.session_state.dynamic_catalog[new_type] = {"dimensions": ["40x40"], "thicknesses": ["2.0 מ\"מ"], "length": default_len, "prices": {}}
                    st.success(f"הלשונית '{new_type}' נוצרה בהצלחה!")
                    st.rerun()
                    
            st.markdown("---")
            target_type = st.selectbox("בחר סוג ברזל להוספת שורה/עמודה:", list(st.session_state.dynamic_catalog.keys()), key="target_add")
            add_mode = st.radio("מה ברצונך להוסיף?", ["מידה חדשה (שורה)", "עובי ברזל חדש (עמודה)"])
            new_value = st.text_input("הזן את הערך (למשל: 70x70 או 4.0 מ\"מ):")
            if st.button("הוסף לקטלוג הקיים"):
                if new_value:
                    if add_mode == "מידה חדשה (שורה)" and new_value not in st.session_state.dynamic_catalog[target_type]["dimensions"]:
                        st.session_state.dynamic_catalog[target_type]["dimensions"].append(new_value)
                    elif add_mode == "עובי ברזל חדש (עמודה)" and new_value not in st.session_state.dynamic_catalog[target_type]["thicknesses"]:
                        st.session_state.dynamic_catalog[target_type]["thicknesses"].append(new_value)
                    st.success(f"הערך {new_value} נוסף בהצלחה ל-{target_type}!")
                    st.rerun()
                    
        with c2:
            st.markdown("### ❌ הסרת רכיבים קיימים")
            delete_type = st.selectbox("בחר לשונית סוג ברזל למחיקה:", ["-- בחר סוג --"] + list(st.session_state.dynamic_catalog.keys()))
            if st.button("מחק לשונית זו לצמיתות", type="secondary"):
                if delete_type in st.session_state.dynamic_catalog:
                    del st.session_state.dynamic_catalog[delete_type]
                    st.success(f"הלשונית '{delete_type}' נמחקה בהצלחה!")
                    st.rerun()
                    
            st.markdown("---")
            target_del_type = st.selectbox("בחר סוג ברזל למחיקת שורה/עמודה:", list(st.session_state.dynamic_catalog.keys()), key="target_del")
            del_mode = st.radio("מה ברצונך להסיר?", ["מידה (שורה)", "עובי (עמודה)"])
            
            if del_mode == "מידה (שורה)":
                val_to_del = st.selectbox("בחר מידה להסרה:", st.session_state.dynamic_catalog[target_del_type]["dimensions"])
                if st.button("מחק שורת מידה זו"):
                    st.session_state.dynamic_catalog[target_del_type]["dimensions"].remove(val_to_del)
                    st.success(f"המידה {val_to_del} הוסרה מהקטלוג!")
                    st.rerun()
            else:
                val_to_del = st.selectbox("בחר עובי להסרה:", st.session_state.dynamic_catalog[target_del_type]["thicknesses"])
                if st.button("מחק עמודת עובי זו"):
                    st.session_state.dynamic_catalog[target_del_type]["thicknesses"].remove(val_to_del)
                    st.success(f"העובי {val_to_del} הוסר מהקטלוג!")
                    st.rerun()

    st.markdown("---")

    # -------------------------------------------------------------------------
    # הצגת הלשוניות והטבלאות מימין לשמאל
    # -------------------------------------------------------------------------
    cat_keys = list(st.session_state.dynamic_catalog.keys())
    if cat_keys:
        tabs = st.tabs([f"🔳 {t}" for t in cat_keys])
        
        for idx, mat_type in enumerate(cat_keys):
            with tabs[idx]:
                info = st.session_state.dynamic_catalog[mat_type]
                st.subheader(f"מחירי מוטות עבור: {mat_type} (אורך מוט בסיס: {info.get('length', 600)} ס\"מ)")
                
                # בניית המטריצה לתצוגה
                data_matrix = []
                for dim in info["dimensions"]:
                    row = {"מידות": dim}
                    for thk in info["thicknesses"]:
                        row[thk] = info.get("prices", {}).get(dim, {}).get(thk, 0.0)
                    data_matrix.append(row)
                    
                df = pd.DataFrame(data_matrix)
                
                # עורך הטבלה בגירסה מיושרת לימין
                edited_df = st.data_editor(
                    df,
                    key=f"editor_dyn_{mat_type}",
                    use_container_width=True,
                    hide_index=True,
                    disabled=["מידות"]
                )
                
                # סנכרון מיידי של המחירים שהוקלדו לתוך ה-Session State
                changes_made = False
                if "prices" not in info:
                    info["prices"] = {}
                    
                for _, row in edited_df.iterrows():
                    dim = row["מידות"]
                    if dim not in info["prices"]:
                        info["prices"][dim] = {}
                    for thk in info["thicknesses"]:
                        new_val = float(row[thk])
                        if info["prices"][dim].get(thk, 0.0) != new_val:
                            info["prices"][dim][thk] = new_val
                            changes_made = True
                            
                if changes_made:
                    st.toast("💾 השינויים והמחירים החדשים עודכנו במערכת!", icon="💾")
    else:
        st.info("הקטלוג ריק לחלוטין. פתח את תיבת הניהול למעלה כדי להוסיף סוגי ברזל ראשונים.")

# =============================================================================
# עמוד 2: מחשבון פרויקט - מסונכרן לחלוטין עם המחירון החי
# =============================================================================
else:
    st.title("📊 חישוב פרויקט שלם ושרטוטים")
    
    # שליפת כל הברזלים שהוזן להם מחיר תקין מהמחירון הדינמי בזמן אמת
    available_materials = []
    for m_type, info in st.session_state.dynamic_catalog.items():
        prices = info.get("prices", {})
        for dim in info["dimensions"]:
            for thk in info["thicknesses"]:
                price = prices.get(dim, {}).get(thk, 0.0)
                if price > 0:  # רק מה שיש לו מחיר יופיע כאופציה לבחירה
                    available_materials.append({
                        "label": f"{m_type} | מידה: {dim} | עובי: {thk} (עלות: ₪{price:.2f})",
                        "type": m_type, "dim": dim, "thk": thk, "price": price, "length": info.get("length", 600)
                    })
                    
    if not available_materials:
        st.warning("⚠️ לא נמצאו פריטים מתומחרים במחירון! כנס לעמוד המחירון והזן מחיר (הגדול מ-0) לפריטים שאתה צריך לפרויקט.")
    else:
        material_labels = [m["label"] for m in available_materials]
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if st.button("➕ הוסף קבוצת ברזל חדשה לפרויקט"):
                st.session_state.project_groups.append({
                    'sel_idx': 0,
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
            
            # תיבת הבחירה המעודכנת והמסונכרנת אוטומטית לחלוטין
            selected_label_idx = st.selectbox(
                f"בחר חומר מהמחירון הדינמי:",
                range(len(material_labels)),
                format_func=lambda x: material_labels[x],
                key=f"group_mat_{g_idx}",
                index=min(group.get('sel_idx', 0), len(material_labels)-1)
            )
            group['sel_idx'] = selected_label_idx
            
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
                mat_data = available_materials[group['sel_idx']]
                bars_plan, err = calculate_optimal_cutting(group['cuts'], mat_data['length'])
                
                if err:
                    st.error(f"שגיאה בקבוצה #{g_idx+1}: {err}")
                    has_errors = True
                else:
                    bars_count = len(bars_plan)
                    material_cost = bars_count * mat_data['price']
                    total_iron_cost += material_cost
                    all_plans_results.append({
                        "mat_info": mat_data, "plan": bars_plan, "count": bars_count, "cost": material_cost, "group_num": g_idx + 1
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
                
                st.markdown("---")
                st.subheader("📐 תוכניות חיתוך מפורטות (מימין לשמאל):")
                for res in all_plans_results:
                    m_info = res['mat_info']
                    st.markdown(f"#### 🔨 קבוצה #{res['group_num']} - {m_info['type']} | {m_info['dim']} | עובי {m_info['thk']} ({res['count']} מוטות)")
                    table_rows = []
                    for b_idx, bar in enumerate(res['plan']):
                        table_rows.append({
                            "מספר מוט": f"מוט #{b_idx + 1}",
                            "חיתוכים לבצוע מהמוט": "  |  ".join([f"{p} ס\"מ" for p in bar]),
                            "סה\"כ מנוצל": f"{sum(bar)} ס\"מ",
                            "פחת שנשאר בברזל": f"{m_info['length'] - sum(bar)} ס\"מ"
                        })
                    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
