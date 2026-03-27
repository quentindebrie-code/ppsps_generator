"""
ppsps_generator.py — Génère un PPSPS professionnel en ReportLab Platypus.
Contenu 100% dynamique : le document s'adapte à la quantité de données.
"""

import io
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.pdfbase.pdfmetrics import stringWidth

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#0D1B3E")
NAVY_MID  = colors.HexColor("#1A3A6B")
NAVY_LITE = colors.HexColor("#D6E4F0")
ACCENT    = colors.HexColor("#2E75B6")
ROW_ALT   = colors.HexColor("#F4F7FB")
WHITE     = colors.white
GREY_LINE = colors.HexColor("#CCCCCC")
GREY_TEXT = colors.HexColor("#555555")
BLACK     = colors.black

PW, PH = A4  # 595.3 x 841.9 pt
ML = MR = 1.8*cm
MT = MB = 2.0*cm
CONTENT_W = PW - ML - MR


# ═══════════════════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════════════════
def _build_styles():
    s = getSampleStyleSheet()

    def add(name, **kw):
        s.add(ParagraphStyle(name=name, **kw))

    add("Cover_Company",   fontName="Helvetica-Bold", fontSize=13, textColor=NAVY,
        spaceAfter=2, leading=16)
    add("Cover_Address",   fontName="Helvetica",       fontSize=9,  textColor=GREY_TEXT,
        spaceAfter=2, leading=12)
    add("Cover_Title",     fontName="Helvetica-Bold",  fontSize=22, textColor=WHITE,
        alignment=TA_CENTER, leading=28)
    add("Cover_Subtitle",  fontName="Helvetica",       fontSize=12, textColor=WHITE,
        alignment=TA_CENTER, leading=16, spaceAfter=4)
    add("Cover_Client",    fontName="Helvetica-Bold",  fontSize=16, textColor=NAVY,
        alignment=TA_CENTER, leading=20)
    add("Cover_Meta",      fontName="Helvetica",       fontSize=9,  textColor=GREY_TEXT,
        alignment=TA_CENTER, leading=13)
    add("Cover_Mention",   fontName="Helvetica-Oblique", fontSize=7.5, textColor=GREY_TEXT,
        alignment=TA_CENTER)

    add("H1",  fontName="Helvetica-Bold", fontSize=11, textColor=WHITE,
        spaceBefore=8, spaceAfter=6, leading=14)
    add("H2",  fontName="Helvetica-Bold", fontSize=9.5, textColor=NAVY,
        spaceBefore=6, spaceAfter=3, leading=13)
    add("H3",  fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY_MID,
        spaceBefore=4, spaceAfter=2, leading=11)

    add("Body", fontName="Helvetica", fontSize=8.5, textColor=BLACK,
        spaceAfter=3, leading=12)
    add("BodySmall", fontName="Helvetica", fontSize=7.5, textColor=BLACK,
        spaceAfter=2, leading=10)
    add("BulletItem", fontName="Helvetica", fontSize=8.5, textColor=BLACK,
        leftIndent=12, firstLineIndent=-8, spaceAfter=2, leading=11)

    add("TH",  fontName="Helvetica-Bold", fontSize=8,   textColor=WHITE,
        alignment=TA_CENTER, leading=10)
    add("TD",  fontName="Helvetica",       fontSize=8,   textColor=BLACK,
        leading=10, spaceAfter=1)
    add("TD_C",fontName="Helvetica",       fontSize=8,   textColor=BLACK,
        alignment=TA_CENTER, leading=10)
    add("TLabel",fontName="Helvetica-Bold",fontSize=8,  textColor=NAVY,
        leading=10)
    add("TVal", fontName="Helvetica",      fontSize=8,  textColor=BLACK,
        leading=10)

    add("Footer", fontName="Helvetica", fontSize=7, textColor=GREY_TEXT,
        alignment=TA_CENTER)
    add("TOC_Entry", fontName="Helvetica", fontSize=9, textColor=BLACK,
        spaceAfter=3, leading=13)
    add("TOC_Title",fontName="Helvetica-Bold", fontSize=11, textColor=NAVY,
        spaceAfter=8, leading=14)

    add("Annex_Title", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY,
        spaceBefore=0, spaceAfter=10, leading=17, alignment=TA_CENTER)
    add("Risk_Phase",  fontName="Helvetica-Bold", fontSize=7.5, textColor=NAVY,
        leading=9)
    add("Risk_Cell",   fontName="Helvetica",       fontSize=7,   textColor=BLACK,
        leading=9, spaceAfter=1)

    return s

