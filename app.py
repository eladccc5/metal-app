import json
import base64
import io
import streamlit as st
import pandas as pd
from PIL import Image
import google.generativeai as genai

# -----------------------------------------------------------------------------
# הגדרות עיצוב ומרכוז טבלאות (CSS)
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
# מפתח API מובנה עבור מודל ה-AI
# -----------------------------------------------------------------------------
# הגדרת מפתח ה-API של Gemini ישירות בקוד כדי שלא יקרוס
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# -----------------------------------------------------------------------------
# ניהול מצב גלובלי (Session State) לקטלוג הברזל הדינמי של אלעד
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

# -----------------------------------------------------------------------------
# אלגוריתם חיתוך אופטימלי (Bin Packing)
# -----------------------------------------------------------------------------
def calculate_optimal_cutting(cuts_list, max_capacity):
    all_pieces = []
    for length, qty in cuts_list:
        for _ in range(int(qty)):
            if length > max_capacity:
                return None, f"שגיאה: חתיכה באורך {length} ס\"מ ארוכה יותר מאורך מוט גלם מקסימלי ({max_capacity} ס\"מ)."
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
# ניווט בין עמודים (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.title("🗂️ תפריט ניווט")
page = st.sidebar.radio("עבור לעמוד:", ["💰 עמוד מחירון ומלאי ברזל", "📊 חישוב חיתוך ותמחור פרויקט"])

st.sidebar.markdown("---")
st.sidebar.subheader("📈 הגדרות פרויקט")
profit_margin = st.sidebar.slider("אחוז רווח מבוקש ללקוח (%):", min_value=0, max_value=200, value=50, step=5)

# =============================================================================
# עמוד 1: מחירון ומלאי ברזל (דינמי ומותאם אישית)
# =============================================================================
if page == "💰 עמוד מחירון ומלאי ברזל":
    st.title("💰 עמוד מחירון ומלאי ברזל")
    st.write("כאן אתה מנהל וממיין את כל קטלוג הברזלים שאתה עובד איתם בשוטף ומעדכן את מחירי הקנייה שלהם.")
    
    st.subheader("➕ הוספת סוג ברזל חדש לקטלוג")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_type = st.selectbox("סוג ברזל:", ["פרופיל מרובע", "פרופיל מלבני", "שטוח", "זווית", "עגול מלא", "מרובע מלא"])
    
    with col2:
        # חוקי מידות משתנים בהתאם לסוג הברזל שנבחר כפי שביקשת
        if selected_type == "פרופיל מרובע":
            dims = st.text_input("מידות (למשל 30*30, 40*40):", value="40*40")
        elif selected_type == "פרופיל מלבני":
            dims = st.text_input("מידות (למשל 40*20, 50*25):", value="50*25")
        elif selected_type == "שטוח":
            dims = st.text_input("מידת רוחב (למשל 2 ס\"מ, 3 ס\"מ):", value="3 ס\"מ")
        elif selected_type == "זווית":
            dims = st.text_input("מידות זווית (למשל 30*30):", value="30*30")
        else: # עגול מלא או מרובע מלא - אין מידות רוחב/אורך אלא רק עובי
            dims = "-"
            st.caption("למוט מלא יש רק מידת עובי (בשדה הבא)")
            
    with col3:
        thickness = st.text_input("עובי הברזל:", value="2 מ\"מ" if "פרופיל" in selected_type else "6 מ\"מ")
        
    with col4:
        price = st.number_input("מחיר קנייה למוט מהספק (₪):", min_value=0.0, value=100.0, step=5.0)
        
    # קביעת אורך המוט אוטומטית לפי חוקי השוק (שטוח 3 מטר, כל השאר 6 מטר)
    bar_length = 300 if selected_type == "שטוח" else 600
    
    if st.button("💾 שמור ברזל זה למחירון", type="primary"):
        st.session_state.iron_catalog.append({
            "type": selected_type,
            "dimensions": dims,
            "thickness": thickness,
            "price": price,
            "length": bar_length
        })
        st.success(f"הפריט {selected_type} נוסף בהצלחה למחירון!")
        st.rerun()

    st.markdown("---")
    st.subheader("🗄️ טבלת מלאי ומחירון הברזל שלך")
    
    if st.session_state.iron_catalog:
        df_catalog = pd.DataFrame(st.session_state.iron_catalog)
        df_catalog.columns = ["סוג ברזל", "מידות (בלי עובי)", "עובי ברזל", "מחיר קנייה למוט", "אורך מוט (ס\"מ)"]
        
        # הצגת הטבלה המלאה כשהיא ממורכזת ויפה
        st.dataframe(df_catalog, use_container_width=True, hide_index=False)
        
        # בחירה ומחיקה של שורות מהמחירון בצורה פשוטה
        row_to_delete = st.number_input("להסרת פריט, הזן את מספר השורה השמאלי שלו בטבלה:", min_value=0, max_value=len(st.session_state.iron_catalog)-1, value=len(st.session_state.iron_catalog)-1, step=1)
        if st.button("❌ מחק שורה נבחרת מהמחירון"):
            st.session_state.iron_catalog.pop(int(row_to_delete))
            st.success("השורה נמחקה מהקטלוג.")
            st.rerun()
    else:
        st.info("המחירון ריק כרגע. הוסף חומרים למעלה כדי להתחיל לעבוד.")

