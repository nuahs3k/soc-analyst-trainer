import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import requests

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
AI_MODE = os.getenv("AI_MODE", "online").lower()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Try to import OpenAI only if online mode
client = None
if AI_MODE == "online":
    try:
        from openai import OpenAI
        if not OPENAI_KEY:
            st.warning("⚠️ OpenAI API key not found. Online mode will not work.")
        else:
            client = OpenAI(api_key=OPENAI_KEY)
    except ImportError:
        st.warning("⚠️ OpenAI library not installed. Install with 'pip install openai'.")

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="SOC Analyst AI Trainer", page_icon="🧠", layout="wide")
st.title("🧠 SOC Analyst AI Trainer")
st.markdown("Learn to analyze and respond to security alerts — online or offline!")

# Sidebar settings
st.sidebar.header("⚙️ Settings")
alert_type = st.sidebar.selectbox("Alert Type", ["General", "Network", "Login", "Malware", "DNS", "Web", "Cloud"])
ai_mode = st.sidebar.radio("Select AI Mode", ["Online (OpenAI)", "Offline (Ollama)"])
save_results = st.sidebar.checkbox("💾 Save Results", True)
model_choice = st.sidebar.text_input("Offline Model (for Ollama)", "llama3")

# Input area
user_input = st.text_area("🔍 Paste a suspicious log or alert here:", height=150)

# Prepare CSV
csv_file = "analysis_history.csv"
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
else:
    df = pd.DataFrame(columns=["timestamp", "mode", "alert_type", "input", "analysis", "learning_notes"])

# -----------------------------
# AI Analysis Function
# -----------------------------
def get_ai_analysis(prompt_text):
    # Offline mode
    if ai_mode.lower().startswith("offline"):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model_choice, "prompt": prompt_text},
                stream=False
            )
            return response.json().get("response", "No response from local model.")
        except Exception as e:
            return f"⚠️ Offline mode error: {e}"

    # Online mode
    else:
        if client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_text}],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"⚠️ Online mode error: {e}"
        else:
            return "⚠️ Online mode unavailable. OpenAI API key missing or library not installed."

# -----------------------------
# Run Analysis
# -----------------------------
if st.button("🚀 Analyze Log"):
    if user_input.strip():
        with st.spinner("Analyzing log..."):
            prompt = f"""
            You are a cybersecurity instructor AI helping students learn SOC analysis.
            Analyze this {alert_type} alert or log. Provide:
            1. A short summary of what’s happening.
            2. The potential threat or behavior type (phishing, brute force, data exfiltration, etc.).
            3. Severity rating (1–5).
            4. Recommended immediate response steps.
            5. Learning Notes: teach students what key indicators to look for in this log and why.

            Log:
            {user_input}
            """
            analysis = get_ai_analysis(prompt)
            st.subheader("🧩 AI Analysis Result")
            st.write(analysis)

            # Extract learning notes
            learn_start = analysis.find("Learning Notes")
            learning_notes = analysis[learn_start:] if learn_start != -1 else ""

            # Save results
            if save_results:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df = pd.concat([
                    df,
                    pd.DataFrame([{
                        "timestamp": timestamp,
                        "mode": ai_mode,
                        "alert_type": alert_type,
                        "input": user_input,
                        "analysis": analysis,
                        "learning_notes": learning_notes
                    }])
                ], ignore_index=True)
                df.to_csv(csv_file, index=False)
            st.success("✅ Analysis complete. Scroll below for learning insights.")
    else:
        st.warning("Please enter a log or alert first.")

# -----------------------------
# Show Previous Analyses
# -----------------------------
st.markdown("---")
st.subheader("📊 Previous Analyses")
if not df.empty:
    st.dataframe(df.tail(5), use_container_width=True)
else:
    st.info("No prior analyses yet — start by analyzing a log.")
