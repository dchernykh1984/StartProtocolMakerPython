"""PySide6 main window for Start Protocol Maker."""

from __future__ import annotations

import re
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    auto_shift_time,
    build_competitor_line,
    check_duplicate_fields,
    current_local_seconds,
    get_next_number,
    get_time_from_seconds,
    load_backup,
    parse_competitor_line,
    save_backup,
    write_start_protocol,
)

_BACKUP_PATH = "data/spm_backup.txt"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Start Protocol Maker")
        self._start_protocol_file: str = ""
        self._regexp_from: str = ""
        self._regexp_to: str = ""
        self._ftp_address: str = ""
        self._setup_ui()
        self._load_backup(_BACKUP_PATH)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # ---- LEFT PANEL: open (database) list ----
        left = QVBoxLayout()
        row = QHBoxLayout()
        self._btn_open_list = QPushButton("Open List")
        self._btn_open_list.clicked.connect(self._on_open_list)
        row.addWidget(self._btn_open_list)
        self._btn_search = QPushButton("Find")
        self._btn_search.clicked.connect(self._on_search_open)
        row.addWidget(self._btn_search)
        self._edit_search = QLineEdit()
        self._edit_search.setPlaceholderText("Search...")
        self._edit_search.returnPressed.connect(self._on_search_open)
        row.addWidget(self._edit_search)
        left.addLayout(row)

        self._list_open = QListWidget()
        self._list_open.setMinimumWidth(350)
        self._list_open.itemDoubleClicked.connect(self._on_edit_open)
        left.addWidget(self._list_open)

        row2 = QHBoxLayout()
        self._btn_edit_open = QPushButton("Edit ->")
        self._btn_edit_open.clicked.connect(self._on_edit_open)
        row2.addWidget(self._btn_edit_open)
        self._btn_to_protocol = QPushButton("Add ->")
        self._btn_to_protocol.clicked.connect(self._on_open_to_protocol)
        row2.addWidget(self._btn_to_protocol)
        self._btn_all_to_protocol = QPushButton("All ->")
        self._btn_all_to_protocol.clicked.connect(self._on_all_to_protocol)
        row2.addWidget(self._btn_all_to_protocol)
        self._btn_add_into_team = QPushButton("Join Team")
        self._btn_add_into_team.clicked.connect(self._on_add_into_team)
        row2.addWidget(self._btn_add_into_team)
        left.addLayout(row2)

        root.addLayout(left)

        # ---- CENTRE PANEL: entry form ----
        centre = QVBoxLayout()

        def _lbl_edit(label: str, default: str = "") -> tuple[QLabel, QLineEdit]:
            lbl = QLabel(label)
            edit = QLineEdit(default)
            return lbl, edit

        lbl, self._edit_number = _lbl_edit("Number:")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_number)

        lbl, self._edit_name = _lbl_edit("Name:")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_name)

        centre.addWidget(QLabel("Group:"))
        self._combo_group = QComboBox()
        self._combo_group.setEditable(False)
        centre.addWidget(self._combo_group)

        lbl, self._edit_yob = _lbl_edit("Year of birth:")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_yob)

        lbl, self._edit_team = _lbl_edit("Team:")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_team)

        lbl, self._edit_city = _lbl_edit("City:")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_city)

        lbl, self._edit_comment = _lbl_edit("Comment:")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_comment)

        lbl, self._edit_time_shift = _lbl_edit("Time shift:", "0 00:00:00.000")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_time_shift)

        self._chk_stage = QCheckBox("Stage number:")
        self._edit_stage = QLineEdit("1")
        self._edit_stage.setReadOnly(True)
        self._chk_stage.toggled.connect(lambda v: self._edit_stage.setReadOnly(not v))
        centre.addWidget(self._chk_stage)
        centre.addWidget(self._edit_stage)

        self._btn_save = QPushButton("Add to protocol")
        self._btn_save.setFixedHeight(36)
        self._btn_save.clicked.connect(self._on_save_to_file)
        centre.addWidget(self._btn_save)

        self._btn_get_number = QPushButton("Get number")
        self._btn_get_number.clicked.connect(self._on_get_number)
        centre.addWidget(self._btn_get_number)

        lbl, self._edit_first_number = _lbl_edit("First number:")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_first_number)

        lbl, self._edit_delay = _lbl_edit("Delay per number (sec):")
        centre.addWidget(lbl)
        centre.addWidget(self._edit_delay)

        self._chk_auto_shift = QCheckBox("AutoShift")
        centre.addWidget(self._chk_auto_shift)

        self._btn_auto_shift = QPushButton("Calc time shift")
        self._btn_auto_shift.clicked.connect(self._on_auto_shift)
        centre.addWidget(self._btn_auto_shift)

        self._btn_clear_shift = QPushButton("Clear shift (0)")
        self._btn_clear_shift.clicked.connect(
            lambda: self._edit_time_shift.setText(get_time_from_seconds(0))
        )
        centre.addWidget(self._btn_clear_shift)

        self._btn_current_time = QPushButton("Current time")
        self._btn_current_time.clicked.connect(self._on_current_time)
        centre.addWidget(self._btn_current_time)

        self._btn_parse_new = QPushButton("Parse new competitor")
        self._btn_parse_new.clicked.connect(self._on_parse_new_competitor)
        centre.addWidget(self._btn_parse_new)

        row_regexp = QHBoxLayout()
        self._btn_regexp_from = QPushButton("RegExp From")
        self._btn_regexp_from.clicked.connect(self._on_set_regexp_from)
        row_regexp.addWidget(self._btn_regexp_from)
        self._btn_regexp_to = QPushButton("RegExp To")
        self._btn_regexp_to.clicked.connect(self._on_set_regexp_to)
        row_regexp.addWidget(self._btn_regexp_to)
        centre.addLayout(row_regexp)

        centre.addStretch()
        root.addLayout(centre)

        # ---- RIGHT PANEL: groups + save-as list ----
        right = QVBoxLayout()

        # groups
        right.addWidget(QLabel("Groups (name#laps):"))
        self._list_groups = QListWidget()
        self._list_groups.setMaximumHeight(120)
        right.addWidget(self._list_groups)

        row3 = QHBoxLayout()
        self._edit_add_group = QLineEdit()
        self._edit_add_group.setPlaceholderText("Group name")
        row3.addWidget(self._edit_add_group)
        lbl_laps = QLabel("Laps:")
        row3.addWidget(lbl_laps)
        self._edit_add_laps = QLineEdit()
        self._edit_add_laps.setPlaceholderText("N")
        self._edit_add_laps.setFixedWidth(40)
        row3.addWidget(self._edit_add_laps)
        self._edit_numbers_range = QLineEdit()
        self._edit_numbers_range.setPlaceholderText("1-100")
        row3.addWidget(self._edit_numbers_range)
        self._btn_add_group = QPushButton("Add group")
        self._btn_add_group.clicked.connect(self._on_add_group)
        row3.addWidget(self._btn_add_group)
        self._btn_remove_group = QPushButton("Remove")
        self._btn_remove_group.clicked.connect(self._on_remove_group)
        row3.addWidget(self._btn_remove_group)
        right.addLayout(row3)
        self._chk_use_all = QCheckBox("Use all numbers")
        right.addWidget(self._chk_use_all)

        # save-as list
        row4 = QHBoxLayout()
        self._btn_search_save_as = QPushButton("Find")
        self._btn_search_save_as.clicked.connect(self._on_search_save_as)
        row4.addWidget(self._btn_search_save_as)
        self._edit_search_save_as = QLineEdit()
        self._edit_search_save_as.setPlaceholderText("Search in protocol...")
        self._edit_search_save_as.returnPressed.connect(self._on_search_save_as)
        row4.addWidget(self._edit_search_save_as)
        right.addLayout(row4)

        self._list_save_as = QListWidget()
        self._list_save_as.setMinimumWidth(350)
        self._list_save_as.itemDoubleClicked.connect(self._on_edit_save_as)
        right.addWidget(self._list_save_as)

        self._lbl_error = QLabel("DUPLICATE ID DETECTED!")
        self._lbl_error.setStyleSheet("color: red; font-weight: bold;")
        self._lbl_error.setVisible(False)
        right.addWidget(self._lbl_error)

        row5 = QHBoxLayout()
        self._btn_edit_save_as = QPushButton("Edit")
        self._btn_edit_save_as.clicked.connect(self._on_edit_save_as)
        row5.addWidget(self._btn_edit_save_as)
        self._btn_delete = QPushButton("Delete")
        self._btn_delete.clicked.connect(self._on_delete)
        row5.addWidget(self._btn_delete)
        self._btn_check_doubles = QPushButton("Check IDs")
        self._btn_check_doubles.clicked.connect(self._on_check_doubles)
        row5.addWidget(self._btn_check_doubles)
        self._btn_check_names = QPushButton("Check names")
        self._btn_check_names.clicked.connect(self._on_check_names)
        row5.addWidget(self._btn_check_names)
        right.addLayout(row5)

        row6 = QHBoxLayout()
        self._btn_save_start = QPushButton("Save start protocol")
        self._btn_save_start.clicked.connect(self._on_save_start)
        row6.addWidget(self._btn_save_start)
        self._btn_save_as_start = QPushButton("Save as...")
        self._btn_save_as_start.clicked.connect(self._on_save_as_start)
        row6.addWidget(self._btn_save_as_start)
        right.addLayout(row6)

        row7 = QHBoxLayout()
        self._btn_backup = QPushButton("Backup")
        self._btn_backup.clicked.connect(self._on_backup)
        row7.addWidget(self._btn_backup)
        self._btn_load_backup = QPushButton("Load backup")
        self._btn_load_backup.clicked.connect(self._on_load_backup)
        row7.addWidget(self._btn_load_backup)
        self._btn_save_cfg = QPushButton("Save config")
        self._btn_save_cfg.clicked.connect(self._on_save_config)
        row7.addWidget(self._btn_save_cfg)
        right.addLayout(row7)

        root.addLayout(right)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _open_items(self) -> list[str]:
        return [self._list_open.item(i).text() for i in range(self._list_open.count())]

    def _save_as_items(self) -> list[str]:
        return [
            self._list_save_as.item(i).text() for i in range(self._list_save_as.count())
        ]

    def _groups(self) -> list[str]:
        return [
            self._list_groups.item(i).text() for i in range(self._list_groups.count())
        ]

    def _numbers(self) -> list[str]:
        # numbers list is parallel to groups; stored as data role
        result = []
        for i in range(self._list_groups.count()):
            item = self._list_groups.item(i)
            result.append(item.data(Qt.ItemDataRole.UserRole) or "")
        return result

    def _refresh_duplicate_indicator(self) -> None:
        found, idx = check_duplicate_fields(self._save_as_items(), 0, False)
        self._lbl_error.setVisible(found)
        if found and idx >= 0:
            self._list_save_as.setCurrentRow(idx)

    def _save_all_data(self) -> None:
        self._refresh_duplicate_indicator()
        self._write_backup("data", "spm_backup.txt")
        if self._start_protocol_file:
            try:
                write_start_protocol(self._start_protocol_file, self._save_as_items())
            except FileNotFoundError:
                QMessageBox.warning(
                    self,
                    "Save",
                    f'Cannot save: directory for "{self._start_protocol_file}"'
                    ' does not exist.\nUse "Save as" to choose a new location.',
                )

    def _write_backup(self, folder: str, filename: str) -> None:
        save_backup(
            path=f"{folder}/{filename}",
            open_items=self._open_items(),
            save_items=self._save_as_items(),
            groups=self._groups(),
            numbers=self._numbers(),
            regexp_from=self._regexp_from,
            regexp_to=self._regexp_to,
            ftp_address=self._ftp_address,
            start_protocol_file=self._start_protocol_file,
            use_all_numbers=self._chk_use_all.isChecked(),
            auto_shift=self._chk_auto_shift.isChecked(),
        )

    def _parse_and_fill_form(self, line: str) -> None:
        d = parse_competitor_line(line)
        self._edit_number.setText(d["number"])
        self._edit_name.setText(d["name"])
        group_with_laps = d["group"] + "#" + d["laps"] if d["laps"] else d["group"]
        idx = self._combo_group.findText(group_with_laps)
        if idx == -1:
            self._list_groups.addItem(group_with_laps)
            item = self._list_groups.item(self._list_groups.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, "1-10000")
            self._combo_group.addItem(group_with_laps)
            idx = self._combo_group.count() - 1
        self._combo_group.setCurrentIndex(idx)
        self._edit_yob.setText(d["year_of_birth"])
        self._edit_team.setText(d["team"])
        self._edit_city.setText(d["city"])
        self._edit_comment.setText(d["comment"])
        if self._chk_auto_shift.isChecked():
            self._on_get_number()
            self._on_auto_shift()
        else:
            self._edit_time_shift.setText(d["time_shift"] or "0 00:00:00.000")
        self._edit_stage.setText(d["stage"] or "1")

    def _load_backup(self, path: str) -> None:
        data = load_backup(path)
        self._list_open.clear()
        self._list_open.addItems(data["open_items"])
        self._list_save_as.clear()
        self._list_save_as.addItems(data["save_items"])
        self._list_groups.clear()
        self._combo_group.clear()
        for grp, num in zip(data["groups"], data["numbers"], strict=False):
            self._list_groups.addItem(grp)
            item = self._list_groups.item(self._list_groups.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, num)
            self._combo_group.addItem(grp)
        self._regexp_from = data["regexp_from"]
        self._regexp_to = data["regexp_to"]
        self._ftp_address = data["ftp_address"]
        self._start_protocol_file = data["start_protocol_file"]
        self._chk_use_all.setChecked(data["use_all_numbers"])
        self._chk_auto_shift.setChecked(data["auto_shift"])
        self._refresh_duplicate_indicator()

    # ------------------------------------------------------------------
    # slots
    # ------------------------------------------------------------------

    def _on_open_list(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open competitors list")
        if not path:
            return
        p = Path(path)
        for enc in ("utf-8", "cp1251", "latin-1"):
            try:
                lines = [
                    ln for ln in p.read_text(encoding=enc).splitlines() if ln.strip()
                ]
                break
            except UnicodeDecodeError:
                continue
        else:
            lines = []
        self._list_open.clear()
        self._list_open.addItems(lines)
        self._btn_search.setText(f"Find ({len(lines)})")

    def _on_search_open(self) -> None:
        term = self._edit_search.text().lower()
        if not term:
            return
        count = self._list_open.count()
        if count == 0:
            QMessageBox.information(self, "Search", "No matches found.")
            return
        start = self._list_open.currentRow() + 1
        for offset in range(count):
            idx = (start + offset) % count
            item = self._list_open.item(idx)
            if item and term in item.text().lower():
                self._list_open.setCurrentRow(idx)
                return
        QMessageBox.information(self, "Search", "No matches found.")

    def _on_search_save_as(self) -> None:
        term = self._edit_search_save_as.text().lower()
        if not term:
            return
        count = self._list_save_as.count()
        if count == 0:
            QMessageBox.information(self, "Search", "No matches found.")
            return
        start = self._list_save_as.currentRow() + 1
        for offset in range(count):
            idx = (start + offset) % count
            item = self._list_save_as.item(idx)
            if item and term in item.text().lower():
                self._list_save_as.setCurrentRow(idx)
                return
        QMessageBox.information(self, "Search", "No matches found.")

    def _on_edit_open(self) -> None:
        if self._list_open.currentItem():
            self._parse_and_fill_form(self._list_open.currentItem().text())

    def _on_open_to_protocol(self) -> None:
        if self._list_open.currentItem():
            self._list_save_as.addItem(self._list_open.currentItem().text())
            self._refresh_duplicate_indicator()

    def _on_all_to_protocol(self) -> None:
        reply = QMessageBox.question(self, "Warning", "Are you sure?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        for i in range(self._list_open.count()):
            self._list_save_as.addItem(self._list_open.item(i).text())
        self._refresh_duplicate_indicator()

    def _on_add_group(self) -> None:
        name = self._edit_add_group.text().strip()
        laps = self._edit_add_laps.text().strip()
        numbers_range = self._edit_numbers_range.text().strip()
        if not name or not laps:
            return
        group_text = f"{name}#{laps}"
        self._list_groups.addItem(group_text)
        item = self._list_groups.item(self._list_groups.count() - 1)
        item.setData(Qt.ItemDataRole.UserRole, numbers_range)
        self._combo_group.addItem(group_text)
        self._edit_add_group.clear()
        self._edit_add_laps.clear()

    def _on_remove_group(self) -> None:
        row = self._list_groups.currentRow()
        if row < 0:
            return
        grp = self._list_groups.item(row).text()
        self._list_groups.takeItem(row)
        idx = self._combo_group.findText(grp)
        if idx >= 0:
            self._combo_group.removeItem(idx)

    def _on_save_to_file(self) -> None:
        number = self._edit_number.text().strip()
        name = self._edit_name.text().strip()
        group_text = self._combo_group.currentText().strip()
        if not number or not name or not group_text:
            return
        line = build_competitor_line(
            number=number,
            name=name,
            group_with_laps=group_text,
            stage=self._edit_stage.text().strip() or "1",
            year_of_birth=self._edit_yob.text().strip(),
            team=self._edit_team.text().strip(),
            city=self._edit_city.text().strip(),
            comment=self._edit_comment.text().strip(),
            time_shift=self._edit_time_shift.text().strip() or "0 00:00:00.000",
        )
        self._list_save_as.addItem(line)
        self._edit_name.clear()
        self._edit_number.clear()
        self._save_all_data()

    def _on_get_number(self) -> None:
        idx = self._list_groups.findItems(
            self._combo_group.currentText(), Qt.MatchFlag.MatchExactly
        )
        group_index = self._list_groups.row(idx[0]) if idx else -1
        result = get_next_number(
            group_index=group_index,
            open_items=self._open_items(),
            save_as_items=self._save_as_items(),
            numbers_items=self._numbers(),
            use_all_numbers=self._chk_use_all.isChecked(),
        )
        if result is None:
            QMessageBox.information(self, "Get number", "No free numbers.")
        else:
            self._edit_number.setText(result)

    def _on_auto_shift(self) -> None:
        if self._chk_auto_shift.isChecked():
            idx = self._list_groups.findItems(
                self._combo_group.currentText(), Qt.MatchFlag.MatchExactly
            )
            if not idx:
                QMessageBox.information(self, "AutoShift", "Please select a group.")
                return
            row = self._list_groups.row(idx[0])
            numbers_str = self._numbers()[row] if row < len(self._numbers()) else ""
            parts = numbers_str.split("#")
            first_n = parts[1] if len(parts) > 1 else ""
            delay = parts[2] if len(parts) > 2 else ""
            self._edit_first_number.setText(first_n)
            self._edit_delay.setText(delay)
        result = auto_shift_time(
            self._edit_number.text(),
            self._edit_first_number.text(),
            self._edit_delay.text(),
        )
        if result is not None:
            self._edit_time_shift.setText(result)

    def _on_current_time(self) -> None:
        self._edit_time_shift.setText(get_time_from_seconds(current_local_seconds()))

    def _text_area_dialog(self, title: str, initial_text: str = "") -> tuple[bool, str]:
        """Modal dialog with a multi-line text area. Returns (accepted, text)."""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(560, 360)
        layout = QVBoxLayout(dlg)
        text_edit = QTextEdit()
        text_edit.setPlainText(initial_text)
        layout.addWidget(text_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        accepted = dlg.exec() == QDialog.DialogCode.Accepted
        return accepted, text_edit.toPlainText()

    def _on_parse_new_competitor(self) -> None:
        accepted, text = self._text_area_dialog("Registration Form")
        if not accepted or not text.strip():
            return
        line = text.strip()
        if self._regexp_from:
            try:
                line = re.sub(self._regexp_from, self._regexp_to, line)
            except re.error:
                pass
        self._parse_and_fill_form(line)
        if self._chk_auto_shift.isChecked():
            self._on_get_number()

    def _on_set_regexp_from(self) -> None:
        accepted, text = self._text_area_dialog('"RegExp From" Form', self._regexp_from)
        if accepted:
            self._regexp_from = text

    def _on_set_regexp_to(self) -> None:
        accepted, text = self._text_area_dialog('"RegExp To" Form', self._regexp_to)
        if accepted:
            self._regexp_to = text

    def _on_edit_save_as(self) -> None:
        if self._list_save_as.currentItem():
            self._parse_and_fill_form(self._list_save_as.currentItem().text())
        self._save_all_data()

    def _on_delete(self) -> None:
        row = self._list_save_as.currentRow()
        if row >= 0:
            self._list_save_as.takeItem(row)
        self._save_all_data()

    def _on_check_doubles(self) -> None:
        self._refresh_duplicate_indicator()

    def _on_check_names(self) -> None:
        found, idx = check_duplicate_fields(self._save_as_items(), 1, False)
        self._lbl_error.setVisible(found)
        if found and idx >= 0:
            self._list_save_as.setCurrentRow(idx)

    def _on_save_start(self) -> None:
        if not self._start_protocol_file:
            QMessageBox.warning(
                self, "Save", 'File with start protocol not selected. Click "Save as"'
            )
            return
        try:
            write_start_protocol(self._start_protocol_file, self._save_as_items())
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "Save",
                f'Cannot save: directory for "{self._start_protocol_file}"'
                ' does not exist.\nUse "Save as" to choose a new location.',
            )

    def _on_save_as_start(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save start protocol")
        if path:
            self._start_protocol_file = path
            self._on_save_start()

    def _on_backup(self) -> None:
        ts = int(time.time())
        self._write_backup("temp", f"spm{ts}.txt")

    def _on_load_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load backup")
        if path:
            self._regexp_from = ""
            self._regexp_to = ""
            self._load_backup(path)

    def _on_save_config(self) -> None:
        self._write_backup("data", "spm_backup.txt")

    def _on_add_into_team(self) -> None:
        if not self._list_open.currentItem():
            return
        saved_name = self._edit_name.text()
        saved_yob = self._edit_yob.text()
        saved_city = self._edit_city.text()
        saved_team = self._edit_team.text()
        self._parse_and_fill_form(self._list_open.currentItem().text())
        self._edit_name.setText(saved_name + " / " + self._edit_name.text())
        self._edit_yob.setText(saved_yob + " / " + self._edit_yob.text())
        if self._edit_team.text() != saved_team:
            if not self._edit_team.text():
                self._edit_team.setText(saved_team)
            elif saved_team:
                self._edit_team.setText(saved_team + " / " + self._edit_team.text())
        if self._edit_city.text() != saved_city:
            self._edit_city.setText(saved_city + " / " + self._edit_city.text())

    # ------------------------------------------------------------------
    # close event
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        reply = QMessageBox.question(self, "Warning", "Are you sure to exit?")
        if reply == QMessageBox.StandardButton.Yes:
            self._write_backup("data", "spm_backup.txt")
            event.accept()
        else:
            event.ignore()
