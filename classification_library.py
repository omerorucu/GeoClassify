# -*- coding: utf-8 -*-
"""
Classification Library
Literature-based classification thresholds and definitions
"""


class ClassificationLibrary:
    """Raster classification library"""

    def __init__(self):
        self.classifications = {
            # VEGETATION INDICES
            'ndvi': {
                'name': 'NDVI (Normalized Difference Vegetation Index)',
                'description': 'Index used to determine vegetation density. Values range from -1 to +1.',
                'unit': 'Index Value',
                'ranges': [
                    {'min': -1.0, 'max': 0.0,  'label': 'Water/Snow/Rock',          'color': '#0000FF'},
                    {'min': 0.0,  'max': 0.1,  'label': 'Bare Soil',                'color': '#8B4513'},
                    {'min': 0.1,  'max': 0.2,  'label': 'Sparse Vegetation',        'color': '#FFE4B5'},
                    {'min': 0.2,  'max': 0.3,  'label': 'Moderate Vegetation',      'color': '#ADFF2F'},
                    {'min': 0.3,  'max': 0.4,  'label': 'Dense Vegetation',         'color': '#7CFC00'},
                    {'min': 0.4,  'max': 0.6,  'label': 'Very Dense Vegetation',    'color': '#32CD32'},
                    {'min': 0.6,  'max': 1.0,  'label': 'Very Healthy Vegetation',  'color': '#006400'},
                ]
            },

            'ndwi': {
                'name': 'NDWI (Normalized Difference Water Index)',
                'description': 'Used to detect water content and water bodies.',
                'unit': 'Index Value',
                'ranges': [
                    {'min': -1.0, 'max': -0.3, 'label': 'Dry Area/Vegetation',      'color': '#8B4513'},
                    {'min': -0.3, 'max': -0.1, 'label': 'Moist Soil',               'color': '#DEB887'},
                    {'min': -0.1, 'max': 0.0,  'label': 'Wet Area',                 'color': '#F0E68C'},
                    {'min': 0.0,  'max': 0.2,  'label': 'Water Stress',             'color': '#87CEEB'},
                    {'min': 0.2,  'max': 0.4,  'label': 'Moderate Water Content',   'color': '#4682B4'},
                    {'min': 0.4,  'max': 0.6,  'label': 'High Water Content',       'color': '#1E90FF'},
                    {'min': 0.6,  'max': 1.0,  'label': 'Water Body',               'color': '#00008B'},
                ]
            },

            'savi': {
                'name': 'SAVI (Soil Adjusted Vegetation Index)',
                'description': 'Evaluates vegetation cover while minimizing soil reflectance.',
                'unit': 'Index Value',
                'ranges': [
                    {'min': -1.0, 'max': 0.0,  'label': 'Water/Artificial Surface', 'color': '#808080'},
                    {'min': 0.0,  'max': 0.1,  'label': 'Bare Soil',                'color': '#D2691E'},
                    {'min': 0.1,  'max': 0.2,  'label': 'Very Sparse Vegetation',   'color': '#F4A460'},
                    {'min': 0.2,  'max': 0.3,  'label': 'Sparse Vegetation',        'color': '#BDB76B'},
                    {'min': 0.3,  'max': 0.4,  'label': 'Moderate Vegetation',      'color': '#9ACD32'},
                    {'min': 0.4,  'max': 0.6,  'label': 'Dense Vegetation',         'color': '#228B22'},
                    {'min': 0.6,  'max': 1.0,  'label': 'Very Dense Vegetation',    'color': '#006400'},
                ]
            },

            'evi': {
                'name': 'EVI (Enhanced Vegetation Index)',
                'description': 'Vegetation index corrected for atmospheric effects and soil background.',
                'unit': 'Index Value',
                'ranges': [
                    {'min': -1.0, 'max': 0.0,  'label': 'Non-Vegetated',            'color': '#696969'},
                    {'min': 0.0,  'max': 0.2,  'label': 'Very Low Vegetation',      'color': '#CD853F'},
                    {'min': 0.2,  'max': 0.3,  'label': 'Low Vegetation',           'color': '#DAA520'},
                    {'min': 0.3,  'max': 0.4,  'label': 'Low-Moderate Vegetation',  'color': '#ADFF2F'},
                    {'min': 0.4,  'max': 0.5,  'label': 'Moderate Vegetation',      'color': '#7FFF00'},
                    {'min': 0.5,  'max': 0.7,  'label': 'Dense Vegetation',         'color': '#00FF00'},
                    {'min': 0.7,  'max': 1.0,  'label': 'Very Dense Vegetation',    'color': '#008000'},
                ]
            },

            'ndmi': {
                'name': 'NDMI (Normalized Difference Moisture Index)',
                'description': 'Detects plant water content and moisture stress.',
                'unit': 'Index Value',
                'ranges': [
                    {'min': -1.0, 'max': -0.4, 'label': 'Very Dry/Stressed',        'color': '#8B0000'},
                    {'min': -0.4, 'max': -0.2, 'label': 'Dry',                      'color': '#CD5C5C'},
                    {'min': -0.2, 'max': 0.0,  'label': 'Slightly Moist',           'color': '#F0E68C'},
                    {'min': 0.0,  'max': 0.2,  'label': 'Moderately Moist',         'color': '#90EE90'},
                    {'min': 0.2,  'max': 0.4,  'label': 'Moist',                    'color': '#3CB371'},
                    {'min': 0.4,  'max': 0.6,  'label': 'Very Moist',               'color': '#228B22'},
                    {'min': 0.6,  'max': 1.0,  'label': 'Extremely Moist',          'color': '#006400'},
                ]
            },

            # TOPOGRAPHIC DATA
            'elevation': {
                'name': 'Elevation Classification',
                'description': 'Elevation zones from DEM data (optimized for general use).',
                'unit': 'Metres',
                'ranges': [
                    {'min': -500, 'max': 0,    'label': 'Below Sea Level',          'color': '#0000CD'},
                    {'min': 0,    'max': 200,  'label': 'Coastal Plain (0-200m)',    'color': '#228B22'},
                    {'min': 200,  'max': 500,  'label': 'Low Plain (200-500m)',      'color': '#32CD32'},
                    {'min': 500,  'max': 1000, 'label': 'High Plain (500-1000m)',    'color': '#ADFF2F'},
                    {'min': 1000, 'max': 1500, 'label': 'Mid Elevation (1000-1500m)','color': '#FFD700'},
                    {'min': 1500, 'max': 2000, 'label': 'High Area (1500-2000m)',    'color': '#FF8C00'},
                    {'min': 2000, 'max': 2500, 'label': 'Mountainous (2000-2500m)', 'color': '#CD853F'},
                    {'min': 2500, 'max': 3500, 'label': 'High Mountain (2500-3500m)','color': '#8B4513'},
                    {'min': 3500, 'max': 5500, 'label': 'Very High Mountain (>3500m)','color': '#FFFFFF'},
                ]
            },

            'slope': {
                'name': 'Slope Classification',
                'description': 'Terrain slope categories (degrees).',
                'unit': 'Degrees',
                'ranges': [
                    {'min': 0,  'max': 2,  'label': 'Flat (0-2°)',           'color': '#006400'},
                    {'min': 2,  'max': 5,  'label': 'Gentle (2-5°)',         'color': '#228B22'},
                    {'min': 5,  'max': 10, 'label': 'Moderate (5-10°)',      'color': '#9ACD32'},
                    {'min': 10, 'max': 15, 'label': 'Sloped (10-15°)',       'color': '#FFD700'},
                    {'min': 15, 'max': 25, 'label': 'Steep (15-25°)',        'color': '#FF8C00'},
                    {'min': 25, 'max': 35, 'label': 'Very Steep (25-35°)',   'color': '#FF4500'},
                    {'min': 35, 'max': 90, 'label': 'Extreme (>35°)',        'color': '#8B0000'},
                ]
            },

            'aspect': {
                'name': 'Aspect Classification',
                'description': 'Terrain orientation categories.',
                'unit': 'Degrees',
                'ranges': [
                    # QGIS/GDAL aspect: flat terrain is encoded as -1.
                    # North wraps around: 0–22.5° and 337.5–360°.
                    # Flat range ends at 0.01 and North begins at 0.01
                    # to avoid a classification gap for values in [0, 0.01).
                    {'min': -1,    'max': 0.01, 'label': 'Flat/No Aspect',   'color': '#FFFFFF'},
                    {'min': 0.01,  'max': 22.5, 'label': 'North',            'color': '#0000FF'},
                    {'min': 22.5,  'max': 67.5, 'label': 'Northeast',        'color': '#4169E1'},
                    {'min': 67.5,  'max': 112.5,'label': 'East',             'color': '#00BFFF'},
                    {'min': 112.5, 'max': 157.5,'label': 'Southeast',        'color': '#FFD700'},
                    {'min': 157.5, 'max': 202.5,'label': 'South',            'color': '#FF8C00'},
                    {'min': 202.5, 'max': 247.5,'label': 'Southwest',        'color': '#FF4500'},
                    {'min': 247.5, 'max': 292.5,'label': 'West',             'color': '#DC143C'},
                    {'min': 292.5, 'max': 337.5,'label': 'Northwest',        'color': '#8B008B'},
                    {'min': 337.5, 'max': 360,  'label': 'North',            'color': '#0000FF'},
                ]
            },

            # CLIMATE DATA
            'temperature_annual': {
                'name': 'Annual Mean Temperature',
                'description': 'Annual average temperature classification.',
                'unit': '°C',
                'ranges': [
                    {'min': -50, 'max': -10, 'label': 'Very Cold (<-10°C)',   'color': '#000080'},
                    {'min': -10, 'max': 0,   'label': 'Cold (-10–0°C)',       'color': '#0000CD'},
                    {'min': 0,   'max': 5,   'label': 'Cool (0–5°C)',         'color': '#4169E1'},
                    {'min': 5,   'max': 10,  'label': 'Cool-Temperate (5–10°C)','color': '#87CEEB'},
                    {'min': 10,  'max': 15,  'label': 'Temperate (10–15°C)',  'color': '#90EE90'},
                    {'min': 15,  'max': 20,  'label': 'Warm (15–20°C)',       'color': '#FFD700'},
                    {'min': 20,  'max': 25,  'label': 'Hot (20–25°C)',        'color': '#FF8C00'},
                    {'min': 25,  'max': 50,  'label': 'Very Hot (>25°C)',     'color': '#FF0000'},
                ]
            },

            'precipitation_annual': {
                'name': 'Annual Total Precipitation',
                'description': 'Annual total precipitation classification.',
                'unit': 'mm',
                'ranges': [
                    {'min': 0,    'max': 250,   'label': 'Hyper-Arid (<250mm)',      'color': '#8B0000'},
                    {'min': 250,  'max': 500,   'label': 'Arid (250–500mm)',         'color': '#CD853F'},
                    {'min': 500,  'max': 750,   'label': 'Semi-Arid (500–750mm)',    'color': '#DAA520'},
                    {'min': 750,  'max': 1000,  'label': 'Semi-Humid (750–1000mm)',  'color': '#FFD700'},
                    {'min': 1000, 'max': 1500,  'label': 'Humid (1000–1500mm)',      'color': '#ADFF2F'},
                    {'min': 1500, 'max': 2000,  'label': 'Very Humid (1500–2000mm)','color': '#32CD32'},
                    {'min': 2000, 'max': 3000,  'label': 'Wet (2000–3000mm)',        'color': '#228B22'},
                    {'min': 3000, 'max': 10000, 'label': 'Very Wet (>3000mm)',       'color': '#006400'},
                ]
            },

            # LAND USE AND SOIL
            'lulc': {
                'name': 'Land Use / Land Cover (LULC)',
                'description': 'Basic land use categories.',
                'unit': 'Class',
                'ranges': [
                    {'min': 1, 'max': 1, 'label': 'Urban/Built-up',   'color': '#FF0000'},
                    {'min': 2, 'max': 2, 'label': 'Agricultural Land','color': '#FFD700'},
                    {'min': 3, 'max': 3, 'label': 'Grassland/Pasture','color': '#90EE90'},
                    {'min': 4, 'max': 4, 'label': 'Forest',           'color': '#006400'},
                    {'min': 5, 'max': 5, 'label': 'Water Body',       'color': '#0000FF'},
                    {'min': 6, 'max': 6, 'label': 'Wetland',          'color': '#00CED1'},
                    {'min': 7, 'max': 7, 'label': 'Bare Land/Rock',   'color': '#8B4513'},
                    {'min': 8, 'max': 8, 'label': 'Ice/Snow',         'color': '#FFFFFF'},
                ]
            },

            # EROSION AND RISK ANALYSES
            'erosion_risk': {
                'name': 'Erosion Risk Class',
                'description': 'Soil erosion risk assessment.',
                'unit': 'Risk Level',
                'ranges': [
                    {'min': 1, 'max': 1, 'label': 'Very Low Risk',  'color': '#006400'},
                    {'min': 2, 'max': 2, 'label': 'Low Risk',       'color': '#32CD32'},
                    {'min': 3, 'max': 3, 'label': 'Moderate Risk',  'color': '#FFD700'},
                    {'min': 4, 'max': 4, 'label': 'High Risk',      'color': '#FF8C00'},
                    {'min': 5, 'max': 5, 'label': 'Very High Risk', 'color': '#FF0000'},
                ]
            },

            # REMOTE SENSING INDICES
            'nbr': {
                'name': 'NBR (Normalized Burn Ratio)',
                'description': 'Index used for burned area detection.',
                'unit': 'Index Value',
                'ranges': [
                    {'min': -1.0,  'max': -0.5,  'label': 'High Burn Severity',     'color': '#8B0000'},
                    {'min': -0.5,  'max': -0.25, 'label': 'Moderate-High Burn',     'color': '#CD5C5C'},
                    {'min': -0.25, 'max': -0.1,  'label': 'Low-Moderate Burn',      'color': '#F08080'},
                    {'min': -0.1,  'max': 0.1,   'label': 'Unburned',               'color': '#FFE4B5'},
                    {'min': 0.1,   'max': 0.3,   'label': 'Healthy Vegetation',     'color': '#ADFF2F'},
                    {'min': 0.3,   'max': 1.0,   'label': 'High Vegetation Density','color': '#006400'},
                ]
            },

            'bsi': {
                'name': 'BSI (Bare Soil Index)',
                'description': 'Index for detecting bare soil.',
                'unit': 'Index Value',
                'ranges': [
                    {'min': -1.0, 'max': -0.2, 'label': 'Vegetated',          'color': '#006400'},
                    {'min': -0.2, 'max': 0.0,  'label': 'Partial Cover',      'color': '#32CD32'},
                    {'min': 0.0,  'max': 0.1,  'label': 'Low Bare Soil',      'color': '#F0E68C'},
                    {'min': 0.1,  'max': 0.2,  'label': 'Moderate Bare Soil', 'color': '#DAA520'},
                    {'min': 0.2,  'max': 0.4,  'label': 'Bare Soil',          'color': '#CD853F'},
                    {'min': 0.4,  'max': 1.0,  'label': 'Completely Bare',    'color': '#8B4513'},
                ]
            },
        }

    def get_classification(self, key):
        """Get classification info by key"""
        return self.classifications.get(key, None)

    def get_all_classifications(self):
        """Get all classifications"""
        return self.classifications

    def get_classification_names(self):
        """Get list of classification names"""
        return [(k, v['name']) for k, v in self.classifications.items()]
