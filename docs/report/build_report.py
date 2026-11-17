"""Build the project report inside the official AISR sample .docx template.

    python3 docs/report/build_report.py SAMPLE.docx OUT.docx [pages.json]

The title page, page border, fonts, margins and page-number sections of the
sample are kept; everything else is replaced. pages.json (optional) maps
headings/captions to page labels for the Index and the Lists; it is produced
by docs/report/paginate.py after a first PDF export.

Text in yellow highlight = must be filled or confirmed by the team before printing.
"""

import copy
import json
import os
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

SAMPLE, OUT = sys.argv[1], sys.argv[2]
PAGES = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
RES = os.path.join(ROOT, "results")
J = lambda n: json.load(open(os.path.join(RES, n)))  # noqa: E731

TITLE = "Hospital Delivery Robot with Probabilistic Roadmap (PRM) Path Planning in CoppeliaSim"
MEMBERS = [("Mihika", "500122055"), ("Divyanshu Dhyani", "500122522"),
           ("Disha Rastogi", "500119681"), ("Sumit Malhotra", "500123752"),
           ("Prachi Chetan Padodara", "500126371")]
REPO = "https://github.com/MIHIKA06/Hospital-Delivery-Robot-with-Probabilistic-Roadmap-PRM-"

BODY_HEADS = ["1.  Introduction", "2.  Problem Statement and Objectives", "3.  Literature and Industry Review",
              "4.  Novelty", "5.  Syllabus Mapping and Theory", "6.  System Design",
              "7.  Methodology and Algorithms", "8.  Simulation Setup", "9.  Results and Analysis",
              "10.  Contribution", "11.  Co-learning Reflection", "12.  Conclusion and Future Scope",
              "References", "Appendix: Links and Logs"]

E1, E2, E3, E4, E5, E6 = (J("E1_samplers.json"), J("E2_prm_vs_rrt.json"), J("E3_dispatch.json"),
                          J("E4_controller.json"), J("E5_blocked.json"), J("E6_coppeliasim.json"))

d = docx.Document(SAMPLE)
P = d.paragraphs
body = d.element.body
kids = list(body.iterchildren())
TAB_TEMPLATE = copy.deepcopy(P[27]._p.pPr)       # index line with dot leader
REF_TEMPLATE = copy.deepcopy(P[104]._p.pPr)      # reference with hanging indent
ITEM_TEMPLATE = copy.deepcopy(P[60]._p.pPr)      # numbered item


def set_text(par, text):
    runs = par.runs
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


# ------------------------------------------------------------------ title page
set_text(P[3], TITLE)
for i, v in ((7, "P05"), (8, "G06"), (9, "B1")):
    P[i].runs[-1].text = "\t" + v          # keep the bold label run, change only the value
set_text(P[15], "Academic Year 2026-2027   |   November 2026")
t0 = d.tables[0]
for r, (name, sap) in enumerate(MEMBERS, 1):
    t0.cell(r, 1).paragraphs[0].runs[0].text = name
    t0.cell(r, 2).paragraphs[0].runs[0].text = sap

# ------------------------------------------------------------------ declaration
set_text(P[18], f"We declare that this project report titled “{TITLE}” is our own work, carried "
         "out for the course CSAI4014 Algorithms for Intelligent Systems and Robotics. The code, results "
         "and text are original, and all sources used are cited in the References.")
t1 = d.tables[1]
for r, (name, sap) in enumerate(MEMBERS, 1):
    t1.cell(r, 0).paragraphs[0].runs[0].text = name
    t1.cell(r, 1).paragraphs[0].runs[0].text = sap

# ------------------------------------------------------------------ clear old content
front_end = kids[56]                       # paragraph holding the front-matter sectPr
body_sect = kids[-1]                       # final sectPr
abstract_heading = P[22]._p
start = kids.index(abstract_heading)
for el in kids[start:56]:
    body.remove(el)
# keep the sectPr paragraph of section 2 but empty its text
for r in list(front_end.iter(qn("w:r"))):
    r.getparent().remove(r)
for el in kids[57:-1]:
    body.remove(el)

ANCHOR = [front_end]                       # insert new content before this element


def place(el):
    ANCHOR[0].addprevious(el)
    return el


def new_par(style=None):
    p = d.add_paragraph(style=style)
    place(p._p)
    return p


def runs(p, text, size=None, italic=False):
    """**bold** and ==highlight== markup."""
    import re
    for tok in re.split(r"(\*\*.+?\*\*|==.+?==)", text):
        if not tok:
            continue
        if tok.startswith("**"):
            r = p.add_run(tok[2:-2]); r.bold = True
        elif tok.startswith("=="):
            r = p.add_run(tok[2:-2]); r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        else:
            r = p.add_run(tok)
        if size:
            r.font.size = Pt(size)
        if italic:
            r.italic = True
    return p


def page_break():
    p = new_par()
    p.add_run().add_break(WD_BREAK.PAGE)


def H1(text):
    p = new_par("Heading 1")
    p.add_run(text)
    return p


def H2(text):
    p = new_par()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run(text); r.bold = True; r.font.size = Pt(12)
    return p


def para(text):
    p = new_par()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return runs(p, text)


def items(lst, numbered=True):
    for i, t in enumerate(lst, 1):
        p = new_par()
        p._p.insert(0, copy.deepcopy(ITEM_TEMPLATE))
        runs(p, (f"{i}.  " if numbered else "•  ") + t)


def code(lines):
    for ln in lines:
        p = new_par()
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Cm(0.8)
        r = p.add_run(ln if ln else " ")
        r.font.name = "Courier New"
        r._r.rPr.rFonts.set(qn("w:hAnsi"), "Courier New")
        r.font.size = Pt(10)
    new_par().paragraph_format.space_after = Pt(0)


def eq(text, n):
    p = new_par()
    pf = p.paragraph_format
    pf.tab_stops.add_tab_stop(Cm(7.7), alignment=1)
    pf.tab_stops.add_tab_stop(Cm(15.4), alignment=2)
    r = p.add_run("\t" + text); r.italic = True
    p.add_run(f"\t({n})")


FIG = [0]
TAB = [0]
FIGS, TABS = [], []


def figure(path, width_cm, caption):
    FIG[0] += 1
    p = new_par()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(os.path.join(RES, path), width=Cm(width_cm))
    c = new_par("Caption")
    c.add_run(f"Figure {FIG[0]}: ")
    c.add_run(caption)
    FIGS.append(f"Figure {FIG[0]}:  {caption}")
    return FIG[0]


def table(rows, caption, widths=None, size=10.5):
    TAB[0] += 1
    c = new_par("Caption")
    c.paragraph_format.keep_with_next = True
    c.add_run(f"Table {TAB[0]}: ")
    c.add_run(caption)
    TABS.append(f"Table {TAB[0]}:  {caption}")
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = 1
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cp = cell.paragraphs[0]
            cp.paragraph_format.line_spacing = 1.15
            cp.paragraph_format.space_after = Pt(2)
            cp.paragraph_format.space_before = Pt(2)
            if i == 0:
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            runs(cp, str(val), size=size)
            if i == 0:
                for r in cp.runs:
                    r.bold = True
    if widths:
        set_widths(t, widths)
    place(t._tbl)
    sp = new_par()
    sp.paragraph_format.space_after = Pt(2)
    return TAB[0]


def set_widths(t, widths):
    """Fixed column widths that both Word and LibreOffice respect."""
    t.autofit = False
    grid = t._tbl.tblGrid
    for gc, w in zip(grid.iterchildren(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(Cm(w).twips)))
    for row in t.rows:
        for j, w in enumerate(widths):
            row.cells[j].width = Cm(w)


