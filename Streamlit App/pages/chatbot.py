import html
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="LawLM",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Auth guard + RAG pipeline hookup -- mirrors frontend.py's pattern exactly:
# check for a logged-in session, then make the project root importable so
# rag_pipeline (which lives one directory above "Streamlit App") can be
# imported.
# ----------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.switch_page("pages/login.py")
    st.stop()

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag_pipeline import answer_question  # noqa: E402  (path must be set first)

# ----------------------------------------------------------------------------
# Icons -- small inline SVGs, generic line-icon shapes (not lifted from any
# icon library), styled via currentColor so they inherit text color.
# ----------------------------------------------------------------------------
ICON = {
    "logo": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M4 7l4-1.5L12 7l4-1.5L20 7"/><path d="M4 7l-2.2 5A3 3 0 0 0 4.5 15 3 3 0 0 0 7.2 12L4 7Z"/><path d="M20 7l-2.2 5a3 3 0 0 0 2.7 3 3 3 0 0 0 2.7-3L20 7Z"/><path d="M8.5 21h7"/></svg>',
}

def icon(name: str, size: int = 16) -> str:
    """HTML icon -- only valid inside st.markdown(unsafe_allow_html=True)."""
    return f'<span class="lx-icon" style="width:{size}px;height:{size}px">{ICON[name]}</span>'

# st.button() labels are plain markdown text, NOT unsafe HTML -- an <svg>
# string in a button label just prints as escaped tag text. Use plain
# glyphs for anything that has to live inside a button.
BTN_GLYPH = {
    "bell": "🔔",
    "settings": "⚙",
    "bookmark": "🔖",
    "share": "↗",
    "more": "⋯",
    "plus": "+",
}

