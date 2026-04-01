# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoClassify
                                 A QGIS plugin
 Reclassifies raster layers based on literature-based thresholds and
 applies automatic styling.

 Supported index / data types
 ----------------------------
 Vegetation  : NDVI, NDWI, SAVI, EVI, NDMI, NBR, BSI
 Topographic : Elevation, Slope, Aspect
 Climate     : Annual Temperature, Annual Precipitation
 Other       : LULC, Erosion Risk, user-defined classifications

 Features
 --------
 * Preview & edit classification ranges before processing
 * Create, save, import and export user-defined classifications
 * CRS-aware area calculation (projected & geographic / WGS84)
 * Automatic QML style application
 * CSV export of per-class area statistics

                             -------------------
        begin                : 2026-03-31
        copyright            : (C) 2026
        email                : omerorucu@sdu.edu.tr
 ***************************************************************************/
"""


def classFactory(iface):
    """Load GeoClassify class from file geo_classify.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    :returns: Plugin instance.
    :rtype: GeoClassify
    """
    from .geo_classify import GeoClassify
    return GeoClassify(iface)
