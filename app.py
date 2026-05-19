import json
import base64
import io
import streamlit as st
import pandas as pd
from PIL import Image
import google.generativeai as genai

# -----------------------------------------------------------------------------
# הגדרות עיצוב ומרכוז טבלאות (CSS להזרקה)
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
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ניהול מצב גלובלי (Session State)
# -----------------------------------------------------------------------------
if 'iron_catalog' not in st.session_state:
    st.session_state.iron_catalog = [
        {"type": "פרופיל מרובע", "dimensions": "40*40", "thickness": "2 מ\"מ", "price": 110.0, "length": 600},
        {"type": "פרופיל מלבני", "dimensions": "50*25", "thickness": "2 מ\"מ", "price": 125.0, "length": 600},
        {"type": "שטוח", "dimensions": "3 ס\"מ", "thickness": "6 מ\"מ", "price": 55.0, "length": 300},
        {"type": "זווית", "dimensions": "30*30", "thickness": "3 מ\"מ", "price": 75.0, "length": 600},
        {"type": "עגול מלא", "dimensions": "-", "thickness": "12 מ\"מ", "price": 45.0, "length": 600},
        {"type": "מרובע מלא", "dimensions": "-", "thickness": "14 מ\"מ", "price": 50.0, "length": 600}
    ]

# רשימת השורות הדינמית של פרויקט רב-חומרי
if 'project_items' not in st.session_state:
    st.session_state.project_items = [{'material_idx': 0, 'length': 90.0, 'qty': 5}]

# -----------------------------------------------------------------------------
# אלגוריתם חיתוך אופטימלי (Bin Packing)
# -----------------------------------------------------------------------------
def calculate_optimal_cutting(cuts_list, max_capacity):
    all_pieces = []
    for length, qty in cuts_list:
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
# סרגל צדדי (Sidebar) לניהול הגדרות ומפתחות
# -----------------------------------------------------------------------------
st.sidebar.title("🛠️ הגדרות מערכת")
page = st.sidebar.radio("ניווט בין עמודים:", ["💰 עמוד מחירון ומלאי ברזל", "📊 חישוב פרויקט שלם ושרטוטים"])

st.sidebar.markdown("---")
profit_margin = st.sidebar.slider("אחוז רווח מבוקש ללקוח (%):", min_value=0, max_value=200, value=50, step=5)

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 חיבור ל-AI (Gemini)")
custom_api_key = st.sidebar.text_input("הדבק מפתח API של גוגל כאן:", type="password", help="מאפשר להפעיל את מודל זיהוי השרטוטים ישירות מהנייד")

if custom_api_key:
    genai.configure(api_key=custom_api_key)

# =============================================================================
# עמוד 1: מחירון ומלאי ברזל (חלוקה ללשוניות לפי בקשתך)
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("📋 קטלוג ומחירון חומרי גלם מפוצל")
    st.write("הוסף חומרים חדשים ומיין אותם בקלות לפי סוג הברזל בלשוניות הייעודיות.")
    
    st.subheader("➕ הוספת ברזל חדש לקטלוג")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_type = st.selectbox("סוג ברזל:", ["פרופיל מרובע", "פרופיל מלבני", "שטוח", "זווית", "עגול מלא", "מרובע מלא"])
    
    with col2:
        if selected_type == "פרופיל מרובע":
            dims = st.text_input("מידות (למשל 30*30, 40*40):", value="40*40")
        elif selected_type == "פרופיל מלבני":
            dims = st.text_input("מידות (למשל 40*20, 50*25):", value="50*25")
        elif selected_type == "שטוח":
            dims = st.text_input("מידת רוחב (למשל 2 ס\"מ, 3 ס\"מ):", value="3 ס\"מ")
        elif selected_type == "זווית":
            dims = st.text_input("מידות זווית (למשל 30*30):", value="30*30")
        else:
            dims = "-"
            st.caption("למוט מלא יש רק מידת עובי")
            
    with col3:
        thickness = st.text_input("עובי הברזל:", value="2 מ\"מ" if "פרופיל" in selected_type else "6 מ\"מ")
        
    with col4:
        price = st.number_input("מחיר קנייה למוט (₪):", min_value=0.0, value=100.0, step=5.0)
        
    bar_length = 300 if selected_type == "שטוח" else 600
    
    if st.button("💾 שמור פריט למחירון", type="primary"):
        st.session_state.iron_catalog.append({
            "type": selected_type,
            "dimensions": dims,
            "thickness": thickness,
            "price": price,
            "length": bar_length
        })
        st.success("הברזל נוסף בהצלחה!")
        st.rerun()

    st.markdown("---")
    st.subheader("🗄️ תצוגת מחירון ממוינת לפי סוגי חומרים")
    
    # חלוקה ללשוניות לפי בקשתך המדויקת
    t_square, t_rect, t_flat, t_angle, t_round_full, t_square_full = st.tabs([
        "🔳 פרופיל מרובע", "█ פרופיל מלבני", "➖ שטוח", "📐 זווית", "⚪ עגול מלא", "⬛ מרובע מלא"
    ])
    
    types_mapping = {
        "פרופיל מרובע": t_square, "פרופיל מלבני": t_rect, "שטוח": t_flat,
        "זווית": t_angle, "עגול מלא": t_round_full, "מרובע מלא": t_square_full
    }
    
    df_global = pd.DataFrame(st.session_state.iron_catalog)
    
    for iron_type, tab_obj in types_mapping.items():
        with tab_obj:
            df_filtered = df_global[df_global['type'] == iron_type]
            if not df_filtered.empty:
                df_view = df_filtered.copy()
                df_view.columns = ["סוג ברזל", "מידות", "עובי ברזל", "מחיר קנייה", "אורך מוט (ס\"מ)"]
                st.dataframe(df_view, use_container_width=True, hide_index=False)
            else:
                st.info(f"אין כרגע פריטים מסוג {iron_type} במחירון.")
                
    st.markdown("---")
    st.subheader("🗑️ הסרת פריט מהמחירון הכללי")
    if st.session_state.iron_catalog:
        catalog_list = [f"{i}: {item['type']} {item['dimensions']} ({item['thickness']})" for i, item in enumerate(st.session_state.iron_catalog)]
        selected_to_delete = st.selectbox("בחר פריט להסרה:", range(len(catalog_list)), format_func=lambda x: catalog_list[x])
        if st.button("❌ מחק פריט נבחר"):
            st.session_state.iron_catalog.pop(selected_to_delete)
            st.success("הפריט הוסר.")
            st.rerun()

