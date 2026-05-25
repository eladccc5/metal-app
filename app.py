import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import requests
from xhtml2pdf import pisa  # ספרייה להפקת PDF אמיתי

# הגדרות עמוד ותצוגה בעברית (יישור לימין)
st.set_page_config(page_title="Elad Cohen Iron Art - תמחור", layout="wide")
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 90%; }
    div[data-testid="stMarkdownContainer"] p { text-align: right; direction: rtl; }
    div[data-testid="stDataFrame"] { direction: rtl; }
    .stButton>button { width: 100%; font-weight: bold; }
    h1, h2, h3, h4, h5, h6 { text-align: right; direction: rtl; }
    label { text-align: right !important; width: 100%; direction: rtl; }
    div[data-baseweb="select"] { direction: rtl; text-align: right; }
    div[data-baseweb="input"] { direction: rtl; text-align: right; }
    .stAlert p { text-align: right !important; direction: rtl !important; }
    </style>
""", unsafe_allow_html=True)

# קבצי בסיס נתונים מקומיים בשרת
PRICES_FILE = "saved_prices.json"
PROJECTS_FILE = "saved_projects.json"

# טעינת מחירון ברירת מחדל או שמור
def load_prices():
    default_prices = {
        "פרופיל מרובע 20x20": 20.0,
        "פרופיל מרובע 30x30": 30.0,
        "פרופיל מרובע 40x40": 40.0,
        "פרופיל מרובע 50x50": 55.0,
        "פרופיל מלבן 40x20": 35.0,
        "פרופיל מלבן 60x40": 50.0,
        "פרופיל מלבן 80x40": 65.0,
        "צינור עגול 1 צול": 25.0,
        "צינור עגול 1.5 צול": 38.0,
        "צינור עגול 2 צול": 48.0,
        "ברזל שטוח 30x5": 12.0,
        "ברזל שטוח 40x6": 18.0,
        "פח שחור 1.5 מ\"מ (למ\"ר)": 110.0,
        "פח שחור 2 מ\"מ (למ\"ר)": 140.0,
        "פח שחור 3 מ\"מ (למ\"ר)": 200.0,
        "פח מרוג 3 מ\"מ (למ\"ר)": 240.0,
        "אלקטרודות זיקה (חבילה)": 90.0,
        "דיסקים חיתוך/השחזה (יחידה)": 8.0,
        "צבע יסוד + עליון (ליטר)": 75.0,
    }
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_prices
    return default_prices

def save_prices(prices):
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=4)

# טעינת ושמירת ארכיון פרויקטים שמורים
def load_projects():
    if os.path.exists(PROJECTS_FILE):
        try:
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_projects(projects):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=4)

prices = load_prices()
projects_archive = load_projects()

# ניהול מצב דינמי (Session State) לטובת רשימת החיתוכים הנוכחית
if "cuts" not in st.session_state:
    st.session_state.cuts = []
if "other_costs" not in st.session_state:
    st.session_state.other_costs = {"צביעה": 0.0, "הובלה": 0.0, "התקנה": 0.0, "פרזול/אחר": 0.0}
if "labor_cost" not in st.session_state:
    st.session_state.labor_cost = 0.0
if "labor_details" not in st.session_state:
    st.session_state.labor_details = {"workers": 1, "days": 1, "daily_rate": 800.0}
if "markup" not in st.session_state:
    st.session_state.markup = 1.3
if "client_info" not in st.session_state:
    st.session_state.client_info = {"name": "", "phone": "", "address": "", "date": datetime.today().strftime('%Y/%m/%d')}

# תפריט ניווט עליון/צידי
st.sidebar.title("🎨 Elad Cohen Iron Art")
menu = st.sidebar.radio("ניווט במערכת:", ["מחשבון חיתוך ותמחור", "עדכון מחירון חומרי גלם", "ארכיון פרויקטים שמורים"])

# ==========================================
# מסך 2: עדכון מחירון
# ==========================================
if menu == "עדכון מחירון חומרי גלם":
    st.title("⚙️ עדכון מחירון חומרי גלם ומתכלים")
    st.write("המחירים המוזנים כאן משפיעים ישירות על חישובי העלויות במחשבון הראשי.")
    
    updated_prices = {}
    categories = {
        "📊 פרופילי ברזל וצינורות (מחיר למטר רץ)": [k for k in prices.keys() if "פרופיל" in k or "צינור" in k or "שטוח" in k],
        "🧱 פחים ולוחות (מחיר למטר מרובע)": [k for k in prices.keys() if "פח" in k],
        "🧪 חומרים מתכלים וצבע": [k for k in prices.keys() if "אלקטרודות" in k or "דיסקים" in k or "צבע" in k]
    }
    
    for cat_name, items in categories.items():
        st.subheader(cat_name)
        cols = st.columns(2)
        for idx, item in enumerate(items):
            with cols[idx % 2]:
                updated_prices[item] = st.number_input(f"מחיר עבור {item} (₪):", min_value=0.0, value=float(prices[item]), step=1.0, key=f"price_{item}")
                
    # הוספת חומר חדש דינמית
    st.markdown("---")
    st.subheader("➕ הוספת חומר גלם חדש למחירון")
    new_cols = st.columns(3)
    with new_cols[0]:
        new_name = st.text_input("שם החומר החדש:")
    with new_cols[1]:
        new_price = st.number_input("מחיר בשקלים:", min_value=0.0, value=0.0)
    with new_cols[2]:
        st.write("<br>", unsafe_allow_html=True)
        add_btn = st.button("הוסף למחירון")
        
    if add_btn and new_name:
        if new_name in prices:
            st.warning("החומר כבר קיים במחירון!")
        else:
            prices[new_name] = new_price
            save_prices(prices)
            st.success(f"החומר '{new_name}' נוסף בהצלחה!")
            st.rerun()

    if st.button("💾 שמור את כל שינויי המחירים", type="primary"):
        for k, v in updated_prices.items():
            prices[k] = v
        save_prices(prices)
        st.success("המחירון העדכני נשמר בהצלחה בשרת!")

# ==========================================
# מסך 3: ארכיון פרויקטים שמורים
# ==========================================
elif menu == "ארכיון פרויקטים שמורים":
    st.title("📂 ארכיון הפרויקטים השמורים של Elad Cohen Iron Art")
    st.write("כאן שמורים כל הפרויקטים שסנכרנת מול הענן.")
    
    if not projects_archive:
        st.info("אין עדיין פרויקטים שמורים בארכיון. תוכל לשמור פרויקטים דרך עמוד המחשבון הראשי.")
    else:
        project_names = list(projects_archive.keys())
        selected_project_name = st.selectbox("📁 בחר פרויקט לצפייה מהארכיון:", [""] + project_names)
        
        if selected_project_name and selected_project_name != "":
            proj = projects_archive[selected_project_name]
            
            st.markdown("---")
            st.header(f"🗂️ פרויקט: {selected_project_name}")
            
            # פרטי לקוח
            c_info = proj.get("client_info", {"name": "-", "phone": "-", "address": "-", "date": "-"})
            cols_c = st.columns(4)
            cols_c[0].metric("שם הלקוח", c_info.get("name", "-"))
            cols_c[1].metric("טלפון", c_info.get("phone", "-"))
            cols_c[2].metric("כתובת הפרויקט", c_info.get("address", "-"))
            cols_c[3].metric("תאריך שמירה", c_info.get("date", "-"))
            
            # סיכום כספי מהיר
            st.markdown("### 💰 סיכום עלויות והצעה")
            cols_metrics = st.columns(4)
            cols_metrics[0].metric("הצעת מחיר סופית ללקוח", f"₪{proj.get('final_price', 0):,.2f}")
            cols_metrics[1].metric("עלות חומרי גלם (ברזל)", f"₪{proj.get('total_material_cost', 0):,.2f}")
            cols_metrics[2].metric("עלות עבודה", f"₪{proj.get('labor_cost', 0):,.2f}")
            cols_metrics[3].metric("מכפיל רווח (Markup)", f"x{proj.get('markup', 1.3)}")
            
            # פירוט הוצאות ספקים וחוץ
            st.markdown("### 🚚 הוצאות וספקי חוץ:")
            o_costs = proj.get("other_costs", {})
            st.write(f"🎨 **צביעה:** ₪{o_costs.get('צביעה', 0):,.2f} | 🚛 **הובלה:** ₪{o_costs.get('הובלה', 0):,.2f} | 🔨 **התקנה:** ₪{o_costs.get('התקנה', 0):,.2f} | 🔩 **פרזול/אחר:** ₪{o_costs.get('פרזול/אחר', 0):,.2f}")
            
            # פירוט חומרים וחיתוכים שנשמרו בפרויקט זה
            st.markdown("### 🪵 חומרים וחיתוכים שנשמרו:")
            saved_cuts = proj.get("cuts", [])
            if saved_cuts:
                df_saved_cuts = pd.DataFrame(saved_cuts)
                df_saved_cuts.columns = ["סוג החומר", "אורך חיתוך (ס"מ)", "כמות יחידות", "קבוצת שיוך"]
                st.dataframe(df_saved_cuts, use_container_width=True)
            
            # כפתור מחיקה מהארכיון
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🗑️ מחק את פרויקט '{selected_project_name}' לצמיתות", type="secondary"):
                del projects_archive[selected_project_name]
                save_projects(projects_archive)
                st.success(f"הפרויקט '{selected_project_name}' נמחק מהארכיון.")
                st.rerun()

# ==========================================
# מסך 1: מחשבון ראשי + אופטימיזציה
# ==========================================
else:
    st.title("⚒️ מערכת תמחור חכמה ואופטימיזציית חיתוך מוטות ברזל")
    st.write("הזן את רשימת חיתוכי הברזל הנדרשים לפרויקט. המערכת תבצע אופטימיזציה לפחת מינימלי, תחשב את כמות המוטות הארוכים (6 מטר) לקנייה, ותפיק תמחור מלא כולל עבודה, ספקים ורווח.")
    
    # חלוקה לטאבים לנוחות עבודה
    tab1, tab2, tab3 = st.tabs(["📐 הזנת חומרים וחיתוכים", "💵 הוצאות, עבודה ותמחור סופי", "📋 פרטי לקוח והפקה"])
    
    with tab1:
        st.subheader("🔹 הוספת סדרת חיתוכים חדשה")
        input_cols = st.columns(4)
        
        with input_cols[0]:
            material_type = st.selectbox("בחר סוג חומר גלם:", list(prices.keys()))
        with input_cols[1]:
            cut_length = st.number_input("אורך כל חיתוך (בסנטימטרים):", min_value=1.0, max_value=600.0, value=100.0, step=5.0)
        with input_cols[2]:
            cut_qty = st.number_input("כמות חיתוכים מסוג זה:", min_value=1, value=1, step=1)
        with input_cols[3]:
            cut_label = st.text_input("שיוך/תיאור (לדוגמה: מסגרת שער, שלבים):", value="כללי")
            
        if st.button("➕ הוסף לרשימת החיתוכים לפרויקט", type="primary"):
            st.session_state.cuts.append({
                "material": material_type,
                "length": cut_length,
                "qty": int(cut_qty),
                "label": cut_label
            })
            st.success("החיתוך נוסף בהצלחה!")
            st.rerun()
            
        # הצגת טבלת החיתוכים הנוכחית
        if st.session_state.cuts:
            st.markdown("---")
            st.subheader("📋 רשימת החיתוכים הנוכחית בפרויקט")
            df_cuts = pd.DataFrame(st.session_state.cuts)
            df_cuts.columns = ["סוג החומר", "אורך (ס"מ)", "כמות", "קבוצה/תיאור"]
            st.dataframe(df_cuts, use_container_width=True)
            
            if st.button("🗑️ נקה את כל רשימת החיתוכים והתחל מחדש"):
                st.session_state.cuts = []
                st.rerun()
        else:
            st.info("רשימת החיתוכים ריקה כרגע. השתמש בטופס למעלה כדי להוסיף חיתוכים לפרויקט.")

    with tab2:
        st.subheader("🔨 עלויות עבודה וצוות")
        lab_cols = st.columns(3)
        with lab_cols[0]:
            st.session_state.labor_details["workers"] = st.number_input("מספר עובדים בפרויקט:", min_value=1, value=st.session_state.labor_details["workers"])
        with lab_cols[1]:
            st.session_state.labor_details["days"] = st.number_input("מספר ימי עבודה מוערכים:", min_value=1, value=st.session_state.labor_details["days"])
        with lab_cols[2]:
            st.session_state.labor_details["daily_rate"] = st.number_input("עלות יומית לעובד (₪):", min_value=0.0, value=st.session_state.labor_details["daily_rate"], step=50.0)
            
        st.session_state.labor_cost = st.session_state.labor_details["workers"] * st.session_state.labor_details["days"] * st.session_state.labor_details["daily_rate"]
        st.write(f"**עלות עבודה כוללת מחושבת:** ₪{st.session_state.labor_cost:,.2f} ({st.session_state.labor_details['workers']} עובדים × {st.session_state.labor_details['days']} ימים)")
        
        st.markdown("---")
        st.subheader("🚛 הוצאות חיצוניות וספקי חוץ")
        cost_cols = st.columns(4)
        with cost_cols[0]:
            st.session_state.other_costs["צביעה"] = st.number_input("עלות צביעה/גלוון (₪):", min_value=0.0, value=st.session_state.other_costs["צביעה"], step=50.0)
        with cost_cols[1]:
            st.session_state.other_costs["הובלה"] = st.number_input("עלות הובלה/מנוף (₪):", min_value=0.0, value=st.session_state.other_costs["הובלה"], step=50.0)
        with cost_cols[2]:
            st.session_state.other_costs["התקנה"] = st.number_input("הוצאות התקנה ושטח (₪):", min_value=0.0, value=st.session_state.other_costs["התקנה"], step=50.0)
        with cost_cols[3]:
            st.session_state.other_costs["פרזול/אחר"] = st.number_input("אביזרי פרזול, מנעולים ואחר (₪):", min_value=0.0, value=st.session_state.other_costs["פרזול/אחר"], step=50.0)
            
        st.markdown("---")
        st.subheader("📈 אחוז רווח ומכפיל סופי לקביעת מחיר")
        st.session_state.markup = st.slider("מכפיל רווח מבוקש לפרויקט (Markup):", min_value=1.0, max_value=3.0, value=st.session_state.markup, step=0.05)
        st.write(f"מכפיל הנוכחי `x{st.session_state.markup}` משמעותו רווח של {int((st.session_state.markup-1)*100)}% מעל כל עלויות הייצור והחומרים.")

    with tab3:
        st.subheader("👤 פרטי הלקוח להצעת המחיר")
        client_cols = st.columns(4)
        with client_cols[0]:
            st.session_state.client_info["name"] = st.text_input("שם הלקוח:", value=st.session_state.client_info["name"])
        with client_cols[1]:
            st.session_state.client_info["phone"] = st.text_input("מספר טלפון:", value=st.session_state.client_info["phone"])
        with client_cols[2]:
            st.session_state.client_info["address"] = st.text_input("כתובת הפרויקט:", value=st.session_state.client_info["address"])
        with client_cols[3]:
            st.session_state.client_info["date"] = st.text_input("תאריך:", value=st.session_state.client_info["date"])

    # ==========================================
    # מנוע החישוב הראשי והאלגוריתם (ייפתח אוטומטית כשיש חיתוכים)
    # ==========================================
    if st.session_state.cuts:
        st.markdown("---")
        st.header("📊 תוצאות אופטימיזציה ותמחור פרויקט")
        
        # שלב א': פיצול רשימת החיתוכים לפי סוגי חומרים שונים
        materials_in_project = set([c["material"] for c in st.session_state.cuts])
        total_material_cost = 0.0
        
        all_materials_summary = []
        
        for mat in materials_in_project:
            st.subheader(f"🧱 תוכנית חיתוך חכמה עבור: {mat}")
            
            # הכנת רשימת החיתוכים הבודדים לחומר הנוכחי
            mat_cuts = [c for c in st.session_state.cuts if c["material"] == mat]
            flat_cuts = []
            for c in mat_cuts:
                for _ in range(c["qty"]):
                    flat_cuts.append(c["length"])
                    
            # מיון מהארוך לקצר (שיטת מעבר ראשון - First Fit Decreasing)
            flat_cuts.sort(reverse=True)
            
            # אלגוריתם אריזה בתיבות (Bin Packing) - אורך מוט ברזל סטנדרטי הוא 600 ס"מ (6 מטר)
            BAR_LENGTH = 600.0
            bars = []  # רשימה של מוטות, כל מוט מכיל מערך של חיתוכים בתוכו
            
            for cut in flat_cuts:
                placed = False
                for bar in bars:
                    if sum(bar) + cut <= BAR_LENGTH:
                        bar.append(cut)
                        placed = True
                        break
                if not placed:
                    bars.append([cut])
            
            # חישוב עלויות לחומר זה
            unit_price_per_meter = prices.get(mat, 0.0)
            cost_per_6m_bar = unit_price_per_meter * 6.0
            mat_total_cost = len(bars) * cost_per_6m_bar
            total_material_cost += mat_total_cost
            
            st.write(f"💡 **נדרשים {len(bars)} מוטות באורך 600 ס\"מ לקבוצה זו.** עלות ברזל: ₪{mat_total_cost:,.2f}")
            
            # הצגה ויזואלית גרפית של ניצול המוטות והפחת
            for idx, bar in enumerate(bars):
                used_space = sum(bar)
                waste = BAR_LENGTH - used_space
                waste_pct = (waste / BAR_LENGTH) * 100
                
                # יצירת בר אחוזים צבעוני לכל מוט
                st.write(f"**מוט #{idx+1}** (פחת: {waste:.1f} ס\"מ):")
                
                # הכנת מחרוזת טקסט להצגה על הגרף
                bar_labels = [f"{length}ס\"מ" for length in bar]
                
                # שימוש בטכניקת פרוגרס בר מרובה של streamlit באמצעות קוד HTML קל
                html_bar = f"<div style='display: flex; width:100%; border:1px solid #ccc; border-radius:5px; margin-bottom:15px; height:25px; overflow:hidden; font-size:11px; text-align:center; line-height:25px; color:white; font-weight:bold;'>"
                for length in bar:
                    pct = (length / BAR_LENGTH) * 100
                    html_bar += f"<div style='width:{pct}%; background-color:#1f77b4; border-right:1px solid #fff;'>{length}</div>"
                if waste > 0:
                    waste_pct_bar = (waste / BAR_LENGTH) * 100
                    html_bar += f"<div style='width:{waste_pct_bar}%; background-color:#d62728;'>פחת: {waste:.1f}</div>"
                html_bar += "</div>"
                st.markdown(html_bar, unsafe_allow_html=True)
                
            all_materials_summary.append({
                "חומר גלם": mat,
                "מוטות לרוכש": len(bars),
                "עלות ברזל (₪)": mat_total_cost
            })

        # ==========================================
        # כרטיסיית סיכום כספי סופי
        # ==========================================
        st.markdown("---")
        st.header("💰 סיכום תמחור ורווחיות פרויקט")
        
        sum_other_costs = sum(st.session_state.other_costs.values())
        total_net_cost = total_material_cost + st.session_state.labor_cost + sum_other_costs
        final_client_price = total_net_cost * st.session_state.markup
        net_profit = final_client_price - total_net_cost
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric("📦 סך עלות חומרי גלם (נטו)", f"₪{total_material_cost:,.2f}")
            st.metric("🔨 סך עלות עבודה צוות", f"₪{st.session_state.labor_cost:,.2f}")
        with col_res2:
            st.metric("🚚 סך הוצאות חוץ וספקים", f"₪{sum_other_costs:,.2f}")
            st.metric("📉 סך כל עלות הייצור (נטו)", f"₪{total_net_cost:,.2f}")
        with col_res3:
            st.subheader(f"💰 הצעת מחיר סופית: ₪{final_client_price:,.2f}")
            st.write(f"**רווח גולמי צפוי לפרויקט:** ₪{net_profit:,.2f} (מכפיל x{st.session_state.markup})")
            
        # ==========================================
        # כפתורי שמירה לענן וייצוא PDF
        # ==========================================
        st.markdown("---")
        action_cols = st.columns(2)
        
        with action_cols[0]:
            project_name_to_save = st.text_input("הזן שם ייחודי לשמירת הפרויקט בארכיון:", value=st.session_state.client_info["name"] if st.session_state.client_info["name"] else "פרויקט ללא שם")
            if st.button("💾 שמור וסנכרן פרויקט לארכיון הענן", type="primary"):
                projects_archive[project_name_to_save] = {
                    "cuts": st.session_state.cuts,
                    "other_costs": st.session_state.other_costs,
                    "labor_cost": st.session_state.labor_cost,
                    "markup": st.session_state.markup,
                    "client_info": st.session_state.client_info,
                    "total_material_cost": total_material_cost,
                    "final_price": final_client_price
                }
                save_projects(projects_archive)
                st.success(f"🎉 הפרויקט '{project_name_to_save}' סונכרן ונשמר בהצלחה בארכיון!")
                
        with action_cols[1]:
            st.markdown("### 📄 הפקת מסמך הצעת מחיר רשמית")
            st.write("בלחיצה על הכפתור למטה המערכת תייצר מסמך PDF נקי ומעוצב לחלוקה ללקוח.")
            
            # בניית קוד HTML עבור ה-PDF
            html_pdf_template = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Helvetica, Arial, sans-serif; direction: rtl; text-align: right; color: #333; }}
                    .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                    .section {{ margin-top: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; direction: rtl; }}
                    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: right; }}
                    th {{ background-color: #f2f2f2; }}
                    .total {{ font-size: 18px; font-weight: bold; color: #1a5276; margin-top: 20px; text-align: left; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Elad Cohen Iron Art</h1>
                    <h3>הצעת מחיר רשמית לעבודות מסגרות ואמנות בברזל</h3>
                    <p>תאריך: {st.session_state.client_info['date']}</p>
                </div>
                <div class="section">
                    <h4>פרטי לקוח ופרויקט:</h4>
                    <p><b>שם הלקוח:</b> {st.session_state.client_info['name']}</p>
                    <p><b>טלפון:</b> {st.session_state.client_info['phone']}</p>
                    <p><b>כתובת אספקה/התקנה:</b> {st.session_state.client_info['address']}</p>
                </div>
                <div class="section">
                    <h4>פירוט חומרי גלם ועבודות חיתוך שנכללו:</h4>
                    <table>
                        <tr>
                            <th>סוג החומר</th>
                            <th>אורך (ס"מ)</th>
                            <th>כמות חיתוכים</th>
                            <th>שיוך רכיב</th>
                        </tr>
            """
            for cut in st.session_state.cuts:
                html_pdf_template += f"""
                        <tr>
                            <td>{cut['material']}</td>
                            <td>{cut['length']}</td>
                            <td>{cut['qty']}</td>
                            <td>{cut['label']}</td>
                        </tr>
                """
            html_pdf_template += f"""
                    </table>
                </div>
                <div class="section" style="border-top: 1px solid #eee; padding-top: 15px;">
                    <h4>סיכום כללי והתחייבות:</h4>
                    <p>המחיר כולל את כל הוצאות חומרי הגלם, צבע, הובלה והתקנה בשטח בהתאם לסיכום.</p>
                    <div class="total">סה"כ לתשלום סופי (₪): {final_client_price:,.2f} ₪</div>
                </div>
            </body>
            </html>
            """
            
            # פונקציה לייצור קובץ ה-PDF בפועל בזיכרון המערכת
            def generate_pdf(html_data):
                import io
                pdf_buffer = io.BytesIO()
                pisa_status = pisa.CreatePDF(html_data, dest=pdf_buffer, encoding='utf-8')
                if pisa_status.err:
                    return None
                pdf_buffer.seek(0)
                return pdf_buffer.getvalue()
                
            pdf_data = generate_pdf(html_pdf_template)
            
            if pdf_data:
                st.download_button(
                    label="📥 הורד הצעת מחיר כ-PDF ללקוח",
                    data=pdf_data,
                    file_name=f"הצעת_מחיר_{st.session_state.client_info['name'] if st.session_state.client_info['name'] else 'אלעד_כהן'}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("תקלה ביצירת ה-PDF. ודא כי כל הנתונים רשומים בצורה תקינה.")