S = _build_styles()


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM FLOWABLES
# ═══════════════════════════════════════════════════════════════════════════════
class SectionHeader(Flowable):
    """Bande bleue avec numéro + titre de section."""
    def __init__(self, number, title, width=CONTENT_W):
        super().__init__()
        self.number = number
        self.title  = title
        self.width  = width
        self.height = 22

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 10)
        label = f"{self.number}.  {self.title.upper()}" if self.number else self.title.upper()
        c.drawString(8, 6, label)

    def wrap(self, aw, ah):
        return self.width, self.height


class SubSectionHeader(Flowable):
    """Bande bleu clair avec titre de sous-section."""
    def __init__(self, number, title, width=CONTENT_W):
        super().__init__()
        self.number = number
        self.title  = title
        self.width  = width
        self.height = 17

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY_LITE)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9)
        label = f"{self.number}  {self.title}" if self.number else self.title
        c.drawString(8, 4, label)

    def wrap(self, aw, ah):
        return self.width, self.height


class ColorRect(Flowable):
    """Rectangle de couleur plein."""
    def __init__(self, width, height, fill_color):
        super().__init__()
        self.width  = width
        self.height = height
        self.fill   = fill_color

    def draw(self):
        self.canv.setFillColor(self.fill)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)

    def wrap(self, aw, ah):
        return self.width, self.height


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE TEMPLATE (en-tête / pied de page)
# ═══════════════════════════════════════════════════════════════════════════════
def _make_page_template(entreprise_nom, projet_intitule):
    def on_page(canvas, doc):
        canvas.saveState()
        # Bande haute
        canvas.setFillColor(NAVY)
        canvas.rect(0, PH - 28, PW, 28, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(ML, PH - 19, entreprise_nom or "")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PW - MR, PH - 19, projet_intitule or "")

        # Bande basse
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, PW, 20, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(ML, 6, "Ce document est la propriété de "
                          + (entreprise_nom or "") + ". Il ne peut être diffusé sans autorisation.")
        canvas.drawRightString(PW - MR, 6,
                               f"Page {doc.page}")
        canvas.restoreState()

    def on_first_page(canvas, doc):
        canvas.saveState()
        # Pied de page simple sur la couverture
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, PW, 20, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(PW / 2, 6,
            "Ce document est la propriété de "
            + (entreprise_nom or "") + ". Il ne peut être diffusé sans autorisation.")
        canvas.restoreState()

    return on_first_page, on_page


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def P(text, style="Body"):
    return Paragraph(str(text) if text else "", S[style])

def SP(h=4):
    return Spacer(1, h)

def HR():
    return HRFlowable(width="100%", thickness=0.5, color=GREY_LINE, spaceAfter=4, spaceBefore=4)

def _info_table(rows, col_w=None):
    """Tableau label/valeur à 2 colonnes."""
    if col_w is None:
        col_w = [5.5*cm, CONTENT_W - 5.5*cm]
    data = [[P(label, "TLabel"), P(val or "—", "TVal") if isinstance(val, str) else val]
            for label, val in rows]
    t = Table(data, colWidths=col_w, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",  (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0), (-1,-1), 4),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [WHITE, ROW_ALT]),
        ("GRID",        (0,0), (-1,-1), 0.3, GREY_LINE),
    ]))
    return t

def _chk(checked, size=7):
    """Carré vectoriel : noir plein si coché, blanc avec contour si non coché."""
    d = Drawing(size + 2, size + 2)
    d.add(Rect(1, 1, size, size,
               fillColor=BLACK if checked else WHITE,
               strokeColor=BLACK, strokeWidth=0.8))
    return d

