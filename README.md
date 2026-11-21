# HimaWatch 🏔️
### Geospatial Road Disruption & Restoration Analysis

**Team Silent Supernova | ASTRA 2026 | VIT Bhopal University**

**Domain:** Space-Based Disaster Management

**[🚀 Live Application](https://himawatch.streamlit.app/)** | **[💻 GitHub Repository](https://github.com/vaishnaviupadhyayy/Himawatch)**

---

## Overview

HimaWatch is an interactive geospatial planning prototype for studying how road-network disruptions can affect accessibility in mountainous regions.

Inspired by the October 2023 South Lhonak Glacial Lake Outburst Flood (GLOF) in Sikkim, HimaWatch focuses on the road network around Chungthang.

The application allows users to simulate hypothetical road closures, identify critical network connections, measure accessibility changes, and explore restoration scenarios.

## Problem Statement

Natural disasters in mountainous regions can disrupt transportation networks. The loss of a critical road connection may isolate parts of a network and complicate access to important destinations.

HimaWatch investigates:

**How can geospatial network analysis help identify vulnerable road connections and evaluate potential connectivity restoration after a disruption?**

## Key Features

- **Interactive road-network visualization:** Explore mapped roads around Chungthang using OpenStreetMap data.
- **Critical-link detection:** Identify graph connections whose removal would disconnect parts of the network.
- **Road-closure simulation:** Test hypothetical disruptions and observe changes in reachability.
- **Destination accessibility:** Evaluate connectivity to representative corridor destinations.
- **Restoration analysis:** Compare network access before closure, after closure, and after restoration.
- **Distance comparison:** Analyze network route distances where suitable edge-length data is available.
- **Data layers:** Support optional geospatial overlays with documented sources.
- **Evaluation evidence:** View graph checks and export scenario results.
- **Interactive dashboard:** A Himalayan night-themed interface with mapping and visualization controls.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and analytical logic |
| Streamlit | Interactive web interface |
| OSMnx | OpenStreetMap road-network acquisition |
| NetworkX | Graph modelling, connectivity and bridge detection |
| Folium | Interactive geospatial maps |
| PyDeck | Optional 3D geospatial visualization |
| GeoJSON / GraphML | Geospatial data storage and interchange |

## System Workflow

1. **Data acquisition:** Obtain mapped road-network data around Chungthang from OpenStreetMap using OSMnx.
2. **Graph construction:** Represent road intersections and connections as nodes and edges.
3. **Critical-link identification:** Use graph algorithms to identify connections critical to network connectivity.
4. **Scenario simulation:** Remove selected connections from the model.
5. **Accessibility analysis:** Recalculate nodes and representative destinations reachable from a reference hub.
6. **Restoration:** Reintroduce connections and evaluate recovered accessibility.
7. **Reporting:** Visualize and export results.

## Verified Prototype Results

The current Chungthang pilot dataset contains:

| Metric | Result |
|---|---:|
| Road-network nodes | 34 |
| Original directed edges | 70 |
| Simplified physical links | 34 |
| Graph-critical links | 30 |
| Connected components before disruption | 1 |
| Single-link closure/restoration checks | 34 passed |

### Example: E001 Closure

| Scenario | Nodes reachable from the reference hub |
|---|---:|
| Before closure | 34 |
| After E001 closure | 25 |
| After restoration | 34 |

Removing E001 disconnects **9 network nodes** from the reference hub in this scenario. Restoring the link reconnects them.

These results are derived from graph analysis and do not represent actual flood damage or the number of affected settlements or people.

## Run Locally

Clone the repository:

```bash
git clone https://github.com/vaishnaviupadhyayy/Himawatch.git
cd Himawatch
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch:

```bash
python -m streamlit run app.py
```

Open `http://localhost:8501`.

### Verify the Network Analysis

```bash
python verify_project.py
```

This checks graph connectivity, single-link closure and restoration behaviour, and the existing CSV export schema.

## Data Sources and Limitations

**OpenStreetMap:** Supplies the mapped road-network geometry. OpenStreetMap contributors are credited as the data source.

**Indian satellite-data sources:** The application provides optional integration paths for Bhuvan, Bhoonidhi/CartoDEM and MOSDAC data. These should not be interpreted as verified loaded satellite observations unless the corresponding datasets and provenance are present.

HimaWatch is a research and demonstration prototype.

It does not provide real-time road-condition monitoring, flood prediction, verified population exposure, emergency routing, or operational disaster warnings. Representative corridor points are not necessarily verified settlements or facilities.

## Future Scope

- Integrate validated Indian satellite-derived terrain and hazard layers.
- Extend analysis to verified settlements, hospitals and emergency facilities.
- Expand geographic coverage across additional Himalayan road networks.
- Include multiple disruption scenarios and restoration-cost information.
- Develop evidence-backed decision-support workflows with authoritative local data.

## Team

**Silent Supernova**

- Vaishnavi Upadhyay
- Vaanya Singh

Developed for **ASTRA 2026 — Advanced Space Technology & Research Arena**, organised by ANTERiX Club at VIT Bhopal University.

## Live Demo

**https://himawatch.streamlit.app/**

---

*HimaWatch — Exploring road-network resilience through geospatial analysis.*
