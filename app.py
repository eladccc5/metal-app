import json
import os
import streamlit as st
import pandas as pd
from PIL import Image
import google.generativeai as genai

# -----------------------------------------------------------------------------
# הגדרות עיצוב ומרכוז טבלאות (CSS מיושר ותיקון סליידרים גלובלי)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="מערכת תמחור וחיתוך - Elad Cohen Iron Art", layout="wide")

st.markdown("""
    <style>
    body {
        direction: rtl;
        text-align: right;
    }
    .stDataFrame table {
        direction: rtl !important;
        text-align: center !important;
    }
    .stDataFrame th, .stDataFrame td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    div[data-testid="stDataFrameCustomRowHeaderCell"] {
        text-align: center !important;
    }
    div.stMarkdown {
        direction: rtl;
        text-align: right;
    }
    
    /* תיקון סליידרים גלובלי */
    div[data-baseweb="slider"] {
        direction: ltr !important;
    }
    div[data-testid="stWidgetLabel"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* עיצוב תיבות הקבוצה לפרויקט */
    .material-block {
        border: 2px solid #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        background-color: #fafbfc;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# פונקציות שמירה וטעינה של המטריצה לקובץ מקומי
# -----------------------------------------------------------------------------
MATRIX_FILE = "iron_matrix_catalog.json"

# הגדרת המבנה הקבוע של המידות והעוביים לפי צילומי המסך שלך
CATALOG_STRUCTURE = {
    "פרופיל מרובע": {
        "dimensions": ["20x20", "25x25", "30x30", "40x40", "50x50", "60x60", "80x80", "100x100", "120x120"],
        "thicknesses": ["1.5 מ\"מ", "2.0 מ\"מ", "2.5 מ\"מ", "3.0 מ\"מ"],
        "length": 600
    },
    "פרופיל מלבני": {
        "dimensions": ["40x20", "50x20", "50x25", "60x40", "80x40", "100x40", "100x50", "150x50"],
        "thicknesses": ["1.5 מ\"מ", "2.0 מ\"מ", "2.5 מ\"מ", "3.0 מ\"מ"],
        "length": 600
    },
    "שטוח": {
        "dimensions": ["20 מ\"מ", "25 מ\"מ", "30 מ\"מ", "35 מ\"מ", "40 מ\"מ", "50 מ\"מ", "60 מ\"מ", "80 מ\"מ", "100 מ\"מ"],
        "thicknesses": ["3 מ\"מ", "5 מ\"מ", "8 מ\"מ", "10 מ\"מ", "12 מ\"מ"],
        "length": 300
    },
    "זווית": {
        "dimensions": ["20x20", "25x25", "30x30", "40x40", "50x50"],
        "thicknesses": ["3 מ\"מ", "4 מ\"מ", "5 מ\"מ"],
        "length": 600
    }
}

def load_matrix_data():
    # יצירת מבנה ריק כברירת מחדל
    default_data = {}
    for mat_type, info in CATALOG_STRUCTURE.items():
        default_data[mat_type] = {}
        for dim in info["dimensions"]:
            default_data[mat_type][dim] = {}
            for thk in info["thicknesses"]:
                # מחיר ברירת מחדל 0 (לא קיים במלאי/במחירון)
                default_data[mat_type][dim][thk] = 0.0
                
    if os.path.exists(MATRIX_FILE):
        try:
            with open(MATRIX_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # מיזוג עם הדיפלוט כדי למנוע שגיאות אם המבנה משתנה
                for mat_type in default_data:
                    if mat_type in loaded:
                        for dim in default_data[mat_type]:
                            if dim in loaded[mat_type]:
                                for thk in default_data[mat_type][dim]:
                                    if thk in loaded[mat_type][dim]:
                                        default_data[mat_type][dim][thk] = float(loaded[mat_type][dim][thk])
                return default_data
        except:
            pass
    return default_data

def save_matrix_data():
    with open(MATRIX_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.matrix_catalog, f, ensure_ascii=False, indent=4)

# -----------------------------------------------------------------------------
# אתחול Session State
# -----------------------------------------------------------------------------
if 'matrix_catalog' not in st.session_state:
    st.session_state.matrix_catalog = load_matrix_data()

if 'project_groups' not in st.session_state:
    st.session_state.project_groups = [
        {
            'type': "פרופיל מרובע",
            'dim': "40x40",
            'thk': "2.0 מ\"מ",
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

api_key_from_secrets = st.secrets.get("GEMINI_API_KEY", None)
if api_key_from_secrets:
    genai.configure(api_key=api_key_from_secrets)
    active_key = api_key_from_secrets
else:
    active_key = None

# =============================================================================
# עמוד 1: מחירון רשת מובנה (בדיוק כמו האקסל שלך)
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון חומרי גלם ברשת חכמה")
    st.write("הזן את המחירים (למוט שלם) ישירות בתוך הטבלאות למטה. פריט עם מחיר 0.0 ייחשב כלא קיים במלאי.")

    tabs = st.tabs([f"🔳 {t}" for t in CATALOG_STRUCTURE.keys()])
    
    for idx, (mat_type, info) in enumerate(CATALOG_STRUCTURE.items()):
        with tabs[idx]:
            st.subheader(f"מחירי מוטות עבור: {mat_type} (אורך מוט: {info['length']} ס\"מ)")
            
            # בניית ה-DataFrame הנוכחי מתוך ה-session_state
            data_matrix = []
            for dim in info["dimensions"]:
                row = {"מידות (מ\"מ)": dim}
                for thk in info["thicknesses"]:
                    row[thk] = st.session_state.matrix_catalog[mat_type][dim][thk]
                data_matrix.append(row)
                
            df = pd.DataFrame(data_matrix)
            
            # תצוגת טבלה ניתנת לעריכה (st.data_editor)
            edited_df = st.data_editor(
                df,
                key=f"editor_{mat_type}",
                use_container_width=True,
                hide_index=True,
                disabled=["מידות (מ\"מ)"]
            )
            
            # עדכון השינויים חזרה לתוך ה-session_state ושמירה לקובץ
            changes_made = False
            for _, row in edited_df.iterrows():
                dim = row["מידות (מ\"מ)"]
                for thk in info["thicknesses"]:
                    new_val = float(row[thk])
                    if st.session_state.matrix_catalog[mat_type][dim][thk] != new_val:
                        st.session_state.matrix_catalog[mat_type][dim][thk] = new_val
                        changes_made = True
                        
            if changes_made:
                save_matrix_data()
                st.toast("💾 השינויים נשמרו אוטומטית!", icon="💾")

# =============================================================================
# עמוד 2: מחשבון פרויקט המבוסס על הרשת החדשה
# =============================================================================
else:
    st.title("📊 חישוב פרויקט שלם ושרטוטים")
    
    # איסוף כל החומרים שיש להם מחיר מעל 0 מהקטלוג החדש
    available_materials = []
    for m_type, dims_data in st.session_state.matrix_catalog.items():
        for dim, thks_data in dims_data.items():
            for thk, price in thks_data.items():
                if price > 0:
                    available_materials.append({
                        "label": f"{m_type} | {dim} | {thk} (₪{price})",
                        "type": m_type, "dim": dim, "thk": thk, "price": price, "length": CATALOG_STRUCTURE[m_type]["length"]
                    })
                    
    if not available_materials:
        st.warning("⚠️ לא הגדרת אף מחיר בקטלוג! כנס לעמוד המחירון והזן מחירים בטבלאות כדי שהם יופיעו כאן.")
    else:
        material_labels = [m["label"] for m in available_materials]
        
        tab_multi_manual, tab_ai_drawing = st.tabs(["✍️ בניית פרויקט רב-חומרי מורכב", "📸 ניתוח שרטוט כולל (AI)"])
        
        with tab_multi_manual:
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
                
                selected_label_idx = st.selectbox(
                    f"בחר חומר מהמחירון:",
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
                    st.subheader("📐 תוכניות חיתוך מפורטות:")
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

        # --- טאב 2: ניתוח שרטוטים על בסיס המחירון החדש ---
        with tab_ai_drawing:
            st.subheader("📸 ניתוח שרטוט כולל מהשטח באמצעות AI")
            uploaded_file = st.file_uploader("העלה או צלם תמונת שרטוט:", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="השרטוט שהועלה", width=350)
                if st.button("🔍 הפעל ניתוח AI לשרטוט"):
                    st.info("מנתח את השרטוט ומבצע התאמה אוטומטית לחומר הראשון במחירון הקיים...")
