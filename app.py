# -*- coding: utf-8 -*-
"""
APPLICATION AUDIT 5S LOGISTIQUE - MASSILLY FRANCE (VERSION v65)
- Mode Terrain & Mode Administrateur
- Ergonomie Tactile Géante (Taille 28px Extra-Gras)
- Cartes Utilisateurs : Bleu Garçon (#0284C7) / Rose Fille (#DB2777)
- Spectres de Dégradés Multicolores pour les 10 Zones Logistiques
- Boutons d'Audit : OUI (Vert Émeraude #10B981), NON (Rouge Vif #EF4444), N/A (Bleu Royal #3B82F6)
- Case "Commentaire Additionnel" à chaque étape d'audit (c1_comment à c15_comment)
- Horodatage complet au millième de seconde de chaque clic utilisateur (Journal de Clics)
- Connexion native Google Sheets & Backup CSV local
"""

import streamlit as st
import pandas as pd
import numpy as np
import os, json, math, random, time
from datetime import datetime

# Streamlit-GSheets Connection sécurisée
try:
    from st_gsheets_connection import GSheetsConnection
except ImportError:
    try:
        from streamlit_gsheets import GSheetsConnection
    except ImportError:
        GSheetsConnection = None

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Audit 5S Logistique - Massilly",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# HORODATAGE & JOURNALISATION DES CLICS UTILISATEUR
# ---------------------------------------------------------
if st.session_state.get("test_mode", False):
    SHARED_DATA_FILE = "test_suivi_audits_5s.csv"
    SHARED_LOG_FILE = "test_journal_activite_5s.json"
    SHARED_CLICS_FILE = "test_journal_clics_5s.csv"
else:
    SHARED_DATA_FILE = "suivi_audits_5s.csv"
    SHARED_LOG_FILE = "journal_activite_5s.json"
    SHARED_CLICS_FILE = "journal_clics_5s.csv"

