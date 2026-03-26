"""
app.py — Interface Streamlit pour la génération du PPSPS.
Navigation par boutons Précédent / Suivant (session state).
"""

import io
import streamlit as st
from pypdf import PdfReader, PdfWriter
from ppsps_generator import generer_ppsps

st.set_page_config(page_title="Générateur PPSPS", page_icon="🏗️", layout="wide")

# ── Constantes de navigation ───────────────────────────────────────────────
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

# ── Init session state ─────────────────────────────────────────────────────
if "tab" not in st.session_state:
    st.session_state.tab = 0
if "nb_risques" not in st.session_state:
    st.session_state.nb_risques = 3
if "annexes" not in st.session_state:
    st.session_state.annexes = []   # list of {"titre": str, "file": UploadedFile}

# ── Helpers navigation ─────────────────────────────────────────────────────
def go_to(n):
    st.session_state.tab = n

def nav_buttons(current):
    """Barre précédent / suivant en bas de section."""
    st.write("")
    left, _, right = st.columns([1, 6, 1])
    if current > 0:
        left.button("← Précédent", key=f"prev_{current}",
                    on_click=go_to, args=(current - 1,), use_container_width=True)
    if current < N_TABS - 1:
        right.button("Suivant →", key=f"next_{current}",
                     on_click=go_to, args=(current + 1,), use_container_width=True,
                     type="primary")

# ── En-tête + barre de navigation ─────────────────────────────────────────
st.title("🏗️ Générateur PPSPS")

# Barre de tabs cliquables
cols = st.columns(N_TABS)
for i, (col, name) in enumerate(zip(cols, TAB_NAMES)):
    btn_type = "primary" if i == st.session_state.tab else "secondary"
    col.button(name, key=f"nav_{i}", use_container_width=True,
               type=btn_type, on_click=go_to, args=(i,))

st.divider()
tab = st.session_state.tab


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Entreprise & Projet
# ════════════════════════════════════════════════════════════════════════════
if tab == 0:
    st.subheader("Votre entreprise")
    c1, c2 = st.columns(2)
    c1.text_input("Nom de l'entreprise",                       key="ent_nom")
    c2.text_input("Adresse",                                    key="ent_adresse")
    c1.text_input("Téléphone",                                  key="ent_tel")
    c2.text_input("Email",                                      key="ent_email")
    c1.text_input("Responsable technique / Chef de chantier",   key="ent_resp")
    c2.text_input("Téléphone responsable",                      key="ent_tel_resp")
    c1.text_input("Email responsable",                          key="ent_email_resp")

    st.divider()
    st.subheader("Informations projet")
    c1, c2 = st.columns(2)
    c1.text_input("Intitulé du chantier",           key="proj_intitule")
    c2.text_input("Client / Maître d'ouvrage",      key="proj_client")
    c1.text_input("Situation des travaux (adresse)", key="proj_situation")
    c2.text_input("Type d'ouvrage",                 key="proj_type")
    st.text_area("Description des travaux", height=80, key="proj_description")
    c1, c2, c3 = st.columns(3)
    c1.text_input("Date de début",          key="proj_debut")
    c2.text_input("Durée d'intervention",   key="proj_duree")
    c3.text_input("Effectif moyen propre",  key="proj_effectif")
    c1, c2 = st.columns(2)
    c1.checkbox("Avis d'ouverture de chantier déposé", key="proj_avis")
    c2.text_input("Date de création du document",      key="proj_date_creation")

    st.divider()
    st.subheader("Accès au site")
    st.text_area("Description de l'accès", height=60, key="acces_site")

    nav_buttons(tab)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Gestion & Diffusion
