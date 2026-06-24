"""
app.py — Interface Streamlit pour la génération du PPSPS.
Navigation Précédent / Suivant avec persistance totale des données entre sections.
"""

import csv
import io
import streamlit as st
from pypdf import PdfReader, PdfWriter
from ppsps_generator import generer_ppsps

st.set_page_config(page_title="Générateur PPSPS", page_icon="🏗️", layout="wide")

# ════════════════════════════════════════════════════════════════════════════
# PERSISTANCE — snapshot des valeurs de widgets avant qu'elles soient effacées
# Streamlit supprime les clés de session_state des widgets non rendus.
# On copie toutes les valeurs connues vers des clés _p_* qui, elles, persistent.
# ════════════════════════════════════════════════════════════════════════════
_STATIC_KEYS = [
    # Entreprise & Projet
    "ent_nom","ent_adresse","ent_tel","ent_email","ent_resp","ent_tel_resp","ent_email_resp",
    "proj_intitule","proj_client","proj_situation","proj_type","proj_description",
    "proj_debut","proj_duree","proj_effectif","proj_avis","proj_date_creation","acces_site",
    # Gestion
    "gest_elab","gest_verif","gest_appro","nb_rev",
    "diff_moa","diff_moe","diff_mand","diff_cotrait","diff_st","diff_csps",
    "diff_qse","diff_dir","diff_conducteur","diff_chef",
    # Intervenants
    "moa_nom","moa_adr","moa_int","moa_tel","moa_em",
    "moe_nom","moe_adr","moe_int","moe_tel","moe_em",
    "csps_nom","csps_adr","csps_int","csps_tel","csps_em",
    "it_nom","it_adr","it_int","it_tel","it_em",
    "med_nom","med_adr","med_int","med_tel","med_em",
    # Organisation
    "nb_membres",
    "inst_charge","inst_bungalow","inst_remorque","inst_locaux","inst_autre",
    "vest_nb","vest_surf","vest_com",
    "ref_nb","ref_surf","ref_com",
    "san_nb","san_surf","san_com",
    "en_elec","en_group","en_gaz","eau","repas","date_inst",
    # Secours
    "sec_tel","sec_nom","sec_num","sec_adresse","sec_sst","sec_defib",
    "epi_text","consignes_text","proprete_text","nb_sign",
]

_MAX_DYN = 25  # maximum pour les listes dynamiques

def _snapshot():
    """Copie toutes les valeurs de widgets actuellement en session vers les clés _p_.
    Sautée juste après un import CSV pour ne pas écraser les valeurs importées."""
    if st.session_state.pop("_skip_snapshot", False):
        return
    for k in _STATIC_KEYS:
        if k in st.session_state:
            st.session_state[f"_p_{k}"] = st.session_state[k]
    for i in range(_MAX_DYN):
        for k in [
            f"rev_ind_{i}", f"rev_date_{i}", f"rev_nat_{i}",
            f"role_{i}", f"membre_{i}",
            f"sign_nom_{i}", f"sign_ent_{i}",
            f"r_phase_{i}", f"r_facteur_{i}", f"r_sit_{i}",
            f"r_risque_{i}", f"r_dang_{i}", f"r_expo_{i}", f"r_mes_{i}",
        ]:
            if k in st.session_state:
                st.session_state[f"_p_{k}"] = st.session_state[k]

_snapshot()  # ← exécuté à chaque render, AVANT le rendu des widgets

# ── Données entreprise fixes (non modifiables) ────────────────────────────
ENTREPRISE_FIXE = {
    "ent_nom": "Agence Deldossi Assainissement",
    "ent_adresse": "490 Route de Toulouse, 81370 Saint-Sulpice-la-Pointe",
    "ent_tel": "05 63 40 21 98",
    "ent_email": "contact@deldossi-assainissement.com",
    "ent_resp": "Kevin HAVEL",
    "ent_tel_resp": "06 27 25 59 82",
    "ent_email_resp": "k.havel@deldossi-assainissement.com",
}
# Toujours injecter dans les clés persistées (pour export CSV + génération)
for _k, _v in ENTREPRISE_FIXE.items():
    st.session_state[f"_p_{_k}"] = _v

