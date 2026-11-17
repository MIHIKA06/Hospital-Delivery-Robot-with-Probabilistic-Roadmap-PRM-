"""Build the 17-slide presentation (AISR rules: max 17 slides, heading 28-32 pt,
body >= 20 pt, presenter name in the corner, own figures).

    python3 docs/slides/build_slides.py        # -> docs/slides/AISR_P05_G06_Slides.pptx
    (PDF: soffice --headless --convert-to pdf AISR_P05_G06_Slides.pptx)
"""

import json
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
RES = os.path.join(ROOT, "results")
J = lambda n: json.load(open(os.path.join(RES, n)))  # noqa: E731
E2, E3, E5, E6 = J("E2_prm_vs_rrt.json"), J("E3_dispatch.json"), J("E5_blocked.json"), J("E6_coppeliasim.json")

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
BLUE = RGBColor(0x21, 0x71, 0xB5)
GREY = RGBColor(0x55, 0x55, 0x55)
FONT = "Arial"
REPO = "github.com/MIHIKA06/Hospital-Delivery-Robot-with-Probabilistic-Roadmap-PRM-"

prs = Presentation()
prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]
N = [0]


def text(slide, x, y, w, h, lines, size=20, bold=False, color=None, align=None, bullet=False):
    tb = slide.shapes.add_textbox(Cm(x), Cm(y), Cm(w), Cm(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        b = bold
        if ln.startswith("**"):
            ln, b = ln.strip("*"), True
        p.text = ("•  " + ln) if bullet else ln
        p.space_after = Pt(8)
        if align:
            p.alignment = align
        for r in p.runs:
            r.font.size, r.font.bold, r.font.name = Pt(size), b, FONT
            if color:
                r.font.color.rgb = color
    return tb


def slide(title, presenter):
    N[0] += 1
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, 0, 0, W, Cm(2.6))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    text(s, 1.0, 0.45, 26, 1.8, title, size=30, bold=True, color=RGBColor(255, 255, 255))
    text(s, 24.0, 17.6, 9.3, 1.0, f"Presenter: {presenter}", size=12, color=GREY, align=PP_ALIGN.RIGHT)
    text(s, 0.8, 17.6, 14, 1.0, f"P05 · G06 · Hospital Delivery Robot with PRM   |   {N[0]}",
         size=12, color=GREY)
    return s


def pic(s, name, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Cm(w)
    if h:
        kw["height"] = Cm(h)
    return s.shapes.add_picture(os.path.join(RES, name), Cm(x), Cm(y), **kw)


def table(s, rows, x, y, widths, size=16, row_h=1.0):
    t = s.shapes.add_table(len(rows), len(rows[0]), Cm(x), Cm(y), Cm(sum(widths)),
                           Cm(row_h * len(rows))).table
    for j, w in enumerate(widths):
        t.columns[j].width = Cm(w)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j)
            c.text = str(v)
            for p in c.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size, r.font.name, r.font.bold = Pt(size), FONT, i == 0
    return t


# 1 ---------------------------------------------------------------- title
N[0] += 1
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, W, Cm(7.2))
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
text(s, 1.5, 1.2, 31, 3.5, ["Hospital Delivery Robot with", "Probabilistic Roadmap (PRM) Path Planning"],
     size=32, bold=True, color=RGBColor(255, 255, 255))
text(s, 1.5, 5.0, 31, 1.5, "CSAI4014 Algorithms for Intelligent Systems and Robotics  ·  B.Tech CSE (AI & ML), Sem VII",
     size=18, color=RGBColor(0xDD, 0xE6, 0xF0))
text(s, 1.5, 7.8, 16.5, 1.2, "**Project P05  ·  Group G06  ·  Batch B1", size=22)
text(s, 1.5, 9.3, 16.5, 6.5, ["Mihika – 500122055", "Divyanshu Dhyani – 500122522",
                              "Disha Rastogi – 500119681", "Sumit Malhotra – 500123752",
                              "Prachi Chetan Padodara – 500126371"], size=20)
text(s, 1.5, 15.9, 16.5, 1.6, ["Submitted to: Course Faculty, CSAI4014",
                               "School of Computer Science, UPES"], size=15, color=GREY)
