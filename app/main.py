"""Entry point for Start Protocol Maker."""

import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1100, 650)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
