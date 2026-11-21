
from pathlib import Path

import osmnx as ox

# Chungthang, Sikkim — approximate town centre
LATITUDE = 27.606
LONGITUDE = 88.647

# Download road data within 3 km
RADIUS_METRES = 3000

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

print("Downloading Chungthang road network...")

try:
    graph = ox.graph_from_point(
        (LATITUDE, LONGITUDE),
        dist=RADIUS_METRES,
        network_type="drive",
        simplify=True
    )

    print("Download successful!")

    print(f"Road intersections/nodes: {len(graph.nodes)}")
    print(f"Road segments/edges: {len(graph.edges)}")

    # Preserve the actual road network for the app
    ox.io.save_graphml(
        graph,
        filepath=str(OUTPUT_DIR / "chungthang_roads.graphml")
    )

    # Export geographic road features
    nodes, edges = ox.graph_to_gdfs(graph)

    edges.to_file(
        OUTPUT_DIR / "chungthang_roads.geojson",
        driver="GeoJSON"
    )

    print("Files saved in the data folder.")

except Exception as error:
    print("Road download failed.")
    print(type(error).__name__, str(error))
    raise