def toc_line(text, key, bold=False):
    p = new_par()
    p._p.insert(0, copy.deepcopy(TAB_TEMPLATE))
    r = p.add_run(f"{text}\t{PAGES.get(key, '#')}")
    r.bold = bold


def fmt(x, n=1):
    return f"{x:.{n}f}"


# ================================================================== FRONT MATTER
# (the sample's "Date ... Place" line already ends with a page break)
H1("Abstract")
para("Hospitals move medicines, laboratory samples and supplies between departments many times a day, "
     "and this repetitive transport takes nurses and porters away from patient care. This project builds "
     "a simulated autonomous delivery robot for a hospital floor that plans its routes with a "
     "Probabilistic Roadmap (PRM). The roadmap is built once over the floor plan and reused for every "
     "order between the pharmacy, laboratory, wards, ICU and emergency department. A door-seeded sampler "
     "solves the narrow-doorway problem, and a local repair step updates the roadmap when a corridor is "
     "blocked. A Pioneer P3-DX robot in CoppeliaSim follows each route with a PID heading controller. Staff "
     "send orders from a Python command-line client over the ZeroMQ remote API; the client serves urgent "
     "orders first and provides status, cancel, block and emergency-stop commands. The door-seeded PRM "
     "connected all 72 location pairs on 10 of 10 random roadmaps with only 100 nodes, against 54% for "
     "uniform sampling with 300 nodes. A route query took 0.37 ms against 43.6 ms for an RRT baseline. "
     "Priority dispatch cut the mean waiting time of urgent orders by 52-88%, and in CoppeliaSim the robot "
     "completed every test delivery with a 2-4 cm RMS tracking error.")
para("**Keywords:** probabilistic roadmap, path planning, hospital delivery robot, CoppeliaSim, "
     "PID control, priority scheduling.")

page_break()
H1("Index")
for text, key in [("Declaration", "Declaration"), ("Abstract", "Abstract"),
                  ("List of Figures", "List of Figures"), ("List of Tables", "List of Figures"),
                  ("Writing Allocation", "Writing Allocation")]:
    toc_line(text, key, bold=True)

for h in BODY_HEADS:
    toc_line(h, h, bold=True)

LISTS_ANCHOR = None
page_break()
H1("List of Figures")
fig_list_anchor = new_par()           # filled at the end, when all figures are known
H1("List of Tables")
tab_list_anchor = new_par()

page_break()
H1("Writing Allocation")
ALL_WRITTEN = "Abstract, 1-9, 12, 13 (References), Appendix"
# (member, index, sections written, sections reviewed): the truthful record of who wrote what
WA = [("M1", 0, ALL_WRITTEN, ""), ("M2", 1, "None", "3, 4"), ("M3", 2, "None", "5, 7"),
      ("M4", 3, "None", "6, 8"), ("M5", 4, "None", "9, 12")]
SEC_OF = {"M1": ["Abstract"] + [h for h in BODY_HEADS
                                  if not h.startswith(("10.", "11."))]}


def section_pages(member):
    """Approximate pages per member from the section start pages of the last PDF."""
    if member not in SEC_OF:
        return "-"
    if not PAGES:
        return "#"
    total = 0.0
    for h in SEC_OF[member]:
        if h == "Abstract":
            total += 1
            continue
        i = BODY_HEADS.index(h)
        start = int(PAGES[h])
        end = int(PAGES[BODY_HEADS[i + 1]]) if i + 1 < len(BODY_HEADS) else int(PAGES["_last"]) + 1
        total += max(0.5, end - start)
    return f"{total:g}"


t = d.add_table(rows=7, cols=4)
t.style = "Table Grid"
t.alignment = 1
hdr = ["Member", "Name and SAP ID", "Sections written (reviewed)", "Pages"]
for j, h in enumerate(hdr):
    runs(t.cell(0, j).paragraphs[0], f"**{h}**", size=11)
for i, (m, k, wrote, reviewed) in enumerate(WA, 1):
    runs(t.cell(i, 0).paragraphs[0], m, size=11)
    runs(t.cell(i, 1).paragraphs[0], f"{MEMBERS[k][0]} ({MEMBERS[k][1]})", size=11)
    runs(t.cell(i, 2).paragraphs[0], wrote + (f" (reviewed {reviewed})" if reviewed else ""), size=11)
    runs(t.cell(i, 3).paragraphs[0], section_pages(m), size=11)
runs(t.cell(6, 0).paragraphs[0], "All", size=11)
runs(t.cell(6, 1).paragraphs[0], "Every member", size=11)
runs(t.cell(6, 2).paragraphs[0], "10 (own row), 11 (own reflection), Declaration", size=11)
runs(t.cell(6, 3).paragraphs[0], "-", size=11)
set_widths(t, (1.6, 5.2, 6.4, 1.6))
place(t._tbl)

# ================================================================== BODY
ANCHOR[0] = body_sect
first = H1("1.  Introduction")
para("A hospital is a busy logistics system. Every day, medicines travel from the pharmacy to the wards, "
     "blood and tissue samples travel from the wards to the laboratory, and linen, meals and documents "
     "move between departments. Most of this transport is still done on foot by nurses, ward assistants "
     "and porters. It is repetitive work, it interrupts clinical tasks, and it must be done on time: a "
     "delayed antibiotic dose or a sample that reaches the laboratory late can directly affect a patient.")
para("Autonomous mobile robots offer a way to take over this routine transport. One of the first commercial "
     "examples was HelpMate, a courier robot that carried meals, medicines and records along hospital "
     "corridors in the 1990s [1]. Today, tug-style robots and autonomous mobile robots (AMRs) from several "
     "manufacturers tow carts and carry locked medicine drawers in hospitals around the world [2]. The "
     "COVID-19 pandemic further increased interest in such robots, because they reduce the number of "
     "person-to-person contacts needed to move supplies inside isolation wards.")
para("For a delivery robot, the central question is asked again and again: how do I get from my current "
     "position to the destination without hitting anything? This is the path planning problem [3]. A "
     "hospital floor gives it some special features. The building layout is known in advance and changes "
     "rarely, so a map can be prepared once. However, the free space contains many narrow passages, such as "
     "doorways that are only slightly wider than the robot, and corridors that are partly blocked by beds, "
     "carts and benches. Delivery requests arrive at unpredictable times and between many different pairs "
     "of locations, so the same map is used to plan hundreds of different routes in a day. Finally, not all "
     "requests are equally important: an emergency medicine for the ICU must not wait behind a routine "
     "delivery of files to the reception.")
para("The Probabilistic Roadmap (PRM) method of Kavraki, Švestka, Latombe and Overmars [4] fits this "
     "usage pattern well. In a learning phase, PRM samples random collision-free robot positions over the "
     "map and connects nearby positions with short straight-line motions, forming a graph called the "
     "roadmap. In the query phase, the start and goal of a delivery are connected to the roadmap and the "
     "route is found with a graph search such as A* [5]. The cost of building the roadmap is paid once and "
     "shared by every later delivery, while each individual query is very fast. Single-query planners such "
     "as the Rapidly-exploring Random Tree (RRT) [6] instead grow a new search tree for every request, which "
     "wastes work when the map does not change.")
