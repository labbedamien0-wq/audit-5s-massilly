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
    if not HAS_GSHEETS:
        return None, "La bibliothèque 'st-gsheets-connection' n'est pas installée sur Streamlit Cloud (vérifiez votre fichier requirements.txt)."
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn, None
    except Exception as e:
        return None, str(e)

def charger_audits():
    conn, err = get_gsheets_connection()
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

def sauvegarder_audit(data_dict):
    conn, err_conn = get_gsheets_connection()
    
    # Si la connexion échoue d'emblée
    if conn is None:
        try:
            df_local = pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
        except Exception:
            df_local = pd.DataFrame()
        new_row = pd.DataFrame([data_dict])
        df_local = pd.concat([df_local, new_row], ignore_index=True)
        df_local.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')
        return False, f"Connexion Google Sheets impossible : {err_conn}"

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

        # Copie locale
        try:
            df_local = pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
        except Exception:
            df_local = pd.DataFrame()
        df_local = pd.concat([df_local, new_row], ignore_index=True)
        df_local.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

        return True, "✅ Diagnostic enregistré avec succès dans Google Sheets en temps réel !"
    except Exception as e:
        try:
            df_local = pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
        except Exception:
            df_local = pd.DataFrame()
        new_row = pd.DataFrame([data_dict])
        df_local = pd.concat([df_local, new_row], ignore_index=True)
        df_local.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')
        return False, f"Erreur lors de l'écriture Google Sheets : {str(e)}"


