# -*- coding: utf-8 -*-
"""
Style Manager
Automatically applies styles to classified rasters
"""

from qgis.core import (QgsRasterLayer, QgsPalettedRasterRenderer,
                       QgsColorRampShader, QgsSingleBandPseudoColorRenderer,
                       QgsRasterShader, Qgis)
from qgis.PyQt.QtGui import QColor
from xml.sax.saxutils import escape as _xml_escape
import os


class StyleManager:
    """Applies styles to raster layers"""

    def __init__(self):
        pass

    def apply_style(self, layer, classification_info):
        """
        Apply style to a raster layer based on classification info.

        Args:
            layer: QgsRasterLayer
            classification_info: Dictionary with classification details

        Returns:
            bool: True if successful
        """
        if not isinstance(layer, QgsRasterLayer) or not layer.isValid():
            return False

        try:
            ranges = classification_info.get('ranges', [])

            if not ranges:
                return False

            # Create paletted renderer with color ramp
            classes = []

            for i, range_item in enumerate(ranges, start=1):
                color_str = range_item.get('color', '#808080')
                label = range_item.get('label', f'Class {i}')

                # Parse color
                if color_str.startswith('#'):
                    color = QColor(color_str)
                else:
                    color = QColor('#808080')

                # Create class
                classes.append(QgsPalettedRasterRenderer.Class(i, color, label))

            # Create paletted renderer
            renderer = QgsPalettedRasterRenderer(
                layer.dataProvider(),
                1,  # band number
                classes
            )

            # Apply renderer to layer
            layer.setRenderer(renderer)

            # Refresh layer
            layer.triggerRepaint()

            # Save style as default
            style_path = self._get_style_path(layer, classification_info)
            if style_path:
                layer.saveNamedStyle(style_path)

            return True

        except Exception as e:
            print(f"Style application error: {str(e)}")
            return False

    def _get_style_path(self, layer, classification_info):
        """Get path for saving style file"""
        try:
            source = layer.source()
            if source:
                base_name = os.path.splitext(source)[0]
                style_path = f"{base_name}.qml"
                return style_path
        except:
            pass
        return None

    def create_qml_style(self, classification_info, output_path):
        """
        Create a QML style file.

        Args:
            classification_info: Dictionary with classification details
            output_path: Path to save QML file
        """
        ranges = classification_info.get('ranges', [])

        if not ranges:
            return False

        # Build QML content
        qml_content = self._generate_qml_content(ranges)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(qml_content)
            return True
        except Exception as e:
            print(f"QML creation error: {str(e)}")
            return False

    def _generate_qml_content(self, ranges):
        """Generate QML XML content"""

        qml_header = '''<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="4.0" styleCategories="AllStyleCategories">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" band="1" type="paletted">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
      </minMaxOrigin>
      <colorPalette>
'''

        qml_footer = '''      </colorPalette>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
'''

        # Build palette entries
        palette_entries = []
        for i, range_item in enumerate(ranges, start=1):
            color_str = range_item.get('color', '#808080')
            label = range_item.get('label', f'Class {i}')

            # Parse color
            if color_str.startswith('#'):
                color_hex = color_str[1:]  # Remove #
                r = int(color_hex[0:2], 16)
                g = int(color_hex[2:4], 16)
                b = int(color_hex[4:6], 16)
            else:
                color_hex = '808080'

            # Escape special XML characters in label to prevent malformed QML
            label_safe = _xml_escape(label)

            entry = f'        <paletteEntry value="{i}" color="#{color_hex}" alpha="255" label="{label_safe}"/>\n'
            palette_entries.append(entry)

        qml_content = qml_header + ''.join(palette_entries) + qml_footer

        return qml_content

    def apply_pseudo_color_style(self, layer, classification_info):
        """
        Apply pseudo-color (gradient) style for continuous data.

        Args:
            layer: QgsRasterLayer
            classification_info: Dictionary with classification details
        """
        if not isinstance(layer, QgsRasterLayer) or not layer.isValid():
            return False

        try:
            ranges = classification_info.get('ranges', [])

            if not ranges:
                return False

            # Create color ramp shader
            shader_function = QgsColorRampShader()
            shader_function.setColorRampType(QgsColorRampShader.Type.Interpolated)

            # Create color ramp items
            color_ramp_items = []

            for range_item in ranges:
                min_val = range_item.get('min', 0)
                max_val = range_item.get('max', 1)
                color_str = range_item.get('color', '#808080')
                label = range_item.get('label', '')

                # Use middle value for color ramp
                value = (min_val + max_val) / 2.0

                # Parse color
                if color_str.startswith('#'):
                    color = QColor(color_str)
                else:
                    color = QColor('#808080')

                item = QgsColorRampShader.ColorRampItem(value, color, label)
                color_ramp_items.append(item)

            shader_function.setColorRampItemList(color_ramp_items)

            # Create raster shader
            raster_shader = QgsRasterShader()
            raster_shader.setRasterShaderFunction(shader_function)

            # Create renderer
            renderer = QgsSingleBandPseudoColorRenderer(
                layer.dataProvider(),
                1,  # band number
                raster_shader
            )

            # Apply renderer
            layer.setRenderer(renderer)
            layer.triggerRepaint()

            return True

        except Exception as e:
            print(f"Pseudo-color style error: {str(e)}")
            return False