# ── Intervenants de prévention fixes (non modifiables) ────────────────────
# Ces organismes sont stables d'un chantier à l'autre (rattachement géographique
# de l'entreprise dans le Tarn). Injectés comme ENTREPRISE_FIXE.
# NB : le Coordinateur SPS (csps) est en théorie désigné par le maître d'ouvrage
# pour CHAQUE opération. S'il devait varier selon les chantiers, déplacer la clé
# "csps_*" hors de PREVENTION_FIXE et la repasser en champ éditable (voir section 3).
PREVENTION_FIXE = {
    # Inspection du travail
    "it_nom": "D.I.R.E.C.C.T.E",
    "it_adr": "44, Boulevard Maréchal Lannes Cantepau BP 18 81027 ALBI CEDEX 9",
    "it_int": "",
    "it_tel": "05.63.78.32.44",
    "it_em": "",
    # Médecine du travail
    "med_nom": "SPSTI 81 – Dr GAFFET",
    "med_adr": "12 rue léonard de Vinci 81500 LAVAUR",
    "med_int": "",
    "med_tel": "05 63 58 54 23",
    "med_em": "secretariatdrgaffet@spsti81.fr",
}
for _k, _v in PREVENTION_FIXE.items():
    st.session_state[f"_p_{_k}"] = _v

# ── Coordinateur SPS : éditable, mais pré-rempli par défaut ────────────────
# Le CSPS est désigné par le maître d'ouvrage pour chaque opération : il reste
# donc modifiable. On ne fait que SEMER une valeur par défaut (setdefault) la
# première fois — les saisies et imports ultérieurs ne sont jamais écrasés.
CSPS_DEFAUT = {
    "csps_nom": "ELYFEC SPS",
    "csps_adr": "16 rue du Cassé 31240 SAINT-JEAN",
    "csps_tel": "05.61.16.61.79",
}
for _k, _v in CSPS_DEFAUT.items():
    st.session_state.setdefault(f"_p_{_k}", _v)

# ── Raccourcis lecture / écriture persistance ─────────────────────────────
def g(key, default=""):
    """Lire la valeur persistée d'un champ (ou default si pas encore saisie)."""
    return st.session_state.get(f"_p_{key}", default)

# ════════════════════════════════════════════════════════════════════════════
# EXPORT / IMPORT CSV
# ════════════════════════════════════════════════════════════════════════════
# Clés dont la valeur est un booléen (pour conversion correcte à l'import)
_BOOL_KEYS = {
    "proj_avis",
    "diff_moa","diff_moe","diff_mand","diff_cotrait","diff_st","diff_csps",
    "diff_qse","diff_dir","diff_conducteur","diff_chef",
    "inst_charge","inst_bungalow","inst_remorque","inst_locaux","inst_autre",
    "en_elec","en_group","en_gaz",
}
# Clés dont la valeur est un entier
_INT_KEYS = {"nb_rev", "nb_membres", "nb_sign"}

_DYN_PREFIXES = [
    "rev_ind_","rev_date_","rev_nat_",
    "role_","membre_",
    "sign_nom_","sign_ent_",
    "r_phase_","r_facteur_","r_sit_","r_risque_","r_dang_","r_expo_","r_mes_",
]

def _all_data_rows():
    """Retourne toutes les paires (clé, valeur) à exporter."""
    rows = []
    # Clé spéciale nb_risques (directement dans session_state)
    rows.append(("nb_risques", str(st.session_state.get("nb_risques", 3))))
    # Clés statiques
    for k in _STATIC_KEYS:
        rows.append((k, str(g(k, ""))))
    # Clés dynamiques (on exporte toutes les valeurs, même vides, pour la fidélité)
    for i in range(_MAX_DYN):
        for pfx in _DYN_PREFIXES:
            k = f"{pfx}{i}"
            rows.append((k, str(g(k, ""))))
    return rows

def export_csv() -> bytes:
    """Sérialise toutes les données du formulaire en CSV (encodage UTF-8 BOM pour Excel)."""
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow(["cle", "valeur"])
    writer.writerows(_all_data_rows())
    return buf.getvalue().encode("utf-8-sig")

def import_csv(file_bytes: bytes):
    """Charge un CSV exporté et restaure toutes les valeurs dans le session_state."""
    content = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    loaded = 0
    for row in reader:
        k = row.get("cle","").strip()
        v = row.get("valeur","")
        if not k:
            continue
        if k == "nb_risques":
            try:
                st.session_state.nb_risques = max(1, int(v))
            except ValueError:
                pass
        elif k in _BOOL_KEYS:
            val = v.strip().lower() in ("true", "1", "oui", "yes")
            st.session_state[f"_p_{k}"] = val
            st.session_state[k] = val  # met à jour la clé widget directe
        elif k in _INT_KEYS:
            try:
                val = max(0, int(v))
                st.session_state[f"_p_{k}"] = val
                st.session_state[k] = val  # met à jour la clé widget directe
            except ValueError:
                pass
        else:
            st.session_state[f"_p_{k}"] = v
            st.session_state[k] = v  # met à jour la clé widget directe
        loaded += 1
    # Les champs figés restent prioritaires même après import
    for _k, _v in ENTREPRISE_FIXE.items():
        st.session_state[f"_p_{_k}"] = _v
    for _k, _v in PREVENTION_FIXE.items():
        st.session_state[f"_p_{_k}"] = _v
    return loaded

