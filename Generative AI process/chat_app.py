import streamlit as st
import pandas as pd
from agent import answer_question
from db import get_dynamic_schema
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io

# Helper function to create PDF
def create_pdf(question, summary, data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("helvetica", 'B', 20)
    pdf.set_text_color(15, 23, 42) # Dark Slate
    pdf.cell(0, 15, "Executive Business Briefing", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(5)
    
    # Question Section
    pdf.set_font("helvetica", 'B', 12)
    pdf.set_text_color(99, 102, 241) # Indigo
    pdf.cell(0, 10, f"Inquiry: {question}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    
    # Summary Section
    pdf.set_font("helvetica", 'B', 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "Executive Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", '', 11)
    pdf.multi_cell(0, 7, summary)
    pdf.ln(10)
    
    # Data Table Section
    if data:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, "Supporting Data", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 9)
        
        df = pd.DataFrame(data)
        # Simple table rendering
        col_width = pdf.epw / len(df.columns)
        line_height = pdf.font_size * 2
        
        # Headers
        pdf.set_fill_color(241, 245, 249)
        for col in df.columns:
            pdf.multi_cell(col_width, line_height, str(col), border=1, align='C', fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(line_height)
        
        # Rows
        for i, row in df.iterrows():
            for val in row:
                pdf.multi_cell(col_width, line_height, str(val), border=1, align='C', new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.ln(line_height)

    return bytes(pdf.output())

# Helper function to intelligently visualize data
def auto_visualize(data):
    if not data or len(data) == 0:
        return
    
    df = pd.DataFrame(data)
    
    # Check for visualizable columns
    cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    non_numeric_cols = [c for c in cols if c not in numeric_cols]
    
    if not numeric_cols:
        return # Nothing to chart

    with st.expander("📊 Data Visualization", expanded=True):
        # Case 1: Time Series (Trend Line)
        time_keywords = ['month', 'year', 'date', 'day', 'period']
        time_col = next((c for c in non_numeric_cols if any(k in c.lower() for k in time_keywords)), None)
        
        if time_col and len(df) > 1:
            st.write(f"**Trend Analysis by {time_col}**")
            chart_data = df.set_index(time_col)[numeric_cols]
            st.line_chart(chart_data)
        
        # Case 2: Categorical (Bar Chart)
        elif non_numeric_cols:
            cat_col = non_numeric_cols[0]
            st.write(f"**Comparative Analysis by {cat_col}**")
            chart_data = df.set_index(cat_col)[numeric_cols]
            st.bar_chart(chart_data)
        
        # Case 3: Just numbers
        else:
            st.bar_chart(df[numeric_cols])

# Set page config
st.set_page_config(
    page_title="InsightEngine | Enterprise AI Data Agent",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Premium UI styling with custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Global font override */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header Gradient Container */
    .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        text-align: center;
        position: relative;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.025em;
        background: linear-gradient(to right, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-top: 0.5rem;
        margin-bottom: 0;
        font-weight: 400;
    }
    
    /* Chat history styling */
    .chat-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    .sql-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #818cf8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .summary-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #a78bfa;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Input borders */
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Control Panel
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    st.markdown("Manage application configuration and inspect metadata.")
    
    # Clear conversation history
    if st.button("🗑️ Clear Chat History", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

    # Clear Engine Cache
    if st.button("🔄 Clear Engine Cache", use_container_width=True, type="secondary"):
        from agent import sql_cache, explanation_cache
        with sql_cache.lock:
            sql_cache.cache.clear()
        with explanation_cache.lock:
            explanation_cache.cache.clear()
        st.toast("Internal SQL & Explanation caches cleared!")
        
    st.markdown("---")
    
    st.markdown("### 📋 Database Schema")
    with st.expander("Inspect Analytics Tables", expanded=True):
        st.markdown(f"```\n{get_dynamic_schema().strip()}\n```")
        
    st.markdown("---")
    st.markdown("🟢 **Performance Engine: Active**")
    st.markdown("- Thread-safe LRU SQL caching")
    st.markdown("- Explanation result caching")
    st.markdown("- Connection pool & pre-ping")

# Custom header in main content
st.markdown("""
<div class="header-container">
    <div class="header-title">📊 InsightEngine</div>
    <div class="header-subtitle">Enterprise AI Data Agent: A self-healing, agentic system that translates natural language into verified SQL, real-time visualizations, and executive-ready reporting.</div>
</div>
""", unsafe_allow_html=True)

# Suggested Questions / Quick Actions
st.markdown("### 💡 Quick Insights")
cols = st.columns(3)
suggestions = [
    "Who are our top 5 customers?",
    "Compare Profit vs. Sales by Region",
    "Which shipping mode is most profitable?"
]

selected_suggestion = None
for i, suggestion in enumerate(suggestions):
    if cols[i % 3].button(suggestion, use_container_width=True):
        selected_suggestion = suggestion

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown('<div class="sql-label">💻 Executed SQL Query:</div>', unsafe_allow_html=True)
            if msg.get("status") == "self_corrected":
                st.info(f"✨ **Self-Healing Active:** The agent detected a database error and automatically corrected the SQL (Attempts: {msg.get('attempts', 1)})")
            st.code(msg["sql"], language="sql")
            
            # Re-render visualization from history
            if msg.get("data"):
                auto_visualize(msg["data"])

            st.markdown('<div class="summary-label">📝 Executive Summary:</div>', unsafe_allow_html=True)
            st.markdown(msg["summary"])
            
            # PDF Export Button
            pdf_bytes = create_pdf(msg.get("content", "Analysis"), msg["summary"], msg.get("data"))
            st.download_button(
                label="📄 Download Executive Briefing (PDF)",
                data=pdf_bytes,
                file_name=f"Executive_Briefing_{idx}.pdf",
                mime="application/pdf",
                key=f"pdf_hist_{idx}"
            )

# Chat input
input_question = st.chat_input("Ask a business question (e.g., 'Which region has the highest profit?')")

# Prioritize suggestion if clicked, otherwise use manual input
question = selected_suggestion if selected_suggestion else input_question

if question:
    # Display and record user question
    st.chat_message("user").write(question)
    st.session_state.messages.append({"role": "user", "content": question})
    
    # Execute query
    with st.chat_message("assistant"):
        with st.spinner("Analyzing database and generating executive summary..."):
            try:
                res = answer_question(question)
                
                st.markdown('<div class="sql-label">💻 Executed SQL Query:</div>', unsafe_allow_html=True)
                if res.get("status") == "self_corrected":
                    st.info(f"✨ **Self-Healing Active:** The agent detected a database error and automatically corrected the SQL (Attempts: {res.get('attempts')})")
                st.code(res["sql"], language="sql")
                
                # Intelligent Visualization
                if res.get("data"):
                    auto_visualize(res["data"])

                st.markdown('<div class="summary-label">📝 Executive Summary:</div>', unsafe_allow_html=True)
                st.markdown(res["summary"])
                
                # PDF Export Button (Real-time)
                pdf_bytes_new = create_pdf(question, res["summary"], res.get("data"))
                st.download_button(
                    label="📄 Download Executive Briefing (PDF)",
                    data=pdf_bytes_new,
                    file_name=f"Executive_Briefing_New.pdf",
                    mime="application/pdf",
                    key="pdf_new"
                )
                
                # Append to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "sql": res["sql"],
                    "summary": res["summary"],
                    "data": res.get("data"),
                    "status": res.get("status"),
                    "attempts": res.get("attempts")
                })
                
            except Exception as e:
                st.error(f"Error executing request: {str(e)}")
