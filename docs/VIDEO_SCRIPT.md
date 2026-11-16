# Video script: P05 Hospital Delivery Robot with PRM (Group G06)

Target length **about 20 minutes** (allowed 18-22). Everyone keeps their **camera on for the whole meeting**.
Mihika shares the screen and moves the slides. When you finish, say **"Next slide, please"** or hand over by name.
Speak slowly. Each part below is about 3 minutes when read aloud at a calm pace.
You don't need to read word for word; say it in your own way, but keep the numbers.

| Time | Slides | Speaker |
|---|---|---|
| 0:00-1:00 | - | Introductions (all) |
| 1:00-4:00 | 1-3 | Mihika |
| 4:00-7:00 | 4-6 | Divyanshu |
| 7:00-10:00 | 7-9 | Disha |
| 10:00-12:00 | 10-11 | Sumit |
| 12:00-17:00 | 12 | Live demo: Mihika types, Sumit explains |
| 17:00-19:30 | 13-15 | Prachi |
| 19:30-20:30 | 16-17 | Conclusion (all), thank you (Mihika) |

---

## 0:00 Introductions (all, about 1 min)

**Mihika:** Good morning. We are Group G06 of Batch B1, and our project is P05: a Hospital Delivery Robot with Probabilistic Roadmap path planning in CoppeliaSim. Before we start, each of us will introduce ourselves. I am Mihika, SAP ID 500122055.

**Divyanshu:** I am Divyanshu Dhyani, SAP ID 500122522.

**Disha:** I am Disha Rastogi, SAP ID 500119681.

**Sumit:** I am Sumit Malhotra, SAP ID 500123752.

**Prachi:** I am Prachi Chetan Padodara, SAP ID 500126371.

---

## 1:00 Mihika: slides 1-3 (about 3 min)

**Slide 1, Title**
This is our project for the course Algorithms for Intelligent Systems and Robotics. In the picture you can see our hospital in CoppeliaSim: a pharmacy, a laboratory, three wards, an ICU and a corridor, with our Pioneer robot in the middle.

**Slide 2, Problem and Motivation**
In every hospital, medicines, blood samples and supplies are carried by nurses and porters many times a day. It is repetitive work, and if a medicine or a sample arrives late, it can directly affect a patient. That is why hospitals already use delivery robots, like HelpMate in the past and the TUG robot today.
But a hospital is not easy for a robot. The doors are narrow, corridors get blocked by beds and trolleys, many orders arrive at random times, and some orders, like medicine for the ICU, are urgent and must go first.
So our goal was: plan every route with a Probabilistic Roadmap, which is built once and reused for every order, and let staff control the robot from a simple command-line client.

**Slide 3, Objectives**
We set five measurable objectives, and all five were met.
One: a route between all 72 pairs of locations. We reached 100 percent.
Two: plan a route in under 10 milliseconds. Ours takes 0.37 milliseconds.
Three: follow the path in CoppeliaSim accurately. The error was only 2 to 4 centimetres.
Four: an emergency stop from the client in under half a second. It stops in under 0.1 seconds.
And five: urgent orders should wait at least 30 percent less. They wait 52 to 88 percent less.
Now Divyanshu will explain the existing solutions and what is new in our work.

---

## 4:00 Divyanshu: slides 4-6 (about 3 min)

**Slide 4, Existing Solutions and the Gap**
Thank you, Mihika. The classic method for this problem is the Probabilistic Roadmap, or PRM, proposed by Kavraki and others in 1996. It places random points in the free space and connects nearby points into a graph, the roadmap. The roadmap is built once and then reused, so every new order is answered very quickly.
Its weakness is narrow passages. In the picture on the right you can see a PRM with plain uniform sampling. Some rooms are not connected, because random points rarely fall inside a narrow door. Methods like the bridge test help, but they are still not reliable.
The other common planner is RRT, which grows a new tree for every single order, so it repeats the same work again and again.
Commercial hospital robots work well, but their methods are closed.
So the gap is: a planner that reliably passes doors, handles blocked corridors and serves urgent orders first, in one open system.

