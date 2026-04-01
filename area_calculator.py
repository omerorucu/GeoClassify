# -*- coding: utf-8 -*-
"""
Area Calculator
Calculates the area of each class in reclassified raster layers.

CRS Support:
  - Projected (UTM, etc.)  → pixel size already in metres, direct calculation
  - Geographic (WGS84/degrees) → real pixel area calculated per row using
                                  haversine-based latitude-dependent formula
"""

import os
import csv
import math
import numpy as np
from osgeo import gdal, osr


# ---------------------------------------------------------------------------
# Helper: single pixel area (m²) for geographic CRS
# ---------------------------------------------------------------------------
def _geographic_pixel_area_m2(lat_center_deg, pixel_height_deg, pixel_width_deg):
    """
    Real area of a pixel at the given latitude on the WGS84 ellipsoid.
    Uses meridian and parallel arc lengths.

    WGS84: a=6378137.0 m, e²=0.00669437999014
    """
    a  = 6_378_137.0
    e2 = 0.00669437999014

    lat     = math.radians(lat_center_deg)
    sin_lat = math.sin(lat)

    # Meridian radius of curvature (north-south)
    M = a * (1 - e2) / (1 - e2 * sin_lat**2)**1.5
    # Normal radius (east-west)
    N = a / math.sqrt(1 - e2 * sin_lat**2)

    height_m = M * math.radians(abs(pixel_height_deg))
    width_m  = N * math.cos(lat) * math.radians(abs(pixel_width_deg))

    return height_m * width_m


