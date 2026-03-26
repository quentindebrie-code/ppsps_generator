"""
app.py — Interface Streamlit pour la génération du PPSPS.
"""

import streamlit as st
from ppsps_generator import generer_ppsps

st.set_page_config(page_title="Générateur PPSPS", page_icon="🏗️", layout="wide")

st.title("🏗️ Générateur PPSPS")
st.caption("Remplissez les informations ci-dessous puis téléchargez votre PPSPS en PDF.")

tabs = st.tabs([
    "1 · Entreprise & Projet",
    "2 · Gestion & Diffusion",
    "3 · Intervenants",
    "4 · Organisation & Installation",
    "5 · Secours & Prévention",
    "6 · Analyse des risques",
    "7 · Générer le PDF",
])

# ── TAB 1 ─────────────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("Votre entreprise")
    c1, c2 = st.columns(2)
    ent_nom        = c1.text_input("Nom de l'entreprise")
    ent_adresse    = c2.text_input("Adresse")
    ent_tel        = c1.text_input("Téléphone")
    ent_email      = c2.text_input("Email")
    ent_resp       = c1.text_input("Responsable technique / Chef de chantier")
    ent_tel_resp   = c2.text_input("Téléphone responsable")
    ent_email_resp = c1.text_input("Email responsable")

    st.divider()
    st.subheader("Informations projet")
    c1, c2 = st.columns(2)
    proj_intitule    = c1.text_input("Intitulé du chantier")
    proj_client      = c2.text_input("Client / Maître d'ouvrage")
    proj_situation   = c1.text_input("Situation des travaux (adresse)")
    proj_type        = c2.text_input("Type d'ouvrage")
    proj_description = st.text_area("Description des travaux", height=80)
    c1, c2, c3 = st.columns(3)
    proj_debut          = c1.text_input("Date de début")
    proj_duree          = c2.text_input("Durée d'intervention")
    proj_effectif       = c3.text_input("Effectif moyen propre")
    c1, c2 = st.columns(2)
    proj_avis           = c1.checkbox("Avis d'ouverture de chantier déposé")
    proj_date_creation  = c2.text_input("Date de création du document")

    st.divider()
    st.subheader("Accès au site")
    acces_site = st.text_area("Description de l'accès", height=60)


# ── TAB 2 ─────────────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Circuit de validation")
    c1, c2, c3 = st.columns(3)
    gest_elab  = c1.text_input("Élaboration")
    gest_verif = c2.text_input("Vérification")
    gest_appro = c3.text_input("Approbation")

    st.subheader("Suivi des révisions")
    nb_rev = st.number_input("Nombre de révisions", min_value=1, max_value=10, value=1)
    suivis = []
    for i in range(int(nb_rev)):
        r1, r2, r3 = st.columns([1, 2, 4])
        ind    = r1.text_input(f"Indice #{i+1}", value="A" if i == 0 else "", key=f"rev_ind_{i}")
        date_r = r2.text_input(f"Date #{i+1}", key=f"rev_date_{i}")
        nature = r3.text_input(f"Nature #{i+1}", value="Création du document" if i == 0 else "", key=f"rev_nat_{i}")
        suivis.append({"indice": ind, "date": date_r, "nature": nature})

    st.subheader("Diffusion")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**Intervenants externes**")
        diff_moa      = st.checkbox("Maître d'ouvrage", value=True, key="d_moa")
        diff_moe      = st.checkbox("Maître d'œuvre", value=True, key="d_moe")
        diff_mand     = st.checkbox("Entreprise mandataire", key="d_mand")
        diff_cotrait  = st.checkbox("Entreprise cotraitante", key="d_cotrait")
        diff_st       = st.checkbox("Sous-traitant", key="d_st")
        diff_csps     = st.checkbox("Coordinateur SPS", value=True, key="d_csps")
    with dc2:
        st.markdown("**Intervenants internes**")
        diff_qse        = st.checkbox("Service QSE", value=True, key="d_qse")
        diff_dir        = st.checkbox("Directeur travaux", value=True, key="d_dir")
        diff_conducteur = st.checkbox("Conducteur de travaux", key="d_conducteur")
        diff_chef       = st.checkbox("Chef de chantier", value=True, key="d_chef")


# ── TAB 3 ─────────────────────────────────────────────────────────────────
with tabs[2]:
    def intervenant_form(titre, kp):
        st.markdown(f"**{titre}**")
        c1, c2 = st.columns(2)
        nom_i  = c1.text_input("Nom / Raison sociale", key=f"{kp}_nom")
        adr_i  = c2.text_input("Adresse", key=f"{kp}_adr")
        int_i  = c1.text_input("Interlocuteur référent", key=f"{kp}_int")
        tel_i  = c1.text_input("Téléphone", key=f"{kp}_tel")
        em_i   = c2.text_input("Email", key=f"{kp}_em")
        return {"nom": nom_i, "adresse": adr_i, "interlocuteur": int_i,
                "telephone": tel_i, "email": em_i}

    st.subheader("Intervenants du marché")
    moa_data = intervenant_form("Maître d'ouvrage", "moa")
    st.divider()
    moe_data = intervenant_form("Maîtrise d'œuvre (MOE)", "moe")
    st.divider()
    st.subheader("Intervenants de la prévention")
    csps_data = intervenant_form("Coordinateur SPS", "csps")
    st.divider()
    it_data   = intervenant_form("Inspection du travail", "it")
    st.divider()
    med_data  = intervenant_form("Médecine du travail", "med")


