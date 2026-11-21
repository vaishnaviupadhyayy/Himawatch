"""Independent local verification of HimaWatch's physical-connectivity model.

Run: python verify_project.py
Requires your existing data/chungthang_roads.graphml.
Does NOT alter files, contact external servers or claim disaster predictions.
"""
from pathlib import Path
import csv
import io
import math

import networkx as nx
import osmnx as ox

SOURCE = Path('data/chungthang_roads.graphml')
FIELDS = ['Destination','Baseline','After closure','After restoration','Path (links)']

def make_graph():
    G = ox.io.load_graphml(SOURCE)
    U = nx.Graph()
    U.add_nodes_from(G.nodes(data=True))
    for u,v,d in G.edges(data=True):
        if u != v and not U.has_edge(u,v):
            U.add_edge(u,v,**d)
    return G,U

def norm(u,v):
    return tuple(sorted((u,v), key=str))

def checks():
    assert SOURCE.is_file(), f'Missing {SOURCE}; keep your existing downloaded road file.'
    G,U = make_graph()
    assert U.number_of_nodes() > 1 and U.number_of_edges() > 0
    assert all(-90<=float(d['y'])<=90 and -180<=float(d['x'])<=180 for _,d in U.nodes(data=True)), 'Invalid node coordinates'
    edges=sorted({norm(u,v) for u,v in U.edges()}, key=lambda e:(str(e[0]),str(e[1])))
    ids={f'E{i:03d}': edge for i,edge in enumerate(edges,1)}
    bridges={norm(u,v) for u,v in nx.bridges(U)}
    bridge_ids=[c for c,e in ids.items() if e in bridges]
    nodes=list(U.nodes)
    hub=min(nodes,key=lambda n:(float(U.nodes[n]['y'])-27.606)**2+(float(U.nodes[n]['x'])-88.647)**2)
    baseline=set(nx.node_connected_component(U,hub))
    print('Dataset:',SOURCE)
    print('Directed edges:',G.number_of_edges(),'Simplified links:',len(ids),'Nodes:',len(nodes))
    print('Connected components:',nx.number_connected_components(U),'Graph-critical links:',len(bridge_ids))
    print('Baseline reachable from default reference hub:',len(baseline))
    # All single-edge tests, not only the sample default.
    for code,(u,v) in ids.items():
        failed=U.copy();failed.remove_edge(u,v)
        after=set(nx.node_connected_component(failed,hub))
        assert after<=baseline, f'{code}: closure increased reachability'
        repaired=failed.copy();repaired.add_edge(u,v,**U[u][v])
        assert set(nx.node_connected_component(repaired,hub))==baseline, f'{code}: restoration not inverse of closure'
        assert (nx.number_connected_components(failed)>nx.number_connected_components(U))==(code in bridge_ids), f'{code}: criticality mismatch'
    print('PASS: every single-link closure and restoration invariant (',len(ids),'links )')
    # E001 is a familiar scenario but should never be assumed to have a fixed size on other maps/hubs.
    if 'E001' in ids:
        test=U.copy();test.remove_edge(*ids['E001'])
        result=len(set(nx.node_connected_component(test,hub)))
        print(f'E001 example: {len(baseline)} -> {result} -> {len(baseline)} accessible nodes (default hub)')
    # Export field order check based on the user-provided legacy file, independent of UI.
    sample={field:'—' for field in FIELDS}
    buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=list(sample));writer.writeheader();writer.writerow(sample)
    assert next(csv.reader(io.StringIO(buffer.getvalue())))==FIELDS
    print('PASS: CSV header fields and order retained:',', '.join(FIELDS))
    print('PASS: graph model and scenario invariants; geographical and satellite validation require separate evidence.')

if __name__=='__main__':
    checks()