def log_user_click(action, details=""):
    """Enregistre chaque clic utilisateur avec un horodatage complet à la milliseconde."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    user = st.session_state.get("user_name", "ANONYME")
    role = st.session_state.get("user_role", "INCONNU")
    zone = st.session_state.get("user_zone", "NON_DEFINIE")
    
    click_entry = {
        "Horodatage": now_str,
        "Utilisateur": user,
        "Role": role,
        "Zone": zone,
        "Action": action,
        "Details": str(details)
    }
    
    # Session state buffer
    if "session_clics_log" not in st.session_state:
        st.session_state.session_clics_log = []
    st.session_state.session_clics_log.append(click_entry)
    
    # Append to CSV local
    try:
        df_click = pd.DataFrame([click_entry])
        if not os.path.exists(SHARED_CLICS_FILE):
            df_click.to_csv(SHARED_CLICS_FILE, index=False, encoding='utf-8')
        else:
            df_click.to_csv(SHARED_CLICS_FILE, mode='a', header=False, index=False, encoding='utf-8')
    except Exception as e:
        pass

# ---------------------------------------------------------
# DONNÉES OFFICIELLES MASSILLY
# ---------------------------------------------------------
ZONES_MASSILLY = {
    "Zone 1": {"label": "Zone 1 - Filmeuse & quais prod", "sponsor": "Audrey Sordet", "icon": "🎞️", "cls": "z-color-0"},
    "Zone 2": {"label": "Zone 2 - Bureaux expédition", "sponsor": "Anthony Duplessis", "icon": "🖥️", "cls": "z-color-1"},
    "Zone 3": {"label": "Zone 3 - Quai chargement", "sponsor": "Jonathan Mele", "icon": "🚛", "cls": "z-color-2"},
    "Zone 4": {"label": "Zone 4 - Prépa commandes", "sponsor": "Thomas Collin", "icon": "📋", "cls": "z-color-3"},
    "Zone 5": {"label": "Zone 5 - Emplacements boîtes", "sponsor": "Gaspard Sommereux", "icon": "🥫", "cls": "z-color-4"},
    "Zone 6": {"label": "Zone 6 - Palettier", "sponsor": "Mariia Leliukh", "icon": "🏗️", "cls": "z-color-5"},
    "Zone 7": {"label": "Zone 7 - Réception MP & bureaux", "sponsor": "Céline Hereng", "icon": "📦", "cls": "z-color-6"},
    "Zone 8": {"label": "Zone 8 - Stockage métal", "sponsor": "Dimitri Dupasquier", "icon": "⚙️", "cls": "z-color-7"},
    "Zone 9": {"label": "Zone 9 - Local joint", "sponsor": "Frédéric Bouvy", "icon": "🧪", "cls": "z-color-8"},
    "Zone 10": {"label": "Zone 10 - Produits dangereux", "sponsor": "Nathalie Berthelin", "icon": "☣️", "cls": "z-color-9"}
}

PERSONNES_MASSILLY = [
    {"prenom": "Damien", "full": "Damien Labbé", "icon": "⚡", "gender": "boy"},
    {"prenom": "Audrey", "full": "Audrey Sordet", "icon": "🎯", "gender": "girl"},
    {"prenom": "Anthony", "full": "Anthony Duplessis", "icon": "📦", "gender": "boy"},
    {"prenom": "Jonathan", "full": "Jonathan Mele", "icon": "🚚", "gender": "boy"},
    {"prenom": "Thomas", "full": "Thomas Collin", "icon": "📋", "gender": "boy"},
    {"prenom": "Gaspard", "full": "Gaspard Sommereux", "icon": "🥫", "gender": "boy"},
    {"prenom": "Mariia", "full": "Mariia Leliukh", "icon": "🏭", "gender": "girl"},
    {"prenom": "Céline", "full": "Céline Hereng", "icon": "📑", "gender": "girl"},
    {"prenom": "Dimitri", "full": "Dupasquier Dimitri", "icon": "⚙️", "gender": "boy"},
    {"prenom": "Frédéric", "full": "Frédéric Bouvy", "icon": "🔧", "gender": "boy"},
    {"prenom": "Nathalie", "full": "Nathalie Berthelin", "icon": "🛡️", "gender": "girl"}
]

CRITERES_OFFICIELS = [
    {"id": "c1", "cat": "1S - SEIRI (TRIER)", "txt": "Absence de palettes cassées, de films plastiques usagés et d'emballages inutiles dans la zone."},
    {"id": "c2", "cat": "1S - SEIRI (TRIER)", "txt": "Les produits non conformes ou bloqués sont clairement isolés et étiquetés avec la fiche rouge."},
    {"id": "c3", "cat": "1S - SEIRI (TRIER)", "txt": "Seuls les outils et consommables nécessaires au poste sont présents."},
    {"id": "c4", "cat": "2S - SEITON (RANGER)", "txt": "Le marquage au sol des allées de circulation et zones de stockage est propre et visible."},
    {"id": "c5", "cat": "2S - SEITON (RANGER)", "txt": "Chaque équipement, chariot et outil a un emplacement défini et identifié (panneaux d'ombres)."},
    {"id": "c6", "cat": "2S - SEITON (RANGER)", "txt": "Les palettes et colis sont rangés de manière alignée sans débordement sur les allées."},
    {"id": "c7", "cat": "3S - SEISO (NETTOYER)", "txt": "Les sols, racks et postes de travail sont propres et exempts de poussière ou d'huile."},
    {"id": "c8", "cat": "3S - SEISO (NETTOYER)", "txt": "Les engins de manutention et transpalettes sont nettoyés et inspectés régulièrement."},
    {"id": "c9", "cat": "3S - SEISO (NETTOYER)", "txt": "Les poubelles et bacs de recyclage sont vider régulièrement et correctement triés."},
    {"id": "c10", "cat": "4S - SEIKETSU (STANDARDISER)", "txt": "Les standards visuels 5S et consignes de sécurité sont affichés et à jour."},
    {"id": "c11", "cat": "4S - SEIKETSU (STANDARDISER)", "txt": "Les règles d'étiquetage et d'identification des emplacements sont strictly respectées."},
    {"id": "c12", "cat": "4S - SEIKETSU (STANDARDISER)", "txt": "Les équipements de protection individuelle (EPI) sont disponibles et rangés à leur place."},
    {"id": "c13", "cat": "5S - SHITSUKE (SUIVRE)", "txt": "L'audit 5S est réalisé de façon régulière selon le planning établi."},
    {"id": "c14", "cat": "5S - SHITSUKE (SUIVRE)", "txt": "Les remarques et actions des audits précédents ont fait l'objet d'un suivi ou d'un solde."},
    {"id": "c15", "cat": "5S - SHITSUKE (SUIVRE)", "txt": "L'équipe de la zone montre de l'implication dans le maintien au quotidien des standards 5S."}
]

# Initialisation du fichier CSV de données
if not os.path.exists(SHARED_DATA_FILE):
    cols_init = [
        "Date", "Zone", "Sponsor", "Auditeur", "Role",
        "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10", "c11", "c12", "c13", "c14", "c15",
        "c1_comment", "c2_comment", "c3_comment", "c4_comment", "c5_comment",
        "c6_comment", "c7_comment", "c8_comment", "c9_comment", "c10_comment",
        "c11_comment", "c12_comment", "c13_comment", "c14_comment", "c15_comment",
        "Score_Total", "Pourcentage", "Observations", "Actions_Correctives", "Journal_Horodatage_Clics"
    ]
    pd.DataFrame(columns=cols_init).to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

def sauvegarder_audit_local(data_dict):
    """Enregistre l'audit complet localement et via Google Sheets si disponible."""
    try:
        df_exist = pd.read_csv(SHARED_DATA_FILE)
        df_new = pd.concat([df_exist, pd.DataFrame([data_dict])], ignore_index=True)
        df_new.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')
        
        # Google Sheets backup si configuré
        if GSheetsConnection is not None:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                conn.update(worksheet="Audits_5S", data=df_new)
            except Exception:
                pass
        return True, ""
    except Exception as e:
        return False, str(e)

