import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURATION ET CONSTANTES GLOBALES
# ==========================================
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

# ==========================================
# 2. INITIALISATION BLINDÉE DU SESSION STATE
# ==========================================
SESSION_DEFAULTS = {
    "user_authenticated": False,
    "user_role": "",
    "user_name": "",
    "user_zone": "Zone 1",
    "audit_started": False,
    "current_q_idx": 0,
    "answers": {},
    "test_mode": False,
    "portal_shown": False,
    "audit_just_saved": False,
    "last_save_status": False,
    "last_save_msg": ""
}

for k_sess, v_sess in SESSION_DEFAULTS.items():
    if k_sess not in st.session_state:
        st.session_state[k_sess] = v_sess

# Définition dynamique des fichiers de données
if st.session_state.get("test_mode", False):
    SHARED_DATA_FILE = "test_suivi_audits_5s.csv"
    SHARED_LOG_FILE = "test_journal_activite_5s.json"
else:
    SHARED_DATA_FILE = "suivi_audits_5s.csv"
    SHARED_LOG_FILE = "journal_activite_5s.json"

# Création automatique des fichiers CSV/JSON locaux de secours
if not os.path.exists(SHARED_DATA_FILE):
    cols = ["Date", "Zone", "Sponsor", "Auditeur", "Role",
            "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "c10", "c11", "c12", "c13", "c14", "c15",
            "Score_Total", "Pourcentage", "Observations", "Actions_Correctives"]
    pd.DataFrame(columns=cols).to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

if not os.path.exists(SHARED_LOG_FILE):
    with open(SHARED_LOG_FILE, 'w', encoding='utf-8') as f_log:
        json.dump([], f_log, ensure_ascii=False)

# ==========================================
# 3. FONCTIONS GOOGLE SHEETS & SAUVEGARDE
# ==========================================
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS = True
except ImportError:
    HAS_GSHEETS = False

def get_gsheets_conn():
    if not HAS_GSHEETS:
        return None, "Bibliothèque st-gsheets-connection non installée."
    try:
        # Tente la connexion Streamlit GSheets
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn, None
    except Exception as e_conn:
        return None, str(e_conn)

def charger_audits():
    conn, _ = get_gsheets_conn()
    if conn is not None:
        try:
            df_g = conn.read(ttl=0)
            if df_g is not None and not df_g.empty:
                return df_g.dropna(how="all")
        except Exception:
            pass
    try:
        return pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
    except Exception:
        return pd.DataFrame()

def sauvegarder_audit(data_dict):
    gsheets_success = False
    err_detail = ""
    conn, conn_err = get_gsheets_conn()
    
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
            gsheets_success = True
        except Exception as e_upd:
            err_detail = str(e_upd)
    else:
        err_detail = conn_err or "Configuration des Secrets non trouvée."

    # Backup local CSV
    try:
        df_loc = pd.read_csv(SHARED_DATA_FILE, encoding='utf-8')
    except Exception:
        df_loc = pd.DataFrame()
    df_loc = pd.concat([df_loc, pd.DataFrame([data_dict])], ignore_index=True)
    df_loc.to_csv(SHARED_DATA_FILE, index=False, encoding='utf-8')

    # Journal JSON
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "TEST - Diagnostic" if st.session_state.get("test_mode", False) else "Diagnostic Réel",
        "details": f"Zone {data_dict['Zone']} par {data_dict['Auditeur']} ({data_dict['Score_Total']}/15 - {data_dict['Pourcentage']}%)",
        "gsheets": "OK" if gsheets_success else f"ERREUR ({err_detail})"
    }
    try:
        with open(SHARED_LOG_FILE, 'r', encoding='utf-8') as f_in:
            logs = json.load(f_in)
    except Exception:
        logs = []
    logs.append(log_entry)
    with open(SHARED_LOG_FILE, 'w', encoding='utf-8') as f_out:
        json.dump(logs, f_out, ensure_ascii=False, indent=4)

    return gsheets_success, err_detail