def _chk_row(prefix, *options):
    """
    Retourne un Table flowable :  prefix  [■/□] label  [■/□] label …
    options : list of (checked: bool, label: str)
    """
    cells  = []
    widths = []
    FONT, FS = "Helvetica", 8.5
    if prefix:
        cells.append(P(prefix, "Body"))
        widths.append(stringWidth(prefix, FONT, FS) + 4)
    for checked, label in options:
        cells.append(_chk(checked))
        cells.append(P(f" {label}", "Body"))
        widths.append(0.35 * cm)
        widths.append(stringWidth(f" {label}", FONT, FS) + 8)
    t = Table([cells], colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _page_cover(story, data):
    ent  = data.get("entreprise", {})
    proj = data.get("projet", {})

    # En-tête société
    story.append(SP(10))
    story.append(P(ent.get("nom", ""), "Cover_Company"))
    if ent.get("adresse"):
        story.append(P(ent["adresse"], "Cover_Address"))
    contact = " | ".join(filter(None, [ent.get("telephone"), ent.get("email")]))
    if contact:
        story.append(P(contact, "Cover_Address"))

    story.append(SP(20))

    # Bandeau titre principal
    title_w = CONTENT_W
    title_data = [[P("PLAN PARTICULIER DE SÉCURITÉ", "Cover_Title")],
                  [P("ET DE PROTECTION DE LA SANTÉ", "Cover_Title")],
                  [P("P.P.S.P.S.", "Cover_Subtitle")]]
    tt = Table(title_data, colWidths=[title_w])
    tt.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), NAVY),
        ("TOPPADDING",   (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0), (-1,-1), 10),
        ("LEFTPADDING",  (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(tt)
    story.append(SP(20))

    # Infos projet
    client = proj.get("client","")
    intitule = proj.get("intitule","")
    if client or intitule:
        story.append(P(client or intitule, "Cover_Client"))
        if client and intitule:
            story.append(P(intitule, "Cover_Meta"))
    story.append(SP(8))

    meta_rows = []
    if proj.get("situation"):
        meta_rows.append(("Situation :", proj["situation"]))
    if proj.get("date_debut"):
        meta_rows.append(("Date de début :", proj["date_debut"]))
    if proj.get("duree"):
        meta_rows.append(("Durée :", proj["duree"]))
    if meta_rows:
        story.append(_info_table(meta_rows, col_w=[4*cm, CONTENT_W-4*cm]))
    story.append(SP(30))

    # Indice / Date
    indice_data = [
        [P("Indice", "TH"), P("Date", "TH"), P("Nature de révision", "TH")],
        [P("A", "TD_C"),    P(proj.get("date_creation",""), "TD_C"),
         P("Création du document", "TD")],
    ]
    it = Table(indice_data, colWidths=[2*cm, 4*cm, CONTENT_W-6*cm])
    it.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), NAVY_MID),
        ("GRID",         (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, ROW_ALT]),
    ]))
    story.append(it)
    story.append(SP(30))
    story.append(P("Page : 1/" + "—", "Cover_Mention"))
    story.append(P("Ce document est la propriété de "
                   + (ent.get("nom","")) + ". Il ne peut être diffusé ou reproduit sans son autorisation.",
                   "Cover_Mention"))
    story.append(PageBreak())


