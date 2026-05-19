import json
import base64
import io
import streamlit as st
import pandas as pd
from PIL import Image

# -----------------------------------------------------------------------------
# הגדרות עיצוב ומרכוז טבלאות (CSS להזרקה)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="מחשבון תמחור וחיתוך ברזל", layout="wide")

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
# אלגוריתם חיתוך אופטימלי (Bin Packing / Cutting Stock)
# -----------------------------------------------------------------------------
def calculate_optimal_cutting(cuts_list, max_capacity):
    """
    מחשב את תוכנית החיתוך האופטימלית למוטות ברזל.
    cuts_list: רשימה של טאפלים (אורך_בסמ, כמות)
    max_capacity: אורך מוט מקסימלי (300 או 600 ס"מ)
    """
    # פירוק הרשימה לחתיכות בודדות
    all_pieces = []
    for length, qty in cuts_list:
        for _ in range(int(qty)):
            if length > max_capacity:
                # הגנה למקרה וחתיכה אחת ארוכה ממוט שלם
                return None, f"שגיאה: חתיכה באורך {length} ס\"מ ארוכה יותר מאורך מוט גלם מקסימלי ({max_capacity} ס\"מ)."
            all_pieces.append(length)
            
    # מיון מהגדול לקטן (קריטי לאופטימיזציה)
    all_pieces.sort(reverse=True)
    
    bars = [] # רשימה של מוטות, כל מוט הוא רשימת חיתוכים בתוכו
    
    for piece in all_pieces:
        placed = False
        # ניסיון להכניס למוט קיים שבו נשאר מספיק מקום
        for bar in bars:
            if sum(bar) + piece <= max_capacity:
                bar.append(piece)
                placed = True
                break
        # אם אין מקום באף מוט קיים, פותחים מוט חדש
        if not placed:
            bars.append([piece])
            
    return bars, None

# -----------------------------------------------------------------------------
# ממשק המשתמש הראשי
# -----------------------------------------------------------------------------
st.title("🛠️ מערכת תמחור ואופטימיזציית חיתוך - Elad Cohen Iron Art")

# יצירת טאבים לנוחיות העבודה בטלפון
tab_manual, tab_drawing = st.tabs(["📊 הזנת מידות וחיתוך אופטימלי", "📸 ניתוח שרטוט מהשטח"])

# חוקי הברזל של השוק לסוגי חומרים
MATERIAL_RULES = {
    "פרופיל מלבני (6 מטר)": 600,
    "פרופיל מרובע (6 מטר)": 600,
    "מוט מלא מרובע (6 מטר)": 600,
    "מוט מלא עגול (6 מטר)": 600,
    "ברזל שטוח / פלאח (3 מטר)": 300
}

with tab_manual:
    st.subheader("הזנת דרישות חיתוך ידנית")
    
    col1, col2 = st.columns(2)
    with col1:
        material_type = st.selectbox("בחר סוג חומר גלם:", list(MATERIAL_RULES.keys()))
        max_len = MATERIAL_RULES[material_type]
        st.caption(f"ℹ️ חומר זה מנוהל אוטומטית לפי אורך שוק של: {max_len} ס\"מ ({max_len/100} מטר)")
    
    with col2:
        price_per_bar = st.number_input("מחיר למוט גלם בודד (ש\"ח):", min_value=0.0, value=100.0, step=10.0)

    # טבלה דינמית להזנת החיתוכים
    st.write("📋 רשימת החיתוכים הנדרשת עבור הפרויקט:")
    if 'rows' not in st.session_state:
        st.session_state.rows = [{'length': 90.0, 'qty': 5}, {'length': 10.0, 'qty': 5}]
        
    # כפתורים להוספה ומחיקה של שורות
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("➕ הוסף חתיכה לרשימה"):
            st.session_state.rows.append({'length': 100.0, 'qty': 1})
    with c_btn2:
        if st.button("❌ מחק חתיכה אחרונה") and len(st.session_state.rows) > 1:
            st.session_state.rows.pop()

    # הצגת השדות להזנה
    formatted_cuts = []
    for i, row in enumerate(st.session_state.rows):
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            length_val = st.number_input(f"אורך חתיכה #{i+1} (בס\"מ):", min_value=1.0, value=float(row['length']), key=f"len_{i}")
        with r_col2:
            qty_val = st.number_input(f"כמות חתיכות #{i+1}:", min_value=1, value=int(row['qty']), key=f"qty_{i}")
        formatted_cuts.append((length_val, qty_val))
        st.session_state.rows[i] = {'length': length_val, 'qty': qty_val}

    if st.button("🚀 חשב תוכנית חיתוך ותמחור אופטימלית", type="primary"):
        bars_plan, error_msg = calculate_optimal_cutting(formatted_cuts, max_len)
        
        if error_msg:
            st.error(error_msg)
        else:
            st.success(f"🔥 החישוב האופטימלי הושלם! עליך להזמין סך הכל: **{len(bars_plan)} מוטות**.")
            
            # תצוגת סיכום כספי
            total_cost = len(bars_plan) * price_per_bar
            st.metric(label="סך הכל עלות חומר גלם משוערת", value=f"₪ {total_cost:,.2f}")
            
            # פירוט תוכנית החיתוך (איזה חתיכות לחתוך מכל מוט)
            st.subheader("📐 תוכנית עבודה מפורטת לחיתוך (BOM אופטימלי):")
            
            table_data = []
            for idx, bar in enumerate(bars_plan):
                cuts_text = " + ".join([f"{p}ס\"מ" for p in bar])
                used_space = sum(bar)
                waste = max_len - used_space
                table_data.append({
                    "מספר מוט": f"מוט #{idx + 1}",
                    "חיתוכים לבצוע מהמוט": cuts_text,
                    "סה\"כ מנוצל (ס\"מ)": f"{used_space} ס\"מ",
                    "פחת/שארית שנשארת (ס\"מ)": f"{waste} ס\"מ"
                })
                
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

with tab_drawing:
    st.subheader("ניתוח שרטוטים חכם באמצעות בינה מלאכותית")
    st.write("העלה תמונה או צילום של שרטוט ידני/טכני. המערכת תחלץ את המידות המדויקות בלבד ללא המצאות.")
    
    # פקודת ההנחיה הקשוחה ל-AI כדי למנוע ניתוחים קבועים
    ai_prompt = """
    You are an expert steel welder and structural estimator. Analyze this uploaded sketch/drawing.
    CRITICAL INSTRUCTION: Extract ONLY the explicit numbers and dimensions written on the image (in cm). 
    Do not guess dimensions, do not use boilerplate templates, and do not hallucinate standard parts.
    Every single cut item must be directly derived from a visible number on the paper.
    Return your result strictly as a clean JSON format matching this schema:
    {
       "detected_items": [
          {"material": "description", "length_cm": 120.0, "quantity": 4}
       ]
    }
    """
    
    uploaded_file = st.file_uploader("📸 צלם או העלה שרטוט מהגלריה:", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="השרטוט שהועלה", width=400)
        st.info("מערכת ה-AI מוכנה לניתוח השרטוט לפי בקשתך. (כאן יופעל הקישור ישירות למודל הראייה של Gemini/OpenAI לפי הגדרות המפתח שלך).")
