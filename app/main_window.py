"""PySide6 main window for Start Protocol Maker."""

from __future__ import annotations

import ftplib
import re
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
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

from app.http_io import fetch_participants, upload_start_list
from app.models import (
    DEFAULT_NUMBER_RANGE,
    auto_shift_time,
    build_competitor_line,
    categories_to_group_rows,
    check_duplicate_fields,
    current_local_seconds,
    get_next_number,
    get_time_from_seconds,
    load_backup,
    parse_competitor_line,
    participant_to_open_line,
    save_backup,
    write_start_protocol,
)
from app.paths import app_path

_BACKUP_FOLDER = "data"
_BACKUP_FILENAME = "spm_backup.txt"
# Edits arrive in bursts (a name, then a bib, then a shift); waiting out a short
# idle window collapses them into a single upload instead of one call per click.
_AUTO_SEND_DELAY_MS = 2000


def _participant_merge_key(line: str) -> tuple[str, str, str]:
    """Return (last_name_lower, first_name_lower, birth_year) for dedup."""
    parts = line.split("#")
    name = parts[1] if len(parts) > 1 else ""
    name_split = name.split(" ", 1)
    last_name = name_split[0].lower()
    first_name = name_split[1].lower() if len(name_split) > 1 else ""
    year = parts[5] if len(parts) > 5 else ""
    return (last_name, first_name, year)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Start Protocol Maker")
        self.setWindowIcon(QIcon(str(Path(__file__).parent / "app.ico")))
        self._start_protocol_file: str = ""
        self._regexp_from: str = ""
        self._regexp_to: str = ""
        self._client_revision: int = 0
        self._auto_send_pending: bool = False
        self._auto_send_suspended: bool = False
        self._auto_send_timer = QTimer(self)
        self._auto_send_timer.setSingleShot(True)
        self._auto_send_timer.setInterval(_AUTO_SEND_DELAY_MS)
        self._auto_send_timer.timeout.connect(self._on_auto_send_timeout)
        self._setup_ui()
        self._load_backup(str(app_path(_BACKUP_FOLDER, _BACKUP_FILENAME)))

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
        self._btn_check_mail = QPushButton("Check mail")
        self._btn_check_mail.clicked.connect(self._on_check_mail)
        row5.addWidget(self._btn_check_mail)
        right.addLayout(row5)

        row6 = QHBoxLayout()
        self._btn_save_start = QPushButton("Save start protocol")
        self._btn_save_start.clicked.connect(self._on_save_start)
        row6.addWidget(self._btn_save_start)
        self._btn_save_as_start = QPushButton("Save as...")
        self._btn_save_as_start.clicked.connect(self._on_save_as_start)
        row6.addWidget(self._btn_save_as_start)
        right.addLayout(row6)

        row_ftp = QHBoxLayout()
        row_ftp.addWidget(QLabel("FTP:"))
        self._edit_ftp_address = QLineEdit()
        self._edit_ftp_address.setPlaceholderText("ftp://host/path/#login#password")
        row_ftp.addWidget(self._edit_ftp_address)
        self._btn_upload = QPushButton("Upload")
        self._btn_upload.clicked.connect(self._on_upload)
        row_ftp.addWidget(self._btn_upload)
        right.addLayout(row_ftp)

        row_http_url = QHBoxLayout()
        row_http_url.addWidget(QLabel("Site URL:"))
        self._edit_http_site_url = QLineEdit()
        self._edit_http_site_url.setPlaceholderText("https://your-site.com")
        row_http_url.addWidget(self._edit_http_site_url)
        right.addLayout(row_http_url)

        row_http_token = QHBoxLayout()
        row_http_token.addWidget(QLabel("Token:"))
        self._edit_http_token = QLineEdit()
        self._edit_http_token.setPlaceholderText("upload token UUID")
        row_http_token.addWidget(self._edit_http_token)
        right.addLayout(row_http_token)

        row_device = QHBoxLayout()
        row_device.addWidget(QLabel("Device ID:"))
        self._edit_device_id = QLineEdit()
        self._edit_device_id.setPlaceholderText("auto-generated on first run")
        row_device.addWidget(self._edit_device_id)
        right.addLayout(row_device)

        row_http_btns = QHBoxLayout()
        self._btn_merge_from_site = QPushButton("Load from site (Merge)")
        self._btn_merge_from_site.clicked.connect(self._on_merge_from_site)
        row_http_btns.addWidget(self._btn_merge_from_site)
        self._btn_replace_from_site = QPushButton("Load from site (Replace)")
        self._btn_replace_from_site.clicked.connect(self._on_replace_from_site)
        row_http_btns.addWidget(self._btn_replace_from_site)
        right.addLayout(row_http_btns)

        row_send = QHBoxLayout()
        self._chk_auto_send = QCheckBox("Auto")
        self._chk_auto_send.setToolTip(
            "Upload the start list to the site after every change"
        )
        self._chk_auto_send.toggled.connect(self._on_auto_send_toggled)
        row_send.addWidget(self._chk_auto_send)
        self._btn_send_to_site = QPushButton("Send start list to site")
        self._btn_send_to_site.clicked.connect(self._on_send_to_site)
        # The button takes the rest of the row; the checkbox keeps only what it needs.
        row_send.addWidget(self._btn_send_to_site, 1)
        right.addLayout(row_send)
        # The status goes on its own line so a long message never squeezes the button.
        self._lbl_auto_send_status = QLabel("")
        right.addWidget(self._lbl_auto_send_status)

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
        self._write_backup("temp", f"spm{int(time.time())}.txt")
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
        self._schedule_auto_send()

    def _write_backup(self, folder: str, filename: str) -> None:
        save_backup(
            path=str(app_path(folder, filename)),
            open_items=self._open_items(),
            save_items=self._save_as_items(),
            groups=self._groups(),
            numbers=self._numbers(),
            regexp_from=self._regexp_from,
            regexp_to=self._regexp_to,
            ftp_address=self._edit_ftp_address.text(),
            start_protocol_file=self._start_protocol_file,
            use_all_numbers=self._chk_use_all.isChecked(),
            auto_shift=self._chk_auto_shift.isChecked(),
            auto_send=self._chk_auto_send.isChecked(),
            first_number=self._edit_first_number.text(),
            delay=self._edit_delay.text(),
            http_site_url=self._edit_http_site_url.text(),
            http_token=self._edit_http_token.text(),
            device_id=self._edit_device_id.text().strip(),
            client_revision=self._client_revision,
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
        # Always restore the line's own shift first: AutoShift only overwrites it when
        # it can actually compute one, and without this the field would keep the
        # previously edited competitor's shift.
        self._edit_time_shift.setText(d["time_shift"] or "0 00:00:00.000")
        if self._chk_auto_shift.isChecked():
            # A line that already carries a number keeps it; re-running "Get number"
            # would hand an edited competitor a different bib.
            if not self._edit_number.text().strip():
                self._on_get_number()
            self._on_auto_shift()
        self._edit_stage.setText(d["stage"] or "1")

    def _load_backup(self, path: str) -> None:
        self._auto_send_suspended = True
        try:
            self._fill_from_backup(load_backup(path))
        finally:
            self._auto_send_suspended = False

    def _fill_from_backup(self, data: dict) -> None:
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
        self._edit_ftp_address.setText(data["ftp_address"])
        self._edit_http_site_url.setText(data["http_site_url"])
        self._edit_http_token.setText(data["http_token"])
        # A stable per-machine id, generated once and persisted so the site can tell
        # referees' uploads apart (re-posting the same id overwrites that device).
        self._edit_device_id.setText(data.get("device_id") or uuid.uuid4().hex)
        self._client_revision = data.get("client_revision", 0)
        self._start_protocol_file = data["start_protocol_file"]
        self._chk_use_all.setChecked(data["use_all_numbers"])
        self._chk_auto_shift.setChecked(data["auto_shift"])
        self._chk_auto_send.setChecked(data.get("auto_send", False))
        self._edit_first_number.setText(data.get("first_number", ""))
        self._edit_delay.setText(data.get("delay", ""))
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
            self._save_all_data()

    def _on_all_to_protocol(self) -> None:
        reply = QMessageBox.question(self, "Warning", "Are you sure?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        for i in range(self._list_open.count()):
            self._list_save_as.addItem(self._list_open.item(i).text())
        self._save_all_data()

    def _on_add_group(self) -> None:
        name = self._edit_add_group.text().strip()
        laps = self._edit_add_laps.text().strip()
        numbers_range = self._edit_numbers_range.text().strip() or "1-200"
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
            # A group range may carry its own "range#first#delay" override; when it
            # does not, the values typed into the form are kept instead of wiped.
            parts = numbers_str.split("#")
            if len(parts) > 1 and parts[1].strip():
                self._edit_first_number.setText(parts[1].strip())
            if len(parts) > 2 and parts[2].strip():
                self._edit_delay.setText(parts[2].strip())
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
                # Convert .NET-style backreferences ($1, $2) to Python (\1, \2)
                py_to = re.sub(r"\$(\d+)", r"\\\1", self._regexp_to)
                line = re.sub(self._regexp_from, py_to, line)
            except re.error:
                pass
        self._parse_and_fill_form(line)
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

    def _on_check_mail(self) -> None:
        found, idx = check_duplicate_fields(self._save_as_items(), 8, True)
        self._lbl_error.setVisible(found)
        if found and idx >= 0:
            self._list_save_as.setCurrentRow(idx)

    def _on_upload(self) -> None:
        self._on_save_start()
        if not self._start_protocol_file:
            return
        ftp_address = self._edit_ftp_address.text().strip()
        if not ftp_address:
            QMessageBox.warning(self, "Upload", "FTP address is not set.")
            return
        parts = ftp_address.split("#")
        if len(parts) < 3:
            QMessageBox.warning(
                self,
                "Upload",
                "FTP address format: ftp://host/path/#login#password",
            )
            return
        ftp_url, login, password = parts[0], parts[1], parts[2]
        filename = Path(self._start_protocol_file).name
        try:
            parsed = urlparse(ftp_url)
            host = parsed.hostname or ftp_url
            remote_dir = parsed.path or "/"
            with ftplib.FTP(host, login, password) as ftp:  # noqa: S321
                ftp.cwd(remote_dir)
                with Path(self._start_protocol_file).open("rb") as f:
                    ftp.storbinary(f"STOR {filename}", f)
        except Exception as exc:
            QMessageBox.warning(self, "Upload", f"Exception during file upload: {exc}")

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

    def _fetch_site_payload(self) -> dict | None:
        """Fetch the participants payload from the site (participants + categories).

        Returns the parsed dict, or ``None`` after showing a popup when the URL/token
        are missing or the request fails (no data is changed in that case).
        """
        site_url = self._edit_http_site_url.text().strip()
        token = self._edit_http_token.text().strip()
        if not site_url or not token:
            QMessageBox.warning(
                self, "Load from site", "Site URL and Token must be set."
            )
            return None
        try:
            return fetch_participants(site_url, token)
        except ValueError as exc:
            QMessageBox.warning(self, "Load from site", str(exc))
            return None

    @staticmethod
    def _payload_to_open_lines(data: dict) -> list[str]:
        categories = data.get("categories", [])
        return [
            participant_to_open_line(p, categories)
            for p in data.get("participants", [])
        ]

    def _group_texts(self) -> list[str]:
        return [
            self._list_groups.item(i).text() for i in range(self._list_groups.count())
        ]

    def _add_group_row(
        self, group_text: str, numbers_range: str = DEFAULT_NUMBER_RANGE
    ) -> None:
        """Append a group (with its number range) to the list and the combo box."""
        self._list_groups.addItem(group_text)
        item = self._list_groups.item(self._list_groups.count() - 1)
        item.setData(Qt.ItemDataRole.UserRole, numbers_range)
        if self._combo_group.findText(group_text) == -1:
            self._combo_group.addItem(group_text)

    def _merge_groups_from_payload(self, data: dict) -> int:
        """Add site groups not already present; returns how many were added.

        New groups take the site's bib range; existing groups keep their current range.
        """
        present = set(self._group_texts())
        added = 0
        for group_text, numbers_range in categories_to_group_rows(
            data.get("categories", [])
        ):
            if group_text not in present:
                present.add(group_text)
                self._add_group_row(group_text, numbers_range)
                added += 1
        return added

    def _replace_groups_from_payload(self, data: dict) -> int:
        """Replace the groups list with the site's groups.

        A group that already exists keeps its current (possibly hand-tuned) range;
        a new group takes the site's bib range. Called only with a successfully fetched
        payload, so an empty ``categories`` legitimately clears the groups (a network
        or JSON error never reaches here -- ``_fetch_site_payload`` returns ``None``).
        """
        incoming = categories_to_group_rows(data.get("categories", []))
        preserved = {
            self._list_groups.item(i).text(): (
                self._list_groups.item(i).data(Qt.ItemDataRole.UserRole)
                or DEFAULT_NUMBER_RANGE
            )
            for i in range(self._list_groups.count())
        }
        self._list_groups.clear()
        self._combo_group.clear()
        for group_text, numbers_range in incoming:
            self._add_group_row(group_text, preserved.get(group_text, numbers_range))
        return len(incoming)

    def _on_merge_from_site(self) -> None:
        data = self._fetch_site_payload()
        if data is None:
            return
        lines = self._payload_to_open_lines(data)
        existing_keys = {
            _participant_merge_key(self._list_open.item(i).text())
            for i in range(self._list_open.count())
            if "#" in self._list_open.item(i).text()
        }
        added = 0
        for line in lines:
            if "#" not in line:
                continue
            key = _participant_merge_key(line)
            if key not in existing_keys:
                self._list_open.addItem(line)
                existing_keys.add(key)
                added += 1
        added_groups = self._merge_groups_from_payload(data)
        self._save_all_data()
        QMessageBox.information(
            self,
            "Load from site",
            f"Added {added} new participant(s) and {added_groups} new group(s).",
        )

    def _on_replace_from_site(self) -> None:
        data = self._fetch_site_payload()
        if data is None:
            return
        lines = self._payload_to_open_lines(data)
        # Groups are returned by the site independently of registrations, so sync them
        # even with no participants yet (e.g. preparing an empty start before sign-ups).
        group_count = self._replace_groups_from_payload(data)
        if not lines:
            self._save_all_data()
            QMessageBox.information(
                self,
                "Load from site",
                "No participants returned; participant list unchanged. "
                f"Loaded {group_count} group(s).",
            )
            return
        self._list_open.clear()
        self._list_open.addItems(lines)
        self._save_all_data()
        QMessageBox.information(
            self,
            "Load from site",
            f"Loaded {len(lines)} participant(s) and {group_count} group(s).",
        )

    def _upload_to_site(self) -> tuple[bool, str]:
        """Upload the save list (right list) to the site for this device.

        Returns (succeeded, message); the message is shown either way, so the auto
        mode can report a failure without a modal dialog.
        """
        site_url = self._edit_http_site_url.text().strip()
        token = self._edit_http_token.text().strip()
        device_id = self._edit_device_id.text().strip()
        if not site_url or not token:
            return False, "Site URL and Token must be set"
        if not device_id:
            device_id = uuid.uuid4().hex
            self._edit_device_id.setText(device_id)
        # Bump the per-device counter on every send so the server can order uploads and
        # reject a delayed/reordered one; persist it (with the list) before sending.
        self._client_revision += 1
        self._auto_send_suspended = True  # saving here must not queue another upload
        try:
            self._save_all_data()  # persists the device id, counter and current list
        finally:
            self._auto_send_suspended = False
        try:
            count = upload_start_list(
                site_url, token, device_id, self._save_as_items(), self._client_revision
            )
        except ValueError as exc:
            return False, str(exc)
        return True, f"Sent {count} competitor(s)"

    def _on_send_to_site(self) -> None:
        """Upload the current save list on demand (the button)."""
        self._auto_send_timer.stop()
        ok, message = self._upload_to_site()
        self._auto_send_pending = not ok
        self._report_auto_send(ok, message)
        if ok:
            QMessageBox.information(self, "Send to site", message)
        else:
            QMessageBox.warning(self, "Send to site", message)

    # ------------------------------------------------------------------
    # auto send
    # ------------------------------------------------------------------

    def _schedule_auto_send(self) -> None:
        """Queue a debounced upload of the current list when auto mode is on."""
        if self._auto_send_suspended or not self._chk_auto_send.isChecked():
            return
        site_url = self._edit_http_site_url.text().strip()
        token = self._edit_http_token.text().strip()
        if not site_url or not token:
            self._lbl_auto_send_status.setText("auto: set Site URL and Token")
            return
        self._auto_send_pending = True
        # Restarting the timer coalesces a burst of edits into a single upload.
        self._auto_send_timer.start()

    def _on_auto_send_toggled(self, checked: bool) -> None:
        if checked:
            # Turning auto on means "make the site match what I have".
            self._schedule_auto_send()
        else:
            self._auto_send_timer.stop()
            self._auto_send_pending = False
            self._lbl_auto_send_status.setText("")

    def _on_auto_send_timeout(self) -> None:
        self._auto_send_timer.stop()
        if not self._auto_send_pending or not self._chk_auto_send.isChecked():
            return
        ok, message = self._upload_to_site()
        # A failed upload stays pending so the next edit retries it.
        self._auto_send_pending = not ok
        self._report_auto_send(ok, message)

    def _report_auto_send(self, ok: bool, message: str) -> None:
        """Show the outcome next to the button: never a dialog, this runs unattended."""
        if not self._chk_auto_send.isChecked():
            self._lbl_auto_send_status.setText("")
        elif ok:
            self._lbl_auto_send_status.setText(
                f"auto: {message} at {time.strftime('%H:%M:%S')}"
            )
        else:
            self._lbl_auto_send_status.setText(f"auto: {message} (will retry)")

    # ------------------------------------------------------------------
    # close event
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        reply = QMessageBox.question(self, "Warning", "Are you sure to exit?")
        if reply == QMessageBox.StandardButton.Yes:
            self._auto_send_timer.stop()
            if self._auto_send_pending and self._chk_auto_send.isChecked():
                # Flush what the debounce window still holds; a failure here cannot be
                # retried, and must not keep the window from closing.
                self._upload_to_site()
            self._write_backup("data", "spm_backup.txt")
            event.accept()
        else:
            event.ignore()