# ========================================== STYLE CSS : EFFET WAHOU CINÉMATIQUE 3D ET BLEU MASSILLY RAL 5017
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;600;700;800&family=Playfair+Display:ital,wght=0,600;0,800;1,600&display=swap');

    /* Fond d'application dynamique (Dégradé de bleus onduleux lent en boucle) */
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

    /* Force la couleur claire pour tous les textes par défaut de Streamlit */
    .stApp label, .stApp p, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* CORRECTION RADICALE DU TEXTE BLANC SUR BLANC DANS LES CARTES (RAPPEL DES STANDARDS ET AUDIT) */
    .question-card, .question-card p, .question-card span, .question-card li, .question-card div, .question-card h4, .question-text {
        color: #0F172A !important;
    }

    /* --- TITRE CORPO ULTRA-EXTRUDÉ 3D MÉTALLIQUE ET FLOTTAISON ACTIVE --- */
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
        /* Effet d'extrusion 3D physique lourde */
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
    .main-header-3d:hover {
        transform: perspective(800px) rotateX(5deg) scale(1.03) !important;
        text-shadow: 
            0 1px 0 #38BDF8,
            0 2px 0 #0E529E,
            0 8px 25px rgba(56, 189, 248, 0.5) !important;
    }

    /* --- ENCART DE TITRE : IDENTIFICATION DE L'UTILISATEUR (PLAQUE PRO PRESTIGE CYBER-3D) --- */
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
        border-bottom: 8px solid #005F73 !important; /* Semelle 3D plaque */
    }

    @keyframes floatBadge {
        0% { transform: perspective(800px) rotateX(10deg) translateY(0px) scale(0.98); }
        100% { transform: perspective(800px) rotateX(10deg) translateY(-8px) scale(1.01); }
    }

    /* --- ONGLES DU MENU PRINCIPAL EN PUISSANT DESIGN PHYSIQUE 3D --- */
    /* Container global du radiogroup (Le pupitre de commande métallique) */
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

    /* Style par défaut de chaque bouton-onglet (Plaque de métal inactive suspendue) */
    div[data-testid="stRadio"] div[role="radiogroup"] label, 
    div.row-widget.stRadio label,
    div[data-testid="stRadio"] div[role="radiogroup"] [data-testid="stWidgetLabel"] {
        background: linear-gradient(135deg, #334155, #1E293B) !important;
        color: #94A3B8 !important; /* Contraste soigné gris-bleu clair */
        border: 2px solid #475569 !important;
        /* Épaisse semelle 3D sous le bouton inactif */
        border-bottom: 6px solid #0F172A !important; 
        border-radius: 14px !important;
        padding: 14px 28px !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        text-align: center !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6) !important;
        transform: translateY(-2px) rotateX(10deg);
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3) !important;
    }

    /* Effet de survol : la plaque s'élève et projette son énergie bleue */
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover, 
    div.row-widget.stRadio label:hover {
        color: #FFFFFF !important;
        border-color: #38BDF8 !important;
        transform: translateY(-6px) rotateX(0deg) scale(1.02) !important;
        box-shadow: 
            0 12px 25px rgba(56, 189, 248, 0.35),
            0 4px 8px rgba(0,0,0,0.2) !important;
        border-bottom: 8px solid #0E529E !important;
    }

    /* --- L'ONGLET ACTIF : ENFONCEMENT PHYSIQUE ET ALLUMAGE DE SES LUNETTES NÉON --- */
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
    div.row-widget.stRadio label:has(input:checked),
    div[data-testid="stRadio"] div[role="radiogroup"] div[data-checked="true"] label,
    div.row-widget.stRadio div[data-checked="true"] label,
    div[data-testid="stRadio"] div[role="radiogroup"] [aria-checked="true"] label,
    div.row-widget.stRadio [aria-checked="true"] label,
    div[data-testid="stRadio"] div[role="radiogroup"] [aria-checked="true"],
    div.row-widget.stRadio [aria-checked="true"] {
        background: linear-gradient(135deg, #0E529E 0%, #38BDF8 100%) !important;
        color: #FFFFFF !important;
        border-color: #38BDF8 !important;
        /* Enfoncement physique : la semelle 3D s'écrase */
        border-bottom: 2px solid #063970 !important;
        transform: translateY(4px) rotateX(0deg) scale(0.98) !important;
        /* Halo de lumière intense sous l'onglet actif */
        box-shadow: 
            0 0 35px rgba(56, 189, 248, 0.85),
            0 0 15px rgba(56, 189, 248, 0.4),
            inset 0 0 12px rgba(255, 255, 255, 0.3) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8) !important;
    }

    /* --- CARTES DE CONTENU D'AUDIT EN SUSPENSION (EFFET 3D HAUT CONTRASTE NOIR SUR BLANC) --- */
    .question-card {
        background-color: #FFFFFF !important;
        border: 2px solid #E2E8F0 !important;
        border-left: 8px solid #0E529E !important; /* Signature Bleu Massilly */
        border-radius: 20px !important;
        padding: 30px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3) !important;
        transform: perspective(1000px) rotateX(0deg);
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    .question-card:hover {
        transform: perspective(1000px) rotateX(4deg) translateY(-8px) scale(1.01);
        box-shadow: 0 25px 50px rgba(56, 189, 248, 0.25) !important;
        border-color: #38BDF8 !important;
    }

    .question-cat {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        color: #0E529E !important; /* Bleu Massilly */
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
    }

    .question-text {
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        color: #0F172A !important; /* Noir ardoise contrasté */
        line-height: 1.45;
    }

    /* --- ENTRÉES UTILISATEUR & SELECTBOX GLASSMORPHIC --- */
    div[data-testid="stSelectbox"] > div {
        height: 60px !important;
        background-color: rgba(30, 41, 59, 0.85) !important;
        border: 2px solid #334155 !important;
        border-radius: 12px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    div[data-testid="stSelectbox"] > div:hover {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2) !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        font-size: 20px !important;
        font-weight: 600 !important;
    }

    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        background-color: rgba(30, 41, 59, 0.85) !important;
        color: #FFFFFF !important;
        border: 2px solid #334155 !important;
        border-radius: 12px !important;
        font-size: 20px !important;
        padding: 12px !important;
    }

    div[data-testid="stTextInput"] label, div[data-testid="stTextArea"] label, div[data-testid="stSelectbox"] label {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #E2E8F0 !important;
        margin-bottom: 8px !important;
    }

    /* --- CARRES DE KPI SUSPENDUS (MODULE DE RESULTATS) --- */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1E293B, #0F172A) !important;
        border: 2px solid #334155 !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important;
        transform: perspective(800px) rotateX(5deg);
        transition: all 0.3s ease !important;
    }
    div[data-testid="metric-container"]:hover {
        transform: perspective(800px) rotateX(0deg) translateY(-5px);
        border-color: #38BDF8 !important;
        box-shadow: 0 15px 30px rgba(56, 189, 248, 0.2) !important;
    }

    /* ========================================== STYLE GLOBAL DES BOUTONS DE L'APPLICATION (ENTRER / COMMENCER / ENREGISTRER) ========================================== */
    /* TOUS les boutons standard reçoivent le style Prestige 3D, Shimmer, Pulsation */
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
        /* Semelle 3D mécanique noire/bleu très épaisse */
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
    
    /* Effet Shimmer (Reflet brillant ultra-visible qui glisse sur le bouton) */
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

    .stButton > button:hover,
    div[data-testid="stButton"] button:hover {
        filter: brightness(1.25) !important;
        background-position: right center !important;
        transform: translateY(-8px) !important;
        box-shadow: 
            0 25px 45px rgba(56, 189, 248, 0.75),
            0 0 40px rgba(56, 189, 248, 0.6) !important;
        border-bottom: 12px solid #063970 !important;
    }
    
    .stButton > button:active,
    div[data-testid="stButton"] button:active {
        transform: translateY(4px) !important;
        border-bottom: 2px solid #063970 !important;
        box-shadow: 0 4px 10px rgba(14, 82, 158, 0.2) !important;
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 10px 20px rgba(14, 82, 158, 0.3), 0 0 10px rgba(56, 189, 248, 0.2); }
        100% { box-shadow: 0 10px 40px rgba(56, 189, 248, 0.75), 0 0 25px rgba(56, 189, 248, 0.4); }
    }

    /* --- SPECIFIC OVERRIDES FOR SHINY & GLOSSY START CARD BUTTON --- */
    .btn-start-3d button {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        height: 420px !important; /* Super caisson massif */
        white-space: pre-wrap !important;
        line-height: 1.5 !important;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%) !important;
        color: #FFFFFF !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        border-radius: 28px !important;
        border: 4px solid #0E529E !important; /* Cadre Bleu Massilly */
        border-bottom: 14px solid #063970 !important; /* Énorme semelle 3D mécanique */
        box-shadow: 
            0 30px 60px rgba(0,0,0,0.6),
            0 0 40px rgba(14, 82, 158, 0.4) !important;
        transform: perspective(1000px) rotateX(10deg) translateY(0px) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        text-shadow: 0 2px 5px rgba(0,0,0,0.8) !important;
        padding: 40px !important;
        letter-spacing: 1px;
        cursor: pointer !important;
        position: relative !important;
        overflow: hidden !important;
        animation: pulseGreenGlow 3s infinite alternate !important;
    }

    /* Ajoute la fusée géante rotative EN TANT QUE PSEUDO-ÉLÉMENT intégré au bouton de démarrage */
    .btn-start-3d button::before {
        content: "🚀" !important;
        font-size: 7.5rem !important; /* Giga fusée */
        display: block !important;
        margin-top: -15px !important;
        margin-bottom: 25px !important;
        animation: spinIcon 7s linear infinite !important;
        filter: drop-shadow(0 0 25px rgba(56, 189, 248, 0.8)) !important;
        background: none !important;
        width: auto !important;
        height: auto !important;
    }

    @keyframes spinIcon {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Reflet Glossy/Shiny sweep sur le bouton de démarrage */
    .btn-start-3d button::after {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -150% !important;
        width: 80% !important;
        height: 100% !important;
        background: linear-gradient(
            to right, 
            rgba(255,255,255,0) 0%, 
            rgba(255,255,255,0.3) 50%, 
            rgba(255,255,255,0) 100%
        ) !important;
        transform: skewX(-25deg) !important;
        animation: shineSweepStart 2.5s infinite !important;
    }
    
    @keyframes shineSweepStart {
        0% { left: -150%; }
        100% { left: 250%; }
    }
    
    .btn-start-3d button:hover {
        filter: brightness(1.2) !important;
        transform: perspective(1000px) rotateX(0deg) translateY(-14px) scale(1.03) !important;
        border-color: #38BDF8 !important;
        box-shadow: 
            0 45px 85px rgba(0,0,0,0.7),
            0 0 60px rgba(56, 189, 248, 0.8) !important;
        border-bottom: 18px solid #063970 !important;
    }
    
    .btn-start-3d button:active {
        transform: perspective(1000px) rotateX(0deg) translateY(8px) scale(0.96) !important;
        border-bottom: 3px solid #063970 !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5) !important;
    }
    
    @keyframes pulseGreenGlow {
        0% { box-shadow: 0 15px 30px rgba(14, 82, 158, 0.4), 0 0 15px rgba(56, 189, 248, 0.2); }
        100% { box-shadow: 0 15px 50px rgba(56, 189, 248, 0.85), 0 0 35px rgba(56, 189, 248, 0.5); }
    }

    /* --- BOUTONS TACTILES GÉANTS POUR AUDIT (OUI / NON / N/A) --- */
    div[data-testid="stHorizontalBlock"] button {
        width: 100% !important;
        height: 115px !important;
        font-size: 28px !important;
        font-weight: 900 !important;
        border-radius: 22px !important;
        color: #FFFFFF !important;
        border: none !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.4) !important;
        transition: all 0.15s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        animation: none !important; /* No global pulse glow */
        transform: none !important;
    }
    div[data-testid="stHorizontalBlock"] button::before {
        display: none !important; /* No shimmer */
    }

    /* 🟢 BOUTON OUI (Vert Émeraude Néon) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background: linear-gradient(135deg, #10B981, #059669) !important;
        border-bottom: 8px solid #047857 !important;
        box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2) !important;
        transform: translateY(-4px) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:hover {
        filter: brightness(1.15) !important;
        transform: translateY(-8px) !important;
        box-shadow: 0 15px 30px rgba(16, 185, 129, 0.45) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:active {
        border-bottom: 2px solid #047857 !important;
        transform: translateY(2px) !important;
        box-shadow: 0 3px 6px rgba(16, 185, 129, 0.1) !important;
    }

    /* 🔴 BOUTON NON (Rouge Signal Laser) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background: linear-gradient(135deg, #EF4444, #DC2626) !important;
        border-bottom: 8px solid #B91C1C !important;
        box-shadow: 0 10px 20px rgba(239, 68, 68, 0.2) !important;
        transform: translateY(-4px) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover {
        filter: brightness(1.15) !important;
        transform: translateY(-8px) !important;
        box-shadow: 0 15px 30px rgba(239, 68, 68, 0.45) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:active {
        border-bottom: 2px solid #B91C1C !important;
        transform: translateY(2px) !important;
        box-shadow: 0 3px 8px rgba(239, 68, 68, 0.1) !important;
    }

    /* 🔵 BOUTON N/A (Bleu Slate Électrique) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
        background: linear-gradient(135deg, #3B82F6, #1D4ED8) !important;
        border-bottom: 8px solid #1E40AF !important;
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.2) !important;
        transform: translateY(-4px) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button:hover {
        filter: brightness(1.15) !important;
        transform: translateY(-8px) !important;
        box-shadow: 0 15px 30px rgba(59, 130, 246, 0.45) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button:active {
        border-bottom: 2px solid #1E40AF !important;
        transform: translateY(2px) !important;
        box-shadow: 0 3px 6px rgba(59, 130, 246, 0.1) !important;
    }

    /* --- BOUTONS EN COULOIR POUR LE RETOUR OU LE RESET (SÉLECTEUR ADJACENT ET CONTENEUR) --- */
    .back-btn-container + .stButton button,
    .back-btn-container + div.stButton button,
    .back-btn-container button {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #94A3B8 !important;
        border: 2px solid #475569 !important;
        border-bottom: none !important;
        height: 55px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
        animation: none !important;
        transform: none !important;
    }
    .back-btn-container + .stButton button:hover,
    .back-btn-container + div.stButton button:hover,
    .back-btn-container button:hover {
        background-color: rgba(148, 163, 184, 0.1) !important;
        color: #F8FAFC !important;
        border-color: #94A3B8 !important;
    }

    /* --- BOUTON CHANGER D'UTILISATEUR (RELAXÉ ET PETIT) --- */
    .small-btn-container + .stButton button,
    .small-btn-container + div.stButton button,
    .small-btn-container button {
        height: 50px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border-bottom: 3px solid #0B1329 !important;
        box-shadow: none !important;
        animation: none !important;
        transform: none !important;
        letter-spacing: 0px !important;
        background: #1E293B !important;
    }
    .small-btn-container + .stButton button::before,
    .small-btn-container button::before {
        display: none !important;
    }

    /* ========================================== DOUBLE PORTE CINÉMATIQUE 3D EXTREME ========================================== */
    .portal-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 999999;
        pointer-events: none;
        display: flex;
        perspective: 1200px;
    }
    .portal-door {
        width: 50vw;
        height: 100vh;
        background: linear-gradient(135deg, #0E529E, #0F172A) !important;
        box-sizing: border-box;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 1.8s cubic-bezier(0.85, 0, 0.15, 1);
        border: 12px solid #1E293B;
        box-shadow: inset 0 0 100px rgba(0,0,0,0.85);
    }
    .portal-door-left {
        border-right: 6px solid #38BDF8;
        transform-origin: left center;
        animation: openLeftDoor 2.2s cubic-bezier(0.85, 0, 0.15, 1) forwards;
    }
    .portal-door-right {
        border-left: 6px solid #38BDF8;
        transform-origin: right center;
        animation: openRightDoor 2.2s cubic-bezier(0.85, 0, 0.15, 1) forwards;
    }
    
    /* Rivets de tôle industriels */
    .portal-door::after {
        content: "•  •  •  •  •  •  •";
        position: absolute;
        font-size: 32px;
        color: rgba(56, 189, 248, 0.35);
        letter-spacing: 22px;
    }
    .portal-door-left::after { right: 25px; writing-mode: vertical-rl; }
    .portal-door-right::after { left: 25px; writing-mode: vertical-rl; }

    @keyframes openLeftDoor {
        0% { transform: translateX(0) rotateY(0deg) scale(1); opacity: 1; }
        20% { transform: translateX(0) rotateY(-6deg) scale(0.98); opacity: 1; } /* Recul mécanique */
        100% { transform: translateX(-105%) rotateY(-95deg) scale(0.9); opacity: 0; visibility: hidden; }
    }
    @keyframes openRightDoor {
        0% { transform: translateX(0) rotateY(0deg) scale(1); opacity: 1; }
        20% { transform: translateX(0) rotateY(6deg) scale(0.98); opacity: 1; }
        100% { transform: translateX(105%) rotateY(95deg) scale(0.9); opacity: 0; visibility: hidden; }
    }
</style>
""", unsafe_allow_html=True)

# Affichage permanent du titre principal extrudé et flottant 3D
st.markdown("<h1 class='main-header-3d'>📦 MASSILLY LOGISTIQUE</h1>", unsafe_allow_html=True)

# Affichage du badge de Test si actif
if st.session_state.test_mode:
    st.markdown("<div class='test-badge'>🧪 SESSION DE TEST ACTIVE – ENREGISTREMENTS ISOLÉS</div>", unsafe_allow_html=True)


# ========================================== EFFET CINÉMATIQUE PORTE DOUBLE (WAHOU ENTRÉE)
if st.session_state.user_authenticated and not st.session_state.portal_shown:
    st.markdown("""
    <div class="portal-container">
        <!-- PORTAL DOOR LEFT -->
        <div class="portal-door portal-door-left">
            <div style="text-align: center; color: #FFFFFF !important; font-family: 'Playfair Display', serif;">
                <span style="font-size: 7.5rem; display: block; filter: drop-shadow(0 5px 15px rgba(0,0,0,0.6));">⚙️</span>
                <span style="font-size: 3.5rem; font-weight: 900; letter-spacing: 4px; display: block; color: #FFFFFF !important;">MASSILLY</span>
                <span style="font-size: 1.25rem; color: #38BDF8 !important; letter-spacing: 6px; font-weight: bold; text-transform: uppercase;">MÉTAL INDUSTRIE</span>
            </div>
        </div>
        <!-- PORTAL DOOR RIGHT -->
        <div class="portal-door portal-door-right">
            <div style="text-align: center; color: #FFFFFF !important; font-family: 'Playfair Display', serif;">
                <span style="font-size: 7.5rem; display: block; filter: drop-shadow(0 5px 15px rgba(0,0,0,0.6));">📦</span>
                <span style="font-size: 3.5rem; font-weight: 900; letter-spacing: 4px; display: block; color: #FFFFFF !important;">EXCELLENCE</span>
                <span style="font-size: 1.25rem; color: #38BDF8 !important; letter-spacing: 6px; font-weight: bold; text-transform: uppercase;">LOGISTIQUE 5S</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.portal_shown = True


# ========================================== ÉCRAN 1 : CONNEXION ET CRÉATION DE PROFIL
if not st.session_state.user_authenticated:
    # Grosse plaque 3D "PORTAIL D'IDENTIFICATION" (Remplace la ligne blanche inutile et s'affiche plus gros)
    st.markdown("<div class='user-id-badge-3d'>📋 PORTAIL D'IDENTIFICATION DE L'UTILISATEUR</div>", unsafe_allow_html=True)
    
    # 1. Sélection du Rôle
    role = st.selectbox(
        "Sélectionnez votre rôle :",
        ["Sponsor de zone", "Référent 5S", "Éditeur (Méthodes / Alternant)"]
    )
    
    # Liste nominative de l'usine
    personnes_massilly = [
        "Labbé Damien (Alternant)",
        "Audrey Sordet (Sponsor Z1)",
        "Anthony Duplessis (Sponsor Z2)",
        "Jonathan Mele (Sponsor Z3)",
        "Thomas Collin (Sponsor Z4)",
        "Gaspard Sommereux (Sponsor Z5)",
        "Mariia Leliukh (Sponsor Z6)",
        "Céline Hereng (Sponsor Z7)",
        "Dimitri Dupasquier (Sponsor Z8)",
        "Frédéric Bouvy (Sponsor Z9)",
        "Nathalie Berthelin (Sponsor Z10)",
        "Autre (Saisie manuelle)..."
    ]
    
    # 2. Sélection du Nom
    nom_select = st.selectbox("Sélectionnez votre Prénom & Nom :", personnes_massilly)
    
    if nom_select == "Autre (Saisie manuelle)...":
        nom_complet = st.text_input("Saisissez votre Prénom et Nom :")
    else:
        nom_complet = nom_select.split(" (")[0]
        
    # 3. Sélection de la Zone
    liste_zones = list(ZONES_MASSILLY.keys())
    zone_select = st.selectbox(
        "Zone logistique ciblée :",
        liste_zones,
        format_func=lambda x: ZONES_MASSILLY[x]["label"]
    )
    
    # Choix du Mode Test
    st.markdown("---")
    st.markdown("### Configuration de la base de données")
    st.session_state.test_mode = st.checkbox(
        "🧪 Activer le MODE TEST d'entraînement (Pour valider les diagnostics sans toucher aux statistiques de l'usine)",
        value=st.session_state.test_mode
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
    if st.button("🔓 ENTRER SUR L'APPLICATION", use_container_width=True):
        if not nom_complet.strip():
            st.error("Veuillez renseigner votre nom pour continuer.")
        else:
            st.session_state.user_role = role
            st.session_state.user_name = nom_complet
            st.session_state.user_zone = zone_select
            st.session_state.user_authenticated = True
            st.session_state.portal_shown = False # Réinitialise l'ouverture cinématique pour l'accès
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ========================================== APPLICATION PRINCIPALE (UTILISATEUR CONNECTÉ)
else:
    # Bandeau supérieur d'information de session
    col_u1, col_u2 = st.columns([4, 1])
    with col_u1:
        st.markdown(
            f"👤 **{st.session_state.user_name}** ({st.session_state.user_role}) | Zone active : **{ZONES_MASSILLY[st.session_state.user_zone]['label']}**"
        )
    with col_u2:
        st.markdown("<div class='small-btn-container'>", unsafe_allow_html=True)
        if st.button("🔄 Changer d'utilisateur", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.audit_started = False
            st.session_state.current_q_idx = 0
            st.session_state.answers = {}
            st.session_state.portal_shown = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("---")

    # Onglets horizontaux de navigation (Relookés en boutons command-plates 3D par CSS)
    onglets = ["📋 Saisie d'Audit terrain", "📊 Analyse & Historique", "🗺️ Rappel des Standards"]
    menu_actif = st.radio("Menu principal :", onglets, horizontal=True, key="menu_actif")

    st.markdown("---")

    # ========================================== ONGLET 1 : SAISIE D'AUDIT COMPORTEMENTAL
    if menu_actif == "📋 Saisie d'Audit terrain":
        
        # Étape 1 : Proposition de départ de l'audit (AVEC MASTER CARD BOUTON 3D COMBINÉ)
        if not st.session_state.audit_started:
            st.markdown("<div class='btn-start-3d'>", unsafe_allow_html=True)
            # Les deux textes fusionnés dans un bouton-carte géant de niveau Prestige avec la fusée rotative intégrée par CSS
            btn_label = f"DÉMARRER UNE NOUVELLE VISITE 5S\n\n🚀 COMMENCER LE DIAGNOSTIC TECHNIQUE\n\n📍 Zone Active : {ZONES_MASSILLY[st.session_state.user_zone]['label']}\nSponsor Responsable : {ZONES_MASSILLY[st.session_state.user_zone]['sponsor']}"
            if st.button(btn_label, use_container_width=True):
                st.session_state.audit_started = True
                st.session_state.current_q_idx = 0
                st.session_state.answers = {}
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Étape 2 : Déroulement de l'audit critère par critère
        else:
            idx = st.session_state.current_q_idx
            
            if idx < 15:
                crit = CRITERES_OFFICIELS[idx]
                
                # Progression
                st.progress(idx / 15)
                st.markdown(f"<p style='text-align: right; font-size: 16px; color: #CBD5E1; font-weight: bold;'>Critère {idx+1} sur 15</p>", unsafe_allow_html=True)
                
                # CARTE DU CRITÈRE 3D (Contraste maximal noir sur blanc)
                st.markdown(f"""
                <div class="question-card">
                    <div class="question-cat">{crit['cat']}</div>
                    <div class="question-text">{crit['txt']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<p style='font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 15px;'>Valider l'état sur le terrain :</p>", unsafe_allow_html=True)
                
                # 3 Boutons géants de vote tactile 3D
                col_o, col_n, col_na = st.columns(3)
                with col_o:
                    if st.button("🟢 OUI", use_container_width=True, key=f"btn_o_{idx}"):
                        st.session_state.answers[crit["id"]] = "OUI"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with col_n:
                    if st.button("🔴 NON", use_container_width=True, key=f"btn_n_{idx}"):
                        st.session_state.answers[crit["id"]] = "NON"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                with col_na:
                    if st.button("🔵 N/A", use_container_width=True, key=f"btn_na_{idx}"):
                        st.session_state.answers[crit["id"]] = "N/A"
                        st.session_state.current_q_idx += 1
                        st.rerun()
                
                # --- RETOUR EN ARRIÈRE (Centré sous les boutons) ---
                if idx > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                    if st.button("⬅️ Retour à la question précédente", use_container_width=True, key=f"btn_prev_{idx}"):
                        st.session_state.current_q_idx -= 1
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            # Étape 3 : Fin d'audit et écran de synthèse
            else:
                if "audit_completed" not in st.session_state:
                    st.session_state.audit_completed = False

                if st.session_state.audit_completed:
                    ok, msg = st.session_state.get("audit_result", (False, "Statut inconnu"))
                    if ok:
                        st.success(msg)
                        st.balloons()
                        st.markdown("""
                        <div class="question-card" style="border-left-color: #10B981 !important;">
                            <h3 style="color: #10B981 !important; margin-bottom: 10px;">🎉 Diagnostic synchronisé avec succès !</h3>
                            <p style="color: #0F172A !important; font-size: 18px;">
                                Vos réponses ont été envoyées et enregistrées directement dans votre fichier <b>Google Sheets</b>.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(msg)
                        st.warning("⚠️ L'enregistrement en ligne dans Google Sheets a échoué. Regardez le message d'erreur rouge ci-dessus pour corriger le paramétrage de vos Secrets TOML.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
                    if st.button("🚀 DÉMARRER UN NOUVEL AUDIT", use_container_width=True):
                        st.session_state.audit_started = False
                        st.session_state.audit_completed = False
                        st.session_state.current_q_idx = 0
                        st.session_state.answers = {}
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.success("🎉 Évaluation terminée !")
                    st.subheader("Synthèse de l'évaluation")
                    
                    # Calculs des scores
                    t_oui = sum(1 for v in st.session_state.answers.values() if v == "OUI")
                    t_non = sum(1 for v in st.session_state.answers.values() if v == "NON")
                    t_na = sum(1 for v in st.session_state.answers.values() if v == "N/A")
                    t_app = 15 - t_na
                    
                    score_final_pct = int((t_oui / t_app) * 100) if t_app > 0 else 0
                    
                    # Score d'affichage (Métriques 3D flottantes)
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        st.metric("Critères Conformités", f"{t_oui} / {t_app} conformes")
                    with col_s2:
                        st.metric("Taux de Conformité Final", f"{score_final_pct} %")
                    
                    st.markdown("### 📝 Observations terrain")
                    obs = st.text_area("Remarques / Anomalies constatées :")
                    act = st.text_area("Plan d'action corrective :")
                    
                    # Récapitulatif
                    with st.expander("🔎 Afficher le récapitulatif détaillé"):
                        for c in CRITERES_OFFICIELS:
                            rep = st.session_state.answers.get(c["id"], "N/A")
                            bullet = "🟢" if rep == "OUI" else ("🔴" if rep == "NON" else "🔵")
                            st.markdown(f"{bullet} **{c['cat']}** : {c['txt']} → **{rep}**")
                    
                    # Actions de validation finales
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_end1, col_end2 = st.columns(2)
                    with col_end1:
                        st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
                        if st.button("❌ Réinitialiser l'audit", use_container_width=True):
                            st.session_state.audit_started = False
                            st.session_state.audit_completed = False
                            st.session_state.current_q_idx = 0
                            st.session_state.answers = {}
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    with col_end2:
                        st.markdown("<div class='valide-btn'>", unsafe_allow_html=True)
                        if st.button("💾 ENREGISTRER LE DIAGNOSTIC", use_container_width=True):
                            sc_num = {k: (1 if v == "OUI" else (0 if v == "NON" else "")) for k, v in st.session_state.answers.items()}
                            
                            row_data = {
                                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Zone": st.session_state.user_zone,
                                "Sponsor": ZONES_MASSILLY[st.session_state.user_zone]["sponsor"],
                                "Auditeur": st.session_state.user_name,
                                "Role": st.session_state.user_role,
                                "Score_Total": t_oui,
                                "Pourcentage": score_final_pct,
                                "Observations": obs,
                                "Actions_Correctives": act
                            }
                            row_data.update(sc_num)
                            
                            ok, msg = sauvegarder_audit(row_data)
                            st.session_state.audit_result = (ok, msg)
                            st.session_state.audit_completed = True
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

    # ========================================== ONGLET 2 : TABLEAU DE BORD LOGISTIQUE (KPIs 3D)
    elif menu_actif == "📊 Analyse & Historique":
        st.subheader("Historique d'Amélioration Continue")
        
        df = charger_audits()
        
        if df.empty or len(df) == 0:
            st.warning("Aucune donnée enregistrée dans ce mode d'accès.")
        else:
            tot = len(df)
            moy = int(df["Pourcentage"].mean())
            last_row = df.iloc[-1]
            
            # 3 Métriques en boites 3D en suspension
            k_1, k_2, k_3 = st.columns(3)
            with k_1:
                st.metric("Audits Complétés", tot)
            with k_2:
                st.metric("Performance Moyenne", f"{moy} %")
            with k_3:
                st.metric("Dernière Zone Évaluée", f"{last_row['Zone']} ({last_row['Pourcentage']}%)\"")
                
            st.markdown("### Journal d'activité (Données du fichier CSV)")
            champs = ["Date", "Zone", "Sponsor", "Auditeur", "Role", "Score_Total", "Pourcentage", "Observations", "Actions_Correctives"]
            st.dataframe(df[champs].sort_values(by="Date", ascending=False), use_container_width=True)

            try:
                df_c = df.pivot_table(index="Date", columns="Zone", values="Pourcentage", aggfunc='last').ffill()
                st.markdown("### Courbes de Progrès par Zone")
                st.line_chart(df_c)
            except Exception:
                pass

    # ========================================== ONGLET 3 : RAPPEL DES CODES DE L'USINE MASSILLY
    elif menu_actif == "🗺️ Rappel des Standards":
        st.subheader("Les Impératifs Physiques et Visuels de Massilly")
        
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            # Plaque blanche 3D de rappel standard
            st.markdown("""
            <div class="question-card" style="border-left-color: #EF4444 !important;">
                <h4 style="color: #EF4444 !important; font-weight: 800; margin-bottom: 12px;">🟥 Le Code de Couleur au Sol (Standard Massilly)</h4>
                <p style="color: #0F172A !important; font-size: 1.1rem; line-height: 1.5;">
                    • <b>Zones de blocage et anomalies</b> : Doivent obligatoirement être peintes ou entourées de bandes <b>ROUGES</b> au sol (ex: <i>Zone Anomalie Boîtes</i>).<br>
                    • <b>Condition Obligatoire</b> : Toute palette déposée dans cette zone rouge de blocage doit <b>obligatoirement posséder une feuille d'identification bleue</b> complétée et scotchée de manière visible.<br>
                    • <b>Aires AGV / Chariots</b> : Tracées obligatoirement en <b>ROUGE VIF</b> pour la sécurité du personnel.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_st2:
            st.markdown("""
            <div class="question-card" style="border-left-color: #3B82F6 !important;">
                <h4 style="color: #0E529E !important; font-weight: 800; margin-bottom: 12px;">⬜ Tracés pour Accessoires de Conditionnement</h4>
                <p style="color: #0F172A !important; font-size: 1.1rem; line-height: 1.5;">
                    • <b>Matériels Mobiles et Outils</b> : Matérialisés au sol par un marquage de couleur <b>BLANCHE</b> (bac à cornières de Lucien Lefebvre, kit de cerclage, table de préparation, etc.).<br>
                    • <b>Stations de propreté</b> : Les 21 stations mobiles Seton acquises par Massilly doivent être garées dans leurs emplacements blancs de propreté à chaque fin de poste.<br>
                    • <b>Règle d'or</b> : Remettre tous les outils de balayage, pelles et consommables dans leurs stations prévues.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        st.markdown("#### Plan de Responsabilité Officiel des 10 Zones")
        for k, v in ZONES_MASSILLY.items():
            st.markdown(f"📍 **{k}** : {v['label']} — **Sponsor officiel de zone** : `{v['sponsor']}`")
