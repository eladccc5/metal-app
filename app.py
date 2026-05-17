"""
מחשבון BOM ועלויות לעבודות מתכת
=================================
אפליקציית Streamlit לנפחים ועובדי מתכת:
העלאת סקיצה → חילוץ חומרים עם בינה מלאכותית → חישוב עלויות

הרצה:
    pip install streamlit pandas pillow openai google-generativeai
    streamlit run app.py
"""

import json
import base64
import io
import streamlit as st
import pandas as pd
from PIL import Image

# ─────────────────────────────────────────────
# הגדרות עמוד
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="מחשבון BOM ועלויות לנפחות",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# עיצוב CSS — תעשייתי, RTL, עברית
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&family=Heebo:wght@300;400;600;700&display=swap');

/* ── משתני צבע ── */
:root {
    --forge-black:   #0d0d0d;
    --forge-dark:    #161616;
    --forge-panel:   #1e1e1e;
    --forge-border:  #2e2e2e;
    --forge-iron:    #3a3a3a;
    --forge-steel:   #8a9aaa;
    --forge-spark:   #ff6a00;
    --forge-amber:   #f0a500;
    --forge-text:    #d8d8d8;
    --forge-muted:   #666;
    --forge-white:   #f5f5f0;
    --forge-green:   #00e5a0;
}

/* ── איפוס גלובלי + RTL ── */
html, body, [class*="css"] {
    background-color: var(--forge-dark) !important;
    color: var(--forge-text) !important;
    font-family: 'Heebo', sans-serif !important;
    direction: rtl !important;
}

/* ── כל הטקסט ל-RTL ── */
p, h1, h2, h3, h4, h5, h6, li, span, div, label,
.stMarkdown, .stText, [data-testid="stMarkdownContainer"] {
    direction: rtl !important;
    text-align: right !important;
    unicode-bidi: embed;
}

/* ── סרגל צד ── */
[data-testid="stSidebar"] {
    background-color: var(--forge-black) !important;
    border-left: 2px solid var(--forge-spark) !important;
    border-right: none !important;
    direction: rtl !important;
}
[data-testid="stSidebar"] * {
    color: var(--forge-text) !important;
    direction: rtl !important;
    text-align: right !important;
}

/* ── כותרת ראשית ── */
.forge-title-heb {
    font-family: 'Heebo', sans-serif;
    font-weight: 700;
    font-size: 1.8rem;
    color: var(--forge-white);
    direction: rtl;
    text-align: right;
    margin: 0;
    letter-spacing: 1px;
}
.forge-subtitle {
    font-family: 'Heebo', sans-serif;
    color: var(--forge-spark);
    font-size: 0.9rem;
    letter-spacing: 1px;
    margin-top: 4px;
    direction: rtl;
    text-align: right;
}
.forge-divider {
    border: none;
    border-top: 2px solid var(--forge-border);
    margin: 1rem 0 1.5rem;
}
.accent-line {
    width: 60px; height: 3px;
    background: var(--forge-spark);
    margin-bottom: 1rem;
}

/* ── תג שלב ── */
.step-badge {
    display: inline-block;
    background: var(--forge-spark);
    color: #000 !important;
    font-family: 'Heebo', sans-serif;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 3px 14px;
    margin-bottom: 6px;
    border-radius: 1px;
    direction: rtl;
}

/* ── כרטיסי מדד ── */
.metric-card {
    background: var(--forge-panel);
    border: 1px solid var(--forge-border);
    border-right: 4px solid var(--forge-spark);
    border-left: none;
    padding: 1.2rem 1.5rem;
    border-radius: 2px;
    direction: rtl;
    text-align: right;
}
.metric-label {
    font-family: 'Heebo', sans-serif;
    font-size: 0.75rem;
    color: var(--forge-muted);
    direction: rtl;
}
.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    letter-spacing: 1px;
    color: var(--forge-amber);
    line-height: 1.1;
    direction: ltr;
    text-align: left;
}
.metric-sub {
    font-size: 0.75rem;
    color: var(--forge-muted);
    margin-top: 2px;
    direction: rtl;
}