# =============================================================================
# עמוד 2: מחשבון חיתוך ותמחור פרויקטים (כולל הזנה ידנית או AI פעיל)
# =============================================================================
else:
    st.title("📊 חישוב חיתוך ותמחור פרויקט")
    
    if not st.session_state.iron_catalog:
        st.warning("⚠️ לא הגדרת אף ברזל במחירון! עבור לעמוד 'מחירון ומלאי ברזל' כדי להוסיף חומרים קודם.")
    else:
        # רשימת הברזלים הזמינים מהמחירון הדינמי שהמשתמש בנה בעמוד 1
        material_options = [f"{item['type']} | מידה: {item['dimensions']} | עובי: {item['thickness']} (קנייה: ₪{item['price']})" for item in st.session_state.iron_catalog]
        selected_material_idx = st.selectbox("בחר את סוג הברזל לפרויקט הנוכחי (מתוך המחירון הדינמי שלך):", range(len(material_options)), format_func=lambda x: material_options[x])
        
        chosen_item = st.session_state.iron_catalog[selected_material_idx]
        max_len = chosen_item["length"]
        cost_per_bar = chosen_item["price"]
        
        tab_manual, tab_drawing = st.tabs(["✍️ הזנה ידנית של מידות", "📸 ניתוח שרטוט אמיתי מהשטח"])
        
        # --- טאב הזנה ידנית ---
        with tab_manual:
            if 'calc_rows' not in st.session_state:
                st.session_state.calc_rows = [{'length': 90.0, 'qty': 5}]
                
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("➕ הוסף שורת מידה לפרויקט"):
                    st.session_state.calc_rows.append({'length': 100.0, 'qty': 1})
            with col_b2:
                if st.button("❌ מחק שורה אחרונה") and len(st.session_state.calc_rows) > 1:
                    st.session_state.calc_rows.pop()
                    
            formatted_cuts = []
            for i, row in enumerate(st.session_state.calc_rows):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    l_val = st.number_input(f"אורך חיתוך #{i+1} (בס\"מ):", min_value=1.0, value=float(row['length']), key=f"p_len_{i}")
                with r_col2:
                    q_val = st.number_input(f"כמות חתיכות #{i+1}:", min_value=1, value=int(row['qty']), key=f"p_qty_{i}")
                formatted_cuts.append((l_val, q_val))
                st.session_state.calc_rows[i] = {'length': l_val, 'qty': q_val}
                
            if st.button("🚀 חשב תוכנית חיתוך ותמחור סופית", type="primary", key="btn_calc_manual"):
                bars_plan, error_msg = calculate_optimal_cutting(formatted_cuts, max_len)
                
                if error_msg:
                    st.error(error_msg)
                else:
                    total_bars = len(bars_plan)
                    total_cost = total_bars * cost_per_bar
                    client_price = total_cost * (1 + profit_margin / 100)
                    
                    st.success(f"🔥 חישוב אופטימלי הושלם! נדרשים סך הכל: **{total_bars} מוטות** של חומר גלם.")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric(label="כמות מוטות להזמנה", value=f"{total_bars} יח'")
                    with c2:
                        st.metric(label="עלות קנייה חומר (לפני מע\"מ)", value=f"₪ {total_cost:,.2f}")
                    with c3:
                        st.metric(label="מחיר מומלץ ללקוח (כולל רווח)", value=f"₪ {client_price:,.2f}")
                        
                    st.subheader("📐 תוכנית עבודה מפורטת לחיתוך מהמוטות:")
                    table_data = []
                    for idx, bar in enumerate(bars_plan):
                        table_data.append({
                            "מספר מוט": f"מוט #{idx + 1}",
                            "חיתוכים לבצוע מהמוט": "  |  ".join([f"{p} ס\"מ" for p in bar]),
                            "סה\"כ מנוצל": f"{sum(bar)} ס\"מ",
                            "פחת/שארית שנשארת": f"{max_len - sum(bar)} ס\"מ"
                        })
                    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        # --- טאב ניתוח שרטוטים (AI פעיל ללא דמו קבוע) ---
        with tab_drawing:
            st.subheader("📸 העלאת שרטוט לניתוח בינה מלאכותית")
            st.write("העלה צילום של שרטוט ידני מהשטח. המערכת תפעיל את מודל הראייה ותחלץ ממנו את המידות לפרויקט.")
            
            uploaded_file = st.file_uploader("בחר או צלם תמונת שרטוט:", type=["png", "jpg", "jpeg"], key="ai_uploader")
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="השרטוט שהועלה לפענוח", width=350)
                
                if st.button("🔍 הפעל ניתוח AI אמיתי לשרטוט", type="primary"):
                    if not GOOGLE_API_KEY:
                        st.error("שגיאה: לא מוגדר מפתח API במערכת. יש להוסיף את ה-API Key תחת Advanced settings ב-Streamlit Cloud.")
                    else:
                        with st.spinner("ה-AI קורא ומנתח את השרטוט ומחלץ את המידות..."):
                            try:
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                
                                prompt = """
                                You are an expert iron welding estimator. Scan this uploaded image carefully.
                                Identify all explicit numerical dimensions that represent cut pieces or required metal lengths (usually marked in cm or numbers on lines).
                                Extract them into a valid JSON list. Do not use generic examples, only read the exact text and drawings in front of you.
                                Return your result strictly in this valid JSON format, with no extra text, explanations or markdown block wrappers:
                                {"detected_items": [{"length_cm": 150.0, "quantity": 2}]}
                                """
                                
                                response = model.generate_content([prompt, image])
                                
                                # ניקוי תגיות קוד אם חזרו מהמודל
                                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                                result_data = json.loads(clean_text)
                                
                                if "detected_items" in result_data and len(result_data["detected_items"]) > 0:
                                    st.success("🎉 השרטוט פוענח בהצלחה על ידי ה-AI!")
                                    
                                    ai_cuts = [(float(item['length_cm']), int(item['quantity'])) for item in result_data['detected_items']]
                                    
                                    # הרצת האלגוריתם על המידות האמיתיות שחולצו מהתמונה
                                    bars_plan, error_msg = calculate_optimal_cutting(ai_cuts, max_len)
                                    
                                    if error_msg:
                                        st.error(error_msg)
                                    else:
                                        total_bars = len(bars_plan)
                                        total_cost = total_bars * cost_per_bar
                                        client_price = total_cost * (1 + profit_margin / 100)
                                        
                                        d1, d2, d3 = st.columns(3)
                                        with d1:
                                            st.metric(label="מוטות נדרשים מהשרטוט", value=f"{total_bars} יח'")
                                        with d2:
                                            st.metric(label="עלות חומר גלם (₪)", value=f"₪ {total_cost:,.2f}")
                                        with d3:
                                            st.metric(label="מחיר מומלץ ללקוח", value=f"₪ {client_price:,.2f}")
                                            
                                        ai_table_data = []
                                        for idx, bar in enumerate(bars_plan):
                                            ai_table_data.append({
                                                "מספר מוט": f"מוט #{idx + 1}",
                                                "חיתוכים לבצוע (מהשרטוט)": "  |  ".join([f"{p} ס\"מ" for p in bar]),
                                                "פחת מוגדר (ס\"מ)": f"{max_len - sum(bar)} ס\"מ"
                                            })
                                        st.dataframe(pd.DataFrame(ai_table_data), use_container_width=True, hide_index=True)
                                else:
                                    st.error("ה-AI לא מצא מידות ברורות בשרטוט זה. ודא שהכתב קריא והתמונה מוארת היטב.")
                                    
                            except Exception as e:
                                st.error(f"אירעה שגיאה בפענוח השרטוט: {str(e)}. ודא שקובץ התמונה תקין וקריא.")