para("Planning a route is only one part of a useful delivery system. Hospital staff need a simple way to "
     "request deliveries, to see what the robot is doing, to cancel requests and to stop the robot "
     "immediately in an emergency. In industry this is solved with a layered software architecture in "
     "which an operator interface, a task dispatcher, a motion planner and a low-level controller are "
     "separate components that exchange messages, as popularised by the Robot Operating System (ROS) [7]. "
     "Robot simulators such as CoppeliaSim [8] allow such an architecture to be developed and tested "
     "safely before it is moved to real hardware, and they give external programs access to the simulated "
     "robot through a remote API based on the ZeroMQ messaging library [9].")
para("In this project we build a complete hospital delivery system around PRM in CoppeliaSim. It consists "
     "of (i) a 12 m × 12 m hospital floor with a pharmacy, a laboratory, a reception, three wards, an "
     "ICU and an emergency department; (ii) a PRM planner with three sampling strategies, A* search, path "
     "smoothing and local repair when a corridor is blocked; (iii) a PID path-following controller for a "
     "differential-drive Pioneer P3-DX robot; (iv) a Python command-line client through which delivery "
     "orders are sent, with a priority queue, status, cancel, block and emergency-stop commands and a log "
     "of every order; and (v) a quantitative evaluation, including a comparison with an RRT baseline and "
     "with first-come-first-served dispatch.")
para("The rest of the report is organised as follows. Section 2 defines the problem and the objectives. "
     "Section 3 reviews research and industrial solutions, and Section 4 states the novelty of our work. "
     "Section 5 maps the project to the AISR syllabus and presents the theory. Sections 6 to 8 describe the "
     "system design, the algorithms and the simulation set-up. Section 9 presents and discusses the "
     "results, Section 10 lists each member’s contribution, Section 11 gives our co-learning "
     "reflections and Section 12 concludes the report.")

H1("2.  Problem Statement and Objectives")
para("**Problem statement.** A differential-drive delivery robot operates on a single, known floor of a "
     "hospital. Hospital staff send delivery orders of the form “collect item I at location A and "
     "deliver it to location B” from a Python command-line client, at arbitrary times; each order is "
     "either normal or urgent. For every order the system must (a) plan a collision-free route from the "
     "robot’s current position to the pickup location and then to the drop-off location, using a "
     "Probabilistic Roadmap built over the floor plan; (b) drive the robot along the route in the "
     "CoppeliaSim simulator; and (c) decide the order in which waiting requests are served so that urgent "
     "deliveries are not delayed by routine ones. Staff must be able to query the robot’s status, cancel "
     "a waiting order, mark a blocked area and trigger an emergency stop at any time.")
para("**Objectives.** The project has five measurable objectives:")
items(["**Route planning:** build a PRM that finds a collision-free route between every ordered pair of "
       "the nine named locations (72 pairs) on at least 95% of random roadmaps, with at most 300 nodes.",
       "**Planning speed:** answer a route query from the existing roadmap in under 10 ms on average, and "
       "show quantitatively that roadmap reuse is faster than planning each order with an RRT baseline.",
       "**Path execution:** follow every planned route in CoppeliaSim to within 0.10 m of the goal with zero "
       "collisions and an RMS cross-track error below 5 cm.",
       "**Order handling:** accept, queue, cancel and execute orders from a command-line client over the "
       "ZeroMQ remote API, with an emergency stop that halts the robot within 0.5 s.",
       "**Priority dispatch:** reduce the mean waiting time of urgent orders by at least 30% compared with "
       "first-come-first-served (FCFS) dispatch for the same stream of orders."])
para("**Assumptions and limits.** The robot works on one flat floor; lifts and stairs are not modelled. The "
     "floor plan is known, and walls and furniture do not move during a run. The robot pose is read from the "
     "simulator (ideal localisation); in the offline controller study we add heading noise and wheel slip "
     "instead. People are not simulated; a blocked corridor is modelled as a new static obstacle reported "
     "with the block command. The robot carries one order at a time, and loading and unloading are not "
     "simulated physically. All obstacles are axis-aligned rectangles and the robot is modelled as a disc "
     "of radius 0.30 m.")

H1("3.  Literature and Industry Review")
para("**Sampling-based planning.** The probabilistic roadmap was introduced by Kavraki et al. for robots "
     "with many degrees of freedom [4]. It is probabilistically complete: if a path exists, the probability "
     "of finding it tends to one as the number of samples grows [3]. Its well-known weakness is the "
     "narrow-passage problem. Uniform samples rarely fall inside thin gaps such as doorways, so rooms stay "
     "disconnected from the rest of the roadmap. Hsu et al. proposed the bridge test, which keeps the "
     "midpoint of two colliding samples when the midpoint itself is free, so that nodes appear inside "
     "narrow gaps [10]. Boor et al. use Gaussian sampling to concentrate nodes near obstacle surfaces [11]. "
     "Both methods are general but spend many samples near every obstacle surface, not only in the gaps "
     "that matter.")
para("**Single-query planners.** The Rapidly-exploring Random Tree (RRT) of LaValle and Kuffner grows a tree "
     "from the start towards random samples until it reaches the goal [6]. It needs no learning phase but "
     "repeats its work for every query and returns jagged paths. RRT* by Karaman and Frazzoli adds rewiring "
     "and converges to optimal paths, at a higher cost per query [12]. The Open Motion Planning Library "
     "(OMPL) of Şucan et al. provides PRM, RRT and many variants and is available inside CoppeliaSim as "
     "a plugin [13].")
para("**Changing environments.** A hospital corridor can be blocked by a bed or a cleaning cart. Lazy PRM "
     "postpones collision checks until a path is used, so invalid edges can be discovered and removed "
     "cheaply [14]. Jaillet and Siméon maintain a roadmap for dynamically changing environments by "
     "invalidating and repairing only the affected parts [15]. We follow the same idea in a simple form.")
para("**Path following and architecture.** Differential-drive kinematics and path-tracking controllers are "
     "described in standard texts [16]. The pure-pursuit tracker steers towards a look-ahead point on the "
     "path [17], and PID control [18] is the most widely used feedback law in industry. ROS popularised a "
     "layered architecture in which user interface, task manager, planner and controller are separate "
     "processes [7].")
para("**Industry.** Hospital courier robots such as HelpMate [1] and the Aethon TUG [2] use a known building "
     "map, plan routes on it, and accept jobs from staff through a touch screen or a hospital information "
     "system. Commercial products are closed, so the planning and dispatching methods cannot be studied or "
     "compared. Table 1 summarises the approaches and the gap that our work addresses.")
table([["Approach", "Strength", "Limitation for hospital delivery"],
       ["PRM, uniform sampling [4]", "Roadmap reused for all queries; fast queries", "Misses narrow doorways unless very many samples are used"],
       ["Bridge test / Gaussian sampling [10], [11]", "More nodes in narrow passages", "Samples spent near all walls; still not reliable at small n"],
       ["RRT / RRT* [6], [12]", "No learning phase; good for one-off queries", "Work repeated for every order; slower per query"],
       ["Lazy / dynamic PRM [14], [15]", "Cheap update when the map changes", "Research code; not combined with order dispatch"],
       ["Commercial hospital AMRs [1], [2]", "Proven in real hospitals", "Closed; methods and dispatching rules not published"],
       ["This work", "Door-seeded PRM, local repair, priority dispatch, open CLI", "Simulation only; ideal localisation; no people"]],
      "Comparison of existing approaches", widths=[4.4, 5.0, 5.8])

H1("4.  Novelty")
e1d = {(r["sampler"], r["n"]): r for r in E1}
para("Compared with the textbook PRM example and the solutions reviewed in Section 3, our work adds the "
     "following. Each point is supported by our own results in Section 9.")