pic(s, "fig_scene_3d.png", 18.2, 7.9, w=14.5)
text(s, 24.0, 17.6, 9.3, 1.0, "Presenter: Mihika", size=12, color=GREY, align=PP_ALIGN.RIGHT)

# 2 ---------------------------------------------------------------- problem
s = slide("Problem and Motivation", "Mihika")
text(s, 1.2, 3.3, 15.5, 13, [
    "Nurses and porters carry medicines and samples by hand all day",
    "Late medicine or samples → risk to patients",
    "Hospital robots (HelpMate, TUG) already do this in industry",
    "Hard parts: narrow doors, blocked corridors, many orders, urgent orders first",
    "**Our goal: plan every route with a reusable PRM, controlled from a command line"],
    size=21, bullet=True)
pic(s, "fig_scene_top.png", 18.5, 3.1, h=14.0)

# 3 ---------------------------------------------------------------- objectives
s = slide("Objectives (all met)", "Mihika")
table(s, [["Objective", "Target", "Achieved"],
          ["Route planning: all 72 location pairs", "≥ 95% of roadmaps", "100% (10/10 seeds)"],
          ["Planning speed per route", "< 10 ms", "0.37 ms"],
          ["Path following in CoppeliaSim", "< 5 cm RMS, ≤ 0.10 m at goal", "2.2–3.5 cm, < 0.10 m"],
          ["Emergency stop from the client", "< 0.5 s", "0.06–0.09 s"],
          ["Urgent orders wait less than FCFS", "≥ 30% less", "52–88% less"]],
      1.5, 3.6, [13.5, 8.5, 8.8], size=20, row_h=2.0)

# 4 ---------------------------------------------------------------- existing
s = slide("Existing Solutions and the Gap", "Divyanshu Dhyani")
text(s, 1.2, 3.3, 17, 13, [
    "**PRM (Kavraki 1996): roadmap reused, but misses narrow doors",
    "**Bridge test / Gaussian: more nodes in gaps, still unreliable",
    "**RRT / RRT*: new tree for every order → slow, repeated work",
    "**Commercial AMRs: proven, but closed methods",
    "**Gap: reliable doors + blocked corridors + urgent orders, in one open system"],
    size=20, bullet=True)
pic(s, "fig_roadmap_uniform.png", 19.5, 3.0, h=14.3)
text(s, 19.5, 16.9, 13, 0.8, "Uniform PRM: rooms left unconnected at the doors", size=14, color=GREY)

# 5 ---------------------------------------------------------------- novelty
s = slide("Novelty", "Divyanshu Dhyani")
text(s, 1.2, 3.3, 31, 14, [
    "**1. Door-seeded sampling: 100% of routes with only 100 nodes (uniform: 54% with 300)",
    "**2. Local roadmap repair for a blocked corridor: 72/72 routes kept, 3 ms vs 27 ms rebuild",
    "**3. Priority dispatch + PRM: urgent orders wait 52–88% less than FCFS",
    "**4. Open command-line client over ZeroMQ: deliver, status, cancel, block, stop (0.06–0.09 s)",
    "**5. Measured benefit of roadmap reuse: 0.37 ms vs 43.6 ms per route (RRT)"],
    size=22)

# 6 ---------------------------------------------------------------- syllabus
s = slide("Syllabus Mapping", "Divyanshu Dhyani")
table(s, [["AISR topic", "Where we use it"],
          ["Probabilistic path planning", "PRM learning and query phases, samplers, repair"],
          ["Planning to move", "A* on the roadmap, smoothing, pickup → drop-off legs"],
          ["Robotic software architectures", "Client → queue → dispatcher → planner → controller"],
          ["Mobile ground robots", "Differential-drive Pioneer P3-DX kinematics"],
          ["Closed-loop control, stability", "PID heading control, cross-track error"],
          ["Intelligent agents", "Priority dispatch, emergency stop, re-planning"]],
      1.5, 3.6, [11.0, 19.8], size=20, row_h=1.9)

