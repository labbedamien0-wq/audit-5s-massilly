import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

try:
    from streamlit_gsheets import GSheetsConnection
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
    page_title="Massilly - Audit 5S Mobile v15",
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
    # Seiri (Trier)
    {
        "id": "c1",
        "cat": "1. Sort (Seiri) - Trier",
        "txt": "Les éléments inutiles ont été supprimés de la zone (au sol, sur les murs, autour des piliers, au plafond, sur les abords)."
    },
    {
        "id": "c2",
        "cat": "1. Sort (Seiri) - Trier",
        "txt": "Les tiroirs, établis, servantes et armoires sont vidés des choses inutiles ou superflues."
    },
    {
        "id": "c3",
        "cat": "1. Sort (Seiri) - Trier",
        "txt": "Les allées de circulation sont dégagées et propres (absence d'encombrement par des palettes)."
    },
    # Seiton (Ranger)
    {
        "id": "c4",
        "cat": "2. Straighten (Seiton) - Ranger",
        "txt": "Tous les équipements, bennes, palettes et outils de la zone ont un marquage au sol et sont bien rangés à leur emplacement."
    },
    {
        "id": "c5",
        "cat": "2. Straighten (Seiton) - Ranger",
        "txt": "Le matériel de fourniture, de consommable et les outils de nettoyage sont clairement identifiés, étiquetés et rangés."
    },
    {
        "id": "c6",
        "cat": "2. Straighten (Seiton) - Ranger",
        "txt": "Les matières premières et produits bloqués sont correctement stockés dans la zone (présence de la feuille d'identification bleue)."
    },
    # Seiso (Nettoyer)
    {
        "id": "c7",
        "cat": "3. Sweep (Seiso) - Nettoyer",
        "txt": "Les sols, les surfaces de travail, l'équipement et les aires d'entreposage de la zone sont propres (sans poussière ni résidus)."
    },
    {
        "id": "c8",
        "cat": "3. Sweep (Seiso) - Nettoyer",
        "txt": "Les déchets et les matières recyclables sont collectés et éliminés correctement (respect du tri sélectif cartons/plastiques)."
    },
    {
        "id": "c9",
        "cat": "3. Sweep (Seiso) - Nettoyer",
        "txt": "L'environnement de travail est bon (éclairages fonctionnels, absence de poussière excessive, marquage au sol bien visible)."
    },
    # Seiketsu (Standardiser)
    {
        "id": "c10",
        "cat": "4. Standardize (Seiketsu) - Standardiser",
        "txt": "Les rôles sont clairement définis pour garder la zone propre et ordonnée (Opérateurs, planning de nettoyage...)."
    },
    {
        "id": "c11",
        "cat": "4. Standardize (Seiketsu) - Standardiser",
        "txt": "Les tâches standard liées au nettoyage et à l'organisation sont définies (Rituel de fin de poste de 5-10 minutes...)."
    },
    {
        "id": "c12",
        "cat": "4. Standardize (Seiketsu) - Standardiser",
        "txt": "Il est évident visuellement qu'il y a une place désignée pour chaque chose (bennes, corbeilles, balais...)."
    },
    # Shitsuke (Maintenir)
    {
        "id": "c13",
        "cat": "5. Sustain (Shitsuke) - Maintenir/Respecter",
        "txt": "La zone présente une bonne organisation générale et ne présente aucun danger pour la sécurité du personnel (pas de risque de chute)."
    },
    {
        "id": "c14",
        "cat": "5. Sustain (Shitsuke) - Maintenir/Respecter",
        "txt": "Les documents et instructions visuelles de la zone sont à jour (pas de feuilles volantes ou de notes obsolètes)."
    },
    {
        "id": "c15",
        "cat": "5. Sustain (Shitsuke) - Maintenir/Respecter",
        "txt": "Le standard de la zone est conforme, pertinent et respecté au quotidien par l'ensemble de l'équipe terrain."
    }
]

# Initialisation robuste de la session
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

# Définition dynamique des fichiers de données selon le mode (Réel vs Test)
if st.session_state.get("test_mode", False):
    SHARED_DATA_FILE = "test_suivi_audits_5s.csv"
    SHARED_LOG_FILE = "test_journal_activite_5s.json"
else:
    SHARED_DATA_FILE = "suivi_audits_5s.csv"
    SHARED_LOG_FILE = "journal_activite_5s.json"