/* ── כרטיס סה"כ ── */
.total-block {
    background: #0f1f18;
    border: 1px solid var(--forge-border);
    border-right: 4px solid var(--forge-green);
    padding: 1.4rem 1.8rem;
    border-radius: 2px;
    direction: rtl;
    text-align: right;
}
.total-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    color: var(--forge-green);
    letter-spacing: 2px;
    line-height: 1;
    direction: ltr;
    text-align: left;
}

/* ── אזור העלאה ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--forge-iron) !important;
    border-radius: 2px !important;
    background: var(--forge-panel) !important;
    transition: border-color 0.2s;
    direction: rtl !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--forge-spark) !important;
}

/* ── כפתורים ── */
.stButton > button {
    background: var(--forge-spark) !important;
    color: #000 !important;
    font-family: 'Heebo', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 1px !important;
    border: none !important;
    border-radius: 1px !important;
    padding: 0.55rem 2rem !important;
    transition: background 0.15s, transform 0.1s;
    direction: rtl !important;
    width: 100%;
}
.stButton > button:hover {
    background: var(--forge-amber) !important;
    transform: translateY(-1px);
}

/* ── טבלאות ── */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    background: var(--forge-panel) !important;
    border: 1px solid var(--forge-border) !important;
}

/* ── תיבות קלט ── */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input {
    background: var(--forge-panel) !important;
    color: var(--forge-text) !important;
    border-color: var(--forge-iron) !important;
    direction: rtl !important;
    text-align: right !important;
}
.stSelectbox label, .stNumberInput label,
.stTextInput label, .stSlider label {
    direction: rtl !important;
    text-align: right !important;
    display: block;
}

/* ── הודעות מערכת ── */
.stAlert {
    border-radius: 2px !important;
    direction: rtl !important;
    text-align: right !important;
}

/* ── לשוניות ── */
[data-testid="stTabs"] { direction: rtl !important; }
[data-testid="stTabs"] button {
    font-family: 'Heebo', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: var(--forge-muted) !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--forge-spark) !important;
    border-bottom: 2px solid var(--forge-spark) !important;
}

/* ── פאנל פרשנות AI ── */
.ai-interp-box {
    background: var(--forge-panel);
    border-right: 4px solid var(--forge-amber);
    padding: 0.8rem 1.2rem;
    margin-bottom: 1rem;
    border-radius: 1px;
    direction: rtl;
    text-align: right;
}
.ai-interp-label {
    font-family: 'Heebo', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 2px;
    color: var(--forge-muted);
}