# 7 ---------------------------------------------------------------- architecture
s = slide("System Architecture", "Disha Rastogi")
pic(s, "fig_architecture_slide.png", 1.0, 4.6, w=31.8)
text(s, 1.2, 15.6, 31, 1.6, "One map file feeds both the planner and the CoppeliaSim scene  ·  modules talk through plan() and follow()",
     size=18, color=GREY)

# 8 ---------------------------------------------------------------- robot & env
s = slide("Robot and Environment Model", "Disha Rastogi")
text(s, 1.2, 3.3, 17, 13.5, [
    "**Robot: Pioneer P3-DX, differential drive",
    "wheel radius 0.0975 m, track 0.331 m",
    "v = r(ωR+ωL)/2,  ω = r(ωR−ωL)/b",
    "**Map: 12 m × 12 m, 7 rooms + corridor, 9 locations",
    "Doors 1.0 m; robot radius 0.30 m → only 0.4 m free in C-space",
    "Obstacles inflated by the robot radius (configuration space)"],
    size=20, bullet=True)
pic(s, "fig_scene_3d.png", 18.5, 3.6, w=14.5)

# 9 ---------------------------------------------------------------- algorithm 1
s = slide("Algorithm 1: PRM Planner", "Disha Rastogi")
pic(s, "fig_flowchart.png", 1.0, 2.9, h=14.5)
pic(s, "fig_roadmap_door.png", 12.6, 2.9, h=14.5)
text(s, 27.4, 4.0, 6.2, 12, ["n = 300 nodes", "k = 10 neighbours", "edges ≤ 3 m",
                              "A* + shortcut smoothing", "built once: 28 ms", "query: 0.37 ms"], size=18)

# 10 --------------------------------------------------------------- algorithm 2
s = slide("Algorithm 2: Path-Following Controller", "Sumit Malhotra")
text(s, 1.2, 3.3, 13.5, 13.5, [
    "Carrot 0.35 m ahead on the current segment (no corner cutting)",
    "PID on heading error: Kp 2.2, Ki 0.05, Kd 0.25",
    "v = vmax·cos²(e), turn in place if |e| > 50°",
    "(v, ω) → wheel speeds, 50 ms steps",
    "Stops on e-stop, no progress, or > 0.8 m off path"],
    size=20, bullet=True)
pic(s, "fig_tracking.png", 14.8, 4.2, w=18.5)

# 11 --------------------------------------------------------------- setup
s = slide("Simulation Setup", "Sumit Malhotra")
text(s, 1.2, 3.3, 14, 13, [
    "CoppeliaSim Edu 4.10, Bullet physics",
    "Python 3.9 + ZeroMQ remote API",
    "Scene generated from planner/hospital_map.py",
    "Fixed seeds; results in results/*.json"], size=20, bullet=True)
tb = text(s, 15.6, 3.4, 17.5, 13, [
    "python3 tools/build_hospital_scene.py",
    "python3 -m client",
    "hospital> deliver pharmacy icu --urgent",
    "hospital> status   |   queue   |   cancel 2",
    "hospital> block -0.6 -3.4 1.9 -2.6",
    "hospital> stop   |   resume",
    "python3 -m experiments.run_experiments"], size=17)
for p in tb.text_frame.paragraphs:
    for r in p.runs:
        r.font.name = "Courier New"

# 12 --------------------------------------------------------------- live demo
s = slide("Live Demonstration", "Sumit Malhotra")
text(s, 1.2, 3.5, 31, 12, [
    "**Switching to CoppeliaSim now",
    "1. Two normal orders, then an urgent insulin order → served first",
    "2. status while the robot drives through the doors",
    "3. block a corridor → the next route goes around it",
    "4. stop → robot halts immediately; resume"], size=24)

# 13 --------------------------------------------------------------- results 1
s = slide("Results 1: Planning", "Prachi Chetan Padodara")
pic(s, "fig_success_vs_n.png", 0.8, 3.0, w=16.0)
pic(s, "fig_prm_vs_rrt.png", 17.0, 3.0, w=16.0)
text(s, 1.0, 13.0, 32, 4, [
    "Door-seeded PRM: 100% of 72 routes from n = 100; uniform 54%, bridge 83% at n = 300",
    f"PRM 0.37 ms vs RRT 43.6 ms per route; 200 orders: 0.11 s vs 9.3 s; paths 4% shorter"],
    size=20, bullet=True)

