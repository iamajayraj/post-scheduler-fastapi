# streamlit_app.py
import streamlit as st
import requests
from datetime import datetime


API_GENERATE_URL = "http://127.0.0.1:8000/generate"
API_FEEDBACK_URL = "http://127.0.0.1:8000/feedback"

st.title("AI-Powered Post Generator")

# ——— Inputs ———
topic   = st.text_input("Topic")
context = st.text_area("Context")
tone    = st.text_input("Tone")
cta     = st.text_input("CTA")

# ——— Dialog definition ———
@st.dialog("Your AI Generated Post", width="large")
def feedback_dialog():
    state = st.session_state.generated
    # Show the latest generated output
    st.subheader("📝 Generated Post")
    st.write(state.get("output_post", "_No content returned_"))

    # Feedback input
    feedback = st.text_area("✏️ Your feedback:", value=state.get("feedback", ""), key="dlg_fb")

    # Two-column layout for buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Feedback", key="dlg_submit"):
            # Update state and call feedback API
            state["feedback"] = feedback
            try:
                resp = requests.post(API_FEEDBACK_URL, json=state)
                resp.raise_for_status()
                st.session_state.generated = resp.json()
                # Rerun so the dialog reopens with updated content
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to submit feedback: {e}")
    with col2:
        if st.button("Approve", key="dlg_approve"):
            # Mark approved and rerun without calling the dialog again
            st.session_state.generated["approved"] = True
            try:
                resp = requests.post(API_FEEDBACK_URL, json=state)
                resp.raise_for_status()
                st.session_state.generated = resp.json()
                # Rerun so the dialog reopens with updated content
                st.success("🎉 Post Approved!")
            except Exception as e:
                st.error(f"❌ Failed to submit feedback: {e}")
            
            

# ——— Generate step ———
if st.button("Save"):
    payload = {
        "id":   123,
        "date": datetime.now().date().isoformat(),
        "time": datetime.now().time().replace(microsecond=0).isoformat(),
        "topic":   topic,
        "context": context,
        "tone":    tone,
        "cta":     cta,
    }
    try:
        resp = requests.post(API_GENERATE_URL, json=payload)
        resp.raise_for_status()
        st.session_state.generated = resp.json()
        # Open the dialog right away
        feedback_dialog()
    except Exception as e:
        st.error(f"❌ Failed to generate: {e}")

# ——— Keep dialog open until approved ———
if "generated" in st.session_state:
    if not st.session_state.generated.get("approved", False):
        feedback_dialog()
    else:
        # After approval, you can clear state or keep it to show a summary
        st.success("✅ You've approved the post!")


        

