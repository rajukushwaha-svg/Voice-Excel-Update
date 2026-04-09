import os
import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import VoiceExcelWindow


def configure_qt_platform():
    if os.name != "posix":
        return

    if os.environ.get("QT_QPA_PLATFORM"):
        return

    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "wayland"


def main():
    configure_qt_platform()
    app = QApplication(sys.argv)
    window = VoiceExcelWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