/* ── גרסה בסרגל ── */
.version-tag {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #444;
    letter-spacing: 2px;
    direction: ltr;
    text-align: center;
    display: block;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# קבועים וברירות מחדל — מטרי + עברית
# ─────────────────────────────────────────────

DEFAULT_PRICE_LIST = [
    {"חומר": 'פרופיל מלבני 60×40×2 מ"מ',   "יחידה": "מ'",    "מחיר_ליחידה": 8.50},
    {"חומר": 'פרופיל מלבני 40×20×2 מ"מ',   "יחידה": "מ'",    "מחיר_ליחידה": 5.80},
    {"חומר": 'פרופיל ריבועי 40×40×2 מ"מ',  "יחידה": "מ'",    "מחיר_ליחידה": 7.20},
    {"חומר": 'פרופיל ריבועי 20×20×1.5 מ"מ',"יחידה": "מ'",    "מחיר_ליחידה": 3.90},
    {"חומר": 'מוט עגול ⌀16 מ"מ',            "יחידה": "מ'",    "מחיר_ליחידה": 4.20},
    {"חומר": 'מוט עגול ⌀10 מ"מ',            "יחידה": "מ'",    "מחיר_ליחידה": 2.50},
    {"חומר": 'פס שטוח 40×4 מ"מ',            "יחידה": "מ'",    "מחיר_ליחידה": 3.10},
    {"חומר": 'פלטת פלדה 5 מ"מ',             "יחידה": 'מ"ר',   "מחיר_ליחידה": 62.00},
    {"חומר": 'פלטת פלדה 3 מ"מ',             "יחידה": 'מ"ר',   "מחיר_ליחידה": 38.00},
    {"חומר": 'זווית פלדה 50×50×5 מ"מ',      "יחידה": "מ'",    "מחיר_ליחידה": 6.40},
    {"חומר": 'פח 1.5 מ"מ',                  "יחידה": 'מ"ר',   "מחיר_ליחידה": 28.00},
    {"חומר": 'חוט ריתוך (לק"ג)',            "יחידה": 'ק"ג',   "מחיר_ליחידה": 5.50},
]

# נתוני הדגמה — שער ברזל קישוטי 200×180 ס"מ
FALLBACK_AI_RESPONSE = {
    "תיאור_פרויקט": 'שער ברזל קישוטי — רוחב 200 ס"מ × גובה 180 ס"מ, עם 9 מוטות אנכיים',
    "פריטים": [
        {
            "חומר": 'פרופיל מלבני 60×40×2 מ"מ',
            "כמות": 7.6,
            "יחידה": "מ'",
            "הערות": '2 עמודים (1.8 מ׳ כ"א) + עליון ותחתון (2 מ׳ כ"א) + חוצה (2 מ׳)',
        },
        {
            "חומר": 'פרופיל ריבועי 40×40×2 מ"מ',
            "כמות": 4.0,
            "יחידה": "מ'",
            "הערות": '2 חוצי אמצע אופקיים × 2 מ׳ כ"א',
        },
        {
            "חומר": 'מוט עגול ⌀16 מ"מ',
            "כמות": 16.2,
            "יחידה": "מ'",
            "הערות": '9 מוטות אנכיים קישוטיים × 1.8 מ׳ כ"א',
        },
        {
            "חומר": 'פס שטוח 40×4 מ"מ',
            "כמות": 4.0,
            "יחידה": "מ'",
            "הערות": '2 פסי תמיכה לקישוט × 2 מ׳ כ"א',
        },
        {
            "חומר": 'חוט ריתוך (לק"ג)',
            "כמות": 1.5,
            "יחידה": 'ק"ג',
            "הערות": "צריכת ריתוך משוערת לפי מספר הצמתים",
        },
    ],
}

# פרומפט מערכת לבינה המלאכותית — עברית + מטרי בלבד
VISION_SYSTEM_PROMPT = """
אתה מהנדס ייצור ומעריך עלויות מומחה בתחום עבודות מתכת ונפחות.
המשתמש יספק לך סקיצה מצוירת ביד או שרטוט טכני של פרויקט מתכת.

המשימה שלך:
1. נתח את השרטוט בקפידה וזהה כל אלמנט מבני וקישוטי.
2. התאם כל אלמנט לפריט הקרוב ביותר ברשימת המחירים שסופקה.
3. העריך כמויות ריאליסטיות — אורך במטרים (מ'), שטח במ"ר, משקל בק"ג — לפי המידות בשרטוט.
4. כל המידות הן מטריות בלבד: מטרים (מ') וסנטימטרים (ס"מ). אין להשתמש ביחידות אינצ' או רגל.
5. החזר JSON תקני בלבד — ללא markdown, ללא הסברים — לפי הסכימה הבאה:

{
  "תיאור_פרויקט": "<תיאור חד-שורתי בעברית>",
  "פריטים": [
    {
      "חומר":   "<שם מדויק מרשימת המחירים>",
      "כמות":   <מספר חיובי>,
      "יחידה":  "<יחידה מרשימת המחירים>",
      "הערות":  "<הנמקה קצרה בעברית>"
    }
  ]
}

רשימת המחירים:
{price_list}

כללים:
- השתמש רק בחומרים מרשימת המחירים.
- כמויות — מספרים חיוביים, עם הפרזה קלה (5-10%) לחשבון הפסדי חיתוך.
- שדה הערות — עברית בלבד.
- מידות לא ברורות — הנח הנחה סבירה וציין אותה.
"""


# ─────────────────────────────────────────────
# אתחול מצב סשן
# ─────────────────────────────────────────────
if "price_list_df" not in st.session_state:
    st.session_state.price_list_df = pd.DataFrame(DEFAULT_PRICE_LIST)
if "extracted_items" not in st.session_state:
    st.session_state.extracted_items = None
if "project_desc" not in st.session_state:
    st.session_state.project_desc = ""
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False


# ─────────────────────────────────────────────
# פונקציות עזר
# ─────────────────────────────────────────────
def encode_image_base64(pil_image: Image.Image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def price_list_as_text(df: pd.DataFrame) -> str:
    lines = []
    for _, row in df.iterrows():
        lines.append(f"- {row['חומר']} | {row['יחידה']} | ₪{row['מחיר_ליחידה']:.2f}")
    return "\n".join(lines)


def call_vision_ai(
    pil_image: Image.Image,
    api_key: str,
    provider: str,
    df_prices: pd.DataFrame,
) -> dict:
    """
    שולח את התמונה לבינה מלאכותית ומחזיר BOM בעברית.
    מחזיר נתוני הדגמה אם אין מפתח API.
    תומך: openai (GPT-4o), gemini (Gemini 1.5 Flash).
    """
    if not api_key:
        return FALLBACK_AI_RESPONSE

    pl_text = price_list_as_text(df_prices)
    system  = VISION_SYSTEM_PROMPT.replace("{price_list}", pl_text)
    b64     = encode_image_base64(pil_image)

    try:
        if provider == "openai":
            from openai import OpenAI
            client   = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        {"type": "text",
                         "text": "נתח את שרטוט עבודת המתכת הזו והחזר JSON של רשימת החומרים."},
                    ]},
                ],
                max_tokens=1500,
                temperature=0.2,
            )
            raw = response.choices[0].message.content

        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model    = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system,
            )
            response = model.generate_content([
                "נתח את שרטוט עבודת המתכת הזו והחזר JSON של רשימת החומרים.",
                pil_image,
            ])
            raw = response.text

        else:
            return FALLBACK_AI_RESPONSE

        # הסרת גדרות markdown אם קיימות
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)

    except Exception as exc:
        st.warning(f"קריאת ה-AI נכשלה ({exc}). נטענים נתוני הדגמה.")
        return FALLBACK_AI_RESPONSE