def charger_audits():
    try:
        return pd.read_csv(SHARED_DATA_FILE)
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# STYLES CSS SUR-MESURE : MARQUEURS HTML & ERGONOMIE GÉANTE
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Styles généraux */
    .stApp {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    
    /* Titre 5S Flottant 3D */
    .logo-5s-3d-floating {
        background: linear-gradient(135deg, rgba(14, 82, 158, 0.4), rgba(15, 23, 42, 0.95)) !important;
        border: 3px solid #38BDF8 !important;
        border-radius: 26px !important;
        padding: 35px 20px !important;
        text-align: center !important;
        margin: 20px auto !important;
        max-width: 850px !important;
        box-shadow: 0 20px 50px rgba(56, 189, 248, 0.35) !important;
    }
    .logo-5s-3d-text {
        font-family: 'Playfair Display', serif !important;
        font-size: clamp(1.6rem, 6.5vw, 3.2rem) !important;
        font-weight: 900 !important;
        text-align: center !important;
        color: #38BDF8 !important;
        letter-spacing: 2px !important;
    }
    
    /* BADGES CARTES GARÇONS (BLEU OCÉAN GÉANT) */
    div:has(.boy-marker) + div button,
    .boy-marker + div button,
    div.boy-marker + div button {
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        border: 3px solid #38BDF8 !important;
        border-bottom: 8px solid #075985 !important;
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        height: 90px !important;
        border-radius: 20px !important;
        box-shadow: 0 12px 30px rgba(2, 132, 199, 0.5) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5) !important;
    }
    
    /* BADGES CARTES FILLES (ROSE MAGENTA GÉANT) */
    div:has(.girl-marker) + div button,
    .girl-marker + div button,
    div.girl-marker + div button {
        background: linear-gradient(135deg, #E11D48 0%, #BE123C 100%) !important;
        border: 3px solid #FB7185 !important;
        border-bottom: 8px solid #881337 !important;
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        height: 90px !important;
        border-radius: 20px !important;
        box-shadow: 0 12px 30px rgba(225, 29, 72, 0.5) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5) !important;
    }

    /* BADGES ZONES 1 à 10 EN DÉGRADÉ MULTICOLORE */
    div:has(.z-marker-0) + div button { background: linear-gradient(135deg, #06B6D4, #0891B2) !important; border: 3px solid #67E8F9 !important; border-bottom: 8px solid #155E75 !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-1) + div button { background: linear-gradient(135deg, #0D9488, #0F766E) !important; border: 3px solid #5EEAD4 !important; border-bottom: 8px solid #115E59 !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-2) + div button { background: linear-gradient(135deg, #10B981, #059669) !important; border: 3px solid #6EE7B7 !important; border-bottom: 8px solid #047857 !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-3) + div button { background: linear-gradient(135deg, #84CC16, #65A30D) !important; border: 3px solid #BEF264 !important; border-bottom: 8px solid #4D7C0F !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-4) + div button { background: linear-gradient(135deg, #EAB308, #CA8A04) !important; border: 3px solid #FDE047 !important; border-bottom: 8px solid #854D0E !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-5) + div button { background: linear-gradient(135deg, #F97316, #EA580C) !important; border: 3px solid #FDBA74 !important; border-bottom: 8px solid #9A3412 !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-6) + div button { background: linear-gradient(135deg, #EF4444, #DC2626) !important; border: 3px solid #FCA5A5 !important; border-bottom: 8px solid #991B1B !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-7) + div button { background: linear-gradient(135deg, #EC4899, #DB2777) !important; border: 3px solid #FBCFE8 !important; border-bottom: 8px solid #9D174D !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-8) + div button { background: linear-gradient(135deg, #A855F7, #9333EA) !important; border: 3px solid #E9D5FF !important; border-bottom: 8px solid #6B21A8 !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }
    div:has(.z-marker-9) + div button { background: linear-gradient(135deg, #6366F1, #4F46E5) !important; border: 3px solid #C7D2FE !important; border-bottom: 8px solid #3730A3 !important; font-size: 28px !important; font-weight: 900 !important; height: 90px !important; border-radius: 20px !important; color: #FFF !important; }

    /* BOUTONS DE VOTE AUDIT : OUI (VERT), NON (ROUGE), N/A (BLEU) */
    div:has(.vote-oui-marker) + div button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        border: 3px solid #6EE7B7 !important;
        border-bottom: 8px solid #047857 !important;
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        height: 85px !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4) !important;
    }
    div:has(.vote-non-marker) + div button {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
        border: 3px solid #FCA5A5 !important;
        border-bottom: 8px solid #991B1B !important;
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        height: 85px !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(239, 68, 68, 0.4) !important;
    }
    div:has(.vote-na-marker) + div button {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%) !important;
        border: 3px solid #93C5FD !important;
        border-bottom: 8px solid #1E40AF !important;
        color: #FFFFFF !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        height: 85px !important;
        border-radius: 18px !important;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Carte de question */
    .question-card {
        background: #1E293B !important;
        border: 2px solid #38BDF8 !important;
        border-radius: 20px !important;
        padding: 25px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
    }
    .question-cat {
        font-size: 16px !important;
        font-weight: 800 !important;
        color: #F59E0B !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
    }
    .question-text {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
        margin-top: 10px !important;
        line-height: 1.4 !important;
    }

    /* Animation explosion */
    .explosion-overlay {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(15, 23, 42, 0.95);
        z-index: 999999;
        display: flex; justify-content: center; align-items: center;
        overflow: hidden;
    }
    .particle-3d {
        position: absolute; font-size: 3rem;
        animation: burstOut 1.1s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
    }
    @keyframes burstOut {
        0% { transform: translate(0, 0) scale(0.2) rotate(0deg); opacity: 1; }
        100% { transform: translate(var(--tx), var(--ty)) scale(2.2) rotate(var(--rot)); opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INITIALISATION DU SESSION STATE
# ---------------------------------------------------------
st.session_state.setdefault("user_authenticated", False)
st.session_state.setdefault("user_role", "")
st.session_state.setdefault("user_name", "")
st.session_state.setdefault("user_zone", "")
st.session_state.setdefault("audit_started", False)
st.session_state.setdefault("current_q_idx", 0)
st.session_state.setdefault("answers", {})
st.session_state.setdefault("step_comments", {})
st.session_state.setdefault("test_mode", False)
st.session_state.setdefault("auth_step", 0)

# =========================================================
# FLUX DE NAVIGATION MULTI-ÉTAPES (AUTHENTIFICATION & SETUP)
# =========================================================
if not st.session_state.get("user_authenticated", False):
    
    # 💥 EXPLOSION 3D AU CLIC SUR ENTRER
    if st.session_state.get("show_explosion", False):
        particles_html = "<div class='explosion-overlay'>"
        symbols = ["✨", "💥", "🌟", "⚡", "⭐", "📦", "👑", "🎯", "🔥", "🚀", "💫", "🏆"]
        for i in range(48):
            sym = random.choice(symbols)
            angle = (i / 48.0) * 360.0
            dist = random.randint(280, 750)
            rad = math.radians(angle)
            tx = int(math.cos(rad) * dist)
            ty = int(math.sin(rad) * dist)
            rot = random.randint(-540, 540)
            particles_html += f"<div class='particle-3d' style='--tx: {tx}px; --ty: {ty}px; --rot: {rot}deg;'>{sym}</div>"
        particles_html += "</div>"
        st.markdown(particles_html, unsafe_allow_html=True)
        
        time.sleep(1.1)
        st.session_state.show_explosion = False
        st.session_state.auth_step = 1
        st.rerun()

    auth_step = st.session_state.get("auth_step", 0)
    
    # -----------------------------------------------------
    # ÉTAPE 0 : ACCUEIL & LOGO 5S 3D
    # -----------------------------------------------------
    if auth_step == 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #38BDF8; letter-spacing: 3px;'>✨ BIENVENUE CHEZ MASSILLY ✨</h2>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class='logo-5s-3d-floating'>
            <div class='logo-5s-3d-text'>✨ 5S LOGISTIQUE ✨</div>
            <div style='font-size: 1.4rem; font-weight: 800; color: #38BDF8; letter-spacing: 4px; text-transform: uppercase; margin-top: 15px;'>
                SEIRI • SEITON • SEISO • SEIKETSU • SHITSUKE
            </div>
            <div style='font-size: 1.1rem; color: #94A3B8; margin-top: 12px; font-weight: 600;'>
                MÉTHODE D'EXCELLENCE OPÉRATIONNELLE MASSILLY
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 ENTRER DANS L'APPLICATION 5S", use_container_width=True):
            log_user_click("Clic Entrer Application", "Accueil Étape 0")
            st.session_state.show_explosion = True
            st.rerun()

    # -----------------------------------------------------
    # ÉTAPE 1 : SELECTION DU RÔLE
    # -----------------------------------------------------
    elif auth_step == 1:
        st.markdown("<h2 style='text-align: center;'>📋 SÉLECTIONNEZ VOTRE RÔLE</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; font-weight: bold; color: #94A3B8;'>Choisissez votre profil d'accès :</p>", unsafe_allow_html=True)
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            if st.button("🎯 Sponsor de zone", use_container_width=True):
                log_user_click("Choix Rôle", "Sponsor de zone")
                st.session_state.user_role = "Sponsor de zone"
                st.session_state.auth_step = 2
                st.rerun()
        with col_r2:
            if st.button("🔍 Référent 5S", use_container_width=True):
                log_user_click("Choix Rôle", "Référent 5S")
                st.session_state.user_role = "Référent 5S"
                st.session_state.auth_step = 2
                st.rerun()
        with col_r3:
            if st.button("⚙️ Administrateur", use_container_width=True):
                log_user_click("Choix Rôle", "Administrateur")
                st.session_state.user_role = "Éditeur (Méthodes / Alternant)"
                st.session_state.auth_step = 2
                st.rerun()

    # -----------------------------------------------------
    # ÉTAPE 2 : SELECTION DE L'UTILISATEUR (BLEU / ROSE)
    # -----------------------------------------------------
    elif auth_step == 2:
        st.markdown("<h2 style='text-align: center;'>👤 SÉLECTION DE L'UTILISATEUR</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; color: #CBD5E1; font-weight: 700;'>Cliquez sur votre prénom (28px Extra-Gras) :</p>", unsafe_allow_html=True)
        
        col_p1, col_p2 = st.columns(2)
        for idx, p in enumerate(PERSONNES_MASSILLY):
            target_col = col_p1 if idx % 2 == 0 else col_p2
            marker_cls = "boy-marker" if p["gender"] == "boy" else "girl-marker"
            with target_col:
                st.markdown(f"<div class='{marker_cls}'></div>", unsafe_allow_html=True)
                lbl = f"{p['icon']}  {p['prenom']}"
                if st.button(lbl, key=f"p_badge_{idx}", use_container_width=True):
                    log_user_click("Sélection Utilisateur", p["full"])
                    st.session_state.user_name = p['full']
                    st.session_state.auth_step = 3
                    st.rerun()

    # -----------------------------------------------------
    # ÉTAPE 3 : SELECTION DE LA ZONE LOGISTIQUE (DÉGRADÉ MULTICOLORE)
    # -----------------------------------------------------
    elif auth_step == 3:
        st.markdown("<h2 style='text-align: center;'>📍 SÉLECTION DE LA ZONE LOGISTIQUE</h2>", unsafe_allow_html=True)
        st.info(f"Profil actif : **{st.session_state.get('user_name', '')}** ({st.session_state.get('user_role', '')})")
        st.markdown("<p style='text-align: center; font-size: 20px; color: #CBD5E1; font-weight: 700;'>Cliquez sur votre zone (Nom seul en dégradé 28px) :</p>", unsafe_allow_html=True)
        
        col_z1, col_z2 = st.columns(2)
        for idx, (z_key, z_val) in enumerate(ZONES_MASSILLY.items()):
            target_col = col_z1 if idx % 2 == 0 else col_z2
            marker_cls = f"z-marker-{idx}"
            with target_col:
                st.markdown(f"<div class='{marker_cls}'></div>", unsafe_allow_html=True)
                lbl = f"{z_val['icon']}  {z_key}"
                if st.button(lbl, key=f"z_badge_{idx}", use_container_width=True):
                    log_user_click("Sélection Zone", z_key)
                    st.session_state.user_zone = z_key
                    st.session_state.auth_step = 4
                    st.rerun()

    # -----------------------------------------------------
    # ÉTAPE 4 : CONFIRMATION RECAPITULATIVE AVANT AUDIT
    # -----------------------------------------------------
    elif auth_step == 4:
        st.markdown("<h2 style='text-align: center; color: #38BDF8;'>🚀 PRÊT POUR LE DIAGNOSTIC 5S</h2>", unsafe_allow_html=True)
        
        z_info = ZONES_MASSILLY.get(st.session_state.user_zone, {})
        st.markdown(f"""
        <div style='background: #1E293B; border: 3px solid #38BDF8; border-radius: 24px; padding: 30px; text-align: center; margin: 20px auto; max-width: 700px;'>
            <div style='font-size: 1.3rem; color: #94A3B8; font-weight: 700;'>RÉCAPITULATIF DE LA SESSION :</div>
            <div style='font-size: 2.2rem; font-weight: 900; color: #F59E0B; margin-top: 10px;'>{z_info.get("label", "")}</div>
            <div style='font-size: 1.4rem; color: #38BDF8; font-weight: 800; margin-top: 8px;'>Sponsor Responsable : {z_info.get("sponsor", "")}</div>
            <hr style='border-color: #334155; margin: 20px 0;'>
            <div style='font-size: 1.3rem; color: #F8FAFC;'>Auditeur : <b>{st.session_state.user_name}</b> ({st.session_state.user_role})</div>
        </div>
        """, unsafe_allow_html=True)
        
        c_c1, c_c2 = st.columns(2)
        with c_c1:
            if st.button("🚀 COMMENCER LE DIAGNOSTIC TERRAIN", use_container_width=True):
                log_user_click("Lancement Diagnostic", f"Zone {st.session_state.user_zone}")
                st.session_state.user_authenticated = True
                st.session_state.audit_started = True
                st.session_state.current_q_idx = 0
                st.session_state.answers = {}
                st.session_state.step_comments = {}
                st.rerun()
        with c_c2:
            if st.button("⬅️ RETOUR AU MENU / CHANGER DE ZONE", use_container_width=True):
                log_user_click("Retour Menu", "Depuis confirmation Étape 4")
                st.session_state.auth_step = 3
                st.rerun()

# =========================================================
# APPLICATION PRINCIPALE (UTILISATEUR CONNECTÉ SUR LE TERRAIN)
# =========================================================
else:
    # Mode Administrateur : vue complète avec onglets et test GSheets
    if st.session_state.get("user_role") == "Éditeur (Méthodes / Alternant)":
        col_u1, col_u2 = st.columns([4, 1])
        with col_u1:
            st.markdown(f"👤 **{st.session_state.user_name}** (Admin) | Zone active : **{ZONES_MASSILLY[st.session_state.user_zone]['label']}**")
        with col_u2:
            if st.button("🔄 Changer d'utilisateur", use_container_width=True):
                log_user_click("Changer utilisateur", "Admin")
                st.session_state.user_authenticated = False
                st.session_state.auth_step = 0
                st.rerun()
                
        onglets = ["📋 Audit Terrain", "📊 Analyse & Journal de Clics", "🗺️ Standards & Test Connexion"]
        menu_admin = st.radio("Menu Admin :", onglets, horizontal=True)
        st.markdown("---")
        
        if menu_admin == "📊 Analyse & Journal de Clics":
            st.markdown("### 📊 Historique des Audits Enregistrés")
            df_h = charger_audits()
            if not df_h.empty:
                st.dataframe(df_h, use_container_width=True)
            else:
                st.info("Aucun audit enregistré pour le moment.")
                
            st.markdown("### ⏱️ Journal Complet des Clics Horodatés (Millisecondes)")
            if os.path.exists(SHARED_CLICS_FILE):
                df_clics = pd.read_csv(SHARED_CLICS_FILE)
                st.dataframe(df_clics, use_container_width=True)
            else:
                st.info("Aucun clic journalisé pour l'instant.")
                
        elif menu_admin == "🗺️ Standards & Test Connexion":
            st.markdown("### 🔌 Test de Connexion Google Sheets")
            if st.button("🔌 TESTER LA CONNEXION GOOGLE SHEETS EN DIRECT", use_container_width=True):
                log_user_click("Test GSheets", "Admin")
                ok, err = sauvegarder_audit_local({
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Zone": "TEST_CONNEXION",
                    "Sponsor": "SYSTEM",
                    "Auditeur": st.session_state.user_name,
                    "Role": "ADMIN_TEST",
                    "Score_Total": 15,
                    "Pourcentage": 100,
                    "Observations": "Test connexion automatique Admin",
                    "Actions_Correctives": "Aucune",
                    "Journal_Horodatage_Clics": json.dumps(st.session_state.get("session_clics_log", []))
                })
                if ok:
                    st.success("✅ Connexion Google Sheets & CSV locale 100 % opérationnelle !")
                else:
                    st.error(f"❌ Échec de connexion : {err}")
    
    # -----------------------------------------------------
    # PARCOURS AUDIT TERRAIN (POUR SPONSORS ET RÉFÉRENTS)
    # -----------------------------------------------------
    idx = st.session_state.current_q_idx
    total_q = len(CRITERES_OFFICIELS)
    
    if idx < total_q:
        crit = CRITERES_OFFICIELS[idx]
        pct_prog = int(((idx + 1) / total_q) * 100)
        
        st.progress(pct_prog / 100.0)
        st.markdown(f"<p style='text-align: right; font-size: 18px; color: #38BDF8; font-weight: bold;'>Étape {idx + 1} sur {total_q} ({pct_prog}%)</p>", unsafe_allow_html=True)
        
        # Carte de la question
        st.markdown(f"""
        <div class='question-card'>
            <div class='question-cat'>{crit['cat']}</div>
            <div class='question-text'>{crit['txt']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Boutons de vote OUI (VERT), NON (ROUGE), N/A (BLEU)
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            st.markdown("<div class='vote-oui-marker'></div>", unsafe_allow_html=True)
            if st.button("🟢 OUI", key=f"btn_oui_{idx}", use_container_width=True):
                log_user_click("Vote OUI", f"Question {crit['id']}")
                st.session_state.answers[crit["id"]] = "OUI"
                st.session_state.current_q_idx += 1
                st.rerun()
        with col_v2:
            st.markdown("<div class='vote-non-marker'></div>", unsafe_allow_html=True)
            if st.button("🔴 NON", key=f"btn_non_{idx}", use_container_width=True):
                log_user_click("Vote NON", f"Question {crit['id']}")
                st.session_state.answers[crit["id"]] = "NON"
                st.session_state.current_q_idx += 1
                st.rerun()
        with col_v3:
            st.markdown("<div class='vote-na-marker'></div>", unsafe_allow_html=True)
            if st.button("🔵 N/A", key=f"btn_na_{idx}", use_container_width=True):
                log_user_click("Vote N/A", f"Question {crit['id']}")
                st.session_state.answers[crit["id"]] = "N/A"
                st.session_state.current_q_idx += 1
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # CASE COMMENTAIRE ADDITIONNEL ATTRIBUÉ À L'ÉTAPE ACCUELLE
        comm_curr = st.text_input(
            f"💬 Commentaire / Observation spécifique à l'Étape {idx + 1} ({crit['id']}) :",
            value=st.session_state.step_comments.get(crit["id"], ""),
            key=f"comm_input_{idx}"
        )
        st.session_state.step_comments[crit["id"]] = comm_curr
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Étape précédente", use_container_width=True):
            log_user_click("Étape précédente", f"Depuis question {crit['id']}")
            if st.session_state.current_q_idx > 0:
                st.session_state.current_q_idx -= 1
                st.rerun()

    # -----------------------------------------------------
    # SYNTHÈSE DE FIN D'AUDIT & ENREGISTRMENT COMPLET
    # -----------------------------------------------------
    else:
        st.markdown("<h2 style='text-align: center; color: #38BDF8;'>📝 SYNTHÈSE DU DIAGNOSTIC 5S</h2>", unsafe_allow_html=True)
        
        score = 0
        max_score = 0
        for c in CRITERES_OFFICIELS:
            rep = st.session_state.answers.get(c["id"], "N/A")
            if rep == "OUI":
                score += 1
                max_score += 1
            elif rep == "NON":
                max_score += 1
                
        pct = int((score / max_score * 100)) if max_score > 0 else 100
        
        st.metric("Score Total 5S", f"{score} / {max_score}", f"{pct}%")
        
        st.markdown("### 📝 Observations Globales & Remarques")
        obs_gen = st.text_area("Observations complémentaires globales :", key="obs_gen_txt")
        act_gen = st.text_area("Actions correctives immédiates préconisées :", key="act_gen_txt")
        
        st.markdown("### 📋 Récapitulatif détaillé par Étape :")
        full_step_observations = []
        for idx_c, c in enumerate(CRITERES_OFFICIELS):
            rep = st.session_state.answers.get(c["id"], "N/A")
            cm = st.session_state.step_comments.get(c["id"], "").strip()
            bullet = "🟢" if rep == "OUI" else ("🔴" if rep == "NON" else "🔵")
            
            dis_txt = f"{bullet} **Étape {idx_c + 1} ({c['cat']})** : {c['txt']} → **{rep}**"
            if cm:
                dis_txt += f" | Commentaire: {cm}"
                full_step_observations.append(f"Étape {idx_c + 1} ({c['id']}): {cm}")
            st.markdown(dis_txt)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 ENREGISTRER L'AUDIT COMPLET EN EXCEL & GSHEETS", use_container_width=True):
            log_user_click("Enregistrement Audit Final", f"Score {score}/{max_score} ({pct}%)")
            
            # Combinaison des commentaires d'étapes et des remarques globales
            all_obs = " | ".join(full_step_observations)
            if obs_gen.strip():
                all_obs = f"{all_obs} || Remarques Globales: {obs_gen.strip()}"
                
            data_audit = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Zone": ZONES_MASSILLY[st.session_state.user_zone]["label"],
                "Sponsor": ZONES_MASSILLY[st.session_state.user_zone]["sponsor"],
                "Auditeur": st.session_state.user_name,
                "Role": st.session_state.user_role,
            }
            
            # Reponses et commentaires par étape
            for c in CRITERES_OFFICIELS:
                data_audit[c["id"]] = st.session_state.answers.get(c["id"], "N/A")
                data_audit[f"{c['id']}_comment"] = st.session_state.step_comments.get(c["id"], "")
                
            data_audit["Score_Total"] = score
            data_audit["Pourcentage"] = pct
            data_audit["Observations"] = all_obs
            data_audit["Actions_Correctives"] = act_gen
            data_audit["Journal_Horodatage_Clics"] = json.dumps(st.session_state.get("session_clics_log", []), ensure_ascii=False)
            
            ok, err = sauvegarder_audit_local(data_audit)
            if ok:
                st.success("✅ Audit et Journal de Clics enregistrés avec succès !")
                st.session_state.audit_started = False
                st.session_state.user_authenticated = False
                st.session_state.auth_step = 0
            else:
                st.error(f"❌ Erreur d'enregistrement : {err}")
