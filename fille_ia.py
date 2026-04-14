import streamlit as st
from langchain_groq import ChatGroq
import base64
import requests
from datetime import datetime
import time

# --- 1. CONFIGURATION ---
NOM_IA = "Olivia"
REPO_OWNER = "HRichard58"
REPO_NAME = "Olivia-ia"
FILE_PATH = "Souvenirs_Olivia.txt"  # Vérifie bien les majuscules ici !

# Connexion API
try:
    groq_key = st.secrets["GROQ_API_KEY"]
    gh_token = st.secrets["GITHUB_TOKEN"]
    llm = ChatGroq(temperature=0.8, groq_api_key=groq_key, model_name="llama-3.1-8b-instant")
except Exception as e:
    st.error(f"Erreur Secrets Streamlit : {e}")
    st.stop()

# --- 2. FONCTIONS GITHUB (MÉMOIRE) ---
def lire_memoire_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return content, r.json()['sha']
    else:
        # Si le fichier n'existe pas encore ou erreur
        return "Olivia commence son journal.", None

def sauver_memoire_github(nouveau_souvenir):
    contenu_actuel, sha = lire_memoire_github()
    date = datetime.now().strftime("%d/%m")
    nouveau_contenu = contenu_actuel + f"\n- {nouveau_souvenir} ({date})"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    
    data = {
        "message": f"Mise à jour mémoire - {date}",
        "content": base64.b64encode(nouveau_contenu.encode('utf-8')).decode('utf-8'),
        "sha": sha if sha else ""
    }
    
    headers = {"Authorization": f"token {gh_token}"}
    r = requests.put(url, json=data, headers=headers)
    
    # Debug dans la barre latérale
    if r.status_code in [200, 201]:
        st.sidebar.success("✅ Souvenir enregistré sur GitHub !")
    else:
        st.sidebar.error(f"❌ Erreur GitHub {r.status_code} : {r.text}")

# --- 3. INTERFACE ---
st.set_page_config(page_title=NOM_IA)

st.markdown("""
    <style>
    .avatar-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .avatar-img { border-radius: 50%; border: 4px solid #FF69B4; width: 150px; height: 150px; object-fit: cover; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("📱 Menu d'Olivia")
    st.info(f"Fichier : {FILE_PATH}")
    if st.button("Réinitialiser la conversation"):
        st.session_state.messages = []
        st.rerun()

# Initialisation des états
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "souvenirs" not in st.session_state:
    memo, _ = lire_memoire_github()
    st.session_state.souvenirs = memo

# Affichage de l'historique
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. LOGIQUE CHAT ---
if prompt := st.chat_input("Dis quelque chose à Olivia..."):
    # Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Préparer le contexte pour l'IA
    historique = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-10:]])
    instruction = f"Tu es {NOM_IA}. Voici tes souvenirs : {st.session_state.souvenirs}. Réponds de façon naturelle. Historique récent : {historique}"

    with st.chat_message("assistant"):
        try:
            with st.spinner("Olivia écrit..."):
                response = llm.invoke(instruction).content
            
            # Effet machine à écrire
            placeholder = st.empty()
            full_res = ""
            for char in response:
                full_res += char
                placeholder.markdown(full_res + "▌")
                time.sleep(0.01)
            placeholder.markdown(full_res)
            
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # --- LOGIQUE DE MÉMOIRE ---
            # On baisse la limite à 1 pour tester facilement
            if len(prompt) > 1:
                analyse_prompt = f"Résume ce fait sur l'utilisateur en 3-5 mots maximum (ex: Aime le café, Habite à Paris). Si rien d'important, réponds 'NON'. Phrase : '{prompt}'"
                analyse = llm.invoke(analyse_prompt).content
                
                if "NON" not in analyse.upper():
                    sauver_memoire_github(analyse.strip())
                    st.session_state.souvenirs += f"\n- {analyse.strip()}"
                    
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
