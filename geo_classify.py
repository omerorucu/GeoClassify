# -*- coding: utf-8 -*-
"""
QGIS GeoClassify Plugin
Reclassifies raster layers based on literature-based thresholds
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QAction, QFileDialog, QMessageBox, QDialog,
                                 QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                                 QListWidgetItem, QPushButton, QTableWidget,
                                 QTableWidgetItem, QHeaderView, QSizePolicy,
                                 QAbstractItemView)
from qgis.core import (QgsProject, QgsRasterLayer,
                       QgsProcessingFeedback, QgsProcessingContext,
                       QgsMapLayer, QgsRasterBandStats,
                       Qgis)
from qgis.gui import QgsMessageBar
import processing
import os

from .geo_classify_dialog import GeoClassifyDialog
from .classification_library import ClassificationLibrary
from .style_manager import StyleManager
from .custom_classification_manager import CustomClassificationManager
from .custom_classification_dialog import CustomClassificationDialog
from .classification_preview_dialog import ClassificationPreviewDialog
from .manage_classifications_dialog import ManageClassificationsDialog
from .area_calculator import AreaCalculator
from .batch_processing_dialog import BatchProcessingDialog


class GeoClassify:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeoClassify_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&GeoClassify')

        self.dlg = None
        self.classification_lib = ClassificationLibrary()
        self.custom_classification_mgr = CustomClassificationManager()
        self.style_manager = StyleManager()
        self.area_calculator = AreaCalculator()

    def tr(self, message):
        return QCoreApplication.translate('GeoClassify', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToRasterMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'GeoClassify'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&GeoClassify'), action)
            self.iface.removeToolBarIcon(action)

    # ------------------------------------------------------------------
    def run(self):
        """Run method that performs all the real work"""
        # Create a new dialog on each run so the layer list is always
        # up-to-date and signal connections are clean.
        self.dlg = GeoClassifyDialog(self.iface.mainWindow())

        # Input / output file browse buttons
        self.dlg.input_file_button.clicked.connect(self.select_input_file)
        self.dlg.output_file_button.clicked.connect(self.select_output_file)

        # Custom classification buttons
        self.dlg.create_custom_btn.clicked.connect(self.create_custom_classification)
        self.dlg.manage_custom_btn.clicked.connect(self.manage_custom_classifications)

        # Batch processing button
        self.dlg.batch_btn.clicked.connect(self.open_batch_dialog)

        # CSV file browse button
        self.dlg.csv_file_button.clicked.connect(self.select_csv_file)

        # Populate layer list and classification types
        self.populate_layer_combo()
        self.populate_classification_types()

        # Combo change signals
        self.dlg.layer_combo.currentIndexChanged.connect(self.on_layer_selected)
        self.dlg.classification_combo.currentIndexChanged.connect(
            self.update_classification_description)

        # Prepare file input field based on initial selection
        self.on_layer_selected(self.dlg.layer_combo.currentIndex())

        # Show dialog modally; start processing if OK is pressed
        if self.dlg.exec() == QDialog.DialogCode.Accepted:
            self.process_reclassification()

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    def open_batch_dialog(self):
        """Open BatchProcessingDialog using the currently selected classification."""
        current_data = self.dlg.classification_combo.currentData()
        if not current_data:
            QMessageBox.warning(self.dlg, "No Classification",
                                "Please select a classification type first.")
            return

        class_type, class_key = current_data
        classification_info = (
            self.classification_lib.get_classification(class_key)
            if class_type == 'builtin'
            else self.custom_classification_mgr.get_classification(class_key))

        if not classification_info:
            QMessageBox.warning(self.dlg, "Error",
                                "Could not retrieve classification information.")
            return

        # Let the user preview / edit ranges before batch
        preview = ClassificationPreviewDialog(classification_info, self.dlg)
        if preview.exec() != QDialog.DialogCode.Accepted:
            return
        classification_info = preview.get_classification_data()

        batch_dlg = BatchProcessingDialog(classification_info, self.dlg)
        batch_dlg.exec()

    # ------------------------------------------------------------------
    def populate_layer_combo(self):
        self.dlg.layer_combo.clear()
        # Mark file selection mode with "file" string
        self.dlg.layer_combo.addItem("📂 Select from File...", "file")
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if isinstance(layer, QgsRasterLayer) and layer.isValid():
                self.dlg.layer_combo.addItem(f"🗺  {layer.name()}", layer)

    def populate_classification_types(self):
        self.dlg.classification_combo.clear()
        classifications = self.classification_lib.get_all_classifications()
        self.dlg.classification_combo.addItem("--- Built-in Classifications ---", None)
        for key, value in classifications.items():
            self.dlg.classification_combo.addItem(value['name'], ('builtin', key))

        custom_classifications = self.custom_classification_mgr.get_all_classifications()
        if custom_classifications:
            self.dlg.classification_combo.addItem("--- User-Defined ---", None)
            for key, value in custom_classifications.items():
                self.dlg.classification_combo.addItem(
                    f"🔧 {value['name']}", ('custom', key))

    def update_classification_description(self):
        current_data = self.dlg.classification_combo.currentData()
        if not current_data:
            self.dlg.description_text.clear()
            return
        class_type, class_key = current_data
        if class_type == 'builtin':
            classification = self.classification_lib.get_classification(class_key)
        else:
            classification = self.custom_classification_mgr.get_classification(class_key)
        if classification:
            desc = f"<b>{classification['name']}</b><br><br>"
            desc += f"{classification['description']}<br><br>"
            desc += f"<b>Unit:</b> {classification['unit']}<br>"
            desc += f"<b>Number of Classes:</b> {len(classification['ranges'])}"
            self.dlg.description_text.setHtml(desc)

    def on_layer_selected(self, index):
        """Update input fields when layer selection changes"""
        data = self.dlg.layer_combo.currentData()
        # "file" → file selection mode; QgsRasterLayer → existing layer
        if data == "file" or data is None:
            self.dlg.input_file_line.setEnabled(True)
            self.dlg.input_file_button.setEnabled(True)
            self.dlg.input_file_line.clear()
        elif isinstance(data, QgsRasterLayer):
            self.dlg.input_file_line.setEnabled(False)
            self.dlg.input_file_button.setEnabled(False)
            self.dlg.input_file_line.setText(data.source())

    def select_input_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.dlg, "Select Input Raster File", "",
            "Raster Files (*.tif *.tiff *.img *.asc);;All Files (*.*)")
        if filename:
            self.dlg.input_file_line.setText(filename)

    def select_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self.dlg, "Select Output GeoTIFF File", "",
            "GeoTIFF Files (*.tif *.tiff);;All Files (*.*)")
        if filename:
            if not filename.lower().endswith(('.tif', '.tiff')):
                filename += '.tif'
            self.dlg.output_file_line.setText(filename)

    def select_csv_file(self):
        """Select CSV output file"""
        # Default location: next to the output raster
        default_dir = ""
        output_path = self.dlg.output_file_line.text()
        if output_path:
            default_dir = os.path.splitext(output_path)[0] + "_area_analysis.csv"

        filename, _ = QFileDialog.getSaveFileName(
            self.dlg, "Save CSV File", default_dir,
            "CSV Files (*.csv);;All Files (*.*)")
        if filename:
            if not filename.lower().endswith('.csv'):
                filename += '.csv'
            self.dlg.csv_file_line.setText(filename)

    # ------------------------------------------------------------------
    def process_reclassification(self):
        """Process the reclassification"""
        try:
            # --- Input layer ---
            layer_data = self.dlg.layer_combo.currentData()
            if layer_data == "file" or layer_data is None:
                # File selection mode
                input_path = self.dlg.input_file_line.text().strip()
                if not input_path:
                    QMessageBox.warning(self.dlg, "Error",
                                        "Please select an input raster file!")
                    return
                if not os.path.exists(input_path):
                    QMessageBox.warning(self.dlg, "Error",
                                        f"File not found:\n{input_path}")
                    return
                input_layer = QgsRasterLayer(input_path, "temp_input")
                if not input_layer.isValid():
                    QMessageBox.warning(self.dlg, "Error",
                                        "The selected file is not a valid raster!")
                    return
            elif isinstance(layer_data, QgsRasterLayer):
                # Existing layer mode
                input_layer = layer_data
                input_path = input_layer.source()
            else:
                QMessageBox.warning(self.dlg, "Error",
                                    "Please select a valid input layer or file!")
                return

            # --- Output path ---
            output_path = self.dlg.output_file_line.text()
            if not output_path:
                QMessageBox.warning(self.dlg, "Error",
                                    "Please specify an output file location!")
                return

            # --- Classification type ---
            current_data = self.dlg.classification_combo.currentData()
            if not current_data:
                QMessageBox.warning(self.dlg, "Error",
                                    "Please select a classification type!")
                return

            class_type, class_key = current_data
            if class_type == 'builtin':
                classification_info = self.classification_lib.get_classification(class_key)
            else:
                classification_info = self.custom_classification_mgr.get_classification(class_key)

            if not classification_info:
                QMessageBox.warning(self.dlg, "Error",
                                    "Could not retrieve classification information!")
                return

            # --- Preview / Edit dialog ---
            preview_dialog = ClassificationPreviewDialog(classification_info, self.dlg)

            if preview_dialog.exec():
                edited_classification = preview_dialog.get_classification_data()

                if preview_dialog.should_save_as_custom():
                    custom_name = preview_dialog.get_custom_name()
                    custom_key = custom_name.lower().replace(' ', '_')\
                        .replace('(', '').replace(')', '')
                    custom_key = ''.join(
                        c for c in custom_key if c.isalnum() or c == '_')

                    # Check for key collision before saving
                    key_exists = (
                        self.custom_classification_mgr.get_classification(custom_key) or
                        self.classification_lib.get_classification(custom_key)
                    )
                    if key_exists:
                        reply = QMessageBox.question(
                            self.dlg, "Key Already Exists",
                            f"The key '{custom_key}' is already in use. "
                            f"Do you want to overwrite it?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                        if reply == QMessageBox.StandardButton.No:
                            return

                    if self.custom_classification_mgr.add_classification(
                            custom_key, edited_classification):
                        self.iface.messageBar().pushMessage(
                            "Success",
                            f"Customized classification saved as '{custom_name}'!",
                            level=Qgis.MessageLevel.Success, duration=5)
                        self.populate_classification_types()

                classification_info = edited_classification
            else:
                return

            # --- Reclassification ---
            self.iface.messageBar().pushMessage(
                "Processing",
                f"Applying {classification_info['name']} classification...",
                level=Qgis.MessageLevel.Info, duration=5)

            self.reclassify_raster(input_path, output_path, classification_info)

            # --- Add layer to QGIS ---
            output_layer = QgsRasterLayer(
                output_path,
                os.path.splitext(os.path.basename(output_path))[0])

            if output_layer.isValid():
                QgsProject.instance().addMapLayer(output_layer)

                if self.dlg.apply_style_check.isChecked():
                    self.style_manager.apply_style(output_layer, classification_info)

                self.iface.mapCanvas().refresh()

                # -------------------------------------------------------
                # Area calculation and CSV export
                # -------------------------------------------------------
                if self.dlg.calculate_area_check.isChecked():
                    self._run_area_analysis(
                        output_path=output_path,
                        classification_info=classification_info)
                # -------------------------------------------------------

                self.iface.messageBar().pushMessage(
                    "Success",
                    "Reclassification complete!",
                    level=Qgis.MessageLevel.Success, duration=5)
            else:
                QMessageBox.critical(self.dlg, "Error",
                                     "Could not load the output layer!")

        except Exception as e:
            QMessageBox.critical(self.dlg, "Error",
                                 f"An error occurred during processing:\n{str(e)}")

    # ------------------------------------------------------------------
    # Area analysis workflow
    # ------------------------------------------------------------------
    def _run_area_analysis(self, output_path, classification_info):
        """
        Executes area calculation and (optionally) CSV export steps.
        """
        import traceback

        try:
            self.iface.messageBar().pushMessage(
                "Area Calculation",
                "Calculating class areas...",
                level=Qgis.MessageLevel.Info, duration=3)

            area_results, crs_note = self.area_calculator.calculate_class_areas(
                output_path, classification_info)

            # Show CRS info in message bar
            self.iface.messageBar().pushMessage(
                "CRS Info", crs_note, level=Qgis.MessageLevel.Info, duration=8)

            # CSV export
            if self.dlg.export_csv_check.isChecked():
                csv_path = self.dlg.csv_file_line.text().strip()
                if not csv_path:
                    base = os.path.splitext(output_path)[0]
                    csv_path = base + "_area_analysis.csv"

                include_meta = self.dlg.csv_metadata_check.isChecked()
                success = self.area_calculator.export_to_csv(
                    area_results=area_results,
                    csv_path=csv_path,
                    classification_info=classification_info,
                    raster_path=output_path,
                    include_metadata=include_meta,
                    crs_note=crs_note)

                if success:
                    self.iface.messageBar().pushMessage(
                        "CSV Saved",
                        f"Area analysis saved to '{os.path.basename(csv_path)}'.",
                        level=Qgis.MessageLevel.Success, duration=8)
                else:
                    self.iface.messageBar().pushMessage(
                        "CSV Error", "Could not save CSV file!",
                        level=Qgis.MessageLevel.Warning, duration=5)

            # Results window
            if self.dlg.show_area_results_check.isChecked():
                self._show_area_results_dialog(area_results, classification_info, crs_note)

        except Exception as e:
            # Print full traceback to QGIS Python console for debugging
            traceback.print_exc()
            QMessageBox.critical(
                self.dlg, "Area Calculation Error",
                f"An error occurred during area calculation:\n{str(e)}\n\n"
                f"See the QGIS Python console for the full traceback.")

    def _show_area_results_dialog(self, area_results, classification_info, crs_note=None):
        """Dialog showing area results as a table"""
        from qgis.PyQt.QtGui import QColor, QBrush, QFont

        dlg = QDialog(self.dlg)
        dlg.setWindowTitle(f"Area Analysis — {classification_info.get('name', '')}")
        dlg.resize(860, 520)

        layout = QVBoxLayout()

        # Title
        title = QLabel(
            f"<b>{classification_info.get('name', 'Classification')} — Class Area Analysis</b>")
        title.setStyleSheet("font-size: 13pt; padding: 6px;")
        layout.addWidget(title)

        # CRS info note
        if crs_note:
            note_label = QLabel(f"ℹ️ {crs_note}")
            note_label.setWordWrap(True)
            note_label.setStyleSheet(
                "background:#e8f4fd; border:1px solid #b3d7f0; "
                "border-radius:4px; padding:6px; font-size:9pt;")
            layout.addWidget(note_label)

        # Table — populate first, then enable sorting
        columns = ["Class No", "Label", "Color",
                   "Pixel Count", "Area (m²)", "Area (ha)", "Area (km²)", "Percentage (%)"]

        # Put TOTAL row last
        data_rows  = [r for r in area_results if str(r['class_id']) != 'TOTAL']
        total_rows = [r for r in area_results if str(r['class_id']) == 'TOTAL']
        ordered = data_rows + total_rows

        table = QTableWidget(len(ordered), len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(False)  # Keep OFF while populating

        header = table.horizontalHeader()
        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        bold_font = QFont()
        bold_font.setBold(True)

        for row_idx, row_data in enumerate(ordered):
            is_total = (str(row_data['class_id']) == 'TOTAL')

            def make_item(text, bold=is_total):
                it = QTableWidgetItem(str(text))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if bold:
                    it.setFont(bold_font)
                return it

            table.setItem(row_idx, 0, make_item(row_data['class_id']))
            table.setItem(row_idx, 1, make_item(row_data['label']))

            # Color cell
            color_val = row_data.get('color', '')
            if color_val and color_val.startswith('#'):
                color_item = QTableWidgetItem(color_val)
                color_item.setBackground(QBrush(QColor(color_val)))
                color_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_total:
                    color_item.setFont(bold_font)
                table.setItem(row_idx, 2, color_item)
            else:
                table.setItem(row_idx, 2, make_item(''))

            # Numeric columns
            px = row_data['pixel_count']
            table.setItem(row_idx, 3, make_item(f"{px:,}"))
            table.setItem(row_idx, 4, make_item(f"{row_data['area_m2']:,.2f}"))
            table.setItem(row_idx, 5, make_item(f"{row_data['area_ha']:,.4f}"))
            table.setItem(row_idx, 6, make_item(f"{row_data['area_km2']:,.6f}"))
            table.setItem(row_idx, 7, make_item(f"{row_data['percentage']:.4f}"))

        # Enable sorting after population
        table.setSortingEnabled(True)

        layout.addWidget(table)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save as CSV")
        def _save_csv():
            default = os.path.join(
                os.path.expanduser("~"),
                f"{classification_info.get('name', 'area_analysis')}.csv"
                .replace(' ', '_'))
            path, _ = QFileDialog.getSaveFileName(
                dlg, "Save CSV", default,
                "CSV Files (*.csv);;All Files (*.*)")
            if path:
                if not path.lower().endswith('.csv'):
                    path += '.csv'
                if self.area_calculator.export_to_csv(
                        area_results, path, classification_info,
                        crs_note=crs_note):
                    QMessageBox.information(dlg, "Success",
                                            f"CSV file saved:\n{path}")
                else:
                    QMessageBox.critical(dlg, "Error", "Could not save CSV file!")

        save_btn.clicked.connect(_save_csv)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec()

    # ------------------------------------------------------------------
    def reclassify_raster(self, input_path, output_path, classification_info):
        """Perform reclassification using QGIS processing.

        DATA_TYPE=2 → Int16 (-32768…32767).
        This is required because the nodata value is -9999, which cannot be
        represented in Byte (DATA_TYPE=1, range 0-255). Using Byte caused
        nodata to be silently truncated to 0/255, making all pixels appear
        valid during area calculation and producing incorrect area totals.
        Int16 also supports up to 32 767 classes, future-proofing the plugin.
        """
        ranges = classification_info['ranges']
        table = []
        for i, range_item in enumerate(ranges, start=1):
            min_val = float(range_item['min'])
            max_val = float(range_item['max'])
            table.extend([min_val, max_val, i])

        params = {
            'INPUT_RASTER': input_path,
            'RASTER_BAND':  1,
            'TABLE':        table,
            'NO_DATA':      -9999,
            'RANGE_BOUNDARIES':   2,   # min <= x < max  (last class catches exact max)
            'NODATA_FOR_MISSING': True,
            'DATA_TYPE':    2,         # Int16 — supports -9999 nodata correctly
            'OUTPUT':       output_path
        }
        processing.run("native:reclassifybytable", params)

    # ------------------------------------------------------------------
    def create_custom_classification(self):
        dialog = CustomClassificationDialog(self.dlg)
        if dialog.exec():
            class_data = dialog.get_classification_data()
            class_key = class_data.pop('key')
            if (self.custom_classification_mgr.get_classification(class_key) or
                    self.classification_lib.get_classification(class_key)):
                reply = QMessageBox.question(
                    self.dlg, "Key Already Exists",
                    f"The key '{class_key}' is already in use. Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
            if self.custom_classification_mgr.add_classification(class_key, class_data):
                QMessageBox.information(
                    self.dlg, "Success",
                    f"Classification '{class_data['name']}' created successfully!")
                self.populate_classification_types()
            else:
                QMessageBox.critical(self.dlg, "Error",
                                     "Could not save the classification!")

    def manage_custom_classifications(self):
        """Open the Manage Classifications dialog."""
        dlg = ManageClassificationsDialog(self.custom_classification_mgr, self.dlg)
        dlg.exec()
        # Refresh combo in case the user added/edited/deleted classifications
        self.populate_classification_types()

