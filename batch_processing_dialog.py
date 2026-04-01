# -*- coding: utf-8 -*-
"""
Batch Processing Dialog
Reclassifies multiple raster files using a selected classification.
"""

import os
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QPushButton, QListWidget, QListWidgetItem,
                                 QFileDialog, QGroupBox, QCheckBox, QLineEdit,
                                 QProgressBar, QTextEdit, QMessageBox,
                                 QDialogButtonBox, QAbstractItemView,
                                 QSplitter, QWidget)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QColor


# ---------------------------------------------------------------------------
# Worker thread — keeps the UI responsive during long batch runs
# ---------------------------------------------------------------------------
class BatchWorker(QThread):
    """Runs reclassification jobs in a background thread."""

    progress     = pyqtSignal(int)          # 0-100
    file_started = pyqtSignal(str)          # current filename
    file_done    = pyqtSignal(str, bool)    # filename, success
    log_message  = pyqtSignal(str)          # text for the log panel
    finished     = pyqtSignal(int, int)     # done_count, fail_count

    def __init__(self, jobs, classification_info, options, parent=None):
        """
        Parameters
        ----------
        jobs : list[dict]  — each dict has keys 'input' and 'output'
        classification_info : dict
        options : dict     — apply_style, calculate_area, export_csv,
                             include_metadata, add_to_canvas
        """
        super().__init__(parent)
        self.jobs               = jobs
        self.classification_info = classification_info
        self.options            = options
        self._cancelled         = False

    def cancel(self):
        self._cancelled = True

    # ------------------------------------------------------------------
    def run(self):
        import processing
        from qgis.core import QgsRasterLayer, QgsProject
        from .area_calculator import AreaCalculator
        from .style_manager import StyleManager

        area_calc    = AreaCalculator()
        style_mgr    = StyleManager()
        total        = len(self.jobs)
        done         = 0
        fail         = 0

        ranges = self.classification_info['ranges']
        table  = []
        for i, r in enumerate(ranges, start=1):
            table.extend([float(r['min']), float(r['max']), i])

        for idx, job in enumerate(self.jobs):
            if self._cancelled:
                self.log_message.emit("⛔ Batch cancelled by user.")
                break

            input_path  = job['input']
            output_path = job['output']
            fname       = os.path.basename(input_path)

            self.file_started.emit(fname)
            self.log_message.emit(f"▶ Processing: {fname}")

            try:
                params = {
                    'INPUT_RASTER':      input_path,
                    'RASTER_BAND':       1,
                    'TABLE':             table,
                    'NO_DATA':           -9999,
                    'RANGE_BOUNDARIES':  2,
                    'NODATA_FOR_MISSING':True,
                    'DATA_TYPE':         2,
                    'OUTPUT':            output_path,
                }
                processing.run("native:reclassifybytable", params)

                # Optional: add to canvas
                if self.options.get('add_to_canvas'):
                    layer_name = os.path.splitext(os.path.basename(output_path))[0]
                    out_layer  = QgsRasterLayer(output_path, layer_name)
                    if out_layer.isValid():
                        QgsProject.instance().addMapLayer(out_layer)
                        if self.options.get('apply_style'):
                            style_mgr.apply_style(out_layer, self.classification_info)

                # Optional: area calculation + CSV
                if self.options.get('calculate_area'):
                    area_results, crs_note = area_calc.calculate_class_areas(
                        output_path, self.classification_info)

                    if self.options.get('export_csv'):
                        csv_path = os.path.splitext(output_path)[0] + '_area_analysis.csv'
                        area_calc.export_to_csv(
                            area_results, csv_path, self.classification_info,
                            raster_path=output_path,
                            include_metadata=self.options.get('include_metadata', True),
                            crs_note=crs_note)
                        self.log_message.emit(f"   📊 CSV saved: {os.path.basename(csv_path)}")

                self.log_message.emit(f"   ✅ Done → {os.path.basename(output_path)}")
                self.file_done.emit(fname, True)
                done += 1

            except Exception as e:
                self.log_message.emit(f"   ❌ Error: {str(e)}")
                self.file_done.emit(fname, False)
                fail += 1

            self.progress.emit(int((idx + 1) / total * 100))

        self.finished.emit(done, fail)


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
class BatchProcessingDialog(QDialog):
    """Dialog for batch reclassification of multiple raster files."""

    def __init__(self, classification_info, parent=None):
        super().__init__(parent)
        self.classification_info = classification_info
        self._worker             = None
        self.setWindowTitle("Batch Reclassification")
        self.resize(780, 620)
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout()

        # ── Classification info banner ──────────────────────────────────
        info_label = QLabel(
            f"<b>Classification:</b> {self.classification_info.get('name', '—')}  "
            f"&nbsp;&nbsp;<b>Classes:</b> {len(self.classification_info.get('ranges', []))}")
        info_label.setStyleSheet(
            "background:#e8f4fd; border:1px solid #b3d7f0; "
            "border-radius:4px; padding:6px;")
        main_layout.addWidget(info_label)

        # ── Input files ────────────────────────────────────────────────
        input_group  = QGroupBox("Input Raster Files")
        input_layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        add_files_btn = QPushButton("➕ Add Files...")
        add_files_btn.clicked.connect(self._add_files)
        btn_row.addWidget(add_files_btn)

        add_folder_btn = QPushButton("📂 Add Folder...")
        add_folder_btn.clicked.connect(self._add_folder)
        btn_row.addWidget(add_folder_btn)

        remove_btn = QPushButton("✖ Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(remove_btn)

        clear_btn = QPushButton("🗑 Clear All")
        clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        input_layout.addLayout(btn_row)

        self._file_list = QListWidget()
        self._file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self._file_list.setMinimumHeight(150)
        input_layout.addWidget(self._file_list)

        self._file_count_label = QLabel("0 file(s) selected")
        self._file_count_label.setStyleSheet("color:#666; font-style:italic;")
        input_layout.addWidget(self._file_count_label)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # ── Output folder ──────────────────────────────────────────────
        output_group  = QGroupBox("Output Folder")
        output_layout = QVBoxLayout()

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Output Folder:"))
        self._output_dir_line = QLineEdit()
        self._output_dir_line.setPlaceholderText(
            "Leave empty to save next to each input file")
        out_row.addWidget(self._output_dir_line)
        browse_out_btn = QPushButton("Browse...")
        browse_out_btn.clicked.connect(self._browse_output_dir)
        out_row.addWidget(browse_out_btn)
        output_layout.addLayout(out_row)

        suffix_row = QHBoxLayout()
        suffix_row.addWidget(QLabel("Output Suffix:"))
        self._suffix_line = QLineEdit("_reclassified")
        self._suffix_line.setToolTip(
            "Appended to each input filename, e.g. input_reclassified.tif")
        suffix_row.addWidget(self._suffix_line)
        suffix_row.addStretch()
        output_layout.addLayout(suffix_row)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # ── Options ────────────────────────────────────────────────────
        opt_group  = QGroupBox("Options")
        opt_layout = QHBoxLayout()

        self._add_to_canvas_chk = QCheckBox("Add layers to map")
        self._add_to_canvas_chk.setChecked(False)
        opt_layout.addWidget(self._add_to_canvas_chk)

        self._apply_style_chk = QCheckBox("Apply style automatically")
        self._apply_style_chk.setChecked(True)
        opt_layout.addWidget(self._apply_style_chk)

        self._calc_area_chk = QCheckBox("Calculate class areas")
        self._calc_area_chk.setChecked(False)
        opt_layout.addWidget(self._calc_area_chk)

        self._export_csv_chk = QCheckBox("Export area CSV")
        self._export_csv_chk.setChecked(False)
        self._export_csv_chk.setEnabled(False)
        opt_layout.addWidget(self._export_csv_chk)

        self._metadata_chk = QCheckBox("Include metadata in CSV")
        self._metadata_chk.setChecked(True)
        self._metadata_chk.setEnabled(False)
        opt_layout.addWidget(self._metadata_chk)

        opt_layout.addStretch()
        opt_group.setLayout(opt_layout)
        main_layout.addWidget(opt_group)

        self._calc_area_chk.stateChanged.connect(self._on_area_chk_changed)
        self._export_csv_chk.stateChanged.connect(self._on_csv_chk_changed)

        # ── Progress ───────────────────────────────────────────────────
        prog_group  = QGroupBox("Progress")
        prog_layout = QVBoxLayout()

        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        prog_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready.")
        prog_layout.addWidget(self._status_label)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(120)
        self._log_text.setStyleSheet("font-family: monospace; font-size: 9pt;")
        prog_layout.addWidget(self._log_text)

        prog_group.setLayout(prog_layout)
        main_layout.addWidget(prog_group)

        # ── Buttons ────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()

        self._run_btn = QPushButton("▶  Run Batch")
        self._run_btn.setStyleSheet(
            "background-color:#2196F3; color:white; "
            "font-weight:bold; padding:6px 18px;")
        self._run_btn.clicked.connect(self._run_batch)
        btn_layout.addWidget(self._run_btn)

        self._cancel_btn = QPushButton("⛔ Cancel")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_batch)
        btn_layout.addWidget(self._cancel_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------
    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Raster Files", "",
            "Raster Files (*.tif *.tiff *.img *.asc);;All Files (*.*)")
        self._append_files(files)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing Raster Files")
        if not folder:
            return
        exts = ('.tif', '.tiff', '.img', '.asc')
        files = [
            os.path.join(folder, f)
            for f in sorted(os.listdir(folder))
            if f.lower().endswith(exts)
        ]
        if not files:
            QMessageBox.information(
                self, "No Files Found",
                "No raster files (.tif, .tiff, .img, .asc) found in the selected folder.")
            return
        self._append_files(files)

    def _append_files(self, paths):
        existing = {self._file_list.item(i).data(Qt.ItemDataRole.UserRole)
                    for i in range(self._file_list.count())}
        added = 0
        for p in paths:
            if p not in existing:
                item = QListWidgetItem(os.path.basename(p))
                item.setData(Qt.ItemDataRole.UserRole, p)
                item.setToolTip(p)
                self._file_list.addItem(item)
                added += 1
        self._update_count()

    def _remove_selected(self):
        for item in self._file_list.selectedItems():
            self._file_list.takeItem(self._file_list.row(item))
        self._update_count()

    def _clear_files(self):
        self._file_list.clear()
        self._update_count()

    def _update_count(self):
        n = self._file_list.count()
        self._file_count_label.setText(f"{n} file(s) selected")

    def _browse_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_dir_line.setText(folder)

    # ------------------------------------------------------------------
    # Option signals
    # ------------------------------------------------------------------
    def _on_area_chk_changed(self, state):
        enabled = (state == Qt.CheckState.Checked)
        self._export_csv_chk.setEnabled(enabled)
        if not enabled:
            self._export_csv_chk.setChecked(False)

    def _on_csv_chk_changed(self, state):
        self._metadata_chk.setEnabled(state == Qt.CheckState.Checked)

    # ------------------------------------------------------------------
    # Batch run
    # ------------------------------------------------------------------
    def _build_jobs(self):
        suffix     = self._suffix_line.text().strip() or '_reclassified'
        output_dir = self._output_dir_line.text().strip()
        jobs = []
        for i in range(self._file_list.count()):
            input_path = self._file_list.item(i).data(Qt.ItemDataRole.UserRole)
            base_name  = os.path.splitext(os.path.basename(input_path))[0]
            out_name   = base_name + suffix + '.tif'
            if output_dir:
                out_path = os.path.join(output_dir, out_name)
            else:
                out_path = os.path.join(os.path.dirname(input_path), out_name)
            jobs.append({'input': input_path, 'output': out_path})
        return jobs

    def _run_batch(self):
        if self._file_list.count() == 0:
            QMessageBox.warning(self, "No Files",
                                "Please add at least one raster file.")
            return

        jobs = self._build_jobs()

        options = {
            'add_to_canvas':    self._add_to_canvas_chk.isChecked(),
            'apply_style':      self._apply_style_chk.isChecked(),
            'calculate_area':   self._calc_area_chk.isChecked(),
            'export_csv':       self._export_csv_chk.isChecked(),
            'include_metadata': self._metadata_chk.isChecked(),
        }

        self._log_text.clear()
        self._progress_bar.setValue(0)
        self._status_label.setText("Running…")
        self._run_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)

        self._worker = BatchWorker(jobs, self.classification_info, options, self)
        self._worker.progress.connect(self._progress_bar.setValue)
        self._worker.file_started.connect(
            lambda f: self._status_label.setText(f"Processing: {f}"))
        self._worker.log_message.connect(self._append_log)
        self._worker.finished.connect(self._on_batch_finished)
        self._worker.start()

    def _cancel_batch(self):
        if self._worker:
            self._worker.cancel()
        self._cancel_btn.setEnabled(False)
        self._status_label.setText("Cancelling…")

    def _on_batch_finished(self, done, fail):
        self._run_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        total = done + fail
        msg   = f"Batch complete: {done}/{total} succeeded, {fail} failed."
        self._status_label.setText(msg)
        self._append_log(f"\n{'✅' if fail == 0 else '⚠️'} {msg}")
        self._progress_bar.setValue(100)
        if fail > 0:
            QMessageBox.warning(self, "Batch Finished with Errors", msg)
        else:
            QMessageBox.information(self, "Batch Complete", msg)

    def _append_log(self, text):
        self._log_text.append(text)
        self._log_text.verticalScrollBar().setValue(
            self._log_text.verticalScrollBar().maximum())

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self, "Batch Running",
                "A batch job is running. Cancel it and close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._worker.cancel()
                self._worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