def _section_gestion(story, data):
    proj    = data.get("projet", {})
    ent     = data.get("entreprise", {})
    gestion = data.get("gestion", {})

    story.append(SectionHeader("1", "GESTION ET DIFFUSION"))
    story.append(SP(6))

    # 1.1 Révisions
    story.append(SubSectionHeader("1.1", "Révisions"))
    story.append(SP(4))
    story.append(P("La mise à jour du PPSPS suit le même circuit de validation et de vérification. "
                   "Selon l'évolution des tâches d'exécution, un additif au PPSPS est préparé et validé "
                   "préalablement à toute intervention.", "Body"))
    story.append(SP(4))

    elab  = gestion.get("elaboration",  ent.get("responsable_technique", ""))
    verif = gestion.get("verification", ent.get("responsable_technique", ""))
    appro = gestion.get("approbation",  ent.get("chef_chantier", ""))

    rev_data = [
        [P("Élaboration","TH"), P("Vérification","TH"), P("Approbation","TH"),
         P("Avis du CSE","TH"), P("Avis médecin du travail","TH")],
        [P(elab,"TD_C"),        P(verif,"TD_C"),         P(appro,"TD_C"),
         P("","TD_C"),           P("","TD_C")],
    ]
    rt = Table(rev_data, colWidths=[CONTENT_W/5]*5)
    rt.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), NAVY_MID),
        ("GRID",         (0,0),(-1,-1), 0.3, GREY_LINE),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",        (0,0),(-1,-1), "CENTER"),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE]),
    ]))
    story.append(rt)
    story.append(SP(8))

    # 1.2 Suivi
    story.append(SubSectionHeader("1.2", "Suivi des révisions"))
    story.append(SP(4))
    suivis = gestion.get("suivis", [{"indice":"A","date":proj.get("date_creation",""),"nature":"Création du document"}])
    suivi_data = [[P("Indice","TH"), P("Date","TH"), P("Nature de révision","TH")]]
    for s in suivis:
        suivi_data.append([P(s.get("indice",""),"TD_C"), P(s.get("date",""),"TD_C"), P(s.get("nature",""),"TD")])
    st2 = Table(suivi_data, colWidths=[2*cm, 4*cm, CONTENT_W-6*cm])
    st2.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), NAVY_MID),
        ("GRID",         (0,0),(-1,-1), 0.3, GREY_LINE),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,ROW_ALT]),
    ]))
    story.append(st2)
    story.append(SP(8))

    # 1.3 Diffusion
    story.append(SubSectionHeader("1.3", "Diffusion"))
    story.append(SP(4))
    diffusion = gestion.get("diffusion", {})
    ext = diffusion.get("externes", {})
    int_ = diffusion.get("internes", {})

    diff_rows = [
        [P("INTERVENANTS EXTERNES","TH"), P("Diffusé","TH"), P("INTERVENANTS INTERNES","TH"), P("Diffusé","TH")],
        [P("Maître d'ouvrage","TD"),   _chk(ext.get("moa",True)),
         P("Service QSE","TD"),         _chk(int_.get("qse",True))],
        [P("Maître d'œuvre","TD"),      _chk(ext.get("moe",True)),
         P("Directeur travaux","TD"),   _chk(int_.get("dir_travaux",True))],
        [P("Entreprise mandataire","TD"),_chk(ext.get("mandataire",False)),
         P("Conducteur de travaux","TD"),_chk(int_.get("conducteur",False))],
        [P("Entreprise cotraitante","TD"),_chk(ext.get("cotraitant",False)),
         P("Chef de chantier","TD"),    _chk(int_.get("chef_chantier",True))],
        [P("Sous-traitant","TD"),        _chk(ext.get("sous_traitant",False)),
         P("","TD"),                    P("","TD")],
        [P("Coordinateur SPS","TD"),    _chk(ext.get("csps",True)),
         P("","TD"),                    P("","TD")],
    ]
    hw = (CONTENT_W - 2*cm) / 2
    dt = Table(diff_rows, colWidths=[hw*0.75, hw*0.25, hw*0.75, hw*0.25])
    dt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), NAVY_MID),
        ("GRID",          (0,0),(-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0),(1,-1), "CENTER"),
        ("ALIGN",         (3,0),(3,-1), "CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,ROW_ALT]),
    ]))
    story.append(dt)
    story.append(PageBreak())


def _section_presentation(story, data):
    proj = data.get("projet", {})

    story.append(SectionHeader("2", "PRÉSENTATION DES TRAVAUX"))
    story.append(SP(6))

    rows = [
        ("Intitulé du chantier",      proj.get("intitule","")),
        ("Client / Maître d'ouvrage", proj.get("client","")),
        ("Situation des travaux",     proj.get("situation","")),
        ("Type d'ouvrage",            proj.get("type_ouvrage","")),
        ("Description des travaux",   proj.get("description","")),
        ("Date de début",             proj.get("date_debut","")),
        ("Durée d'intervention",      proj.get("duree","")),
        ("Effectif moyen propre",     proj.get("effectif_moyen","")),
        ("Avis d'ouverture de chantier",
         _chk_row("",
                  (proj.get("avis_ouverture", False), "OUI"),
                  (not proj.get("avis_ouverture", False), "NON  (si > 1 semaine ET > 10 personnes)"))),
    ]
    story.append(_info_table(rows, col_w=[6*cm, CONTENT_W-6*cm]))
    story.append(SP(10))

    story.append(SectionHeader("3", "ACCÈS AU SITE"))
    story.append(SP(6))
    acces = data.get("acces_site", "")
    story.append(P("L'accès au chantier se fera par :", "Body"))
    story.append(P(acces if acces else "—", "Body"))
    story.append(SP(10))


def _section_intervenants(story, data):
    interv = data.get("intervenants", {})

    story.append(SectionHeader("4", "INTERVENANTS ET CONTACTS"))
    story.append(SP(6))
    story.append(SubSectionHeader("4.1", "Intervenants du marché"))
    story.append(SP(4))

    def bloc_intervenant(titre, d):
        if not d:
            return []
        items = [SP(4), P(titre, "H3")]
        rows = []
        for k, label in [("nom","Nom / Raison sociale"),("adresse","Adresse"),
                          ("interlocuteur","Interlocuteur référent"),
                          ("telephone","Téléphone"),("email","Mail")]:
            v = d.get(k,"")
            if v:
                rows.append((label, v))
        if rows:
            items.append(_info_table(rows))
        return items

    moa = interv.get("moa",{})
    moe = interv.get("moe",{})
    ent = data.get("entreprise",{})

    for titre, d in [("Maître d'ouvrage", moa),
                     ("Maîtrise d'œuvre", moe),
                     ("Entreprise", {
                         "nom": ent.get("nom",""),
                         "adresse": ent.get("adresse",""),
                         "telephone": ent.get("telephone",""),
                         "email": ent.get("email",""),
                         "interlocuteur": ent.get("responsable_technique",""),
                     })]:
        for fl in bloc_intervenant(titre, d):
            story.append(fl)

    story.append(SP(8))
    story.append(SubSectionHeader("4.2", "Intervenants de la prévention"))
    story.append(SP(4))

    for titre, key in [("Coordinateur SPS","csps"),
                       ("Inspection du travail","inspection_travail"),
                       ("Médecine du travail","medecine_travail")]:
        for fl in bloc_intervenant(titre, interv.get(key,{})):
            story.append(fl)
    story.append(PageBreak())