items([f"**Door-seeded sampling.** The planner uses the known floor plan to put roadmap nodes in and on "
       f"both sides of every doorway before it samples the rest of the map. With only 100 nodes it connected "
       f"all 72 location pairs on 10 of 10 random roadmaps. Uniform sampling reached "
       f"{fmt(e1d[('uniform', 300)]['success_pct'])}% and bridge-test sampling "
       f"{fmt(e1d[('bridge', 300)]['success_pct'])}% with 300 nodes (Table 7, Figure 4).",
       f"**Local roadmap repair for blocked corridors.** When staff report a blocked area, the planner removes "
       f"only the nodes and edges that the obstacle invalidates and adds 40 new samples around it. All 72 routes "
       f"stayed available in three blockage scenarios, and the repair took about 3 ms, roughly 8 times "
       f"faster than rebuilding the roadmap (Table 11, Figure 9).",
       f"**Priority-aware dispatch combined with PRM planning.** Urgent orders are served first, which cut "
       f"their mean waiting time by 52%, 79% and 88% at low, medium and high load compared with FCFS "
       f"(Table 9, Figure 7). We also report the cost: normal orders wait longer.",
       f"**An open, scriptable command-line architecture.** Orders, status, cancel, block and emergency stop are "
       f"sent from a Python shell over the ZeroMQ remote API, and every order is logged. The same client runs "
       f"on the simulator or in a dry-run mode, and the measured emergency-stop latency was "
       f"{min(E6['estop_latency_s'])}-{max(E6['estop_latency_s'])} s (Section 9.6).",
       f"**Quantified benefit of roadmap reuse.** On identical queries the PRM answered in "
       f"{fmt(E2['PRM (door, n=300)']['query_ms_mean'], 2)} ms against {fmt(E2['RRT']['query_ms_mean'])} ms "
       f"for RRT, with 4% shorter paths. Over 200 orders this was 0.11 s against 9.3 s of total planning "
       f"time (Table 8, Figure 6)."])

H1("5.  Syllabus Mapping and Theory")
para("Table 2 maps each AISR syllabus topic used in this project to the part of the system where it "
     "is used. The theory behind the main topics is given in Sections 5.1 to 5.5.")
table([["AISR syllabus topic", "Where it is used in this project"],
       ["Probabilistic path planning", "PRM learning and query phases, samplers, roadmap repair (planner/prm.py)"],
       ["Planning to move", "A* search on the roadmap, path smoothing, pickup and drop-off legs"],
       ["Robotic software architectures", "Client - queue - dispatcher - planner - controller layers over ZeroMQ"],
       ["Mobile ground robots", "Differential-drive Pioneer P3-DX, kinematic model, wheel speed limits"],
       ["Open- and closed-loop control", "PID heading controller with feedback of the robot pose"],
       ["Stability and performance", "Cross-track error, settling at corners, tuning of PID gains"],
       ["Intelligent agents / decision making", "Priority dispatch of orders, emergency stop, re-planning"]],
      "Mapping of AISR syllabus topics to the project", widths=[5.0, 10.2])
H2("5.1 Configuration space")
para("The robot is modelled as a disc of radius r = 0.30 m. Instead of checking the disc against every "
     "obstacle, every obstacle rectangle is enlarged by r on all sides. The robot can then be treated as a "
     "point (x, y) in this configuration space (C-space) [3]. A point is free if it lies outside all "
     "enlarged rectangles and inside the floor, and a straight edge is free if it does not cross any "
     "enlarged rectangle; we test this exactly with the Liang–Barsky segment clipping test. The 1.0 m "
     "doors leave a free gap of only 1.0 − 2r = 0.4 m in C-space, which is the narrow passage of this "
     "problem.")
H2("5.2 Probabilistic roadmap")
para("The roadmap is an undirected graph G = (V, E). V contains n collision-free configurations, and E "
     "contains a free straight edge between each node and up to k of its nearest neighbours within a "
     "distance d_max. Each edge has the Euclidean length as its cost. A query connects the start s and the "
     "goal g to their nearest visible nodes and searches G with A* [5], which expands nodes in order of")
eq("f(v) = g(v) + h(v),    h(v) = ‖v − g‖₂", 1)
para("where g(v) is the cost of the best known path from s to v. Because the straight-line distance h never "
     "over-estimates the remaining path length, A* returns the shortest path in the roadmap. PRM is "
     "probabilistically complete: the probability that it fails to find an existing path decreases "
     "exponentially with n, but the rate depends on the width of the narrowest passage [3], [4]. This is "
     "why the sampling strategy matters so much for doorways.")
H2("5.3 Differential-drive kinematics")
para("The Pioneer P3-DX has two driven wheels of radius r_w = 0.0975 m separated by b = 0.331 m. With wheel "
     "speeds ω_R and ω_L the forward speed v and turn rate ω are [16]")
eq("v = r_w (ω_R + ω_L) / 2,      ω = r_w (ω_R − ω_L) / b", 2)
para("and the pose (x, y, θ) evolves as")
eq("ẋ = v cos θ,    ẏ = v sin θ,    θ̇ = ω", 3)
para("The controller computes (v, ω) and inverts Eq. (2): ω_R = (v + ωb/2)/r_w and "
     "ω_L = (v − ωb/2)/r_w, scaled down together if either exceeds the motor limit of 2π rad/s.")
H2("5.4 PID heading control")
para("The heading error e(t) is the angle between the robot heading and the direction to a carrot point "
     "0.35 m ahead on the current path segment. The turn rate is computed with a PID law [18]")
eq("ω(t) = K_p e(t) + K_i ∫ e(τ) dτ + K_d de(t)/dt", 4)
para("with K_p = 2.2, K_i = 0.05 and K_d = 0.25 and an anti-windup limit on the integral. The forward speed "
     "is reduced as v = v_max cos² e, so that the robot slows down when it is misaligned and turns in "
     "place when |e| > 50°. The cross-track error, the perpendicular distance from the robot to the "
     "current segment, is used to evaluate tracking performance.")
H2("5.5 Priority dispatch")
para("Waiting orders are kept in a binary heap ordered by the key (priority, arrival number), with priority "
     "0 for urgent and 1 for normal orders. Removing the next order takes O(log m) time for m waiting "
     "orders. With all priorities set equal, the same queue becomes first-come-first-served, which is our "
     "baseline.")

H1("6.  System Design")
para("Figure 1 shows the full system. Staff type commands in the command-line client. Delivery orders go "
     "into the order queue; status, cancel, block and stop commands act immediately. A dispatcher thread "
     "takes the next order, asks the PRM planner for a route from the robot’s position to the pickup and "
     "then to the drop-off, and passes each route to the PID path follower. The follower reads the robot "
     "pose and sets the wheel speeds in CoppeliaSim through the ZeroMQ remote API. Every finished order is "
     "written to a CSV log, which we use for the results.")
figure("fig_architecture.png", 15.0, "System architecture of the hospital delivery robot")
H2("6.1 Robot model")
para("The robot is the Pioneer P3-DX model supplied with CoppeliaSim: a differential-drive base about "
     "0.45 m × 0.38 m with two driven wheels and a castor. Its built-in demonstration script was removed so "
     "that only our controller commands the motors. The actuators are the left and right wheel motors "
     "(velocity control). The sensor used by the controller is the robot pose, read from the simulator; "
     "this stands for the output of a localisation module on a real robot.")
H2("6.2 Environment model")
para("The hospital floor (Figure 2) is 12 m × 12 m. A 4 m wide central corridor connects the pharmacy and "
     "the laboratory on the left with wards 1-3 and the ICU on the right. Every room has a 1.0 m door. "
     "Furniture such as shelves, beds, a reception desk, a trolley and a bench forms additional obstacles. "
     "The map is defined once in planner/hospital_map.py, and the CoppeliaSim scene is generated from the "
     "same file, so the planner and the simulator always agree. Table 3 lists the nine named locations.")