# Création automatique des fichiers s'ils n'existent pas
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

    # Backup local CSV
    try:
        df = pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
    except Exception:
        df = pd.DataFrame()

    new_row = pd.DataFrame([data_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

    # Journal JSON
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


# ========================================== STYLE CSS : EFFET WAHOU CINÉMATIQUE 3D ET BLEU MASSILLY
st.markdown("""
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
        cursor: pointer;
        transition: all 0.3s ease !important;
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
        margin: 25px auto 40px auto !important;
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

    /* --- SCÈNE D'ACCUEIL ANIMÉE ET SYMBOLES MASSILLY EN VOL --- */
    .welcome-hero-container {
        text-align: center;
        padding: 40px 20px;
        position: relative;
        overflow: hidden;
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
        border: 3px solid #38BDF8;
        border-radius: 28px;
        box-shadow: 0 20px 50px rgba(56, 189, 248, 0.3);
        margin-bottom: 35px;
    }

    .welcome-title-glow {
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #FFFFFF, #38BDF8, #0E529E);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(56, 189, 248, 0.8);
        letter-spacing: 3px;
        margin-bottom: 25px;
    }

    .floating-symbols-field {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin: 35px 0;
        font-size: 3.8rem;
    }

    .sym-fly-1 { animation: floatOrbit1 4s ease-in-out infinite alternate; }
    .sym-fly-2 { animation: floatOrbit2 5s ease-in-out infinite alternate; }
    .sym-fly-3 { animation: floatOrbit3 3.5s ease-in-out infinite alternate; }
    .sym-fly-4 { animation: floatOrbit1 4.5s ease-in-out infinite alternate; }
    .sym-fly-5 { animation: floatOrbit2 3.8s ease-in-out infinite alternate; }

    @keyframes floatOrbit1 {
        0% { transform: translateY(0px) rotate(0deg) scale(1); }
        100% { transform: translateY(-18px) rotate(12deg) scale(1.15); }
    }
    @keyframes floatOrbit2 {
        0% { transform: translateY(0px) rotate(0deg) scale(1); }
        100% { transform: translateY(20px) rotate(-15deg) scale(0.9); }
    }
    @keyframes floatOrbit3 {
        0% { transform: translateY(0px) rotate(0deg) scale(1.05); }
        100% { transform: translateY(-25px) rotate(8deg) scale(1.2); }
    }

    /* --- MENUS DÉROULANTS (SELECTBOX) XXL MULTI-TACTILE MOBILE --- */
    div[data-testid="stSelectbox"] > div {
        min-height: 82px !important;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95)) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(56, 189, 248, 0.25) !important;
        display: flex !important;
        align-items: center !important;
        padding: 8px 16px !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        letter-spacing: 1px !important;
    }

    div[data-testid="stSelectbox"] label {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #38BDF8 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        margin-bottom: 12px !important;
    }

    div[data-baseweb="menu"] li {
        min-height: 72px !important;
        font-size: 22px !important;
        font-weight: 700 !important;
        padding: 18px 24px !important;
    }

    /* --- ONGLES DU MENU PRINCIPAL 3D --- */
    div[data-testid="stRadio"] div[role="radiogroup"], 
    div.row-widget.stRadio > div {
        background: linear-gradient(180deg, #1E293B, #0F172A) !important;
        border: 3px solid #334155 !important;
        border-radius: 20px !important;
        padding: 12px 16px !important;
        gap: 16px !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-around !important;
        box-shadow: 
            inset 0 4px 12px rgba(0, 0, 0, 0.6),
            0 10px 20px rgba(0, 0, 0, 0.4) !important;
        perspective: 1000px;
        margin-bottom: 25px !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label, 
    div.row-widget.stRadio label {
        background: linear-gradient(135deg, #334155, #1E293B) !important;
        color: #94A3B8 !important;
        border: 2px solid #475569 !important;
        border-bottom: 6px solid #0F172A !important; 
        border-radius: 14px !important;
        padding: 14px 28px !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        text-align: center !important;
        transform: translateY(-2px) rotateX(10deg);
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
    div.row-widget.stRadio label:has(input:checked) {
        background: linear-gradient(135deg, #0E529E 0%, #38BDF8 100%) !important;
        color: #FFFFFF !important;
        border-color: #38BDF8 !important;
        border-bottom: 2px solid #063970 !important;
        transform: translateY(4px) rotateX(0deg) scale(0.98) !important;
        box-shadow: 
            0 0 35px rgba(56, 189, 248, 0.85),
            0 0 15px rgba(56, 189, 248, 0.4),
            inset 0 0 12px rgba(255, 255, 255, 0.3) !important;
    }

    /* --- CARTES DE CONTENU D'AUDIT 3D --- */
    .question-card {
        background-color: #FFFFFF !important;
        border: 2px solid #E2E8F0 !important;
        border-left: 8px solid #0E529E !important;
        border-radius: 20px !important;
        padding: 30px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3) !important;
    }

    .question-cat {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        color: #0E529E !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
    }

    .question-text {
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        line-height: 1.45;
    }

    /* --- STYLE GLOBAL DES BOUTONS DE L'APPLICATION --- */
    .stButton > button,
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #0E529E 0%, #38BDF8 50%, #0E529E 100%) !important;
        background-size: 200% auto !important;
        color: #FFFFFF !important;
        height: 85px !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        border-radius: 20px !important;
        border: none !important;
        border-bottom: 10px solid #063970 !important;
        box-shadow: 
            0 15px 30px rgba(14, 82, 158, 0.45),
            0 0 20px rgba(56, 189, 248, 0.3) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6) !important;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        letter-spacing: 3px;
        transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        animation: pulseGlow 2s infinite alternate !important;
    }

    .stButton > button::before,
    div[data-testid="stButton"] button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 40%;
        height: 100%;
        background: linear-gradient(
            to right, 
            rgba(255,255,255,0) 0%, 
            rgba(255,255,255,0.6) 50%, 
            rgba(255,255,255,0) 100%
        );
        transform: skewX(-25deg);
        animation: shineSweep 2.2s infinite !important;
    }

    @keyframes shineSweep {
        0% { left: -120%; }
        100% { left: 220%; }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 10px 20px rgba(14, 82, 158, 0.3), 0 0 10px rgba(56, 189, 248, 0.2); }
        100% { box-shadow: 0 10px 40px rgba(56, 189, 248, 0.75), 0 0 25px rgba(56, 189, 248, 0.4); }
    }

    /* --- BOUTONS DE VOTE (OUI / NON / N/A) --- */
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

    /* --- BOUTONS RETOUR & PETITS BOUTONS --- */
    .back-btn-container + .stButton button,
    .back-btn-container + div.stButton button,
    .back-btn-container button {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #94A3B8 !important;
        border: 2px solid #475569 !important;
        border-bottom: none !important;
        height: 60px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }

    .small-btn-container + .stButton button,
    .small-btn-container + div.stButton button,
    .small-btn-container button {
        height: 50px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border-bottom: 3px solid #0B1329 !important;
        background: #1E293B !important;
    }
</style>
""", unsafe_allow_html=True)

# Affichage permanent du titre principal extrudé 3D
st.markdown("<h1 class='main-header-3d'>📦 MASSILLY LOGISTIQUE</h1>", unsafe_allow_html=True)

if st.session_state.get("test_mode", False):
    st.markdown("<div class='test-badge'>🧪 SESSION DE TEST ACTIVE – ENREGISTREMENTS ISOLÉS</div>", unsafe_allow_html=True)


# ========================================== ÉCRAN 1 : CONNEXION MULTI-ÉTAPES (ETAPES 0 à 4)
if not st.session_state.get("user_authenticated", False):
    auth_step = st.session_state.get("auth_step", 0)
    
    # ÉTAPE 0 : PAGE DE BIENVENUE AVEC SYMBOLES MASSILLY ANIMÉS EN VOL
    if auth_step == 0:
        st.markdown("""
        <div class='welcome-hero-container'>
            <div class='welcome-title-glow'>✨ BIENVENUE CHEZ MASSILLY ✨</div>
            <div style='font-size: 1.3rem; font-weight: 700; color: #E2E8F0; letter-spacing: 2px;'>
                LEADER DE L'EMBALLAGE MÉTALLIQUE INDUSTRIEL
            </div>
            
            <!-- SYMBOLES MASSILLY EN FLOTTAISON 3D -->
            <div class='floating-symbols-field'>
                <span class='sym-fly-1' title='Boîte Décorée'>🥫</span>
                <span class='sym-fly-2' title='Boîte à Lait'>🥛</span>
                <span class='sym-fly-3' title='Capsule EuroCap'>🍾</span>
                <span class='sym-fly-4' title='Emballage Métallique'>📦</span>
                <span class='sym-fly-5' title='Aérosol Haute Performance'>💈</span>
                <span class='sym-fly-1' title='Capsule Couronne'>👑</span>
            </div>

            <div style='font-size: 1.15rem; color: #38BDF8; font-weight: 800; letter-spacing: 3px; text-transform: uppercase;'>
                PORTAIL DE DIAGNOSTIC D'EXCELLENCE OPÉRATIONNELLE 5S
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
        if st.button("🚀 ENTRER DANS L'APPLICATION 5S", use_container_width=True):
            st.session_state.auth_step = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ÉTAPE 1 : ACCUEIL PRESTIGE AVEC BADGE CLIQUABLE
    elif auth_step == 1:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='user-id-badge-3d'>📋 PORTAIL D'IDENTIFICATION DE L'UTILISATEUR</div>", unsafe_allow_html=True)
        st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
        if st.button("🚀 CLIQUER ICI POUR VOUS IDENTIFIER", use_container_width=True):
            st.session_state.auth_step = 2
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class='welcome-hero-container' style='margin-top: 25px;'>
            <div style='font-size: 2.2rem; font-weight: 900; color: #38BDF8;'>✨ 5S ✨</div>
            <div style='font-size: 1.3rem; font-weight: 800; color: #FFFFFF; letter-spacing: 4px; text-transform: uppercase; margin-top: 10px;'>
                SEIRI • SEITON • SEISO • SEIKETSU • SHITSUKE
            </div>
            <div style='font-size: 1.05rem; color: #94A3B8; margin-top: 8px; font-weight: 600;'>
                MÉTHODE D'EXCELLENCE OPÉRATIONNELLE LOGISTIQUE MASSILLY
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # ÉTAPE 2 : CHOIX DU RÔLE
    elif auth_step == 2:
        st.markdown("<div class='user-id-badge-3d'>📋 SÉLECTIONNEZ VOTRE RÔLE</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; font-weight: bold;'>Choisissez votre profil d'accès :</p>", unsafe_allow_html=True)
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            if st.button("🎯 Sponsor de zone", use_container_width=True):
                st.session_state.user_role = "Sponsor de zone"
                st.session_state.auth_step = 3
                st.rerun()
        with col_r2:
            if st.button("🔍 Référent 5S", use_container_width=True):
                st.session_state.user_role = "Référent 5S"
                st.session_state.auth_step = 3
                st.rerun()
        with col_r3:
            if st.button("⚙️ Administrateur", use_container_width=True):
                st.session_state.user_role = "Éditeur (Méthodes / Alternant)"
                st.session_state.auth_step = 3
                st.rerun()
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
        if st.button("⬅️ Retour à l'accueil", use_container_width=True):
            st.session_state.auth_step = 0
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    # ÉTAPE 3 : CHOIX DU NOM SELON LE RÔLE (ÉPURÉ PAR PRÉNOM SEUL / PRÉNOM N.)
    elif auth_step == 3:
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
                st.session_state.auth_step = 2
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with col_n2:
            st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
            if st.button("CONTINUER VERS LE CHOIX DE ZONE ➡️", use_container_width=True):
                if not nom_complet.strip():
                    st.error("Veuillez renseigner votre nom.")
                else:
                    st.session_state.user_name = nom_complet
                    st.session_state.auth_step = 4
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    # ÉTAPE 4 : SÉLECTION DE LA ZONE & CONFIGURATION
    elif auth_step == 4:
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
                st.session_state.auth_step = 3
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
                st.session_state.audit_saved = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            idx = st.session_state.current_q_idx
            total_q = len(CRITERES_OFFICIELS)
            
            if idx < total_q:
                crit = CRITERES_OFFICIELS[idx]
                st.markdown(f"<p style='text-align: right; font-size: 16px; color: #CBD5E1; font-weight: bold;'>Critère {idx + 1} sur {total_q}</p>", unsafe_allow_html=True)
                st.progress((idx + 1) / total_q)
                
                st.markdown(f"""
                <div class='question-card'>
                    <div class='question-cat'>{crit['cat']}</div>
                    <div class='question-text'>{crit['txt']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<p style='font-size: 18px; font-weight: bold; color: #FFFFFF; margin-top: 15px;'>Évaluation terrain :</p>", unsafe_allow_html=True)
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("🟢 OUI (Conforme)", key=f"btn_oui_{idx}", use_container_width=True):
                        st.session_state.answers[crit["id"]] = "OUI"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                        
                with col_btn2:
                    if st.button("🔴 NON (Écart)", key=f"btn_non_{idx}", use_container_width=True):
                        st.session_state.answers[crit["id"]] = "NON"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                        
                with col_btn3:
                    if st.button("🔵 N/A (Non applicable)", key=f"btn_na_{idx}", use_container_width=True):
                        st.session_state.answers[crit["id"]] = "N/A"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                        
                if idx > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                    if st.button("⬅️ Question précédente", use_container_width=True):
                        st.session_state.current_q_idx -= 1
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            else:
                st.markdown("<div class='user-id-badge-3d'>📊 SYNTHÈSE DU DIAGNOSTIC 5S</div>", unsafe_allow_html=True)
                
                t_oui = sum(1 for v in st.session_state.answers.values() if v == "OUI")
                t_non = sum(1 for v in st.session_state.answers.values() if v == "NON")
                t_na = sum(1 for v in st.session_state.answers.values() if v == "N/A")
                
                denom = t_oui + t_non
                pct = round((t_oui / denom) * 100, 1) if denom > 0 else 0.0
                
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Score Conforme", f"{t_oui} / 15")
                col_m2.metric("Écarts Détectés", f"{t_non}")
                col_m3.metric("Non Applicable", f"{t_na}")
                col_m4.metric("Taux de Conformité", f"{pct} %")
                
                st.markdown("---")
                
                st.markdown("### 📝 Observations terrain & Actions")
                obs = st.text_area("Remarques / Anomales observées pendant la visite :", height=100)
                actions = st.text_area("Actions correctives immédiates engagées ou recommandées :", height=100)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
                if st.button("💾 ENREGISTRER L'AUDIT SUR GOOGLE SHEETS", use_container_width=True):
                    zone_cle = st.session_state.get('user_zone', 'Zone 1')
                    data_save = {
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Zone": ZONES_MASSILLY[zone_cle]["label"],
                        "Sponsor": ZONES_MASSILLY[zone_cle]["sponsor"],
                        "Auditeur": st.session_state.get('user_name', 'Inconnu'),
                        "Role": st.session_state.get('user_role', 'Auditeur'),
                        "Score_Total": t_oui,
                        "Pourcentage": pct,
                        "Observations": obs,
                        "Actions_Correctives": actions
                    }
                    for c in CRITERES_OFFICIELS:
                        data_save[c["id"]] = st.session_state.answers.get(c["id"], "N/A")
                        
                    ok, err = sauvegarder_audit_local(data_save)
                    st.session_state.audit_saved = True
                    st.session_state.save_result_ok = ok
                    st.session_state.save_result_err = err
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

                if st.session_state.get("audit_saved", False):
                    if st.session_state.get("save_result_ok", False):
                        st.success("✅ Audit enregistré avec succès dans Google Sheets et dans la base locale !")
                    else:
                        st.warning("⚠️ Audit sauvegardé localement (Backup CSV). Connexion Google Sheets en attente.")
                        
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                if st.button("🔄 NOUVEL AUDIT TERRAIN", use_container_width=True):
                    st.session_state.audit_started = False
                    st.session_state.current_q_idx = 0
                    st.session_state.answers = {}
                    st.session_state.audit_saved = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # ========================================== ONGLET 2 : ANALYSE & HISTORIQUE
    elif menu_actif == "📊 Analyse & Historique":
        st.markdown("### Historique des audits")
        df_hist = charger_audits()
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("Aucun audit enregistré pour le moment.")

    # ========================================== ONGLET 3 : RAPPEL DES STANDARDS
    elif menu_actif == "🗺️ Rappel des Standards":
        st.markdown("### Les 5 Piliers de la Méthode 5S chez Massilly")
        st.markdown("""
        - **1. Seiri (Trier)** : Éliminer l'inutile dans les allées et postes de travail.
        - **2. Seiton (Ranger)** : Une place pour chaque outil, bac ou palette.
        - **3. Seiso (Nettoyer)** : Inspection visuelle et propreté des zones.
        - **4. Seiketsu (Standardiser)** : Règles claires et check-lists visuelles.
        - **5. Shitsuke (Maintenir)** : Rigueur quotidienne et audits réguliers.
        """)