def calculate_costs(items_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    """חיבור BOM עם מחירים וחישוב עלות לשורה."""
    price_map = {
        row["חומר"]: row["מחיר_ליחידה"]
        for _, row in price_df.iterrows()
    }
    df = items_df.copy()
    df["מחיר_ליחידה"] = df["חומר"].map(price_map).fillna(0.0)
    df["עלות_שורה"]   = (df["כמות"] * df["מחיר_ליחידה"]).round(2)
    return df


# ─────────────────────────────────────────────
# סרגל צד — הגדרות
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-family:\'Heebo\',sans-serif;font-weight:700;font-size:1.3rem;'
        'color:var(--forge-white);margin:0 0 4px 0;">⚙ הגדרות</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="accent-line"></div>', unsafe_allow_html=True)

    st.markdown("**ספק בינה מלאכותית**")
    provider = st.selectbox(
        "ספק",
        ["הדגמה (ללא מפתח)", "openai", "gemini"],
        label_visibility="collapsed",
    )
    api_key = ""
    if provider != "הדגמה (ללא מפתח)":
        api_key = st.text_input(
            "מפתח API", type="password", placeholder="הדבק את מפתח ה-API שלך…"
        )

    st.markdown("---")
    st.markdown("**גורם פסולת / גזירה**")
    waste_pct = st.slider(
        "אחוז שיוסף לסכום הביניים", min_value=0, max_value=30, value=10, step=1
    )

    st.markdown("---")
    st.markdown("**סמל מטבע**")
    currency = st.text_input("סמל", value="₪", max_chars=3)

    st.markdown(
        '<span class="version-tag">METALWORK BOM CALCULATOR v1.0 | RTL</span>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# כותרת ראשית
# ─────────────────────────────────────────────
st.markdown(
    '<p class="forge-title-heb">⚙ מחשבון BOM ועלויות לנפחות ועבודות מתכת</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="forge-subtitle">העלאת שרטוט ← חילוץ חומרים ← עריכה ← סיכום עלויות</p>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="forge-divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# לשוניות ראשיות
# ─────────────────────────────────────────────
tab_prices, tab_upload, tab_review, tab_summary = st.tabs([
    "📋  רשימת מחירים",
    "📐  העלאת שרטוט",
    "✏️  עריכה ואישור",
    "💰  סיכום עלויות",
])

UNIT_OPTIONS = ["מ'", 'מ"ר', 'ק"ג', "יחידה"]


# ══════════════════════════════════════════════
# לשונית 1 — רשימת מחירים
# ══════════════════════════════════════════════
with tab_prices:
    st.markdown('<span class="step-badge">שלב 1</span>', unsafe_allow_html=True)
    st.markdown("### הגדרת רשימת מחירי חומרים")
    st.markdown(
        "ערוך את הטבלה להלן כך שתתאים למחירי הספק שלך. "
        "ניתן להוסיף שורות, למחוק ולשנות יחידות. "
        "הבינה המלאכותית תשתמש ברשימה זו לזיהוי החומרים בשרטוט."
    )

    edited_df = st.data_editor(
        st.session_state.price_list_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "חומר":         st.column_config.TextColumn("חומר / פרופיל",    width="large"),
            "יחידה":        st.column_config.SelectboxColumn("יחידה", options=UNIT_OPTIONS, width="small"),
            "מחיר_ליחידה": st.column_config.NumberColumn(
                "מחיר ליחידה (₪)", format="%.2f", min_value=0.0, width="small"
            ),
        },
        key="price_editor",
    )
    st.session_state.price_list_df = edited_df

    if st.button("↺  איפוס לברירת מחדל"):
        st.session_state.price_list_df = pd.DataFrame(DEFAULT_PRICE_LIST)
        st.rerun()


# ══════════════════════════════════════════════
# לשונית 2 — העלאת שרטוט וניתוח
# ══════════════════════════════════════════════
with tab_upload:
    st.markdown('<span class="step-badge">שלב 2</span>', unsafe_allow_html=True)
    st.markdown("### העלאת שרטוט או סקיצה")

    uploaded_file = st.file_uploader(
        "גרור ושחרר קובץ PNG / JPG של הפרויקט",
        type=["png", "jpg", "jpeg"],
        help="סקיצות מצוירות ביד, ייצוא CAD, או צילום של שרטוט טכני — הכל מתאים.",
    )

    if uploaded_file:
        pil_img = Image.open(uploaded_file)
        col_img, col_info = st.columns([1, 1])

        with col_img:
            st.image(pil_img, caption="השרטוט שהועלה", use_container_width=True)

        with col_info:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">שם קובץ</div>
                    <div style="font-family:'Share Tech Mono',monospace;font-size:0.85rem;
                                color:var(--forge-text);margin-top:4px;
                                direction:ltr;text-align:left;">
                        {uploaded_file.name}
                    </div>
                    <br>
                    <div class="metric-label">רזולוציה</div>
                    <div style="font-family:'Share Tech Mono',monospace;font-size:0.85rem;
                                color:var(--forge-text);margin-top:4px;
                                direction:ltr;text-align:left;">
                        {pil_img.width} × {pil_img.height} px
                    </div>
                    <br>
                    <div class="metric-label">פריטים ברשימת המחירים</div>
                    <div class="metric-value" style="font-size:1.5rem;">
                        {len(st.session_state.price_list_df)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            analyse_btn = st.button("🔍  ניתוח השרטוט")

        if analyse_btn:
            real_provider = provider if provider != "הדגמה (ללא מפתח)" else "demo"
            with st.spinner("שולח את השרטוט לבינה המלאכותית…"):
                result = call_vision_ai(
                    pil_img, api_key, real_provider, st.session_state.price_list_df
                )

            st.session_state.project_desc = result.get("תיאור_פרויקט", "")
            items = result.get("פריטים", [])
            if items:
                st.session_state.extracted_items = pd.DataFrame(items)
                st.session_state.analysis_done = True
                st.success(
                    f"✅  חולצו {len(items)} פריטים. עבור ל**עריכה ואישור** לאמת את התוצאות."
                )
            else:
                st.error("לא ניתן היה לחלץ פריטים. בדוק את התמונה או מפתח ה-API.")

    else:
        st.info("👆  העלה שרטוט למעלה ולאחר מכן לחץ על **ניתוח השרטוט**.")
        st.markdown("_אין תמונה? לחץ על הכפתור למטה לטעינת נתוני הדגמה של שער ברזל._")

        if st.button("▶  טעינת נתוני הדגמה (ללא תמונה)"):
            result = FALLBACK_AI_RESPONSE
            st.session_state.project_desc    = result["תיאור_פרויקט"]
            st.session_state.extracted_items = pd.DataFrame(result["פריטים"])
            st.session_state.analysis_done   = True
            st.success("נתוני הדגמה נטענו. עבור ל**עריכה ואישור**.")


# ══════════════════════════════════════════════
# לשונית 3 — עריכה ואישור
# ══════════════════════════════════════════════
with tab_review:
    st.markdown('<span class="step-badge">שלב 3</span>', unsafe_allow_html=True)
    st.markdown("### עריכה ואישור רשימת החומרים")

    if not st.session_state.analysis_done or st.session_state.extracted_items is None:
        st.info("אין נתונים עדיין — עבור ל**העלאת שרטוט** והפעל את הניתוח תחילה.")
    else:
        if st.session_state.project_desc:
            st.markdown(
                f"""
                <div class="ai-interp-box">
                    <div class="ai-interp-label">פרשנות הבינה המלאכותית</div>
                    <div style="font-family:'Heebo',sans-serif;font-size:1rem;
                                color:var(--forge-text);margin-top:4px;">
                        {st.session_state.project_desc}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        all_materials = list(st.session_state.price_list_df["חומר"])

        review_df = st.data_editor(
            st.session_state.extracted_items,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "חומר": st.column_config.SelectboxColumn(
                    "חומר", options=all_materials, width="large"
                ),
                "כמות": st.column_config.NumberColumn(
                    "כמות", format="%.2f", min_value=0.0, width="small"
                ),
                "יחידה": st.column_config.SelectboxColumn(
                    "יחידה", options=UNIT_OPTIONS, width="small"
                ),
                "הערות": st.column_config.TextColumn("הערות / הנחות", width="large"),
            },
            key="review_editor",
        )
        st.session_state.extracted_items = review_df

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅  אישור וחישוב עלויות"):
            st.success("הפריטים אושרו! עבור ל**סיכום עלויות** לראות את הפירוט.")


# ══════════════════════════════════════════════
# לשונית 4 — סיכום עלויות
# ══════════════════════════════════════════════
with tab_summary:
    st.markdown('<span class="step-badge">שלב 4</span>', unsafe_allow_html=True)
    st.markdown("### סיכום עלויות ואומדן")

    if not st.session_state.analysis_done or st.session_state.extracted_items is None:
        st.info("אין נתונים עדיין — השלם את שלבים 1–3 תחילה.")
    else:
        costed       = calculate_costs(
            st.session_state.extracted_items,
            st.session_state.price_list_df,
        )
        subtotal     = costed["עלות_שורה"].sum()
        waste_amount = subtotal * (waste_pct / 100.0)
        grand_total  = subtotal + waste_amount

        # ── שלושה כרטיסי KPI ──
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">סכום ביניים (חומרים)</div>
                    <div class="metric-value">{currency}{subtotal:,.2f}</div>
                    <div class="metric-sub">{len(costed)} פריטים</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"""
                <div class="metric-card" style="border-right-color:var(--forge-amber);">
                    <div class="metric-label">פסולת / גזירה ({waste_pct}%)</div>
                    <div class="metric-value" style="color:var(--forge-steel);">
                        {currency}{waste_amount:,.2f}
                    </div>
                    <div class="metric-sub">שנה בסרגל הצד</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"""
                <div class="total-block">
                    <div class="metric-label">⚡ סה"כ אומדן</div>
                    <div class="total-value">{currency}{grand_total:,.2f}</div>
                    <div class="metric-sub">כולל {waste_pct}% פסולת</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── פירוט שורות ──
        st.markdown("#### פירוט עלות לפי פריט")
        display_df = costed[
            ["חומר", "כמות", "יחידה", "מחיר_ליחידה", "עלות_שורה", "הערות"]
        ].copy()
        display_df.columns = ["חומר", "כמות", "יחידה", "מחיר ליחידה", "עלות שורה", "הערות"]
        display_df["מחיר ליחידה"] = display_df["מחיר ליחידה"].map(lambda x: f"{currency}{x:.2f}")
        display_df["עלות שורה"]   = display_df["עלות שורה"].map(lambda x: f"{currency}{x:.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # ── גרף עמודות ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### התפלגות עלות לפי חומר")
        chart_data = costed[["חומר", "עלות_שורה"]].set_index("חומר")
        st.bar_chart(chart_data, use_container_width=True, height=280, color="#ff6a00")

        # ── טבלת סיכום ויזואלית ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="background:var(--forge-panel);border:1px solid var(--forge-border);
                        padding:1.4rem 2rem;border-radius:2px;direction:rtl;text-align:right;">
                <table style="width:100%;border-collapse:collapse;direction:rtl;">
                    <tr>
                        <td style="color:var(--forge-muted);font-size:0.9rem;padding:8px 0;">
                            סכום ביניים
                        </td>
                        <td style="font-family:'Share Tech Mono',monospace;
                                   color:var(--forge-text);text-align:left;direction:ltr;">
                            {currency}{subtotal:,.2f}
                        </td>
                    </tr>
                    <tr>
                        <td style="color:var(--forge-muted);font-size:0.9rem;padding:8px 0;">
                            פסולת / גזירה ({waste_pct}%)
                        </td>
                        <td style="font-family:'Share Tech Mono',monospace;
                                   color:var(--forge-steel);text-align:left;direction:ltr;">
                            + {currency}{waste_amount:,.2f}
                        </td>
                    </tr>
                    <tr style="border-top:2px solid var(--forge-spark);">
                        <td style="color:var(--forge-white);font-weight:700;
                                   font-size:1.1rem;padding:12px 0;">
                            סה"כ אומדן פרויקט
                        </td>
                        <td style="font-family:'Bebas Neue',sans-serif;font-size:2.2rem;
                                   color:var(--forge-green);text-align:left;direction:ltr;">
                            {currency}{grand_total:,.2f}
                        </td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── ייצוא CSV (UTF-8 BOM לתמיכה ב-Excel) ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ייצוא נתונים")

        export_df = costed.copy()
        export_df['גורם_פסולת_%'] = waste_pct
        export_df['סכום_ביניים']  = subtotal
        export_df['סכום_פסולת']   = waste_amount
        export_df['סה"כ_אומדן']   = grand_total

        csv_bytes = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇  הורדת CSV",
            data=csv_bytes,
            file_name="bom_נפחות.csv",
            mime="text/csv",
        )