def _section_organisation(story, data):
    org  = data.get("organisation", {})
    inst = data.get("installation", {})

    story.append(SectionHeader("5", "ORGANISATION DE CHANTIER"))
    story.append(SP(6))
    story.append(SubSectionHeader("5.1", "Organisation de l'équipe d'exécution"))
    story.append(SP(6))

    membres = org.get("membres", [])
    if membres:
        org_rows = [[P("Rôle","TH"), P("Nom / Prénom","TH")]]
        for m in membres:
            org_rows.append([P(m.get("role",""),"TD"), P(m.get("nom",""),"TD")])
        ot = Table(org_rows, colWidths=[CONTENT_W*0.4, CONTENT_W*0.6])
        ot.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,0), NAVY_MID),
            ("GRID",         (0,0),(-1,-1), 0.3, GREY_LINE),
            ("TOPPADDING",   (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING",  (0,0),(-1,-1), 6),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,ROW_ALT]),
        ]))
        story.append(ot)
    else:
        story.append(P("—", "Body"))
    story.append(SP(10))

    story.append(SectionHeader("6", "INSTALLATION DE CHANTIER"))
    story.append(SP(6))

    charge = inst.get("a_charge_entreprise", False)
    story.append(P("Les installations de chantier sont-elles à la charge de l'entreprise ?", "Body"))
    story.append(_chk_row("", (charge, "Oui"), (not charge, "Non")))
    story.append(SP(4))

    types = inst.get("types", [])
    type_labels = {"bungalow":"Bungalow","remorque":"Remorque VRS",
                   "locaux_existants":"Locaux existants","autre":"Autre"}
    story.append(_chk_row("Cantonnements prévus :  ",
                           *[(t in types, type_labels.get(t, t)) for t in type_labels]))
    story.append(SP(6))

    # Tableau locaux
    loc_data = [[P("Locaux","TH"), P("Nombre","TH"), P("Surface","TH"),
                 P("Équipements inclus","TH"), P("Commentaires","TH")]]
    eqp_std = {
        "vestiaire":    "Bancs/chaises · Patères · Armoire-vestiaire/pers.",
        "refectoire":   "Tables/chaises · Micro-ondes · Réfrigérateur · 1 robinet/10 pers.",
        "sanitaire":    "Douches · WC · Chauffe-eau · Chauffage",
    }
    for key, label in [("vestiaire","Vestiaire"),("refectoire","Réfectoire"),("sanitaire","Sanitaire")]:
        d = inst.get(key, {})
        loc_data.append([
            P(label,"TD"), P(str(d.get("nombre","")),"TD_C"), P(d.get("surface",""),"TD_C"),
            P(eqp_std[key],"TD"), P(d.get("commentaires",""),"TD"),
        ])
    lt = Table(loc_data, colWidths=[2.5*cm, 1.8*cm, 1.8*cm, 6*cm, CONTENT_W-12.1*cm])
    lt.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), NAVY_MID),
        ("GRID",         (0,0),(-1,-1), 0.3, GREY_LINE),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",  (0,0),(-1,-1), 5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,ROW_ALT]),
    ]))
    story.append(lt)
    story.append(SP(6))

    repas = inst.get("repas_sur_chantier", True)
    story.append(_chk_row("Repas :  ",
                           (repas, "Sur le chantier"), (not repas, "À l'extérieur")))

    energies = inst.get("energies", [])
    e_map = {"reseau_elec":"Raccordement réseau électrique",
             "groupe":"Groupe électrogène","chauffage_gaz":"Chauffage auxiliaire gaz"}
    story.append(_chk_row("Énergie :  ",
                           *[(e in energies, e_map.get(e, e)) for e in e_map]))

    eau = inst.get("eau_potable","reseau")
    story.append(_chk_row("Eau potable :  ",
                           (eau == "bouteilles", "Bouteilles"), (eau == "reseau", "Raccordement réseau")))

    if inst.get("date_mise_en_service"):
        story.append(P("Date de mise en service des installations : "
                        + inst["date_mise_en_service"], "Body"))

    story.append(PageBreak())


