# Submission checklist: P05, Group G06 (due 19 Nov 2026)

## Done (in this repository)
- [x] Working code: client, PRM, scene, controller, RRT baseline, experiments
- [x] Report: `docs/report/AISR_P05_G06_Report.pdf` (30 pages, sample format, 18 IEEE references)
- [x] Slides: `docs/slides/AISR_P05_G06_Slides.pdf` (17 slides)

## Team must do (only the members can do these)
- [ ] **Fill the yellow parts of the report** (`docs/report/build_report.py`, then run `make_report.sh`):
  - Writing Allocation: who really wrote each section, and page counts
  - Section 10: each member's own technical contribution (must match their commits or the video)
  - Section 11: each member's own 5-8 line reflection
  - Appendix: YouTube link and meeting-log rows
- [ ] Slide 15: each member's technical work; slide 17: e-mails
- [ ] Every member reads the whole report and can explain every part (viva)
- [ ] Record the 20-minute online meeting (18-22 min accepted):
  - [ ] every member joins from their own device, camera ON, gallery view, for the whole recording
  - [ ] start: each member says their name and SAP ID
  - [ ] about 14 min slides (about 3-4 min per member) + about 6 min live CoppeliaSim demo (slide 12)
  - [ ] no cuts in the middle
- [ ] Upload to YouTube as **Unlisted** (not Public, not Private)
- [ ] Each member fills a peer-assessment sheet individually
- [ ] Print the report single-sided, spiral or soft bound; every member signs the Declaration and their row in Section 10; attach the peer-assessment sheets
- [ ] Team lead submits the Google Form: report PDF, slides PDF, GitHub link, YouTube link
- [ ] Hand the printed copy to the course faculty

## Live demo run-sheet (slide 12, about 6 min)
1. `open ~/CoppeliaSim_dl/coppeliaSim.app`, open `scene/hospital.ttt`
2. `python3 -m client`
3. `deliver pharmacy ward1 --item antibiotics`, `deliver lab ward3 --item blood_sample`, `deliver pharmacy icu --urgent --item insulin`, then `queue` (urgent first)
4. `status` while the robot drives through a door
5. `block -0.6 -3.4 1.9 -2.6`, then `deliver reception ward2` (the route avoids the blocked area)
6. `stop` (robot halts), `resume`, `history`, `quit`
