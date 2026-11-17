# Presentation Slides Content: Member M2 (Divyanshu Dhyani)

**Presenter:** Divyanshu Dhyani (M2)  
**SAP ID:** 500122522  
**Assigned Slides:** Slides 4, 5, 6  
**Speaking Duration:** ~4 Minutes  

*(Note: In the final PowerPoint / Google Slides, place "Divyanshu Dhyani (SAP ID: 500122522)" in the bottom corner of Slides 4, 5, and 6).*

---

### Slide 4: Literature Review & Existing Solutions
**Presenter in corner:** *Divyanshu Dhyani (500122522)*

#### Key Bullet Points:
* **The Path Planning Dilemma in Hospitals:**
  * Must navigate repeated multi-query deliveries between pharmacy, lab, and wards through 1.0 m narrow doorways (0.4 m clearance).
* **Classical PRM (Kavraki et al., 1996):**
  * *Strengths:* Precomputed roadmap enables sub-millisecond queries ($<1\text{ ms}$).
  * *Failure Mode:* Uniform random sampling fails in narrow passages (only **$61.1\%$ success rate** in our hospital layout).
* **RRT Baseline (LaValle, 1998):**
  * *Strengths:* Single-query exploration without precomputation.
  * *Failure Mode:* Voronoi bias expands toward open spaces, clustering against door walls; high query latency ($18.6\text{ ms}$ avg, up to $192\text{ ms}$) and **$91.7\%$ success rate**.
* **Bridge Test PRM (Hsu et al., 2003):**
  * Two colliding points whose midpoint is free; increases build time by $76\%$ ($67.1\text{ ms}$) and still misses doors ($58.3\%$ success).
* **Grid A\* (Hart et al., 1968):**
  * Complete and optimal, but memory scales with resolution and discrete cell expansions take $8.0\text{ ms}$ per query with jagged paths.

#### Speaking Notes (~75-80 seconds):
> *"Good morning/afternoon everyone. My name is Divyanshu Dhyani, SAP ID 500122522. Today I will present the literature review, our novelty, and syllabus mapping.*  
> *When designing a hospital delivery robot, selecting the right motion planning paradigm is critical. Classical PRM by Kavraki et al. precomputes a roadmap, allowing ultra-fast sub-millisecond queries. However, because hospital doors are narrow (only 0.4 meters of clearance for our Pioneer P3-DX), uniform sampling frequently fails to place nodes in doorways—yielding only a 61% success rate in our benchmarks.*  
> *We implemented RRT as a single-query baseline. While RRT explores open corridors well, its Voronoi bias makes penetrating narrow doors difficult, leading to 18 millisecond average query times and inconsistent paths.*  
> *Hsu's Bridge Test improves narrow passage sampling but incurs high rejection overhead during construction. Finally, discrete Grid A* guarantees path discovery but suffers from grid resolution bottlenecks and 8 millisecond query times. This motivated our novel hybrid approach."*

---

### Slide 5: Novelty & Technical Innovation
**Presenter in corner:** *Divyanshu Dhyani (500122522)*

#### Key Bullet Points:
* **1. Domain-Specific Door-Seeded Sampling (DSS-PRM):**
  * Exploits known architectural floor plan coordinates *a priori*.
  * Deterministically seeds doorway portals (triad: room side, door center, corridor side).
  * **Result:** **100.0% path success rate** across all 72 clinical pairs at both $N=300$ and $N=100$ ($9.2\text{ ms}$ build time).
* **2. Localized Dynamic Corridor Invalidation (`block`):**
  * Medical trolleys or beds temporarily blocking corridors do **not** trigger a full roadmap rebuild.
  * Localized Liang-Barsky segment clipping invalidates affected edges/nodes in **$< 1.0\text{ ms}$**.
  * Instantaneous re-routing around obstructions.
* **3. Decoupled Asynchronous Microservice Architecture:**
  * Thread-safe order dispatching via Python ZeroMQ bridge to CoppeliaSim simulation.
  * Supports urgent priority task insertion (`--urgent`) and real-time operator overrides.

#### Speaking Notes (~80-90 seconds):
> *"On Slide 5, we highlight the core novelties of our project.*  
> *First, we developed Door-Seeded Sampling for PRM, or DSS-PRM. In a hospital, we already know where the rooms and doors are. Instead of blindly hoping random samples land in narrow doorways, DSS-PRM deterministically injects transition triads through each doorway. As our benchmarks prove, this guarantees a 100% success rate across all 72 clinical pairs, even with just 100 samples, taking under 10 milliseconds to construct and 0.3 milliseconds to query.*  
> *Second, we developed dynamic obstacle invalidation. If a gurney or bed blocks a hallway, traditional PRM has to discard and regenerate the entire graph. Our system prunes only the intersecting edges in under one millisecond, letting the robot immediately divert through an alternate corridor without stopping.*  
> *Third, our software architecture cleanly decouples the CLI order queue from the PRM planner and the CoppeliaSim physics simulator using ZeroMQ and thread locks, ensuring safe, real-time command handling."*

---

### Slide 6: Syllabus Mapping & Benchmark Summary
**Presenter in corner:** *Divyanshu Dhyani (500122522)*

#### Key Bullet Points:
* **Direct Mapping to Course Curriculum:**
  * **1. Probabilistic Path Planning:** PRM learning vs query phases, C-space obstacle inflation ($r=0.30\text{ m}$), sampling strategies (Uniform vs Bridge vs Door-Seeded), and RRT exploration trees.
  * **2. Planning to Move:** Graph search algorithms (A* on roadmap nodes, Grid A* discrete search), heuristics ($h(n) = \text{Euclidean dist}$), and greedy shortcut smoothing.
  * **3. Robotic Software Architectures:** Decoupled layered architecture (User CLI $\to$ Dispatcher $\to$ Motion Planner $\to$ Controller $\to$ CoppeliaSim ZeroMQ API).
* **Key Benchmarking Results (All 72 Clinical Pairs):**
  * **DSS-PRM ($N=300$):** 100% Success | $0.54\text{ ms}$ Query | $38.1\text{ ms}$ Build
  * **Uniform PRM ($N=300$):** 61.1% Success (Door bottleneck failure)
  * **Bridge PRM ($N=300$):** 58.3% Success | $67.1\text{ ms}$ Build (Rejection overhead)
  * **RRT Baseline:** 91.7% Success | $18.62\text{ ms}$ Query (Single-query overhead)
  * **Grid A\* Baseline:** 100% Success | $8.01\text{ ms}$ Query (Cell expansion overhead)

#### Speaking Notes (~75-80 seconds):
> *"Finally, on Slide 6, we map our implementation directly to the syllabus topics.*  
> *For Probabilistic Path Planning, we implemented and analyzed continuous C-space obstacle inflation, k-nearest neighbour graph construction, and random sampling versus goal-directed RRT.*  
> *For Planning to Move, we applied A* search with Euclidean heuristics across both topological roadmap graphs and discrete 2D occupancy grids, followed by line-of-sight shortcut smoothing to produce executable paths for our robot controller.*  
> *For Robotic Software Architectures, we followed a modular layered architecture where each subsystem operates independently through defined interfaces.*  
> *As summarized in the benchmark table, DSS-PRM outperforms all baselines, achieving 100% delivery success with 35 times faster response than RRT and 15 times faster than Grid A\*. Thank you, and I now hand over to Disha/Sumit for the next section."*