figure("fig_scene_3d.png", 13.5, "Hospital scene in CoppeliaSim generated from the floor-plan map "
       "(blue discs: delivery locations; robot at home)")
table([["Location", "(x, y) m", "Location", "(x, y) m"],
       ["home", "(0.0, 0.0)", "ward 1", "(4.0, 4.0)"],
       ["pharmacy", "(−4.0, 3.0)", "ward 2", "(4.0, 1.5)"],
       ["laboratory", "(−4.0, −3.0)", "ward 3", "(4.0, −1.5)"],
       ["reception", "(0.0, −4.0)", "ICU", "(4.0, −4.0)"],
       ["emergency", "(−1.5, 4.5)", "", ""]],
      "Named delivery locations", widths=[3.0, 3.4, 3.0, 3.4])
H2("6.3 Software architecture")
para("Table 4 lists the software modules, their files in the GitHub repository and their roles.")
table([["Module", "Files", "Role"],
       ["Command-line client", "client/client.py, orders.py", "Shell commands, priority/FCFS order queue"],
       ["Dispatcher", "client/dispatcher.py", "Serves orders: plan and drive each leg, log results"],
       ["Simulator bridge", "client/sim_bridge.py", "ZeroMQ connection to CoppeliaSim; dry-run robot"],
       ["PRM planner", "planner/prm.py, hospital_map.py", "Map, samplers, roadmap, A*, smoothing, repair"],
       ["Controller", "controller/controller.py", "PID path follower, wheel speeds, safety aborts"],
       ["Baseline", "baseline/rrt.py", "Single-query RRT for comparison"],
       ["Scene and tools", "tools/build_hospital_scene.py", "Builds scene/hospital.ttt from the map"],
       ["Experiments", "experiments/*.py", "Experiments E1-E6 and figures"]],
      "Software modules (GitHub repository)", widths=[3.6, 5.2, 6.4])
para("The modules communicate only through small interfaces: the planner offers plan(start, goal), which "
     "returns a list of waypoints, and the controller offers follow(sim, robot, path, should_stop), which "
     "returns True on arrival. This made it possible to develop and test each module on its own, to swap "
     "the PRM for the RRT baseline with one command-line option, and to run the client without the "
     "simulator in a dry-run mode.")

H1("7.  Methodology and Algorithms")
para("Figure 3 shows the two phases of the planner. The learning phase runs once when the client starts "
     "(about 30 ms); the query phase runs for every leg of every order.")
figure("fig_flowchart.png", 8.5, "Flowchart of the PRM planner")
H2("7.1 Roadmap construction")
code(["Algorithm 1: BuildRoadmap(map, r, n, k, d_max)",
      "  C <- inflate every obstacle of map by r",
      "  V <- {}",
      "  for each door (x, y) in map:                 # door-seeded sampler",
      "      for p in {(x-0.6, y), (x, y), (x+0.6, y)}:",
      "          if Free(p, C): V <- V + {p}",
      "  while |V| < n:",
      "      p <- uniform random point in the floor",
      "      if Free(p, C): V <- V + {p}",
      "  for each v in V:",
      "      for u in k nearest nodes of v with |u - v| <= d_max:",
      "          if EdgeFree(v, u, C): add edge (v, u) with cost |u - v|",
      "  return G = (V, E)"])
para("We use n = 300, k = 10 and d_max = 3 m. The uniform sampler omits the door step. The bridge sampler "
     "first draws 30% of the nodes with the bridge test [10]: two points a and b ~ N(a, 0.6²) that are "
     "both in collision, keeping their midpoint if it is free.")
H2("7.2 Route query and smoothing")
code(["Algorithm 2: Query(G, s, g)",
      "  if EdgeFree(s, g): return [s, g]",
      "  connect s and g to their k nearest visible nodes",
      "  path <- A*(G, s, g) with h(v) = |v - g|",
      "  if no path: return None",
      "  # greedy shortcut smoothing",
      "  out <- [path[0]];  i <- 0",
      "  while i < last:",
      "      j <- last;  while j > i+1 and not EdgeFree(path[i], path[j]): j <- j-1",
      "      out <- out + [path[j]];  i <- j",
      "  return out"])
H2("7.3 Local repair for a blocked area")
code(["Algorithm 3: Block(G, R)          # R = new obstacle rectangle",
      "  add R to the map;  R' <- R inflated by r",
      "  delete every node inside R' and its edges",
      "  delete every edge that crosses R'",
      "  draw 40 random points in a 1 m band around R'",
      "  add the free ones as nodes and connect them (k nearest, EdgeFree)"])
para("Step 3 alone can cut the roadmap if all nodes beside the obstacle are removed, even when a gap remains. "
     "Our first version had this problem (only 36 of 72 routes remained in one test). The resampling step "
     "fixed it, which is why we added it.")
H2("7.4 Path following")
para("The controller follows the waypoints one segment at a time. At every 50 ms simulation step it (1) "
     "projects the robot onto the current segment and places a carrot 0.35 m ahead on that segment, (2) "
     "computes the heading error to the carrot and the PID turn rate of Eq. (4), (3) sets v = v_max cos² e "
     "with v_max = 0.45 m/s, slowing to 0.08 m/s near the goal, and (4) converts (v, ω) to wheel speeds. "
     "Because the carrot never leaves the current segment, the robot does not cut corners near door frames. "
     "It switches to the next segment within 0.15 m of the segment end and stops within 0.10 m of the goal. "
     "It aborts and stops the wheels on an emergency stop, after 8 s without progress or more than 0.8 m off "
     "the path. Table 5 lists the tuned parameters.")
table([["Parameter", "Value", "Parameter", "Value"],
       ["K_p, K_i, K_d", "2.2, 0.05, 0.25", "Look-ahead (carrot)", "0.35 m"],
       ["Cruise speed v_max", "0.45 m/s", "Turn-rate limit", "1.6 rad/s"],
       ["Turn in place above", "50°", "Goal tolerance", "0.10 m"],
       ["Segment switch", "0.15 m", "Control period", "50 ms"]],
      "Controller parameters", widths=[4.2, 3.4, 4.2, 3.4])
para("The gains were tuned by hand on the offline kinematic model (Section 9.4): K_p was raised until the "
     "robot settled on a new segment within about 2 s, K_d was added to damp the overshoot after sharp "
     "corners, and a small K_i removes the steady heading offset caused by wheel slip.")
H2("7.5 Order dispatch")
para("The dispatcher thread repeatedly takes the next order from the queue (urgent first, then by arrival), "
     "plans and drives the leg to the pickup, then the leg to the drop-off, and logs the waiting time, run "
     "time, planning time and path length. Only the dispatcher thread talks to the simulator, because the "
     "ZeroMQ client is not thread-safe; the shell thread only changes shared flags such as the emergency "
     "stop. A lock protects the roadmap so that a block command cannot change it in the middle of a query.")

