# GeoClassify

**A literature-based raster classification toolkit for QGIS**

GeoClassify is a free, open-source QGIS 4 plugin that automates the reclassification of raster datasets using scientifically validated, peer-reviewed threshold values. It integrates reclassification, automatic styling, CRS-aware area calculation, and batch processing into a single workflow — eliminating the need for manual threshold entry, symbol design, or separate area computation.

---

## Features

- **14 built-in classification schemes** — vegetation indices, topographic parameters, climate variables, land use/land cover, and erosion risk, all with literature-derived thresholds
- **Interactive preview editor** — inspect and modify any classification range, label, or colour before processing
- **User-defined classifications** — create, save, edit, import, and export custom schemes in JSON format
- **CRS-aware area calculator** — geodetically correct per-class areas (m², km², %) for both projected and geographic (WGS 84) coordinate systems
- **Automatic QML style application** — classified layers are styled and added to the QGIS project immediately
- **Batch processing** — reclassify an entire folder or a selected list of raster files in a single run
- **CSV export** — per-class area statistics saved alongside every output raster

---

## Supported Classification Schemes

| Category | Types |
|---|---|
| Vegetation indices | NDVI, NDWI, SAVI, EVI, NDMI, NBR, BSI |
| Topographic data | Elevation, Slope, Aspect |
| Climate data | Annual mean temperature, Annual total precipitation |
| Land use / land cover | LULC (8 classes) |
| Risk analysis | Erosion risk class |
| Custom | Unlimited user-defined schemes (JSON) |