**Slide 5, Novelty**
Our work adds five new things.
First, door-seeded sampling: we use the floor plan to place roadmap points inside and next to every door. With only 100 points we connect all routes, while uniform sampling reaches only 54 percent even with 300 points.
Second, local roadmap repair: if a corridor is blocked, we only fix the part of the roadmap around it. All 72 routes stay available, and the repair takes about 3 milliseconds instead of 27 for a full rebuild.
Third, priority dispatch: urgent orders wait 52 to 88 percent less than with first-come-first-served.
Fourth, an open command-line client over ZeroMQ with deliver, status, cancel, block and emergency stop.
And fifth, we measured the benefit of reusing the roadmap: 0.37 milliseconds per route, against 43.6 for RRT.

**Slide 6, Syllabus Mapping**
This table shows where we use the AISR syllabus. Probabilistic path planning is the PRM itself. Planning to move is the A-star search and path smoothing. Robotic software architectures is our layered design: client, queue, dispatcher, planner and controller. We also use mobile ground robots for the differential-drive model, closed-loop control for the PID controller, and intelligent agents for priority dispatch and re-planning.
Now Disha will explain the system design and the PRM algorithm.

---

## 7:00 Disha: slides 7-9 (about 3 min)

**Slide 7, System Architecture**
Thank you, Divyanshu. This is our system architecture. Hospital staff type commands in the command-line client. Delivery orders go into the order queue, which serves urgent orders first. A dispatcher thread takes the next order and asks the PRM planner for a route. The route, a list of waypoints, goes to the PID path follower, which sets the wheel speeds of the robot in CoppeliaSim through the ZeroMQ remote API, and reads back the robot's position. Every finished order is saved in a log file.
One important design choice: the map is defined in one file, and both the planner and the CoppeliaSim scene are generated from it, so they always match.

**Slide 8, Robot and Environment Model**
Our robot is the Pioneer P3-DX, a differential-drive robot. Its wheel radius is 0.0975 metres and the distance between the wheels is 0.331 metres. Its forward speed is the average of the two wheel speeds, and its turn rate comes from their difference.
The hospital is 12 by 12 metres, with 7 rooms, a corridor and 9 delivery locations. The doors are 1 metre wide. We treat the robot as a circle of radius 0.3 metres and grow every obstacle by that amount; this is the configuration space. So inside a door only 0.4 metres of free space is left. That is the narrow-passage problem.

**Slide 9, Algorithm 1: PRM Planner**
On the left is the flowchart. In the learning phase, which runs only once, we first place points in and beside every door, then add random free points until we have 300. Each point is connected to its 10 nearest neighbours, if the straight line between them is free. This takes about 28 milliseconds.
In the query phase, for every order, we connect the start and goal to the roadmap, find the shortest path with A-star, and then smooth it by cutting unnecessary corners. One query takes only 0.37 milliseconds.
On the right you can see the roadmap and three example routes going through the doors.
Now Sumit will explain how the robot follows these routes.

---

## 10:00 Sumit: slides 10-11 (about 2 min)

**Slide 10, Algorithm 2: Path-Following Controller**
Thank you, Disha. The planner gives us a path made of straight segments, and the controller makes the robot follow it.
At every 50 milliseconds, the robot looks at a "carrot" point 0.35 metres ahead on the current segment. Because the carrot stays on the current segment, the robot does not cut corners near the door frames.
A PID controller on the heading error decides how fast to turn. Our gains are Kp 2.2, Ki 0.05 and Kd 0.25. The robot slows down when it is not facing the right way, and turns on the spot if the error is more than 50 degrees. For safety, it stops immediately on an emergency stop, or if it gets stuck or goes off the path.
The graph on the right shows one route from the pharmacy to the ICU. The error stays within a few centimetres, with small spikes only at the corners.

**Slide 11, Simulation Setup**
We used CoppeliaSim Edu 4.10 with Python and the ZeroMQ remote API. The scene is built automatically from our map file. On the right are the commands: we start the client, and then staff can type commands like "deliver pharmacy icu urgent", "status", "block" and "stop". All experiments use fixed random seeds, so they can be repeated.
Now we will show the live demonstration.