# ----------------------------------------------------------------------------
# Formatting the model's answer
# ----------------------------------------------------------------------------
def format_answer_html(raw_text: str) -> str:
    """
    Turn Gemini's markdown-ish reply into the HTML this UI expects.

    Gemini is prompted (see rag_pipeline.py) to structure answers with
    headings, bold terms, and lists, so its output is Markdown, not HTML.
    This converts that Markdown into simple HTML so it renders instead of
    showing literal asterisks -- and critically, every **bold** span becomes
    a <b> tag, which picks up the gold highlight automatically via the
    existing ".lx-answer b { color: var(--gold); }" rule below. That's the
    whole mechanism behind requirement #5: nothing needs a hardcoded color,
    any bold term the model produces turns gold on its own.

    The raw text is HTML-escaped before any tag is introduced, so nothing
    in the model's output can inject markup.
    """
    text = html.escape(raw_text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)          # **bold**
    text = re.sub(r"(?m)^#{1,6}\s*(.+)$", r"<b>\1</b>", text)     # ### Heading

    out, in_list = [], False
    for line in text.split("\n"):
        stripped = line.strip()
        is_bullet = stripped.startswith("- ") or stripped.startswith("* ")
        if is_bullet and not in_list:
            out.append("<ul style='margin:4px 0 8px 18px; padding:0;'>")
            in_list = True
        elif not is_bullet and in_list:
            out.append("</ul>")
            in_list = False

        if is_bullet:
            out.append(f"<li>{stripped[2:].strip()}</li>")
        elif stripped == "":
            out.append("<br>")
        else:
            out.append(stripped + "<br>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


def generate_reply(user_text: str) -> str:
    try:
        answer_text, _usage = answer_question(user_text)
    except Exception as e:
        return (
            "<b>Something went wrong generating that answer.</b><br><br>"
            f"{html.escape(str(e))}"
        )
    return format_answer_html(answer_text)


# ----------------------------------------------------------------------------
# Mock data -- this seeds the sidebar with one illustrative conversation so
# the UI isn't empty on first load. Swap for real conversation history from
# Supabase (conversations.py / save_messages.py already exist for this) when
# you're ready to persist chats across sessions.
# ----------------------------------------------------------------------------
DEMO_USER = {"name": "Pranav K", "role": "Student", "initials": "PK"}

FIRST_MESSAGE = "What is article 14?"

FIRST_REPLY_HTML = (
    "<b>Article 14</b> of the Constitution of India guarantees the fundamental right to <b>equality.</b>"
    "It states that the State shall not deny to any person equality before the law or the "
    "equal protection of the laws within the territory of India. This right applies to "
    "both citizens and non-citizens, including companies.<br><br>"
    "<b>Key Concepts under Article 14:</b><br><br>"
    "<b>Equality before the law</b> — No individual or group is above the law; everyone is subject to the same legal standards.<br><br>"
    "<b>Equal protection of the laws</b> — The State must ensure that laws are applied equally and fairly to all individuals, without discrimination.<br><br>"
)

if "conversations" not in st.session_state:
    st.session_state.conversations = {
        "noncompete": {
            "title": "Article 14",
            "badge": "Constitution",
            "group": "TODAY",
            "time": "1h ago",
            "preview": "Article 14 of the Constitution…",
            "messages": [
                {"role": "user", "text": FIRST_MESSAGE, "time": "09:28 AM"},
                {"role": "assistant", "html": FIRST_REPLY_HTML, "time": "09:29 AM"},
            ],
        },
    }

if "active_id" not in st.session_state:
    st.session_state.active_id = "noncompete"

# ----------------------------------------------------------------------------
# CSS
# ----------------------------------------------------------------------------
st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
    --bg:#0a0a09;
    --sidebar-bg:#111110;
    --panel-bg:#121211;
    --border:#242320;
    --border-soft:#1a1917;
    --gold:#e8b923;
    --gold-soft:rgba(232,185,35,0.12);
    --gold-softer:rgba(232,185,35,0.06);
    --text-hi:#f2f0e6;
    --text-mid:#96948a;
    --text-low:#5c5a52;
    --bubble-bg:#1b1a17;
    --radius:10px;
    --footer-h:78px;
}
html, body, [data-testid="stAppViewContainer"], .stApp{
    background:var(--bg) !important;
    color:var(--text-hi);
    font-family:'Inter',sans-serif;
}
[data-testid="stHorizontalBlock"]{ align-items:center; }
[data-testid="stHeader"]{ background:transparent; height:0; }
[data-testid="stToolbar"]{ display:none; }
footer{ display:none; }
.block-container{ padding:1.25rem 2.5rem 1rem 2.5rem !important; max-width:100% !important; }
.lx-mono{ font-family:'JetBrains Mono',monospace; }
/* --- Fix #1: Streamlit's own sidebar collapse/expand arrow can render */
/* using the browser's light-theme icon color, which is invisible against */
/* this dark background on devices that don't force dark mode. Force it */
/* visible on every device regardless of theme. Both selectors are kept */
/* since the testid has changed across Streamlit versions. */
[data-testid="collapsedControl"]{
    background:var(--panel-bg) !important;
    border:1px solid var(--gold-soft) !important;
    border-radius:8px !important;
    opacity:1 !important;
    visibility:visible !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="baseButton-header"] svg{
    fill:var(--gold) !important;
    color:var(--gold) !important;
}
[data-testid="stSidebar"]{
    background:var(--sidebar-bg) !important;
    border-right:1px solid var(--border-soft);
    min-width:300px !important;
    max-width:320px !important;
    position:relative !important;
}
[data-testid="stSidebar"] > div:first-child{
    height:100vh !important;
    display:flex !important;
    flex-direction:column !important;
    padding-top:0.5rem;
}
/* --- Fix #3: pin the account/profile footer to the bottom of the sidebar */
/* regardless of how many conversations are above it. The scrollable body */
/* gets bottom padding so real content never hides underneath the footer, */
/* and the footer itself is absolutely positioned against the sidebar, */
/* which is now a fixed-height, position:relative box (rules above). */
[data-testid="stSidebarUserContent"]{
    padding-top:0.25rem;
    flex:1 1 auto;
    overflow-y:auto;
    padding-bottom:var(--footer-h);
}
div.st-key-sidebar_footer{
    position:absolute;
    left:0;
    right:0;
    bottom:0;
    background:var(--sidebar-bg);
    border-top:1px solid var(--border-soft);
    padding:12px 14px;
    z-index:5;
}
.lx-logo-row{ display:flex; align-items:center; gap:10px; padding:6px 4px 18px 4px; }
.lx-logo-badge{
    width:38px; height:38px; border-radius:9px; background:var(--gold-soft);
    border:1px solid var(--gold-soft); display:flex; align-items:center; justify-content:center;
    color:var(--gold); flex-shrink:0;
}
.lx-logo-badge .lx-icon{ width:20px !important; height:20px !important; }
.lx-brand-name{ font-weight:700; font-size:1.05rem; color:var(--text-hi); line-height:1.15; }
.lx-brand-sub{ font-family:'JetBrains Mono',monospace; font-size:0.62rem; letter-spacing:.09em;
    color:var(--text-low); margin-top:2px; }
