HimaWatch — Evaluation Evidence Upgrade
Team Silent Supernova · ASTRA 2026 · Domain 03

This package builds on the working HimaWatch Night Operations Streamlit app. It does not invent verified villages, populations, satellite observations or flood outcomes, and does not guarantee any judging score.
Install (existing project, no new project folder)
1. In your himawatch folder, keep data/chungthang_roads.graphml unchanged.
2. Back up the working file: cp app.py app_before_evaluation.py.
3. Replace only app.py with the provided updated file. Optionally replace .streamlit/config.toml and requirements.txt with the included versions.
4. Copy verify_project.py beside app.py if you want a command-line local verification. This is not required for the app to start.
5. With your virtual environment activated:python -m pip install -r requirements.txt
   python verify_project.py
   python -m streamlit run app.py
New, measured evidence
- Evaluation Evidence view: current scenario counts, independent graph-integrity checks, per-reference-point distances in kilometres only if all graph edge lengths are present, local layer provenance, downloadable human-readable evidence brief.
- verify_project.py: verifies every mapped link's closure/restoration and NetworkX graph-bridge classification against the local graph, then confirms the five-column CSV schema. Checks are deterministic and do not contact a web service.
- Original graph construction, critical-link detection, closure simulation, restoration, 4 directional corridor destinations and original CSV column values/order remain unchanged.
- The dark/Himalayan design, map layers, offline Space void mode, optional Bhuvan/Bhoonidhi/MOSDAC overlay paths and existing footer remain present.
What the checks DO NOT establish
- Accuracy of OpenStreetMap roads or completeness of mapped roads.
- Whether a real road is open, flooded, damaged, safe or traversable.
- Whether directional road nodes are inhabited settlements, health posts, bridges or relief centres.
- That locally supplied files are actually ISRO observations without provenance validation.
- Any GLOF likelihood, flood depth, arrival times, number of people affected or emergency warning.
High-mark gaps still requiring actual evidence
1. Satellite use (important for ASTRA): Obtain a documented, georeferenced Bhuvan or CartoDEM/MOSDAC input relevant to the pilot; save its source, date and bounds. Use the supplied optional offline scripts to prepare/display overlays. Merely displaying an image without an analytical role is insufficient. Do not claim unverified sources.
2. Meaningful destinations: Replace/further supplement directional reference points with verified settlement/facility positions and documented mapping/provenance. Keep the established legacy CSV results comparable until a separate analysis validates changes.
3. Testing: On your Mac, check Mission Brief, Scenario Workspace, Critical Links, Evaluation Evidence, Data Layers, Satellite Context, 2D Night/Streets/Space void, 3D fallback, guided demo, reset, selection, and CSV/GeoJSON/TXT downloads.
4. Deliverables: Publish a working hosted link, source repository, six-slide deck and recorded demo according to the event instructions. Verify the hosted app can load your GraphML and optional overlays.
Suggested judge demonstration (90 seconds)
- 0–15 seconds: Present the 2023 Sikkim GLOF transport-access problem; define HimaWatch as a scenario planner, not a prediction system.
- 15–30: Show the mapped Chungthang road graph and explain OSMnx + NetworkX.
- 30–50: Close a graph-critical connection; display reduced reachable nodes and an affected reference destination.
- 50–65: Restore the same connection; show the inverse connectivity result and the destination status change.
- 65–78: Open Evaluation Evidence; show source dates/limitations, reproducible checks and weighted distances when present.
- 78–90: State the technical contribution and precisely what Indian satellite layer has or has not been integrated.
Source and data honesty
OSM roads: OpenStreetMap contributors; Bhuvan: ISRO/NRSC; Bhoonidhi CartoDEM: NRSC; MOSDAC GSMap ISRO: SAC-ISRO — credit satellite layers only when genuinely loaded and verified. The app uses optional overlays and does not authenticate to any provider. No actual population exposure or verified early warning is implemented.