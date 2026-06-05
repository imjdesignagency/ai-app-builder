"""
AI App Builder - Powered by DeepSeek
Deploy once. Build forever. No code required.
"""

import streamlit as st
from openai import OpenAI
import os
import re
from datetime import datetime

# Page config
st.set_page_config(
    page_title="AI App Builder | DeepSeek",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme
st.markdown("""
<style>
    .stApp { background: #0f1117; }
    .stButton > button { border-radius: 8px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'app_code' not in st.session_state:
    st.session_state.app_code = """# Your app will appear here
import streamlit as st

st.title("Ready to Build")
st.write("Describe your app in the chat!")
"""

if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0

if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = False

if 'show_settings' not in st.session_state:
    st.session_state.show_settings = True

# Client setup
def get_client():
    api_key = st.session_state.get('api_key') or os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# System prompt
SYSTEM_PROMPT = """You are an expert Streamlit app builder.

RULES:
1. ALWAYS output complete code between ```python and ``` markers
2. Include ALL imports at the top
3. Use st.session_state for state
4. Make UI professional with tabs, columns, sidebars
5. Return the ENTIRE app code every time
6. Make apps immediately runnable"""

def extract_code(content):
    match = re.search(r'```python\n(.*?)```', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    if 'import streamlit' in content:
        return content.strip()
    return None

def build_app(prompt, existing_code):
    client = get_client()
    if not client:
        return None, "Please set your API key first"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Current code:\n```python\n{existing_code}\n```\n\nRequest: {prompt}\n\nOutput the complete updated app between ```python and ``` markers."}
            ],
            temperature=0.4,
            max_tokens=4000
        )
        st.session_state.total_tokens += response.usage.total_tokens
        return extract_code(response.choices[0].message.content), None
    except Exception as e:
        return None, str(e)

def detect_features(code):
    features = []
    patterns = {
        "Tabs": "st.tabs",
        "Sidebar": "st.sidebar",
        "Charts": "st.bar_chart|st.line_chart|plotly",
        "AI Integration": "openai|deepseek|llm",
        "File Upload": "st.file_uploader",
        "Data Tables": "st.dataframe",
        "Forms": "st.form",
        "Metrics": "st.metric",
        "Maps": "st.map|folium",
        "Database": "sqlite|postgresql|supabase",
        "Caching": "@st.cache",
        "Auth": "password|login|authenticate"
    }
    for name, pattern in patterns.items():
        if re.search(pattern, code, re.IGNORECASE):
            features.append(name)
    return features

# Settings page
if st.session_state.show_settings:
    st.title("🤖 AI App Builder")
    st.caption("Powered by DeepSeek")
    st.markdown("### Build apps by chatting with AI")
    st.markdown("Describe what you want, and DeepSeek generates the complete app. No code needed.")
    st.divider()
    
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        placeholder="sk-...",
        value=st.session_state.get('api_key', '')
    )
    
    if api_key:
        st.session_state.api_key = api_key
        if st.button("Connect & Start Building", type="primary", use_container_width=True):
            try:
                test_client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                test_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": "Say ok"}],
                    max_tokens=5
                )
                st.session_state.api_key_set = True
                st.session_state.show_settings = False
                st.success("Connected!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")
    
    st.caption("Get your key at platform.deepseek.com")
    st.stop()

# Main interface
col1, col2 = st.columns([4, 6])

with col1:
    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if st.button("🆕 New", use_container_width=True):
            st.session_state.app_code = "import streamlit as st\n\nst.title('New App')\nst.write('Describe what to build!')"
            st.session_state.messages = []
            st.rerun()
    with btn2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with btn3:
        st.download_button("⬇️ Download", st.session_state.app_code, 
                          file_name="my_app.py", mime="text/plain", use_container_width=True)
    
    st.divider()
    
    chat_container = st.container(height=500)
    
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Describe the app you want to build!\n\nExamples:\n- Build a job application tracker\n- Create a dashboard with charts\n- Build a resume analyzer")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    st.divider()
    
    prompt = st.chat_input("Describe what to build or change...")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Building..."):
            new_code, error = build_app(prompt, st.session_state.app_code)
            
            if error:
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {error}"})
            elif new_code:
                st.session_state.app_code = new_code
                features = detect_features(new_code)
                lines = len(new_code.split('\n'))
                msg = f"App updated! ({lines} lines)\n\nFeatures: {', '.join(features) if features else 'Basic app'}"
                st.session_state.messages.append({"role": "assistant", "content": msg})
        
        st.rerun()

with col2:
    tab1, tab2 = st.tabs(["Preview", "Code"])
    
    with tab1:
        st.caption("Your app preview:")
        features = detect_features(st.session_state.app_code)
        lines = len(st.session_state.app_code.split('\n'))
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Lines", lines)
        m2.metric("Features", len(features))
        m3.metric("Tokens", f"{st.session_state.total_tokens:,}")
        
        if features:
            st.write("**Features:**")
            st.write(", ".join(f"`{f}`" for f in features))
        
        st.divider()
        st.caption("Run the downloaded file to see the actual app")
        
        with st.container(border=True):
            title_match = re.search(r'st\.title\(["\'](.*?)["\']\)', st.session_state.app_code)
            if title_match:
                st.markdown(f"## {title_match.group(1)}")
            writes = re.findall(r'st\.write\(["\'](.*?)["\']\)', st.session_state.app_code)
            for w in writes[:5]:
                st.write(w)
    
    with tab2:
        st.download_button("⬇️ Download app.py", st.session_state.app_code,
                          file_name="my_app.py", use_container_width=True)
        st.code(st.session_state.app_code, language="python", line_numbers=True)

# Status bar
st.divider()
c1, c2, c3 = st.columns(3)
c1.caption(f"Messages: {len(st.session_state.messages)}")
c2.caption(f"Tokens: {st.session_state.total_tokens:,}")
c3.caption(f"Est. cost: ${(st.session_state.total_tokens / 1000000) * 0.27:.4f}")