def _section_secours(story, data):
    sec = data.get("secours", {})

    story.append(SectionHeader("7", "ORGANISATION DES SECOURS"))
    story.append(SP(6))
    story.append(SubSectionHeader("7.1", "Organisation des appels de secours"))
    story.append(SP(4))
    story.append(P("Les points de rendez-vous sont définis et validés par le CSPS. En cas d'accident, "
                   "le point de rendez-vous le plus proche sera communiqué aux secours. "
                   "La fiche d'appel de secours est affichée dans le bureau du chantier.", "Body"))
    story.append(SP(6))

    rows = []
    if sec.get("telephone_urgence"):
        rows.append(("Téléphone urgence chantier", sec["telephone_urgence"]))
    if sec.get("chantier_nom"):
        rows.append(("Nom du chantier", sec["chantier_nom"]))
    if sec.get("chantier_numero"):
        rows.append(("Numéro de chantier", sec["chantier_numero"]))
    if sec.get("chantier_adresse"):
        rows.append(("Adresse / Localisation", sec["chantier_adresse"]))
    sst = sec.get("sst_noms","")
    if sst:
        rows.append(("SST (Sauveteur Secouriste)", sst))
    if sec.get("defibrillateur"):
        rows.append(("Défibrillateur", sec["defibrillateur"]))
    if rows:
        story.append(_info_table(rows))
    story.append(SP(8))

    story.append(SubSectionHeader("7.2", "Trousse de premiers soins"))
    story.append(SP(4))
    story.append(P("Une trousse de secours par chef de chantier dans le fourgon, "
                   "et une dans la base vie au minimum. "
                   "Tenir à jour les boîtes de secours selon la liste établie avec la médecine du travail. "
                   "Stocker à l'abri de la chaleur et de la lumière. "
                   "Vérifier les dates de péremption régulièrement.", "Body"))
    story.append(SP(4))
    story.append(P("⚠  Il est interdit d'avoir des médicaments (type aspirine) dans la trousse de secours.",
                   "Body"))
    story.append(PageBreak())


def _section_prevention(story, data):
    prev = data.get("prevention", {})
    epi_list = prev.get("epi", [
        "Casque de chantier", "Gilet haute visibilité",
        "Chaussures ou bottes de sécurité"
    ])

    story.append(SectionHeader("8", "MESURES GÉNÉRALES DE PRÉVENTION"))
    story.append(SP(6))
    story.append(SubSectionHeader("8.1", "Consignes de sécurité"))
    story.append(SP(4))
    story.append(P("Afin de sensibiliser le personnel à sa présence sur site, les consignes réglementaires "
                   "sont rappelées lors de la 1ère journée :", "Body"))
    consignes = prev.get("consignes", [
        "Port des EPI obligatoire",
        "Arrêt des moteurs si possible",
        "Interdiction de fumer",
    ])
    for c in consignes:
        story.append(P("• " + c, "BulletItem"))
    story.append(SP(6))

    story.append(SubSectionHeader("8.2", "Équipements de protection individuelle (EPI)"))
    story.append(SP(4))
    story.append(P("Sur ce chantier, toutes les personnes intervenantes doivent disposer des EPI suivants :", "Body"))
    for e in epi_list:
        story.append(P("• " + e, "BulletItem"))
    story.append(SP(6))

    story.append(SubSectionHeader("8.3", "Propreté et cheminement"))
    story.append(SP(4))
    proprete = prev.get("proprete", [
        "Nettoyer régulièrement les postes de travail",
        "Utiliser les zones de stockage prévues pour le matériel",
        "Maintenir le cantonnement propre en permanence",
        "Effectuer un nettoyage quotidien du chantier",
        "Mettre à disposition des poubelles et bennes pour le tri des déchets",
        "Désencombrer les voies de circulation",
    ])
    for p in proprete:
        story.append(P("• " + p, "BulletItem"))

    remarques = prev.get("remarques","")
    if remarques:
        story.append(SP(6))
        story.append(P(remarques, "Body"))
    story.append(PageBreak())


