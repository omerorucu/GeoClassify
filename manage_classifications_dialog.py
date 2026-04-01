# -*- coding: utf-8 -*-
"""
Manage Classifications Dialog
Dialog for viewing, editing, deleting, importing and exporting
user-defined classifications.
"""

from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QPushButton, QListWidget, QListWidgetItem,
                                 QMessageBox, QFileDialog)
from qgis.PyQt.QtCore import Qt


class ManageClassificationsDialog(QDialog):
    """
    Standalone dialog for managing user-defined classifications.

    Extracted from the inline nested-function implementation in
    GeoClassify.manage_custom_classifications() for improved
    readability, testability and maintainability.
    """

    def __init__(self, custom_mgr, parent=None):
        """
        Parameters
        ----------
        custom_mgr : CustomClassificationManager
            The manager instance used to read/write custom classifications.
        parent : QWidget, optional
        """
        super().__init__(parent)
        self._mgr = custom_mgr
        self.setWindowTitle("Manage User-Defined Classifications")
        self.resize(600, 400)
        self._setup_ui()
        self._populate_list()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("User-Defined Classifications:"))

        self._list = QListWidget()
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.clicked.connect(self._edit_classification)
        btn_layout.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.clicked.connect(self._delete_classification)
        btn_layout.addWidget(self._delete_btn)

        self._export_btn = QPushButton("Export")
        self._export_btn.clicked.connect(self._export_classification)
        btn_layout.addWidget(self._export_btn)

        self._import_btn = QPushButton("Import")
        self._import_btn.clicked.connect(self._import_classification)
        btn_layout.addWidget(self._import_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # List helpers
    # ------------------------------------------------------------------
    def _populate_list(self):
        """(Re)populate the list widget from the manager."""
        self._list.clear()
        for key, classification in self._mgr.get_all_classifications().items():
            item = QListWidgetItem(f"{classification['name']} ({key})")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._list.addItem(item)

    def _selected_key(self):
        """Return the key of the currently selected item, or None."""
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _require_selection(self):
        """Show a warning and return False if nothing is selected."""
        if self._selected_key() is None:
            QMessageBox.warning(self, "Warning", "Please select a classification!")
            return False
        return True

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _edit_classification(self):
        if not self._require_selection():
            return

        # Import here to avoid circular imports at module level
        from .custom_classification_dialog import CustomClassificationDialog

        key = self._selected_key()
        classification = self._mgr.get_classification(key)
        if not classification:
            return

        # Pass a copy with the key included so the dialog can pre-fill it
        classification['key'] = key
        edit_dialog = CustomClassificationDialog(self, classification)

        if edit_dialog.exec():
            class_data = edit_dialog.get_classification_data()
            class_key = class_data.pop('key')
            if self._mgr.add_classification(class_key, class_data):
                QMessageBox.information(self, "Success", "Classification updated!")
                self._populate_list()
            else:
                QMessageBox.critical(self, "Error", "Could not save the classification!")

    def _delete_classification(self):
        if not self._require_selection():
            return

        key = self._selected_key()
        classification = self._mgr.get_classification(key)
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete '{classification['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self._mgr.remove_classification(key):
                self._populate_list()
                QMessageBox.information(self, "Success", "Classification deleted!")
            else:
                QMessageBox.critical(self, "Error", "Could not delete the classification!")

    def _export_classification(self):
        if not self._require_selection():
            return

        key = self._selected_key()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save JSON File", f"{key}.json",
            "JSON Files (*.json);;All Files (*.*)")

        if file_path:
            if self._mgr.export_classification(key, file_path):
                QMessageBox.information(
                    self, "Success", f"Classification exported to '{file_path}'!")
            else:
                QMessageBox.critical(self, "Error", "Could not export classification!")

    def _import_classification(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select JSON File", "",
            "JSON Files (*.json);;All Files (*.*)")

        if file_path:
            if self._mgr.import_classification(file_path):
                self._populate_list()
                QMessageBox.information(self, "Success", "Classification imported!")
            else:
                QMessageBox.critical(
                    self, "Error", "Could not import classification!")
