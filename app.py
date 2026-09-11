import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

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
    page_title="Massilly - Audit 5S Mobile v14",
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
st.session_state.setdefault("audit_saved", False)

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


# ========================================== STYLE CSS : DESIGN 3D PURE ET SÉCURISÉ
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;600;700;800&family=Playfair+Display:ital,wght=0,600;0,800;1,600&display=swap');

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
        0% { transform: perspective(800px) rotateX(15deg) translateY(0px); }
        100% { transform: perspective(800px) rotateX(15deg) translateY(-10px); }
    }

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
        margin: 20px auto 30px auto !important;
        max-width: 820px;
        box-shadow: 0 15px 35px rgba(56, 189, 248, 0.4) !important;
    }

    /* --- CARTE BOÎTE DÉCORÉE MASSILLY 1911 (ACCEUIL 3D PRESTIGE) --- */
    .massilly-box-card-3d {
        background: linear-gradient(135deg, #0A1E3F 0%, #0E529E 60%, #062850 100%) !important;
        border: 4px solid #F59E0B !important; /* Dorure Or Massilly */
        border-radius: 24px !important;
        padding: 40px 25px !important;
        text-align: center !important;
        margin: 25px auto !important;
        max-width: 650px !important;
        box-shadow: 
            0 20px 50px rgba(0, 0, 0, 0.8),
            0 0 30px rgba(245, 158, 11, 0.4) !important;
        transform: perspective(800px) rotateX(5deg);
        animation: boxFloat 3.5s ease-in-out infinite alternate !important;
    }

    @keyframes boxFloat {
        0% { transform: perspective(800px) rotateX(5deg) translateY(0px); }
        100% { transform: perspective(800px) rotateX(5deg) translateY(-12px); }
    }

    /* --- SELECTBOX XXL TACTILE SPÉCIALE SMARTPHONE --- */
    div[data-testid="stSelectbox"] > div {
        background: linear-gradient(135deg, #1E293B, #0F172A) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 18px !important;
        min-height: 82px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
        display: flex !important;
        align-items: center !important;
    }

    div[data-testid="stSelectbox"] div[role="combobox"] {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        padding-left: 20px !important;
    }

    div[data-testid="stSelectbox"] label {
        font-size: 22px !important;
        font-weight: 900 !important;
        color: #38BDF8 !important;
        letter-spacing: 1.5px !important;
        margin-bottom: 12px !important;
        text-transform: uppercase !important;
    }

    /* --- TOUS LES BOUTONS PRESTIGE 3D --- */
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
        box-shadow: 0 15px 30px rgba(14, 82, 158, 0.45) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6) !important;
        cursor: pointer !important;
        letter-spacing: 2px !important;
    }

    /* Boutons de vote (OUI / NON / N/A) */
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
    }

    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background: linear-gradient(135deg, #EF4444, #DC2626) !important;
        border-bottom: 8px solid #B91C1C !important;
    }

    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
        background: linear-gradient(135deg, #3B82F6, #1D4ED8) !important;
        border-bottom: 8px solid #1E40AF !important;
    }

    .back-btn-container + .stButton button, .back-btn-container button {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #94A3B8 !important;
        border: 2px solid #475569 !important;
        height: 60px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
    }

    .small-btn-container + .stButton button, .small-btn-container button {
        height: 50px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        background: #1E293B !important;
    }

    /* ========================================== EXPLOSION DE PARTICULES 3D PLEIN ÉCRAN ========================================== */
    .explosion-overlay {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 999999 !important;
        background: rgba(10, 17, 40, 0.92) !important;
        backdrop-filter: blur(12px) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }

    .explosion-core-flash {
        position: absolute;
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, #FFFFFF 0%, #38BDF8 50%, rgba(56,189,248,0) 100%);
        border-radius: 50%;
        animation: coreFlash 1.1s ease-out forwards;
    }

    @keyframes coreFlash {
        0% { transform: scale(0.1); opacity: 1; filter: drop-shadow(0 0 50px #38BDF8); }
        50% { transform: scale(8); opacity: 0.9; filter: drop-shadow(0 0 120px #FFFFFF); }
        100% { transform: scale(25); opacity: 0; }
    }

    .particle-3d {
        position: absolute;
        font-size: 2.8rem;
        user-select: none;
        animation: burstOut 1.1s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
    }

    @keyframes burstOut {
        0% {
            transform: translate(0, 0) scale(0.2) rotate(0deg);
            opacity: 1;
            filter: drop-shadow(0 0 10px #38BDF8);
        }
        70% {
            opacity: 1;
            filter: drop-shadow(0 0 25px #F59E0B);
        }
        100% {
            transform: translate(var(--tx), var(--ty)) scale(2.2) rotate(var(--rot));
            opacity: 0;
            filter: drop-shadow(0 0 40px rgba(255,255,255,0));
        }
    }

    /* --- LOGO 5S FLOTTANT 3D HAUTE DÉFINITION (ACCUEIL) --- */
    .logo-5s-3d-floating {
        background: linear-gradient(135deg, rgba(14, 82, 158, 0.35), rgba(15, 23, 42, 0.9)) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 26px !important;
        padding: 40px 25px !important;
        text-align: center !important;
        margin: 30px auto !important;
        max-width: 800px !important;
        box-shadow: 
            0 20px 50px rgba(56, 189, 248, 0.35),
            inset 0 0 30px rgba(56, 189, 248, 0.25) !important;
        transform: perspective(900px) rotateX(8deg);
        animation: floatLogo5S 3.5s ease-in-out infinite alternate !important;
    }

    @keyframes floatLogo5S {
        0% { transform: perspective(900px) rotateX(8deg) translateY(0px) scale(0.99); }
        100% { transform: perspective(900px) rotateX(8deg) translateY(-12px) scale(1.02); }
    }

    .logo-5s-3d-text {
        font-family: 'Playfair Display', serif !important;
        font-size: 3.8rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #38BDF8 50%, #0E529E 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: 0 10px 25px rgba(56, 189, 248, 0.5) !important;
        letter-spacing: 4px;
    }

</style>
""", unsafe_allow_html=True)

# Affichage permanent du titre principal
# Top header removed per user request

if st.session_state.get("test_mode", False):
    st.markdown("<div class='test-badge'>🧪 SESSION DE TEST ACTIVE – ENREGISTREMENTS ISOLÉS</div>", unsafe_allow_html=True)


# ========================================== ÉCRAN DE CONNEXION MULTI-ÉTAPES (ETAPES 0 à 3)
# ========================================== ÉCRAN 0 : ACCUEIL ET LOGO 5S FLOTTANT AVEC EXPLOSION
if not st.session_state.get("user_authenticated", False):
    
    # ÉCRAN DE L'EXPLOSION LORS DU CLIC SUR ENTRER
    if st.session_state.get("show_explosion", False):
        import time
        import random
        
        # Génération dynamique de 45 particules explosives en 3D
        particles_html = "<div class='explosion-overlay'><div class='explosion-core-flash'></div>"
        symbols = ["✨", "💥", "🌟", "⚡", "⭐", "📦", "👑", "🎯", "🔥", "🚀", "💫", "🏆"]
        
        for i in range(48):
            sym = random.choice(symbols)
            angle = (i / 48.0) * 360.0
            dist = random.randint(280, 750)
            import math
            rad = math.radians(angle)
            tx = int(math.cos(rad) * dist)
            ty = int(math.sin(rad) * dist)
            rot = random.randint(-540, 540)
            particles_html += f"<div class='particle-3d' style='--tx: {tx}px; --ty: {ty}px; --rot: {rot}deg;'>{sym}</div>"
            
        particles_html += "</div>"
        st.markdown(particles_html, unsafe_allow_html=True)
        
        # Pause de 1.1s pour voir l'explosion éclater à l'écran
        time.sleep(1.1)
        st.session_state.show_explosion = False
        st.session_state.auth_step = 1
        st.rerun()

    auth_step = st.session_state.get("auth_step", 0)
    
    # ÉTAPE 0 : ACCUEIL AVEC LOGO 5S FLOTTANT 3D
    if auth_step == 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='user-id-badge-3d'>✨ BIENVENUE CHEZ MASSILLY ✨</div>", unsafe_allow_html=True)
        
        # Le Grand Logo 5S Flottant 3D
        st.markdown("""
        <div class='logo-5s-3d-floating'>
            <div class='logo-5s-3d-text'>✨ 5S LOGISTIQUE ✨</div>
            <div style='font-size: 1.45rem; font-weight: 800; color: #38BDF8; letter-spacing: 5px; text-transform: uppercase; margin-top: 15px;'>
                SEIRI • SEITON • SEISO • SEIKETSU • SHITSUKE
            </div>
            <div style='font-size: 1.1rem; color: #94A3B8; margin-top: 12px; font-weight: 600; letter-spacing: 1.5px;'>
                MÉTHODE D'EXCELLENCE OPÉRATIONNELLE MASSILLY
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
        if st.button("🚀 ENTRER DANS L'APPLICATION 5S", use_container_width=True):
            st.session_state.show_explosion = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
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
        
        # ÉTAPE 2 : CHOIX DU NOM (BADGES DE COULEURS DEFILANTS)
    elif auth_step == 2:
        st.markdown("<div class='user-id-badge-3d'>👤 SÉLECTION DE L'UTILISATEUR</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #CBD5E1; font-weight: 700;'>Cliquez sur votre prénom pour continuer :</p>", unsafe_allow_html=True)
        
        PERSONNES_BADGES = [
            {"prenom": "Damien", "nom": "Labbé", "full": "Damien Labbé", "icon": "⚡", "sub": "Alternant Méthodes 5S", "cls": "p-color-0"},
            {"prenom": "Audrey", "nom": "Sordet", "full": "Audrey Sordet", "icon": "🎯", "sub": "Sponsor Zone 1", "cls": "p-color-1"},
            {"prenom": "Anthony", "nom": "Duplessis", "full": "Anthony Duplessis", "icon": "📦", "sub": "Sponsor Zone 2", "cls": "p-color-2"},
            {"prenom": "Jonathan", "nom": "Mele", "full": "Jonathan Mele", "icon": "🚚", "sub": "Sponsor Zone 3", "cls": "p-color-3"},
            {"prenom": "Thomas", "nom": "Collin", "full": "Thomas Collin", "icon": "📋", "sub": "Sponsor Zone 4", "cls": "p-color-4"},
            {"prenom": "Gaspard", "nom": "Sommereux", "full": "Gaspard Sommereux", "icon": "🥫", "sub": "Sponsor Zone 5", "cls": "p-color-5"},
            {"prenom": "Mariia", "nom": "Leliukh", "full": "Mariia Leliukh", "icon": "🏭", "sub": "Sponsor Zone 6", "cls": "p-color-6"},
            {"prenom": "Céline", "nom": "Hereng", "full": "Céline Hereng", "icon": "📑", "sub": "Sponsor Zone 7", "cls": "p-color-7"},
            {"prenom": "Dimitri", "nom": "Dupasquier", "full": "Dimitri Dupasquier", "icon": "⚙️", "sub": "Sponsor Zone 8", "cls": "p-color-8"},
            {"prenom": "Frédéric", "nom": "Bouvy", "full": "Frédéric Bouvy", "icon": "🔧", "sub": "Sponsor Zone 9", "cls": "p-color-9"},
            {"prenom": "Nathalie", "nom": "Berthelin", "full": "Nathalie Berthelin", "icon": "🛡️", "sub": "Sponsor Zone 10", "cls": "p-color-10"}
        ]
        
        # Grille 2 colonnes tactile de badges colorés
        col_p1, col_p2 = st.columns(2)
        for idx, p in enumerate(PERSONNES_BADGES):
            target_col = col_p1 if idx % 2 == 0 else col_p2
            with target_col:
                st.markdown(f"<div class='person-badge-wrap {p['cls']}'>", unsafe_allow_html=True)
                lbl = f"{p['icon']}  {p['prenom']}  •  {p['sub']}"
                if st.button(lbl, key=f"p_badge_{idx}", use_container_width=True):
                    st.session_state.user_name = p['full']
                    st.session_state.auth_step = 3
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
        if st.button("⬅️ Retour au choix du rôle", use_container_width=True):
            st.session_state.auth_step = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    # ÉTAPE 3 : SÉLECTION DE LA ZONE (BADGES DE COULEURS DEFILANTS)
    elif auth_step == 3:
        st.markdown("<div class='user-id-badge-3d'>📍 SÉLECTION DE LA ZONE LOGISTIQUE</div>", unsafe_allow_html=True)
        st.info(f"Profil actif : **{st.session_state.get('user_name', '')}** ({st.session_state.get('user_role', '')})")
        st.markdown("<p style='text-align: center; font-size: 18px; color: #CBD5E1; font-weight: 700;'>Cliquez sur une zone pour LANCER LE DIAGNOSTIC :</p>", unsafe_allow_html=True)
        
        ZONES_BADGES = [
            {"key": "Zone 1", "label": "Zone 1 - Filmeuse & quais prod", "sponsor": "Audrey Sordet", "icon": "🎞️", "cls": "z-color-0"},
            {"key": "Zone 2", "label": "Zone 2 - Bureaux expédition", "sponsor": "Anthony Duplessis", "icon": "🖥️", "cls": "z-color-1"},
            {"key": "Zone 3", "label": "Zone 3 - Quai chargement", "sponsor": "Jonathan Mele", "icon": "🚛", "cls": "z-color-2"},
            {"key": "Zone 4", "label": "Zone 4 - Prépa commandes", "sponsor": "Thomas Collin", "icon": "📋", "cls": "z-color-3"},
            {"key": "Zone 5", "label": "Zone 5 - Emplacements boîtes", "sponsor": "Gaspard Sommereux", "icon": "🥫", "cls": "z-color-4"},
            {"key": "Zone 6", "label": "Zone 6 - Palettier", "sponsor": "Mariia Leliukh", "icon": "🏗️", "cls": "z-color-5"},
            {"key": "Zone 7", "label": "Zone 7 - Réception MP & bureaux", "sponsor": "Céline Hereng", "icon": "📦", "cls": "z-color-6"},
            {"key": "Zone 8", "label": "Zone 8 - Stockage métal", "sponsor": "Dimitri Dupasquier", "icon": "⚙️", "cls": "z-color-7"},
            {"key": "Zone 9", "label": "Zone 9 - Local joint", "sponsor": "Frédéric Bouvy", "icon": "🧪", "cls": "z-color-8"},
            {"key": "Zone 10", "label": "Zone 10 - Produits dangereux", "sponsor": "Nathalie Berthelin", "icon": "☣️", "cls": "z-color-9"}
        ]
        
        st.session_state.test_mode = st.checkbox(
            "🧪 Activer le MODE TEST d'entraînement",
            value=st.session_state.get("test_mode", False)
        )
        
        col_z1, col_z2 = st.columns(2)
        for idx, z in enumerate(ZONES_BADGES):
            target_col = col_z1 if idx % 2 == 0 else col_z2
            with target_col:
                st.markdown(f"<div class='zone-badge-wrap {z['cls']}'>", unsafe_allow_html=True)
                lbl = f"{z['icon']}  {z['key']}  •  {z['sponsor']}\n{z['label']}"
                if st.button(lbl, key=f"z_badge_{idx}", use_container_width=True):
                    st.session_state.user_zone = z["key"]
                    st.session_state.user_authenticated = True
                    st.session_state.auth_step = 0
                    st.session_state.portal_shown = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
        if st.button("⬅️ Retour à la sélection de l'utilisateur", use_container_width=True):
            st.session_state.auth_step = 2
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
                
                st.markdown(f"""
                <div class='question-card'>
                    <div class='question-cat'>{crit['cat']}</div>
                    <div class='question-text'>{crit['txt']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c_v1, c_v2, c_v3 = st.columns(3)
                with c_v1:
                    if st.button("🟢 OUI", use_container_width=True, key=f"btn_oui_{idx}"):
                        st.session_state.answers[crit["id"]] = "OUI"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with c_v2:
                    if st.button("🔴 NON", use_container_width=True, key=f"btn_non_{idx}"):
                        st.session_state.answers[crit["id"]] = "NON"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with c_v3:
                    if st.button("🔵 N/A", use_container_width=True, key=f"btn_na_{idx}"):
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
                st.success("🎉 Questionnaire terminé ! Saisissez vos observations ci-dessous :")
                
                t_oui = sum(1 for v in st.session_state.answers.values() if v == "OUI")
                t_non = sum(1 for v in st.session_state.answers.values() if v == "NON")
                t_na = sum(1 for v in st.session_state.answers.values() if v == "N/A")
                score = t_oui
                total_ev = 15 - t_na
                pct = int((score / total_ev) * 100) if total_ev > 0 else 0
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Score Conforme", f"{score}/{total_ev}")
                m2.metric("Taux de Conformité", f"{pct}%")
                m3.metric("Non-Conformités (NON)", f"{t_non}")
                m4.metric("Non Applicables (N/A)", f"{t_na}")
                
                st.markdown("---")
                st.markdown("### 📝 Observations terrain & Actions")
                obs = st.text_area("Remarques ou écarts constatés :")
                act = st.text_area("Actions correctives immédiates :")
                
                col_fin1, col_fin2 = st.columns(2)
                with col_fin1:
                    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                    if st.button("⬅️ Modifier les réponses", use_container_width=True):
                        st.session_state.current_q_idx = 0
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with col_fin2:
                    st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
                    if st.button("💾 VALIDER & ENREGISTRER L'AUDIT 5S", use_container_width=True):
                        audit_record = {
                            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Zone": ZONES_MASSILLY[st.session_state.user_zone]["label"],
                            "Sponsor": ZONES_MASSILLY[st.session_state.user_zone]["sponsor"],
                            "Auditeur": st.session_state.user_name,
                            "Role": st.session_state.user_role,
                            "Score_Total": score,
                            "Pourcentage": pct,
                            "Observations": obs,
                            "Actions_Correctives": act
                        }
                        for c in CRITERES_OFFICIELS:
                            audit_record[c["id"]] = st.session_state.answers.get(c["id"], "N/A")
                            
                        ok, err = sauvegarder_audit_local(audit_record)
                        st.session_state.audit_started = False
                        st.session_state.current_q_idx = 0
                        st.session_state.answers = {}
                        if ok:
                            st.balloons()
                            st.success("✅ Audit enregistré avec succès dans Google Sheets !")
                        else:
                            st.warning(f"⚠️ Audit sauvegardé localement (GSheets offline : {err})")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    # ========================================== ONGLET 2 : HISTORIQUE & STATISTIQUES
    elif menu_actif == "📊 Analyse & Historique":
        st.markdown("### 📊 Historique des Audits 5S Logistique")
        
        # Section Outils Admin / Test Connexion Google Sheets
        if st.session_state.get("user_role") == "Éditeur (Méthodes / Alternant)":
            with st.expand_container() if hasattr(st, 'expand_container') else st.expander("🛠️ OUTILS ADMINISTRATEUR & CONNEXION GOOGLE SHEETS"):
                st.markdown("#### Diagnostic de liaison Google Sheets")
                if st.button("🔌 TESTER LA CONNEXION GOOGLE SHEETS", use_container_width=True):
                    ok, err = sauvegarder_audit_local({
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Zone": "TEST_CONNEXION",
                        "Sponsor": "SYSTEM",
                        "Auditeur": st.session_state.get('user_name', 'TEST_ADMIN'),
                        "Role": st.session_state.get('user_role', 'ADMIN'),
                        "Score_Total": 15,
                        "Pourcentage": 100,
                        "Observations": "Test de connexion manuel depuis le panneau Administrateur",
                        "Actions_Correctives": "Aucune"
                    })
                    if ok:
                        st.success("✅ Connexion Google Sheets fonctionnelle ! L'audit de test a été enregistré.")
                    else:
                        st.error(f"❌ Échec de connexion : {err}")
        
        df_hist = charger_audits()
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("Aucun audit enregistré pour le moment.")

    # ========================================== ONGLET 3 : RAPPEL DES STANDARDS
    elif menu_actif == "🗺️ Rappel des Standards":
        st.markdown("### 🗺️ Carte des 10 Zones & Standards Massilly")
        for z_key, z_val in ZONES_MASSILLY.items():
            st.markdown(f"**{z_val['label']}** — *Sponsor : {z_val['sponsor']}*")
