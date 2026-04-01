# -*- coding: utf-8 -*-
"""
Classification Preview and Edit Dialog
Dialog for previewing and editing a classification before processing
"""

from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QPushButton, QTableWidget, QTableWidgetItem,
                                 QDialogButtonBox, QGroupBox, QMessageBox,
                                 QDoubleSpinBox, QLineEdit, QHeaderView,
                                 QCheckBox, QColorDialog, QTextEdit,
                                 QAbstractItemView)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
import copy


class ClassificationPreviewDialog(QDialog):
    """Dialog for previewing and editing classification before processing"""

    def __init__(self, classification_info, parent=None):
        super(ClassificationPreviewDialog, self).__init__(parent)
        self.original_classification = classification_info
        self.classification_info = copy.deepcopy(classification_info)
        self.setupUi()
        self.load_classification()

    def setupUi(self):
        """Setup the user interface"""
        self.setWindowTitle("Classification Preview and Edit")
        self.resize(900, 700)

        main_layout = QVBoxLayout()

        # Info section
        info_group = QGroupBox("Classification Information")
        info_layout = QVBoxLayout()

        # Name (read-only)
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Classification:"))
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        name_layout.addWidget(self.name_label)
        name_layout.addStretch()
        info_layout.addLayout(name_layout)

        # Description
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(60)
        info_layout.addWidget(self.description_text)

        # Unit
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit:"))
        self.unit_label = QLabel()
        unit_layout.addWidget(self.unit_label)
        unit_layout.addStretch()
        info_layout.addLayout(unit_layout)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Tip message
        self.warning_label = QLabel(
            "💡 <b>Tip:</b> You can customize the classification by editing the values in the table. "
            "Changes will only apply to this operation."
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("background-color: #FFF3CD; padding: 10px; border-radius: 5px;")
        main_layout.addWidget(self.warning_label)

        # Ranges table
        ranges_group = QGroupBox("Class Ranges")
        ranges_layout = QVBoxLayout()

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.add_class_btn = QPushButton("➕ Add Class")
        self.add_class_btn.clicked.connect(self.add_class)
        toolbar_layout.addWidget(self.add_class_btn)

        self.delete_class_btn = QPushButton("🗑️ Delete Selected Class")
        self.delete_class_btn.clicked.connect(self.delete_class)
        toolbar_layout.addWidget(self.delete_class_btn)

        toolbar_layout.addStretch()

        self.reset_btn = QPushButton("↺ Reset to Default")
        self.reset_btn.setToolTip("Undo all changes and return to original values")
        self.reset_btn.clicked.connect(self.reset_to_original)
        toolbar_layout.addWidget(self.reset_btn)

        ranges_layout.addLayout(toolbar_layout)

        # Table
        self.ranges_table = QTableWidget()
        self.ranges_table.setColumnCount(6)
        self.ranges_table.setHorizontalHeaderLabels(
            ["Order", "Min Value", "Max Value", "Label", "Color", ""])

        # Set column widths
        header = self.ranges_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Order
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)        # Min
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)        # Max
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)            # Label
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)   # Color
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)   # Delete

        self.ranges_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ranges_table.setAlternatingRowColors(True)

        ranges_layout.addWidget(self.ranges_table)

        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-style: italic;")
        ranges_layout.addWidget(self.stats_label)

        ranges_group.setLayout(ranges_layout)
        main_layout.addWidget(ranges_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.save_as_custom_check = QCheckBox(
            "Save these changes as a user-defined classification")
        self.save_as_custom_check.setToolTip(
            "If checked, the edited classification will be saved permanently and available for future use")
        options_layout.addWidget(self.save_as_custom_check)

        save_name_layout = QHBoxLayout()
        save_name_layout.addWidget(QLabel("Save Name:"))
        self.save_name_edit = QLineEdit()
        self.save_name_edit.setPlaceholderText("e.g. NDVI Customized")
        self.save_name_edit.setEnabled(False)
        save_name_layout.addWidget(self.save_name_edit)
        options_layout.addLayout(save_name_layout)

        self.save_as_custom_check.stateChanged.connect(
            lambda state: self.save_name_edit.setEnabled(state == Qt.CheckState.Checked))

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Continue")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def load_classification(self):
        """Load classification data into the dialog"""
        self.name_label.setText(self.classification_info['name'])
        self.description_text.setPlainText(self.classification_info['description'])
        self.unit_label.setText(self.classification_info['unit'])

        # Set default save name
        self.save_name_edit.setText(f"{self.classification_info['name']} (Customized)")

        # Load ranges
        self.load_ranges()

    def load_ranges(self):
        """Load ranges into table"""
        self.ranges_table.setRowCount(0)

        for i, range_item in enumerate(self.classification_info['ranges'], start=1):
            self.add_range_row(
                order=i,
                min_val=range_item['min'],
                max_val=range_item['max'],
                label=range_item['label'],
                color=range_item['color']
            )

        self.update_statistics()

    def add_range_row(self, order=1, min_val=0.0, max_val=1.0, label="", color="#808080"):
        """Add a range row to the table"""
        row = self.ranges_table.rowCount()
        self.ranges_table.insertRow(row)

        # Order (read-only)
        order_item = QTableWidgetItem(str(order))
        order_item.setFlags(order_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ranges_table.setItem(row, 0, order_item)

        # Min value
        min_spin = QDoubleSpinBox()
        min_spin.setRange(-999999, 999999)
        min_spin.setDecimals(4)
        min_spin.setValue(float(min_val))
        self.ranges_table.setCellWidget(row, 1, min_spin)

        # Max value
        max_spin = QDoubleSpinBox()
        max_spin.setRange(-999999, 999999)
        max_spin.setDecimals(4)
        max_spin.setValue(float(max_val))
        self.ranges_table.setCellWidget(row, 2, max_spin)

        # Label
        label_edit = QLineEdit(label)
        label_edit.setPlaceholderText("Class label")
        self.ranges_table.setCellWidget(row, 3, label_edit)

        # Color button
        color_btn = QPushButton()
        color_btn.setFixedSize(60, 28)
        color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #999;")
        color_btn.setProperty('color', color)
        color_btn.clicked.connect(lambda checked, r=row: self.choose_color(r))
        self.ranges_table.setCellWidget(row, 4, color_btn)

        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(40, 30)
        delete_btn.clicked.connect(lambda: self.delete_row(row))
        self.ranges_table.setCellWidget(row, 5, delete_btn)

    def add_class(self):
        """Add a new class"""
        # Get last max value to suggest as new min
        last_max = 1.0
        if self.ranges_table.rowCount() > 0:
            last_row = self.ranges_table.rowCount() - 1
            last_max_spin = self.ranges_table.cellWidget(last_row, 2)
            if last_max_spin:
                last_max = last_max_spin.value()

        # Add new row
        order = self.ranges_table.rowCount() + 1
        self.add_range_row(
            order=order,
            min_val=last_max,
            max_val=last_max + 1.0,
            label=f"Class {order}",
            color="#808080"
        )

        self.update_statistics()

    def delete_class(self):
        """Delete selected class"""
        current_row = self.ranges_table.currentRow()
        if current_row >= 0:
            self.delete_row(current_row)

    def delete_row(self, row):
        """Delete a specific row and renumber"""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete class {row + 1}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ranges_table.removeRow(row)
            # Renumber rows
            for i in range(self.ranges_table.rowCount()):
                order_item = self.ranges_table.item(i, 0)
                if order_item:
                    order_item.setText(str(i + 1))

            self.update_statistics()

    def choose_color(self, row):
        """Choose color for a range"""
        color_btn = self.ranges_table.cellWidget(row, 4)
        current_color = QColor(color_btn.property('color'))

        color = QColorDialog.getColor(current_color, self, "Choose Color")

        if color.isValid():
            color_name = color.name()
            color_btn.setStyleSheet(f"background-color: {color_name}; border: 1px solid #999;")
            color_btn.setProperty('color', color_name)

    def reset_to_original(self):
        """Reset all values to original"""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "All changes will be reverted to the original values. Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.classification_info = copy.deepcopy(self.original_classification)
            self.load_ranges()
            QMessageBox.information(self, "Success", "Classification has been reset to its original state.")

    def update_statistics(self):
        """Update statistics label"""
        total_classes = self.ranges_table.rowCount()

        if total_classes > 0:
            first_min = self.ranges_table.cellWidget(0, 1)
            last_max = self.ranges_table.cellWidget(total_classes - 1, 2)

            if first_min and last_max:
                overall_min = first_min.value()
                overall_max = last_max.value()

                self.stats_label.setText(
                    f"Total {total_classes} classes | "
                    f"Range: {overall_min:.4f} – {overall_max:.4f} | "
                    f"Span: {overall_max - overall_min:.4f}"
                )
        else:
            self.stats_label.setText("No classes defined")

    def validate_and_accept(self):
        """Validate and accept changes"""
        # Check if there are any classes
        if self.ranges_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "You must define at least one class!")
            return

        # Validate each range
        for row in range(self.ranges_table.rowCount()):
            min_spin = self.ranges_table.cellWidget(row, 1)
            max_spin = self.ranges_table.cellWidget(row, 2)
            label_edit = self.ranges_table.cellWidget(row, 3)

            if min_spin.value() >= max_spin.value():
                QMessageBox.warning(
                    self, "Error",
                    f"Class {row + 1}: Min value ({min_spin.value()}) must be less than "
                    f"max value ({max_spin.value()})!"
                )
                return

            if not label_edit.text().strip():
                QMessageBox.warning(self, "Error", f"Class {row + 1}: Label cannot be empty!")
                return

        # Check for gaps warning
        gaps_found = False
        for row in range(self.ranges_table.rowCount() - 1):
            current_max = self.ranges_table.cellWidget(row, 2).value()
            next_min = self.ranges_table.cellWidget(row + 1, 1).value()

            if abs(current_max - next_min) > 0.0001:
                gaps_found = True
                break

        if gaps_found:
            reply = QMessageBox.question(
                self,
                "Warning",
                "There are gaps between class ranges. Values in these gaps will not be classified.\n\n"
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Check for overlaps
        for row in range(self.ranges_table.rowCount() - 1):
            current_max = self.ranges_table.cellWidget(row, 2).value()
            next_min = self.ranges_table.cellWidget(row + 1, 1).value()

            if current_max > next_min:
                QMessageBox.warning(
                    self, "Error",
                    f"Overlap detected between Class {row + 1} and Class {row + 2}!\n"
                    f"Class {row + 1} max ({current_max}) > Class {row + 2} min ({next_min})"
                )
                return

        # If save as custom is checked, validate name
        if self.save_as_custom_check.isChecked():
            if not self.save_name_edit.text().strip():
                QMessageBox.warning(self, "Error", "Save name cannot be empty!")
                return

        self.accept()

    def get_classification_data(self):
        """Get the edited classification data"""
        ranges = []

        for row in range(self.ranges_table.rowCount()):
            min_spin = self.ranges_table.cellWidget(row, 1)
            max_spin = self.ranges_table.cellWidget(row, 2)
            label_edit = self.ranges_table.cellWidget(row, 3)
            color_btn = self.ranges_table.cellWidget(row, 4)

            ranges.append({
                'min': min_spin.value(),
                'max': max_spin.value(),
                'label': label_edit.text().strip(),
                'color': color_btn.property('color')
            })

        result = {
            'name': self.classification_info['name'],
            'description': self.classification_info['description'],
            'unit': self.classification_info['unit'],
            'ranges': ranges
        }

        return result

    def should_save_as_custom(self):
        """Check if user wants to save as custom classification"""
        return self.save_as_custom_check.isChecked()

    def get_custom_name(self):
        """Get the custom classification name"""
        return self.save_name_edit.text().strip()
