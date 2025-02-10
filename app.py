import streamlit as st
import requests

# URL del backend
API_URL = "http://127.0.0.1:8000"

# Titolo dell'app
st.title("💬 Smart DOC ")
st.write("Upload any PDF and ask whatever you need.")

# Upload PDF
uploaded_file = st.file_uploader("📂 Carica un file PDF", type=["pdf"])

if uploaded_file is not None:

    files = {"file": uploaded_file}
    response = requests.post(f"{API_URL}/upload", files=files)

    if response.status_code == 200:
        st.success("📄 PDF caricato con successo!")
    else:
        st.error("❌ Errore nel caricamento del file.")

# Memoria della chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # lista vuota per salvare messaggi


for speaker, message in st.session_state.chat_history:
    with st.chat_message("user" if speaker == "🧑‍💻 Tu" else "assistant"):
        st.markdown(message)


user_input = st.chat_input("✍️ Scrivi un messaggio...")

if user_input:
    # aggiungo il messaggio dell'utente alla cronologia e lo visualizzo
    st.session_state.chat_history.append(("🧑‍💻 Tu", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Chiamata fastapi
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": user_input}
    )

    if response.status_code == 200:
        bot_reply = response.json().get("reply", "Errore nella risposta")

        # Aggiunge la risposta del bot alla cronologia e la visualizza
        st.session_state.chat_history.append(("🤖 Chatbot", bot_reply))
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
    else:
        st.error("❌ Errore nella comunicazione con il server.")