# ── TAB 4 ─────────────────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("Organisation de l'équipe")
    nb_membres = st.number_input("Nombre de membres", min_value=1, max_value=20, value=2)
    membres = []
    for i in range(int(nb_membres)):
        c1, c2 = st.columns(2)
        role_m = c1.text_input(f"Rôle #{i+1}", key=f"role_{i}")
        nom_m  = c2.text_input(f"Nom / Prénom #{i+1}", key=f"membre_{i}")
        membres.append({"role": role_m, "nom": nom_m})

    st.divider()
    st.subheader("Installation de chantier")
    inst_charge = st.checkbox("Installations à la charge de l'entreprise")
    ic1, ic2, ic3, ic4 = st.columns(4)
    inst_types = []
    if ic1.checkbox("Bungalow"):        inst_types.append("bungalow")
    if ic2.checkbox("Remorque VRS"):    inst_types.append("remorque")
    if ic3.checkbox("Locaux existants"):inst_types.append("locaux_existants")
    if ic4.checkbox("Autre"):           inst_types.append("autre")

    def local_form(lbl, key):
        st.markdown(f"*{lbl}*")
        c1, c2, c3 = st.columns([1,1,3])
        n  = c1.text_input("Nombre", key=f"{key}_nb")
        s  = c2.text_input("Surface", key=f"{key}_surf")
        cm = c3.text_input("Commentaires", key=f"{key}_com")
        return {"nombre": n, "surface": s, "commentaires": cm}

    vestiaire_d  = local_form("Vestiaires", "vest")
    refectoire_d = local_form("Réfectoire", "ref")
    sanitaire_d  = local_form("Sanitaires", "san")

    e1, e2, e3 = st.columns(3)
    en_elec  = e1.checkbox("Réseau électrique", value=True)
    en_group = e2.checkbox("Groupe électrogène")
    en_gaz   = e3.checkbox("Chauffage auxiliaire gaz")
    energies = (["reseau_elec"] if en_elec else []) + \
               (["groupe"] if en_group else []) + \
               (["chauffage_gaz"] if en_gaz else [])

    eau   = st.radio("Eau potable", ["Raccordement réseau", "Bouteilles"], horizontal=True)
    repas = st.radio("Repas", ["Sur le chantier", "À l'extérieur"], horizontal=True)
    date_inst = st.text_input("Date de mise en service des installations")


# ── TAB 5 ─────────────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Organisation des secours")
    c1, c2 = st.columns(2)
    sec_tel     = c1.text_input("Téléphone urgence chantier")
    sec_nom     = c2.text_input("Nom du chantier")
    sec_num     = c1.text_input("Numéro de chantier")
    sec_adresse = c2.text_input("Adresse / Localisation précise")
    sec_sst     = c1.text_input("Nom(s) du/des SST")
    sec_defib   = c2.text_input("Défibrillateur (emplacement)")

    st.divider()
    st.subheader("EPI obligatoires")
    epi_text = st.text_area("Un EPI par ligne",
        value="Casque de chantier\nGilet haute visibilité\nChaussures ou bottes de sécurité",
        height=120)
    epi_list = [e.strip() for e in epi_text.split("\n") if e.strip()]

    st.divider()
    st.subheader("Consignes de sécurité")
    consignes_text = st.text_area("Une consigne par ligne",
        value="Port des EPI obligatoire\nArrêt des moteurs si possible\nInterdiction de fumer",
        height=100)
    consignes_list = [c.strip() for c in consignes_text.split("\n") if c.strip()]

    st.divider()
    st.subheader("Propreté et cheminement")
    proprete_text = st.text_area("Une règle par ligne",
        value=("Nettoyer régulièrement les postes de travail\n"
               "Utiliser les zones de stockage prévues\n"
               "Maintenir le cantonnement propre en permanence\n"
               "Effectuer un nettoyage quotidien du chantier\n"
               "Mettre à disposition des poubelles pour le tri des déchets\n"
               "Désencombrer les voies de circulation"),
        height=130)
    proprete_list = [p.strip() for p in proprete_text.split("\n") if p.strip()]

    st.divider()
    st.subheader("Émargement — membres pré-remplis (optionnel)")
    nb_sign = st.number_input("Nombre de signataires", 0, 20, 0)
    signataires = []
    for i in range(int(nb_sign)):
        s1, s2 = st.columns(2)
        snom = s1.text_input(f"Nom #{i+1}", key=f"sign_nom_{i}")
        sent = s2.text_input(f"Entreprise #{i+1}", key=f"sign_ent_{i}")
        signataires.append({"nom": snom, "entreprise": sent})


