import streamlit as st
from supabase_client import supabase
from auth import login_user

st.set_page_config(page_title="LawLM — Login", page_icon="⚖️", layout="centered")

# ----------------------------------------------------------------------------
# CSS -- same dark/gold design language as chatbot.py. Purely visual: no
# Supabase call, session_state key, or control-flow line below was changed.
# ----------------------------------------------------------------------------
st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
    --bg:#0a0a09;
    --panel-bg:#121211;
    --border:#242320;
    --border-soft:#1a1917;
    --gold:#e8b923;
    --gold-soft:rgba(232,185,35,0.12);
    --gold-softer:rgba(232,185,35,0.06);
    --text-hi:#f2f0e6;
    --text-mid:#96948a;
    --text-low:#5c5a52;
}
html, body, [data-testid="stAppViewContainer"], .stApp{
    background:var(--bg) !important;
    color:var(--text-hi);
    font-family:'Inter',sans-serif;
}
[data-testid="stHeader"]{ background:transparent; }
[data-testid="stToolbar"]{ display:none; }
footer{ display:none; }
[data-testid="stSidebar"]{ display:none; }
[data-testid="stSidebarNav"]{ display:none; }
[data-testid="collapsedControl"]{ display:none; }
.block-container{ max-width:420px !important; padding-top:8vh !important; }
.lx-logo-row{ display:flex; flex-direction:column; align-items:center; gap:10px; margin-bottom:1.6rem; }
.lx-logo-badge{
    width:52px; height:52px; border-radius:14px; background:var(--gold-soft);
    border:1px solid var(--gold-soft); display:flex; align-items:center; justify-content:center;
    color:var(--gold);
}
.lx-logo-badge svg{ width:28px; height:28px; }
.lx-brand-name{ font-weight:700; font-size:1.3rem; color:var(--text-hi); }
.lx-brand-sub{ font-family:'JetBrains Mono',monospace; font-size:0.65rem; letter-spacing:.1em;
    color:var(--text-low); text-transform:uppercase; }
h1#login-form, h1#signup-form{
    text-align:center; font-size:1.3rem !important; font-weight:700 !important;
    color:var(--text-hi) !important; margin-bottom:1.4rem !important;
}
[data-testid="stForm"]{
    background:var(--panel-bg); border:1px solid var(--border); border-radius:14px;
    padding:1.6rem 1.6rem 1.2rem 1.6rem;
}
[data-testid="stTextInput"] label{
    font-family:'JetBrains Mono',monospace; font-size:0.72rem; letter-spacing:.04em;
    color:var(--text-mid) !important; text-transform:uppercase;
}
[data-testid="stTextInput"] input{
    background:var(--bg) !important; border:1px solid var(--border) !important;
    border-radius:8px !important; color:var(--text-hi) !important;
}
[data-testid="stTextInput"] input:focus{ border-color:var(--gold) !important; box-shadow:0 0 0 1px var(--gold) !important; }
div[data-testid="stFormSubmitButton"] button{
    background:var(--gold) !important; color:#0a0a09 !important; border:none !important;
    border-radius:9px !important; font-weight:700 !important; padding:0.6rem 0 !important;
    margin-top:0.4rem !important;
}
div[data-testid="stFormSubmitButton"] button:hover{ filter:brightness(1.08); }
div.st-key-secondary_nav button{
    background:transparent !important; color:var(--gold) !important; border:1px solid var(--gold-soft) !important;
    border-radius:9px !important; font-weight:500 !important;
}
div.st-key-secondary_nav button:hover{ background:var(--gold-softer) !important; border-color:var(--gold) !important; }
.stAlert{ border-radius:9px !important; }
</style>""",
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="lx-logo-row">
            <div class="lx-logo-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 3v18"/><path d="M4 7l4-1.5L12 7l4-1.5L20 7"/>
                    <path d="M4 7l-2.2 5A3 3 0 0 0 4.5 15 3 3 0 0 0 7.2 12L4 7Z"/>
                    <path d="M20 7l-2.2 5a3 3 0 0 0 2.7 3 3 3 0 0 0 2.7-3L20 7Z"/>
                    <path d="M8.5 21h7"/>
                </svg>
            </div>
            <div class="lx-brand-name">LawLM</div>
            <div class="lx-brand-sub">Your Legal Assistant</div>
        </div>""",
    unsafe_allow_html=True,
)

st.title("Login Form")

with st.form(key="user_login"):

    Email = st.text_input("Email")
    Password = st.text_input("Password", type="password")

    submit = st.form_submit_button(
        "Login",
        use_container_width=True
    )

    if submit:

        if not Email or not Password:
            st.warning("Please enter both email and password.")

        else:
            try:
                response = login_user(Email, Password)

                user = response.user

                st.session_state["user_id"] = user.id
                st.session_state["user_mail"] = user.email

                st.success("Login successful!")

                st.switch_page("pages/chatbot.py")

            except Exception as e:
                st.error(f"Login failed: {e}")


st.markdown('<div class="st-key-secondary_nav">', unsafe_allow_html=True)
if st.button("Go to Sign Up", use_container_width=True, key="secondary_nav"):
    st.switch_page("pages/signup.py")
st.markdown("</div>", unsafe_allow_html=True)