---

## 12:00 Live demonstration, slide 12 (about 5 min)

*(Mihika switches the screen share to CoppeliaSim and the Terminal side by side.)*

**Mihika:** I am starting the client now. You can see it is using the PRM planner and the PID controller.
*(types `python3 -m client`)*

**Mihika:** I will send three orders: antibiotics from the pharmacy to ward 1, a blood sample from the lab to ward 3, and an urgent insulin order from the pharmacy to the ICU.
*(types the three `deliver` commands, then `queue`)*

**Sumit:** As you can see in the queue, the urgent insulin order is now at the top, even though it was sent last. The robot is now driving to the pharmacy. Look at how it goes through the narrow door. It follows the planned path and turns at the corners without touching the frame.

**Mihika:** I will check the status.
*(types `status`)*

**Sumit:** The status shows the robot's live position and the order it is working on.

**Mihika:** Now an emergency stop.
*(types `stop`)*

**Sumit:** The robot stopped immediately. In our tests it stops within 0.06 to 0.09 seconds. Now we resume.
*(Mihika types `resume`)*

**Mihika:** Now suppose a trolley blocks the lower corridor. I will tell the system.
*(types `block -0.6 -3.4 1.9 -2.6`)*

**Sumit:** The planner removed the blocked part of the roadmap and repaired it in a few milliseconds. The next routes will go around the blocked area.

**Mihika:** Finally, the history shows every order and its status, and every order is also saved in a log file for analysis.
*(types `history`, switches back to the slides)*

---

## 17:00 Prachi: slides 13-15 (about 2.5 min)

**Slide 13, Results 1: Planning**
Thank you. Now the results. The left graph compares the three sampling methods. With uniform sampling, only 54 percent of routes were found even with 300 points. The bridge test reached 83 percent. Our door-seeded sampling reached 100 percent from just 100 points, on all 10 random tests.
The right graph compares PRM with RRT over 200 orders. PRM takes 0.37 milliseconds per route, and RRT 43.6. In total, PRM needed 0.11 seconds and RRT 9.3 seconds. PRM paths were also 4 percent shorter.

**Slide 14, Results 2: Dispatch, Repair, CoppeliaSim**
The bar chart shows waiting times. At high load, urgent orders waited 432 seconds with first-come-first-served, and only 52 seconds with priority: 88 percent less. But we want to be honest: normal orders waited longer, 521 instead of 391 seconds. In a real hospital we would add "ageing", so that old orders slowly become more important.
The table also shows that after a corridor is blocked, all 72 routes still work after a 3-millisecond repair. In CoppeliaSim the robot completed all 9 legs of a tour with only 2 to 4 centimetres of error, and the emergency stop took under 0.1 seconds.

**Slide 15, Team Contribution**
This slide shows our contributions. Mihika wrote all the code: the client, the PRM, the scene, the controller, the RRT baseline and the experiments. Each of us reviewed two sections of the report and is presenting those topics in this video, as shown in the table. Every claim can be checked in our GitHub repository and in this video.

---

## 19:30 Slide 16, Conclusion and Industry Use (all, one line each)

**Mihika:** We built a complete, working hospital delivery system around a reusable Probabilistic Roadmap.

**Divyanshu:** Door-seeded sampling and local repair make PRM reliable in real floor plans with narrow doors and blocked corridors.

**Disha:** In industry, this can be used for hospital couriers and factory tugger robots, and connected to a hospital information system.

**Sumit:** To move it to a real robot, we would replace the simulator connection with ROS 2, add lidar localisation and a safety layer for people.

**Prachi:** In future we want to add multiple robots, lifts for other floors, and priority ageing. We learned planning, control, software architecture and teamwork.

## Slide 17, End (Mihika)

**Mihika:** Thank you for watching. All our code, results and the report are in our GitHub repository shown on the screen. Thank you.

*(Keep the recording running until everyone has said goodbye, then stop the recording.)*
