# -*- coding: utf-8 -*-
"""
Custom Classification Dialog
Dialog for creating user-defined classifications
"""

from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QLineEdit, QPushButton, QTableWidget,
                                 QTableWidgetItem, QDialogButtonBox, QGroupBox,
                                 QMessageBox, QColorDialog, QDoubleSpinBox,
                                 QHeaderView, QFileDialog, QComboBox, QTextEdit,
                                 QAbstractItemView)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
import json


class CustomClassificationDialog(QDialog):
    """Dialog for creating/editing custom classifications"""

    def __init__(self, parent=None, classification_data=None):
        super(CustomClassificationDialog, self).__init__(parent)
        self.classification_data = classification_data
        self.setupUi()

        if classification_data:
            self.load_classification_data()

    def setupUi(self):
        """Setup the user interface"""
        self.setWindowTitle("User-Defined Classification")
        self.resize(800, 600)

        main_layout = QVBoxLayout()

        # Basic info group
        info_group = QGroupBox("Basic Information")
        info_layout = QVBoxLayout()

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Classification Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Custom NDVI Classification")
        name_layout.addWidget(self.name_edit)
        info_layout.addLayout(name_layout)

        # Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("e.g. custom_ndvi (use lowercase and underscores)")
        key_layout.addWidget(self.key_edit)
        info_layout.addLayout(key_layout)

        # Unit
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit:"))
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g. Index Value, Metres, °C")
        unit_layout.addWidget(self.unit_edit)
        info_layout.addLayout(unit_layout)

        # Description
        desc_label = QLabel("Description:")
        info_layout.addWidget(desc_label)
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Detailed description of the classification...")
        self.description_edit.setMaximumHeight(80)
        info_layout.addWidget(self.description_edit)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Ranges group
        ranges_group = QGroupBox("Class Ranges")
        ranges_layout = QVBoxLayout()

        # Buttons for range management
        range_buttons_layout = QHBoxLayout()
        self.add_range_btn = QPushButton("Add Class")
        self.add_range_btn.clicked.connect(self.add_range)
        range_buttons_layout.addWidget(self.add_range_btn)

        self.remove_range_btn = QPushButton("Remove Selected Class")
        self.remove_range_btn.clicked.connect(self.remove_range)
        range_buttons_layout.addWidget(self.remove_range_btn)

        self.import_btn = QPushButton("Import from JSON")
        self.import_btn.clicked.connect(self.import_from_json)
        range_buttons_layout.addWidget(self.import_btn)

        range_buttons_layout.addStretch()
        ranges_layout.addLayout(range_buttons_layout)

        # Table for ranges
        self.ranges_table = QTableWidget()
        self.ranges_table.setColumnCount(5)
        self.ranges_table.setHorizontalHeaderLabels(
            ["Min Value", "Max Value", "Label", "Color", ""])
        self.ranges_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.ranges_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        ranges_layout.addWidget(self.ranges_table)

        ranges_group.setLayout(ranges_layout)
        main_layout.addWidget(ranges_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def add_range(self, min_val=0.0, max_val=1.0, label="", color="#808080"):
        """Add a range to the table"""
        row = self.ranges_table.rowCount()
        self.ranges_table.insertRow(row)

        # Min value
        min_spin = QDoubleSpinBox()
        min_spin.setRange(-999999, 999999)
        min_spin.setDecimals(4)
        min_spin.setValue(min_val)
        self.ranges_table.setCellWidget(row, 0, min_spin)

        # Max value
        max_spin = QDoubleSpinBox()
        max_spin.setRange(-999999, 999999)
        max_spin.setDecimals(4)
        max_spin.setValue(max_val)
        self.ranges_table.setCellWidget(row, 1, max_spin)

        # Label
        label_edit = QLineEdit(label)
        label_edit.setPlaceholderText("Class label")
        self.ranges_table.setCellWidget(row, 2, label_edit)

        # Color button
        color_btn = QPushButton()
        color_btn.setStyleSheet(f"background-color: {color}")
        color_btn.clicked.connect(lambda: self.choose_color(row))
        color_btn.setProperty('color', color)
        self.ranges_table.setCellWidget(row, 3, color_btn)

        # Delete button
        delete_btn = QPushButton("Remove")
        delete_btn.clicked.connect(lambda: self.delete_range_row(row))
        self.ranges_table.setCellWidget(row, 4, delete_btn)

    def delete_range_row(self, row):
        """Delete a specific row"""
        self.ranges_table.removeRow(row)
        # Update delete button connections
        for i in range(self.ranges_table.rowCount()):
            delete_btn = self.ranges_table.cellWidget(i, 4)
            if delete_btn:
                delete_btn.clicked.disconnect()
                delete_btn.clicked.connect(lambda checked, r=i: self.delete_range_row(r))

    def remove_range(self):
        """Remove selected range"""
        current_row = self.ranges_table.currentRow()
        if current_row >= 0:
            self.ranges_table.removeRow(current_row)

    def choose_color(self, row):
        """Choose color for a range"""
        color_btn = self.ranges_table.cellWidget(row, 3)
        current_color = QColor(color_btn.property('color'))

        color = QColorDialog.getColor(current_color, self, "Choose Color")

        if color.isValid():
            color_name = color.name()
            color_btn.setStyleSheet(f"background-color: {color_name}")
            color_btn.setProperty('color', color_name)

    def validate_and_accept(self):
        """Validate input before accepting"""
        # Check name
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Error", "Classification name cannot be empty!")
            return

        # Check key
        key = self.key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "Key cannot be empty!")
            return

        # Key should be lowercase and use underscores
        if not key.replace('_', '').isalnum() or key != key.lower():
            QMessageBox.warning(self, "Error",
                              "Key must contain only lowercase letters and underscores!\n"
                              "e.g. custom_ndvi, my_classification")
            return

        # Check ranges
        if self.ranges_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "You must add at least one class range!")
            return

        # Validate ranges
        for row in range(self.ranges_table.rowCount()):
            min_spin = self.ranges_table.cellWidget(row, 0)
            max_spin = self.ranges_table.cellWidget(row, 1)
            label_edit = self.ranges_table.cellWidget(row, 2)

            if min_spin.value() > max_spin.value():
                QMessageBox.warning(self, "Error",
                                  f"Row {row + 1}: Min value cannot be greater than max value!")
                return

            if not label_edit.text().strip():
                QMessageBox.warning(self, "Error",
                                  f"Row {row + 1}: Label cannot be empty!")
                return

        self.accept()

    def get_classification_data(self):
        """Get the classification data from dialog"""
        ranges = []

        for row in range(self.ranges_table.rowCount()):
            min_spin = self.ranges_table.cellWidget(row, 0)
            max_spin = self.ranges_table.cellWidget(row, 1)
            label_edit = self.ranges_table.cellWidget(row, 2)
            color_btn = self.ranges_table.cellWidget(row, 3)

            ranges.append({
                'min': min_spin.value(),
                'max': max_spin.value(),
                'label': label_edit.text().strip(),
                'color': color_btn.property('color')
            })

        return {
            'key': self.key_edit.text().strip(),
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'unit': self.unit_edit.text().strip(),
            'ranges': ranges
        }

    def load_classification_data(self):
        """Load existing classification data"""
        if not self.classification_data:
            return

        self.name_edit.setText(self.classification_data.get('name', ''))
        self.key_edit.setText(self.classification_data.get('key', ''))
        self.key_edit.setEnabled(False)  # Don't allow changing key when editing
        self.unit_edit.setText(self.classification_data.get('unit', ''))
        self.description_edit.setPlainText(self.classification_data.get('description', ''))

        # Load ranges
        for range_item in self.classification_data.get('ranges', []):
            self.add_range(
                min_val=range_item.get('min', 0.0),
                max_val=range_item.get('max', 1.0),
                label=range_item.get('label', ''),
                color=range_item.get('color', '#808080')
            )

    def import_from_json(self):
        """Import classification from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JSON File",
            "",
            "JSON Files (*.json);;All Files (*.*)")

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Try to extract classification data
            if isinstance(data, dict):
                # If it's a single classification
                if 'ranges' in data:
                    classification = data
                # If it's wrapped with a key
                else:
                    # Get first item
                    key = list(data.keys())[0]
                    classification = data[key]

                # Load data
                self.name_edit.setText(classification.get('name', ''))
                self.unit_edit.setText(classification.get('unit', ''))
                self.description_edit.setPlainText(classification.get('description', ''))

                # Clear existing ranges
                self.ranges_table.setRowCount(0)

                # Load ranges
                for range_item in classification.get('ranges', []):
                    self.add_range(
                        min_val=range_item.get('min', 0.0),
                        max_val=range_item.get('max', 1.0),
                        label=range_item.get('label', ''),
                        color=range_item.get('color', '#808080')
                    )

                QMessageBox.information(self, "Success", "Classification imported successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read JSON file:\n{str(e)}")
