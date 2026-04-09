from PyQt5.QtCore import QThread, pyqtSignal


class SpeechWorker(QThread):
    listening_started = pyqtSignal(int, int)
    processing_started = pyqtSignal(int, int)
    transcription_ready = pyqtSignal(int, int, dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, speech_service, row, col, language_name, engine_name):
        super().__init__()
        self.speech_service = speech_service
        self.row = row
        self.col = col
        self.language_name = language_name
        self.engine_name = engine_name

    def run(self):
        self.listening_started.emit(self.row, self.col)
        try:
            result = self.speech_service.listen_and_transcribe(
                self.language_name,
                self.engine_name,
            )
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            return

        self.processing_started.emit(self.row, self.col)
        self.transcription_ready.emit(self.row, self.col, result)