H1("8.  Simulation Setup")
para("Table 6 lists the simulation platform and all parameters used in the experiments of Section 9.")
table([["Item", "Setting"],
       ["Simulator", "CoppeliaSim Edu 4.10.0 (macOS, Apple silicon), Bullet physics, 50 ms step"],
       ["Robot", "Pioneer P3-DX (built-in model, demo script removed)"],
       ["Language and libraries", "Python 3.9, coppeliasim-zmqremoteapi-client, matplotlib"],
       ["Map", "12 m × 12 m floor, 17 walls, 10 furniture items, 6 doors of 1.0 m, 9 locations"],
       ["PRM", "n = 300, k = 10, d_max = 3 m, robot radius 0.30 m, door-seeded sampler"],
       ["RRT baseline", "step 0.5 m, goal bias 10%, up to 20 000 iterations, same smoothing"],
       ["Dispatch study (E3)", "30 trials × 40 orders, 25% urgent, 0.35 m/s mean speed, 20 s handling"],
       ["Repeatability", "Fixed random seeds; all results in results/*.json"]],
      "Simulation set-up and parameters", widths=[4.2, 11.0])
para("**How to run.** All commands are run from the repository folder:")
code(["pip install -r requirements.txt",
      "python3 tools/build_hospital_scene.py        # builds scene/hospital.ttt (CoppeliaSim open)",
      "python3 -m client                            # client on CoppeliaSim",
      "python3 -m client --dry-run                  # client without the simulator",
      "python3 -m client --planner rrt --fifo       # baselines",
      "python3 -m experiments.run_experiments       # E1-E5 -> results/*.json",
      "python3 -m experiments.make_figures          # figures",
      "python3 tools/test_controller_sim.py --fast  # E6 tour in CoppeliaSim"])
para("Inside the client, an urgent delivery is requested with deliver pharmacy icu --urgent --item insulin; "
     "other commands are status, queue, history, cancel <id>, block <x0> <y0> <x1> <y1>, stop, resume and "
     "quit.")

H1("9.  Results and Analysis")
H2("9.1 Sampling strategies (E1)")
para("Each sampler was run on 10 random seeds for each roadmap size n, and every roadmap was asked for all 72 "
     "ordered location pairs. Table 7 and Figure 4 show the results.")
rows = [["n", "Uniform success", "Bridge success", "Door-seeded success", "Door: full seeds"]]
for n in (50, 100, 200, 300, 500):
    rows.append([n, f"{fmt(e1d[('uniform', n)]['success_pct'])}% ({e1d[('uniform', n)]['full_seeds']}/10)",
                 f"{fmt(e1d[('bridge', n)]['success_pct'])}% ({e1d[('bridge', n)]['full_seeds']}/10)",
                 f"{fmt(e1d[('door', n)]['success_pct'])}%", f"{e1d[('door', n)]['full_seeds']}/10"])
fig_n = FIG[0] + 1
table(rows, "Route success over 72 location pairs (in brackets: seeds with all pairs connected)",
      widths=[1.6, 3.6, 3.6, 3.6, 2.8])
figure("fig_success_vs_n.png", 12.5, "Route success against roadmap size for the three samplers")
para("Uniform sampling failed mainly at the doors: with 300 nodes it connected only 54% of the pairs and never "
     "all of them. The bridge test helped (83%), but half of its roadmaps still missed at least one room. "
     "The door-seeded sampler connected all pairs on every seed from n = 100. Figure 5 shows a door-seeded "
     "roadmap with example routes passing through the doors.")
figure("fig_roadmap_door.png", 11.5, "Door-seeded roadmap (n = 300) and three example routes")
H2("9.2 PRM against RRT (E2)")
a, b = E2["PRM (door, n=300)"], E2["RRT"]
table([["Metric", "PRM (door, n = 300)", "RRT"],
       ["Route success", f"{fmt(a['success_pct'])}%", f"{fmt(b['success_pct'])}%"],
       ["Mean query time", f"{fmt(a['query_ms_mean'], 2)} ms", f"{fmt(b['query_ms_mean'])} ms"],
       ["Worst query time", f"{fmt(a['query_ms_max'], 2)} ms", f"{fmt(b['query_ms_max'], 0)} ms"],
       ["Mean path length", f"{fmt(a['path_len_mean'], 2)} m", f"{fmt(b['path_len_mean'], 2)} m"],
       ["Total time for 72 orders (incl. build)", f"{fmt(a['total_ms_72_orders'], 0)} ms", f"{fmt(b['total_ms_72_orders'], 0)} ms"]],
      "PRM against RRT on the same 72 queries (mean of 5 seeds)", widths=[6.0, 4.4, 4.4])
figure("fig_prm_vs_rrt.png", 12.5, "Cumulative planning time for 200 random orders")
para(f"Both planners found all routes, but each RRT query took about {fmt(b['query_ms_mean'] / a['query_ms_mean'], 0)} "
     f"times longer, and its worst case exceeded one second when the tree had to find a narrow door. Even "
     f"including the 28 ms needed to build the roadmap, the PRM had answered 200 orders in 0.11 s, while RRT "
     f"needed 9.3 s (Figure 6). PRM paths were also about 4% shorter, because A* searches a whole graph while "
     f"RRT keeps the first path it finds. This confirms that a reusable roadmap suits a hospital, where the "
     f"map is fixed and orders are many.")
H2("9.3 Priority dispatch (E3)")
rows = [["Load", "FCFS urgent", "Priority urgent", "Reduction", "FCFS normal", "Priority normal"]]
for l in ("low", "medium", "high"):
    fu, pu = E3[l]["fifo"]["urgent"]["mean"], E3[l]["priority"]["urgent"]["mean"]
    rows.append([l, f"{fmt(fu, 0)} s", f"{fmt(pu, 0)} s", f"{fmt(100 * (fu - pu) / fu, 0)}%",
                 f"{fmt(E3[l]['fifo']['normal']['mean'], 0)} s", f"{fmt(E3[l]['priority']['normal']['mean'], 0)} s"])
table(rows, "Mean waiting time of orders (30 trials of 40 orders, 25% urgent)",
      widths=[1.8, 2.6, 2.8, 2.4, 2.6, 2.8])
figure("fig_dispatch_wait.png", 12.5, "Mean waiting time of urgent and normal orders under FCFS and priority dispatch")
para("We simulated one robot serving random orders whose travel times come from real PRM path lengths. "
     "Priority dispatch reduced the mean waiting time of urgent orders by 52% at low load and by 88% at high "
     "load, and kept it below one minute even when the queue grew long. The price is paid by normal orders, "
     "which waited 18-33% longer, and their worst case grew. In a hospital this trade-off is acceptable for "
     "medicines and samples, but a real system should add ageing (raising the priority of orders that have "
     "waited too long) so that normal orders are never starved.")
H2("9.4 Path following (E4)")
i_, n_ = E4["ideal"], E4["noise_and_slip"]
para("Every one of the 72 PRM routes was followed with the controller on the kinematic model of Eq. (3), "
     "first ideal and then with heading noise and wheel slip. Table 10 summarises the results, and "
     "Figure 8 shows one route in detail.")
table([["Metric (72 routes)", "Ideal model", "With 2° heading noise and 5% wheel slip"],
       ["Routes completed", f"{i_['arrived']}/72", f"{n_['arrived']}/72"],
       ["Mean RMS cross-track error", f"{fmt(100 * i_['rms_mean_m'])} cm", f"{fmt(100 * n_['rms_mean_m'])} cm"],
       ["Largest cross-track error", f"{fmt(100 * i_['max_xte_m'])} cm", f"{fmt(100 * n_['max_xte_m'])} cm"],
       ["Mean final position error", f"{fmt(100 * i_['final_err_mean_m'])} cm", f"{fmt(100 * n_['final_err_mean_m'])} cm"],
       ["Mean travel time", f"{fmt(i_['time_mean_s'])} s", f"{fmt(n_['time_mean_s'])} s"]],
      "Controller performance on the kinematic model", widths=[5.4, 3.6, 6.0])
