import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Account Settings",
    layout="centered"
)

st.markdown("""
    <style>
    /* Reduce padding and height of file uploader drop zone */
    [data-testid="stFileUploader"] section {
        padding: 8px 12px !important;
        min-height: 80px !important;
    }
    /* Hide default uploader helper text to keep it compact */
    [data-testid="stFileUploader"] section small {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stSidebar"] {
    display: none;
}

[data-testid="stSidebarNav"] {
    display: none;
}

[data-testid="collapsedControl"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)
st.title("Account Settings")
st.caption("Manage your profile details and preferences")

st.divider()

# pfp upload
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# Profile Overview Card
with st.container(border=True):
    st.subheader("Profile Overview")
    
    col_img, col_info = st.columns([1, 2], gap="medium", vertical_alignment="center")

    with col_img:
        if st.session_state.uploaded_image:
            st.image(st.session_state.uploaded_image, width=130)
            
            if st.button("Remove Picture", type="secondary"):
                st.session_state.uploaded_image = None
                st.rerun()
        else:
            uploaded_file = st.file_uploader(
                "No profile picture set",
                type=["jpg", "jpeg", "png"],
                label_visibility="visible"
            )
            if uploaded_file:
                st.session_state.uploaded_image = uploaded_file
                st.rerun()

    with col_info:
        st.markdown("### **User Name**")
        st.write("**Email:** user@gmail.com")

# Session Control
if st.button("Go back to Chatbot", type="secondary", use_container_width=True):
    st.switch_page("pages/frontend.py")
    