# 14 --------------------------------------------------------------- results 2
s = slide("Results 2: Dispatch, Repair, CoppeliaSim", "Prachi Chetan Padodara")
pic(s, "fig_dispatch_wait.png", 0.8, 3.0, w=15.0)
table(s, [["Test", "Result"],
          ["Urgent wait (high load)", "432 s → 52 s (−88%)"],
          ["Normal wait (high load)", "391 s → 521 s (cost)"],
          ["Blocked corridor repair", "72/72 routes, ~3 ms"],
          ["CoppeliaSim 9-leg tour", "9/9, RMS 2.2–3.5 cm"],
          ["Emergency stop", "0.06–0.09 s"]],
      16.6, 3.3, [8.0, 8.6], size=17, row_h=1.6)
text(s, 1.0, 13.8, 32, 3, ["Honest trade-off: priority helps urgent orders but normal orders wait longer → add ageing"],
     size=20, bullet=True)

# 15 --------------------------------------------------------------- contribution
s = slide("Team Contribution", "Prachi Chetan Padodara")
table(s, [["Member", "Presents", "Report", "Contribution (report Table 13)"],
          ["Mihika", "1\u20133", "Wrote all", "All code: client, PRM, scene, controller, RRT, experiments"],
          ["Divyanshu Dhyani", "4\u20136", "Reviewed 3, 4", "Presentation of existing work, novelty, syllabus"],
          ["Disha Rastogi", "7\u20139", "Reviewed 5, 7", "Presentation of architecture, model, PRM"],
          ["Sumit Malhotra", "10\u201312", "Reviewed 6, 8", "Presentation of controller, setup, live demo"],
          ["Prachi C. Padodara", "13\u201315", "Reviewed 9, 12", "Presentation of results and contribution"]],
      1.0, 3.4, [6.0, 3.2, 5.6, 17.0], size=17, row_h=2.0)
text(s, 1.0, 15.8, 32, 1.2, "Every claim is traceable to GitHub commits or this video", size=16, color=GREY)

# 16 --------------------------------------------------------------- conclusion
s = slide("Conclusion and Industry Use", "All")
text(s, 1.2, 3.3, 31, 14, [
    "A complete, working hospital delivery system around a reusable PRM",
    "Door-seeded sampling + local repair make PRM reliable in real floor plans",
    "Industry: hospital couriers, factory tuggers, link to hospital information systems",
    "Real robot: replace the simulator bridge with ROS 2 + lidar localisation + safety layer",
    "Future: multi-robot traffic, lifts, priority ageing, OMPL comparison",
    "**We learned: planning, control, software architecture and teamwork"], size=21, bullet=True)

# 17 --------------------------------------------------------------- end
N[0] += 1
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, W, H)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
text(s, 1.5, 4.0, 31, 3, "Thank you!  Questions?", size=44, bold=True, color=RGBColor(255, 255, 255),
     align=PP_ALIGN.CENTER)
text(s, 1.5, 8.5, 31, 1.5, REPO, size=20, color=RGBColor(0xDD, 0xE6, 0xF0), align=PP_ALIGN.CENTER)
text(s, 1.5, 9.7, 31, 1.5, "Video: youtu.be/STnjWhiyOrg", size=20, color=RGBColor(0xDD, 0xE6, 0xF0),
     align=PP_ALIGN.CENTER)
text(s, 1.5, 12.0, 31, 2, "Mihika · Divyanshu Dhyani · Disha Rastogi · Sumit Malhotra · Prachi Chetan Padodara",
     size=18, color=RGBColor(255, 255, 255), align=PP_ALIGN.CENTER)
text(s, 24.0, 17.6, 9.3, 1.0, "Presenter: All", size=12, color=RGBColor(0xDD, 0xE6, 0xF0), align=PP_ALIGN.RIGHT)

out = os.path.join(HERE, "AISR_P05_G06_Slides.pptx")
prs.save(out)
print("saved", out, len(prs.slides._sldIdLst), "slides")
