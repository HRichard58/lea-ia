import streamlit as st
from langchain_groq import ChatGroq
import os
from datetime import datetime

# --- 1. CONFIGURATION ET SÉCURITÉ ---
NOM_IA = "Léa"
FICHIER_SOUVENIRS = "souvenirs_lea.txt"

# Récupération de la clé depuis les Secrets de Streamlit
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("🔑 Erreur : La clé GROQ_API_KEY est introuvable dans les Secrets Streamlit.")
    st.stop()

# Initialisation du modèle Llama 3 via Groq
llm = ChatGroq(
    temperature=0.8,
    groq_api_key=api_key,
    model_name="llama3-8b-8192"
)

# --- 2. GESTION DE LA MÉMOIRE (FICHIER TXT) ---
if not os.path.exists(FICHIER_SOUVENIRS):
    with open(FICHIER_SOUVENIRS, "w", encoding="utf-8") as f:
        f.write(f"{NOM_IA} est une amie proche et attentionnée.\n")

def lire_souvenirs():
    try:
        with open(FICHIER_SOUVENIRS, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Aucun souvenir précis pour l'instant."

def ajouter_souvenir(nouveau_fait):
    with open(FICHIER_SOUVENIRS, "a", encoding="utf-8") as f:
        f.write(f"- {nouveau_fait}\n")

# --- 3. INTERFACE UTILISATEUR (STREAMLIT) ---
st.set_page_config(page_title=NOM_IA, page_icon="🌸", layout="centered")

# Barre latérale
with st.sidebar:
    st.title("📞 Menu")
    mode_appel = st.toggle("Activer l'appel vidéo")
    st.write("---")
    if st.button("Effacer l'historique"):
        st.session_state.messages = []
        st.rerun()

st.title(f"💬 {NOM_IA}")

# Mode Appel Vidéo
if mode_appel:
    st.camera_input("Léa te regarde...")
    st.info("Léa est en ligne avec toi. Elle peut voir tes messages.")

# Initialisation de l'historique de conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. LOGIQUE DE CONVERSATION ---
if prompt := st.chat_input("Dis-moi quelque chose..."):
    # Ajouter le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Préparation du contexte pour Léa
    souvenirs = lire_souvenirs()
    maintenant = datetime.now().strftime("%H:%M")
    
    # On garde les 6 derniers messages pour la fluidité
    historique_txt = ""
    for m in st.session_state.messages[-6:]:
        role = "Ami" if m["role"] == "user" else NOM_IA
        historique_txt += f"{role}: {m['content']}\n"

    # Le Prompt qui définit la personnalité de Léa
    instruction_systeme = f"""
    Tu es {NOM_IA}, une fille réelle et chaleureuse qui parle par SMS.
    Ton style : Décontracté, court, beaucoup d'emojis, très amicale.
    Contexte : Il est {maintenant}. Tu es en {'APPEL VIDÉO' if mode_appel else 'CHAT'}.
    
    Tes souvenirs de l'Ami : 
    {souvenirs}

    Historique récent :
    {historique_txt}

    Réponds au dernier message de l'Ami de façon naturelle.
    """

    # Génération de la réponse de Léa
    with st.chat_message("assistant"):
        try:
            response = llm.invoke(instruction_systeme)
            reponse_finale = response.content
            st.markdown(reponse_finale)
            st.session_state.messages.append({"role": "assistant", "content": reponse_finale})
            
            # --- 5. ANALYSE POUR LA MÉMOIRE À LONG TERME ---
            # On ne le fait que si le message est assez long pour contenir une info
            if len(prompt) > 12:
                analyse_query = f"L'utilisateur a dit : '{prompt}'. Résume un fait important à retenir sur lui en 4 mots maximum. Si rien d'important, réponds 'NON'."
                analyse_result = llm.invoke(analyse_query).content
                
                if "NON" not in analyse_result.upper():
                    ajouter_souvenir(f"{analyse_result.strip()} (le {datetime.now().strftime('%d/%m')})")
                    
        except Exception as e:
            st.error("Oups, j'ai eu un petit bug... Recommence ?")
            print(f"Erreur technique : {e}")