figure("fig_tracking.png", 15.0, "Example route pharmacy to ICU with noise and slip: path and cross-track error")
para("The controller completed all routes in both conditions with a mean RMS error below 2 cm. The largest "
     "errors (about 15 cm) occur for a moment at sharp corners, where the robot rotates towards the next "
     "segment (the spikes in Figure 8). Noise and slip mainly made the robot slower (+4% travel time), "
     "because the integral term has to correct the slip. The final error of about 10 cm equals the goal "
     "tolerance and could be reduced with a slower final approach.")
H2("9.5 Blocked corridors (E5)")
rows = [["Blocked area", "Nodes / edges removed", "Old routes blocked", "Routes after repair", "Repair", "Rebuild", "Extra length"]]
for r in E5:
    rows.append([r["blocker"], f"{r['nodes_removed']} / {r['edges_removed']}", r["old_routes_now_blocked"],
                 f"{r['success_after']}/72", f"{fmt(r['repair_ms'])} ms", f"{fmt(r['rebuild_ms'])} ms",
                 f"{fmt(r['mean_extra_len_m'], 2)} m"])
table(rows, "Local roadmap repair against full rebuild", widths=[3.6, 2.4, 2.0, 2.1, 1.7, 1.8, 1.8], size=10)
figure("fig_roadmap_door_blocked.png", 11.0, "Roadmap after the lower corridor is blocked (red); routes detour around it")
para("Each blockage invalidated between 13 and 34 of the existing routes, but after the local repair all 72 "
     "routes were available again, with detours of 0.1-1.0 m on average. The repair took about 3 ms against "
     "27 ms for a full rebuild. The difference matters more on larger maps, where rebuilding grows with the "
     "number of nodes while the repair only touches the area around the obstacle.")
H2("9.6 Full system in CoppeliaSim (E6)")
para("Finally, the complete system was run in CoppeliaSim with the hospital scene of Figure 2. Table 12 "
     "lists a nine-leg tour through all locations, planned by the PRM and driven by the PID controller.")
rows = [["Leg (from previous stop)", "Path length", "Sim time", "RMS error", "Max error", "Final error"]]
for leg in E6["tour"]:
    rows.append([f"→ {leg['goal']}", f"{fmt(leg['path_m'], 2)} m", f"{fmt(leg['sim_s'])} s",
                 f"{fmt(100 * leg['rms_xte_m'])} cm", f"{fmt(100 * leg['max_xte_m'])} cm",
                 f"{fmt(100 * leg['end_err_m'])} cm"])
table(rows, "Nine-leg delivery tour in CoppeliaSim with the PRM and PID controller", widths=[4.0, 2.4, 2.2, 2.2, 2.2, 2.2])
para(f"In CoppeliaSim, with full physics and real wheel dynamics, the robot completed all nine legs without "
     f"collision. The RMS cross-track error was 2.2-3.5 cm, the maximum 14 cm at corners, and the final error "
     f"below 10 cm, very close to the offline model. We then sent three orders from the command-line client "
     f"(pharmacy to ward 1, laboratory to ward 3, and an urgent insulin order from the pharmacy to the ICU). "
     f"The urgent order was served first and all three were delivered. In three emergency-stop tests the robot "
     f"stopped {', '.join(str(x) for x in E6['estop_latency_s'])} s after the stop command, well inside the "
     f"0.5 s objective.")
H2("9.7 Discussion")
para("All five objectives of Section 2 were met: 100% route success at n ≤ 300 (objective 1), 0.37 ms per "
     "query (2), arrival within 0.10 m with an RMS error below 5 cm and no collisions (3), a working "
     "command-line client with an emergency stop below 0.1 s (4), and a 52-88% reduction in urgent waiting "
     "time (5). What did not work at first is equally instructive. Uniform PRM sampling was unreliable at the "
     "doors. The first version of the blockage repair could cut the roadmap. The fallback follower we used "
     "before the controller was ready let the robot coast after a stop. The limits of the study are the "
     "ideal localisation, the absence of moving people, and the fact that priority dispatch can delay "
     "normal orders.")

H1("10.  Contribution")
para("Table 13 lists the technical contribution of each member. Every item can be traced to commits in the "
     f"GitHub repository ({REPO}) or to the demonstration video.")
TAB[0] += 1
c = new_par("Caption"); c.paragraph_format.keep_with_next = True
c.add_run(f"Table {TAB[0]}: "); c.add_run("Technical contribution of each member")
TABS.append(f"Table {TAB[0]}:  Technical contribution of each member")
t = d.add_table(rows=6, cols=4)
t.style = "Table Grid"
t.alignment = 1
for j, h in enumerate(["S. No.", "Name and SAP ID", "Technical contribution", "Report sections + signature"]):
    runs(t.cell(0, j).paragraphs[0], f"**{h}**", size=10)
contrib = {0: "Wrote all code: command-line client, order queue (priority and FCFS), dispatcher and ZeroMQ "
              "bridge (client/); PRM planner with door-seeded sampling and local repair (planner/); hospital "
              "scene builder and PID controller (tools/, controller/); RRT baseline; experiments E1-E6 and "
              "figures; integration and testing in CoppeliaSim; presented slides 1-3 in the video.",
           1: "Presented slides 4-6 (existing solutions, novelty, syllabus mapping) in the demonstration "
              "video; reviewed Sections 3 and 4.",
           2: "Presented slides 7-9 (system architecture, robot and environment model, PRM algorithm) in the "
              "demonstration video; reviewed Sections 5 and 7.",
           3: "Presented slides 10-12 (controller, simulation set-up) and ran the live CoppeliaSim demonstration "
              "in the video; reviewed Sections 6 and 8.",
           4: "Presented slides 13-15 (results and team contribution) in the demonstration video; reviewed "
              "Sections 9 and 12."}
sections = {0: "Wrote: " + ALL_WRITTEN, 1: "Reviewed: 3, 4", 2: "Reviewed: 5, 7", 3: "Reviewed: 6, 8",
            4: "Reviewed: 9, 12"}
for i, (name, sap) in enumerate(MEMBERS, 1):
    runs(t.cell(i, 0).paragraphs[0], str(i), size=10)
    runs(t.cell(i, 1).paragraphs[0], f"{name} ({sap})", size=10)
    runs(t.cell(i, 2).paragraphs[0], contrib[i - 1], size=10)
    runs(t.cell(i, 3).paragraphs[0], sections[i - 1], size=10)
set_widths(t, (1.2, 3.6, 7.0, 3.4))
place(t._tbl)
new_par()

H1("11.  Co-learning Reflection")
REFLECTIONS = {
    "Mihika": "I learned CoppeliaSim and its ZeroMQ remote API on my own, starting from a robot that drove off "
              "the edge of the default floor and ending with a full hospital scene generated from our map. "
              "Building the command-line client taught me how to keep a simulator connection in one thread "
              "while the shell stays responsive. When team-mates were unwell or could not run the simulator, I "
              "also wrote the PRM planner and the controller, which made me understand the narrow-door problem "
              "and PID tuning in depth. From the team I learned to agree on small interfaces first, so that "
              "modules fit together. I explained the client, the PRM and the controller to the team so that "
              "everyone can answer questions on the whole system.",
}
for name, _ in MEMBERS:
    first_name = name.split()[0]
    txt = REFLECTIONS.get(name, f"==[5-8 lines written by {first_name}: what I learned on my own, what I "
                                f"learned from team-mates, and what I taught others.]==")
    para(f"**{name}:** {txt}")