# ════════════════════════════════════════════════════════════════════════════
elif tab == 1:
    st.subheader("Circuit de validation")
    c1, c2, c3 = st.columns(3)
    c1.text_input("Élaboration",  key="gest_elab")
    c2.text_input("Vérification", key="gest_verif")
    c3.text_input("Approbation",  key="gest_appro")

    st.subheader("Suivi des révisions")
    nb_rev = st.number_input("Nombre de révisions", min_value=1, max_value=10, value=1, key="nb_rev")
    for i in range(int(nb_rev)):
        r1, r2, r3 = st.columns([1, 2, 4])
        r1.text_input(f"Indice #{i+1}",  value="A" if i == 0 else "", key=f"rev_ind_{i}")
        r2.text_input(f"Date #{i+1}",                                  key=f"rev_date_{i}")
        r3.text_input(f"Nature #{i+1}",
                      value="Création du document" if i == 0 else "",  key=f"rev_nat_{i}")

    st.subheader("Diffusion")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**Intervenants externes**")
        st.checkbox("Maître d'ouvrage",        value=True, key="diff_moa")
        st.checkbox("Maître d'œuvre",           value=True, key="diff_moe")
        st.checkbox("Entreprise mandataire",               key="diff_mand")
        st.checkbox("Entreprise cotraitante",              key="diff_cotrait")
        st.checkbox("Sous-traitant",                       key="diff_st")
        st.checkbox("Coordinateur SPS",         value=True, key="diff_csps")
    with dc2:
        st.markdown("**Intervenants internes**")
        st.checkbox("Service QSE",              value=True, key="diff_qse")
        st.checkbox("Directeur travaux",        value=True, key="diff_dir")
        st.checkbox("Conducteur de travaux",               key="diff_conducteur")
        st.checkbox("Chef de chantier",         value=True, key="diff_chef")

    nav_buttons(tab)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Intervenants
# ════════════════════════════════════════════════════════════════════════════
elif tab == 2:
    def intervenant_form(titre, kp):
        st.markdown(f"**{titre}**")
        c1, c2 = st.columns(2)
        c1.text_input("Nom / Raison sociale",    key=f"{kp}_nom")
        c2.text_input("Adresse",                 key=f"{kp}_adr")
        c1.text_input("Interlocuteur référent",  key=f"{kp}_int")
        c1.text_input("Téléphone",               key=f"{kp}_tel")
        c2.text_input("Email",                   key=f"{kp}_em")

    st.subheader("Intervenants du marché")
    intervenant_form("Maître d'ouvrage", "moa")
    st.divider()
    intervenant_form("Maîtrise d'œuvre (MOE)", "moe")
    st.divider()
    st.subheader("Intervenants de la prévention")
    intervenant_form("Coordinateur SPS", "csps")
    st.divider()
    intervenant_form("Inspection du travail", "it")
    st.divider()
    intervenant_form("Médecine du travail", "med")

    nav_buttons(tab)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Organisation & Installation
# ════════════════════════════════════════════════════════════════════════════
elif tab == 3:
    st.subheader("Organisation de l'équipe")
    nb_membres = st.number_input("Nombre de membres", min_value=1, max_value=20, value=2, key="nb_membres")
    for i in range(int(nb_membres)):
        c1, c2 = st.columns(2)
        c1.text_input(f"Rôle #{i+1}",         key=f"role_{i}")
        c2.text_input(f"Nom / Prénom #{i+1}",  key=f"membre_{i}")

    st.divider()
    st.subheader("Installation de chantier")
    st.checkbox("Installations à la charge de l'entreprise", key="inst_charge")
    ic1, ic2, ic3, ic4 = st.columns(4)
    ic1.checkbox("Bungalow",         key="inst_bungalow")
    ic2.checkbox("Remorque VRS",     key="inst_remorque")
    ic3.checkbox("Locaux existants", key="inst_locaux")
    ic4.checkbox("Autre",            key="inst_autre")

    def local_form(lbl, key):
        st.markdown(f"*{lbl}*")
        c1, c2, c3 = st.columns([1, 1, 3])
        c1.text_input("Nombre",        key=f"{key}_nb")
        c2.text_input("Surface",       key=f"{key}_surf")
        c3.text_input("Commentaires",  key=f"{key}_com")

    local_form("Vestiaires", "vest")
    local_form("Réfectoire",  "ref")
    local_form("Sanitaires",  "san")

    e1, e2, e3 = st.columns(3)
    e1.checkbox("Réseau électrique",       value=True, key="en_elec")
    e2.checkbox("Groupe électrogène",                  key="en_group")
    e3.checkbox("Chauffage auxiliaire gaz",             key="en_gaz")
    st.radio("Eau potable", ["Raccordement réseau", "Bouteilles"], horizontal=True, key="eau")
    st.radio("Repas", ["Sur le chantier", "À l'extérieur"], horizontal=True, key="repas")
    st.text_input("Date de mise en service des installations", key="date_inst")

    nav_buttons(tab)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Secours & Prévention