# ── TAB 6 ─────────────────────────────────────────────────────────────────
with tabs[5]:
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

    if "nb_risques" not in st.session_state:
        st.session_state.nb_risques = 3

    col_add, col_rem, _ = st.columns([1, 1, 4])
    if col_add.button("＋ Ajouter une phase"):
        st.session_state.nb_risques += 1
    if col_rem.button("－ Supprimer la dernière") and st.session_state.nb_risques > 1:
        st.session_state.nb_risques -= 1

    risques = []
    for i in range(st.session_state.nb_risques):
        with st.expander(f"Phase {i+1}", expanded=(i < 3)):
            r1, r2 = st.columns(2)
            phase   = r1.text_input("Phase de travail", key=f"r_phase_{i}")
            facteur = r2.text_input("Facteur de risque", key=f"r_facteur_{i}")
            r3, r4  = st.columns(2)
            situation = r3.text_input("Situation à risque", key=f"r_sit_{i}")
            risque_id = r4.text_input("Risques identifiés", key=f"r_risque_{i}")
            r5, r6  = st.columns(2)
            dang_l  = r5.selectbox("Dangerosité", list(DANGER_OPTIONS.keys()), key=f"r_dang_{i}")
            expo_l  = r6.selectbox("Exposition", list(EXPO_OPTIONS.keys()), key=f"r_expo_{i}")
            mesures = st.text_area("Mesures de prévention", key=f"r_mes_{i}", height=60)
            risques.append({
                "phase": phase, "facteur_risque": facteur,
                "situation": situation, "risques": risque_id,
                "dangerosite": DANGER_OPTIONS[dang_l],
                "exposition": EXPO_OPTIONS[expo_l],
                "mesures": mesures,
            })


# ── TAB 7 ─────────────────────────────────────────────────────────────────
with tabs[6]:
    st.subheader("Générer le PPSPS")
    st.info("Vérifiez vos informations dans les onglets précédents, puis cliquez sur le bouton.")

    if st.button("📄 Générer le PDF", type="primary", use_container_width=True):
        data = {
            "entreprise": {
                "nom": ent_nom, "adresse": ent_adresse, "telephone": ent_tel,
                "email": ent_email, "responsable_technique": ent_resp,
                "tel_responsable": ent_tel_resp, "email_responsable": ent_email_resp,
            },
            "projet": {
                "intitule": proj_intitule, "client": proj_client,
                "situation": proj_situation, "type_ouvrage": proj_type,
                "description": proj_description, "date_debut": proj_debut,
                "duree": proj_duree, "effectif_moyen": proj_effectif,
                "avis_ouverture": proj_avis, "date_creation": proj_date_creation,
            },
            "acces_site": acces_site,
            "gestion": {
                "elaboration": gest_elab, "verification": gest_verif,
                "approbation": gest_appro, "suivis": suivis,
                "diffusion": {
                    "externes": {"moa": diff_moa, "moe": diff_moe, "mandataire": diff_mand,
                                 "cotraitant": diff_cotrait, "sous_traitant": diff_st, "csps": diff_csps},
                    "internes": {"qse": diff_qse, "dir_travaux": diff_dir,
                                 "conducteur": diff_conducteur, "chef_chantier": diff_chef},
                },
            },
            "intervenants": {
                "moa": moa_data, "moe": moe_data, "csps": csps_data,
                "inspection_travail": it_data, "medecine_travail": med_data,
            },
            "organisation": {"membres": membres},
            "installation": {
                "a_charge_entreprise": inst_charge, "types": inst_types,
                "vestiaire": vestiaire_d, "refectoire": refectoire_d,
                "sanitaire": sanitaire_d,
                "repas_sur_chantier": repas == "Sur le chantier",
                "energies": energies,
                "eau_potable": "reseau" if eau == "Raccordement réseau" else "bouteilles",
                "date_mise_en_service": date_inst,
            },
            "secours": {
                "telephone_urgence": sec_tel, "chantier_nom": sec_nom,
                "chantier_numero": sec_num, "chantier_adresse": sec_adresse,
                "sst_noms": sec_sst, "defibrillateur": sec_defib,
            },
            "prevention": {
                "epi": epi_list, "consignes": consignes_list, "proprete": proprete_list,
            },
            "risques": [r for r in risques if r.get("phase") or r.get("situation")],
            "signataires": signataires,
        }

        with st.spinner("Génération en cours..."):
            try:
                pdf_buf = generer_ppsps(data)
                nom_fichier = f"PPSPS_{(proj_intitule or 'document').replace(' ','_')}.pdf"
                st.success("✅ PDF généré avec succès !")
                st.download_button(
                    label="⬇️ Télécharger le PPSPS",
                    data=pdf_buf,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")
                raise
