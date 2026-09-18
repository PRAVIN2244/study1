import streamlit as st

from rag import ask_question

st.set_page_config(page_title="Company RAG Chatbot")
st.title("Company RAG Chatbot")
st.write("Ask questions about the indexed company documents.")

question = st.text_input("Enter your question:", placeholder="What are the working hours?")

if st.button("Ask question", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Searching company documents..."):
                answer = ask_question(question)
            st.subheader("Answer")
            st.write(answer)
        except Exception as error:
            st.error(str(error))