# ---------------------------------------------------------------------------
class AreaCalculator:
    """Calculates areas of raster classes"""

    def __init__(self):
        pass

    # -----------------------------------------------------------------------
    def _detect_crs_type(self, ds):
        """Returns the CRS type of the raster."""
        wkt = ds.GetProjection()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(wkt)

        is_geo  = bool(srs.IsGeographic())
        is_proj = bool(srs.IsProjected())
        unit    = (srs.GetLinearUnitsName() if is_proj else
                   'degree'                 if is_geo  else 'unknown')

        return {
            'is_geographic': is_geo,
            'is_projected':  is_proj,
            'unit_name':     unit,
            'wkt':           wkt,
            'srs':           srs,
        }

    # -----------------------------------------------------------------------
    def calculate_class_areas(self, raster_path, classification_info):
        """
        Calculates the area of each class in pixel count and real units.

        Uses block-based reading to avoid loading the entire raster into RAM,
        making it safe for large (multi-GB) GeoTIFFs.

        Returns: (results: list[dict], crs_note: str)
        """
        if not os.path.exists(raster_path):
            raise FileNotFoundError(f"Raster file not found: {raster_path}")

        ds = gdal.Open(raster_path)
        if ds is None:
            raise RuntimeError(f"Could not open raster file: {raster_path}")

        band          = ds.GetRasterBand(1)
        nodata        = band.GetNoDataValue()
        gt            = ds.GetGeoTransform()
        crs           = self._detect_crs_type(ds)
        n_rows        = ds.RasterYSize
        n_cols        = ds.RasterXSize

        pixel_width  = abs(gt[1])
        pixel_height = abs(gt[5])
        origin_y     = gt[3]

        ranges  = classification_info.get('ranges', [])
        n_classes = len(ranges)

        # Accumulators — one entry per class (index 0 = class_id 1)
        pixel_counts = np.zeros(n_classes, dtype=np.int64)
        area_m2_sums = np.zeros(n_classes, dtype=np.float64)

        # ------------------------------------------------------------------
        # Area strategy: pre-compute a per-row area array for geographic CRS
        # ------------------------------------------------------------------
        if crs['is_projected']:
            linear_units = crs['srs'].GetLinearUnits()
            px_m2_fixed  = (pixel_width * linear_units) * (pixel_height * linear_units)
            row_px_area  = None  # not used

            crs_note = (f"Projected CRS ({crs['unit_name']}). "
                        f"Fixed pixel area: {px_m2_fixed:,.4f} m²")

        elif crs['is_geographic']:
            px_m2_fixed = None
            row_px_area = np.empty(n_rows, dtype=np.float64)
            for i in range(n_rows):
                lat = origin_y - (i + 0.5) * pixel_height
                row_px_area[i] = _geographic_pixel_area_m2(lat, pixel_height, pixel_width)

            avg_px_m2 = float(np.mean(row_px_area))
            crs_note = (f"Geographic CRS (WGS84/degrees). "
                        f"Real area calculated per latitude. "
                        f"Average pixel area: {avg_px_m2:,.2f} m²")
        else:
            px_m2_fixed = pixel_width * pixel_height
            row_px_area = None
            crs_note = ("⚠ CRS could not be determined. "
                        "Pixel size assumed in metres; areas may be inaccurate.")

        # ------------------------------------------------------------------
        # Block-based processing
        # ------------------------------------------------------------------
        BLOCK_ROWS = 256  # read 256 rows at a time — safe for any raster size

        # Convert nodata to int32 for reliable comparison after block cast.
        # reclassified output is always integer (DATA_TYPE=1 → Byte/Int16),
        # but gdal returns nodata as float. We round to nearest int.
        if nodata is not None:
            nodata_int = int(round(nodata))
        else:
            nodata_int = None

        total_valid_pixels = 0

        for y_off in range(0, n_rows, BLOCK_ROWS):
            rows_in_block = min(BLOCK_ROWS, n_rows - y_off)

            # Single read per block — cast to int32 immediately
            raw_block = band.ReadAsArray(0, y_off, n_cols, rows_in_block)

            if raw_block is None:
                continue

            block = raw_block.astype(np.int32)

            # Build valid-pixel mask using the already-cast int32 block
            if nodata_int is not None:
                valid_mask = block != nodata_int
            else:
                valid_mask = np.ones(block.shape, dtype=bool)

            total_valid_pixels += int(np.sum(valid_mask))

            # Build per-row area weights for this block (geographic CRS only)
            if row_px_area is not None:
                block_row_areas = row_px_area[y_off: y_off + rows_in_block]
                area_weight = np.broadcast_to(
                    block_row_areas[:, np.newaxis], block.shape)
            else:
                area_weight = None

            for class_idx in range(n_classes):
                class_id   = class_idx + 1
                class_mask = (block == class_id) & valid_mask
                px_count   = int(np.sum(class_mask))
                pixel_counts[class_idx] += px_count

                if px_count > 0:
                    if area_weight is not None:
                        area_m2_sums[class_idx] += float(np.sum(area_weight[class_mask]))
                    else:
                        area_m2_sums[class_idx] += px_count * px_m2_fixed

        ds = None  # close dataset

        # ------------------------------------------------------------------
        # Build result list
        # ------------------------------------------------------------------
        results = []
        for class_idx, rng in enumerate(ranges):
            label   = rng.get('label', f'Class {class_idx + 1}')
            color   = rng.get('color', '#808080')
            min_val = rng.get('min', 0)
            max_val = rng.get('max', 1)

            px  = int(pixel_counts[class_idx])
            m2  = float(area_m2_sums[class_idx])
            ha  = m2 / 10_000.0
            km2 = m2 / 1_000_000.0
            pct = (px / total_valid_pixels * 100.0) if total_valid_pixels > 0 else 0.0

            results.append({
                'class_id':    class_idx + 1,
                'label':       label,
                'color':       color,
                'min_value':   min_val,
                'max_value':   max_val,
                'pixel_count': px,
                'area_m2':     round(m2,  2),
                'area_ha':     round(ha,  4),
                'area_km2':    round(km2, 6),
                'percentage':  round(pct, 4),
            })

        total_px = sum(r['pixel_count'] for r in results)
        total_m2 = sum(r['area_m2']     for r in results)
        results.append({
            'class_id':    'TOTAL',
            'label':       'TOTAL',
            'color':       '',
            'min_value':   '',
            'max_value':   '',
            'pixel_count': total_px,
            'area_m2':     round(total_m2,               2),
            'area_ha':     round(total_m2 / 10_000.0,    4),
            'area_km2':    round(total_m2 / 1_000_000.0, 6),
            'percentage':  100.0,
        })

        return results, crs_note

    # -----------------------------------------------------------------------
    def export_to_csv(self, area_results, csv_path, classification_info,
                      raster_path=None, include_metadata=True, crs_note=None):
        """Writes area results to CSV."""
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                if include_metadata:
                    w.writerow(['# Raster Classification Area Analysis'])
                    w.writerow(['# Classification:', classification_info.get('name', '')])
                    w.writerow(['# Description:',    classification_info.get('description', '')])
                    w.writerow(['# Unit:',            classification_info.get('unit', '')])
                    if raster_path:
                        w.writerow(['# Source Raster:', os.path.basename(raster_path)])
                    if crs_note:
                        w.writerow(['# CRS Info:', crs_note])
                    w.writerow([])

                w.writerow(['Class No', 'Label', 'Color (Hex)',
                            'Min Value', 'Max Value', 'Pixel Count',
                            'Area (m²)', 'Area (ha)', 'Area (km²)', 'Percentage (%)'])
                for row in area_results:
                    w.writerow([
                        row['class_id'], row['label'],    row['color'],
                        row['min_value'], row['max_value'], row['pixel_count'],
                        row['area_m2'],  row['area_ha'],   row['area_km2'],
                        row['percentage'],
                    ])
            return True
        except Exception as e:
            print(f"CSV write error: {str(e)}")
            return False

    # -----------------------------------------------------------------------
    def get_pixel_size_info(self, raster_path):
        """Returns pixel size and CRS information."""
        ds = gdal.Open(raster_path)
        if ds is None:
            return None
        gt  = ds.GetGeoTransform()
        crs = self._detect_crs_type(ds)
        ds  = None
        return {
            'pixel_width':  abs(gt[1]),
            'pixel_height': abs(gt[5]),
            'crs_type':     ('projected'  if crs['is_projected']  else
                             'geographic' if crs['is_geographic'] else 'unknown'),
            'unit_name':    crs['unit_name'],
        }