def _section_risques(story, data):
    risques = data.get("risques", [])

    story.append(SectionHeader("", "ANNEXE 1 — ÉVALUATION DES RISQUES"))
    story.append(SP(8))

    if not risques:
        story.append(P("Aucune phase de travail renseignée.", "Body"))
        story.append(PageBreak())
        return

    # Grille de lecture dangerosité
    story.append(SubSectionHeader("", "Grille de lecture"))
    story.append(SP(4))
    grille_data = [
        [P("Dangerosité","TH"), P("Indice","TH"), P("Exposition","TH"), P("Indice","TH")],
        [P("Blessure légère, sans arrêt de travail","TD"),         P("1","TD_C"),
         P("Exposition occasionnelle","TD"),                        P("1","TD_C")],
        [P("Atteinte sans effets irréversibles, avec arrêt","TD"), P("10","TD_C"),
         P("Exposition intermittente","TD"),                        P("2","TD_C")],
        [P("Effets irréversibles / incapacité permanente","TD"),   P("100","TD_C"),
         P("Exposition fréquente","TD"),                            P("3","TD_C")],
        [P("Danger de mort","TD"),                                  P("1000","TD_C"),
         P("Exposition permanente","TD"),                           P("4","TD_C")],
    ]
    hw2 = CONTENT_W / 2
    gt = Table(grille_data, colWidths=[hw2*0.8, hw2*0.2, hw2*0.8, hw2*0.2])
    gt.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), NAVY_MID),
        ("GRID",         (0,0),(-1,-1), 0.3, GREY_LINE),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,ROW_ALT]),
    ]))
    story.append(gt)
    story.append(SP(10))

    # Tableau des risques (auto-paginé par Platypus)
    col_w = [2.5*cm, 2.2*cm, 3*cm, 2.5*cm, 1.2*cm, 1.2*cm, 1.2*cm, CONTENT_W-13.8*cm]
    header = [
        P("Phase de\ntravail","TH"),
        P("Facteur de\nrisque","TH"),
        P("Situation\nà risque","TH"),
        P("Risques\nidentifiés","TH"),
        P("Danger.\n(D)","TH"),
        P("Expo.\n(E)","TH"),
        P("Prio.\n(D×E)","TH"),
        P("Mesures de\nprévention","TH"),
    ]
    risk_data = [header]

    DANGER_COLORS = {1: colors.HexColor("#C8E6C9"), 10: colors.HexColor("#FFF9C4"),
                     100: colors.HexColor("#FFCCBC"), 1000: colors.HexColor("#EF9A9A")}

    for r in risques:
        d_val = r.get("dangerosité", r.get("dangerosite", 1))
        e_val = r.get("exposition", 1)
        try:
            prio = int(d_val) * int(e_val)
        except (ValueError, TypeError):
            prio = ""
        risk_data.append([
            P(r.get("phase",""),         "Risk_Phase"),
            P(r.get("facteur_risque",""),"Risk_Cell"),
            P(r.get("situation",""),     "Risk_Cell"),
            P(r.get("risques",""),       "Risk_Cell"),
            P(str(d_val),                "TD_C"),
            P(str(e_val),                "TD_C"),
            P(str(prio),                 "TD_C"),
            P(r.get("mesures",""),       "Risk_Cell"),
        ])

    risk_table = Table(risk_data, colWidths=col_w, repeatRows=1)

    ts = [
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("GRID",          (0,0), (-1,-1), 0.3, GREY_LINE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
    ]
    # Colorer les lignes selon dangerosité
    for i, r in enumerate(risques, start=1):
        d_val = r.get("dangerosité", r.get("dangerosite", 1))
        try:
            d_int = int(d_val)
        except (ValueError, TypeError):
            d_int = 1
        bg = DANGER_COLORS.get(d_int, WHITE)
        ts.append(("BACKGROUND", (4, i), (6, i), bg))
        ts.append(("BACKGROUND", (0, i), (3, i), WHITE if i % 2 == 0 else ROW_ALT))
        ts.append(("BACKGROUND", (7, i), (7, i), WHITE if i % 2 == 0 else ROW_ALT))

    risk_table.setStyle(TableStyle(ts))
    story.append(risk_table)
    story.append(PageBreak())


def _section_accident(story, data):
    sec  = data.get("secours", {})
    proj = data.get("projet", {})

    story.append(SectionHeader("", "ANNEXE 2 — EN CAS D'ACCIDENT"))
    story.append(SP(10))

    # Cadre urgence
    urg_data = [
        [P("EN CAS D'ACCIDENT", "Cover_Title")],
        [P("Appelez le sauveteur secouriste du travail qui, après avoir examiné la victime,\n"
           "vous demandera d'appeler les secours.", "Cover_Subtitle")],
    ]
    ut = Table(urg_data, colWidths=[CONTENT_W])
    ut.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), NAVY),
        ("TOPPADDING", (0,0),(-1,-1), 12),
        ("BOTTOMPADDING",(0,0),(-1,-1),12),
    ]))
    story.append(ut)
    story.append(SP(12))

    tel = sec.get("telephone_urgence","")
    if tel:
        tel_data = [[P(f"Téléphonez au :  {tel}", "Cover_Client")]]
        tt2 = Table(tel_data, colWidths=[CONTENT_W])
        tt2.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), NAVY_LITE),
            ("TOPPADDING",(0,0),(-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("BOX",(0,0),(-1,-1), 1, NAVY),
        ]))
        story.append(tt2)
        story.append(SP(10))

    # Infos chantier
    rows = []
    if proj.get("intitule"):   rows.append(("Chantier",  proj["intitule"]))
    if proj.get("client"):     rows.append(("Client",    proj["client"]))
    if sec.get("chantier_adresse"): rows.append(("Adresse", sec["chantier_adresse"]))
    sst = sec.get("sst_noms","")
    if sst: rows.append(("SST (Sauveteur Secouriste)", sst))
    if sec.get("defibrillateur"): rows.append(("Défibrillateur le plus proche", sec["defibrillateur"]))
    if rows:
        story.append(P("À RETENIR :", "H2"))
        story.append(_info_table(rows))
        story.append(SP(8))

    consignes_accident = [
        "Précisez la nature de l'accident (ex : éboulement, asphyxie, chute…)",
        "Précisez la position du blessé et s'il y a nécessité de dégagement",
        "Signalez le nombre de blessés et leur état",
        "Décrivez l'intervention du secouriste",
        "Fixez un point de rendez-vous et envoyez quelqu'un guider les secours",
        "Faites répéter le message — Ne raccrochez jamais le premier",
    ]
    story.append(P("Consignes au téléphone :", "H2"))
    for c in consignes_accident:
        story.append(P("• " + c, "BulletItem"))
    story.append(PageBreak())


