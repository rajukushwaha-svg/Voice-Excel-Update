from pathlib import Path

import pandas as pd
from PyQt5.QtCore import QItemSelectionModel, QModelIndex, Qt
from PyQt5.QtGui import QColor, QKeySequence, QPalette
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QShortcut,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from services.file_service import FileService
from services.speech_service import SpeechService
from ui.table_model import DataFrameTableModel
from workers.speech_worker import SpeechWorker


class VoiceExcelWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Excel Pro")
        self.resize(1200, 760)

        self.file_path = None
        self.cached_dataframe = pd.DataFrame()
        self.model = DataFrameTableModel(self.cached_dataframe)
        self.speech_service = SpeechService()
        self.speech_worker = None
        self.selected_index = QModelIndex()

        self._build_ui()
        self._apply_dark_palette()
        self._wire_shortcuts()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)

        controls = QHBoxLayout()
        root_layout.addLayout(controls)

        self.open_button = QPushButton("Open File")
        self.open_button.clicked.connect(self.open_file)
        controls.addWidget(self.open_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_file)
        self.save_button.setEnabled(False)
        controls.addWidget(self.save_button)

        self.listen_button = QPushButton("Start Listening")
        self.listen_button.clicked.connect(self.start_listening_for_selected_cell)
        self.listen_button.setEnabled(False)
        controls.addWidget(self.listen_button)

        self.auto_listen_checkbox = QCheckBox("Auto listen on cell click")
        self.auto_listen_checkbox.setChecked(True)
        controls.addWidget(self.auto_listen_checkbox)

        self.auto_save_checkbox = QCheckBox("Auto save")
        controls.addWidget(self.auto_save_checkbox)

        controls.addWidget(QLabel("Language"))
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItems(["English", "Hindi"])
        self.language_dropdown.currentTextChanged.connect(self.refresh_engine_options)
        controls.addWidget(self.language_dropdown)

        controls.addWidget(QLabel("Engine"))
        self.engine_dropdown = QComboBox()
        controls.addWidget(self.engine_dropdown)

        self.file_label = QLabel("No file loaded")
        self.file_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        controls.addWidget(self.file_label, stretch=1)

        info_row = QHBoxLayout()
        root_layout.addLayout(info_row)

        self.selected_cell_label = QLabel("Selected Cell: -")
        info_row.addWidget(self.selected_cell_label)

        self.engine_label = QLabel("Engine: -")
        info_row.addWidget(self.engine_label)

        self.confidence_label = QLabel("Confidence: -")
        info_row.addWidget(self.confidence_label)

        self.status_label = QLabel("Load a CSV or XLSX file to begin.")
        info_row.addWidget(self.status_label, stretch=1)

        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectItems)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_view.horizontalHeader().setStretchLastSection(False)
        self.table_view.clicked.connect(self.handle_cell_clicked)
        self.table_view.setStyleSheet(
            "QTableView::item:selected { background-color: #f59e0b; color: #111827; }"
        )
        root_layout.addWidget(self.table_view)

        status_bar = QStatusBar()
        status_bar.showMessage("Ready")
        self.setStatusBar(status_bar)

        self.refresh_engine_options()

    def _apply_dark_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#111827"))
        palette.setColor(QPalette.WindowText, QColor("#f9fafb"))
        palette.setColor(QPalette.Base, QColor("#1f2937"))
        palette.setColor(QPalette.AlternateBase, QColor("#111827"))
        palette.setColor(QPalette.ToolTipBase, QColor("#f9fafb"))
        palette.setColor(QPalette.ToolTipText, QColor("#111827"))
        palette.setColor(QPalette.Text, QColor("#f9fafb"))
        palette.setColor(QPalette.Button, QColor("#1f2937"))
        palette.setColor(QPalette.ButtonText, QColor("#f9fafb"))
        palette.setColor(QPalette.Highlight, QColor("#f59e0b"))
        palette.setColor(QPalette.HighlightedText, QColor("#111827"))
        self.setPalette(palette)

    def _wire_shortcuts(self):
        self.listen_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.listen_shortcut.activated.connect(self.start_listening_for_selected_cell)

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_file)

    def refresh_engine_options(self):
        current_language = self.language_dropdown.currentText()
        available = ["Auto"] + self.speech_service.available_engines(current_language)

        current_value = self.engine_dropdown.currentText()
        self.engine_dropdown.blockSignals(True)
        self.engine_dropdown.clear()
        self.engine_dropdown.addItems(available)
        if current_value in available:
            self.engine_dropdown.setCurrentText(current_value)
        self.engine_dropdown.blockSignals(False)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Spreadsheet",
            "",
            "Spreadsheet Files (*.csv *.xlsx)",
        )

        if not file_path:
            return

        try:
            self.cached_dataframe = FileService.load_file(file_path)
        except Exception as exc:
            self.show_error(f"Could not load file:\n{exc}")
            return

        self.file_path = file_path
        self.model.set_dataframe(self.cached_dataframe)
        self.file_label.setText(Path(file_path).name)
        self.save_button.setEnabled(True)
        self.listen_button.setEnabled(True)
        self.selected_index = QModelIndex()
        self.selected_cell_label.setText("Selected Cell: -")
        self.confidence_label.setText("Confidence: -")
        self.update_status("File loaded. Select a cell to start voice updates.")
        self.table_view.resizeColumnsToContents()

    def handle_cell_clicked(self, index):
        if not index.isValid():
            return

        self.selected_index = index
        self.table_view.selectionModel().setCurrentIndex(
            index,
            QItemSelectionModel.ClearAndSelect,
        )
        self.selected_cell_label.setText(
            f"Selected Cell: Row {index.row() + 1}, Column {index.column() + 1}"
        )
        self.statusBar().showMessage("Cell selected")

        if self.auto_listen_checkbox.isChecked():
            self.start_listening_for_selected_cell()

    def start_listening_for_selected_cell(self):
        if self.speech_worker and self.speech_worker.isRunning():
            self.update_status("A listening task is already running.")
            return

        if not self.selected_index.isValid():
            self.show_error("Select a cell before starting voice input.")
            return

        if self.model.dataframe.empty:
            self.show_error("Load a file before starting voice input.")
            return

        language_name = self.language_dropdown.currentText()
        engine_name = self.engine_dropdown.currentText() or "Auto"
        row = self.selected_index.row()
        col = self.selected_index.column()

        self.speech_worker = SpeechWorker(
            self.speech_service,
            row,
            col,
            language_name,
            engine_name,
        )
        self.speech_worker.listening_started.connect(self.on_listening_started)
        self.speech_worker.processing_started.connect(self.on_processing_started)
        self.speech_worker.transcription_ready.connect(self.apply_transcription)
        self.speech_worker.error_occurred.connect(self.on_worker_error)
        self.speech_worker.finished.connect(self.on_worker_finished)
        self.listen_button.setEnabled(False)
        self.speech_worker.start()

    def on_listening_started(self, row, col):
        self.selected_cell_label.setText(f"Selected Cell: Row {row + 1}, Column {col + 1}")
        self.confidence_label.setText("Confidence: -")
        self.update_status("Listening...")

    def on_processing_started(self, row, col):
        self.selected_cell_label.setText(f"Selected Cell: Row {row + 1}, Column {col + 1}")
        self.update_status("Processing...")

    def apply_transcription(self, row, col, result):
        text = result.get("text", "")
        confidence = result.get("confidence")
        engine = result.get("engine", "Unknown")

        self.model.update_cell(row, col, text)
        self.selected_index = self.model.index(row, col)
        self.table_view.selectionModel().setCurrentIndex(
            self.selected_index,
            QItemSelectionModel.ClearAndSelect,
        )
        self.engine_label.setText(f"Engine: {engine}")
        if confidence is None:
            self.confidence_label.setText("Confidence: n/a")
        else:
            self.confidence_label.setText(f"Confidence: {confidence:.2f}")

        self.update_status("Updated")
        self.statusBar().showMessage(f"Updated R{row + 1} C{col + 1}")

        if self.auto_save_checkbox.isChecked():
            self.save_file(show_success=False)

    def on_worker_error(self, message):
        self.update_status(message)
        self.show_error(message)

    def on_worker_finished(self):
        self.listen_button.setEnabled(True)
        self.speech_worker = None

    def save_file(self, show_success=True):
        if self.model.dataframe.empty or not self.file_path:
            self.show_error("Load a file before saving.")
            return

        try:
            FileService.save_file(self.model.dataframe, self.file_path)
        except Exception as exc:
            self.show_error(f"Could not save file:\n{exc}")
            return

        if show_success:
            self.update_status(f"Saved changes to {Path(self.file_path).name}.")
        self.statusBar().showMessage("Saved")

    def update_status(self, message):
        self.status_label.setText(message)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
