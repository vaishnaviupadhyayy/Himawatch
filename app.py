"""HimaWatch / Silent Supernova — ASTRA 2026.

A screening-level *hypothetical* road-access scenario explorer.
Data required: data/chungthang_roads.graphml (existing OSMnx export).
Optional: data/lakes.json for explicit, attributed satellite context.
"""
from __future__ import annotations

import csv
import json
import base64
import mimetypes
import math
from datetime import datetime, timezone
from html import escape
from io import StringIO, BytesIO
from pathlib import Path
from typing import Any

import folium
from folium import plugins
import networkx as nx
import osmnx as ox
import streamlit as st
import streamlit.components.v1 as components

try:
    import pydeck as pdk
except ImportError:
    pdk = None

try:
    from shapely.geometry import shape, LineString
except ImportError:
    shape = None
    LineString = None

st.set_page_config(page_title="HimaWatch | Mission Control", page_icon="🏔️", layout="wide", initial_sidebar_state="expanded")

# ── Palette and the only CSS block ────────────────────────────────────────
VOID = "#080F1C"
PANEL = "#102237"
BORDER = "#2B4659"
TEXT = "#E7F0FA"
MUTED = "#A5B8CA"
TEAL = "#50D4BC"
AURORA = "#8FE8DC"
RED = "#FF7D88"
AMBER = "#EEB86A"