.lx-group-label{
    font-family:'JetBrains Mono',monospace; font-size:0.66rem; letter-spacing:.12em;
    color:var(--text-low); margin:16px 4px 6px 4px; text-transform:uppercase;
}
.lx-iconbtn button{
    background:transparent !important; border:1px solid var(--border) !important;
    color:var(--text-mid) !important; border-radius:8px !important;
    width:34px !important; height:34px !important; padding:0 !important;
    display:flex; align-items:center; justify-content:center;
}
.lx-iconbtn button:hover{ border-color:var(--gold) !important; color:var(--gold) !important; }
.lx-iconbtn button p{ display:none; }
div.st-key-new_conv button{
    width:100%; background:var(--gold-softer) !important; color:var(--gold) !important;
    border:1px solid var(--gold-soft) !important; border-radius:9px !important;
    font-weight:600 !important; font-size:0.86rem !important; padding:0.55rem 0 !important;
}
div.st-key-new_conv button:hover{ background:var(--gold-soft) !important; border-color:var(--gold) !important; }
[data-testid="stSidebar"] div[class*="st-key-conv_"] button{
    width:100%; text-align:left !important; background:transparent !important;
    border:1px solid transparent !important; border-left:2px solid transparent !important;
    border-radius:8px !important; padding:8px 10px !important; color:var(--text-mid) !important;
    font-weight:400 !important; line-height:1.45 !important; white-space:normal !important;
}
[data-testid="stSidebar"] div[class*="st-key-conv_"] button p{ font-size:0.82rem !important; margin:0; }
[data-testid="stSidebar"] div[class*="st-key-conv_"] button:hover{
    background:var(--border-soft) !important;
}
[data-testid="stSidebar"] div[class*="st-key-conv_active"] button{
    background:var(--gold-softer) !important; border-left:2px solid var(--gold) !important;
}
.lx-profile{ display:flex; align-items:center; gap:10px; }
.lx-avatar{
    width:34px; height:34px; border-radius:50%; background:var(--gold-soft); color:var(--gold);
    display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.78rem;
    flex-shrink:0; font-family:'JetBrains Mono',monospace;
}
.lx-profile-name{ font-size:0.82rem; font-weight:600; color:var(--text-hi); line-height:1.2; }
.lx-profile-role{ font-size:0.7rem; color:var(--text-low); line-height:1.2; }
.lx-header-row{ display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:1.1rem; }
.lx-title{ font-size:1.35rem; font-weight:700; color:var(--text-hi); display:inline; }
.lx-badge{
    display:inline-block; margin-left:10px; padding:2px 10px; border-radius:999px;
    border:1px solid var(--gold-soft); color:var(--gold); font-size:0.7rem; font-weight:600;
    vertical-align:middle; font-family:'JetBrains Mono',monospace;
}
.lx-meta{ font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:var(--text-low); margin-top:4px; }
.lx-timestamp{ text-align:center; font-family:'JetBrains Mono',monospace; font-size:0.68rem;
    color:var(--text-low); margin:18px 0 14px 0; }