# ── Constantes de navigation ──────────────────────────────────────────────
TAB_NAMES = [
    "1 · Entreprise & Projet",
    "2 · Gestion & Diffusion",
    "3 · Intervenants",
    "4 · Organisation & Installation",
    "5 · Secours & Prévention",
    "6 · Analyse des risques",
    "7 · Annexes",
    "8 · Générer le PDF",
]
N_TABS = len(TAB_NAMES)

# ── Init session state ────────────────────────────────────────────────────
if "tab" not in st.session_state:
    st.session_state.tab = 0
if "nb_risques" not in st.session_state:
    st.session_state.nb_risques = 3
if "annexes" not in st.session_state:
    st.session_state.annexes = []

def go_to(n):
    st.session_state.tab = n

def nav_buttons(current):
    st.write("")
    left, _, right = st.columns([1, 6, 1])
    if current > 0:
        left.button("← Précédent", key=f"prev_{current}",
                    on_click=go_to, args=(current - 1,), use_container_width=True)
    if current < N_TABS - 1:
        right.button("Suivant →", key=f"next_{current}",
                     on_click=go_to, args=(current + 1,), use_container_width=True,
                     type="primary")

# ── En-tête + barre de navigation ────────────────────────────────────────
st.title("🏗️ Générateur PPSPS")

cols = st.columns(N_TABS)
for i, (col, name) in enumerate(zip(cols, TAB_NAMES)):
    col.button(name, key=f"nav_{i}", use_container_width=True,
               type="primary" if i == st.session_state.tab else "secondary",
               on_click=go_to, args=(i,))
st.divider()

