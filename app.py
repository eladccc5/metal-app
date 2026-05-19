import json
import os
import base64
import io
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
    
    /* תיקון סליידרים גלובלי ואגרסיבי נגד היפוך וכיווניות */
    div[data-baseweb="slider"] {
        direction: ltr !important;
    }
    div[data-testid="stWidgetLabel"] {
        direction: rtl !important;
        text-align: right !important;
    }
    div[data-baseweb="slider"] div {
        direction: ltr !important;
    }
    
    /* עיצוב תיבות הקבוצה לפרויקט רב-חומרי */
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
# פונקציות שמירה וטעינה מקובץ מקומי (למניעת מחיקה ברענון)
# -----------------------------------------------------------------------------
CATALOG_FILE = "iron_catalog.json"

def load_catalog():
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    # קטלוג ברירת מחדל אם הקובץ לא קיים או פגום
    return [
        {"type": "פרופיל מרובע", "dimensions": "40*40", "thickness": "2 מ\"מ", "price": 110.0, "length": 600},
        {"type": "פרופיל מלבני", "dimensions": "50*25", "thickness": "2 מ\"מ", "price": 125.0, "length": 600},
        {"type": "שטוח", "dimensions": "3 ס\"מ", "thickness": "6 מ\"מ", "price": 55.0, "length": 300},
        {"type": "זווית", "dimensions": "30*30", "thickness": "3 מ\"מ", "price": 75.0, "length": 600},
        {"type": "עגול מלא", "dimensions": "-", "thickness": "12 מ\"מ", "price": 45.0, "length": 600},
        {"type": "מרובע מלא", "dimensions": "-", "thickness": "14 מ\"מ", "price": 50.0, "length": 600}
    ]

def save_catalog():
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.iron_catalog, f, ensure_ascii=False, indent=4)

# -----------------------------------------------------------------------------
# ניהול מצב גלובלי (Session State)
# -----------------------------------------------------------------------------
if 'iron_catalog' not in st.session_state:
    st.session_state.iron_catalog = load_catalog()