# =============================================================================
# עמוד 2: מחשבון פרויקט שלם (רב-חומרי + AI מתוקן)
# =============================================================================
else:
    st.title("📊 חישוב פרויקט שלם ורב-חומרי")
    
    if not st.session_state.iron_catalog:
        st.warning("⚠️ המחירון ריק! הגדר חומרים בעמוד המחירון תחילה.")
    else:
        # בניית רשימת האפשרויות לבחירה מתוך קטלוג הברזלים
        material_labels = [f"{item['type']} | {item['dimensions']} | {item['thickness']}" for item in st.session_state.iron_catalog]
        
        tab_multi_manual, tab_ai_drawing = st.tabs(["✍️ בניית פרויקט רב-חומרי", "📸 ניתוח שרטוט כולל (AI)"])
        
        # --- טאב 1: בניית פרויקט שלם רב-חומרי ---
        with tab_multi_manual:
            st.write("הוסף שורות, בחר עבור כל שורה את סוג הברזל הספציפי מהמחירון שלך, והזן את מידות החיתוך.")
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("➕ הוסף חיתוך/חומר לפרויקט"):
                    st.session_state.project_items.append({'material_idx': 0, 'length': 100.0, 'qty': 1})
            with col_act2:
                if st.button("❌ מחק שורה אחרונה") and len(st.session_state.project_items) > 1:
                    st.session_state.project_items.pop()
            
            # הדפסת השורות בצורה דינמית
            for idx, item in enumerate(st.session_state.project_items):
                r_col1, r_col2, r_col3 = st.columns([2, 1, 1])
                with r_col1:
                    mat_idx = st.selectbox(f"סוג ברזל שורה #{idx+1}:", range(len(material_labels)), format_func=lambda x: material_options[x] if 'material_options' in locals() else material_labels[x], key=f"mat_{idx}", index=min(item['material_idx'], len(material_labels)-1))
                with r_col2:
                    l_val = st.number_input(f"אורך (ס\"מ) #{idx+1}:", min_value=1.0, value=float(item['length']), key=f"len_{idx}")
                with r_col3:
                    q_val = st.number_input(f"כמות #{idx+1}:", min_value=1, value=int(item['qty']), key=f"qty_{idx}")
                    
                st.session_state.project_items[idx] = {'material_idx': mat_idx, 'length': l_val, 'qty': q_val}

            if st.button("🚀 חשב ותמחר פרויקט שלם", type="primary"):
                # קיבוץ כל הנתונים לפי סוג חומר
                grouped_cuts = {}
                for item in st.session_state.project_items:
                    m_idx = item['material_idx']
                    if m_idx not in grouped_cuts:
                        grouped_cuts[m_idx] = []
                    grouped_cuts[m_idx].append((item['length'], item['qty']))
                
                total_project_cost = 0.0
                has_errors = False
                all_plans_results = []
                
                # הרצת אלגוריתם חיתוך נפרד לכל חומר בפרויקט
                for m_idx, cuts in grouped_cuts.items():
                    mat_data = st.session_state.iron_catalog[m_idx]
                    bars_plan, err = calculate_optimal_cutting(cuts, mat_data['length'])
                    
                    if err:
                        st.error(f"עבור {mat_data['type']} {mat_data['dimensions']}: {err}")
                        has_errors = True
                    else:
                        bars_count = len(bars_plan)
                        material_cost = bars_count * mat_data['price']
                        total_project_cost += material_cost
                        all_plans_results.append({
                            "mat_info": mat_data,
                            "plan": bars_plan,
                            "count": bars_count,
                            "cost": material_cost
                        })
                
                if not has_errors:
                    final_client_price = total_project_cost * (1 + profit_margin / 100)
                    
                    st.success("🔥 חישוב פרויקט משולב הושלם בהצלחה!")
                    
                    # כרטיסיות סיכום כספיות לכלל הפרויקט
                    m1, m2 = st.columns(2)
                    with m1:
                        st.metric(label="עלות קניית חומרים כוללת (לפני מע\"מ)", value=f"₪ {total_project_cost:,.2f}")
                    with m2:
                        st.metric(label="מחיר סופי מומלץ ללקוח (כולל רווח)", value=f"₪ {final_client_price:,.2f}")
                    
                    # הצגת תוכניות העבודה השונות מופרדות
                    st.markdown("---")
                    st.subheader("📐 תוכניות חיתוך מפורטות לפי חומרים:")
                    
                    for res in all_plans_results:
                        m_info = res['mat_info']
                        st.markdown(f"#### 🔨 חומר: **{m_info['type']} | {m_info['dimensions']} | עובי {m_info['thickness']}** (נדרשים {res['count']} מוטות)")
                        
                        table_rows = []
                        for b_idx, bar in enumerate(res['plan']):
                            table_rows.append({
                                "מספר מוט": f"מוט #{b_idx + 1}",
                                "חיתוכים לבצוע מהמוט": "  |  ".join([f"{p} ס\"מ" for p in bar]),
                                "סה\"כ מנוצל": f"{sum(bar)} ס\"מ",
                                "פחת שנשאר": f"{m_info['length'] - sum(bar)} ס\"מ"
                            })
                        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        # --- טאב 2: ניתוח שרטוטים מתוקן ללא שגיאות סינטקס ---
        with tab_ai_drawing:
            st.subheader("📸 ניתוח שרטוט כולל מהשטח באמצעות AI")
            
            uploaded_file = st.file_uploader("העלה או צלם תמונת שרטוט:", type=["png", "jpg", "jpeg"], key="multi_ai_uploader")
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="השרטוט שהועלה לפענוח פרויקט", width=350)
                
                if st.button("🔍 הפעל ניתוח AI לשרטוט", type="primary", key="btn_ai_multi"):
                    if not custom_api_key:
                        st.error("⚠️ אנא הזן תחילה את מפתח ה-API שלך בסרגל הצד (Sidebar) כדי להפעיל את ה-AI.")
                    else:
                        with st.spinner("ה-AI מנתח את השרטוט ומחלץ את כל סוגי המידות..."):
                            try:
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                
                                prompt = """
                                You are an expert metal welding estimator. Scan this uploaded image carefully.
                                Extract all cut pieces, lengths (in cm), and quantities. 
                                Match them to general items.
                                Return the results strictly as a valid JSON object with no markdown wrappers or explanation text, using this format:
                                {"detected_items": [{"length_cm": 120.0, "quantity": 4}]}
                                """
                                
                                response = model.generate_content([prompt, image])
                                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                                result_data = json.loads(clean_text)
                                
                                if "detected_items" in result_data and len(result_data["detected_items"]) > 0:
                                    st.success("🎉 השרטוט פוענח בהצלחה!")
                                    
                                    # תיקון שורת הסינטקס שנשברה בצילום המסך הקודם
                                    ai_cuts = [(float(item['length_cm']), int(item['quantity'])) for item in result_data['detected_items']]
                                    
                                    # שימוש בחומר הראשון שנבחר כברירת מחדל לחישוב המהיר מהשרטוט
                                    default_mat = st.session_state.iron_catalog[0]
                                    bars_plan, err = calculate_optimal_cutting(ai_cuts, default_mat['length'])
                                    
                                    if err:
                                        st.error(err)
                                    else:
                                        total_bars = len(bars_plan)
                                        total_cost = total_bars * default_mat['price']
                                        client_price = total_cost * (1 + profit_margin / 100)
                                        
                                        # הצגת כרטיסיות
                                        d1, d2, d3 = st.columns(3)
                                        with d1:
                                            st.metric(label="מוטות נדרשים להזמנה", value=f"{total_bars} יח'")
                                        with d2:
                                            st.metric(label="עלות חומר (₪)", value=f"₪ {total_cost:,.2f}")
                                        with d3:
                                            st.metric(label="מחיר ללקוח (₪)", value=f"₪ {client_price:,.2f}")
                                            
                                        ai_table = []
                                        for b_idx, bar in enumerate(bars_plan):
                                            ai_table.append({
                                                "מספר מוט": f"מוט #{b_idx + 1}",
                                                "חיתוכים לבצוע מהשרטוט": "  |  ".join([f"{p} ס\"מ" for p in bar]),
                                                "שארית/פחת (ס\"מ)": f"{default_mat['length'] - sum(bar)} ס\"מ"
                                            })
                                        st.dataframe(pd.DataFrame(ai_table), use_container_width=True, hide_index=True)
                                else:
                                    st.error("המודל לא זיהה מידות ברורות בשרטוט, נסה לצלם מקרוב או ברור יותר.")
                            except Exception as e:
                                st.error(f"שגיאה בתקשורת עם ה-AI: {str(e)}")
