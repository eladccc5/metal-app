import streamlit as st
import pandas as pd

# (הגדרות ה-CSS וה-Session State נשארים כפי שהיו בקוד הקודם, 
# פשוט תשתמש בבלוק החדש עבור עמוד "חישוב פרויקט")

# =============================================================================
# עמוד 2: מחשבון פרויקט עם תפריטים מדורגים
# =============================================================================
else:
    st.title("📊 חישוב פרויקט שלם (בחירה מדורגת)")
    
    # פונקציית עזר למציאת מחיר
    def get_price(m_type, dim, thk):
        try:
            return st.session_state.dynamic_catalog[m_type]["prices"][dim][thk]
        except:
            return 0.0

    # ניהול קבוצות ברזל
    if st.button("➕ הוסף קבוצת ברזל"):
        st.session_state.project_groups.append({'cuts': [{'length': 100.0, 'qty': 1}]})
        
    for g_idx, group in enumerate(st.session_state.project_groups):
        st.markdown(f"### 🧱 קבוצה #{g_idx + 1}")
        
        # שלב 1: בחירת סוג ברזל
        m_types = list(st.session_state.dynamic_catalog.keys())
        selected_type = st.selectbox(f"בחר סוג ברזל:", m_types, key=f"type_{g_idx}")
        
        # שלב 2: בחירת מידה (מסונן לפי הסוג)
        dimensions = st.session_state.dynamic_catalog[selected_type]["dimensions"]
        selected_dim = st.selectbox(f"בחר מידה:", dimensions, key=f"dim_{g_idx}")
        
        # שלב 3: בחירת עובי (מסונן לפי המידה והסוג)
        thicknesses = st.session_state.dynamic_catalog[selected_type]["thicknesses"]
        selected_thk = st.selectbox(f"בחר עובי:", thicknesses, key=f"thk_{g_idx}")
        
        current_price = get_price(selected_type, selected_dim, selected_thk)
        st.info(f"מחיר ליחידה שנבחרה: ₪{current_price:.2f}")
        
        # חיתוכים... (המשך הלוגיקה הרגילה של הוספת חיתוכים וחישוב)
        # ... כאן תמשיך עם קוד ה-cuts כפי שהיה ...
