# -*- coding: utf-8 -*-
"""
Dialog UI for GeoClassify Plugin
"""

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                                 QLabel, QLineEdit, QPushButton,
                                 QComboBox, QDialogButtonBox, QGroupBox,
                                 QTextEdit, QCheckBox, QMessageBox)
from qgis.PyQt.QtCore import Qt
import os


class GeoClassifyDialog(QDialog):
    """Dialog for GeoClassify Plugin"""

    def __init__(self, parent=None):
        super(GeoClassifyDialog, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        """Setup the user interface"""
        self.setWindowTitle("GeoClassify")
        self.resize(620, 600)

        # Main layout
        main_layout = QVBoxLayout()

        # Input section
        input_group = QGroupBox("Input Data")
        input_layout = QVBoxLayout()

        # Layer selection
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel("Select Layer:"))
        self.layer_combo = QComboBox()
        layer_layout.addWidget(self.layer_combo)
        input_layout.addLayout(layer_layout)

        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("File:"))
        self.input_file_line = QLineEdit()
        self.input_file_line.setEnabled(True)   # Active initially since "Select from File" is the first option
        self.input_file_line.setPlaceholderText("Select a raster file or choose a layer above...")
        file_layout.addWidget(self.input_file_line)
        self.input_file_button = QPushButton("Browse...")
        self.input_file_button.setEnabled(True)
        file_layout.addWidget(self.input_file_button)
        input_layout.addLayout(file_layout)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # Classification section
        class_group = QGroupBox("Classification Type")
        class_layout = QVBoxLayout()

        class_select_layout = QHBoxLayout()
        class_select_layout.addWidget(QLabel("Classification:"))
        self.classification_combo = QComboBox()
        class_select_layout.addWidget(self.classification_combo)
        class_layout.addLayout(class_select_layout)

        # Custom classification buttons
        custom_buttons_layout = QHBoxLayout()
        self.create_custom_btn = QPushButton("➕ Create New Classification")
        self.create_custom_btn.setToolTip("Create a user-defined classification")
        custom_buttons_layout.addWidget(self.create_custom_btn)

        self.manage_custom_btn = QPushButton("⚙️ Manage Classifications")
        self.manage_custom_btn.setToolTip("Edit or delete user-defined classifications")
        custom_buttons_layout.addWidget(self.manage_custom_btn)
        class_layout.addLayout(custom_buttons_layout)

        # Description text
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)
        class_layout.addWidget(QLabel("Description:"))
        class_layout.addWidget(self.description_text)

        class_group.setLayout(class_layout)
        main_layout.addWidget(class_group)

        # Batch processing button
        self.batch_btn = QPushButton("🗂  Batch Reclassification...")
        self.batch_btn.setToolTip(
            "Reclassify multiple raster files using the selected classification")
        self.batch_btn.setStyleSheet(
            "QPushButton { background-color: #1976D2; color: white; "
            "font-weight: bold; padding: 6px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #1565C0; }")
        main_layout.addWidget(self.batch_btn)
        output_group = QGroupBox("Output Data")
        output_layout = QVBoxLayout()

        output_file_layout = QHBoxLayout()
        output_file_layout.addWidget(QLabel("Output File:"))
        self.output_file_line = QLineEdit()
        output_file_layout.addWidget(self.output_file_line)
        self.output_file_button = QPushButton("Browse...")
        output_file_layout.addWidget(self.output_file_button)
        output_layout.addLayout(output_file_layout)

        # Add to canvas checkbox
        self.add_to_canvas_check = QCheckBox("Add to Map")
        self.add_to_canvas_check.setChecked(True)
        output_layout.addWidget(self.add_to_canvas_check)

        # Apply style checkbox
        self.apply_style_check = QCheckBox("Apply Style Automatically")
        self.apply_style_check.setChecked(True)
        output_layout.addWidget(self.apply_style_check)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # ---------------------------------------------------------------
        # Area Calculation & CSV Export section
        # ---------------------------------------------------------------
        area_group = QGroupBox("Area Calculation and CSV Export")
        area_layout = QVBoxLayout()

        # Area calculation checkbox
        self.calculate_area_check = QCheckBox(
            "Calculate the area of each class after reclassification")
        self.calculate_area_check.setChecked(False)
        self.calculate_area_check.setToolTip(
            "Calculates pixel count, area in m², ha, and km² for each class")
        area_layout.addWidget(self.calculate_area_check)

        # CSV export checkbox
        self.export_csv_check = QCheckBox("Save area results to a CSV file")
        self.export_csv_check.setChecked(False)
        self.export_csv_check.setEnabled(False)  # Enabled when area calculation is selected
        area_layout.addWidget(self.export_csv_check)

        # CSV file selector
        csv_file_layout = QHBoxLayout()
        csv_file_layout.addWidget(QLabel("CSV File:"))
        self.csv_file_line = QLineEdit()
        self.csv_file_line.setPlaceholderText(
            "Leave empty to save in the same folder as the raster")
        self.csv_file_line.setEnabled(False)
        csv_file_layout.addWidget(self.csv_file_line)
        self.csv_file_button = QPushButton("Browse...")
        self.csv_file_button.setEnabled(False)
        csv_file_layout.addWidget(self.csv_file_button)
        area_layout.addLayout(csv_file_layout)

        # Include metadata checkbox
        self.csv_metadata_check = QCheckBox(
            "Include classification metadata in CSV")
        self.csv_metadata_check.setChecked(True)
        self.csv_metadata_check.setEnabled(False)
        area_layout.addWidget(self.csv_metadata_check)

        # Show area results checkbox
        self.show_area_results_check = QCheckBox(
            "Show area results in the results window")
        self.show_area_results_check.setChecked(True)
        self.show_area_results_check.setEnabled(False)
        area_layout.addWidget(self.show_area_results_check)

        area_group.setLayout(area_layout)
        main_layout.addWidget(area_group)

        # Signal connections: enable related controls when area calculation is activated
        self.calculate_area_check.stateChanged.connect(self._on_area_check_changed)
        self.export_csv_check.stateChanged.connect(self._on_csv_check_changed)
        # ---------------------------------------------------------------

        # Button box
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self._on_ok_clicked)
        self.buttonBox.rejected.connect(self.reject)
        main_layout.addWidget(self.buttonBox)

        self.setLayout(main_layout)

    # ------------------------------------------------------------------
    # Validation — keeps dialog open on error
    # ------------------------------------------------------------------
    def _on_ok_clicked(self):
        """Validate required fields; keep dialog open if anything is missing."""
        if not self.output_file_line.text().strip():
            QMessageBox.warning(
                self,
                "Missing Output File",
                "Please specify an output file location before continuing.")
            self.output_file_line.setFocus()
            return          # dialog stays open
        self.accept()       # all good — close with Accepted

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------
    def _on_area_check_changed(self, state):
        """Enable/disable related controls when area calculation checkbox changes"""
        enabled = (state == Qt.CheckState.Checked)
        self.export_csv_check.setEnabled(enabled)
        self.show_area_results_check.setEnabled(enabled)
        if not enabled:
            self.export_csv_check.setChecked(False)

    def _on_csv_check_changed(self, state):
        """Enable/disable file controls when CSV export checkbox changes"""
        enabled = (state == Qt.CheckState.Checked)
        self.csv_file_line.setEnabled(enabled)
        self.csv_file_button.setEnabled(enabled)
        self.csv_metadata_check.setEnabled(enabled)
