#!/usr/bin/env python3
"""Offline: make a labelled CartoDEM hillshade or MOSDAC GSMap PNG.

Requires rasterio only for this prep script, never for the running app.
Usage:
  python -m pip install rasterio
  python prepare_overlays.py --dem cartodem.tif --bbox 88.56,27.54,88.72,27.70
  python prepare_overlays.py --rain gsmap.tif --date 2026-11-21
Input must be a rasterio-readable, geographically referenced dataset.
NetCDF/HDF5 unsupported by rasterio should first be exported to GeoTIFF.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

try:
    import rasterio
    from rasterio.warp import reproject, Resampling, transform_bounds
    from rasterio.transform import from_bounds
except ImportError as e:
    raise SystemExit('This offline script requires rasterio: python -m pip install rasterio') from e

ROOT = Path('data/overlays')


def reproject_band(src, bounds: list[float], width=1024, height=1024) -> tuple[np.ndarray, np.ndarray]:
    if src.crs is None:
        raise ValueError('Raster has no CRS. Supply a georeferenced GeoTIFF.')
    transform = from_bounds(*bounds, width, height)
    dest = np.full((height, width), np.nan, dtype=np.float32)
    reproject(
        source=rasterio.band(src, 1), destination=dest,
        src_transform=src.transform, src_crs=src.crs,
        dst_transform=transform, dst_crs='EPSG:4326',
        src_nodata=src.nodata, dst_nodata=np.nan,
        resampling=Resampling.bilinear
    )
    valid = np.isfinite(dest)
    return dest, valid


def manifest_update(key: str, out: Path, bbox: list[float], source: str, date: str, note: str) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    file = ROOT / 'overlays.json'
    if file.is_file():
        data = json.loads(file.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or not isinstance(data.get('layers'), dict):
            raise ValueError('Invalid existing overlays.json')
    else:
        data = {'layers': {}}
    data['layers'][key] = {
        'file': out.name,
        'bounds': [[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
        'source': source, 'date': date,
        'area': 'Bounds from source raster / user clipping box',
        'note': note,
    }
    tmp = file.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
    tmp.replace(file)


def source_bounds(src) -> list[float]:
    b = transform_bounds(src.crs, 'EPSG:4326', *src.bounds, densify_pts=21)
    return list(map(float, b))


def hillshade(dem: np.ndarray, valid: np.ndarray, bbox: list[float]) -> np.ndarray:
    safe = np.where(valid, dem, np.nan)
    if not valid.any():
        raise ValueError('No valid elevation data in supplied extent')
    med = float(np.nanmedian(safe))
    safe = np.where(valid, safe, med)
    # Approximate lon/lat pixels in meters at the centre latitude.
    midlat = (bbox[1] + bbox[3]) / 2
    dx = max((bbox[2] - bbox[0]) * 111320 * np.cos(np.radians(midlat)) / dem.shape[1], 1)
    dy = max((bbox[3] - bbox[1]) * 111320 / dem.shape[0], 1)
    gy, gx = np.gradient(safe, dy, dx)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    altitude, azimuth = np.radians(30), np.radians(315)
    luminance = np.sin(altitude)*np.cos(slope) + np.cos(altitude)*np.sin(slope)*np.cos(azimuth-aspect)
    intensity = np.clip((luminance + .18) * 190, 0, 255)
    rgba = np.zeros((*dem.shape, 4), dtype=np.uint8)
    rgba[...,0] = np.clip(12 + intensity*.43, 0, 255)
    rgba[...,1] = np.clip(35 + intensity*.67, 0, 255)
    rgba[...,2] = np.clip(68 + intensity*.83, 0, 255)
    rgba[...,3] = np.where(valid, 235, 0)
    return rgba


def rainfall_palette(values: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, tuple[float, float]]:
    positive = valid & (values >= 0)
    if not positive.any():
        raise ValueError('No nonnegative valid rainfall measurements')
    lo, hi = map(float, [values[positive].min(), values[positive].max()])
    t = np.clip((values - lo)/max(hi-lo, 1e-6), 0, 1)
    # Cyan -> blue -> violet, relative to source raster min/max.
    colors = np.array([[44,211,226],[51,122,226],[142,93,221]], dtype=float)
    segment = np.minimum((t * 2).astype(int), 1)
    fraction = (t * 2) - segment
    rgb = colors[segment] * (1-fraction[...,None]) + colors[segment+1] * fraction[...,None]
    rgba = np.zeros((*values.shape,4),dtype=np.uint8)
    rgba[...,:3] = np.clip(np.nan_to_num(rgb),0,255).astype(np.uint8)
    rgba[...,3] = np.where(positive, 150 + (t*75).astype(np.uint8), 0)
    return rgba,(lo,hi)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    exclusive = ap.add_mutually_exclusive_group(required=True)
    exclusive.add_argument('--dem', help='CartoDEM GeoTIFF path')
    exclusive.add_argument('--rain', help='GSMap ISRO GeoTIFF path')
    ap.add_argument('--bbox', help='Optional minlon,minlat,maxlon,maxlat in EPSG:4326')
    ap.add_argument('--date', help='Observation date YYYY-MM-DD (rainfall); otherwise local preparation date')
    args = ap.parse_args()
    srcpath = args.dem or args.rain
    try:
        with rasterio.open(srcpath) as src:
            if src.count == 0:
                raise ValueError('No raster bands')
            if args.bbox:
                bounds = [float(v) for v in args.bbox.split(',')]
                if len(bounds) != 4 or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
                    raise ValueError('Invalid bbox; expected minlon,minlat,maxlon,maxlat')
            else:
                bounds = source_bounds(src)
            data, valid = reproject_band(src, bounds)
        date = args.date or datetime.now(timezone.utc).date().isoformat()
        datetime.strptime(date, '%Y-%m-%d')
        ROOT.mkdir(parents=True, exist_ok=True)
        if args.dem:
            out = ROOT / 'hillshade.png'
            rgba = hillshade(data, valid, bounds)
            note = 'CartoDEM-based visual hillshade; NOT measured flood hazard or flood extent'
            source = 'Bhoonidhi / CartoDEM (NRSC)'
            key = 'hillshade'
        else:
            out = ROOT / 'rainfall.png'
            rgba, extent = rainfall_palette(data, valid)
            note = f'GSMap ISRO rainfall, data range {extent[0]:.3g}–{extent[1]:.3g} SOURCE UNITS; cyan-to-violet relative scale, NOT alert thresholds'
            print('Rainfall value range in source units:', extent)
            source = 'MOSDAC / GSMap ISRO (SAC-ISRO)'
            key = 'rainfall'
        Image.fromarray(rgba,'RGBA').save(out, optimize=True)
        manifest_update(key, out, bounds, source, date, note)
        print('Wrote', out, '|', note)
    except (OSError, ValueError, rasterio.errors.RasterioError) as e:
        print('Preparation failed:', e, file=sys.stderr)
        print('If your original MOSDAC file is HDF5 or NetCDF not readable by rasterio, export/reproject to GeoTIFF first.', file=sys.stderr)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