.lx-msg-row{ display:flex; gap:12px; margin-bottom:22px; max-width:900px; }
.lx-msg-row.assistant{ flex-direction:row-reverse; margin-left:auto; }
.lx-avatar-sm{
    width:30px; height:30px; border-radius:50%; flex-shrink:0; display:flex; align-items:center;
    justify-content:center; font-size:0.68rem; font-weight:700; font-family:'JetBrains Mono',monospace;
}
.lx-avatar-sm.user{ background:var(--gold-soft); color:var(--gold); }
.lx-avatar-sm.assistant{ background:var(--gold-soft); color:var(--gold); }
.lx-avatar-sm.assistant .lx-icon{ width:15px !important; height:15px !important; }
.lx-bubble{ background:var(--bubble-bg); border:1px solid var(--border-soft); border-radius:14px;
    padding:14px 18px; font-size:0.92rem; line-height:1.55; color:var(--text-hi); }
.lx-answer{ font-size:0.93rem; line-height:1.65; color:var(--text-hi); padding-top:2px; }
.lx-answer b{ color:var(--gold); font-weight:600; }
.lx-answer ul{ color:var(--text-hi); }
div.st-key-chip_wrap div[class*="st-key-chip_"] button{
    background:transparent !important; color:var(--gold) !important;
    border:1px solid var(--gold-soft) !important; border-radius:999px !important;
    font-size:0.8rem !important; padding:8px 16px !important; white-space:normal !important;
}
div.st-key-chip_wrap div[class*="st-key-chip_"] button:hover{
    background:var(--gold-softer) !important; border-color:var(--gold) !important;
}
[data-testid="stChatInput"]{
    background:var(--panel-bg) !important; border:1px solid var(--border) !important;
    border-radius:14px !important;
}
[data-testid="stChatInput"] textarea{ color:var(--text-hi) !important; font-family:'Inter',sans-serif !important; }
[data-testid="stChatInput"] textarea::placeholder{ color:var(--text-low) !important; }
[data-testid="stChatInput"] button{ background:var(--gold) !important; border-radius:9px !important; }
[data-testid="stChatInput"] button svg{ fill:#0a0a09 !important; }
.lx-disclaimer{
    text-align:center; font-family:'JetBrains Mono',monospace; font-size:0.68rem;
    color:var(--text-low); margin-top:10px; letter-spacing:.02em;
}
.lx-icon svg{ width:100%; height:100%; }
</style>""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""<div class="lx-logo-row">
                <div class="lx-logo-badge">{icon('logo', 20)}</div>
                <div>
                    <div class="lx-brand-name">LawLM</div>
                    <div class="lx-brand-sub">Your Legal Assistant</div>
                </div>
            </div>""",
        unsafe_allow_html=True,
    )

    if st.button("+  New Conversation", key="new_conv", help="Start a new conversation"):
        new_id = f"conv_{int(time.time())}"
        st.session_state.conversations[new_id] = {
            "title": "New Conversation",
            "badge": "General",
            "group": "TODAY",
            "time": "now",
            "preview": "No messages yet…",
            "messages": [],
        }
        st.session_state.active_id = new_id
        st.rerun()

    groups = {}
    for cid, conv in st.session_state.conversations.items():
        groups.setdefault(conv["group"], []).append((cid, conv))

    for group_name in ("TODAY", "YESTERDAY", "EARLIER"):
        if group_name not in groups:
            continue
        st.markdown(f'<div class="lx-group-label">{group_name}</div>', unsafe_allow_html=True)
        for cid, conv in groups[group_name]:
            is_active = cid == st.session_state.active_id
            key = f"conv_{cid}{'_active' if is_active else ''}"
            label = f"**{conv['title']}**  ·  _{conv['time']}_\n\n{conv['preview']}"
            if st.button(
                label, key=key, use_container_width=True,
                help=f"Open “{conv['title']}”",
            ):
                st.session_state.active_id = cid
                st.rerun()

    # Fix #3: a real st.container(key=...) -- unlike an st.markdown-opened
    # <div>, this genuinely wraps everything inside it in the DOM, so the
    # "div.st-key-sidebar_footer{ position:absolute; bottom:0; }" rule above
    # reliably pins this whole block to the sidebar's bottom edge no matter
    # how short the conversation list above it is.
    with st.container(key="sidebar_footer"):
        pcol1, pcol2, pcol3, pcol4 = st.columns([1.3, 4, 1, 1])
        with pcol1:
            st.markdown(f'<div class="lx-avatar">{DEMO_USER["initials"]}</div>', unsafe_allow_html=True)
        with pcol2:
            st.markdown(
                f'<div class="lx-profile-name">{DEMO_USER["name"]}</div>'
                f'<div class="lx-profile-role">{DEMO_USER["role"]}</div>',
                unsafe_allow_html=True,
            )
        with pcol3:
            st.markdown('<div class="lx-iconbtn">', unsafe_allow_html=True)
            st.button(BTN_GLYPH["bell"], key="bell_btn", help="Notifications")
            st.markdown("</div>", unsafe_allow_html=True)
        with pcol4:
            st.markdown('<div class="lx-iconbtn">', unsafe_allow_html=True)
            # Fix #3 (functional half): this is the "Account button" -- wired
            # to actually navigate to the account page, and pinned in place
            # by the container/CSS above regardless of conversation count.
            if st.button(BTN_GLYPH["settings"], key="settings_btn", help="Account settings"):
                st.switch_page("pages/account.py")
            st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Main panel
# ----------------------------------------------------------------------------
active = st.session_state.conversations[st.session_state.active_id]
msg_count = len(active["messages"])

header_l, header_r = st.columns([6, 1.4])
with header_l:
    st.markdown(
        f"""<div class="lx-header-row">
            <div>
                <span class="lx-title">{html.escape(active['title'])}</span>
                <span class="lx-badge">{html.escape(active['badge'])}</span>
                <div class="lx-meta">{msg_count} message{'s' if msg_count != 1 else ''}  ·  {active['time']}</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
with header_r:
    b1, b2, b3 = st.columns(3)
    icon_help = {
        "bookmark": "Bookmark this conversation",
        "share": "Share this conversation",
        "more": "More options",
    }
    for col, name, key in ((b1, "bookmark", "bm_btn"), (b2, "share", "sh_btn"), (b3, "more", "mo_btn")):
        with col:
            st.markdown('<div class="lx-iconbtn">', unsafe_allow_html=True)
            st.button(BTN_GLYPH[name], key=key, help=icon_help[name])
            st.markdown("</div>", unsafe_allow_html=True)

if active["messages"]:
    st.markdown(f'<div class="lx-timestamp">{active["messages"][0]["time"]}</div>', unsafe_allow_html=True)

for msg in active["messages"]:
    if msg["role"] == "user":
        st.markdown(
            f"""<div class="lx-msg-row user">
                    <div class="lx-avatar-sm user">{DEMO_USER['initials']}</div>
                    <div class="lx-bubble">{html.escape(msg['text'])}</div>
                </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="lx-msg-row assistant">
                    <div class="lx-avatar-sm assistant">{icon('logo', 15)}</div>
                    <div class="lx-answer">{msg['html']}</div>
                </div>""",
            unsafe_allow_html=True,
        )

# Suggested follow-ups
SUGGESTIONS = [
    "What are my fundamental rights under Article 21?",
    "Explain the process for filing anticipatory bail",
    "Draft a legal notice for breach of contract",
]
st.markdown('<div class="st-key-chip_wrap">', unsafe_allow_html=True)
chip_cols = st.columns(len(SUGGESTIONS))
chosen_suggestion = None
for i, (col, text) in enumerate(zip(chip_cols, SUGGESTIONS)):
    with col:
        if st.button(text, key=f"chip_{i}", use_container_width=True, help="Use this suggested question"):
            chosen_suggestion = text
st.markdown("</div>", unsafe_allow_html=True)

prompt = st.chat_input("Ask a legal question or paste a clause to review…")
final_prompt = prompt or chosen_suggestion

if final_prompt:
    now = datetime.now().strftime("%I:%M %p")
    active["messages"].append({"role": "user", "text": final_prompt, "time": now})
    with st.spinner("Researching case law and drafting an answer…"):
        reply_html = generate_reply(final_prompt)
    active["messages"].append({"role": "assistant", "html": reply_html, "time": now})
    active["preview"] = final_prompt[:48] + ("…" if len(final_prompt) > 48 else "")
    st.rerun()

st.markdown(
    '<div class="lx-disclaimer">LawLM provides research assistance only  ·  '
    "Not legal advice  ·  Verify with qualified counsel</div>",
    unsafe_allow_html=True,
)
