import sys
from pathlib import Path

import streamlit as st

if "user_id" not in st.session_state:
    st.switch_page("pages/login.py")
    st.stop()

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from rag_pipeline import answer_question



st.markdown("""
<style>
    div.st-key-top_btn {
        position: absolute;
        top: 15px ;
        right: 25px;
        z-index: 999999;
    }
    div.st-key-top_btn button {
        border-radius: 12px;
        padding: 4px 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)
spacer, col_btn = st.columns([8,1])
with col_btn:
    if st.button("Profile",key="key-top_btn"):
        st.switch_page("pages/account.py")

st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None

prompt = st.chat_input("Say something")
with st.sidebar:
    if st.button(("New Conversation")):
        st.session_state.clear()
        st.rerun()
    saved_chat = st.selectbox("Recent Chat",[f"{prompt}"])
    
if "messages" not in st.session_state:
    st.session_state.messages = []
for messages in st.session_state.messages:
    with st.chat_message(messages["role"]):
        st.write(messages["content"])

if prompt:

    if st.session_state["conversation_id"] is None:
        user_id = st.session_state["user_id"]

        st.session_state["conversation_id"] = create_conversation(
            user_id,
            prompt
        )
    st.session_state.messages.append({
        "role": "user",
        "content": f"User: {prompt}"
    })
    with st.chat_message("user"):
        st.write(f"User: {prompt}")

    answer,_=answer_question(prompt)

    st.session_state.messages.append({
        "role" : "assistant",
        "content" : answer
    })    
    with st.chat_message("assistant"):
        st.write(answer)