# ════════════════════════════════════════════════════════════════════════════
elif tab == 4:
    st.subheader("Organisation des secours")
    c1, c2 = st.columns(2)
    c1.text_input("Téléphone urgence chantier",  key="sec_tel")
    c2.text_input("Nom du chantier",             key="sec_nom")
    c1.text_input("Numéro de chantier",          key="sec_num")
    c2.text_input("Adresse / Localisation",      key="sec_adresse")
    c1.text_input("Nom(s) du/des SST",           key="sec_sst")
    c2.text_input("Défibrillateur (emplacement)",key="sec_defib")

    st.divider()
    st.subheader("EPI obligatoires")
    st.text_area("Un EPI par ligne",
        value="Casque de chantier\nGilet haute visibilité\nChaussures ou bottes de sécurité",
        height=120, key="epi_text")

    st.divider()
    st.subheader("Consignes de sécurité")
    st.text_area("Une consigne par ligne",
        value="Port des EPI obligatoire\nArrêt des moteurs si possible\nInterdiction de fumer",
        height=100, key="consignes_text")

    st.divider()
    st.subheader("Propreté et cheminement")
    st.text_area("Une règle par ligne",
        value=("Nettoyer régulièrement les postes de travail\n"
               "Utiliser les zones de stockage prévues\n"
               "Maintenir le cantonnement propre en permanence\n"
               "Effectuer un nettoyage quotidien du chantier\n"
               "Mettre à disposition des poubelles pour le tri des déchets\n"
               "Désencombrer les voies de circulation"),
        height=130, key="proprete_text")

    st.divider()
    st.subheader("Émargement — membres pré-remplis (optionnel)")
    nb_sign = st.number_input("Nombre de signataires", 0, 20, 0, key="nb_sign")
    for i in range(int(nb_sign)):
        s1, s2 = st.columns(2)
        s1.text_input(f"Nom #{i+1}",        key=f"sign_nom_{i}")
        s2.text_input(f"Entreprise #{i+1}", key=f"sign_ent_{i}")

    nav_buttons(tab)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Analyse des risques
# ════════════════════════════════════════════════════════════════════════════
elif tab == 5:
    st.subheader("Phases de travail et risques")
    st.caption("Ajoutez autant de lignes que nécessaire — le tableau s'adapte automatiquement.")

    DANGER_OPTIONS = {
        "1 – Faible (blessure légère, sans arrêt)": 1,
        "10 – Moyen (arrêt de travail)": 10,
        "100 – Grave (incapacité permanente)": 100,
        "1000 – Très grave (danger de mort)": 1000,
    }
    EXPO_OPTIONS = {
        "1 – Très improbable": 1, "2 – Improbable": 2,
        "3 – Probable": 3, "4 – Très probable": 4,
    }

    col_add, col_rem, _ = st.columns([1, 1, 4])
    if col_add.button("＋ Ajouter une phase", key="add_phase"):
        st.session_state.nb_risques += 1
    if col_rem.button("－ Supprimer la dernière", key="rem_phase") and st.session_state.nb_risques > 1:
        st.session_state.nb_risques -= 1

    for i in range(st.session_state.nb_risques):
        with st.expander(f"Phase {i+1}", expanded=(i < 3)):
            r1, r2 = st.columns(2)
            r1.text_input("Phase de travail",   key=f"r_phase_{i}")
            r2.text_input("Facteur de risque",  key=f"r_facteur_{i}")
            r3, r4 = st.columns(2)
            r3.text_input("Situation à risque", key=f"r_sit_{i}")
            r4.text_input("Risques identifiés", key=f"r_risque_{i}")
            r5, r6 = st.columns(2)
            r5.selectbox("Dangerosité", list(DANGER_OPTIONS.keys()), key=f"r_dang_{i}")
            r6.selectbox("Exposition",  list(EXPO_OPTIONS.keys()),   key=f"r_expo_{i}")
            st.text_area("Mesures de prévention", key=f"r_mes_{i}", height=60)

    nav_buttons(tab)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Annexes