# ── Bandeau Export / Import ────────────────────────────────────────────────
with st.expander("💾 Sauvegarder / Charger mes données", expanded=False):
    col_exp, col_imp = st.columns(2)
    with col_exp:
        st.markdown("**📤 Exporter**")
        st.caption("Téléchargez toutes vos données au format CSV. Vous pourrez les recharger plus tard pour pré-remplir le formulaire.")
        csv_bytes = export_csv()
        st.download_button(
            label="⬇️ Télécharger le CSV",
            data=csv_bytes,
            file_name="ppsps_donnees.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_imp:
        st.markdown("**📥 Importer**")
        st.caption("Chargez un CSV précédemment exporté pour pré-remplir automatiquement tous les champs.")
        uploaded_csv = st.file_uploader("Fichier CSV", type=["csv"],
                                        label_visibility="collapsed",
                                        key="csv_uploader")
        if uploaded_csv is not None:
            if st.button("✅ Charger les données", use_container_width=True, type="primary",
                         key="btn_import"):
                n = import_csv(uploaded_csv.read())
                # Signaler au prochain render de sauter le snapshot pour ne pas
                # écraser les valeurs importées avec les anciennes valeurs des widgets
                st.session_state["_skip_snapshot"] = True
                st.success(f"{n} champs importés — les sections sont maintenant pré-remplies.")
                st.rerun()

st.divider()

tab = st.session_state.tab

# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Entreprise & Projet
# ════════════════════════════════════════════════════════════════════════════
if tab == 0:
    st.subheader("Votre entreprise")
    st.caption("Ces informations sont pré-remplies et non modifiables.")
    c1, c2 = st.columns(2)
    c1.text_input("Nom de l'entreprise", value=ENTREPRISE_FIXE["ent_nom"], disabled=True)
    c2.text_input("Adresse", value=ENTREPRISE_FIXE["ent_adresse"], disabled=True)
    c1.text_input("Téléphone", value=ENTREPRISE_FIXE["ent_tel"], disabled=True)
    c2.text_input("Email", value=ENTREPRISE_FIXE["ent_email"], disabled=True)
    c1.text_input("Responsable technique / Chef de chantier", value=ENTREPRISE_FIXE["ent_resp"], disabled=True)
    c2.text_input("Téléphone responsable", value=ENTREPRISE_FIXE["ent_tel_resp"], disabled=True)
    c1.text_input("Email responsable", value=ENTREPRISE_FIXE["ent_email_resp"], disabled=True)

    st.divider()
    st.subheader("Informations projet")
    c1, c2 = st.columns(2)
    c1.text_input("Intitulé du chantier", key="proj_intitule", value=g("proj_intitule"))
    c2.text_input("Client / Maître d'ouvrage", key="proj_client", value=g("proj_client"))
    c1.text_input("Situation des travaux (adresse)", key="proj_situation", value=g("proj_situation"))
    c2.text_input("Type d'ouvrage", key="proj_type", value=g("proj_type"))
    st.text_area("Description des travaux", height=80, key="proj_description", value=g("proj_description"))
    c1, c2, c3 = st.columns(3)
    c1.text_input("Date de début", key="proj_debut", value=g("proj_debut"))
    c2.text_input("Durée d'intervention", key="proj_duree", value=g("proj_duree"))
    c3.text_input("Effectif moyen propre", key="proj_effectif", value=g("proj_effectif"))
    c1, c2 = st.columns(2)
    c1.checkbox("Avis d'ouverture de chantier déposé", key="proj_avis", value=g("proj_avis", False))
    c2.text_input("Date de création du document", key="proj_date_creation", value=g("proj_date_creation"))

    st.divider()
    st.subheader("Accès au site")
    st.text_area("Description de l'accès", height=60, key="acces_site", value=g("acces_site"))

    nav_buttons(tab)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Gestion & Diffusion
# ════════════════════════════════════════════════════════════════════════════
elif tab == 1:
    st.subheader("Circuit de validation")
    c1, c2, c3 = st.columns(3)
    c1.text_input("Élaboration", key="gest_elab", value=g("gest_elab"))
    c2.text_input("Vérification", key="gest_verif", value=g("gest_verif"))
    c3.text_input("Approbation", key="gest_appro", value=g("gest_appro"))

    st.subheader("Suivi des révisions")
    nb_rev = st.number_input("Nombre de révisions", min_value=1, max_value=10,
                             value=int(g("nb_rev", 1)), key="nb_rev")
    for i in range(int(nb_rev)):
        r1, r2, r3 = st.columns([1, 2, 4])
        r1.text_input(f"Indice #{i+1}", key=f"rev_ind_{i}", value=g(f"rev_ind_{i}", "A" if i==0 else ""))
        r2.text_input(f"Date #{i+1}", key=f"rev_date_{i}", value=g(f"rev_date_{i}"))
        r3.text_input(f"Nature #{i+1}", key=f"rev_nat_{i}", value=g(f"rev_nat_{i}", "Création du document" if i==0 else ""))

    st.subheader("Diffusion")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**Intervenants externes**")
        st.checkbox("Maître d'ouvrage", key="diff_moa", value=g("diff_moa", True))
        st.checkbox("Maître d'œuvre", key="diff_moe", value=g("diff_moe", True))
        st.checkbox("Entreprise mandataire", key="diff_mand", value=g("diff_mand", False))
        st.checkbox("Entreprise cotraitante", key="diff_cotrait", value=g("diff_cotrait", False))
        st.checkbox("Sous-traitant", key="diff_st", value=g("diff_st", False))
        st.checkbox("Coordinateur SPS", key="diff_csps", value=g("diff_csps", True))
    with dc2:
        st.markdown("**Intervenants internes**")
        st.checkbox("Service QSE", key="diff_qse", value=g("diff_qse", True))
        st.checkbox("Directeur travaux", key="diff_dir", value=g("diff_dir", True))
        st.checkbox("Conducteur de travaux", key="diff_conducteur", value=g("diff_conducteur", False))
        st.checkbox("Chef de chantier", key="diff_chef", value=g("diff_chef", True))

    nav_buttons(tab)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Intervenants
# ════════════════════════════════════════════════════════════════════════════
elif tab == 2:
    def intervenant_form(titre, kp):
        st.markdown(f"**{titre}**")
        c1, c2 = st.columns(2)
        c1.text_input("Nom / Raison sociale", key=f"{kp}_nom", value=g(f"{kp}_nom"))
        c2.text_input("Adresse", key=f"{kp}_adr", value=g(f"{kp}_adr"))
        c1.text_input("Interlocuteur référent", key=f"{kp}_int", value=g(f"{kp}_int"))
        c1.text_input("Téléphone", key=f"{kp}_tel", value=g(f"{kp}_tel"))
        c2.text_input("Email", key=f"{kp}_em", value=g(f"{kp}_em"))

    def intervenant_fixe(titre, kp):
        """Affiche un intervenant figé (non modifiable) depuis PREVENTION_FIXE.
        Pas de `key` sur les clés _STATIC_KEYS : on utilise des clés `_fixe_*`
        pour ne pas perturber le snapshot, et on n'affiche que les champs renseignés."""
        st.markdown(f"**{titre}**")
        c1, c2 = st.columns(2)
        c1.text_input("Nom / Raison sociale", value=g(f"{kp}_nom"),
                      disabled=True, key=f"_fixe_{kp}_nom")
        c2.text_input("Adresse", value=g(f"{kp}_adr"),
                      disabled=True, key=f"_fixe_{kp}_adr")
        if g(f"{kp}_int"):
            c1.text_input("Interlocuteur référent", value=g(f"{kp}_int"),
                          disabled=True, key=f"_fixe_{kp}_int")
        if g(f"{kp}_tel"):
            c1.text_input("Téléphone", value=g(f"{kp}_tel"),
                          disabled=True, key=f"_fixe_{kp}_tel")
        if g(f"{kp}_em"):
            c2.text_input("Email", value=g(f"{kp}_em"),
                          disabled=True, key=f"_fixe_{kp}_em")

    st.subheader("Intervenants du marché")
    intervenant_form("Maître d'ouvrage", "moa")
    st.divider()
    intervenant_form("Maîtrise d'œuvre (MOE)", "moe")

    st.divider()
    st.subheader("Intervenants de la prévention")
    intervenant_form("Coordinateur SPS", "csps")
    st.divider()
    st.caption("Inspection du travail et médecine du travail : pré-remplies et non modifiables.")
    intervenant_fixe("Inspection du travail", "it")
    st.divider()
    intervenant_fixe("Médecine du travail", "med")

    nav_buttons(tab)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Organisation & Installation
# ════════════════════════════════════════════════════════════════════════════
elif tab == 3:
    st.subheader("Organisation de l'équipe")
    nb_membres = st.number_input("Nombre de membres", min_value=1, max_value=20,
                                 value=int(g("nb_membres", 2)), key="nb_membres")
    for i in range(int(nb_membres)):
        c1, c2 = st.columns(2)
        c1.text_input(f"Rôle #{i+1}", key=f"role_{i}", value=g(f"role_{i}"))
        c2.text_input(f"Nom / Prénom #{i+1}", key=f"membre_{i}", value=g(f"membre_{i}"))

    st.divider()
    st.subheader("Installation de chantier")
    st.checkbox("Installations à la charge de l'entreprise", key="inst_charge", value=g("inst_charge", False))
    ic1, ic2, ic3, ic4 = st.columns(4)
    ic1.checkbox("Bungalow", key="inst_bungalow", value=g("inst_bungalow", False))
    ic2.checkbox("Remorque VRS", key="inst_remorque", value=g("inst_remorque", False))
    ic3.checkbox("Locaux existants", key="inst_locaux", value=g("inst_locaux", False))
    ic4.checkbox("Autre", key="inst_autre", value=g("inst_autre", False))

    def local_form(lbl, key):
        st.markdown(f"*{lbl}*")
        c1, c2, c3 = st.columns([1, 1, 3])
        c1.text_input("Nombre", key=f"{key}_nb", value=g(f"{key}_nb"))
        c2.text_input("Surface", key=f"{key}_surf", value=g(f"{key}_surf"))
        c3.text_input("Commentaires", key=f"{key}_com", value=g(f"{key}_com"))

    local_form("Vestiaires", "vest")
    local_form("Réfectoire", "ref")
    local_form("Sanitaires", "san")

    _EAU_OPTS = ["Raccordement réseau", "Bouteilles"]
    _REPAS_OPTS = ["Sur le chantier", "À l'extérieur"]
    _eau_saved = g("eau", "Raccordement réseau")
    _repas_saved = g("repas", "Sur le chantier")

    e1, e2, e3 = st.columns(3)
    e1.checkbox("Réseau électrique", key="en_elec", value=g("en_elec", True))
    e2.checkbox("Groupe électrogène", key="en_group", value=g("en_group", False))
    e3.checkbox("Chauffage auxiliaire gaz", key="en_gaz", value=g("en_gaz", False))
    st.radio("Eau potable", _EAU_OPTS, index=_EAU_OPTS.index(_eau_saved) if _eau_saved in _EAU_OPTS else 0, key="eau", horizontal=True)
    st.radio("Repas", _REPAS_OPTS, index=_REPAS_OPTS.index(_repas_saved) if _repas_saved in _REPAS_OPTS else 0, key="repas", horizontal=True)
    st.text_input("Date de mise en service des installations", key="date_inst", value=g("date_inst"))

    nav_buttons(tab)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Secours & Prévention
# ════════════════════════════════════════════════════════════════════════════
elif tab == 4:
    st.subheader("Organisation des secours")
    c1, c2 = st.columns(2)
    c1.text_input("Téléphone urgence chantier", key="sec_tel", value=g("sec_tel"))
    c2.text_input("Nom du chantier", key="sec_nom", value=g("sec_nom"))
    c1.text_input("Numéro de chantier", key="sec_num", value=g("sec_num"))
    c2.text_input("Adresse / Localisation", key="sec_adresse", value=g("sec_adresse"))
    c1.text_input("Nom(s) du/des SST", key="sec_sst", value=g("sec_sst"))
    c2.text_input("Défibrillateur (emplacement)", key="sec_defib", value=g("sec_defib"))

    st.divider()
    st.subheader("EPI obligatoires")
    st.text_area("Un EPI par ligne", height=120, key="epi_text",
                 value=g("epi_text", "Casque de chantier\nGilet haute visibilité\nChaussures ou bottes de sécurité"))

    st.divider()
    st.subheader("Consignes de sécurité")
    st.text_area("Une consigne par ligne", height=100, key="consignes_text",
                 value=g("consignes_text", "Port des EPI obligatoire\nArrêt des moteurs si possible\nInterdiction de fumer"))

    st.divider()
    st.subheader("Propreté et cheminement")
    st.text_area("Une règle par ligne", height=130, key="proprete_text",
                 value=g("proprete_text",
                         "Nettoyer régulièrement les postes de travail\n"
                         "Utiliser les zones de stockage prévues\n"
                         "Maintenir le cantonnement propre en permanence\n"
                         "Effectuer un nettoyage quotidien du chantier\n"
                         "Mettre à disposition des poubelles pour le tri des déchets\n"
                         "Désencombrer les voies de circulation"))

    st.divider()
    st.subheader("Émargement — membres pré-remplis (optionnel)")
    nb_sign = st.number_input("Nombre de signataires", 0, 20,
                              value=int(g("nb_sign", 0)), key="nb_sign")
    for i in range(int(nb_sign)):
        s1, s2 = st.columns(2)
        s1.text_input(f"Nom #{i+1}", key=f"sign_nom_{i}", value=g(f"sign_nom_{i}"))
        s2.text_input(f"Entreprise #{i+1}", key=f"sign_ent_{i}", value=g(f"sign_ent_{i}"))

    nav_buttons(tab)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Analyse des risques
# ════════════════════════════════════════════════════════════════════════════
elif tab == 5:
    st.subheader("Phases de travail et risques")
    st.caption("Ajoutez autant de phases que nécessaire.")

    DANGER_OPTS = [
        "1 – Faible (blessure légère, sans arrêt)",
        "10 – Moyen (arrêt de travail)",
        "100 – Grave (incapacité permanente)",
        "1000 – Très grave (danger de mort)",
    ]
    EXPO_OPTS = [
        "1 – Très improbable", "2 – Improbable",
        "3 – Probable", "4 – Très probable",
    ]
    DANGER_MAP = {o: int(o.split(" ")[0].replace("–","").strip()) for o in DANGER_OPTS}
    EXPO_MAP = {o: int(o.split(" ")[0].replace("–","").strip()) for o in EXPO_OPTS}

    col_add, col_rem, _ = st.columns([1, 1, 4])
    if col_add.button("＋ Ajouter une phase", key="add_phase"):
        st.session_state.nb_risques += 1
    if col_rem.button("－ Supprimer la dernière", key="rem_phase") and st.session_state.nb_risques > 1:
        st.session_state.nb_risques -= 1

    for i in range(st.session_state.nb_risques):
        with st.expander(f"Phase {i+1}", expanded=(i < 3)):
            r1, r2 = st.columns(2)
            r1.text_input("Phase de travail", key=f"r_phase_{i}", value=g(f"r_phase_{i}"))
            r2.text_input("Facteur de risque", key=f"r_facteur_{i}", value=g(f"r_facteur_{i}"))
            r3, r4 = st.columns(2)
            r3.text_input("Situation à risque", key=f"r_sit_{i}", value=g(f"r_sit_{i}"))
            r4.text_input("Risques identifiés", key=f"r_risque_{i}", value=g(f"r_risque_{i}"))
            r5, r6 = st.columns(2)
            _dang_saved = g(f"r_dang_{i}", DANGER_OPTS[0])
            _expo_saved = g(f"r_expo_{i}", EXPO_OPTS[0])
            r5.selectbox("Dangerosité", DANGER_OPTS, key=f"r_dang_{i}",
                         index=DANGER_OPTS.index(_dang_saved) if _dang_saved in DANGER_OPTS else 0)
            r6.selectbox("Exposition", EXPO_OPTS, key=f"r_expo_{i}",
                         index=EXPO_OPTS.index(_expo_saved) if _expo_saved in EXPO_OPTS else 0)
            st.text_area("Mesures de prévention", key=f"r_mes_{i}", height=60,
                         value=g(f"r_mes_{i}"))

    nav_buttons(tab)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Annexes
# ════════════════════════════════════════════════════════════════════════════
elif tab == 6:
    st.subheader("Annexes")
    st.caption("Ajoutez des documents PDF à joindre à la suite du PPSPS (plans, PIC, fiches prévention…).")

    with st.form("form_annexe", clear_on_submit=True):
        fa1, fa2 = st.columns([2, 3])
        titre_annexe = fa1.text_input("Titre de l'annexe",
                                      placeholder="ex : Plan d'Installation de Chantier")
        fichier_annexe = fa2.file_uploader("Fichier PDF", type=["pdf"],
                                           label_visibility="collapsed")
        if st.form_submit_button("＋ Ajouter cette annexe", type="primary"):
            if fichier_annexe is None:
                st.warning("Sélectionnez un fichier PDF.")
            else:
                st.session_state.annexes.append({
                    "titre": titre_annexe or fichier_annexe.name,
                    "data": fichier_annexe.read(),
                })
                st.success(f"Annexe « {titre_annexe or fichier_annexe.name} » ajoutée.")

    if st.session_state.annexes:
        st.markdown(f"**{len(st.session_state.annexes)} annexe(s) enregistrée(s) :**")
        for idx, ann in enumerate(st.session_state.annexes):
            col_t, col_s, col_del = st.columns([5, 2, 1])
            col_t.markdown(f"📎 **{ann['titre']}**")
            col_s.caption(f"{len(ann['data']) // 1024} Ko")
            if col_del.button("🗑", key=f"del_ann_{idx}", help="Supprimer"):
                st.session_state.annexes.pop(idx)
                st.rerun()
    else:
        st.info("Aucune annexe pour l'instant.")

    nav_buttons(tab)

# ════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Générer le PDF
# ════════════════════════════════════════════════════════════════════════════
elif tab == 7:
    st.subheader("Générer le PPSPS")
    st.info("Vérifiez vos informations dans les onglets précédents, puis cliquez sur le bouton.")

    ss = st.session_state

    with st.expander("Récapitulatif rapide", expanded=False):
        st.markdown(f"**Entreprise :** {g('ent_nom') or '—'}")
        st.markdown(f"**Chantier :** {g('proj_intitule') or '—'} — {g('proj_client') or '—'}")
        st.markdown(f"**Phases de risque :** {ss.nb_risques}")
        st.markdown(f"**Annexes :** {len(ss.annexes)}")

    if st.button("📄 Générer le PDF", type="primary", use_container_width=True):
        nb_rev = int(g("nb_rev", 1))
        nb_membres = int(g("nb_membres", 2))
        nb_sign = int(g("nb_sign", 0))

        suivis = [{"indice": g(f"rev_ind_{i}", "A" if i==0 else ""),
                   "date": g(f"rev_date_{i}"),
                   "nature": g(f"rev_nat_{i}", "Création du document" if i==0 else "")}
                  for i in range(nb_rev)]

        membres = [{"role": g(f"role_{i}"), "nom": g(f"membre_{i}")}
                   for i in range(nb_membres)]

        signataires = [{"nom": g(f"sign_nom_{i}"), "entreprise": g(f"sign_ent_{i}")}
                       for i in range(nb_sign)]

        DANGER_MAP = {
            "1 – Faible (blessure légère, sans arrêt)": 1,
            "10 – Moyen (arrêt de travail)": 10,
            "100 – Grave (incapacité permanente)": 100,
            "1000 – Très grave (danger de mort)": 1000,
        }
        EXPO_MAP = {
            "1 – Très improbable": 1, "2 – Improbable": 2,
            "3 – Probable": 3, "4 – Très probable": 4,
        }
        DANGER_DEF = "1 – Faible (blessure légère, sans arrêt)"
        EXPO_DEF = "1 – Très improbable"

        risques = []
        for i in range(ss.nb_risques):
            phase = g(f"r_phase_{i}")
            sit = g(f"r_sit_{i}")
            if phase or sit:
                risques.append({
                    "phase": phase,
                    "facteur_risque":g(f"r_facteur_{i}"),
                    "situation": sit,
                    "risques": g(f"r_risque_{i}"),
                    "dangerosite": DANGER_MAP.get(g(f"r_dang_{i}", DANGER_DEF), 1),
                    "exposition": EXPO_MAP.get(g(f"r_expo_{i}", EXPO_DEF), 1),
                    "mesures": g(f"r_mes_{i}"),
                })

        inst_types = []
        if g("inst_bungalow", False): inst_types.append("bungalow")
        if g("inst_remorque", False): inst_types.append("remorque")
        if g("inst_locaux", False): inst_types.append("locaux_existants")
        if g("inst_autre", False): inst_types.append("autre")

        energies = []
        if g("en_elec", True): energies.append("reseau_elec")
        if g("en_group", False): energies.append("groupe")
        if g("en_gaz", False): energies.append("chauffage_gaz")

        def get_interv(kp):
            return {"nom": g(f"{kp}_nom"),
                    "adresse": g(f"{kp}_adr"),
                    "interlocuteur": g(f"{kp}_int"),
                    "telephone": g(f"{kp}_tel"),
                    "email": g(f"{kp}_em")}

        data = {
            "entreprise": {
                "nom": g("ent_nom"),
                "adresse": g("ent_adresse"),
                "telephone": g("ent_tel"),
                "email": g("ent_email"),
                "responsable_technique": g("ent_resp"),
                "tel_responsable": g("ent_tel_resp"),
                "email_responsable": g("ent_email_resp"),
            },
            "projet": {
                "intitule": g("proj_intitule"),
                "client": g("proj_client"),
                "situation": g("proj_situation"),
                "type_ouvrage": g("proj_type"),
                "description": g("proj_description"),
                "date_debut": g("proj_debut"),
                "duree": g("proj_duree"),
                "effectif_moyen": g("proj_effectif"),
                "avis_ouverture": g("proj_avis", False),
                "date_creation": g("proj_date_creation"),
            },
            "acces_site": g("acces_site"),
            "gestion": {
                "elaboration": g("gest_elab"),
                "verification": g("gest_verif"),
                "approbation": g("gest_appro"),
                "suivis": suivis,
                "diffusion": {
                    "externes": {
                        "moa": g("diff_moa", True),
                        "moe": g("diff_moe", True),
                        "mandataire": g("diff_mand", False),
                        "cotraitant": g("diff_cotrait", False),
                        "sous_traitant": g("diff_st", False),
                        "csps": g("diff_csps", True),
                    },
                    "internes": {
                        "qse": g("diff_qse", True),
                        "dir_travaux": g("diff_dir", True),
                        "conducteur": g("diff_conducteur", False),
                        "chef_chantier":g("diff_chef", True),
                    },
                },
            },
            "intervenants": {
                "moa": get_interv("moa"),
                "moe": get_interv("moe"),
                "csps": get_interv("csps"),
                "inspection_travail": get_interv("it"),
                "medecine_travail": get_interv("med"),
            },
            "organisation": {"membres": membres},
            "installation": {
                "a_charge_entreprise": g("inst_charge", False),
                "types": inst_types,
                "vestiaire": {"nombre": g("vest_nb"), "surface": g("vest_surf"), "commentaires": g("vest_com")},
                "refectoire": {"nombre": g("ref_nb"), "surface": g("ref_surf"), "commentaires": g("ref_com")},
                "sanitaire": {"nombre": g("san_nb"), "surface": g("san_surf"), "commentaires": g("san_com")},
                "repas_sur_chantier": g("repas", "Sur le chantier") == "Sur le chantier",
                "energies": energies,
                "eau_potable": "reseau" if g("eau", "Raccordement réseau") == "Raccordement réseau" else "bouteilles",
                "date_mise_en_service": g("date_inst"),
            },
            "secours": {
                "telephone_urgence": g("sec_tel"),
                "chantier_nom": g("sec_nom"),
                "chantier_numero": g("sec_num"),
                "chantier_adresse": g("sec_adresse"),
                "sst_noms": g("sec_sst"),
                "defibrillateur": g("sec_defib"),
            },
            "prevention": {
                "epi": [e.strip() for e in g("epi_text").split("\n") if e.strip()],
                "consignes": [c.strip() for c in g("consignes_text").split("\n") if c.strip()],
                "proprete": [p.strip() for p in g("proprete_text").split("\n") if p.strip()],
            },
            "risques": risques,
            "signataires": signataires,
        }

        with st.spinner("Génération en cours..."):
            try:
                main_pdf = generer_ppsps(data)
                if ss.annexes:
                    writer = PdfWriter()
                    for page in PdfReader(main_pdf).pages:
                        writer.add_page(page)
                    for ann in ss.annexes:
                        try:
                            for page in PdfReader(io.BytesIO(ann["data"])).pages:
                                writer.add_page(page)
                        except Exception as ex:
                            st.warning(f"Annexe « {ann['titre']} » ignorée : {ex}")
                    final_buf = io.BytesIO()
                    writer.write(final_buf)
                    final_buf.seek(0)
                else:
                    final_buf = main_pdf

                intitule = g("proj_intitule", "document")
                nom_fichier = f"PPSPS_{intitule.replace(' ','_')}.pdf"

                st.success(f"✅ PDF généré avec succès ! ({len(ss.annexes)} annexe(s) incluse(s))")
                st.download_button(
                    label="⬇️ Télécharger le PPSPS",
                    data=final_buf,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")
                raise

    nav_buttons(tab)
