# Submission checklist: P05, Group G06 (due 18 Nov 2026)

## Done
- [x] Working code: client, PRM, scene, controller, RRT baseline, experiments
- [x] Report: `docs/report/AISR_P05_G06_Report.pdf` (30 pages, sample format, 18 IEEE references, no placeholders left)
- [x] Slides: `docs/slides/AISR_P05_G06_Slides.pdf` (17 slides)
- [x] Video recorded, trimmed and uploaded as **Unlisted**: https://youtu.be/STnjWhiyOrg
- [x] Peer-assessment sheets ready to print: `docs/report/Peer_Assessment_Sheets.pdf` (one page per member)

## Left (only the members can do these)
- [ ] Each member reads their own Section 11 reflection and Section 10 row, and asks for changes if needed
- [ ] Every member reads the whole report and can explain every part (viva)
- [ ] Each member fills their own peer-assessment page by hand, on their own, and signs it
- [ ] Print the report single-sided, spiral or soft bound; every member signs the Declaration and their row in Section 10; attach the 5 peer-assessment pages at the end
- [ ] Team lead submits the Google Form: report PDF, slides PDF, GitHub link, YouTube link, group details
- [ ] Hand the printed copy to the course faculty

## Live demo run-sheet (slide 12, about 6 min)
1. `open ~/CoppeliaSim_dl/coppeliaSim.app`, open `scene/hospital.ttt`
2. `python3 -m client`
3. `deliver pharmacy ward1 --item antibiotics`, `deliver lab ward3 --item blood_sample`, `deliver pharmacy icu --urgent --item insulin`, then `queue` (urgent first)
4. `status` while the robot drives through a door
5. `block -0.6 -3.4 1.9 -2.6`, then `deliver reception ward2` (the route avoids the blocked area)
6. `stop` (robot halts), `resume`, `history`, `quit`
