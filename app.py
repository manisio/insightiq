import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from dotenv import load_dotenv
import os
import io
import time
import random

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=gemini_api_key)

st.set_page_config(page_title="InsightIQ", page_icon="📊", layout="wide")

# ---------------- Session state defaults ----------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "show_splash" not in st.session_state:
    st.session_state.show_splash = True
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of dicts: question, code, result_type, result_text, error
if "df" not in st.session_state:
    st.session_state.df = None
if "df2" not in st.session_state:
    st.session_state.df2 = None
if "last_error_question" not in st.session_state:
    st.session_state.last_error_question = None


# ---------------- Theme ----------------
def apply_theme(theme):
    if theme == "dark":
        bg, text, card = "#0E1117", "#FAFAFA", "#1A1D24"
        accent1, accent2 = "#4C9AFF", "#9C6ADE"
        border_glow = "rgba(76, 154, 255, 0.35)"
        uploader_bg = "#161A23"
        uploader_bg_hover = "#1D2230"
    else:
        bg, text, card = "#FFFFFF", "#111111", "#F5F5F5"
        accent1, accent2 = "#2563EB", "#7C3AED"
        border_glow = "rgba(37, 99, 235, 0.25)"
        uploader_bg = "#F5F7FF"
        uploader_bg_hover = "#EBEFFF"

    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg};
        color: {text};
        transition: background-color 0.5s ease, color 0.5s ease;
    }}
    html, body,
    div[data-testid="stAppViewContainer"],
    div[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stBottomBlockContainer"],
    div[data-testid="stMain"],
    header[data-testid="stHeader"] {{
        background-color: {bg} !important;
        color: {text} !important;
    }}
    .stApp p, .stApp span, .stApp label, .stApp div,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stCaptionContainer"],
    div[data-testid="stRadio"] label span,
    div[data-testid="stFileUploaderDropzoneInstructions"] span,
    div[data-testid="stFileUploaderDropzoneInstructions"] small {{
        color: {text} !important;
    }}
    div[data-testid="stMetric"], div[data-testid="stExpander"] {{
        background: linear-gradient(135deg, {card} 0%, {card} 100%);
        border: 1px solid {border_glow};
        border-radius: 10px;
        padding: 8px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="stMetric"]:hover, div[data-testid="stExpander"]:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 16px {border_glow};
        border: 1px solid {accent1};
    }}
    div[data-testid="stMetricValue"] {{
        background: linear-gradient(90deg, {accent1}, {accent2});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }}
    .stButton button {{
        background: linear-gradient(90deg, {accent1}, {accent2});
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .stButton button:hover {{
        transform: scale(1.03);
        box-shadow: 0 4px 14px {border_glow};
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(90deg, {accent1}, {accent2});
        color: #FFFFFF !important;
        border-radius: 8px 8px 0 0;
    }}
    hr {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, {accent1}, {accent2});
        opacity: 0.6;
    }}
    div[data-testid="stFileUploaderDropzone"],
    div[data-testid="stFileUploader"] section {{
        background-color: {uploader_bg} !important;
        border: 2px dashed {accent1} !important;
        border-radius: 14px !important;
        transition: background-color 0.3s ease, border-color 0.3s ease;
    }}
    div[data-testid="stFileUploaderDropzone"]:hover,
    div[data-testid="stFileUploader"] section:hover {{
        background-color: {uploader_bg_hover} !important;
        border-color: {accent2} !important;
    }}
    div[data-testid="stFileUploaderDropzoneInstructions"] svg {{
        fill: {accent1} !important;
        color: {accent1} !important;
    }}
    div[data-testid="stFileUploader"] button {{
        background: linear-gradient(90deg, {accent1}, {accent2}) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {card} !important;
        border-right: 1px solid {border_glow};
        position: fixed !important;
        top: 0;
        left: 0;
        height: 100vh !important;
        z-index: 999999 !important;
        box-shadow: 10px 0 35px rgba(0, 0, 0, 0.45);
        border-radius: 0 18px 18px 0;
        transition: transform 0.3s ease, background-color 0.5s ease;
    }}
    section[data-testid="stSidebar"][aria-expanded="false"] {{
        transform: translateX(-100%);
    }}
    div[data-testid="stAppViewContainer"] > div.main,
    section[data-testid="stMain"] {{
        margin-left: 0 !important;
    }}
    .chat-bubble-user {{
        background: linear-gradient(90deg, {accent1}, {accent2});
        color: #FFFFFF;
        padding: 10px 14px;
        border-radius: 12px 12px 2px 12px;
        margin: 6px 0;
        display: inline-block;
        max-width: 90%;
    }}
    .chat-bubble-ai {{
        background-color: {card};
        border: 1px solid {border_glow};
        color: {text};
        padding: 10px 14px;
        border-radius: 12px 12px 12px 2px;
        margin: 6px 0;
        display: inline-block;
        max-width: 90%;
    }}
    </style>
    """, unsafe_allow_html=True)


def show_splash_screen():
    st.markdown("""
    <style>
    @keyframes fadeInScale {
        0% { opacity: 0; transform: scale(0.7); }
        60% { opacity: 1; transform: scale(1.05); }
        100% { opacity: 1; transform: scale(1); }
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
    }
    .splash-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        animation: fadeInScale 1s ease;
    }
    .splash-emoji {
        font-size: 90px;
        animation: pulse 1.5s ease-in-out infinite;
    }
    .splash-text {
        font-size: 34px;
        font-weight: 700;
        margin-top: 20px;
        background: linear-gradient(90deg, #4C9AFF, #9C6ADE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .splash-sub {
        font-size: 16px;
        color: #888;
        margin-top: 8px;
    }
    </style>
    <div class="splash-container">
        <div class="splash-emoji">🙏</div>
        <div class="splash-text">Welcome to InsightIQ</div>
        <div class="splash-sub">Turn CSVs into conversations...</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------- Helpers ----------------
def get_schema_info(df):
    schema = f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns.\n"
    schema += "Columns:\n"
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample_values = df[col].dropna().unique()[:3].tolist()
        schema += f"- {col} ({dtype}), sample values: {sample_values}\n"
    return schema


def read_any_file(uploaded_file):
    """Reads CSV or Excel based on file extension."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")


def detect_date_columns(df):
    """Detects date-like columns by name AND by attempting to parse content."""
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "year", "month", "day"])]
    if not date_cols:
        for c in df.select_dtypes(include="object").columns[:5]:
            try:
                sample = df[c].dropna().head(20)
                if len(sample) == 0:
                    continue
                parsed = pd.to_datetime(sample, errors="coerce")
                if parsed.notna().mean() > 0.8:
                    date_cols.append(c)
            except Exception:
                pass
    return date_cols


def call_gemini(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )
            return response.text
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise e


def generate_code(question, schema_info, history=None):
    history_context = ""
    if history:
        recent = history[-3:]
        history_context = "\nPrevious questions in this conversation (for context only):\n"
        for h in recent:
            history_context += f'- Q: "{h["question"]}"\n'

    prompt = f"""You are a data analysis assistant. You are given a pandas dataframe called df.

{schema_info}
{history_context}
Write Python code to answer this question: "{question}"

Rules:
- Use the variable name df to refer to the dataframe, it already exists
- Store the final answer in a variable called result
- If the answer is a chart, create it using matplotlib and store the figure in a variable called result
- Only output the Python code, no explanations, no markdown formatting, no backticks
- Do not import pandas or read any file, df is already loaded
- Do not use file I/O, network calls, or system commands
"""
    code = call_gemini(prompt).strip()
    code = code.replace("```python", "").replace("```", "").strip()
    return code


# A restricted set of builtins for exec — blocks file/network/system access
SAFE_BUILTINS = {
    "len": len, "range": range, "sum": sum, "min": min, "max": max,
    "sorted": sorted, "list": list, "dict": dict, "set": set, "tuple": tuple,
    "str": str, "int": int, "float": float, "bool": bool, "round": round,
    "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
    "abs": abs, "any": any, "all": all, "print": print,
}


def run_code(code, df):
    if not code or code.strip() == "":
        return None, "AI could not generate any code for this question. Try rephrasing it."

    plt_module = __import__("matplotlib.pyplot", fromlist=["plt"])
    local_vars = {"df": df.copy(), "pd": pd, "plt": plt_module}
    restricted_globals = {"__builtins__": SAFE_BUILTINS}
    try:
        exec(code, restricted_globals, local_vars)
        if "result" not in local_vars:
            return None, "Code ran but did not produce a result. Try rephrasing your question."
        return local_vars["result"], None
    except SyntaxError:
        return None, "AI generated invalid code. Please try rephrasing your question."
    except KeyError as e:
        return None, f"Column not found: {e}. Check the column names in Schema Info above."
    except Exception as e:
        return None, f"Error while running the analysis: {str(e)}"


def generate_auto_eda(schema_info, df, language="Hinglish"):
    numeric_summary = df.describe().to_string()
    missing_summary = df.isnull().sum().to_string()

    if language == "Hinglish":
        lang_instruction = "Write the summary in Hinglish (Hindi words written in English script, mixed naturally with English technical terms)."
    else:
        lang_instruction = "Write the summary in plain simple English."

    prompt = f"""You are a senior data analyst. Given this dataset information, write a short automatic EDA summary in 5-7 bullet points.

{lang_instruction}

{schema_info}

Numeric column statistics:
{numeric_summary}

Missing values per column:
{missing_summary}

Cover things like: data quality issues, interesting patterns, columns that need cleaning, any outliers you can infer from the stats, and 1-2 suggested questions the user could ask next.

Rules:
- Do NOT include any preamble or intro line like "Here is a summary" or "Here is a quick analysis"
- Start directly with the first bullet point
- Keep it concise, no long paragraphs"""

    try:
        return call_gemini(prompt)
    except Exception:
        return "AI is currently experiencing high demand. Please refresh and try again in a moment."


def generate_auto_charts(df):
    charts = []
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    date_cols = detect_date_columns(df)

    if categorical_cols and numeric_cols:
        try:
            top_cat = df[categorical_cols[0]].value_counts().head(8).reset_index()
            top_cat.columns = [categorical_cols[0], "count"]
            fig = px.bar(top_cat, x=categorical_cols[0], y="count",
                         title=f"Top {categorical_cols[0]} by Count",
                         color="count", color_continuous_scale="Blues")
            charts.append(fig)
        except Exception:
            pass

    if numeric_cols:
        try:
            fig = px.histogram(df, x=numeric_cols[0], nbins=30,
                                title=f"Distribution of {numeric_cols[0]}",
                                color_discrete_sequence=["#4C9AFF"])
            charts.append(fig)
        except Exception:
            pass

    if date_cols and numeric_cols:
        try:
            temp = df.copy()
            temp[date_cols[0]] = pd.to_datetime(temp[date_cols[0]], errors="coerce")
            trend = temp.groupby(temp[date_cols[0]].dt.to_period("M"))[numeric_cols[0]].sum().reset_index()
            trend[date_cols[0]] = trend[date_cols[0]].astype(str)
            fig = px.line(trend, x=date_cols[0], y=numeric_cols[0],
                           title=f"{numeric_cols[0]} Trend Over Time", markers=True)
            charts.append(fig)
        except Exception:
            pass

    return charts


def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def fig_to_png_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    return buf


# ---------------- App start ----------------
apply_theme(st.session_state.theme)

if st.session_state.show_splash:
    splash_placeholder = st.empty()
    with splash_placeholder.container():
        show_splash_screen()
    time.sleep(2.2)
    splash_placeholder.empty()
    st.session_state.show_splash = False
    st.rerun()

top_col1, top_col2 = st.columns([6, 1])
with top_col1:
    st.title("📊 InsightIQ")
    st.caption("Turn CSVs into conversations.")
with top_col2:
    icon = "☀️" if st.session_state.theme == "dark" else "🌙"
    if st.button(icon, key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.eda_language = st.radio(
        "AI response language", ["Hinglish", "English"],
        index=0 if st.session_state.get("eda_language", "Hinglish") == "Hinglish" else 1
    )

    st.divider()
    st.subheader("💬 Question History")
    if st.session_state.chat_history:
        for i, h in enumerate(reversed(st.session_state.chat_history[-10:])):
            st.caption(f"{len(st.session_state.chat_history) - i}. {h['question'][:40]}")
        if st.button("🗑️ Clear history"):
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.caption("No questions asked yet.")

    st.divider()
    st.caption("Built by Manish Joshi")

st.subheader("📁 Upload Data")
mode = st.radio("How many files?", ["Single file", "Two files (join/compare)"], horizontal=True)

if mode == "Single file":
    uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx", "xls"])
    uploaded_file_2 = None
else:
    col_a, col_b = st.columns(2)
    with col_a:
        uploaded_file = st.file_uploader("Upload first file", type=["csv", "xlsx", "xls"], key="file1")
    with col_b:
        uploaded_file_2 = st.file_uploader("Upload second file", type=["csv", "xlsx", "xls"], key="file2")

df = None
df2 = None

if mode == "Single file" and uploaded_file is not None:
    try:
        df = read_any_file(uploaded_file)
        if df.empty:
            st.error("Uploaded file is empty. Please upload a file with data.")
            st.stop()
        st.session_state["df"] = df
    except Exception as e:
        st.error(f"Could not read the file: {str(e)}")
        st.stop()

elif mode == "Two files (join/compare)" and uploaded_file is not None and uploaded_file_2 is not None:
    try:
        df1_raw = read_any_file(uploaded_file)
        df2_raw = read_any_file(uploaded_file_2)

        st.divider()
        st.subheader("📋 Preview: File 1 vs File 2")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.caption("File 1")
            st.dataframe(df1_raw.head(5))
        with col_p2:
            st.caption("File 2")
            st.dataframe(df2_raw.head(5))

        action = st.radio("What do you want to do?", ["Compare separately", "Join into one dataset"], horizontal=True)

        if action == "Compare separately":
            df = df1_raw
            df2 = df2_raw
        else:
            common_cols = list(set(df1_raw.columns) & set(df2_raw.columns))
            if not common_cols:
                st.error("No common column found between the two files to join on.")
                st.stop()
            join_col = st.selectbox("Select column to join on", common_cols)
            join_type = st.selectbox("Join type", ["inner", "left", "right", "outer"])
            df = pd.merge(df1_raw, df2_raw, on=join_col, how=join_type)
            st.success(f"Joined into a single dataset: {df.shape[0]} rows, {df.shape[1]} columns")

        st.session_state["df"] = df
    except Exception as e:
        st.error(f"Could not process the files: {str(e)}")
        st.stop()

if df is not None:
    st.divider()

    tab_names = ["🏠 Overview", "🧠 Auto EDA", "💬 Ask AI", "🧹 Clean Data"]
    if df2 is not None:
        tab_names.append("⚖️ Compare")

    tabs = st.tabs(tab_names)

    # ---------------- Overview ----------------
    with tabs[0]:
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])
        missing_pct = round(df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 1)
        col3.metric("Missing Values", int(df.isnull().sum().sum()), delta=f"{missing_pct}% of data", delta_color="inverse")

        st.subheader("📋 Data Preview")
        st.dataframe(df.head(10))
        st.download_button(
            "⬇️ Download current data as CSV",
            data=df_to_csv_bytes(df),
            file_name="insightiq_data.csv",
            mime="text/csv",
        )

        st.subheader("📈 Auto-Generated Charts")
        auto_charts = generate_auto_charts(df)
        if auto_charts:
            chart_cols = st.columns(2)
            for i, fig in enumerate(auto_charts):
                with chart_cols[i % 2]:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough suitable columns to auto-generate charts.")

        st.subheader("🔍 Schema Info (for AI)")
        with st.expander("View column details"):
            st.text(get_schema_info(df))

    # ---------------- Auto EDA ----------------
    with tabs[1]:
        eda_language = st.radio("Summary language", ["Hinglish", "English"], horizontal=True, key="eda_lang_tab")
        loading_messages = [
            "Reading your columns...",
            "Detecting patterns...",
            "Checking data quality...",
            "Almost done...",
        ]
        with st.spinner(random.choice(loading_messages)):
            eda_summary = generate_auto_eda(get_schema_info(df), df, eda_language)
        st.markdown(eda_summary)

    # ---------------- Ask AI (with chat history) ----------------
    with tabs[2]:
        st.caption("Pichle questions bhi context ke liye AI ko dikhaye jaate hain.")

        # Render chat history
        for h in st.session_state.chat_history:
            st.markdown(f'<div class="chat-bubble-user">🧑 {h["question"]}</div>', unsafe_allow_html=True)
            if h["error"]:
                st.error(h["error"])
                if st.button("🔁 Regenerate", key=f"regen_{h['id']}"):
                    with st.spinner("Retrying..."):
                        schema_info = get_schema_info(df)
                        new_code = generate_code(h["question"], schema_info, st.session_state.chat_history)
                        new_result, new_error = run_code(new_code, df)
                        h["code"] = new_code
                        if new_error:
                            h["error"] = new_error
                        else:
                            h["error"] = None
                            h["result_is_fig"] = hasattr(new_result, "savefig")
                            h["result_fig"] = new_result if h["result_is_fig"] else None
                            h["result_text"] = None if h["result_is_fig"] else str(new_result)
                    st.rerun()
            else:
                with st.expander("View generated code"):
                    st.code(h["code"], language="python")
                if h.get("result_is_fig") and h.get("result_fig") is not None:
                    st.pyplot(h["result_fig"])
                    st.download_button(
                        "⬇️ Download chart as PNG",
                        data=fig_to_png_bytes(h["result_fig"]),
                        file_name=f"chart_{h['id']}.png",
                        mime="image/png",
                        key=f"dl_{h['id']}",
                    )
                else:
                    st.markdown(f'<div class="chat-bubble-ai">🤖 {h["result_text"]}</div>', unsafe_allow_html=True)

        question = st.text_input("Ask something about your data", placeholder="e.g. Which city has the highest sales?", key="ask_ai_input")

        if st.button("Get Answer", type="primary") and question:
            with st.status("Working on your question...", expanded=True) as status:
                st.write("🔍 Understanding your question...")
                schema_info = get_schema_info(df)
                time.sleep(0.3)

                st.write("⚙️ Generating analysis code...")
                code = generate_code(question, schema_info, st.session_state.chat_history)
                time.sleep(0.3)

                st.write("▶️ Running the analysis...")
                result, error = run_code(code, df)
                time.sleep(0.2)

                if error:
                    status.update(label="Something went wrong", state="error", expanded=True)
                else:
                    status.update(label="Analysis complete!", state="complete", expanded=False)

            entry = {
                "id": len(st.session_state.chat_history) + 1,
                "question": question,
                "code": code,
                "error": error,
            }
            if not error:
                is_fig = hasattr(result, "savefig")
                entry["result_is_fig"] = is_fig
                entry["result_fig"] = result if is_fig else None
                entry["result_text"] = None if is_fig else str(result)

            st.session_state.chat_history.append(entry)
            st.rerun()

    # ---------------- Clean Data ----------------
    with tabs[3]:
        st.subheader("🧹 Data Cleaning Tools")
        cleaned_df = df.copy()

        st.markdown("**Missing values**")
        missing_cols = [c for c in df.columns if df[c].isnull().sum() > 0]
        if missing_cols:
            miss_action = st.radio(
                "What to do with missing values?",
                ["Do nothing", "Drop rows with any missing value", "Fill numeric with mean", "Fill numeric with 0", "Fill text with 'Unknown'"],
                horizontal=False,
            )
            if miss_action == "Drop rows with any missing value":
                cleaned_df = cleaned_df.dropna()
            elif miss_action == "Fill numeric with mean":
                num_cols = cleaned_df.select_dtypes(include="number").columns
                cleaned_df[num_cols] = cleaned_df[num_cols].fillna(cleaned_df[num_cols].mean())
            elif miss_action == "Fill numeric with 0":
                num_cols = cleaned_df.select_dtypes(include="number").columns
                cleaned_df[num_cols] = cleaned_df[num_cols].fillna(0)
            elif miss_action == "Fill text with 'Unknown'":
                text_cols = cleaned_df.select_dtypes(include="object").columns
                cleaned_df[text_cols] = cleaned_df[text_cols].fillna("Unknown")
        else:
            st.info("No missing values found. 🎉")

        st.markdown("**Duplicate rows**")
        dup_count = df.duplicated().sum()
        st.write(f"Found {dup_count} duplicate rows.")
        if dup_count > 0 and st.checkbox("Remove duplicate rows"):
            cleaned_df = cleaned_df.drop_duplicates()

        st.markdown("**Drop columns**")
        cols_to_drop = st.multiselect("Select columns to drop", df.columns.tolist())
        if cols_to_drop:
            cleaned_df = cleaned_df.drop(columns=cols_to_drop)

        st.markdown("**Rename a column**")
        rc1, rc2 = st.columns(2)
        with rc1:
            col_to_rename = st.selectbox("Column", ["(none)"] + df.columns.tolist())
        with rc2:
            new_name = st.text_input("New name")
        if col_to_rename != "(none)" and new_name:
            cleaned_df = cleaned_df.rename(columns={col_to_rename: new_name})

        st.divider()
        st.subheader("Preview after cleaning")
        st.write(f"Rows: {cleaned_df.shape[0]}  •  Columns: {cleaned_df.shape[1]}")
        st.dataframe(cleaned_df.head(10))

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "⬇️ Download cleaned data (CSV)",
                data=df_to_csv_bytes(cleaned_df),
                file_name="cleaned_data.csv",
                mime="text/csv",
            )
        with col_dl2:
            if st.button("✅ Use cleaned data for analysis"):
                st.session_state["df"] = cleaned_df
                st.success("Cleaned data is now active. Switch to other tabs to use it.")
                st.rerun()

    # ---------------- Compare ----------------
    if df2 is not None:
        with tabs[4]:
            st.subheader("⚖️ File 1 vs File 2")
            cmp_col1, cmp_col2 = st.columns(2)
            with cmp_col1:
                st.caption("File 1 Stats")
                st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
                st.dataframe(df.describe())
            with cmp_col2:
                st.caption("File 2 Stats")
                st.write(f"Rows: {df2.shape[0]}, Columns: {df2.shape[1]}")
                st.dataframe(df2.describe())

            numeric_cols_1 = df.select_dtypes(include="number").columns.tolist()
            numeric_cols_2 = df2.select_dtypes(include="number").columns.tolist()
            if numeric_cols_1 and numeric_cols_2:
                compare_df = pd.DataFrame({
                    "File 1": [df[numeric_cols_1[0]].sum()],
                    "File 2": [df2[numeric_cols_2[0]].sum()]
                }, index=[numeric_cols_1[0]])
                fig = px.bar(compare_df.T, title=f"Total {numeric_cols_1[0]} Comparison")
                st.plotly_chart(fig, use_container_width=True)

st.divider()
st.divider()
footer_col1, footer_col2 = st.columns(2)
with footer_col1:
    st.subheader("ℹ️ How it works")
    st.markdown("""
    1. **Upload** your CSV or Excel file
    2. Get an **automatic EDA** summary
    3. **Ask questions** in plain English or Hinglish (with chat memory)
    4. **Clean your data** with one click
    5. Get answers as text or downloadable charts
    """)
with footer_col2:
    st.subheader("👤 About")
    st.caption("Built by Manish Joshi")
    st.markdown("[GitHub](https://github.com/manisio) · [LinkedIn](https://linkedin.com/in/manishio) · [X](https://x.com/itsmanishio)")