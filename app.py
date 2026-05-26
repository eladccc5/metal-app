import streamlit as st
import pandas as pd
import json
import requests
import base64
import re
from datetime import datetime

# =============================================================================
# 1. הגדרות עיצוב, כיווניות (RTL) וכפיית ערכת נושא בהירה מוחלטת
# =============================================================================
st.set_page_config(
    page_title="מערכת תמחור וחיתוך - Elad Cohen Iron Art", 
    layout="wide"
)

# הזרקת CSS מקיף לדריסת המצב הכהה של הדפדפן, קביעת סיידבר אפרפר, ושדות בהירים
st.markdown("""
    <style>
    /* כפיית רקע לבן מוחלט וטקסט כהה על מרכז האפליקציה */
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }
    
    /* עיצוב הסרגל הימני (Sidebar) - אפור בהיר ועדין להפרדה משאר העמוד */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
        background-color: #f1f3f5 !important;
        border-left: 1px solid #dee2e6 !important;
    }
    
    /* הגדרת כיווניות מימין לשמאל (RTL) לכל הממשק והסיידבר */
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        direction: rtl !important;
    }
    
    /* יישור טקסט, תוויות וכותרות לימין */
    h1, h2, h3, h4, h5, h6, p, span, label, div.stMarkdown, [data-testid="stWidgetLabel"] p {
        text-align: right !important;
        direction: rtl !important;
        color: #111111 !important;
    }
    
    /* טיפול שורש בשדות הקלט, התיבות והסלקטורים - שלא יהיו שחורים בשום מצב */
    div[data-baseweb="select"], div[data-baseweb="input"], input, select, textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #cccccc !important;
    }
    
    /* תיקון צבע הטקסט הכתוב בתוך השדות ותפריטי הבחירה */
    input, select, textarea, span[data-baseweb="select"], div[role="listbox"], option {
        color: #111111 !important;
        background-color: #ffffff !important;
    }
    
    /* התאמת כפתורים */
    button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-primary"] {
        background-color: #e9ecef !important;
        color: #111111 !important;
        border: 1px solid #ced4da !important;
    }
    
    /* עיצוב לוח עריכת הנתונים והטבלאות ברקע לבן */
    div[data-testid="stDataEditor"], div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        direction: rtl !important;
        background-color: #ffffff !important;
    }
    
    /* שמירה על כיוון משמאל לימין אך ורק עבור סליידרים */
    div[data-baseweb="slider"] {
        direction: ltr !important;
    }
    
    /* קופסאות חלוקה ובלוקים בהירים במרכז העמוד */
    .material-block {
        border: 1px solid #dcdcdc;
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 20px;
        direction: rtl;
    }
    
    /* עיצוב פס המוט הויזואלי - עבה, כחול (מנוצל) ואדום (פחת) */
    .custom-bar-container {
        width: 100%;
        background-color: #d32f2f; /* אדום - פחת */
        height: 35px;
        border-radius: 6px;
        margin: 10px 0;
        position: relative;
        overflow: hidden;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
        direction: ltr !important; /* זרימת מילוי משמאל לימין */
    }
    .custom-bar-fill {
        background-color: #1565c0; /* כחול - מנוצל */
        height: 100%;
        transition: width 0.4s ease;
    }
    
    /* קוביות סיכום כלכלי */
    .metric-box {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. חיבור מאובטח ל-GitHub API
# =============================================================================
GITHUB_USERNAME = "eladccc5"
GITHUB_REPO = "metal-app"

if "GITHUB_TOKEN" in st.secrets:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
else:
    GITHUB_TOKEN = ""

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
        "צינור עגול": {
            "dimensions": ["עגול 1/2 צול", "עגול 3/4 צול", "עגול 1 צול", "עגול 1.25 צול", "עגול 1.5 צול", "עגול 2 צול", "עגול 3 צול"],
            "thicknesses": ["1.5 מ\"מ", "2.0 מ\"מ", "2.5 מ\"מ", "3.0 מ\"מ"],
            "length": 600,
            "prices": {}
        },
        "ברזל זווית": {
            "dimensions": ["20x20", "25x25", "30x30", "40x40", "50x50"],
            "thicknesses": ["3.0 מ\"מ", "4.0 מ\"מ", "5.0 מ\"מ"],
            "length": 600,
            "prices": {}
        },
        "ברזל שטוח": {
            "dimensions": ["20x3", "30x3", "40x4", "50x5", "60x6", "80x8", "100x10"],
            "thicknesses": ["נטול עובי מובנה (מידה מלאה)"],
            "length": 600,
            "prices": {}
        },
        "ברזל בניין עגול": {
            "dimensions": ["קוטר 8 מ\"מ", "קוטר 10 מ\"מ", "קוטר 12 מ\"מ", "קוטר 14 מ\"מ", "קוטר 16 מ\"מ"],
            "thicknesses": ["מלא (ללא עובי דופן)"],
            "length": 600,
            "prices": {}
        }
    }

def load_from_github(filename, default_value):
    if not GITHUB_TOKEN:
        return default_value
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content_b64 = r.json()["content"]
            content_str = base64.b64decode(content_b64).decode('utf-8')
            return json.loads(content_str)
        return default_value
    except:
        return default_value

def save_to_github(filename, data, commit_message="Update data"):
    if not GITHUB_TOKEN:
        return False
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    sha = None
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json()["sha"]
        
    content_str = json.dumps(data, ensure_ascii=False, indent=4)
    content_b64 = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
    
    payload = {"message": commit_message, "content": content_b64}
    if sha:
        payload["sha"] = sha
        
    r_put = requests.put(url, headers=headers, json=payload)
    return r_put.status_code in [200, 201]

def build_pdf_html_content(title, name, phone, date, mult, iron_c, exp_dict, labor_c, final_q, materials_table_html):
    exp_rows = ""
    total_expenses_calc = 0.0
    if exp_dict:
        for item_name, cost_val in exp_dict.items():
            if cost_val > 0:
                total_expenses_calc += cost_val
                exp_rows += f"<tr><td>{item_name}</td><td>₪{cost_val:,.2f}</td></tr>"
    if exp_rows == "":
        exp_rows = "<tr><td colspan='2'>אין הוצאות נלוות נוספות לפרויקט זה</td></tr>"
        
    html_template = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <title>דוח פרויקט - Elad Cohen Iron Art</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 30px; color: #111; line-height: 1.6; background-color: #fff; }}
            .header {{ text-align: center; border-bottom: 3px solid #1E3A8A; padding-bottom: 10px; margin-bottom: 30px; }}
            .header h1 {{ color: #1E3A8A; margin: 0; font-size: 28px; }}
            .header p {{ margin: 5px 0 0 0; color: #555; }}
            .section-title {{ color: #1E3A8A; border-right: 4px solid #1E3A8A; padding-right: 10px; margin-top: 25px; margin-bottom: 15px; font-size: 18px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: right; }}
            th {{ background-color: #f2f2f2; color: #1E3A8A; font-weight: bold; }}
            .summary-box {{ background-color: #f9f9f9; border: 1px solid #ddd; padding: 20px; border-radius: 6px; margin-top: 30px; }}
            .summary-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #eee; font-size: 15px; }}
            .final-price {{ font-size: 20px; font-weight: bold; color: #E65100; border-bottom: none; margin-top: 10px; padding-top: 10px; border-top: 2px solid #E65100; }}
            .footer {{ text-align: center; margin-top: 50px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Elad Cohen Iron Art 🛠️</h1>
            <p>דוח סיכום, תוכנית חיתוך ברזל ותמחור פרויקט</p>
        </div>
        
        <div class="section-title">📋 פרטי לקוח ופרויקט כלליים</div>
        <table>
            <tr>
                <td><b>שם פרויקט:</b> {title}</td>
                <td><b>שם הלקוח:</b> {name}</td>
            </tr>
            <tr>
                <td><b>טלפון:</b> {phone}</td>
                <td><b>תאריך הפקה:</b> {date}</td>
            </tr>
        </table>
        
        <div class="section-title">🧱 פירוט כמויות ברזל חומרי גלם ופחת</div>
        {materials_table_html}
        
        <div class="section-title">🎨 עלויות נלוות וחומרי עזר</div>
        <table>
            <thead>
                <tr><th>תיאור רכיב/חומר</th><th>עלות כוללת בש"ח</th></tr>
            </thead>
            <tbody>
                {exp_rows}
            </tbody>
        </table>
        
        <div class="section-title">💰 סיכום כלכלי הצעת מחיר סופית ללקוח</div>
        <div class="summary-box">
            <div class="summary-row"><span>עלות חומרי גלם (ברזל נטו):</span> <span>₪{iron_c:,.2f}</span></div>
            <div class="summary-row"><span>עלות חומרי עזר והוצאות חיצוניות:</span> <span>₪{total_expenses_calc:,.2f}</span></div>
            <div class="summary-row"><span>עלות ימי עבודה (עבודה עצמית):</span> <span>₪{labor_c:,.2f}</span></div>
            <div class="summary-row"><span>מקדם רווח מוגדר:</span> <span>x{mult}</span></div>
            <div class="summary-row final-price"><span>סך הכל הצעת מחיר סופית ללקוח (כולל מע"מ):</span> <span>₪{final_q:,.2f}</span></div>
        </div>
        
        <div class="footer">
            הופק אוטומטית באמצעות מערכת הניהול והאופטימיזציה של Elad Cohen Iron Art © {datetime.now().year}
        </div>
    </body>
    </html>
    """
    return html_template

# טעינת נתונים ראשונית מהענן
if "catalog" not in st.session_state:
    st.session_state.catalog = load_from_github("catalog.json", get_initial_catalog())

if "saved_projects" not in st.session_state:
    st.session_state.saved_projects = load_from_github("saved_projects.json", [])

if "current_cuts" not in st.session_state:
    st.session_state.current_cuts = []

# =============================================================================
# 3. בניית סרגל הניווט והוצאות קבועות בצד ימין (Sidebar)
# =============================================================================
st.sidebar.markdown(f"<h2 style='text-align: center; color: #1E3A8A;'>Elad Cohen Iron Art 🛠️</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<hr>", unsafe_allow_html=True)

sidebar_page = st.sidebar.radio(
    label="ניווט בתפריט המערכת:",
    options=["💰 מחירון ברזל ומלאי", "🏗️ חישוב פרויקט חדש", "📁 ארכיון פרויקטים"]
)

labor_workers = 1
labor_days = 1
labor_daily_cost = 0.0
profit_multiplier = 1.5
sidebar_expenses = {}

if sidebar_page == "🏗️ חישוב פרויקט חדש":
    st.sidebar.markdown("### 👷 עלויות עבודה ורווח")
    labor_workers = st.sidebar.number_input("כמות עובדים:", min_value=1, value=1, step=1)
    labor_days = st.sidebar.number_input("ימי עבודה:", min_value=1, value=1, step=1)
    labor_daily_cost = st.sidebar.number_input("עלות יומית לעובד (₪):", min_value=0.0, value=0.0, step=100.0)
    profit_multiplier = st.sidebar.slider("מקדם תמחור סופי (רווח):", min_value=1.0, max_value=3.0, value=1.5, step=0.05)
    
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    st.sidebar.markdown("### 🎨 עלויות והוצאות נלוות (₪)")
    sidebar_expenses["צבע בתנור"] = st.sidebar.number_input("צבע בתנור:", min_value=0.0, value=0.0, step=50.0)
    sidebar_expenses["הובלה"] = st.sidebar.number_input("הובלה:", min_value=0.0, value=0.0, step=50.0)
    sidebar_expenses["נגרות"] = st.sidebar.number_input("נגרות:", min_value=0.0, value=0.0, step=50.0)
    sidebar_expenses["זגגות"] = st.sidebar.number_input("זגגות:", min_value=0.0, value=0.0, step=50.0)
    sidebar_expenses["חיתוכי לייזר"] = st.sidebar.number_input("חיתוכי לייזר:", min_value=0.0, value=0.0, step=50.0)
    sidebar_expenses["מנוף"] = st.sidebar.number_input("מנוף:", min_value=0.0, value=0.0, step=50.0)
    sidebar_expenses["שונות"] = st.sidebar.number_input("שונות:", min_value=0.0, value=0.0, step=50.0)

# =============================================================================
# עמוד 1: ניהול ועריכת מחירון חומרי גלם
# =============================================================================
if sidebar_page == "💰 מחירון ברזל ומלאי":
    st.markdown("<h2 style='text-align: right; color: #2E7D32;'>💰 ניהול מחירון ברזל (שקל לטון / מטר רץ)</h2>", unsafe_allow_html=True)
    
    selected_cat = st.selectbox("בחר קטגוריית ברזל לעריכה:", list(st.session_state.catalog.keys()))
    cat_data = st.session_state.catalog[selected_cat]
    
    dims = cat_data["dimensions"]
    thicks = cat_data["thicknesses"]
    
    grid_data = {}
    for t in thicks:
        grid_data[t] = []
        for d in dims:
            key = f"{d}_{t}"
            grid_data[t].append(cat_data["prices"].get(key, 0.0))
            
    df_editor = pd.DataFrame(grid_data, index=dims)
    edited_df = st.data_editor(df_editor, use_container_width=True)
    
    if st.button("💾 שמור מחירון מעודכן לענן", use_container_width=True, type="primary"):
        for t in thicks:
            for d in dims:
                key = f"{d}_{t}"
                val = edited_df.loc[d, t]
                st.session_state.catalog[selected_cat]["prices"][key] = float(val)
                
        if save_to_github("catalog.json", st.session_state.catalog, f"עדכון מחירון {selected_cat}"):
            st.success(f"🎯 מחירון {selected_cat} עודכן ונשמר בהצלחה בענן!")
        else:
            st.error("שגיאה בשמירה לענן.")

# =============================================================================
# עמוד 2: חישוב פרויקט חדש ואופטימיזציית חיתוכים אוטומטית מיידית
# =============================================================================
elif sidebar_page == "🏗️ חישוב פרויקט חדש":
    st.markdown("<h2 style='text-align: right; color: #1E3A8A;'>🏗️ תכנון פרויקט ואופטימיזציית חיתוך אוטומטית</h2>", unsafe_allow_html=True)
    
    st.markdown("<div class='material-block'>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: right;'>📋 פרטי הלקוח והפרויקט</h4>", unsafe_allow_html=True)
    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    with c_p1:
        project_title = st.text_input("שם הפרויקט / לקוח:", value="מעקה דקורטיבי - משפחת כהן")
    with c_p2:
        client_name = st.text_input("איש קשר / שם מלא:", value="אלי כהן")
    with c_p3:
        client_phone = st.text_input("טלפון:", value="050-1234567")
    with c_p4:
        project_date = st.text_input("תאריך פרויקט:", value=datetime.now().strftime("%Y-%m-%d"))
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: right;'>🔨 הזנת רשימת חיתוכים (מוטות נדרשים)</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='material-block'>", unsafe_allow_html=True)
    col_in1, col_in2, col_in3, col_in4, col_in5, col_in6, col_in7 = st.columns([2, 1.5, 1.5, 1.5, 1.2, 1.5, 1.2])
    
    with col_in1:
        in_cat = st.selectbox("סוג ברזל:", list(st.session_state.catalog.keys()), key="add_cat")
    with col_in2:
        in_dim = st.selectbox("מידה (פרופיל/קוטר):", st.session_state.catalog[in_cat]["dimensions"], key="add_dim")
    with col_in3:
        in_thick = st.selectbox("עובי דופן:", st.session_state.catalog[in_cat]["thicknesses"], key="add_thick")
    with col_in4:
        in_length = st.number_input("אורך חיתוך (ס\"מ):", min_value=1.0, max_value=600.0, value=100.0, step=1.0)
    with col_in5:
        in_qty = st.number_input("כמות (יח'):", min_value=1, value=1, step=1)
    with col_in6:
        in_edges = st.selectbox("סוג קצוות (זוויות):", ["ישר / ישר (90°)", "ישר / 45°", "45° / 45°"], key="add_edges")
    with col_in7:
        in_group = st.text_input("שיוך/רכיב:", value="כללי", key="add_group")
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ הוסף חיתוך לרשימה", use_container_width=True, type="secondary"):
        st.session_state.current_cuts.append({
            "קטגוריה": in_cat,
            "מידה": in_dim,
            "עובי דופן": in_thick,
            "אורך (ס\"מ)": in_length,
            "כמות": in_qty,
            "סוג קצוות": in_edges,
            "קבוצת שיוך": in_group
        })
        st.toast("החיתוך נוסף בהצלחה!")
        st.rerun()
        
    if st.session_state.current_cuts:
        st.markdown("<h4 style='text-align: right;'>📋 רשימת חיתוכי הברזל המבוקשים בפרויקט</h4>", unsafe_allow_html=True)
        df_saved_cuts = pd.DataFrame(st.session_state.current_cuts)
        df_saved_cuts.columns = ["קטגוריה", "מידה", "עובי דופן", "אורך חיתוך (ס\"מ)", "כמות יחידות", "סוג קצוות", "קבוצת שיוך"]
        st.dataframe(df_saved_cuts, use_container_width=True)
        
        if st.button("🗑️ נקה את כל רשימת החיתוכים", type="primary"):
            st.session_state.current_cuts = []
            st.rerun()

    # =============================================================================
    # לוגיקת החישוב והאופטימיזציה האוטומטית המיידית
    # =============================================================================
    if st.session_state.current_cuts:
        st.markdown("<hr>", unsafe_allow_html=True)
        
        def run_cutting_optimization(cuts_list, stock_length=600):
            flat_cuts = []
            for c in cuts_list:
                for _ in range(c["כמות"]):
                    flat_cuts.append({
                        "length": c["אורך (ס\"מ)"],
                        "group": c["קבוצת שיוך"],
                        "edges": c["סוג קצוות"],
                        "key": f"{c['קטגוריה']}_{c['מידה']}_{c['עובי דופן']}"
                    })
            
            flat_cuts.sort(key=lambda x: x["length"], reverse=True)
            
            grouped_cuts = {}
            for cut in flat_cuts:
                grouped_cuts.setdefault(cut["key"], []).append(cut)
                
            result_bars = {}
            for mat_key, mat_cuts in grouped_cuts.items():
                bars = []
                for cut in mat_cuts:
                    placed = False
                    for b in bars:
                        if b["remaining"] >= cut["length"]:
                            b["cuts"].append(cut)
                            b["remaining"] -= cut["length"]
                            placed = True
                            break
                    if not placed:
                        bars.append({
                            "total_length": stock_length,
                            "remaining": stock_length - cut["length"],
                            "cuts": [cut]
                        })
                    result_bars[mat_key] = bars
            return result_bars

        optimized_results = run_cutting_optimization(st.session_state.current_cuts)
        
        total_iron_cost = 0.0
        summary_rows = []
        
        st.markdown("<h3 style='text-align: right; color: #1565c0; margin-top:20px;'>📊 תוכנית חיתוך מפורטת ותצוגה ויזואלית של המוטות (כחול ואדום)</h3>", unsafe_allow_html=True)
        
        for mat_key, bars in optimized_results.items():
            parts = mat_key.split("_")
            cat, dim, thick = parts[0], parts[1], parts[2]
            
            price_per_unit = st.session_state.catalog[cat]["prices"].get(f"{dim}_{thick}", 0.0)
            num_bars = len(bars)
            cost_for_material = num_bars * price_per_unit
            total_iron_cost += cost_for_material
            
            total_waste_mat = sum([b["remaining"] for b in bars])
            
            summary_rows.append({
                "קטגוריה": cat,
                "מידה": dim,
                "עובי דופן": thick,
                "מוטות נדרשים (6 מ')": num_bars,
                "מחיר למוט (₪)": price_per_unit,
                "עלות סך הכל (₪)": cost_for_material,
                "פחת מצטבר (ס\"מ)": total_waste_mat
            })
            
            st.markdown(f"<h5 style='text-align: right; color:#1E3A8A; margin-top:15px;'>🔨 {cat} - מידה {dim} (עובי {thick}) | נדרשים {num_bars} מוטות סה\"כ:</h5>", unsafe_allow_html=True)
            
            for idx, b in enumerate(bars):
                used_length = b["total_length"] - b["remaining"]
                utilization_pct = (used_length / b["total_length"]) * 100
                
                st.markdown(f"<div style='margin-bottom: 2px; font-weight: bold;'>מוט מספר {idx+1} (600 ס\"מ) - ניצול: {int(utilization_pct)}%</div>", unsafe_allow_html=True)
                
                # הפס הגרפי העבה בכחול ואדום
                st.markdown(f"""
                <div class='custom-bar-container'>
                    <div class='custom-bar-fill' style='width: {utilization_pct}%;'></div>
                </div>
                """, unsafe_allow_html=True)
                
                cuts_labels = " ← ".join([f"✂️ <b>{c['length']} ס\"מ</b> ({c['group']}) [<span style='color:#555;'>{c['edges']}</span>]" for c in b["cuts"]])
                st.markdown(f"<div style='padding-right:5px; margin-bottom:15px; font-size:0.95rem; color:#111;'><b>תוכנית החיתוך למוט:</b> {cuts_labels} | <span style='color:#d32f2f; font-weight:bold;'>שארית פחת: {b['remaining']} ס\"מ</span></div>", unsafe_allow_html=True)

        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: right; color: #E65100;'>📊 דוח סיכום עלויות ותמחור סופי לפרויקט</h3>", unsafe_allow_html=True)
        
        df_summary_project = pd.DataFrame(summary_rows)
        st.dataframe(df_summary_project, use_container_width=True)
        
        total_ext_expenses = sum(sidebar_expenses.values())
        labor_total_cost = labor_workers * labor_days * labor_daily_cost
        
        net_cost_project = total_iron_cost + total_ext_expenses + labor_total_cost
        final_customer_quote = net_cost_project * profit_multiplier
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f"<div class='metric-box'><b>עלות חומרי גלם (ברזל)</b><br><span style='font-size:1.5rem; color:#1565c0; font-weight:bold;'>₪{total_iron_cost:,.2f}</span></div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div class='metric-box'><b>עלויות נלוות (סרגל צד)</b><br><span style='font-size:1.5rem; color:#2e7d32; font-weight:bold;'>₪{total_ext_expenses:,.2f}</span></div>", unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"<div class='metric-box'><b>עלות עבודה עצמית נטו</b><br><span style='font-size:1.5rem; color:#7B1FA2; font-weight:bold;'>₪{labor_total_cost:,.2f}</span></div>", unsafe_allow_html=True)
        with col_m4:
            st.markdown(f"<div class='metric-box' style='background-color:#FFF3E0; border:2px solid #FF9800;'><b>💰 הצעת מחיר מומלצת ללקוח</b><br><span style='font-size:1.6rem; font-weight:bold; color:#E65100;'>₪{final_customer_quote:,.2f}</span></div>", unsafe_allow_html=True)
        
        materials_html_table = df_summary_project.to_html(index=False, classes='table')
        
        html_pdf_template = build_pdf_html_content(
            project_title, client_name, client_phone, project_date, profit_multiplier,
            total_iron_cost, sidebar_expenses, labor_total_cost, final_customer_quote,
            materials_html_table
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        clean_filename = re.sub(r'[\/*?:"<>|]', "", project_title)
        
        st.download_button(
            label="📄 הורד דף סיכום פרויקט מוכן להדפסה (PDF/HTML)",
            data=html_pdf_template,
            file_name=f"סיכום_פרויקט_{clean_filename}.html",
            mime="text/html",
            use_container_width=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📁 שמור פרויקט זה לארכיון פרויקטים בענן", use_container_width=True):
            project_data_to_archive = {
                "title": project_title,
                "client_name": client_name,
                "phone": client_phone,
                "date": project_date,
                "multiplier": profit_multiplier,
                "iron_cost": total_iron_cost,
                "expenses": sidebar_expenses,
                "labor_cost": labor_total_cost,
                "final_quote": final_customer_quote,
                "summary_rows": summary_rows,
                "cuts_snapshot": st.session_state.current_cuts
            }
            
            st.session_state.saved_projects.append(project_data_to_archive)
            if save_to_github("saved_projects.json", st.session_state.saved_projects, f"הוספת פרויקט {project_title} לארכיון"):
                st.success(f"🎯 פרויקט '{project_title}' נשמר בהצלחה בארכיון הענן!")
                st.rerun()
            else:
                st.error("שגיאה בשמירת הפרויקט בארכיון הענן.")

# =============================================================================
# עמוד 3: ארכיון פרויקטים שמורים וטעינת נתוני עבר
# =============================================================================
elif sidebar_page == "📁 ארכיון פרויקטים":
    st.markdown("<h2 style='text-align: right; color: #7B1FA2;'>📁 ארכיון פרויקטים שמורים בענן</h2>", unsafe_allow_html=True)
    
    if not st.session_state.saved_projects:
        st.info("אין כרגע פרויקטים שמורים בארכיון הענן.")
    else:
        for p_idx, project in enumerate(st.session_state.saved_projects):
            p_title = project.get("title", f"פרויקט ללא שם #{p_idx+1}")
            p_date = project.get("date", "-")
            p_client = project.get("client_name", "-")
            p_final_quote = project.get("final_quote", 0.0)
            
            with st.expander(f"📁 {p_title} | לקוח: {p_client} | תאריך: {p_date} | עלות: ₪{p_final_quote:,.2f}"):
                st.markdown(f"<h5>פרטי ריכוז עלויות לפרויקט: {p_title}</h5>", unsafe_allow_html=True)
                
                archived_rows = project.get("summary_rows", [])
                if archived_rows:
                    df_arch_summary = pd.DataFrame(archived_rows)
                    st.dataframe(df_arch_summary, use_container_width=True)
                    
                col_actions1, col_actions2, col_actions3 = st.columns(3)
                
                if col_actions1.button("🔄 טען חיתוכים והוצאות לעמוד עבודה", key=f"load_{p_idx}", use_container_width=True):
                    st.session_state.current_cuts = project.get("cuts_snapshot", [])
                    st.success("הנתונים נטענו בהצלחה! כנס לטאב 'חישוב פרויקט חדש' לצפייה.")
                    st.rerun()
                    
                archived_iron_cost = project.get('iron_cost', 0.0)
                archive_ext_pdf_dict = project.get('expenses', {})
                labor_total_cost_archived = project.get('labor_cost', 0.0)
                final_quote_archived = project.get('final_quote', 0.0)
                
                df_summary_archived_table = pd.DataFrame(archived_rows)
                pdf_archive_materials_html = df_summary_archived_table.to_html(index=False, classes='table') if archived_rows else ""
                
                archive_html_pdf_template = build_pdf_html_content(
                    p_title, project.get('client_name','-'), project.get('phone','-'), 
                    project.get('date','-'), project.get('multiplier', 1.5),
                    archived_iron_cost, archive_ext_pdf_dict, labor_total_cost_archived, final_quote_archived,
                    pdf_archive_materials_html
                )
                
                clean_archive_filename = re.sub(r'[\/*?:"<>|]', "", p_title)
                col_actions2.download_button(
                    label="📄 הורד מסמך PDF מהארכיון",
                    data=archive_html_pdf_template,
                    file_name=f"ארכיון_פרויקט_{clean_archive_filename}.html",
                    mime="text/html",
                    key=f"pdf_arch_{p_idx}",
                    use_container_width=True
                )
                
                if col_actions3.button("❌ מחק פרויקט לצמיתות", key=f"del_{p_idx}", use_container_width=True):
                    st.session_state.saved_projects.pop(p_idx)
                    if save_to_github("saved_projects.json", st.session_state.saved_projects, f"מחיקת פרויקט {p_title}"):
                        st.success(f"הפרויקט {p_title} נמחק לצמיתות מהארכיון!")
                        st.rerun()
                    else:
                        st.error("שגיאה במחיקת הפרויקט משרת הענן.")