# ════════════════════════════════════════════════════════════════════════════
elif tab == 6:
    st.subheader("Annexes")
    st.caption("Ajoutez des documents PDF à joindre à la suite du PPSPS (plans, PIC, fiches prévention…).")

    # Ajouter une annexe
    with st.form("form_annexe", clear_on_submit=True):
        fa1, fa2 = st.columns([2, 3])
        titre_annexe = fa1.text_input("Titre de l'annexe",
                                      placeholder="ex : Plan d'Installation de Chantier")
        fichier_annexe = fa2.file_uploader("Fichier PDF", type=["pdf"], label_visibility="collapsed")
        submitted = st.form_submit_button("＋ Ajouter cette annexe", type="primary")
        if submitted:
            if fichier_annexe is None:
                st.warning("Sélectionnez un fichier PDF.")
            else:
                st.session_state.annexes.append({
                    "titre": titre_annexe or fichier_annexe.name,
                    "data": fichier_annexe.read(),
                })
                st.success(f"Annexe « {titre_annexe or fichier_annexe.name} » ajoutée.")

    # Liste des annexes
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

    # Résumé rapide
    ss = st.session_state
    with st.expander("Récapitulatif rapide", expanded=False):
        st.markdown(f"**Entreprise :** {ss.get('ent_nom','—')}")
        st.markdown(f"**Chantier :** {ss.get('proj_intitule','—')} — {ss.get('proj_client','—')}")
        st.markdown(f"**Phases de risque :** {ss.nb_risques}")
        st.markdown(f"**Annexes :** {len(ss.annexes)}")

    if st.button("📄 Générer le PDF", type="primary", use_container_width=True):
        ss = st.session_state

        # Reconstruction des listes
        nb_rev = int(ss.get("nb_rev", 1))
        suivis = [{"indice": ss.get(f"rev_ind_{i}",""),
                   "date":   ss.get(f"rev_date_{i}",""),
                   "nature": ss.get(f"rev_nat_{i}","")}
                  for i in range(nb_rev)]

        nb_membres = int(ss.get("nb_membres", 2))
        membres = [{"role": ss.get(f"role_{i}",""), "nom": ss.get(f"membre_{i}","")}
                   for i in range(nb_membres)]

        nb_sign = int(ss.get("nb_sign", 0))
        signataires = [{"nom": ss.get(f"sign_nom_{i}",""), "entreprise": ss.get(f"sign_ent_{i}","")}
                       for i in range(nb_sign)]

        DANGER_MAP = {"1 – Faible (blessure légère, sans arrêt)": 1,
                      "10 – Moyen (arrêt de travail)": 10,
                      "100 – Grave (incapacité permanente)": 100,
                      "1000 – Très grave (danger de mort)": 1000}
        EXPO_MAP   = {"1 – Très improbable": 1, "2 – Improbable": 2,
                      "3 – Probable": 3, "4 – Très probable": 4}

        risques = []
        for i in range(ss.nb_risques):
            phase = ss.get(f"r_phase_{i}", "")
            sit   = ss.get(f"r_sit_{i}", "")
            if phase or sit:
                risques.append({
                    "phase":         phase,
                    "facteur_risque":ss.get(f"r_facteur_{i}",""),
                    "situation":     sit,
                    "risques":       ss.get(f"r_risque_{i}",""),
                    "dangerosite":   DANGER_MAP.get(ss.get(f"r_dang_{i}",""), 1),
                    "exposition":    EXPO_MAP.get(ss.get(f"r_expo_{i}",""), 1),
                    "mesures":       ss.get(f"r_mes_{i}",""),
                })

        inst_types = []
        if ss.get("inst_bungalow"): inst_types.append("bungalow")
        if ss.get("inst_remorque"): inst_types.append("remorque")
        if ss.get("inst_locaux"):   inst_types.append("locaux_existants")
        if ss.get("inst_autre"):    inst_types.append("autre")

        energies = []
        if ss.get("en_elec"):  energies.append("reseau_elec")
        if ss.get("en_group"): energies.append("groupe")
        if ss.get("en_gaz"):   energies.append("chauffage_gaz")

        def get_interv(kp):
            return {"nom":          ss.get(f"{kp}_nom",""),
                    "adresse":      ss.get(f"{kp}_adr",""),
                    "interlocuteur":ss.get(f"{kp}_int",""),
                    "telephone":    ss.get(f"{kp}_tel",""),
                    "email":        ss.get(f"{kp}_em","")}

        data = {
            "entreprise": {
                "nom":                  ss.get("ent_nom",""),
                "adresse":              ss.get("ent_adresse",""),
                "telephone":            ss.get("ent_tel",""),
                "email":                ss.get("ent_email",""),
                "responsable_technique":ss.get("ent_resp",""),
                "tel_responsable":      ss.get("ent_tel_resp",""),
                "email_responsable":    ss.get("ent_email_resp",""),
            },
            "projet": {
                "intitule":       ss.get("proj_intitule",""),
                "client":         ss.get("proj_client",""),
                "situation":      ss.get("proj_situation",""),
                "type_ouvrage":   ss.get("proj_type",""),
                "description":    ss.get("proj_description",""),
                "date_debut":     ss.get("proj_debut",""),
                "duree":          ss.get("proj_duree",""),
                "effectif_moyen": ss.get("proj_effectif",""),
                "avis_ouverture": ss.get("proj_avis", False),
                "date_creation":  ss.get("proj_date_creation",""),
            },
            "acces_site": ss.get("acces_site",""),
            "gestion": {
                "elaboration": ss.get("gest_elab",""),
                "verification":ss.get("gest_verif",""),
                "approbation": ss.get("gest_appro",""),
                "suivis": suivis,
                "diffusion": {
                    "externes": {"moa":    ss.get("diff_moa", True),
                                 "moe":    ss.get("diff_moe", True),
                                 "mandataire": ss.get("diff_mand", False),
                                 "cotraitant": ss.get("diff_cotrait", False),
                                 "sous_traitant": ss.get("diff_st", False),
                                 "csps":   ss.get("diff_csps", True)},
                    "internes": {"qse":    ss.get("diff_qse", True),
                                 "dir_travaux": ss.get("diff_dir", True),
                                 "conducteur":  ss.get("diff_conducteur", False),
                                 "chef_chantier": ss.get("diff_chef", True)},
                },
            },
            "intervenants": {
                "moa": get_interv("moa"), "moe": get_interv("moe"),
                "csps": get_interv("csps"), "inspection_travail": get_interv("it"),
                "medecine_travail": get_interv("med"),
            },
            "organisation": {"membres": membres},
            "installation": {
                "a_charge_entreprise": ss.get("inst_charge", False),
                "types": inst_types,
                "vestiaire":  {"nombre": ss.get("vest_nb",""), "surface": ss.get("vest_surf",""), "commentaires": ss.get("vest_com","")},
                "refectoire": {"nombre": ss.get("ref_nb",""),  "surface": ss.get("ref_surf",""),  "commentaires": ss.get("ref_com","")},
                "sanitaire":  {"nombre": ss.get("san_nb",""),  "surface": ss.get("san_surf",""),  "commentaires": ss.get("san_com","")},
                "repas_sur_chantier": ss.get("repas","Sur le chantier") == "Sur le chantier",
                "energies": energies,
                "eau_potable": "reseau" if ss.get("eau","Raccordement réseau") == "Raccordement réseau" else "bouteilles",
                "date_mise_en_service": ss.get("date_inst",""),
            },
            "secours": {
                "telephone_urgence": ss.get("sec_tel",""),
                "chantier_nom":      ss.get("sec_nom",""),
                "chantier_numero":   ss.get("sec_num",""),
                "chantier_adresse":  ss.get("sec_adresse",""),
                "sst_noms":          ss.get("sec_sst",""),
                "defibrillateur":    ss.get("sec_defib",""),
            },
            "prevention": {
                "epi":       [e.strip() for e in ss.get("epi_text","").split("\n") if e.strip()],
                "consignes": [c.strip() for c in ss.get("consignes_text","").split("\n") if c.strip()],
                "proprete":  [p.strip() for p in ss.get("proprete_text","").split("\n") if p.strip()],
            },
            "risques": risques,
            "signataires": signataires,
        }

        with st.spinner("Génération en cours..."):
            try:
                # 1. Générer le PPSPS principal
                main_pdf = generer_ppsps(data)

                # 2. Fusionner les annexes
                if ss.annexes:
                    writer = PdfWriter()
                    for page in PdfReader(main_pdf).pages:
                        writer.add_page(page)
                    for ann in ss.annexes:
                        try:
                            ann_reader = PdfReader(io.BytesIO(ann["data"]))
                            for page in ann_reader.pages:
                                writer.add_page(page)
                        except Exception as ex:
                            st.warning(f"Annexe « {ann['titre']} » ignorée (PDF invalide) : {ex}")
                    final_buf = io.BytesIO()
                    writer.write(final_buf)
                    final_buf.seek(0)
                else:
                    final_buf = main_pdf

                intitule = ss.get("proj_intitule","document")
                nom_fichier = f"PPSPS_{intitule.replace(' ','_')}.pdf"
                st.success(f"✅ PDF généré avec succès !  ({len(ss.annexes)} annexe(s) incluse(s))")
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
