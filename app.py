import streamlit as st
import pandas as pd
import json
import os
import textwrap
from datetime import datetime

# Import flexible support pour streamlit-gsheets OU st-gsheets-connection
HAS_GSHEETS = False
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS = True
except ImportError:
    try:
        from st_gsheets_connection import GSheetsConnection
        HAS_GSHEETS = True
    except ImportError:
        HAS_GSHEETS = False

def get_gsheets_connection():
    if HAS_GSHEETS:
        try:
            return st.connection("gsheets", type=GSheetsConnection)
        except Exception:
            return None
    return None

# Configuration de la page
st.set_page_config(
    page_title="Massilly - Audit 5S Mobile",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Données des zones et sponsors officiels de Massilly
ZONES_MASSILLY = {
    "Zone 1": {"label": "Zone 1 - Filmeuse et quais production", "sponsor": "Audrey Sordet"},
    "Zone 2": {"label": "Zone 2 - Bureaux expédition", "sponsor": "Anthony Duplessis"},
    "Zone 3": {"label": "Zone 3 - Quai chargement", "sponsor": "Jonathan Mele"},
    "Zone 4": {"label": "Zone 4 - Zone préparation commande", "sponsor": "Thomas Collin"},
    "Zone 5": {"label": "Zone 5 - Emplacements boîtes", "sponsor": "Gaspard Sommereux"},
    "Zone 6": {"label": "Zone 6 - Palettier", "sponsor": "Mariia Leliukh"},
    "Zone 7": {"label": "Zone 7 - Bureaux et zones réception MP", "sponsor": "Céline Hereng"},
    "Zone 8": {"label": "Zone 8 - Zone stockage métal", "sponsor": "Dimitri Dupasquier"},
    "Zone 9": {"label": "Zone 9 - Local joint", "sponsor": "Frédéric Bouvy"},
    "Zone 10": {"label": "Zone 10 - Stockage produits dangereux", "sponsor": "Nathalie Berthelin"}
}

# Les 15 critères d'audit officiels de Massilly
CRITERES_OFFICIELS = [
    {"id": "c1", "cat": "1. Sort (Seiri) - Trier", "txt": "Les éléments inutiles ont été supprimés de la zone (au sol, sur les murs, autour des piliers, au plafond, sur les abords)."},
    {"id": "c2", "cat": "1. Sort (Seiri) - Trier", "txt": "Les tiroirs, établis, servantes et armoires sont vidés des choses inutiles ou superflues."},
    {"id": "c3", "cat": "1. Sort (Seiri) - Trier", "txt": "Les allées de circulation sont dégagées et propres (absence d'encombrement par des palettes)."},
    {"id": "c4", "cat": "2. Straighten (Seiton) - Ranger", "txt": "Tous les équipements, bennes, palettes et outils de la zone ont un marquage au sol et sont bien rangés à leur emplacement."},
    {"id": "c5", "cat": "2. Straighten (Seiton) - Ranger", "txt": "Le matériel de fourniture, de consommable et les outils de nettoyage sont clairement identifiés, étiquetés et rangés."},
    {"id": "c6", "cat": "2. Straighten (Seiton) - Ranger", "txt": "Les matières premières et produits bloqués sont correctement stockés dans la zone (présence de la feuille d'identification bleue)."},
    {"id": "c7", "cat": "3. Sweep (Seiso) - Nettoyer", "txt": "Les sols, les surfaces de travail, l'équipement et les aires d'entreposage de la zone sont propres (sans poussière ni résidus)."},
    {"id": "c8", "cat": "3. Sweep (Seiso) - Nettoyer", "txt": "Les déchets et les matières recyclables sont collectés et éliminés correctement (respect du tri sélectif cartons/plastiques)."},
    {"id": "c9", "cat": "3. Sweep (Seiso) - Nettoyer", "txt": "L'environnement de travail est bon (éclairages fonctionnels, absence de poussière excessive, marquage au sol bien visible)."},
    {"id": "c10", "cat": "4. Standardize (Seiketsu) - Standardiser", "txt": "Les rôles sont clairement définis pour garder la zone propre et ordonnée (Opérateurs, planning de nettoyage...)."},
    {"id": "c11", "cat": "4. Standardize (Seiketsu) - Standardiser", "txt": "Les tâches standard liées au nettoyage et à l'organisation sont définies (Rituel de fin de poste de 5-10 minutes...)."},
    {"id": "c12", "cat": "4. Standardize (Seiketsu) - Standardiser", "txt": "Il est évident visuellement qu'il y a une place désignée pour chaque chose (bennes, corbeilles, balais...)."},
    {"id": "c13", "cat": "5. Sustain (Shitsuke) - Maintenir/Respecter", "txt": "La zone présente une bonne organisation générale et ne présente aucun danger pour la sécurité du personnel (pas de risque de chute)."},
    {"id": "c14", "cat": "5. Sustain (Shitsuke) - Maintenir/Respecter", "txt": "Les documents et instructions visuelles de la zone sont à jour (pas de feuilles volantes ou de notes obsolètes)."},
    {"id": "c15", "cat": "5. Sustain (Shitsuke) - Maintenir/Respecter", "txt": "Le standard de la zone est conforme, pertinent et respecté au quotidien par l'ensemble de l'équipe terrain."}
]

# Initialisation de la session
st.session_state.setdefault("user_authenticated", False)
st.session_state.setdefault("user_role", "")
st.session_state.setdefault("user_name", "")
st.session_state.setdefault("user_zone", "")
st.session_state.setdefault("audit_started", False)
st.session_state.setdefault("current_q_idx", 0)
st.session_state.setdefault("answers", {})
st.session_state.setdefault("test_mode", False)
st.session_state.setdefault("portal_shown", False)
st.session_state.setdefault("auth_step", 0)
st.session_state.setdefault("opening_anim", False)

if st.session_state.get("test_mode", False):
    SHARED_DATA_FILE = "test_suivi_audits_5s.csv"
    SHARED_LOG_FILE = "test_journal_activite_5s.json"
else:
    SHARED_DATA_FILE = "suivi_audits_5s.csv"
    SHARED_LOG_FILE = "journal_activite_5s.json"

if not os.path.exists(SHARED_DATA_FILE):
    colonnes_init = [
        "Date", "Zone", "Sponsor", "Auditeur", "Role",
        "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10", "c11", "c12", "c13", "c14", "c15",
        "Score_Total", "Pourcentage", "Observations", "Actions_Correctives"
    ]
    pd.DataFrame(columns=colonnes_init).to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

if not os.path.exists(SHARED_LOG_FILE):
    with open(SHARED_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)

def charger_audits():
    conn = get_gsheets_connection()
    if conn is not None:
        try:
            df = conn.read(ttl=0)
            if df is not None and not df.empty:
                df = df.dropna(how="all")
                return df
        except Exception:
            pass

    try:
        return pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
    except Exception:
        return pd.DataFrame()

def sauvegarder_audit_local(data_dict):
    gsheets_ok = False
    err_details = ""
    conn = get_gsheets_connection()
    if conn is not None:
        try:
            try:
                existing_df = conn.read(ttl=0)
                if existing_df is None or existing_df.empty:
                    existing_df = pd.DataFrame()
                else:
                    existing_df = existing_df.dropna(how="all")
            except Exception:
                existing_df = pd.DataFrame()
                
            new_row = pd.DataFrame([data_dict])
            if not existing_df.empty:
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            else:
                updated_df = new_row
                
            conn.update(data=updated_df)
            gsheets_ok = True
        except Exception as e:
            err_details = str(e)

    try:
        df = pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
    except Exception:
        df = pd.DataFrame()

    new_row = pd.DataFrame([data_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "TEST - Diagnostic" if st.session_state.get("test_mode", False) else "Diagnostic Réel",
        "details": f"Zone {data_dict.get('Zone', '')} par {data_dict.get('Auditeur', '')} ({data_dict.get('Score_Total', 0)}/15 - {data_dict.get('Pourcentage', 0)}%)",
        "gsheets": "OK" if gsheets_ok else f"OFFLINE ({err_details})"
    }
    try:
        with open(SHARED_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except Exception:
        logs = []
    logs.append(log_entry)
    with open(SHARED_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

    return gsheets_ok, err_details


# CSS GLOBAL ULTRA-SÉCURISÉ & DEDENTED (AUCUNE DÉCORRECTION D'INDENTATION POUR ÉVITER LES BLOCS DE CODE TEXTE)
css_code = textwrap.dedent("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;600;700;800&family=Playfair+Display:ital,wght=0,600;0,800;1,600&display=swap');

    /* Fond d'application dynamique */
    .stApp {
        background: linear-gradient(-45deg, #0A1128, #101F42, #071126, #001F3D) !important;
        background-size: 400% 400% !important;
        animation: gradientBG 20s ease infinite !important;
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp label, .stApp p, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .question-card, .question-card p, .question-card span, .question-card li, .question-card div, .question-card h4, .question-text {
        color: #0F172A !important;
    }

    /* --- TITRE CORPO 3D MÉTALLIQUE FLOTTAISON --- */
    .main-header-3d {
        font-family: 'Playfair Display', serif !important;
        font-weight: 900 !important;
        font-size: 3.3rem !important;
        text-align: center !important;
        text-transform: uppercase;
        margin-top: -10px;
        margin-bottom: 5px;
        background: linear-gradient(135deg, #FFFFFF 20%, #38BDF8 60%, #0E529E 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: 
            0 1px 0 #E2E8F0,
            0 2px 0 #CBD5E1,
            0 3px 0 #94A3B8,
            0 4px 0 #64748B,
            0 5px 0 #475569,
            0 6px 0 #334155,
            0 7px 0 #1E293B,
            0 12px 18px rgba(0,0,0,0.6) !important;
        animation: floatHeader 3.8s ease-in-out infinite alternate !important;
        transform: perspective(800px) rotateX(15deg);
    }
    
    @keyframes floatHeader {
        0% { transform: perspective(800px) rotateX(15deg) translateY(0px) rotateY(-1deg); }
        100% { transform: perspective(800px) rotateX(15deg) translateY(-10px) rotateY(1deg); }
    }

    /* --- BADGE PORTAIL D'IDENTIFICATION 3D --- */
    .user-id-badge-3d {
        background: linear-gradient(135deg, #1E293B, #0B1329) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 20px !important;
        color: #FFFFFF !important;
        text-align: center;
        padding: 20px 40px !important;
        font-size: 1.7rem !important;
        font-weight: 900 !important;
        letter-spacing: 5px;
        margin: 15px auto 30px auto !important;
        max-width: 820px;
        box-shadow: 
            0 15px 35px rgba(56, 189, 248, 0.4),
            inset 0 0 25px rgba(56, 189, 248, 0.3) !important;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.7) !important;
        transform: perspective(800px) rotateX(10deg);
        animation: floatBadge 3.2s ease-in-out infinite alternate !important;
        border-bottom: 8px solid #005F73 !important;
    }

    @keyframes floatBadge {
        0% { transform: perspective(800px) rotateX(10deg) translateY(0px) scale(0.98); }
        100% { transform: perspective(800px) rotateX(10deg) translateY(-8px) scale(1.01); }
    }

    /* --- LA BOÎTE DÉCORÉE MASSILLY 3D INTERACTIVE --- */
    .box-scene-container {
        perspective: 1000px;
        width: 100%;
        max-width: 460px;
        height: 320px;
        margin: 25px auto;
        position: relative;
    }

    .massilly-box-3d {
        width: 100%;
        height: 100%;
        position: relative;
        transform-style: preserve-3d;
        transform: rotateX(16deg) rotateY(-8deg);
        transition: transform 1.2s cubic-bezier(0.25, 1, 0.5, 1);
    }

    /* Animation d'ouverture WHAOU avec plongeon de caméra */
    .massilly-box-3d.opening-active {
        animation: boxWhaouOpen 1.5s cubic-bezier(0.7, 0, 0.25, 1) forwards !important;
    }

    @keyframes boxWhaouOpen {
        0% {
            transform: rotateX(16deg) rotateY(-8deg) scale(1);
        }
        40% {
            transform: rotateX(25deg) rotateY(0deg) scale(1.15) translateY(20px);
        }
        100% {
            transform: rotateX(75deg) rotateY(0deg) scale(3.8) translateY(120px);
            opacity: 0.1;
        }
    }

    /* Intérieur doré étincelant de la boîte */
    .box-interior-glow {
        position: absolute;
        top: 10px;
        left: 10px;
        right: 10px;
        bottom: 10px;
        background: radial-gradient(circle, #F59E0B 0%, #D97706 40%, #000000 100%);
        border-radius: 20px;
        opacity: 0;
        transition: opacity 0.8s ease;
        box-shadow: 0 0 80px rgba(245, 158, 11, 0.9), inset 0 0 50px rgba(255, 255, 255, 0.8);
    }

    .massilly-box-3d.opening-active .box-interior-glow {
        opacity: 1 !important;
    }

    /* Corps métallique de la boîte */
    .box-body-metal {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #0A1E3F 0%, #0E529E 50%, #062850 100%) !important;
        border: 4px solid #F59E0B !important;
        border-radius: 24px !important;
        box-shadow: 
            0 25px 60px rgba(0, 0, 0, 0.8),
            inset 0 0 35px rgba(56, 189, 248, 0.4),
            0 0 35px rgba(245, 158, 11, 0.3) !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        border-bottom: 12px solid #D97706 !important;
    }

    /* Couvercle articulé */
    .box-lid-metal {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(145deg, #0E529E 0%, #1E293B 60%, #0B1329 100%) !important;
        border: 4px solid #F59E0B !important;
        border-radius: 24px !important;
        transform-origin: top center;
        transition: transform 1.2s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        backface-visibility: hidden;
    }

    .massilly-box-3d.opening-active .box-lid-metal {
        transform: rotateX(-125deg) translateY(-20px) !important;
    }

    /* Latch / Serrure or */
    .box-latch-gold {
        position: absolute;
        bottom: 15px;
        width: 50px;
        height: 22px;
        background: linear-gradient(135deg, #F59E0B, #FBBF24, #D97706);
        border-radius: 6px;
        border: 2px solid #FFFFFF;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 900;
        color: #000;
    }

    /* --- SELECTBOX XXL SMARTPHONE TACTILE --- */
    div[data-testid="stSelectbox"] > div {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 18px !important;
        min-height: 82px !important;
        padding: 10px 18px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5), inset 0 0 15px rgba(56, 189, 248, 0.2) !important;
    }

    div[data-testid="stSelectbox"] [data-baseweb="select"] {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stSelectbox"] label {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #38BDF8 !important;
        letter-spacing: 1px !important;
        margin-bottom: 8px !important;
    }

    /* --- BOUTONS VOTE (OUI / NON / N/A) --- */
    div[data-testid="stHorizontalBlock"] button {
        width: 100% !important;
        height: 115px !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        border-radius: 22px !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background: linear-gradient(135deg, #10B981, #059669) !important;
        border-bottom: 8px solid #047857 !important;
        box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2) !important;
    }

    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background: linear-gradient(135deg, #EF4444, #DC2626) !important;
        border-bottom: 8px solid #B91C1C !important;
        box-shadow: 0 10px 20px rgba(239, 68, 68, 0.2) !important;
    }

    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
        background: linear-gradient(135deg, #3B82F6, #1D4ED8) !important;
        border-bottom: 8px solid #1E40AF !important;
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.2) !important;
    }

    /* --- BOUTONS D'ACTION ET RETOUR --- */
    .stButton > button, div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #0E529E 0%, #38BDF8 50%, #0E529E 100%) !important;
        background-size: 200% auto !important;
        color: #FFFFFF !important;
        height: 85px !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        border-radius: 20px !important;
        border: none !important;
        border-bottom: 8px solid #063970 !important;
        box-shadow: 0 12px 28px rgba(14, 82, 158, 0.45) !important;
        letter-spacing: 2px;
    }

    .back-btn-container + .stButton button, .back-btn-container button {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #94A3B8 !important;
        border: 2px solid #475569 !important;
        border-bottom: none !important;
        height: 60px !important;
        font-size: 18px !important;
    }
</style>
""")

st.markdown(css_code, unsafe_allow_html=True)

# Affichage permanent du titre principal
st.markdown("<h1 class='main-header-3d'>📦 MASSILLY LOGISTIQUE</h1>", unsafe_allow_html=True)

if st.session_state.get("test_mode", False):
    st.markdown("<div class='test-badge'>🧪 SESSION DE TEST ACTIVE – ENREGISTREMENTS ISOLÉS</div>", unsafe_allow_html=True)


# ========================================== PARCOURS MULTI-ÉTAPES (ETAPES 0 à 3)
if not st.session_state.get("user_authenticated", False):
    auth_step = st.session_state.get("auth_step", 0)
    
    # ÉTAPE 0 : BIENVENUE CHEZ MASSILLY & LA BOÎTE DÉCORÉE 3D WHAOU
    if auth_step == 0:
        st.markdown("<br>", unsafe_allow_html=True)
        
        header_html = textwrap.dedent("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <div style='font-size: 1.15rem; font-weight: 800; color: #38BDF8; letter-spacing: 6px; text-transform: uppercase; margin-bottom: 6px;'>
                GROUPE MASSILLY • DEPUIS 1911
            </div>
            <h1 style='font-family: "Playfair Display", serif; font-size: 3.2rem; font-weight: 900; background: linear-gradient(135deg, #FFFFFF 20%, #38BDF8 60%, #0E529E 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 10px 30px rgba(56, 189, 248, 0.5); text-transform: uppercase;'>
                ✨ BIENVENUE CHEZ MASSILLY ✨
            </h1>
            <div style='font-size: 1.1rem; color: #94A3B8; font-weight: 700; letter-spacing: 2px;'>
                PORTAIL D'EXCELLENCE OPÉRATIONNELLE ET LOGISTIQUE 5S
            </div>
        </div>
        """)
        st.markdown(header_html, unsafe_allow_html=True)

        is_opening = st.session_state.get("opening_anim", False)
        opening_class = "opening-active" if is_opening else ""

        box_html = textwrap.dedent(f"""
        <div class='box-scene-container'>
            <div class='massilly-box-3d {opening_class}'>
                <div class='box-interior-glow'></div>
                
                <div class='box-body-metal'>
                    <div style='font-size: 3rem;'>🎁</div>
                    <div style='font-family: "Playfair Display", serif; font-size: 1.8rem; font-weight: 900; color: #FBBF24; letter-spacing: 3px; margin-top: 5px;'>
                        MASSILLY 1911
                    </div>
                    <div style='font-size: 0.95rem; color: #38BDF8; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; margin-top: 4px;'>
                        EXCELLENCE OPÉRATIONNELLE
                    </div>
                </div>
                
                <div class='box-lid-metal'>
                    <div style='font-size: 3.5rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.5));'>⚙️</div>
                    <div style='font-family: "Playfair Display", serif; font-size: 1.7rem; font-weight: 900; color: #FFFFFF; letter-spacing: 4px; margin-top: 6px;'>
                        MASSILLY
                    </div>
                    <div style='font-size: 0.85rem; color: #FBBF24; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; margin-top: 2px;'>
                        FABRIQUÉ EN FRANCE • 5S
                    </div>
                    <div class='box-latch-gold'>🔒 1911</div>
                </div>
            </div>
        </div>
        """)
        st.markdown(box_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
        if st.button("🎁 ENTRER DANS L'APPLICATION", use_container_width=True):
            st.session_state.opening_anim = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if is_opening:
            import time
            st.session_state.opening_anim = False
            st.session_state.auth_step = 1
            st.rerun()

    # ÉTAPE 1 : CHOIX DU RÔLE
    elif auth_step == 1:
        st.markdown("<div class='user-id-badge-3d'>📋 SÉLECTIONNEZ VOTRE RÔLE</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; font-weight: bold;'>Choisissez votre profil d'accès :</p>", unsafe_allow_html=True)
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            if st.button("🎯 Sponsor de zone", use_container_width=True):
                st.session_state.user_role = "Sponsor de zone"
                st.session_state.auth_step = 2
                st.rerun()
        with col_r2:
            if st.button("🔍 Référent 5S", use_container_width=True):
                st.session_state.user_role = "Référent 5S"
                st.session_state.auth_step = 2
                st.rerun()
        with col_r3:
            if st.button("⚙️ Administrateur", use_container_width=True):
                st.session_state.user_role = "Éditeur (Méthodes / Alternant)"
                st.session_state.auth_step = 2
                st.rerun()
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
        if st.button("⬅️ Retour à l'accueil", use_container_width=True):
            st.session_state.auth_step = 0
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    # ÉTAPE 2 : CHOIX DU NOM (PRÉNOM SEUL / PRÉNOM N.)
    elif auth_step == 2:
        st.markdown("<div class='user-id-badge-3d'>👤 SÉLECTION DU NOM</div>", unsafe_allow_html=True)
        
        PERSONNES_MASSILLY_RAW = [
            {"prenom": "Damien", "nom": "Labbé", "full": "Damien Labbé"},
            {"prenom": "Audrey", "nom": "Sordet", "full": "Audrey Sordet"},
            {"prenom": "Anthony", "nom": "Duplessis", "full": "Anthony Duplessis"},
            {"prenom": "Jonathan", "nom": "Mele", "full": "Jonathan Mele"},
            {"prenom": "Thomas", "nom": "Collin", "full": "Thomas Collin"},
            {"prenom": "Gaspard", "nom": "Sommereux", "full": "Gaspard Sommereux"},
            {"prenom": "Mariia", "nom": "Leliukh", "full": "Mariia Leliukh"},
            {"prenom": "Céline", "nom": "Hereng", "full": "Céline Hereng"},
            {"prenom": "Dimitri", "nom": "Dupasquier", "full": "Dimitri Dupasquier"},
            {"prenom": "Frédéric", "nom": "Bouvy", "full": "Frédéric Bouvy"},
            {"prenom": "Nathalie", "nom": "Berthelin", "full": "Nathalie Berthelin"}
        ]
        
        counts_prenom = {}
        for p in PERSONNES_MASSILLY_RAW:
            counts_prenom[p["prenom"]] = counts_prenom.get(p["prenom"], 0) + 1
            
        options_map = {}
        options_liste = []
        for p in PERSONNES_MASSILLY_RAW:
            if counts_prenom[p["prenom"]] > 1:
                disp = f"{p['prenom']} {p['nom'][0]}."
            else:
                disp = p["prenom"]
            options_map[disp] = p["full"]
            options_liste.append(disp)
            
        options_liste.append("Autre (Saisie manuelle)...")
        
        nom_select = st.selectbox("Sélectionnez votre Prénom :", options_liste)
        if nom_select == "Autre (Saisie manuelle)...":
            nom_complet = st.text_input("Saisissez votre Prénom et Nom :")
        else:
            nom_complet = options_map.get(nom_select, nom_select)
            
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
            if st.button("⬅️ Retour au choix du rôle", use_container_width=True):
                st.session_state.auth_step = 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with col_n2:
            st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
            if st.button("CONTINUER VERS LE CHOIX DE ZONE ➡️", use_container_width=True):
                if not nom_complet.strip():
                    st.error("Veuillez renseigner votre nom.")
                else:
                    st.session_state.user_name = nom_complet
                    st.session_state.auth_step = 3
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    # ÉTAPE 3 : SÉLECTION DE LA ZONE & CONFIGURATION
    elif auth_step == 3:
        st.markdown("<div class='user-id-badge-3d'>📍 ZONE LOGISTIQUE CIBLÉE</div>", unsafe_allow_html=True)
        st.info(f"Profil configuré : **{st.session_state.get('user_name', '')}** ({st.session_state.get('user_role', '')})")
        
        liste_zones = list(ZONES_MASSILLY.keys())
        zone_select = st.selectbox(
            "Zone logistique ciblée :",
            liste_zones,
            format_func=lambda x: ZONES_MASSILLY[x]["label"]
        )
        
        st.markdown("---")
        st.markdown("### Configuration & Test GSheets")
        st.session_state.test_mode = st.checkbox(
            "🧪 Activer le MODE TEST d'entraînement",
            value=st.session_state.get("test_mode", False)
        )
        
        if st.button("🔌 TESTER CONNEXION GOOGLE SHEETS", use_container_width=True):
            ok, err = sauvegarder_audit_local({
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Zone": "TEST_CONNEXION",
                "Sponsor": "SYSTEM",
                "Auditeur": st.session_state.get('user_name', 'TEST'),
                "Role": st.session_state.get('user_role', 'TEST'),
                "Score_Total": 15,
                "Pourcentage": 100,
                "Observations": "Test automatique de connexion depuis l'écran d'accueil",
                "Actions_Correctives": "Aucune"
            })
            if ok:
                st.success("✅ Connexion Google Sheets fonctionnelle ! L'audit de test a été enregistré.")
            else:
                st.error(f"❌ Échec de connexion : {err}")
                
        st.markdown("<br>", unsafe_allow_html=True)
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
            if st.button("⬅️ Retour au choix du nom", use_container_width=True):
                st.session_state.auth_step = 2
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with col_z2:
            st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
            if st.button("🔓 COMMENCER LE DIAGNOSTIC DE ZONE", use_container_width=True):
                st.session_state.user_zone = zone_select
                st.session_state.user_authenticated = True
                st.session_state.auth_step = 0
                st.session_state.portal_shown = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ========================================== APPLICATION PRINCIPALE (UTILISATEUR CONNECTÉ)
else:
    col_u1, col_u2 = st.columns([4, 1])
    with col_u1:
        st.markdown(
            f"👤 **{st.session_state.get('user_name', '')}** ({st.session_state.get('user_role', '')}) | Zone active : **{ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]['label']}**"
        )
    with col_u2:
        st.markdown("<div class='small-btn-container'>", unsafe_allow_html=True)
        if st.button("🔄 Changer d'utilisateur", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.auth_step = 0
            st.session_state.audit_started = False
            st.session_state.current_q_idx = 0
            st.session_state.answers = {}
            st.session_state.portal_shown = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("---")

    # Onglets horizontaux de navigation
    onglets = ["📋 Saisie d'Audit terrain", "📊 Analyse & Historique", "🗺️ Rappel des Standards"]
    menu_actif = st.radio("Menu principal :", onglets, horizontal=True, key="menu_actif")

    st.markdown("---")

    # ========================================== ONGLET 1 : SAISIE D'AUDIT COMPORTEMENTAL
    if menu_actif == "📋 Saisie d'Audit terrain":
        
        if not st.session_state.audit_started:
            st.markdown("<div class='btn-start-3d'>", unsafe_allow_html=True)
            btn_label = f"DÉMARRER UNE NOUVELLE VISITE 5S\n\n🚀 COMMENCER LE DIAGNOSTIC TECHNIQUE\n\n📍 Zone Active : {ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]['label']}\nSponsor Responsable : {ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]['sponsor']}"
            if st.button(btn_label, use_container_width=True):
                st.session_state.audit_started = True
                st.session_state.current_q_idx = 0
                st.session_state.answers = {}
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            idx = st.session_state.current_q_idx
            total_q = len(CRITERES_OFFICIELS)
            
            if idx < total_q:
                crit = CRITERES_OFFICIELS[idx]
                pct_prog = int(((idx + 1) / total_q) * 100)
                
                st.progress(pct_prog / 100.0)
                st.markdown(f"<p style='text-align: right; font-size: 16px; color: #CBD5E1; font-weight: bold;'>Étape {idx + 1} sur {total_q} ({pct_prog}%)</p>", unsafe_allow_html=True)
                
                card_html = textwrap.dedent(f"""
                <div class='question-card'>
                    <div class='question-cat'>{crit['cat']}</div>
                    <div class='question-text'>{crit['txt']}</div>
                </div>
                """)
                st.markdown(card_html, unsafe_allow_html=True)
                
                col_b1, col_b2, col_b3 = st.columns(3)
                with col_b1:
                    if st.button("🟢 OUI", key=f"btn_oui_{idx}", use_container_width=True):
                        st.session_state.answers[crit["id"]] = "OUI"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with col_b2:
                    if st.button("🔴 NON", key=f"btn_non_{idx}", use_container_width=True):
                        st.session_state.answers[crit["id"]] = "NON"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with col_b3:
                    if st.button("🔵 N/A", key=f"btn_na_{idx}", use_container_width=True):
                        st.session_state.answers[crit["id"]] = "N/A"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                        
                st.markdown("<br>", unsafe_allow_html=True)
                if idx > 0:
                    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                    if st.button("⬅️ Question précédente", use_container_width=True):
                        st.session_state.current_q_idx -= 1
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            else:
                st.markdown("## 🎯 Diagnostic terminé !")
                t_oui = sum(1 for v in st.session_state.answers.values() if v == "OUI")
                t_non = sum(1 for v in st.session_state.answers.values() if v == "NON")
                t_na = sum(1 for v in st.session_state.answers.values() if v == "N/A")
                
                sc_total = t_oui
                pct_final = int((sc_total / 15) * 100) if 15 > 0 else 0
                
                st.markdown(f"### Score Total : {sc_total} / 15 ({pct_final}%)")
                
                obs = st.text_area("Observations terrain / Anomalies constatées :", "")
                act = st.text_area("Actions correctives immédiates proposées :", "")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
                if st.button("💾 VALIDER ET ENREGISTRER L'AUDIT", use_container_width=True):
                    audit_data = {
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Zone": ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]["label"],
                        "Sponsor": ZONES_MASSILLY[st.session_state.get('user_zone', 'Zone 1')]["sponsor"],
                        "Auditeur": st.session_state.get('user_name', ''),
                        "Role": st.session_state.get('user_role', ''),
                        "Score_Total": sc_total,
                        "Pourcentage": pct_final,
                        "Observations": obs,
                        "Actions_Correctives": act
                    }
                    for c in CRITERES_OFFICIELS:
                        audit_data[c["id"]] = st.session_state.answers.get(c["id"], "N/A")
                        
                    gs_ok, err_msg = sauvegarder_audit_local(audit_data)
                    
                    st.session_state.audit_started = False
                    st.session_state.current_q_idx = 0
                    st.session_state.answers = {}
                    
                    if gs_ok:
                        st.success("✅ Audit enregistré avec succès dans Google Sheets et sur le serveur !")
                    else:
                        st.warning(f"⚠️ Audit enregistré en sauvegarde locale CSV. (Sync GSheets: {err_msg})")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # ========================================== ONGLET 2 : ANALYSE & HISTORIQUE
    elif menu_actif == "📊 Analyse & Historique":
        st.markdown("### Historique des audits enregistrés")
        df_hist = charger_audits()
        if df_hist is not None and not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("Aucun audit enregistré pour le moment.")

    # ========================================== ONGLET 3 : RAPPEL DES STANDARDS
    elif menu_actif == "🗺️ Rappel des Standards":
        st.markdown("### Standards 5S Usine Massilly")
        for z_key, z_val in ZONES_MASSILLY.items():
            st.markdown(f"**{z_val['label']}** — Sponsor : *{z_val['sponsor']}*")
