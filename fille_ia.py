import streamlit as st
from langchain_groq import ChatGroq
import os
from datetime import datetime

# --- 1. CONFIGURATION ---
NOM_IA = "Léa"

# Initialisation sécurisée de la clé API
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("❌ La clé GROQ_API_KEY est manquante dans les Secrets de Streamlit.")
    st.stop()

# Initialisation du modèle (MAJ : llama-3.1-8b-instant remplace llama3-8b-8192)
try:
    llm = ChatGroq(
        temperature=0.8,
        groq_api_key=api_key,
        model_name="llama-3.1-8b-instant" 
    )
except Exception as e:
    st.error(f"Erreur d'initialisation du modèle : {e}")
    st.stop()

# --- 2. GESTION DE LA MÉMOIRE ---
# On utilise la mémoire de session (stable sur Cloud) au lieu du fichier .txt
if "long_term_memory" not in st.session_state:
    st.session_state.long_term_memory = [f"{NOM_IA} est une amie proche et drôle."]

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. INTERFACE ---
st.set_page_config(page_title=NOM_IA, page_icon="🌸", layout="centered")

with st.sidebar:
    st.title("📞 Options")
    mode_appel = st.toggle("Activer l'appel vidéo")
    st.write("---")
    if st.button("Effacer la discussion"):
        st.session_state.messages = []
        st.rerun()

st.title(f"💬 {NOM_IA}")

# Affichage de la caméra en mode appel
if mode_appel:
    st.camera_input("Léa est en ligne...")
    st.info("Léa te voit à travers l'écran ! ✨")

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. LOGIQUE DE CHAT ---
if prompt := st.chat_input("Dis-moi quelque chose..."):
    # Ajouter le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Préparation du contexte
    memoire_longue = "\n".join(st.session_state.long_term_memory)
    maintenant = datetime.now().strftime("%H:%M")
    
    # Historique court (6 derniers messages)
    historique_recent = ""
    for m in st.session_state.messages[-6:]:
        role = "Ami" if m["role"] == "user" else NOM_IA
        historique_recent += f"{role}: {m['content']}\n"

    instruction_systeme = f"""
    Tu es {NOM_IA}, une fille réelle, chaleureuse et un peu taquine.
    Style : SMS court, emojis, langage naturel d'une amie.
    Contexte : Il est {maintenant}. Mode : {'APPEL VIDÉO' if mode_appel else 'CHAT'}.
    
    Tes souvenirs de l'Ami :
    {memoire_longue}

    Conversation :
    {historique_recent}

    Réponds brièvement en tant que {NOM_IA}.
    """

    # Génération de la réponse
    with st.chat_message("assistant"):
        try:
            response = llm.invoke(instruction_systeme)
            reponse_finale = response.content
            st.markdown(reponse_finale)
            st.session_state.messages.append({"role": "assistant", "content": reponse_finale})
            
            # 5. MISE À JOUR DE LA MÉMOIRE (Sans fichier .txt pour éviter les erreurs)
            if len(prompt) > 15:
                analyse_query = f"Résume un fait important sur l'utilisateur dans : '{prompt}'. 3 mots max. Sinon 'NON'."
                analyse = llm.invoke(analyse_query).content
                if "NON" not in analyse.upper():
                    st.session_state.long_term_memory.append(f"{analyse.strip()} (retenu à {maintenant})")
                    
        except Exception as e:
            st.error(f"Désolée, j'ai eu un petit bug : {e}")