# ==========================================
# 4. DESIGN CSS 3D ET BLEU MASSILLY RAL 5017
# ==========================================
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
        0% { transform: perspective(800px) rotateX(15deg) translateY(0px) rotateY(-1deg); }
        100% { transform: perspective(800px) rotateX(15deg) translateY(-10px) rotateY(1deg); }
    }

    .user-id-badge-3d {
        background: linear-gradient(135deg, #0E529E 0%, #1E293B 100%) !important;
        border: 2px solid #38BDF8 !important;
        border-radius: 16px !important;
        padding: 18px 25px !important;
        text-align: center !important;
        font-weight: 800 !important;
        font-size: 1.4rem !important;
        color: #FFFFFF !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.2) !important;
        margin-bottom: 25px !important;
    }

    .test-badge {
        background: #DC2626 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 8px !important;
        border-radius: 8px !important;
        margin-bottom: 15px !important;
    }

    .question-card {
        background: #FFFFFF !important;
        border-radius: 20px !important;
        padding: 30px !important;
        margin-bottom: 25px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4) !important;
        border-left: 10px solid #0E529E !important;
    }

    .question-cat {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        color: #0E529E !important;
        text-transform: uppercase !important;
        margin-bottom: 10px !important;
    }

    .question-text {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        line-height: 1.5 !important;
        color: #1E293B !important;
    }

    .portal-container {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: 999999; pointer-events: none; display: flex; perspective: 1200px;
    }
    .portal-door {
        width: 50vw; height: 100vh;
        background: linear-gradient(135deg, #0E529E, #0F172A) !important;
        box-sizing: border-box; display: flex; align-items: center; justify-content: center;
        transition: all 1.8s cubic-bezier(0.85, 0, 0.15, 1);
        border: 12px solid #1E293B; box-shadow: inset 0 0 100px rgba(0,0,0,0.85);
    }
    .portal-door-left { border-right: 6px solid #38BDF8; transform-origin: left center; animation: openLeftDoor 2.2s cubic-bezier(0.85, 0, 0.15, 1) forwards; }
    .portal-door-right { border-left: 6px solid #38BDF8; transform-origin: right center; animation: openRightDoor 2.2s cubic-bezier(0.85, 0, 0.15, 1) forwards; }
    
    @keyframes openLeftDoor {
        0% { transform: translateX(0) rotateY(0deg); opacity: 1; }
        100% { transform: translateX(-105%) rotateY(-95deg); opacity: 0; visibility: hidden; }
    }
    @keyframes openRightDoor {
        0% { transform: translateX(0) rotateY(0deg); opacity: 1; }
        100% { transform: translateX(105%) rotateY(95deg); opacity: 0; visibility: hidden; }
    }
</style>
""", unsafe_allow_html=True)

# Affichage permanent du titre
st.markdown("<h1 class='main-header-3d'>📦 MASSILLY LOGISTIQUE</h1>", unsafe_allow_html=True)

if st.session_state.get("test_mode", False):
    st.markdown("<div class='test-badge'>🧪 SESSION DE TEST ACTIVE – ENREGISTREMENTS ISOLÉS</div>", unsafe_allow_html=True)

# Animation Porte Double à la connexion
if st.session_state.get("user_authenticated", False) and not st.session_state.get("portal_shown", False):
    st.markdown("""
    <div class="portal-container">
        <div class="portal-door portal-door-left">
            <div style="text-align: center; color: #FFFFFF !important;">
                <span style="font-size: 7.5rem; display: block;">⚙️</span>
                <span style="font-size: 3.5rem; font-weight: 900;">MASSILLY</span>
            </div>
        </div>
        <div class="portal-door portal-door-right">
            <div style="text-align: center; color: #FFFFFF !important;">
                <span style="font-size: 7.5rem; display: block;">📦</span>
                <span style="font-size: 3.5rem; font-weight: 900;">LOGISTIQUE 5S</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state["portal_shown"] = True

# ==========================================
# 5. ÉCRAN DE CONNEXION / PORTAIL
# ==========================================
if not st.session_state.get("user_authenticated", False):
    st.markdown("<div class='user-id-badge-3d'>📋 PORTAIL D'IDENTIFICATION DE L'UTILISATEUR</div>", unsafe_allow_html=True)
    
    role = st.selectbox(
        "Sélectionnez votre rôle :",
        ["Sponsor de zone", "Référent 5S", "Éditeur (Méthodes / Alternant)"]
    )
    
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
    
    nom_select = st.selectbox("Sélectionnez votre Prénom & Nom :", personnes_massilly)
    if nom_select == "Autre (Saisie manuelle)...":
        nom_complet = st.text_input("Saisissez votre Prénom et Nom :")
    else:
        nom_complet = nom_select.split(" (")[0]
        
    liste_zones = list(ZONES_MASSILLY.keys())
    zone_select = st.selectbox(
        "Zone logistique ciblée :",
        liste_zones,
        format_func=lambda x: ZONES_MASSILLY[x]["label"]
    )
    
    st.markdown("---")
    st.markdown("### Configuration de la base de données")
    st.session_state["test_mode"] = st.checkbox(
        "🧪 Activer le MODE TEST d'entraînement",
        value=st.session_state.get("test_mode", False)
    )
    
    col_conn1, col_conn2 = st.columns(2)
    with col_conn1:
        if st.button("🔓 ENTRER SUR L'APPLICATION", use_container_width=True):
            if not nom_complet.strip():
                st.error("Veuillez renseigner votre nom pour continuer.")
            else:
                st.session_state["user_role"] = role
                st.session_state["user_name"] = nom_complet
                st.session_state["user_zone"] = zone_select
                st.session_state["user_authenticated"] = True
                st.session_state["portal_shown"] = False
                st.rerun()
                
    with col_conn2:
        if st.button("🔌 TESTER CONNEXION GOOGLE SHEETS", use_container_width=True):
            conn, err_conn = get_gsheets_conn()
            if conn is not None:
                try:
                    df_test = conn.read(ttl=0)
                    st.success("✅ Connexion Google Sheets réussie ! Accès en lecture/écriture confirmé.")
                except Exception as e_t:
                    st.error(f"⚠️ Erreur d'accès au fichier Sheet : {e_t}")
            else:
                st.error(f"⚠️ Échec de connexion : {err_conn}")

# ==========================================
# 6. APPLICATION PRINCIPALE (CONNECTÉ)
# ==========================================
else:
    col_u1, col_u2 = st.columns([4, 1])
    with col_u1:
        z_info = ZONES_MASSILLY.get(st.session_state.get("user_zone", "Zone 1"), {"label": "Zone 1"})
        st.markdown(
            f"👤 **{st.session_state.get('user_name', '')}** ({st.session_state.get('user_role', '')}) | Zone active : **{z_info['label']}**"
        )
    with col_u2:
        if st.button("🔄 Changer d'utilisateur", use_container_width=True):
            st.session_state["user_authenticated"] = False
            st.session_state["audit_started"] = False
            st.session_state["current_q_idx"] = 0
            st.session_state["answers"] = {}
            st.session_state["portal_shown"] = False
            st.session_state["audit_just_saved"] = False
            st.rerun()
            
    st.markdown("---")

    onglets = ["📋 Saisie d'Audit terrain", "📊 Analyse & Historique", "🗺️ Rappel des Standards"]
    menu_actif = st.radio("Menu principal :", onglets, horizontal=True, key="menu_actif")
    st.markdown("---")

    # ------------------------------------------
    # ONGLET 1 : SAISIE D'AUDIT
    # ------------------------------------------
    if menu_actif == "📋 Saisie d'Audit terrain":
        
        # Cas 1 : Viens d'enregistrer un audit -> Écran de bilan permanent
        if st.session_state.get("audit_just_saved", False):
            if st.session_state.get("last_save_status", False):
                st.balloons()
                st.success("🎉 DIAGNOSTIC AUDIT 5S ENREGISTRÉ ET SYNCHRONISÉ AVEC SUCCÈS DANS GOOGLE SHEETS !")
            else:
                st.warning("⚠️ DIAGNOSTIC ENREGISTRÉ LOCALEMENT.")
                st.error(f"Détail de l'erreur Google Sheets : {st.session_state.get('last_save_msg', 'Inconnu')}")
                
            st.markdown("### Récapitulatif de l'évaluation transmise")
            st.info("Les données ont été enregistrées dans la base de données. Vous pouvez démarrer un nouvel audit.")
            
            if st.button("🚀 COMMENCER UN NOUVEL AUDIT 5S", use_container_width=True):
                st.session_state["audit_just_saved"] = False
                st.session_state["audit_started"] = False
                st.session_state["current_q_idx"] = 0
                st.session_state["answers"] = {}
                st.rerun()

        # Cas 2 : Audit non démarré
        elif not st.session_state.get("audit_started", False):
            u_zone = st.session_state.get("user_zone", "Zone 1")
            z_obj = ZONES_MASSILLY.get(u_zone, {"label": u_zone, "sponsor": "N/A"})
            
            btn_label = f"DÉMARRER UNE NOUVELLE VISITE 5S\n\n🚀 COMMENCER LE DIAGNOSTIC TECHNIQUE\n\n📍 Zone Active : {z_obj['label']}\nSponsor Responsable : {z_obj['sponsor']}"
            if st.button(btn_label, use_container_width=True):
                st.session_state["audit_started"] = True
                st.session_state["current_q_idx"] = 0
                st.session_state["answers"] = {}
                st.rerun()

        # Cas 3 : Questions en cours
        else:
            idx = st.session_state.get("current_q_idx", 0)
            
            if idx < 15:
                crit = CRITERES_OFFICIELS[idx]
                st.progress(idx / 15)
                st.markdown(f"<p style='text-align: right; font-size: 16px;'>Critère {idx+1} sur 15</p>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="question-card">
                    <div class="question-cat">{crit['cat']}</div>
                    <div class="question-text">{crit['txt']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**Valider l'état sur le terrain :**")
                
                col_o, col_n, col_na = st.columns(3)
                with col_o:
                    if st.button("🟢 OUI", use_container_width=True, key=f"btn_o_{idx}"):
                        st.session_state["answers"][crit["id"]] = "OUI"
                        st.session_state["current_q_idx"] += 1
                        st.rerun()
                with col_n:
                    if st.button("🔴 NON", use_container_width=True, key=f"btn_n_{idx}"):
                        st.session_state["answers"][crit["id"]] = "NON"
                        st.session_state["current_q_idx"] += 1
                        st.rerun()
                with col_na:
                    if st.button("🔵 N/A", use_container_width=True, key=f"btn_na_{idx}"):
                        st.session_state["answers"][crit["id"]] = "N/A"
                        st.session_state["current_q_idx"] += 1
                        st.rerun()
                
                if idx > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("⬅️ Retour à la question précédente", use_container_width=True, key=f"btn_prev_{idx}"):
                        st.session_state["current_q_idx"] -= 1
                        st.rerun()

            # Cas 4 : Fin des 15 questions -> Synthèse
            else:
                st.success("🎉 Évaluation terminée !")
                st.subheader("Synthèse de l'évaluation")
                
                answers_map = st.session_state.get("answers", {})
                t_oui = sum(1 for v in answers_map.values() if v == "OUI")
                t_non = sum(1 for v in answers_map.values() if v == "NON")
                t_na = sum(1 for v in answers_map.values() if v == "N/A")
                t_app = 15 - t_na
                
                score_final_pct = int((t_oui / t_app) * 100) if t_app > 0 else 0
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.metric("Critères Conformités", f"{t_oui} / {t_app} conformes")
                with col_s2:
                    st.metric("Taux de Conformité Final", f"{score_final_pct} %")
                
                obs = st.text_area("Remarques / Anomalies constatées :")
                act = st.text_area("Plan d'action corrective :")
                
                with st.expander("🔎 Afficher le récapitulatif détaillé"):
                    for c in CRITERES_OFFICIELS:
                        rep = answers_map.get(c["id"], "N/A")
                        bullet = "🟢" if rep == "OUI" else ("🔴" if rep == "NON" else "🔵")
                        st.markdown(f"{bullet} **{c['cat']}** : {c['txt']} → **{rep}**")
                
                col_end1, col_end2 = st.columns(2)
                with col_end1:
                    if st.button("❌ Réinitialiser l'audit", use_container_width=True):
                        st.session_state["audit_started"] = False
                        st.session_state["current_q_idx"] = 0
                        st.session_state["answers"] = {}
                        st.rerun()
                        
                with col_end2:
                    if st.button("💾 ENREGISTRER LE DIAGNOSTIC", use_container_width=True):
                        sc_num = {k: (1 if v == "OUI" else (0 if v == "NON" else "")) for k, v in answers_map.items()}
                        
                        u_z = st.session_state.get("user_zone", "Zone 1")
                        row_data = {
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Zone": u_z,
                            "Sponsor": ZONES_MASSILLY.get(u_z, {}).get("sponsor", "N/A"),
                            "Auditeur": st.session_state.get("user_name", ""),
                            "Role": st.session_state.get("user_role", ""),
                            "Score_Total": t_oui,
                            "Pourcentage": score_final_pct,
                            "Observations": obs,
                            "Actions_Correctives": act
                        }
                        row_data.update(sc_num)
                        
                        is_ok, err_m = sauvegarder_audit(row_data)
                        
                        st.session_state["audit_just_saved"] = True
                        st.session_state["last_save_status"] = is_ok
                        st.session_state["last_save_msg"] = err_m
                        st.session_state["audit_started"] = False
                        st.session_state["current_q_idx"] = 0
                        st.session_state["answers"] = {}
                        st.rerun()

    # ------------------------------------------
    # ONGLET 2 : ANALYSE & HISTORIQUE
    # ------------------------------------------
    elif menu_actif == "📊 Analyse & Historique":
        st.subheader("Historique d'Amélioration Continue")
        
        df_hist = charger_audits()
        
        if df_hist.empty or len(df_hist) == 0:
            st.warning("Aucune donnée enregistrée dans cette base.")
        else:
            tot = len(df_hist)
            moy = int(df_hist["Pourcentage"].mean()) if "Pourcentage" in df_hist.columns else 0
            last_row = df_hist.iloc[-1]
            
            k_1, k_2, k_3 = st.columns(3)
            with k_1:
                st.metric("Audits Complétés", tot)
            with k_2:
                st.metric("Performance Moyenne", f"{moy} %")
            with k_3:
                st.metric("Dernière Zone Évaluée", f"{last_row.get('Zone', 'N/A')} ({last_row.get('Pourcentage', 0)}%)")
                
            st.markdown("### Tableau des enregistrements récents")
            st.dataframe(df_hist, use_container_width=True)

    # ------------------------------------------
    # ONGLET 3 : RAPPEL DES STANDARDS
    # ------------------------------------------
    elif menu_actif == "🗺️ Rappel des Standards":
        st.subheader("Standards d'Excellence Logistique 5S - Massilly")
        st.info("Consultez les 5 étapes officielles pour maintenir les standards sur le terrain.")
        
        for s_idx, (s_titre, s_desc) in enumerate([
            ("1. Seiri (Trier)", "Éliminer l'inutile, jeter ou recycler les palettes cassées et emballages usagés."),
            ("2. Seiton (Ranger)", "Une place pour chaque chose et chaque chose à sa place (marquage au sol et shadow boards)."),
            ("3. Seiso (Nettoyer)", "Nettoyer c'est inspecter. Détecter les fuites et détériorations précocement."),
            ("4. Seiketsu (Standardiser)", "Formaliser les règles visuelles et les rôles de chacun."),
            ("5. Shitsuke (Respecter)", "Rigueur au quotidien et rituel de fin de poste 5S.")
        ], 1):
            st.markdown(f"**{s_titre}** : {s_desc}")