def _section_emargement(story, data):
    signataires = data.get("signataires", [])

    story.append(SectionHeader("", "ANNEXE 3 — ÉMARGEMENT DE L'ÉQUIPE"))
    story.append(SP(8))
    story.append(P("L'équipe qui réalise les travaux doit être sensibilisée aux risques et aux mesures "
                   "de prévention. Le conducteur de travaux et/ou le chef de chantier communique le PPSPS "
                   "à son équipe le 1er jour du démarrage du chantier et avant le commencement des travaux. "
                   "Tout nouvel arrivant doit également prendre connaissance du PPSPS et le signer.",
                   "Body"))
    story.append(SP(10))

    em_data = [[P("NOM + Prénom","TH"), P("Entreprise / Agence d'intérim","TH"), P("Signature","TH")]]
    # Lignes pré-remplies
    for s in signataires:
        em_data.append([P(s.get("nom",""),"TD"), P(s.get("entreprise",""),"TD"), P("","TD")])
    # Lignes vides pour émargement futur
    nb_vides = max(10 - len(signataires), 5)
    for _ in range(nb_vides):
        em_data.append([P("","TD"), P("","TD"), P("","TD")])

    emat = Table(em_data, colWidths=[CONTENT_W*0.35, CONTENT_W*0.35, CONTENT_W*0.30])
    emat.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), NAVY_MID),
        ("GRID",          (0,0),(-1,-1), 0.3, GREY_LINE),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 14),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,ROW_ALT]),
    ]))
    story.append(emat)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
def generer_ppsps(data: dict) -> io.BytesIO:
    """Génère le PPSPS complet. Retourne un BytesIO contenant le PDF."""
    buf = io.BytesIO()
    ent  = data.get("entreprise", {})
    proj = data.get("projet", {})

    on_first, on_later = _make_page_template(
        ent.get("nom",""), proj.get("intitule","")
    )

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT + 28,   # laisser place à la bande haute
        bottomMargin=MB + 20,
        title="PPSPS – " + (proj.get("intitule","") or ""),
        author=ent.get("nom",""),
    )

    story = []
    _page_cover(story, data)
    _section_gestion(story, data)
    _section_presentation(story, data)
    _section_intervenants(story, data)
    _section_organisation(story, data)
    _section_secours(story, data)
    _section_prevention(story, data)
    _section_risques(story, data)
    _section_accident(story, data)
    _section_emargement(story, data)

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    buf.seek(0)
    return buf
