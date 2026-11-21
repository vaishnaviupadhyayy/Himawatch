#!/usr/bin/env python3
"""Discover Bhuvan public WMS layers and save an attributed offline PNG.

No WMS endpoints or layer names are guessed. Read the provider usage policy.
Examples:
  python fetch_isro_layers.py --wms 'https://EXACT-WMS-URL' --list
  python fetch_isro_layers.py --wms 'https://EXACT-WMS-URL' --layer 'EXACT_LAYER' \
      --bbox 88.56,27.54,88.72,27.70 --out data/overlays/bhuvan_x.png
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import requests
from PIL import Image
from io import BytesIO


def get_caps(url: str) -> bytes:
    r = requests.get(url, params={"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetCapabilities"}, timeout=(12, 40), headers={"User-Agent":"HimaWatch/1.0 (academic project; respectful WMS access)"})
    r.raise_for_status()
    return r.content


def names_from_capabilities(raw: bytes) -> list[str]:
    root = ET.fromstring(raw)
    result = []
    for node in root.iter():
        if node.tag.rsplit('}', 1)[-1] != 'Layer':
            continue
        for child in node:
            if child.tag.rsplit('}', 1)[-1] == 'Name' and child.text:
                result.append(child.text.strip())
                break
    return list(dict.fromkeys(result))


def update_manifest(out: Path, bbox: list[float], url: str, layer: str) -> None:
    root = Path('data/overlays').resolve()
    target = out.resolve()
    if root != target.parent:
        raise ValueError('Output must be directly inside data/overlays')
    manifest = root / 'overlays.json'
    try:
        meta = json.loads(manifest.read_text()) if manifest.is_file() else {'layers': {}}
    except (OSError, json.JSONDecodeError):
        raise ValueError('Existing overlays.json is invalid; fix it before continuing')
    layers = meta.setdefault('layers', {})
    layers[out.stem] = {
        'file': out.name,
        'bounds': [[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
        'source': 'Bhuvan, ISRO/NRSC',
        'date': datetime.now(timezone.utc).date().isoformat(),
        'area': 'User-selected WMS bounding box (EPSG:4326)',
        'wms': url,
        'layer': layer,
        'note': 'Public WMS snapshot; verify license, attribution and thematic meaning with provider'
    }
    tmp = manifest.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    tmp.replace(manifest)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--wms', required=True, help='Exact WMS URL obtained from Bhuvan')
    ap.add_argument('--list', action='store_true', help='List advertised layer names')
    ap.add_argument('--layer', help='Exact layer name from GetCapabilities')
    ap.add_argument('--bbox', help='minlon,minlat,maxlon,maxlat in EPSG:4326')
    ap.add_argument('--out', help='data/overlays/bhuvan_x.png')
    args = ap.parse_args()
    try:
        raw = get_caps(args.wms)
        names = names_from_capabilities(raw)
        if args.list:
            print('\n'.join(names) if names else 'No named WMS layers found.')
            return
        if not args.layer or not args.bbox or not args.out:
            ap.error('For GetMap, supply --layer, --bbox, and --out')
        if args.layer not in names:
            raise ValueError('Requested layer not advertised in GetCapabilities; run --list')
        bbox = [float(x.strip()) for x in args.bbox.split(',')]
        if len(bbox) != 4 or not (-180 <= bbox[0] < bbox[2] <= 180 and -90 <= bbox[1] < bbox[3] <= 90):
            raise ValueError('BBox must be minlon,minlat,maxlon,maxlat with increasing bounds')
        out = Path(args.out)
        if out.name != 'bhuvan_x.png':
            raise ValueError('Use output data/overlays/bhuvan_x.png (the app recognises bhuvan_x)')
        out.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(args.wms, params={
            'SERVICE': 'WMS', 'VERSION': '1.1.1', 'REQUEST': 'GetMap',
            'LAYERS': args.layer, 'STYLES': '', 'SRS': 'EPSG:4326',
            'BBOX': ','.join(map(str, bbox)), 'WIDTH': 1024, 'HEIGHT': 1024,
            'FORMAT': 'image/png', 'TRANSPARENT': 'TRUE'
        }, timeout=(12, 65), headers={'User-Agent':'HimaWatch/1.0 (academic project; respectful WMS access)'})
        r.raise_for_status()
        content_type = r.headers.get('content-type', '').lower()
        if 'image/' not in content_type:
            raise ValueError('WMS returned non-image content; check layer, extent and service limits')
        image = Image.open(BytesIO(r.content)).convert('RGBA')
        image.save(out.resolve(), optimize=True)
        update_manifest(out, bbox, args.wms, args.layer)
        print(f'Saved {out} ({image.width}x{image.height}).')
        print('Reminder: read Bhuvan terms of use and cite exact WMS layer, capture date and geographic extent.')
    except (requests.RequestException, ValueError, ET.ParseError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
