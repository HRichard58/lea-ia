import streamlit as st
from langchain_groq import ChatGroq
import os

# --- CONFIGURATION ---
NOM_IA = "Léa"
# On utilise la mémoire de session plutôt qu'un fichier pour éviter les erreurs Cloud
if "long_term_memory" not in st.session_state:
    st.session_state.long_term_memory = ["Léa est une amie proche."]

# Récupération de la clé
try:
    api_key = st.secrets["GROQ_API_KEY"]
    llm = ChatGroq(temperature=0.8, groq_api_key=api_key, model_name="llama3-8b-8192")
except Exception as e:
    st.error("Problème de clé API. Vérifie tes Secrets Streamlit !")
    st.stop()

# --- INTERFACE ---
st.set_page_config(page_title=NOM_IA, page_icon="🌸")
st.title(f"💬 {NOM_IA}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LOGIQUE ---
if prompt := st.chat_input("Dis-moi tout..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Préparation du contexte
    memoire = "\n".join(st.session_state.long_term_memory)
    historique = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])

    instruction = f"Tu es {NOM_IA}, une amie par SMS. Souvenirs : {memoire}. Historique : {historique}. Réponds brièvement."

    with st.chat_message("assistant"):
        try:
            # Appel à Groq
            response = llm.invoke(instruction)
            full_response = response.content
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Sauvegarde d'un souvenir en mémoire vive (plus sûr sur le Cloud)
            if len(prompt) > 15:
                res_mem = llm.invoke(f"Fait important à retenir de '{prompt}' (3 mots max) ou 'NON'").content
                if "NON" not in res_mem.upper():
                    st.session_state.long_term_memory.append(res_mem)
        except Exception as e:
            st.error(f"Erreur Groq : {e}")