if "hw_effects" not in st.session_state:
    st.session_state.hw_effects = "Full"
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root {color-scheme:dark}
html,body,[data-testid="stAppViewContainer"],.stApp {background:#080F1C;color:#E7F0FA}
.stApp {background-image:radial-gradient(ellipse 60% 38% at 90% -7%,rgba(40,141,173,.13),transparent),radial-gradient(ellipse 50% 45% at -12% 40%,rgba(23,97,116,.10),transparent)}
.block-container{max-width:1530px;padding-top:1.5rem;padding-bottom:2.8rem}
[data-testid="stHeader"]{background:rgba(8,15,28,.96)}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.025em!important;color:#E7F0FA!important}
p,div,label,button,span{font-family:'Inter',sans-serif}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:#A5B8CA!important}
.stApp hr{border-color:#2B4659!important}
/* Mission hero uses inline SVG shapes: no external imagery */
.hw-hero{position:relative;isolation:isolate;overflow:hidden;border:1px solid #2B4659;border-radius:14px;padding:30px 34px 24px;margin-bottom:18px;background:radial-gradient(circle at 85% 10%,rgba(80,212,188,.14),transparent 32%),linear-gradient(115deg,#0c192b,#102b3b 66%,#123b47);box-shadow:0 22px 55px #0005,inset 0 1px #ffffff12}
.hw-hero:before{content:'';position:absolute;inset:0;background-image:radial-gradient(#a7e8e6 0.7px,transparent 1px);background-size:42px 39px;opacity:.14;pointer-events:none}
.hw-mark{color:#8FE8DC;font:700 11px 'JetBrains Mono',monospace;letter-spacing:.16em}
.hw-head{font:700 clamp(2.15rem,4vw,3.65rem) 'Space Grotesk',sans-serif;color:#E7F0FA;margin:14px 0 7px;letter-spacing:-.055em;line-height:1.03}
.hw-sub{max-width:680px;color:#C3D8E4;font-size:14px;line-height:1.7}
.hw-ridge{position:absolute;right:-2%;bottom:-7px;width:46%;height:77%;opacity:.42;pointer-events:none}
.hw-status{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0 16px}
.hw-chip{display:inline-flex;gap:6px;align-items:center;border:1px solid #37536b;background:#112b3c;color:#bceee7;border-radius:100px;padding:6px 11px;font:600 10px 'JetBrains Mono',monospace;letter-spacing:.04em}
.hw-chip.warn{color:#ffd19b;border-color:#66513f;background:#33283a}
.hw-micro{font:600 10px 'JetBrains Mono',monospace;color:#93bbc6;letter-spacing:.12em;text-transform:uppercase}
.hw-card{background:linear-gradient(145deg,rgba(21,45,64,.88),rgba(13,32,50,.92));border:1px solid #2B4659;border-radius:12px;padding:15px 18px;margin:8px 0 12px;position:relative;box-shadow:inset 0 1px #ffffff0b,0 10px 20px #0002}
.hw-card:after{content:'';position:absolute;right:0;top:0;width:16px;height:16px;border-top:1px solid #50D4BC77;border-right:1px solid #50D4BC77;border-radius:0 10px 0 0}
.hw-card .num{font:600 29px 'JetBrains Mono',monospace;color:#E7F0FA;margin:4px 0}
.hw-card .desc{font-size:12px;color:#A5B8CA}
.hw-synopsis{border-left:3px solid #50D4BC;background:#10283a;padding:13px 16px;color:#d5e8f0;font-size:13px;border-radius:0 8px 8px 0;margin:10px 0}
.hw-rule{border-top:1px solid #2B4659;margin:20px 0}
.hw-footnote{font-size:12px;color:#A5B8CA;line-height:1.75}
/* Native controls: keep the actual Streamlit light-theme defaults out */
.stApp [data-baseweb="select"]>div,.stApp [data-baseweb="input"]>div,.stApp input,.stApp textarea{background:#102237!important;color:#E7F0FA!important;border-color:#38576d!important}
.stApp [data-baseweb="select"] span,.stApp [data-baseweb="select"] input{color:#E7F0FA!important}
.stApp [data-baseweb="tag"]{background:#175a61!important}
.stApp [data-baseweb="tag"] *{color:#ffffff!important}
.stApp [data-testid="stWidgetLabel"] *{color:#d8e6ee!important}
.stButton>button,.stDownloadButton>button{background:#15394a!important;color:#E7F0FA!important;border:1px solid #376577!important;border-radius:8px!important;transition:background .2s ease,transform .2s ease,border-color .2s ease}
.stButton>button:hover,.stDownloadButton>button:hover{background:#205264!important;border-color:#50D4BC!important;transform:translateY(-1px)}
.stApp [data-testid="stMetric"]{background:linear-gradient(145deg,#12283c,#102237);border:1px solid #2B4659;border-radius:11px;padding:16px;box-shadow:inset 0 1px #ffffff0a}
.stApp [data-testid="stMetricLabel"] *{color:#b7cad8!important;font-size:12px!important}
.stApp [data-testid="stMetricValue"] *{color:#E7F0FA!important;font-family:'JetBrains Mono',monospace!important}
.stApp [data-testid="stAlert"]{background:#132e3d!important;color:#E7F0FA!important;border:1px solid #2B4659}
.stApp [data-testid="stAlert"] *{color:#E7F0FA!important}
.stApp [data-testid="stExpander"]{background:#102237;border-color:#2B4659}
.stApp [data-testid="stTable"] th,.stApp [data-testid="stTable"] td{background:#102237!important;color:#E7F0FA!important;border-color:#2B4659!important}
.stApp [data-testid="stDataFrame"]{border:1px solid #2B4659;border-radius:10px}
.stApp [data-baseweb="tab"]{color:#A5B8CA}
.stApp [aria-selected="true"]{color:#8FE8DC!important}
.stApp button:focus-visible,.stApp input:focus-visible,.stApp a:focus-visible{outline:3px solid #8FE8DC!important;outline-offset:3px}
.hw-table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0 20px}
.hw-table td,.hw-table th{border-bottom:1px solid #2B4659;padding:12px 10px;text-align:left;vertical-align:middle}
.hw-table th{font:600 10px 'JetBrains Mono',monospace;letter-spacing:.09em;color:#a1c5d3;text-transform:uppercase}
.hw-pill{white-space:nowrap;padding:5px 9px;border:1px solid #38766d;border-radius:20px;font:600 11px 'Inter',sans-serif;background:#153b38;color:#bcf4d9}
.hw-pill.off{background:#3b2334;border-color:#864859;color:#ffb1be}
.hw-legend{background:#102237;border:1px solid #3c596b;border-radius:8px;padding:10px 12px;color:#e2edf3;font:12px 'Inter',sans-serif;line-height:1.9}
.hw-footer,.footer{color:#A5B8CA;font-size:12px;border-top:1px solid #2B4659;padding-top:20px;margin-top:32px;line-height:1.9}
@media(max-width:700px){.block-container{padding:1rem .85rem}.hw-hero{padding:24px 20px}.hw-ridge{opacity:.18;width:75%}.hw-card .num{font-size:25px}.hw-table{font-size:11px}.hw-table td,.hw-table th{padding:8px 4px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}

/* ── Night Himalayan observatory: depth and atmosphere ── */
:root{--void:#02040a;--panel:#102237;--border:#2b4659;--teal:#50d4bc;--violet:#8b7cff;--ice:#e7f0fa}
.stApp{background:radial-gradient(ellipse 62% 40% at 80% 0%,#19274466,transparent 75%),radial-gradient(ellipse 50% 38% at 16% 14%,#103b4660,transparent 78%),#02040a!important}
.stApp:before,.stApp:after{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.24;background-image:radial-gradient(#d8f3ff 0.65px,transparent 1px),radial-gradient(#c4ddff .85px,transparent 1.4px),radial-gradient(#91c4f5 .6px,transparent 1px);background-size:83px 97px,157px 131px,229px 191px;background-position:4px 8px,45px 67px,120px 39px;animation:sky-drift 45s linear infinite alternate}
.stApp:after{opacity:.12;filter:blur(1px);background-size:117px 149px,203px 171px,271px 239px;animation-duration:67s}
@keyframes sky-drift{to{transform:translate3d(15px,-10px,0);opacity:.32}}
.block-container{position:relative;z-index:1}
.hw-hero{min-height:295px;padding:31px 36px 44px;background:radial-gradient(ellipse 45% 60% at 82% 5%,#8b7cff30,transparent 80%),radial-gradient(ellipse 46% 38% at 50% 93%,#92dfff24,transparent),linear-gradient(120deg,#09172a 0%,#112638 67%,#14223d 100%)}
.hw-hero:before{opacity:.21;animation:sky-drift 37s linear infinite alternate}
.hw-ridge{width:70%;height:100%;bottom:0;right:-5%;opacity:.82;animation:ridge-float 26s ease-in-out infinite alternate}
@keyframes ridge-float{to{transform:translateX(9px) scale(1.015)}}
.hw-moon{position:absolute;right:19%;top:19px;width:87px;height:87px;border-radius:50%;background:radial-gradient(circle at 38% 32%,#f8fbff,#c7d8ec 55%,#8ba9ca 100%);box-shadow:0 0 30px #d9e9ff6e,0 0 100px #8b7cff47,inset -13px -10px 18px #607b9c90;opacity:.9;pointer-events:none}
.hw-moon:before{content:"";position:absolute;top:17px;left:27px;width:21px;height:19px;border-radius:50%;background:#8499b638;box-shadow:22px 25px 0 3px #748eaa35,-13px 37px 0 -5px #708fac35}
.hw-orbit{position:absolute;right:5.5%;top:-49px;width:275px;height:240px;border:1px solid #a6d4f32b;border-radius:50%;transform:rotate(-25deg);pointer-events:none}
.hw-orbit:after{content:"✦";position:absolute;left:26px;top:52px;color:#bdf9fd;font-size:20px;filter:drop-shadow(0 0 8px #50d4bc);animation:orbit-float 14s ease-in-out infinite alternate}
@keyframes orbit-float{to{transform:translate(37px,-22px)}}
.hw-galaxy{position:absolute;inset:-36% -10%;background:linear-gradient(115deg,transparent 42%,#a7d8ff09 48%,#d0dfff12 51%,#8b7cff0c 54%,transparent 63%);transform:rotate(-14deg);pointer-events:none}
.hw-card{box-shadow:inset 0 1px #ffffff14,0 17px 35px #0005;transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;backdrop-filter:blur(16px)}
.hw-card:hover{transform:perspective(700px) rotateX(1.7deg) rotateY(-1.2deg) translateY(-3px);border-color:#50d4bc88;box-shadow:0 23px 40px #0007,0 0 26px #50d4bc10}
.hw-card:before{content:"";position:absolute;left:0;bottom:0;width:15px;height:15px;border-bottom:1px solid #8b7cff88;border-left:1px solid #8b7cff88;border-radius:0 0 0 10px}
.stButton>button,.stDownloadButton>button{box-shadow:inset 0 1px #d6fbff15,0 4px 12px #0004;min-height:39px}
.stButton>button:active{transform:translateY(1px)!important;box-shadow:inset 0 2px 8px #0008}
.hw-top{display:flex;align-items:center;justify-content:space-between;gap:15px;padding:10px 15px;border:1px solid #2b4659;border-radius:12px;background:#0a1727dd;backdrop-filter:blur(18px);margin-bottom:14px}
.hw-brand{font:700 18px 'Space Grotesk',sans-serif;letter-spacing:-.06em;color:#e7f0fa}
.hw-globe{display:inline-flex;align-items:center;justify-content:center;margin-right:10px;border:1px solid #50d4bc88;color:#8fe8dc;border-radius:50%;width:32px;height:32px;box-shadow:inset 0 0 13px #50d4bc44,0 0 16px #50d4bc22}
.hw-heading{font:700 29px 'Space Grotesk',sans-serif;color:#e7f0fa;letter-spacing:-.04em;margin:12px 0}
.hw-kicker{font:600 10px 'JetBrains Mono',monospace;color:#8fe8dc;letter-spacing:.16em;text-transform:uppercase}
.hw-step{color:#d8edf7;font:13px 'Inter',sans-serif;padding:14px;background:#102237;border:1px solid #2b4659;border-radius:9px;margin:8px 0}
.hw-gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin-top:20px}
.hw-gallery-cell{min-height:105px;border-radius:12px;border:1px solid #2b4659;background:radial-gradient(circle at 80% 15%,#8b7cff1c,transparent),linear-gradient(130deg,#0d2036,#102237);padding:18px;position:relative;overflow:hidden}
.hw-gallery-cell b{color:#e7f0fa}.hw-gallery-cell small{display:block;color:#a5b8ca;margin-top:6px;line-height:1.4}
.hw-layer{font:600 11px 'JetBrains Mono',monospace;color:#8fe8dc;letter-spacing:.12em}
.hw-status-table{width:100%;border-collapse:collapse}.hw-status-table th,.hw-status-table td{border-bottom:1px solid #2b4659;padding:10px;text-align:left;font-size:12px}.hw-status-table th{color:#8fe8dc;font-size:10px;letter-spacing:.08em}
.hw-ring{display:flex;align-items:center;gap:19px;border:1px solid #2b4659;background:#102237;border-radius:12px;padding:14px;margin:12px 0}.hw-ring-visual{width:79px;height:79px;border-radius:50%;display:grid;place-items:center;flex-shrink:0}.hw-ring-core{width:60px;height:60px;border-radius:50%;background:#0a1727;display:grid;place-items:center;font:600 17px 'JetBrains Mono',monospace;color:#e7f0fa}
@media(max-width:760px){.hw-moon{right:6%;opacity:.32}.hw-orbit{opacity:.32}.hw-gallery{grid-template-columns:1fr}.hw-top{flex-wrap:wrap}.hw-hero{min-height:270px}.hw-ridge{opacity:.4;width:100%}}
/* Final layout pass: give hero text a protected readable region, keep art to the right. */
.hw-hero{min-height:275px;padding:30px 35px 32px}
.hw-hero .hw-head,.hw-hero .hw-sub,.hw-hero .hw-mark{position:relative;z-index:3;max-width:59%}
.hw-hero .hw-head{font-size:clamp(2rem,3.25vw,3.05rem);line-height:1.11;letter-spacing:-.045em}
.hw-hero .hw-sub{max-width:58%;font-size:13px;line-height:1.6}
.hw-ridge{right:-5%;width:59%;opacity:.73;z-index:1}
.hw-moon,.hw-orbit{z-index:2}
/* Better control legibility, avoid clipped labels without affecting state. */
.stApp [data-testid="stMetricLabel"]{min-height:2.5rem;line-height:1.25;white-space:normal!important;overflow:visible!important}
.stApp [data-testid="stMetricLabel"] *{white-space:normal!important;text-overflow:clip!important;overflow:visible!important}
.stButton>button,.stDownloadButton>button{white-space:normal!important;min-height:42px;line-height:1.3;padding:7px 10px}
[data-testid="stSidebar"] .stButton>button{font-size:13px}
[data-testid="stSidebar"]{background:#102237}
/* Keep phone and narrow-window controls usable. */
@media(max-width:1000px){.hw-hero .hw-head,.hw-hero .hw-sub{max-width:68%}.hw-ridge{opacity:.5}}
@media(max-width:700px){.hw-hero{min-height:265px;padding:24px 20px}.hw-hero .hw-head,.hw-hero .hw-sub,.hw-hero .hw-mark{max-width:100%}.hw-hero .hw-head{font-size:2.15rem}.hw-ridge{opacity:.17;width:100%}.hw-moon,.hw-orbit{opacity:.16}}
@media(prefers-reduced-motion:reduce){.stApp:before,.stApp:after,.hw-hero:before,.hw-ridge,.hw-orbit:after{animation:none!important}.hw-card:hover{transform:none!important}}
.effects-reduced .stApp:before,.effects-reduced .stApp:after{animation:none!important}

""" + ("""
/* Accessibility setting: animation, parallax, and 3D hover are off. */
.stApp:before,.stApp:after,.hw-hero:before,.hw-ridge,.hw-orbit:after{animation:none!important}
.hw-card:hover{transform:none!important}
*{scroll-behavior:auto!important;transition:none!important}
""" if st.session_state.hw_effects == "Reduced" else "") + """
</style>
""", unsafe_allow_html=True)

DATA_PATH = Path("data/chungthang_roads.graphml")
LAKES_PATH = Path("data/lakes.json")
OVERLAY_INDEX = Path("data/overlays/overlays.json")
OVERLAY_ROOT = Path("data/overlays")
ASSET_ROOT = Path("assets")
# Bhuvan services are optional and never guessed. Put exact metadata discovered
# from GetCapabilities here, or load offline snapshots via overlays.json.
ISRO_LAYERS: dict[str, dict[str, str]] = {
    # "bhuvan_live": {"wms": "OFFICIAL_PUBLIC_WMS_URL", "layer": "EXACT_ADVERTISED_LAYER"},
}

if not DATA_PATH.exists():
    st.error("Road-network data missing. Run python download_roads.py first.")
    st.stop()

@st.cache_resource
def load_network() -> nx.MultiDiGraph:
    return ox.io.load_graphml(DATA_PATH)

G = load_network()
# Keep the ORIGINAL simplified undirected connection construction. Its
# hub reachability and path lengths must stay comparable to previous runs.
U = nx.Graph()
U.add_nodes_from(G.nodes(data=True))
for u, v, data in G.edges(data=True):
    if u != v and not U.has_edge(u, v):
        U.add_edge(u, v, **data)

def normalized_edge(u: Any, v: Any) -> tuple[Any, Any]:
    return tuple(sorted((u, v), key=str))

edge_pairs = sorted([normalized_edge(u, v) for u, v in U.edges], key=lambda pair: (str(pair[0]), str(pair[1])))
edge_lookup = {f"E{i:03d}": pair for i, pair in enumerate(edge_pairs, 1)}
pair_to_id = {pair: code for code, pair in edge_lookup.items()}
critical_pairs = {normalized_edge(u, v) for u, v in nx.bridges(U)}
critical_ids = [code for code, pair in edge_lookup.items() if pair in critical_pairs]
nodes = list(U.nodes)
north = max(nodes, key=lambda n: float(U.nodes[n]["y"]))
south = min(nodes, key=lambda n: float(U.nodes[n]["y"]))
east = max(nodes, key=lambda n: float(U.nodes[n]["x"]))
west = min(nodes, key=lambda n: float(U.nodes[n]["x"]))
destinations = {"Northern corridor": north, "Southern corridor": south, "Eastern corridor": east, "Western corridor": west}
default_hub = min(nodes, key=lambda n: ((float(U.nodes[n]["y"]) - 27.606) ** 2 + (float(U.nodes[n]["x"]) - 88.647) ** 2))

# Save geometries once. The original app uses the selected edge record from U.
@st.cache_data(show_spinner=False)
def prepared_geometry() -> dict[str, list[list[float]]]:
    out: dict[str, list[list[float]]] = {}
    for u, v, data in U.edges(data=True):
        geometry = data.get("geometry")
        if geometry is not None and hasattr(geometry, "coords"):
            out[pair_to_id[normalized_edge(u, v)]] = [[lat, lon] for lon, lat in geometry.coords]
        else:
            out[pair_to_id[normalized_edge(u, v)]] = [[float(U.nodes[u]["y"]), float(U.nodes[u]["x"])], [float(U.nodes[v]["y"]), float(U.nodes[v]["x"])]]
    return out

edge_coords = prepared_geometry()

@st.cache_data(show_spinner=False)
def critical_impacts(hub_id: Any) -> list[dict[str, Any]]:
    baseline = set(nx.node_connected_component(U, hub_id))
    output = []
    for code in critical_ids:
        test = U.copy()
        test.remove_edge(*edge_lookup[code])
        lost = baseline - set(nx.node_connected_component(test, hub_id))
        output.append({"Link": code, "Nodes isolated": len(lost), "Destinations isolated": sum(n in lost for n in destinations.values())})
    return sorted(output, key=lambda row: (-row["Nodes isolated"], row["Link"]))

def label_link(code: str) -> str:
    u, v = edge_lookup[code]
    data = U[u][v]
    name = data.get("name")
    if isinstance(name, (list, tuple)):
        name = ", ".join(map(str, name))
    road_name = str(name).strip() if name else str(data.get("highway", "mapped road"))
    if len(road_name) > 38:
        road_name = road_name[:35] + "…"
    length = data.get("length")
    try:
        length_label = f" · {float(length):.0f} m"
    except (ValueError, TypeError):
        length_label = ""
    return f"{code} · {road_name}{length_label}" + (" · CRITICAL" if code in critical_ids else "")

@st.cache_data(show_spinner=False)
def load_satellite_context() -> tuple[dict[str, Any] | None, str | None]:
    if not LAKES_PATH.exists():
        return None, "No data/lakes.json found. Run your lake-data pipeline to populate satellite context."
    try:
        raw = json.loads(LAKES_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("lakes"), list):
            return raw, None
        return None, "lakes.json must contain a 'lakes' list and an optional 'meta' object."
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Could not read lakes.json: {exc}"

lake_data, lake_error = load_satellite_context()
lakes = lake_data.get("lakes", []) if lake_data else []
lake_meta = lake_data.get("meta", {}) if lake_data else {}
lake_is_demo = bool(lake_meta.get("demo", True)) if lake_data else False

def intersecting_codes(lake: dict[str, Any]) -> list[str]:
    if shape is None or LineString is None:
        return []
    raw = lake.get("corridor_buffer")
    if not isinstance(raw, dict):
        return []
    try:
        polygon = shape(raw.get("geometry", raw))
        if polygon.is_empty or not polygon.is_valid:
            return []
        return [code for code, coords in edge_coords.items() if LineString([(lon, lat) for lat, lon in coords]).intersects(polygon)]
    except (ValueError, TypeError, KeyError):
        return []

# ── Authentic data status and local-only overlays ──────────────────────────
@st.cache_data(show_spinner=False)
def load_overlay_manifest() -> dict[str, Any]:
    if not OVERLAY_INDEX.is_file():
        return {"layers": {}}
    try:
        data = json.loads(OVERLAY_INDEX.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and isinstance(data.get("layers"), dict) else {"layers": {}}
    except (OSError, json.JSONDecodeError):
        return {"layers": {}}

overlay_manifest = load_overlay_manifest()

def safe_overlay(key: str) -> tuple[Path, dict[str, Any]] | None:
    item = overlay_manifest["layers"].get(key)
    if not isinstance(item, dict):
        return None
    # No path traversal; overlay metadata can only refer to local files.
    rel = Path(str(item.get("file", "")))
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.suffix.lower() != ".png":
        return None
    file = (OVERLAY_ROOT / rel).resolve()
    if not file.is_file() or OVERLAY_ROOT.resolve() not in file.parents:
        return None
    bounds = item.get("bounds")
    try:
        assert len(bounds) == 2 and len(bounds[0]) == 2 and len(bounds[1]) == 2
        b = [[float(v) for v in pair] for pair in bounds]
        assert -90 <= b[0][0] < b[1][0] <= 90 and -180 <= b[0][1] < b[1][1] <= 180
    except (TypeError, ValueError, AssertionError, IndexError):
        return None
    return file, dict(item, bounds=b)

def layer_status() -> list[dict[str, str]]:
    rows = [{"Layer": "OSM road graph", "Status": "Loaded", "Source": "OpenStreetMap contributors", "Retrieved": "Date not recorded in GraphML", "Area": "Chungthang pilot"}]
    sources = {
        "bhuvan_x": "Bhuvan, ISRO/NRSC",
        "hillshade": "Bhoonidhi / CartoDEM (NRSC)",
        "rainfall": "MOSDAC / GSMap ISRO (SAC-ISRO)",
    }
    cfg = ISRO_LAYERS.get("bhuvan_live", {})
    if cfg.get("wms") and cfg.get("layer"):
        rows.append({"Layer": "Bhuvan public WMS", "Status": "Configured (online; unverified)", "Source": "Bhuvan, ISRO/NRSC", "Retrieved": "Provider service — not locally saved", "Area": "Service extent unverified"})
    else:
        rows.append({"Layer": "Bhuvan public WMS", "Status": "Not configured", "Source": "Bhuvan, ISRO/NRSC", "Retrieved": "Not supplied", "Area": "Not supplied"})
    for key, source in sources.items():
        active = safe_overlay(key)
        item = active[1] if active else overlay_manifest["layers"].get(key, {})
        if not isinstance(item, dict):
            item = {}
        rows.append({"Layer": key, "Status": "Loaded" if active else "Not loaded", "Source": str(item.get("source") or source), "Retrieved": str(item.get("date") or "Not supplied"), "Area": str(item.get("area") or ("Bounds in manifest" if active else "Not supplied"))})
    return rows

@st.cache_data(show_spinner=False)
def optional_asset_data(name: str) -> str | None:
    if name not in {"hero_night_himalaya.jpg", "moon.png", "satellite_orbit.png", "glacial_lake_night.jpg", "road_valley_night.jpg"}:
        return None
    f = ASSET_ROOT / name
    if not f.is_file() or f.stat().st_size > 420_000:
        return None
    mime = mimetypes.guess_type(f.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(f.read_bytes()).decode('ascii')}"

# ── Evidence and independent analytical checks ─────────────────────────────
def valid_weighted_lengths(graph: nx.Graph) -> bool:
    """True only when every edge has a finite, non-negative length in metres."""
    try:
        return graph.number_of_edges() > 0 and all(
            "length" in data and math.isfinite(float(data["length"]))
            and float(data["length"]) >= 0
            for _, _, data in graph.edges(data=True)
        )
    except (ValueError, TypeError, OverflowError):
        return False


@st.cache_data(show_spinner=False)
def audit_static_graph() -> list[dict[str, str]]:
    """Checks independent of the currently selected scenario."""
    checks = []
    checks.append({"Check": "Source file present", "Result": "PASS" if DATA_PATH.is_file() else "FAIL", "Evidence": "Local GraphML exists; presence does not validate source accuracy"})
    checks.append({"Check": "Geographic coordinates", "Result": "PASS" if all(
        -90 <= float(d.get("y", 999)) <= 90 and -180 <= float(d.get("x", 999)) <= 180 for _, d in U.nodes(data=True)
    ) else "FAIL", "Evidence": "Every graph node has numeric latitude/longitude in valid ranges"})
    checks.append({"Check": "All four reference points mapped", "Result": "PASS" if all(n in U for n in destinations.values()) else "FAIL", "Evidence": "Directional extremes correspond to graph nodes; NOT verified facilities"})
    checks.append({"Check": "Baseline graph connectivity", "Result": "PASS" if nx.is_connected(U) else "REVIEW", "Evidence": f"{nx.number_connected_components(U)} undirected component(s); disconnected components may be valid"})
    computed = {normalized_edge(u,v) for u,v in nx.bridges(U)}
    checks.append({"Check": "Graph bridges independently recomputed", "Result": "PASS" if computed == critical_pairs else "FAIL", "Evidence": f"{len(computed)} bridge edges compared against displayed critical-link set"})
    checks.append({"Check": "Length data coverage", "Result": "PASS" if valid_weighted_lengths(U) else "NOT AVAILABLE", "Evidence": "Network distance is reported only with complete, valid edge lengths"})
    return checks


def audit_scenario(base: nx.Graph, altered: nx.Graph, repaired: nx.Graph, origin: Any,
                   closures: list[str], restoration: str) -> list[dict[str, str]]:
    """Runtime invariants to make a demonstrable, reproducible QA panel."""
    b = set(nx.node_connected_component(base, origin))
    a = set(nx.node_connected_component(altered, origin))
    r = set(nx.node_connected_component(repaired, origin))
    only_selected_removed = {
        normalized_edge(u, v) for u, v in base.edges()
        if not altered.has_edge(u, v)
    } == {edge_lookup[k] for k in closures}
    monotone = a.issubset(b) and a.issubset(r) and r.issubset(b)
    same_nodes = base.number_of_nodes() == altered.number_of_nodes() == repaired.number_of_nodes()
    restoration_edges_ok = ((set(map(lambda e: normalized_edge(*e), repaired.edges())) -
                            set(map(lambda e: normalized_edge(*e), altered.edges()))) ==
                            ({edge_lookup[restoration]} if restoration != "None" else set()))
    return [
        {"Check": "Only selected road connections removed", "Result": "PASS" if only_selected_removed else "FAIL", "Evidence": f"{len(closures)} selected unique road links"},
        {"Check": "No vertices created or deleted", "Result": "PASS" if same_nodes else "FAIL", "Evidence": "Node IDs preserved across all three graph states"},
        {"Check": "Closures cannot increase accessibility", "Result": "PASS" if a.issubset(b) else "FAIL", "Evidence": "Reachable nodes after closures must be a subset of baseline"},
        {"Check": "Restoration cannot reduce accessibility", "Result": "PASS" if monotone else "FAIL", "Evidence": "Baseline ≥ restoration ≥ disruption for reachable node sets"},
        {"Check": "Only the chosen link is restored", "Result": "PASS" if restoration_edges_ok else "FAIL", "Evidence": restoration if restoration != "None" else "No link selected"},
    ]


def weighted_corridor_comparison(base: nx.Graph, altered: nx.Graph, repaired: nx.Graph,
                                 origin: Any) -> list[dict[str, str]]:
    """Supplementary network distances; does NOT change existing CSV results."""
    if not valid_weighted_lengths(base):
        return []
    entries = []
    for name, target in destinations.items():
        dists = []
        for network in (base, altered, repaired):
            if nx.has_path(network, origin, target):
                distance = nx.shortest_path_length(network, origin, target, weight="length")
                dists.append(float(distance))
            else:
                dists.append(None)
        def fmt(value: float | None) -> str:
            return f"{value / 1000:.2f} km" if value is not None else "Disconnected"
        detour = (dists[1] - dists[0]) / 1000 if dists[0] is not None and dists[1] is not None else None
        entries.append({"Reference point": name, "Baseline": fmt(dists[0]),
                        "After closure": fmt(dists[1]), "After restoration": fmt(dists[2]),
                        "Additional network distance": f"+{detour:.2f} km" if detour is not None and detour > 0.0001 else ("0.00 km" if detour is not None else "Not available")})
    return entries



# ── Additional planning intelligence (keeps legacy outputs unchanged) ────
def restoration_priorities(disrupted_graph: nx.Graph, base_graph: nx.Graph,
                           hub_id: Any, closed_codes: list[str],
                           reference_points: dict[str, Any]) -> list[dict[str, Any]]:
    """Rank reopening *each currently closed link* by marginal access recovered.

    Compares reopening one link with the currently disrupted network. It is not
    a repair-cost, population-risk, or emergency-response priority model.
    """
    reachable_now = set(nx.node_connected_component(disrupted_graph, hub_id))
    output: list[dict[str, Any]] = []
    for code in closed_codes:
        candidate = disrupted_graph.copy()
        u, v = edge_lookup[code]
        candidate.add_edge(u, v, **base_graph[u][v])
        recovered = set(nx.node_connected_component(candidate, hub_id)) - reachable_now
        output.append({
            "Link": code,
            "Road description": label_link(code),
            "Nodes reconnected": len(recovered),
            "Reference destinations reconnected": sum(n in recovered for n in reference_points.values()),
        })
    return sorted(output, key=lambda row: (-row["Reference destinations reconnected"],
                                            -row["Nodes reconnected"], row["Link"]))


def nearest_graph_node(lat: float, lon: float) -> tuple[Any, float]:
    """Return nearest mapped graph node and approximate straight-line separation, m."""
    earth_radius_m = 6371008.8
    lat1 = math.radians(lat)
    def distance(node: Any) -> float:
        nlat = math.radians(float(U.nodes[node]["y"]))
        delta_lat = nlat - lat1
        delta_lon = math.radians(float(U.nodes[node]["x"]) - lon)
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(nlat) * math.sin(delta_lon / 2) ** 2
        return 2 * earth_radius_m * math.asin(min(1.0, math.sqrt(a)))
    node = min(U.nodes, key=distance)
    return node, distance(node)


def source_declared_points(csv_bytes: bytes) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate *user-provided* destinations. Names/sources are never invented."""
    import io
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    try:
        reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
        required = {"name", "latitude", "longitude", "category", "source"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return [], ["CSV needs columns: name,latitude,longitude,category,source"]
        for index, record in enumerate(reader, 2):
            if len(rows) >= 100:
                issues.append("Only the first 100 valid points are analysed.")
                break
            try:
                lat = float(record["latitude"])
                lon = float(record["longitude"])
                name = (record["name"] or "").strip()
                category = (record["category"] or "").strip()
                source = (record["source"] or "").strip()
                if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("invalid coordinates")
                if not (name and category and source):
                    raise ValueError("name, category and source are required")
                node, distance_m = nearest_graph_node(lat, lon)
                rows.append({"Name": name, "Category": category, "User-supplied source": source,
                             "Nearest mapped node": node, "Offset from node (m)": round(distance_m),
                             "Within 1000 m": distance_m <= 1000})
            except (TypeError, ValueError, KeyError) as exc:
                issues.append(f"Line {index}: {exc}")
    except UnicodeDecodeError:
        return [], ["Please upload a UTF-8 CSV file."]
    return rows, issues

# ── Session state & top bar ────────────────────────────────────────────────
for key, default in {
    "hw_hub": default_hub, "hw_closures": critical_ids[:1], "hw_restore": "None",
    "hw_view": "After closure", "hw_page": "Mission Brief",
    "hw_presentation": False, "hw_tour": 0, "hw_tour_enabled": False, "hw_navigation": "Mission Brief",
    "hw_lake_id": "", "hw_basemap": "Night", "hw_effects": "Full", "hw_map_mode": "2D", "hw_camera": "Overview", "hw_layers": ["Roads", "Critical links", "Closed links", "Lost nodes", "Destinations", "Hub"],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Closure and restore widgets are synced via their state keys.
def apply_closures(codes: list[str]) -> None:
    st.session_state.hw_closures = list(dict.fromkeys([code for code in codes if code in edge_lookup]))
    if st.session_state.hw_restore not in st.session_state.hw_closures:
        st.session_state.hw_restore = "None"

def reset_scenario() -> None:
    st.session_state.hw_hub = default_hub
    st.session_state.hw_hub_choice = "Chungthang town centre (reference node)"
    st.session_state.hw_raw_node = default_hub
    apply_closures(critical_ids[:1])
    st.session_state.hw_restore = "None"
    st.session_state.hw_view = "After closure"

def navigate(page: str) -> None:
    st.session_state.hw_page = page
    st.session_state.hw_navigation = page

def navigation_changed() -> None:
    st.session_state.hw_page = st.session_state.hw_navigation

def go_to_workspace(code: str) -> None:
    apply_closures([code])
    navigate("Scenario Workspace")

def close_worst_link() -> None:
    impacts = critical_impacts(st.session_state.hw_hub)
    if impacts:
        apply_closures([impacts[0]["Link"]])

def activate_tour() -> None:
    st.session_state.hw_tour_enabled = True
    st.session_state.hw_tour = 0
    navigate("Scenario Workspace")

def tour_back() -> None:
    st.session_state.hw_tour = max(0, st.session_state.hw_tour - 1)

def tour_next() -> None:
    idx = st.session_state.hw_tour
    if idx == 3:
        st.session_state.hw_tour_enabled = False
        return
    st.session_state.hw_tour += 1
    if idx == 0:
        impacts = critical_impacts(st.session_state.hw_hub)
        if impacts:
            go_to_workspace(impacts[0]["Link"])
    if idx == 2 and st.session_state.hw_closures:
        st.session_state.hw_restore = st.session_state.hw_closures[0]

def tour_exit() -> None:
    st.session_state.hw_tour_enabled = False

def use_satellite_links(links: list[str]) -> None:
    apply_closures(links)
    st.session_state.hw_layers = list(dict.fromkeys(st.session_state.hw_layers + ["Satellite corridor"]))
    navigate("Scenario Workspace")

hero_svg = '''<svg class="hw-ridge" viewBox="0 0 900 320" aria-hidden="true"><defs><linearGradient id="snow" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#b2dfff" stop-opacity=".6"/><stop offset="1" stop-color="#1a3858" stop-opacity=".35"/></linearGradient></defs><path d="M0 300 92 212 150 235 300 51 359 144 423 88 508 201 587 71 700 222 787 139 900 271v49H0Z" fill="url(#snow)"/><path d="m249 129 51-78 54 87-43-37-18 21-11-9Z" fill="#e8f1ff" opacity=".75"/><path d="m554 121 33-50 42 84-37-36-10 14Z" fill="#e8f1ff" opacity=".5"/><path d="M0 320 82 257 158 286 275 160 354 272 469 194 531 249 646 156 724 286 811 212 900 281v39Z" fill="#0c2c45"/><path d="M0 320 120 286 242 304 327 234 413 307 523 255 614 300 734 237 900 301v19Z" fill="#07172b"/><g fill="#f9de9a"><circle cx="110" cy="304" r="1.6"/><circle cx="145" cy="300" r="2"/><circle cx="670" cy="288" r="1.5"/><circle cx="717" cy="279" r="1.8"/></g></svg>'''
hero_img = optional_asset_data("hero_night_himalaya.jpg")
hero_img_style = f' style="background-image:linear-gradient(100deg,#09172cf5,#09172c80),url({hero_img});background-size:cover;background-position:center"' if hero_img else ""
st.markdown(f'''<div class="hw-top"><span class="hw-brand"><span class="hw-globe">◉</span> HimaWatch <small style="font:600 10px JetBrains Mono,monospace;color:#8fe8dc;letter-spacing:.1em;margin-left:9px">NIGHT OPERATIONS</small></span><span class="hw-micro">SILENT SUPERNOVA · ASTRA 2026 · DOMAIN 03</span></div><div class="hw-hero"{hero_img_style}><div class="hw-galaxy"></div><div class="hw-orbit"></div><div class="hw-moon"></div><div class="hw-mark">◈  HIMALAYAN DISASTER ACCESS / RESEARCH PROTOTYPE</div><div class="hw-head">Where the road ends,<br>the analysis begins.</div><div class="hw-sub">Explore hypothetical disruptions in the Chungthang road network. Compare lost access, restoration possibilities and—when available—documented Indian satellite-derived context.</div>{hero_svg}</div>''', unsafe_allow_html=True)
st.caption("Illustrative artwork, not satellite imagery")

status_left, status_right = st.columns([4, 1], gap="medium")
with status_left:
    st.markdown(f'<div class="hw-status"><span class="hw-chip">● LOCAL MODEL LOADED</span><span class="hw-chip">CHUNGTHANG / OSM</span><span class="hw-chip">{U.number_of_nodes()} NODES / {U.number_of_edges()} LINKS</span><span class="hw-chip warn">HYPOTHETICAL · NOT LIVE</span></div>', unsafe_allow_html=True)
with status_right:
    components.html('''<div style="text-align:right;font:11px monospace;color:#a5b8ca;padding-top:5px">UTC / IST<br><span id="clock" style="color:#e7f0fa;font-size:13px">--:--:--</span></div><script>function tick(){document.getElementById('clock').textContent=new Date().toLocaleTimeString('en-GB',{timeZone:'UTC',hour12:false})+' / '+new Date().toLocaleTimeString('en-GB',{timeZone:'Asia/Kolkata',hour12:false});}tick();setInterval(tick,1000)</script>''', height=50)

nav_col, toggle_col, guide_col, effect_col = st.columns([4.8, 1.25, 1.4, 1.4], gap="small")
PAGES = ["Mission Brief", "Scenario Workspace", "Critical Links", "Evaluation Evidence", "Destination Evidence", "Data Layers", "Satellite Context", "3D View", "Method & Data", "Team"]
with nav_col:
    st.selectbox("Navigate", PAGES, key="hw_navigation", on_change=navigation_changed, label_visibility="collapsed")
with toggle_col:
    st.toggle("Present", key="hw_presentation", help="Show a larger map and hide secondary captions")
with guide_col:
    st.button("Guided demo", use_container_width=True, on_click=activate_tour)
with effect_col:
    st.selectbox("Effects", ["Full", "Reduced"], key="hw_effects", label_visibility="collapsed")

if st.session_state.hw_tour_enabled:
    steps = [
        "01 / Select the Chungthang reference hub. It is an illustrative network origin, not a verified relief facility.",
        "02 / Close a graph-critical connection to see which parts of the mapped network lose access.",
        "03 / Compare the baseline with the disruption and read the destination access report.",
        "04 / Restore the selected link and watch accessibility return. These results describe topology, not road safety.",
    ]
    idx = st.session_state.hw_tour
    st.markdown(f'<div class="hw-synopsis"><span class="hw-micro">GUIDED DEMONSTRATION · {idx+1}/4</span><br>{escape(steps[idx])}</div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 4])
    with b1:
        st.button("← Back", disabled=idx == 0, key="tour_back", on_click=tour_back)
    with b2:
        st.button("Next →" if idx < 3 else "Finish", key="tour_next", on_click=tour_next)
    with b3:
        st.button("Exit tour", key="tour_exit", on_click=tour_exit)

# Named selectors do not change the node IDs or calculation model.
named_hubs = {"Chungthang town centre (reference node)": default_hub}
for name, node in destinations.items():
    named_hubs[name + " (reference point)"] = node

# For display when current hub is a raw node from Advanced.
def hub_label(n: Any) -> str:
    return next((name for name, node in named_hubs.items() if node == n), f"Advanced node · {n}")

def choose_named_hub() -> None:
    chosen = st.session_state.hw_hub_choice
    if chosen in named_hubs:
        st.session_state.hw_hub = named_hubs[chosen]
        st.session_state.hw_raw_node = named_hubs[chosen]

def choose_raw_hub() -> None:
    st.session_state.hw_hub = st.session_state.hw_raw_node
    st.session_state.hw_hub_choice = hub_label(st.session_state.hw_raw_node)


# ── Sidebar: task-first command center ───────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hw-kicker">OPERATOR CONSOLE</div>', unsafe_allow_html=True)
    st.subheader("Command Center")
    st.caption("Local graph, keyless mapping, hypothetical disruption scenarios")
    if st.button("Open scenario lab", use_container_width=True, on_click=navigate, args=("Scenario Workspace",)):
        pass
    st.button("Close most critical link", use_container_width=True, on_click=close_worst_link)
    st.button("Close all critical links", use_container_width=True, on_click=apply_closures, args=(critical_ids,))
    st.button("Clear closures", use_container_width=True, on_click=apply_closures, args=([],))
    st.button("Reset scenario", use_container_width=True, on_click=reset_scenario)
    st.divider()
    st.selectbox("Map basemap", ["Night", "Streets", "Space void (no tiles)"], key="hw_basemap")
    st.multiselect("Map layers", ["Roads", "Critical links", "Closed links", "Lost nodes", "Reachable nodes", "Destinations", "Hub", "Satellite corridor", "Bhuvan WMS", "Bhuvan snapshot", "CartoDEM hillshade", "MOSDAC rainfall"], key="hw_layers")
    st.markdown('<div class="hw-kicker">DATA STATUS</div>', unsafe_allow_html=True)
    for row in layer_status():
        dot = "●" if row["Status"] == "Loaded" else "○"
        st.caption(f'{dot} {row["Layer"]} — {row["Status"]}')
    with st.expander("Help / keyboard & workflow"):
        st.write("1. Open Scenario Lab and choose a reference hub.\n\n2. Mark links as hypothetically closed.\n\n3. Inspect lost graph connectivity.\n\n4. Restore one link and compare.\n\n5. Export your result, and describe limitations.")
        st.caption("This is not flood prediction, real-time road status, emergency routing or field validation.")

# All views share one computed scenario, exactly as in the original app.
hub = st.session_state.hw_hub
closed = [c for c in st.session_state.hw_closures if c in edge_lookup]
restore = st.session_state.hw_restore if st.session_state.hw_restore in closed else "None"
disrupted = U.copy()
for code in closed:
    u, v = edge_lookup[code]
    if disrupted.has_edge(u, v):
        disrupted.remove_edge(u, v)
baseline_reachable = set(nx.node_connected_component(U, hub))
current_reachable = set(nx.node_connected_component(disrupted, hub))
lost_nodes = baseline_reachable - current_reachable
restored = disrupted.copy()
if restore != "None":
    u, v = edge_lookup[restore]
    restored.add_edge(u, v, **U[u][v])
restored_reachable = set(nx.node_connected_component(restored, hub))
regained_nodes = restored_reachable - current_reachable
results = []
for name, node in destinations.items():
    baseline_status = node in baseline_reachable
    current_status = node in current_reachable
    restored_status = node in restored_reachable
    path_length = nx.shortest_path_length(disrupted, source=hub, target=node) if current_status else None
    results.append({
        "Destination": name,
        "Baseline": "Reachable" if baseline_status else "Disconnected",
        "After closure": "Reachable" if current_status else "Disconnected",
        "After restoration": "Reachable" if restored_status else "Disconnected",
        "Path (links)": path_length if path_length is not None else "—",
    })
lost_destinations = sum(n in baseline_reachable and n not in current_reachable for n in destinations.values())
regained_destinations = sum(n not in current_reachable and n in restored_reachable for n in destinations.values())

# Optional length of inaccessible edges, not a travel distance estimate.
cutoff_km = None
try:
    isolated_edges = [(u, v) for u, v in disrupted.edges() if u in lost_nodes and v in lost_nodes]
    if isolated_edges and all("length" in U[u][v] for u, v in isolated_edges):
        lengths = [float(U[u][v]["length"]) for u, v in isolated_edges]
        if all(x >= 0 for x in lengths):
            cutoff_km = sum(lengths) / 1000
except (KeyError, TypeError, ValueError):
    cutoff_km = None

impact_ratio = len(lost_nodes) / len(baseline_reachable) if baseline_reachable else 0
impact_name = ("Low" if impact_ratio < .1 else "Moderate" if impact_ratio < .25 else "High" if impact_ratio < .5 else "Severe")

# Satellite overlay selection, if any.
selected_lake = next((lake for lake in lakes if str(lake.get("id")) == st.session_state.hw_lake_id), None)
selected_lake_links = intersecting_codes(selected_lake) if selected_lake else []

def draw_map(view: str, layers: list[str], big: bool = False) -> folium.Map:
    lats = [float(U.nodes[n]["y"]) for n in U.nodes]
    lons = [float(U.nodes[n]["x"]) for n in U.nodes]
    fmap = folium.Map(location=[sum(lats) / len(lats), sum(lons) / len(lons)], zoom_start=13, tiles=None, control_scale=True, prefer_canvas=True)
    # The night map is rendered from the same keyless OpenStreetMap tiles,
    # darkened via CSS. This avoids CARTO's API-key watermark on some networks.
    # "Space void" uses no remote basemap at all.
    if st.session_state.hw_basemap in ("Night", "Streets"):
        folium.TileLayer(tiles="OpenStreetMap", name="OpenStreetMap", control=False).add_to(fmap)
        if st.session_state.hw_basemap == "Night":
            fmap.get_root().header.add_child(folium.Element("""
            <style>
            .leaflet-tile-pane img.leaflet-tile {
              filter: brightness(.72) invert(1) contrast(1.08)
                      hue-rotate(180deg) saturate(.60);
            }
            .leaflet-container { background: #0b1829; }
            </style>
            """))
    # Space void intentionally has no map tiles, so the downloaded road graph
    # remains fully usable offline.
    overlays = {name: folium.FeatureGroup(name=name, show=name in layers) for name in ["Roads", "Critical links", "Closed links", "Lost nodes", "Reachable nodes", "Destinations", "Hub", "Satellite corridor", "Bhuvan WMS", "Bhuvan snapshot", "CartoDEM hillshade", "MOSDAC rainfall"]}
    closed_pairs = {edge_lookup[code] for code in closed}
    highlighted_reach = baseline_reachable if view == "Baseline" else restored_reachable if view == "After restoration" else current_reachable
    if "Roads" in layers or "Critical links" in layers or "Closed links" in layers:
        for code, coords in edge_coords.items():
            pair = edge_lookup[code]
            is_closed = view != "Baseline" and pair in closed_pairs and not (view == "After restoration" and code == restore)
            if "Roads" in layers:
                folium.PolyLine(coords, color=TEAL if pair[0] in highlighted_reach and pair[1] in highlighted_reach else "#687d8c", weight=3.5, opacity=.8).add_to(overlays["Roads"])
            if code in critical_ids and "Critical links" in layers:
                folium.PolyLine(coords, color=AMBER, weight=5, opacity=.75, tooltip=label_link(code)).add_to(overlays["Critical links"])
            if is_closed and "Closed links" in layers:
                folium.PolyLine(coords, color=RED, weight=6, dash_array="8,7", opacity=1, tooltip=f"{code} — simulated closure").add_to(overlays["Closed links"])
    if "Lost nodes" in layers:
        for node in baseline_reachable - highlighted_reach:
            folium.CircleMarker([float(U.nodes[node]["y"]), float(U.nodes[node]["x"])], radius=4, color=RED, fill=True, fill_color=RED, tooltip="Network node losing reference-hub access").add_to(overlays["Lost nodes"])
    if "Reachable nodes" in layers:
        for node in highlighted_reach:
            folium.CircleMarker([float(U.nodes[node]["y"]), float(U.nodes[node]["x"])], radius=2, color=AURORA, fill=True, fill_color=AURORA).add_to(overlays["Reachable nodes"])
    if "Destinations" in layers:
        for name, node in destinations.items():
            available = node in highlighted_reach
            folium.CircleMarker([float(U.nodes[node]["y"]), float(U.nodes[node]["x"])], radius=7, color=TEAL if available else RED, fill=True, fill_opacity=1, tooltip=f"{name} · {'Reachable' if available else 'Disconnected'}").add_to(overlays["Destinations"])
    if "Hub" in layers:
        folium.CircleMarker([float(U.nodes[hub]["y"]), float(U.nodes[hub]["x"])], radius=10, color="#f7fbff", weight=2, fill=True, fill_color=AMBER, tooltip=f"Hub: {hub_label(hub)}").add_to(overlays["Hub"])
    if selected_lake and selected_lake.get("corridor_buffer") and "Satellite corridor" in layers:
        try:
            folium.GeoJson(selected_lake["corridor_buffer"], style_function=lambda _: {"fillColor": AMBER, "color": AMBER, "weight": 2, "fillOpacity": .18}, tooltip=f"{selected_lake.get('name','Lake')} · corridor dataset").add_to(overlays["Satellite corridor"])
        except (TypeError, KeyError, ValueError):
            pass
    # An optional public Bhuvan WMS must have been configured from actual
    # GetCapabilities output. There are deliberately no default guessed URLs.
    wms = ISRO_LAYERS.get("bhuvan_live", {})
    if "Bhuvan WMS" in layers and wms.get("wms") and wms.get("layer"):
        try:
            folium.raster_layers.WmsTileLayer(
                url=wms["wms"], layers=wms["layer"], fmt="image/png",
                transparent=True, name="Bhuvan WMS · configured, not validated",
                attr="Bhuvan, ISRO/NRSC", overlay=True, control=True,
            ).add_to(overlays["Bhuvan WMS"])
        except (ValueError, TypeError):
            pass
    # Local raster overlays use only files and bounds from overlays.json.
    for key, group in [("bhuvan_x", "Bhuvan snapshot"), ("hillshade", "CartoDEM hillshade"), ("rainfall", "MOSDAC rainfall")]:
        local = safe_overlay(key)
        if local and group in layers:
            file, details = local
            folium.raster_layers.ImageOverlay(image=str(file.resolve()), bounds=details["bounds"], name=group, opacity=.53 if key != "rainfall" else .66, interactive=False).add_to(overlays[group])
    for name, fg in overlays.items():
        if name in layers:
            fg.add_to(fmap)
    folium.LayerControl(collapsed=True).add_to(fmap)
    plugins.Fullscreen(position="topright").add_to(fmap)
    plugins.MiniMap(toggle_display=True, collapsed_width=20, collapsed_height=20).add_to(fmap)
    try:
        plugins.MeasureControl(position="topright", primary_length_unit="kilometers", secondary_length_unit="meters").add_to(fmap)
    except (TypeError, AttributeError):
        pass
    fmap.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
    legend = '<div class="hw-legend"><b>NETWORK KEY</b><br><span style="color:#50D4BC">━━</span> Available road<br><span style="color:#EEB86A">━━</span> Graph-critical link<br><span style="color:#FF7D88">┄┄</span> Simulated closure<br><span style="color:#FF7D88">●</span> Disconnected node<br><span style="color:#EEB86A">●</span> Reference hub</div>'
    fmap.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:25px;left:12px;z-index:9999">' + legend + '</div>'))
    fmap.get_root().header.add_child(folium.Element('<style>.leaflet-container{background:#0c1929}.leaflet-control-attribution{background:#0c1929dd!important;color:#e7f0fa!important}.leaflet-control-attribution a{color:#8fe8dc!important}</style>'))
    return fmap

def draw_offline_svg(view: str, layers: list[str]) -> str:
    """Pure inline SVG from local GraphML — no map tiles, JS or CDN needed."""
    coords_all = [xy for segment in edge_coords.values() for xy in segment]
    min_y, max_y = min(c[0] for c in coords_all), max(c[0] for c in coords_all)
    min_x, max_x = min(c[1] for c in coords_all), max(c[1] for c in coords_all)
    pad = .08
    width, height = 1040, 560
    def point(lat: float, lon: float) -> tuple[float,float]:
        x = 40 + (lon-min_x)/max(max_x-min_x, 1e-10)*(width-80)
        y = 40 + (max_y-lat)/max(max_y-min_y, 1e-10)*(height-80)
        return x, y
    target_reach = baseline_reachable if view == "Baseline" else restored_reachable if view == "After restoration" else current_reachable
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1040 560" role="img" aria-label="Offline road network diagram drawn from local coordinates">',
           '<rect width="1040" height="560" fill="#081526"/>',
           '<defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" stroke="#27405b" stroke-width=".6" fill="none"/></pattern></defs>',
           '<rect width="1040" height="560" fill="url(#grid)" opacity=".38"/>']
    for code, coords in edge_coords.items():
        pair = edge_lookup[code]
        is_closed = view != "Baseline" and code in closed and not (view == "After restoration" and code == restore)
        if is_closed and "Closed links" not in layers:
            continue
        if not is_closed and "Roads" not in layers:
            continue
        pts = ' '.join(f'{point(float(lat),float(lon))[0]:.2f},{point(float(lat),float(lon))[1]:.2f}' for lat,lon in coords)
        hue = '#ff7d88' if is_closed else '#50d4bc' if all(n in target_reach for n in pair) else '#5d7787'
        dashed = ' stroke-dasharray="8,7"' if is_closed else ''
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{hue}" stroke-width="{5 if is_closed else 3}" opacity=".92"{dashed}/>' )
    if "Lost nodes" in layers:
        for n in baseline_reachable-target_reach:
            x,y=point(float(U.nodes[n]["y"]),float(U.nodes[n]["x"]))
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ff7d88"/>')
    if "Destinations" in layers:
        for label,n in destinations.items():
            x,y=point(float(U.nodes[n]["y"]),float(U.nodes[n]["x"]))
            color = '#50d4bc' if n in target_reach else '#ff7d88'
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" stroke="#e7f0fa" stroke-width="2"><title>{escape(label)}</title></circle>')
    if "Hub" in layers:
        x,y=point(float(U.nodes[hub]["y"]),float(U.nodes[hub]["x"]))
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="#eeb86a" stroke="#f3f8ff" stroke-width="3"><title>Reference hub</title></circle>')
    svg.append('<rect x="25" y="20" width="298" height="40" rx="8" fill="#102237" stroke="#2b4659"/><text x="40" y="46" font-size="14" fill="#cfeaf0" font-family="sans-serif">SPACE VOID / OFFLINE NETWORK VIEW</text>')
    svg.append('</svg>')
    return ''.join(svg)

def draw_3d() -> bool:
    """Keyless 3D view. No remote-data requirement beyond optional tiles."""
    if pdk is None:
        st.info("3D view unavailable because pydeck is not installed. 2D Folium still works offline.")
        return False
    try:
        roads = []
        for code, coords in edge_coords.items():
            pair = edge_lookup[code]
            closed_here = code in closed and not (st.session_state.hw_view == "After restoration" and code == restore) and st.session_state.hw_view != "Baseline"
            roads.append({"path": [[lon, lat] for lat, lon in coords], "color": [255, 125, 136, 225] if closed_here else [80, 212, 188, 220], "link": code})
        centers = [{"lat": float(U.nodes[n]["y"]), "lon": float(U.nodes[n]["x"]), "height": 170, "color": [255,125,136,200]} for n in lost_nodes]
        lat = sum(float(U.nodes[n]["y"]) for n in U.nodes) / U.number_of_nodes()
        lon = sum(float(U.nodes[n]["x"]) for n in U.nodes) / U.number_of_nodes()
        focus = st.session_state.hw_camera
        if focus == "Hub":
            lat, lon = float(U.nodes[hub]["y"]), float(U.nodes[hub]["x"])
        elif focus == "Cut-off area" and lost_nodes:
            lat = sum(float(U.nodes[n]["y"]) for n in lost_nodes) / len(lost_nodes)
            lon = sum(float(U.nodes[n]["x"]) for n in lost_nodes) / len(lost_nodes)
        deck_layers = []
        hill = safe_overlay("hillshade")
        if hill:
            hill_file, hill_meta = hill
            try:
                image_data = 'data:image/png;base64,' + base64.b64encode(hill_file.read_bytes()).decode('ascii')
                south, west = hill_meta["bounds"][0]
                north, east = hill_meta["bounds"][1]
                deck_layers.append(pdk.Layer("BitmapLayer", image=image_data, bounds=[west, south, east, north], opacity=0.68))
            except (OSError, ValueError):
                pass
        deck = pdk.Deck(
            map_provider="carto", map_style="dark",
            initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=12.2, pitch=54, bearing=-22),
            layers=deck_layers + [
                pdk.Layer("PathLayer", data=roads, get_path="path", get_color="color", width_min_pixels=3, get_width=5, pickable=True),
                pdk.Layer("ColumnLayer", data=centers, get_position="[lon,lat]", get_elevation="height", elevation_scale=1, radius=65, get_fill_color="color", extruded=True, pickable=True),
            ],
            tooltip={"text": "{link}"},
        )
        st.pydeck_chart(deck, use_container_width=True)
        st.caption("3D shows actual mapped road geometries and schematic columns at disconnected graph nodes. It is not terrain elevation, flood depth, or an emergency route. A base map may require internet; 2D Space void works offline.")
        return True
    except Exception as exc:
        st.info(f"3D tiles or rendering are unavailable ({type(exc).__name__}). Use 2D / Space void for an offline map.")
        return False

if st.session_state.hw_page == "Mission Brief":
    st.markdown('<div class="hw-kicker">MISSION BRIEF / HIMALAYAN TRANSPORT RESILIENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="hw-heading">The next closure is a question of access.</div>', unsafe_allow_html=True)
    st.write("The 2023 South Lhonak outburst in Sikkim damaged downstream transport links. HimaWatch asks which mapped road-network connections become critical when disruptions are simulated, and how restoration changes network reachability.")
    c1, c2, c3 = st.columns(3)
    for col, label, note, icon in [(c1,"THE PROBLEM","Mountain valleys often have few alternate road connections. A damaged link may isolate destinations.","◇"),(c2,"THE METHOD","Real OSM geometry becomes a graph. Hypothetical closure removes edges, then NetworkX recalculates reachability.","◈"),(c3,"THE DATA","Road data is real mapped OSM geometry. Optional ISRO overlays are explicitly flagged as loaded or missing.","◉")]:
        with col:
            st.markdown(f'<div class="hw-card"><span class="hw-kicker">{icon} {label}</span><p style="line-height:1.7;color:#dce6f5">{note}</p></div>',unsafe_allow_html=True)
    st.button("Enter Mission Control  →", on_click=navigate, args=("Scenario Workspace",), type="primary", use_container_width=True)
    st.button("View test evidence and data status", on_click=navigate, args=("Evaluation Evidence",), use_container_width=True)
    st.markdown('<div class="hw-gallery"><div class="hw-gallery-cell"><span class="hw-layer">01 / CONTEXT</span><br><b>South Lhonak, 2023</b><small>Documented disaster context; this app does not reconstruct the flood.</small></div><div class="hw-gallery-cell"><span class="hw-layer">02 / ANALYSIS</span><br><b>Chungthang road graph</b><small>Graph closures and restoration comparisons.</small></div><div class="hw-gallery-cell"><span class="hw-layer">03 / EVIDENCE</span><br><b>Satellite data status</b><small>Only files with supplied provenance appear as loaded.</small></div></div>',unsafe_allow_html=True)
    with st.expander("Project limitations"):
        st.write("This is not a flood prediction or operational early-warning tool. Closures are hypothetical; four geographic destinations are reference points, not verified settlements or hospitals. Live road conditions and real-time satellite feeds are not supplied.")

elif st.session_state.hw_page == "Scenario Workspace":
    side, main = st.columns([1.08, 2.25], gap="large")
    with side:
        st.subheader("01 / Configure scenario")
        if not st.session_state.hw_presentation:
            st.caption("Choose a reference hub, simulate missing connections, and compare restoration.")
        current_named = hub_label(st.session_state.hw_hub)
        named_options = list(named_hubs)
        hub_options = named_options + ([current_named] if current_named not in named_options else [])
        if st.session_state.get("hw_hub_choice") not in hub_options:
            st.session_state.hw_hub_choice = current_named
        st.selectbox("Reference hub", options=hub_options, index=hub_options.index(current_named), key="hw_hub_choice", on_change=choose_named_hub)
        with st.expander("Advanced / select raw network node"):
            if st.session_state.get("hw_raw_node") not in nodes:
                st.session_state.hw_raw_node = st.session_state.hw_hub
            st.selectbox("Network node ID", options=nodes, index=nodes.index(st.session_state.hw_hub), format_func=lambda n: f"Road node {n}", key="hw_raw_node", on_change=choose_raw_hub)
            st.caption("Advanced selection changes only the hub, not the road topology.")
        st.multiselect("Road links to close", list(edge_lookup), key="hw_closures", format_func=label_link)
        r1, r2 = st.columns(2)
        with r1:
            st.button("Close worst link", use_container_width=True, on_click=close_worst_link)
            st.button("Clear closures", use_container_width=True, on_click=apply_closures, args=([],))
        with r2:
            st.button("Close all critical", use_container_width=True, on_click=apply_closures, args=(critical_ids,))
            st.button("Reset scenario", use_container_width=True, on_click=reset_scenario)
        st.selectbox("Compare restoring one closed link", ["None"] + closed, key="hw_restore")
        with st.expander("What is a critical link?"):
            st.write("A **graph-critical link** is a connection whose removal splits the mapped network into separate pieces. It is not automatically a bridge over a river, or confirmed infrastructure damage.")
        st.markdown('<div class="hw-synopsis"><b>SCENARIO, NOT FORECAST</b><br>Road closures are hypothetical. This is not a flood prediction, not a current road-condition feed, and not an emergency routing service.</div>', unsafe_allow_html=True)
    with main:
        st.subheader("02 / Network explorer")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Network nodes", len(U.nodes)); k2.metric("Closed links", len(closed)); k3.metric("Nodes losing access", len(lost_nodes)); k4.metric("Destinations affected", f"{lost_destinations}/{len(destinations)}")
        a, b, c = st.columns([1.5, 1, 2])
        with a: st.radio("Map state", ["Baseline", "After closure", "After restoration"], horizontal=True, key="hw_view")
        with b: st.selectbox("Map mode", ["2D", "3D"], key="hw_map_mode")
        with c:
            with st.popover("Map layers"):
                st.caption("Toggle layers in the Command Center sidebar")
        if st.session_state.hw_map_mode == "3D":
            st.selectbox("Camera", ["Overview", "Hub", "Cut-off area"], key="hw_camera")
            draw_3d()
        elif st.session_state.hw_basemap == "Space void (no tiles)":
            components.html(draw_offline_svg(st.session_state.hw_view, st.session_state.hw_layers), height=690 if st.session_state.hw_presentation else 545, scrolling=False)
            st.caption("Offline-safe vector fallback drawn from the local road graph; no tile service, MapLibre, or Leaflet assets required.")
        else:
            fmap = draw_map(st.session_state.hw_view, st.session_state.hw_layers, st.session_state.hw_presentation)
            components.html(fmap.get_root().render(), height=690 if st.session_state.hw_presentation else 545, scrolling=False)
        if not st.session_state.hw_presentation:
            st.caption("Teal roads: available in selected map state · Red dashes: hypothetical closed links · Amber: graph-critical links · Markers: reference points. Not live operational conditions.")
    st.markdown('<div class="hw-rule"></div>', unsafe_allow_html=True)
    st.subheader("03 / Scenario impact")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Baseline reachable", len(baseline_reachable)); q2.metric("After disruption", len(current_reachable)); q3.metric("After restoration", len(restored_reachable)); q4.metric("Road km inside lost components", f"{cutoff_km:.2f} km" if cutoff_km is not None else "Data unavailable")
    st.markdown(f'<div class="hw-synopsis"><span class="hw-micro">SCENARIO INTERPRETATION</span><br><b>{len(lost_nodes)} network nodes</b> and <b>{lost_destinations} representative destinations</b> lose access to the reference hub. {("Restoring " + restore + " reconnects " + str(len(regained_nodes)) + " network nodes and " + str(regained_destinations) + " representative destinations.") if restore != "None" else "Select a closed link to compare restoration."}</div>', unsafe_allow_html=True)
    impact_angle = max(0, min(360, round(impact_ratio * 360)))
    st.markdown(f'<div class="hw-ring"><div class="hw-ring-visual" style="background:conic-gradient(#ff7d88 {impact_angle}deg,#233c50 0)"><div class="hw-ring-core">{impact_ratio:.0%}</div></div><div><div class="hw-kicker">NETWORK IMPACT / ILLUSTRATIVE THRESHOLDS</div><strong>{impact_name}</strong><div class="hw-footnote">Share of baseline reachable graph nodes losing access. Not population exposure or a disaster risk score.</div></div></div>', unsafe_allow_html=True)
    st.caption("Illustrative impact bands: Low <10%, Moderate 10–24%, High 25–49%, Severe ≥50%. These are not official risk thresholds or population exposure figures.")
    st.caption("For network distance and automated integrity checks, open Evaluation Evidence. These measures never replace the destination table or its original CSV fields.")
    if closed:
        st.subheader("Restoration options / compare all closed links")
        st.caption("For each hypothetical restoration, reopen just that link while every other selected closure stays active. Ranked by reference points regained, then by nodes regained. These are not repair-cost or safety recommendations.")
        priorities = restoration_priorities(disrupted, U, hub, closed, destinations)
        st.table(priorities)
        best = priorities[0]
        if best["Nodes reconnected"] > 0:
            st.write(f'**Modelled restoration opportunity:** {best["Link"]} would reconnect {best["Nodes reconnected"]} graph nodes and {best["Reference destinations reconnected"]} reference points under the selected scenario.')
            st.button(f'Compare restoration of {best["Link"]}', key="hw_compare_priority",
                      on_click=lambda code: st.session_state.update(hw_restore=code), args=(best["Link"],))
        else:
            st.info("Restoring any single closed connection does not recover hub access in this scenario. Multi-link restoration may be needed.")
    st.subheader("Destination accessibility")
    table_html = '<table class="hw-table"><thead><tr><th>Destination</th><th>Baseline</th><th>After closure</th><th>After restoration</th><th>Path (links)</th></tr></thead><tbody>'
    for record in results:
        cells = [f'<td>{escape(record["Destination"])}</td>']
        for name in ("Baseline", "After closure", "After restoration"):
            ok = record[name] == "Reachable"
            cells.append(f'<td><span class="hw-pill {"" if ok else "off"}">{"● Reachable" if ok else "◆ Disconnected"}</span></td>')
        cells.append(f'<td>{escape(str(record["Path (links)"]))}</td>')
        table_html += '<tr>' + ''.join(cells) + '</tr>'
    st.markdown(table_html + '</tbody></table>', unsafe_allow_html=True)
    # Identical CSV column order and cell values as the original code.
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=list(results[0].keys()))
    writer.writeheader(); writer.writerows(results)
    ex1, ex2 = st.columns(2)
    with ex1: st.download_button("Download scenario report (CSV)", data=csv_buffer.getvalue(), file_name="himawatch_scenario_report.csv", mime="text/csv", use_container_width=True)
    with ex2:
        geo_features = []
        for code in closed:
            geo_features.append({"type":"Feature","properties":{"id":code,"scenario":"hypothetical closure"},"geometry":{"type":"LineString","coordinates":[[lon,lat] for lat,lon in edge_coords[code]]}})
        st.download_button("Download closed links (GeoJSON)", json.dumps({"type":"FeatureCollection","features":geo_features},indent=2), file_name="himawatch_closed_links.geojson", mime="application/geo+json", use_container_width=True)
    with st.expander("Data sources and limitations"):
        st.write("Road geometry is from OpenStreetMap, downloaded using OSMnx. Connectivity calculations use NetworkX on a simplified undirected graph.")
        st.write("The four destinations are geographic road-network reference points, not verified villages or facilities. This model does not account for one-way restrictions, flood extent, actual road damage, travel time, or emergency-route safety.")
        st.write("Indian satellite-derived context appears only if a compatible lakes.json is present. Its provenance must be verified separately; no source integration is inferred from file names.")

elif st.session_state.hw_page == "Critical Links":
    st.subheader("Critical link priority")
    st.caption("Each link is tested alone against the currently selected reference hub. Graph-critical means disconnection in the simplified model, not a confirmed broken bridge.")
    impacts = critical_impacts(hub)
    if not impacts:
        st.info("No graph bridges were found in the mapped road network.")
    else:
        st.bar_chart({row["Link"]: row["Nodes isolated"] for row in impacts}, horizontal=True)
        st.markdown('<span class="hw-micro">LOAD A ONE-LINK SCENARIO</span>', unsafe_allow_html=True)
        for record in impacts[:18]:
            rc, cc = st.columns([5,1])
            with rc:
                st.markdown(f'<div class="hw-card"><b>{escape(label_link(record["Link"]))}</b><div class="desc">{record["Nodes isolated"]} network nodes · {record["Destinations isolated"]} representative destinations isolated from hub</div></div>',unsafe_allow_html=True)
            with cc:
                st.button("Load", key=f"load_{record['Link']}", use_container_width=True, on_click=go_to_workspace, args=(record["Link"],))
    st.caption("The priority ranking measures graph topology only. It does not assign repair cost, likelihood, urgency, or population impact.")

elif st.session_state.hw_page == "Destination Evidence":
    st.subheader("Grounded destinations / optional source import")
    st.caption("This supplements, but NEVER replaces, the four reference corridor points or your original CSV schema.")
    st.write("Upload coordinates for settlements or facilities from a source you have checked. The app connects each point to its nearest mapped road node and calculates modelled access. **A supplied source field is not independent verification.**")
    st.download_button("Download CSV template", "name,latitude,longitude,category,source\n", "destination_template.csv", "text/csv")
    uploaded = st.file_uploader("Source-declared locations CSV", type=["csv"], key="hw_verified_csv")
    if uploaded is None:
        st.info("No destination observations supplied. The four directional reference points remain illustrative; this screen makes no real-facility claims.")
    else:
        points, problems = source_declared_points(uploaded.getvalue())
        for problem in problems[:12]:
            st.warning(problem)
        report = []
        for point in points:
            n = point["Nearest mapped node"]
            in_scope = point["Within 1000 m"]
            state = "Not assessed (too far from mapped roads)" if not in_scope else ("Reachable" if n in current_reachable else "Disconnected")
            restored_state = "Not assessed" if not in_scope else ("Reachable" if n in restored_reachable else "Disconnected")
            report.append({"Location": point["Name"], "Category": point["Category"],
                           "Source as supplied": point["User-supplied source"],
                           "Road-node offset (m)": point["Offset from node (m)"],
                           "After closure": state, "After restoration": restored_state})
        if report:
            st.table(report)
            out = StringIO()
            writer = csv.DictWriter(out, fieldnames=list(report[0]))
            writer.writeheader(); writer.writerows(report)
            st.download_button("Download supplemented destinations report", out.getvalue(),
                               "himawatch_source_declared_destinations.csv", "text/csv")
        st.caption("Modelled connectivity only. Nearest road nodes do not guarantee an actual access route, a verified facility, road safety, or hydraulic flood exposure. Independently verify source, location and mapping accuracy before citing any place to judges.")

elif st.session_state.hw_page == "Evaluation Evidence":
    st.subheader("Evaluation evidence / reproducible analysis")
    st.caption("Live checks against the downloaded local road graph. These are engineering checks, not validation of real road conditions or satellite observations.")
    st.markdown('<div class="hw-synopsis"><span class="hw-micro">SCENARIO AUDIT</span><br>All numbers below are calculated from the selected hub and current closure set. No population, casualty or verified settlement counts are inferred.</div>', unsafe_allow_html=True)
    aa, ab, ac, ad = st.columns(4)
    aa.metric("Graph nodes", U.number_of_nodes())
    ab.metric("Graph connections", U.number_of_edges())
    ac.metric("Graph-critical links", len(critical_ids))
    ad.metric("Disconnected nodes", len(lost_nodes))
    st.subheader("Independent integrity checks")
    checks = audit_static_graph() + audit_scenario(U, disrupted, restored, hub, closed, restore)
    for record in checks:
        if record["Result"] == "FAIL":
            st.error(f'{record["Check"]}: {record["Evidence"]}')
    st.table(checks)
    st.caption("PASS checks are internally reproducible graph invariants. They do not validate geographic coverage, river flooding, road safety or ISRO layer provenance.")
    if closed:
        st.subheader("Restoration priority comparison")
        st.table(restoration_priorities(disrupted, U, hub, closed, destinations))
        st.caption("Marginal graph accessibility gain, not people, repair costs or a flood-risk estimate.")
    st.subheader("Network distance comparison")
    distance_rows = weighted_corridor_comparison(U, disrupted, restored, hub)
    if distance_rows:
        st.table(distance_rows)
        st.caption("Shortest distance along the simplified graph, using OSM length attributes. Not driving time or a safe route; road directions and unrecorded tracks are not modelled.")
    else:
        st.info("Complete, valid OSM segment lengths are not available. Distance claims are hidden instead of estimated.")
    st.subheader("Source and evidence register")
    st.table(layer_status())
    st.warning("Only the OpenStreetMap graph is confirmed loaded in this installation unless optional layers above show 'Loaded'. This does not verify them scientifically.")
    st.subheader("Download a judge-ready reproducibility brief")
    brief = [
        "HIMAWATCH / ASTRA 2026 / TEAM SILENT SUPERNOVA",
        "DOMAIN 03 / SPACE-BASED DISASTER MANAGEMENT",
        "SCENARIO REPORT — HYPOTHETICAL, NOT A FLOOD FORECAST",
        "",
        "Problem: assess how removing mapped road connections changes network access around Chungthang, Sikkim.",
        "Core data: local OSM road GraphML, analysed with OSMnx and NetworkX.",
        f"Mapped nodes: {U.number_of_nodes()}; simplified undirected links: {U.number_of_edges()}.",
        f"Reference hub node ID: {hub}; selected closed link IDs: {', '.join(closed) or 'none'}.",
        f"Baseline reachable: {len(baseline_reachable)}; disrupted reachable: {len(current_reachable)}; restored reachable: {len(restored_reachable)}.",
        f"Lost nodes: {len(lost_nodes)}; destinations losing access: {lost_destinations} of {len(destinations)} representative network points.",
        f"Selected restoration: {restore}; reconnected nodes: {len(regained_nodes)}; reconnected representative points: {regained_destinations}.",
        "",
        "QUALITY CHECKS",
        *[f'{row["Result"]}: {row["Check"]} — {row["Evidence"]}' for row in checks],
        "",
        "DESTINATION TABLE / ORIGINAL CSV COLUMNS",
        " | ".join(results[0].keys()),
        *[" | ".join(str(row[col]) for col in results[0].keys()) for row in results],
        "",
        "SOURCES / LIMITATIONS",
        *[f'{row["Layer"]}: {row["Status"]} / {row["Source"]} / {row["Retrieved"]}' for row in layer_status()],
        "No verified population exposure, field-validation, live road monitoring or hydraulic GLOF prediction is claimed.",
        "Directional corridor points are network references, not verified villages, hospitals or relief facilities.",
        "Not intended for operational disaster decisions.",
        "Vaanya Singh (25BAI11544) · Vaishnavi Upadhyay (25BAI11583)",
    ]
    st.download_button("Download evaluation evidence (TXT)", data="\n".join(brief),
                       file_name="himawatch_evaluation_evidence.txt", mime="text/plain", use_container_width=True)
    st.caption("If you need official technical credit for satellite-data use, load and independently validate one relevant Indian satellite layer. No score can be guaranteed from software alone.")

elif st.session_state.hw_page == "Data Layers":
    st.subheader("Satellite & geographic data inventory")
    st.write("**Loaded** means a local file exists and its geographic bounds are valid. It does not establish the scientific correctness of a source attribution.")
    tab = layer_status()
    table = '<table class="hw-status-table"><thead><tr><th>Layer</th><th>Status</th><th>Source</th><th>Retrieved</th><th>Area</th></tr></thead><tbody>'
    for record in tab:
        table += '<tr>' + ''.join(f'<td>{escape(str(record[k]))}</td>' for k in ["Layer", "Status", "Source", "Retrieved", "Area"]) + '</tr>'
    st.markdown(table + '</tbody></table>', unsafe_allow_html=True)
    for key, title in [("bhuvan_x", "Bhuvan snapshot"),("hillshade", "CartoDEM moonlit hillshade"),("rainfall", "MOSDAC rainfall")]:
        data = safe_overlay(key)
        with st.expander(title + (" · Loaded" if data else " · Not loaded")):
            if data:
                file, info = data
                st.image(str(file), caption=f'{title} · {info.get("source", "Source not provided")} · {info.get("date", "Date not provided")}')
                st.json(info, expanded=False)
            else:
                st.write("No valid local overlay has been configured. Add a PNG and metadata using the supplied offline preparation scripts.")
    st.markdown("**Credits (when loaded):** Bhuvan, ISRO/NRSC · Bhoonidhi, NRSC · MOSDAC, SAC-ISRO · Roads: OpenStreetMap contributors.")
    st.caption("Files must be downloaded and verified independently. The application does not authenticate or fetch protected datasets.")

elif st.session_state.hw_page == "3D View":
    st.subheader("Three-dimensional network overview")
    st.selectbox("Camera preset", ["Overview", "Hub", "Cut-off area"], key="hw_camera")
    draw_3d()
    st.button("Return to 2D scenario", on_click=navigate, args=("Scenario Workspace",))

elif st.session_state.hw_page == "Team":
    st.subheader("Team Silent Supernova")
    st.markdown('<div class="hw-gallery"><div class="hw-gallery-cell"><span class="hw-layer">TEAM MEMBER</span><br><b>Vaanya Singh</b><small>25BAI11544</small></div><div class="hw-gallery-cell"><span class="hw-layer">TEAM MEMBER</span><br><b>Vaishnavi Upadhyay</b><small>25BAI11583</small></div><div class="hw-gallery-cell"><span class="hw-layer">ASTRA 2026</span><br><b>Domain 03</b><small>Space-Based Disaster Management</small></div></div>',unsafe_allow_html=True)
    st.write("The team developed an interactive workflow for exploring hypothetical road-network interruptions. The software is an analytical prototype, not a validated hazard warning service.")

elif st.session_state.hw_page == "Satellite Context":
    st.subheader("Satellite and lake context")
    st.caption("Any supplied terrain-derived corridor is screening-level only, not a hydraulic flood model. A file named lakes.json is not proof of a verified CartoDEM source.")
    st.caption("Optional supporting context; it does not change the established road-network connectivity calculations.")
    if lake_error:
        st.info(lake_error)
        st.markdown('**Expected path:** `data/lakes.json` with `meta` and `lakes` entries from your own lake-data pipeline.')
        st.write("Indian satellite-derived data is **not yet integrated** into this installation.")
    else:
        if lake_is_demo:
            st.warning("DEMO DATA — Lake indicators, scores, and corridors must not be interpreted as verified observations.")
        st.markdown(f'<div class="hw-micro">SOURCE FRESHNESS: {escape(str(lake_meta.get("generated_at") or "NOT PROVIDED"))} · {"DEMO" if lake_is_demo else "SOURCE STATUS: VERIFY PROVENANCE"}</div>', unsafe_allow_html=True)
        choices = {str(l.get("id", f"lake_{i}")): l for i, l in enumerate(lakes)}
        if choices:
            choice_ids = list(choices)
            if st.session_state.hw_lake_id not in choices:
                st.session_state.hw_lake_id = choice_ids[0]
            st.selectbox("Lake", options=choice_ids, format_func=lambda x: str(choices[x].get("name") or x), key="hw_lake_id")
            selected = choices[st.session_state.hw_lake_id]
            st.write(f"**{selected.get('name', 'Lake')}**")
            la, lb, lc = st.columns(3)
            la.metric("Risk score", str(selected.get("risk_score", "Not provided")))
            lb.metric("Risk band", str(selected.get("risk_band", "Not provided")))
            lc.metric("Growth", str(selected.get("growth_pct", "Not provided")))
            st.write("**Rainfall alert:**", str(selected.get("rainfall_alert", "Not provided")))
            st.json(selected.get("downstream", {}), expanded=False)
            links = intersecting_codes(selected)
            st.write(f"**Road connections intersecting supplied corridor polygon:** {len(links)}")
            if not links:
                st.info("No mapped road links intersect the supplied corridor polygon, or the geometry is missing/invalid. No road damage is inferred.")
            else:
                st.write(", ".join(links[:24]) + ("…" if len(links)>24 else ""))
                st.button("Use intersecting links as hypothetical closures", on_click=use_satellite_links, args=(links,))
            if not lake_is_demo:
                st.caption("Dataset is marked non-demo by its creator, but source attribution, spatial accuracy and methods still require independent verification.")
        else:
            st.info("The file contains zero lakes. Populate its lakes list to enable the satellite context view.")
    st.markdown("**Intended sources to document when genuinely used:** ISRO Bhuvan, Bhoonidhi, MOSDAC and CartoDEM. Listing a source here does not mean it has been integrated or verified.")
    st.caption("Screening-level context only; any terrain-derived pathway is not a hydraulic flood model. No rainfall alert or glacial lake observation is live.")

else:
    st.subheader("The problem")
    st.write("The October 2023 South Lhonak Glacial Lake Outburst Flood in Sikkim damaged downstream transport infrastructure. The Sikkim Post-Disaster Needs Assessment reports damage to 33 road bridges.")
    st.write("When a road connection becomes unavailable, the consequences may extend beyond the damaged location. Other destinations can lose access to important routes and services.")
    st.subheader("Our proposed solution")
    st.write("HimaWatch is a scenario-based geospatial planning prototype that models road networks as graphs. Users can remove selected links, analyse connectivity, and compare what happens if a link is restored.")
    st.subheader("System workflow")
    diagram = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 130" role="img" aria-label="Workflow: OpenStreetMap road data to graph model to hypothetical closure to reachability to restoration and report"><style>text{font:600 13px Arial;fill:#e7f0fa}.box{fill:#102237;stroke:#2b4659;stroke-width:2}.arrow{stroke:#50d4bc;stroke-width:2;fill:none}</style><rect class="box" x="4" y="24" width="148" height="74" rx="10"/><text x="78" y="53" text-anchor="middle">OSM road data</text><text x="78" y="72" text-anchor="middle">OSMnx</text><path class="arrow" d="M152 61h26m-8-7 8 7-8 7"/><rect class="box" x="178" y="24" width="148" height="74" rx="10"/><text x="252" y="53" text-anchor="middle">Graph model</text><text x="252" y="72" text-anchor="middle">NetworkX</text><path class="arrow" d="M326 61h26m-8-7 8 7-8 7"/><rect class="box" x="352" y="24" width="148" height="74" rx="10"/><text x="426" y="53" text-anchor="middle">Road closure</text><text x="426" y="72" text-anchor="middle">simulation</text><path class="arrow" d="M500 61h26m-8-7 8 7-8 7"/><rect class="box" x="526" y="24" width="148" height="74" rx="10"/><text x="600" y="53" text-anchor="middle">Reachability</text><text x="600" y="72" text-anchor="middle">analysis</text><path class="arrow" d="M674 61h26m-8-7 8 7-8 7"/><rect class="box" x="700" y="24" width="215" height="74" rx="10"/><text x="807" y="53" text-anchor="middle">Restoration and</text><text x="807" y="72" text-anchor="middle">CSV / GeoJSON report</text></svg>'''
    components.html(diagram, height=145)
    st.subheader("Technical architecture")
    st.table({"Component":["Geographic data","Graph construction","Connectivity engine","User interface","Map rendering","Scenario export"],"Technology":["OpenStreetMap","OSMnx","NetworkX","Streamlit","Folium","Python CSV"]})
    st.subheader("What makes HimaWatch different?")
    st.write("HimaWatch does not attempt to replace existing glacial-lake monitoring or flood-risk assessment. It focuses on a complementary question: how hypothetical transport-network disruptions change accessibility, and what connectivity might be restored by reopening selected links.")
    st.subheader("Future development")
    st.write("Planned extensions include verified settlement and facility locations, Indian satellite-derived terrain or hazard context, improved road selection, and expanded geographic coverage.")
    with st.expander("Data sources and limitations"):
        st.write("Road geometry is from OpenStreetMap and OSMnx. The model uses a simplified undirected NetworkX graph. The four corridor locations are geographic network reference points, not verified villages, hospitals or relief facilities.")
        st.write("Closures are hypothetical; this is not a flood prediction or early-warning service. It does not account for one-way restrictions, real damage, travel time, flood extent, or emergency-route safety.")
        st.write("Indian satellite-derived overlays are present only when local overlay files and overlays.json metadata are loaded. Optional lake context is separate and must show DEMO DATA whenever its metadata declares a demo.")

# The user's original footer block is preserved verbatim.
st.markdown("""
<div class="footer">
    HIMAWATCH / TEAM SILENT SUPERNOVA<br>
    Vaanya Singh · 25BAI11544 &nbsp;&nbsp;|&nbsp;&nbsp;
    Vaishnavi Upadhyay · 25BAI11583<br>
    ASTRA 2026 · Research prototype ·
    Not intended for operational disaster decisions
</div>
""", unsafe_allow_html=True)