All default thresholds are traceable to peer-reviewed publications (Tucker, 1979; Huete, 1988; Gao, 1996; Key & Benson, 2006; and others — see [references](#references)).

---

## Requirements

| Component | Version |
|---|---|
| QGIS | 4.0 or later (Qt6 / PyQt6) |
| Python | 3.9+ (bundled with QGIS) |
| GDAL | 3.0+ (bundled with QGIS) |
| NumPy | Any recent version (bundled with QGIS) |

No additional external Python packages are required.

> **QGIS 3.x users:** Replace `PyQt6` import statements with `PyQt5` equivalents — a two-line change documented in [`__init__.py`](./__init__.py). All functionality is otherwise identical on QGIS 3.22 LTR or later.

---

## Installation

### Option 1 — QGIS Plugin Manager (recommended)

1. Open QGIS.
2. Go to **Plugins → Manage and Install Plugins**.
3. Search for `GeoClassify`.
4. Click **Install Plugin**.

### Option 2 — Manual installation from ZIP

**Windows**
```
1. Extract the GeoClassify folder from the ZIP archive.
2. Copy the folder to:
   %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
3. Restart QGIS.
4. Enable the plugin in Plugins → Manage and Install Plugins → Installed.
```

**Linux**
```bash
cp -r GeoClassify ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

**macOS**
```bash
cp -r GeoClassify ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/
```

Alternatively, use the provided installation scripts:

```bash
# Linux / macOS
chmod +x install.sh && ./install.sh

# Windows — double-click install.bat
```

---

## Quick Start

1. Load a raster layer in QGIS (e.g. a pre-computed NDVI raster).
2. Go to **Raster → GeoClassify**.
3. Select the input layer and classification type.
4. Set an output file path.
5. Click **OK** — a Classification Preview dialog opens.
6. Review or adjust the thresholds, then click **Continue**.
7. The classified layer is added to the map with automatic styling.

For a full step-by-step tutorial see the [wiki](https://github.com/omerorucu/GeoClassify/wiki).

---

## Computing Indices Before Classification

GeoClassify classifies pre-computed rasters. Use the QGIS **Raster Calculator** to derive indices from multi-band imagery before running the plugin.

| Index | Expression (Sentinel-2) | Expression (Landsat 8/9) |
|---|---|---|
| NDVI | `(B8 - B4) / (B8 + B4)` | `(B5 - B4) / (B5 + B4)` |
| NDWI | `(B3 - B8) / (B3 + B8)` | `(B3 - B5) / (B3 + B5)` |
| SAVI | `((B8 - B4) / (B8 + B4 + 0.5)) * 1.5` | `((B5 - B4) / (B5 + B4 + 0.5)) * 1.5` |
| EVI | `2.5 * (B8 - B4) / (B8 + 6*B4 - 7.5*B2 + 1)` | `2.5 * (B5 - B4) / (B5 + 6*B4 - 7.5*B2 + 1)` |
| NDMI | `(B8 - B11) / (B8 + B11)` | `(B5 - B6) / (B5 + B6)` |
| NBR | `(B8 - B12) / (B8 + B12)` | `(B5 - B7) / (B5 + B7)` |
| BSI | `((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2))` | `((B6 + B4) - (B5 + B2)) / ((B6 + B4) + (B5 + B2))` |

For topographic parameters (slope, aspect), use **Raster → Analysis → Slope / Aspect** in QGIS before classifying.

---

## User-Defined Classifications

Custom schemes are stored in `custom_classifications.json`. You can create them interactively through the plugin UI, or author them directly in JSON:

```json
{
  "my_lst": {
    "name": "Land Surface Temperature",
    "description": "Urban thermal zones from Landsat TIRS Band 10.",
    "unit": "°C",
    "ranges": [
      { "min": 10, "max": 20, "label": "Cool surface",      "color": "#87CEEB" },
      { "min": 20, "max": 30, "label": "Moderate surface",  "color": "#FFFF00" },
      { "min": 30, "max": 40, "label": "Warm surface",      "color": "#FF8C00" },
      { "min": 40, "max": 60, "label": "Urban heat island", "color": "#FF0000" }
    ]
  }
}
```

Export and import schemes via **GeoClassify → Manage Classifications → Export / Import JSON** to share them across projects or with collaborators.

---

## Supported File Formats

| Type | Formats |
|---|---|
| Input rasters | GeoTIFF (`.tif`, `.tiff`), ERDAS Imagine (`.img`), ASCII Grid (`.asc`) |
| Output raster | GeoTIFF (`.tif`) |
| Style file | QGIS Layer Style (`.qml`) |
| Area statistics | CSV (`.csv`) |
| Custom schemes | JSON (`.json`) |

---

## Contributing

Contributions are welcome — especially new classification schemes backed by peer-reviewed literature.

```bash
# 1. Fork the repository
# 2. Create a feature branch
git checkout -b feature/new-scheme

# 3. Add your scheme to classification_library.py following the existing pattern
# 4. Commit and push
git commit -am "Add <scheme name> classification"
git push origin feature/new-scheme

# 5. Open a Pull Request
```

When submitting a new built-in classification scheme, please include the full citation for the threshold values in your PR description.

---

## References

The default classification thresholds are derived from the following peer-reviewed publications:

- Rouse, J. W., et al. (1974). Monitoring vegetation systems in the Great Plains with ERTS. *Proceedings of the Third ERTS Symposium*, NASA.
- Tucker, C. J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment*, 8(2), 127–150.
- Huete, A. R. (1988). A soil-adjusted vegetation index (SAVI). *Remote Sensing of Environment*, 25(3), 295–309.
- Liu, H. Q., & Huete, A. (1995). A feedback based modification of the NDVI to minimize canopy background and atmospheric noise. *IEEE Transactions on Geoscience and Remote Sensing*, 33(2), 457–465.
- Gao, B. C. (1996). NDWI — A normalized difference water index for remote sensing of vegetation liquid water from space. *Remote Sensing of Environment*, 58(3), 257–266.
- Wilson, E. H., & Sader, S. A. (2002). Detection of forest harvest type using multiple dates of Landsat TM imagery. *Remote Sensing of Environment*, 80(3), 385–396.
- Key, C. H., & Benson, N. C. (2006). Landscape assessment (LA): Sampling and analysis methods. In *FIREMON: Fire Effects Monitoring and Inventory System*. USDA Forest Service.
- Rikimaru, A., Roy, P. S., & Miyatake, S. (2002). Tropical forest cover density mapping. *Tropical Ecology*, 43(1), 39–47.
- Renard, K. G., et al. (1997). *Predicting Soil Erosion by Water: A Guide to Conservation Planning with RUSLE*. USDA Agricultural Handbook No. 703.
- Zevenbergen, L. W., & Thorne, C. R. (1987). Quantitative analysis of land surface topography. *Earth Surface Processes and Landforms*, 12(1), 47–56.

---

## Citation

If you use GeoClassify in your research, please cite:

> Örücü, Ö. K. (2025). GeoClassify: A literature-based raster classification toolkit for QGIS (Version 1.0.0) \[Software\]. Süleyman Demirel University. https://github.com/omerorucu/GeoClassify

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

Copyright © 2025 Ömer K. Örücü, Süleyman Demirel University, Isparta, Türkiye.