if 'project_groups' not in st.session_state:
    st.session_state.project_groups = [
        {
            'material_idx': 0,
            'cuts': [{'length': 90.0, 'qty': 5}]
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
st.sidebar.info(f"🎯 מכפיל רווח נבחר: **x{profit_multiplier:.1f}**")

st.sidebar.markdown("---")
st.sidebar.subheader("👷 עלויות עבודה ופועלים")
labor_count = st.sidebar.number_input("מספר עובדים בפרויקט:", min_value=0, value=1, step=1)
project_days = st.sidebar.number_input("כמות ימי עבודה מתוכננים:", min_value=0, value=1, step=1)
daily_wage = st.sidebar.number_input("שכר יומי לעובד אחד (₪):", min_value=0.0, value=500.0, step=50.0)

total_labor_cost = labor_count * project_days * daily_wage
st.sidebar.caption(f"💵 סך עלות עבודה מחושבת: ₪ {total_labor_cost:,.2f}")

st.sidebar.markdown("---")
st.sidebar.subheader("🔥 עלויות חיצוניות")
oven_painting_cost = st.sidebar.number_input("עלות ביצוע צביעה בתנור (₪):", min_value=0.0, value=0.0, step=50.0)

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 חיבור ל-AI (Gemini)")

api_key_from_secrets = st.secrets.get("GEMINI_API_KEY", None)
if api_key_from_secrets:
    genai.configure(api_key=api_key_from_secrets)
    st.sidebar.success("✅ מפתח ה-API מחובר אוטומטית!")
    active_key = api_key_from_secrets
else:
    custom_api_key = st.sidebar.text_input("הדבק מפתח API של גוגל כאן:", type="password")
    if custom_api_key:
        genai.configure(api_key=custom_api_key)
    active_key = custom_api_key

# =============================================================================
# עמוד 1: מחירון ומלאי ברזל (כולל אפשרות מחיקה דינמית)
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון חומרי גלם מפוצל")
    
    st.subheader("➕ הוספת ברזל חדש לקטלוג")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_type = st.selectbox("סוג ברזל:", ["פרופיל מרובע", "פרופיל מלבני", "שטוח", "זווית", "עגול מלא", "מרובע מלא"])
    with col2:
        if selected_type in ["פרופיל מרובע", "פרופיל מלבני", "זווית"]:
            dims = st.text_input("מידות (למשל 40*40):", value="40*40")
        elif selected_type == "שטוח":
            dims = st.text_input("מידת רוחב (למשל 3 ס\"מ):", value="3 ס\"מ")
        else:
            dims = "-"
    with col3:
        thickness = st.text_input("עובי הברזל:", value="2 מ\"מ" if "פרופיל" in selected_type else "6 מ\"מ")
    with col4:
        price = st.number_input("מחיר קנייה למוט (₪):", min_value=0.0, value=100.0, step=5.0)
        
    bar_length = 300 if selected_type == "שטוח" else 600
    
    if st.button("💾 שמור פריט למחירון (נשמר לצמיתות)", type="primary"):
        st.session_state.iron_catalog.append({
            "type": selected_type, "dimensions": dims, "thickness": thickness, "price": price, "length": bar_length
        })
        save_catalog()  # שמירה מיידית לקובץ JSON
        st.success("הברזל נוסף ונשמר בהצלחה!")
        st.rerun()

    st.markdown("---")
    st.subheader("🗄️ תצוגת מחירון ממוינת עם אפשרות מחיקה")
    
    t_square, t_rect, t_flat, t_angle, t_round_full, t_square_full = st.tabs([
        "🔳 פרופיל מרובע", "█ פרופיל מלבני", "➖ שטוח", "📐 זווית", "⚪ עגול מלא", "⬛ מרובע מלא"
    ])
    
    types_mapping = {
        "פרופיל מרובע": t_square, "פרופיל מלבני": t_rect, "שטוח": t_flat,
        "זווית": t_angle, "עגול מלא": t_round_full, "מרובע מלא": t_square_full
    }
    
    if st.session_state.iron_catalog:
        for iron_type, tab_obj in types_mapping.items():
            with tab_obj:
                # סינון פריטים השייכים לטאב הנוכחי תוך שמירת האינדקס המקורי שלהם לצורך מחיקה
                filtered_items = [(idx, item) for idx, item in enumerate(st.session_state.iron_catalog) if item['type'] == iron_type]
                
                if filtered_items:
                    for orig_idx, item in filtered_items:
                        # יצירת שורה מעוצבת עם כפתור מחיקה תואם
                        c_info, c_del = st.columns([6, 1])
                        with c_info:
                            st.info(f"📐 מידות: **{item['dimensions']}** |  🧱 עובי: **{item['thickness']}** |  💰 מחיר: **₪{item['price']:.2f}** |  📏 אורך: **{item['length']} ס\"מ**")
                        with c_del:
                            if st.button("🗑️ מחק", key=f"del_item_{orig_idx}", type="secondary"):
                                st.session_state.iron_catalog.pop(orig_idx)
                                save_catalog()  # עדכון קובץ ה-JSON לאחר מחיקה
                                st.success("הפריט נמחק!")
                                st.rerun()
                else:
                    st.info(f"אין כרגע פריטים מסוג {iron_type} במחירון.")

# =============================================================================
# עמוד 2: מחשבון פרויקט (מבנה קבוצות משודרג ורב-חומרי)
# =============================================================================
else:
    st.title("📊 חישוב פרויקט שלם ושרטוטים")
    
    if not st.session_state.iron_catalog:
        st.warning("⚠️ המחירון ריק! הגדר חומרים בעמוד המחירון תחילה.")
    else:
        material_labels = [f"{item['type']} | {item['dimensions']} | {item['thickness']}" for item in st.session_state.iron_catalog]
        
        tab_multi_manual, tab_ai_drawing = st.tabs(["✍️ בניית פרויקט רב-חומרי מורכב", "📸 ניתוח שרטוט כולל (AI)"])
        
        with tab_multi_manual:
            st.write("באפשרותך להגדיר מספר סוגי חומרים שונים לפרויקט, ותחת כל חומר להוסיף רשימת חיתוכים במידות שונות.")
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                if st.button("➕ הוסף קבוצת ברזל חדשה לפרויקט"):
                    st.session_state.project_groups.append({
                        'material_idx': 0,
                        'cuts': [{'length': 100.0, 'qty': 1}]
                    })
                    st.rerun()
            with col_g2:
                if st.button("❌ מחק קבוצת ברזל אחרונה") and len(st.session_state.project_groups) > 1:
                    st.session_state.project_groups.pop()
                    st.rerun()
            
            # ריצה על פני קבוצות הברזל השונות
            for g_idx, group in enumerate(st.session_state.project_groups):
                st.markdown(f"<div class='material-block'>", unsafe_allow_html=True)
                st.subheader(f"🧱 קבוצת חומר #{g_idx + 1}")
                
                group['material_idx'] = st.selectbox(
                    f"בחר סוג ברזל לקבוצה זו:",
                    range(len(material_labels)),
                    format_func=lambda x: material_labels[x],
                    key=f"group_mat_{g_idx}",
                    index=min(group['material_idx'], len(material_labels)-1)
                )
                
                st.write("**📏 מידות חיתוך מבוקשות לחומר זה:**")
                
                sub_c1, sub_c2 = st.columns([1, 5])
                with sub_c1:
                    if st.button(f"➕ הוסף מידת חיתוך", key=f"add_cut_{g_idx}"):
                        group['cuts'].append({'length': 50.0, 'qty': 1})
                        st.rerun()
                with sub_c2:
                    if st.button(f"❌ מחק מידה אחרונה", key=f"del_cut_{g_idx}") and len(group['cuts']) > 1:
                        group['cuts'].pop()
                        st.rerun()
                
                # יצירת שורות החיתוך הפנימיות בתוך הקבוצה
                for c_idx, cut in enumerate(group['cuts']):
                    col_l, col_q = st.columns(2)
                    with col_l:
                        cut['length'] = st.number_input(
                            f"אורך (ס\"מ) - חיתוך {c_idx+1}:",
                            min_value=1.0,
                            value=float(cut['length']),
                            key=f"g_{g_idx}_l_{c_idx}"
                        )
                    with col_q:
                        cut['qty'] = st.number_input(
                            f"כמות חתיכות:",
                            min_value=1,
                            value=int(cut['qty']),
                            key=f"g_{g_idx}_q_{c_idx}"
                        )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")
            if st.button("🚀 חשב ותמחר פרויקט שלם", type="primary", key="calc_group_project"):
                total_iron_cost = 0.0
                has_errors = False
                all_plans_results = []
                
                # חישוב אופטימיזציה נפרד לכל קבוצה
                for g_idx, group in enumerate(st.session_state.project_groups):
                    mat_data = st.session_state.iron_catalog[group['material_idx']]
                    bars_plan, err = calculate_optimal_cutting(group['cuts'], mat_data['length'])
                    
                    if err:
                        st.error(f"שגיאה בקבוצה #{g_idx+1} ({mat_data['type']}): {err}")
                        has_errors = True
                    else:
                        bars_count = len(bars_plan)
                        material_cost = bars_count * mat_data['price']
                        total_iron_cost += material_cost
                        all_plans_results.append({
                            "mat_info": mat_data,
                            "plan": bars_plan,
                            "count": bars_count,
                            "cost": material_cost,
                            "group_num": g_idx + 1
                        })
                
                if not has_errors:
                    total_expenses = total_iron_cost + total_labor_cost + oven_painting_cost
                    final_client_price = total_expenses * profit_multiplier
                    
                    st.success("🔥 חישוב הוצאות ומכפיל רווח לפרויקט מרובה חומרים הושלם!")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.metric("עלות ברזל כוללת", f"₪ {total_iron_cost:,.2f}")
                    with c2: st.metric("עלות פועלים ועבודה", f"₪ {total_labor_cost:,.2f}")
                    with c3: st.metric("עלות צביעה בתנור", f"₪ {oven_painting_cost:,.2f}")
                    with c4: st.metric("📊 סך כל ההוצאות (נטו)", f"₪ {total_expenses:,.2f}")
                    
                    st.markdown("---")
                    st.subheader("💰 הצעת מחיר סופית ללקוח")
                    st.metric(label="מחיר סופי מומלץ (לפני מע\"מ)", value=f"₪ {final_client_price:,.2f}", delta=f"רווח נקי שלך: ₪ {final_client_price - total_expenses:,.2f}")
                    
                    st.markdown("---")
                    st.subheader("📐 תוכניות חיתוך מפורטות לפרויקט:")
                    
                    for res in all_plans_results:
                        m_info = res['mat_info']
                        st.markdown(f"#### 🔨 קבוצה #{res['group_num']} - חומר: **{m_info['type']} | {m_info['dimensions']} | עובי {m_info['thickness']}** (נדרשים {res['count']} מוטות)")
                        
                        table_rows = []
                        for b_idx, bar in enumerate(res['plan']):
                            table_rows.append({
                                "מספר מוט": f"מוט #{b_idx + 1}",
                                "חיתוכים לבצוע מהמוט": "  |  ".join([f"{p} ס\"מ" for p in bar]),
                                "סה\"כ מנוצל": f"{sum(bar)} ס\"מ",
                                "פחת שנשאר בברזל": f"{m_info['length'] - sum(bar)} ס\"מ"
                            })
                        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        # --- טאב 2: ניתוח שרטוטים ---
        with tab_ai_drawing:
            st.subheader("📸 ניתוח שרטוט כולל מהשטח באמצעות AI")
            uploaded_file = st.file_uploader("העלה או צלם תמונת שרטוט:", type=["png", "jpg", "jpeg"], key="multi_ai_uploader")
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="השרטוט שהועלה לפענוח פרויקט", width=350)
                
                if st.button("🔍 הפעל ניתוח AI לשרטוט", type="primary", key="btn_ai_multi"):
                    if not active_key:
                        st.error("⚠️ אנא הגדר את מפתח ה-API ב-Advanced settings תחת ה-Secrets בשרת הדיפלוי.")
                    else:
                        with st.spinner("ה-AI מנתח את השרטוט ומחלץ את כל סוגי המידות..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                prompt = """
                                You are an expert metal welding estimator. Scan this uploaded image carefully.
                                Extract all cut pieces, lengths (in cm), and quantities.
                                Return the results strictly as a valid JSON object with no markdown wrappers or explanation text, using this format:
                                {"detected_items": [{"length_cm": 120.0, "quantity": 4}]}
                                """
                                response = model.generate_content([prompt, image])
                                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                                result_data = json.loads(clean_text)
                                
                                if "detected_items" in result_data and len(result_data["detected_items"]) > 0:
                                    st.success("🎉 השרטוט פוענח בהצלחה!")
                                    ai_cuts = [{'length': float(item['length_cm']), 'qty': int(item['quantity'])} for item in result_data['detected_items']]
                                    default_mat = st.session_state.iron_catalog[0]
                                    bars_plan, err = calculate_optimal_cutting(ai_cuts, default_mat['length'])
                                    
                                    if err:
                                        st.error(err)
                                    else:
                                        total_iron_cost = len(bars_plan) * default_mat['price']
                                        total_expenses = total_iron_cost + total_labor_cost + oven_painting_cost
                                        client_price = total_expenses * profit_multiplier
                                        
                                        d1, d2, d3 = st.columns(3)
                                        with d1: st.metric("מוטות נדרשים להזמנה", f"{len(bars_plan)} יח'")
                                        with d2: st.metric("סך הוצאות פרויקט", f"₪ {total_expenses:,.2f}")
                                        with d3: st.metric("מחיר סופי ללקוח", f"₪ {client_price:,.2f}")
                                            
                                        ai_table = []
                                        for b_idx, bar in enumerate(bars_plan):
                                            ai_table.append({
                                                "מספר מוט": f"מוט #{b_idx + 1}",
                                                "חיתוכים לבצוע מהמוט": "  |  ".join([f"{p} ס\"מ" for p in bar]),
                                                "שארית/פחת (ס\"מ)": f"{default_mat['length'] - sum(bar)} ס\"מ"
                                            })
                                        st.dataframe(pd.DataFrame(ai_table), use_container_width=True, hide_index=True)
                                else:
                                    st.error("המודל לא זיהה מידות ברורות בשרטוט.")
                            except Exception as e:
                                st.error(f"שגיאה בתקשורת עם ה-AI. פרטי השגיאה: {str(e)}")
