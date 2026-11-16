"""Printable peer-assessment sheets: one page per member, teammates pre-filled.
Format from the AISR Project Instructions (Section 4).

    python3 docs/report/peer_assessment.py   # -> docs/report/Peer_Assessment_Sheets.docx
"""

import os

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt

MEMBERS = [("Mihika", "500122055"), ("Divyanshu Dhyani", "500122522"),
           ("Disha Rastogi", "500119681"), ("Sumit Malhotra", "500123752"),
           ("Prachi Chetan Padodara", "500126371")]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Peer_Assessment_Sheets.docx")

d = docx.Document()
sec = d.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin = Cm(3.0)
sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2.5)
sec._sectPr.append(parse_xml(
    f'<w:pgBorders {nsdecls("w")} w:offsetFrom="page">'
    + "".join(f'<w:{s} w:val="single" w:sz="8" w:space="24" w:color="000000"/>'
              for s in ("top", "left", "bottom", "right")) + "</w:pgBorders>"))
st = d.styles["Normal"]
st.font.name = "Times New Roman"
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.font.size = Pt(12)
st.paragraph_format.line_spacing = 1.5


def p(text="", size=12, bold=False, align=None, after=6):
    par = d.add_paragraph()
    par.paragraph_format.space_after = Pt(after)
    if align is not None:
        par.alignment = align
    r = par.add_run(text)
    r.bold, r.font.size = bold, Pt(size)
    return par


for k, (name, sap) in enumerate(MEMBERS):
    if k:
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    p("Peer-Assessment Sheet", 16, True, WD_ALIGN_PARAGRAPH.CENTER, 2)
    p("CSAI4014 AISR  |  Project P05  |  Group G06  |  Batch B1", 12, False, WD_ALIGN_PARAGRAPH.CENTER, 2)
    p("Hospital Delivery Robot with Probabilistic Roadmap (PRM) Path Planning in CoppeliaSim", 11, False,
      WD_ALIGN_PARAGRAPH.CENTER, 14)
    par = p("Member filling this sheet (name, SAP ID): ", 12, True)
    par.add_run(f"{name} ({sap})").bold = False
    p("Give each team-mate a score from 1 (poor) to 5 (excellent) in every column. Fill this sheet on "
      "your own; do not discuss scores.", 11, after=10)
    mates = [m for m in MEMBERS if m[0] != name]
    t = d.add_table(rows=5, cols=6)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    heads = ["No.", "Team-mate name and SAP ID", "Contribution (1-5)", "Reliability / on time (1-5)",
             "Helped others learn (1-5)", "Quality of work (1-5)"]
    widths = [1.0, 4.2, 2.8, 2.6, 2.4, 2.4]
    for j, h in enumerate(heads):
        c = t.cell(0, j)
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold, r.font.size = True, Pt(10.5)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, (mn, ms) in enumerate(mates, 1):
        t.cell(i, 0).paragraphs[0].add_run(str(i)).font.size = Pt(11)
        t.cell(i, 1).paragraphs[0].add_run(f"{mn} ({ms})").font.size = Pt(11)
        t.rows[i].height = Cm(1.4)
    t.autofit = False
    for gc, w in zip(t._tbl.tblGrid.iterchildren(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(Cm(w).twips)))
    for row in t.rows:
        for j, w in enumerate(widths):
            row.cells[j].width = Cm(w)
    p("", after=20)
    p("Comments (optional):", 12, True, after=4)
    for _ in range(4):
        p("_" * 72, 12, after=2)
    p("", after=24)
    p("Signature: ______________________          Date: ____ / 11 / 2026", 12)

d.save(OUT)
print("saved", OUT)