H1("12.  Conclusion and Future Scope")
para("We built a complete hospital delivery robot system in CoppeliaSim around a probabilistic roadmap. A "
     "door-seeded sampler made the roadmap reliable in a floor plan with narrow doors, a local repair step "
     "kept it valid when corridors were blocked, and a PID controller drove a Pioneer P3-DX along the "
     "planned routes with a few centimetres of error. Staff control the robot from a command-line client "
     "that serves urgent orders first and can stop the robot in under 0.1 s. Compared with planning every "
     "order with RRT, roadmap reuse made planning more than 100 times faster.")
para("**Industrial use.** The same structure, a building map prepared once, a fast route planner, a "
     "priority job queue and a simple operator interface, is what hospital courier robots and factory "
     "tuggers need. The open, scriptable client could be connected to a hospital information system, which "
     "would create delivery orders automatically when a doctor prescribes a medicine.")
para("**Moving to a real robot.** The planner and the dispatcher are independent of the simulator. On a real "
     "Pioneer or a similar AMR, the simulator bridge would be replaced by a ROS 2 node that reads the pose "
     "from a localisation module (for example AMCL with a lidar) and publishes wheel velocities. A "
     "reactive safety layer would stop or slow the robot for people, and the floor plan would be taken from "
     "the building’s CAD drawings or from a lidar map.")
para("**Future scope.** Future work includes multiple robots with traffic rules at doors, lifts for "
     "multi-floor delivery, ageing of priorities so that normal orders are not starved, a comparison with "
     "CoppeliaSim’s OMPL planners [13], and detection of blocked corridors from the robot’s own "
     "sensors instead of a staff command.")

H1("References")
REFS = [
    "J. M. Evans, “HelpMate: An autonomous mobile robot courier for hospitals,” in Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS), Munich, Germany, 1994, pp. 1695–1700.",
    "Aethon Inc., “TUG autonomous mobile robot for hospitals.” [Online]. Available: https://aethon.com. [Accessed: Nov. 2026].",
    "S. M. LaValle, Planning Algorithms. Cambridge, U.K.: Cambridge Univ. Press, 2006.",
    "L. E. Kavraki, P. Švestka, J.-C. Latombe, and M. H. Overmars, “Probabilistic roadmaps for path planning in high-dimensional configuration spaces,” IEEE Trans. Robot. Autom., vol. 12, no. 4, pp. 566–580, Aug. 1996.",
    "P. E. Hart, N. J. Nilsson, and B. Raphael, “A formal basis for the heuristic determination of minimum cost paths,” IEEE Trans. Syst. Sci. Cybern., vol. 4, no. 2, pp. 100–107, Jul. 1968.",
    "S. M. LaValle and J. J. Kuffner, “Randomized kinodynamic planning,” Int. J. Robot. Res., vol. 20, no. 5, pp. 378–400, May 2001.",
    "M. Quigley et al., “ROS: An open-source Robot Operating System,” in Proc. ICRA Workshop Open Source Softw., Kobe, Japan, 2009.",
    "E. Rohmer, S. P. N. Singh, and M. Freese, “V-REP: A versatile and scalable robot simulation framework,” in Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS), Tokyo, Japan, 2013, pp. 1321–1326.",
    "P. Hintjens, ZeroMQ: Messaging for Many Applications. Sebastopol, CA, USA: O’Reilly Media, 2013.",
    "D. Hsu, T. Jiang, J. Reif, and Z. Sun, “The bridge test for sampling narrow passages with probabilistic roadmap planners,” in Proc. IEEE Int. Conf. Robot. Autom. (ICRA), Taipei, Taiwan, 2003, pp. 4420–4426.",
    "V. Boor, M. H. Overmars, and A. F. van der Stappen, “The Gaussian sampling strategy for probabilistic roadmap planners,” in Proc. IEEE Int. Conf. Robot. Autom. (ICRA), Detroit, MI, USA, 1999, pp. 1018–1023.",
    "S. Karaman and E. Frazzoli, “Sampling-based algorithms for optimal motion planning,” Int. J. Robot. Res., vol. 30, no. 7, pp. 846–894, Jun. 2011.",
    "I. A. Şucan, M. Moll, and L. E. Kavraki, “The Open Motion Planning Library,” IEEE Robot. Autom. Mag., vol. 19, no. 4, pp. 72–82, Dec. 2012.",
    "R. Bohlin and L. E. Kavraki, “Path planning using lazy PRM,” in Proc. IEEE Int. Conf. Robot. Autom. (ICRA), San Francisco, CA, USA, 2000, pp. 521–528.",
    "L. Jaillet and T. Siméon, “A PRM-based motion planner for dynamically changing environments,” in Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS), Sendai, Japan, 2004, pp. 1606–1611.",
    "R. Siegwart, I. R. Nourbakhsh, and D. Scaramuzza, Introduction to Autonomous Mobile Robots, 2nd ed. Cambridge, MA, USA: MIT Press, 2011.",
    "R. C. Coulter, “Implementation of the pure pursuit path tracking algorithm,” Robotics Inst., Carnegie Mellon Univ., Pittsburgh, PA, USA, Tech. Rep. CMU-RI-TR-92-01, 1992.",
    "K. J. Åström and R. M. Murray, Feedback Systems: An Introduction for Scientists and Engineers. Princeton, NJ, USA: Princeton Univ. Press, 2008.",
]
for i, ref in enumerate(REFS, 1):
    p = new_par()
    p._p.insert(0, copy.deepcopy(REF_TEMPLATE))
    p.add_run(f"[{i}]\t{ref}")

H1("Appendix: Links and Logs")
para(f"**GitHub repository:** {REPO}")
para("**YouTube video (Unlisted):** https://youtu.be/S365_Npse0U")
para("**Meeting log.** Table 14 records the team meetings: date, duration, attendees and decisions.")
TAB[0] += 1
c = new_par("Caption"); c.paragraph_format.keep_with_next = True
c.add_run(f"Table {TAB[0]}: "); c.add_run("Meeting log")
TABS.append(f"Table {TAB[0]}:  Meeting log")
t = d.add_table(rows=7, cols=5)
t.style = "Table Grid"
t.alignment = 1
for j, h in enumerate(["No.", "Date", "Duration", "Attendees", "Decisions"]):
    runs(t.cell(0, j).paragraphs[0], f"**{h}**", size=10)
for i in range(1, 7):
    runs(t.cell(i, 0).paragraphs[0], str(i), size=10)
    for j in range(1, 5):
        runs(t.cell(i, j).paragraphs[0], "==  ==", size=10)
set_widths(t, (1.2, 2.4, 2.0, 4.2, 5.4))
place(t._tbl)
new_par()
para("**Peer-assessment sheets:** one sheet per member, in the format of the Project Instructions "
     "(Section 4), filled individually and attached after this page. ==Attach 5 signed sheets.==")

# ------------------------------------------------------------------ lists of figures / tables
def fill_list(anchor, entries):
    for e in entries:
        p = d.add_paragraph()
        p._p.insert(0, copy.deepcopy(TAB_TEMPLATE))
        key = e.split(":")[0]
        p.add_run(f"{e}\t{PAGES.get(key, '#')}")
        anchor._p.addprevious(p._p)
    anchor._p.getparent().remove(anchor._p)


fill_list(fig_list_anchor, FIGS)
fill_list(tab_list_anchor, TABS)

d.core_properties.title = TITLE
d.core_properties.author = "Group G06"
d.save(OUT)
json.dump({"figures": FIGS, "tables": TABS, "heads": BODY_HEADS},
          open(os.path.join(os.path.dirname(OUT), "report_items.json"), "w"), indent=1)
print("saved", OUT, f"({FIG[0]} figures, {TAB[0]} tables)")
