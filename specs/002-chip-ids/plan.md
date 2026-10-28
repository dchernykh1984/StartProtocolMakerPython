# Implementation Plan: Keep each rider's timing chips on the start protocol line

**Branch**: `feat/chip-ids` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-chip-ids/spec.md`

## Summary

Add field 11, the rider's chip ids, to the start protocol line the way field 10 (site
registration references) was added: pure helpers in `app/models.py`, one more form field in
`app/main_window.py`, and the paths that build a line (the form, a site participant) writing the
field always. Verbatim copies already keep every field, so they need tests, not code. The
second, chip indicator names a line with chip ids no reader can use or a chip bound to two
different bibs -- a relay's k-th rider binds to bib + k -- without moving the selection. A chip id
typed in the wrong keyboard layout stops the save, so the registrar fixes it at the desk.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: PySide6 (unchanged; no new dependency)

**Storage**: the backup `data/spm_backup.txt` and the start protocol file, both line by line and
verbatim -- no new backup tag

**Testing**: pytest with the offscreen Qt `win` fixture; coverage gate 90% on `app/` without the
window

**Target Platform**: the portable desktop builds (Windows, macOS Apple Silicon, Linux)

**Project Type**: desktop application

**Performance Goals**: none beyond today's; helpers are linear in the line length

**Constraints**: fields 0-10 keep position and meaning (constitution II); old backups load
(constitution III)

**Scale/Scope**: a few hundred lines per event; a handful of chips per line

## Constitution Check

| Principle | How the plan meets it |
| --- | --- |
| I. Offline first | Nothing new talks to the network; chips live in the lines that are already the record. |
| II. The start line is a shared contract | Field 11 is optional and after field 10. Readers checked: FinishProtocolGeneratorPython reads fields 0-9; the site reads field 10 by index once a line has 11 separators; the chronometers will read field 11 by their own specifications. Field 8 (comment) is not used for machine data. |
| III. Old files stay readable | A line with fewer than 12 separators reads as having no chips; anything after field 11 is kept wherever the line is not rebuilt from the form. No backup tag is added. |
| IV. Known facts are not asked for again | A merge from the site never changes a line's chips. |
| V. The referee's work is never lost | A save stopped by a wrong-layout chip id keeps every form field as typed and says why; the message answers the Save button just pressed. |
| VI. Behaviour is proven by tests | Unit tests for the helpers, Qt-level tests for each handler touched. |
| VII. Plain history | One commit per task below, one-line conventional messages. |

No violation; Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-chip-ids/
  spec.md
  plan.md                      this file
  research.md                  decisions and their reasons
  data-model.md                field 11 and the chip id
  contracts/
    start-protocol-line.md     the line with field 11, for the programs that read it
  tasks.md                     ordered tasks, one commit each
```

### Source Code (repository root)

```text
app/
  models.py          CHIPS_FIELD, chip helpers, build/parse, chip_bibs, chip_rows
  main_window.py     "Chips:" form field; fill, save, clear, team merge, indicator
tests/
  test_chip_ids.py   unit and Qt-level tests of this feature
specs/app/
  start-protocol.md  field 11 described with the other fields
```

**Structure Decision**: the existing single-project layout; the feature mirrors the field-10
code paths one for one, so a reader finds chips next to refs everywhere.

## Design

- `CHIPS_FIELD = 11`, `has_chips_field(line)` (more than 11 separators), `_raw_riders(text)` (the
  one tokenizer: riders between semicolons, ids between commas; every helper below starts there),
  ids upper-cased with every character that is not an ASCII letter or digit dropped, spaces
  included; empty ids and repeats dropped, first occurrence kept;
  `cleaned_chip_text(text)` (the ids as they will be saved when cleaning dropped a character inside
  one, else None: the form then shows them and waits for a second Save),
  `format_chips(text)` (field 11: commas within a rider, semicolons between riders, an empty rider
  kept before others). No `set_chips()`: nothing changes the chips of a line except rebuilding it
  from the form.
- `foreign_chip_tokens(text)`: the typed tokens that contain a letter or digit outside ASCII. The
  form refuses to save while it returns anything (research, decision 3).
- `chip_bibs(line)`: the (chip, bib) pairs a line binds, a relay's k-th rider to bib + k and a
  rider past the last stage to None, no repeats dropped across riders (research,
  decision 5); `chip_rows()` compares them across lines and finds, in the same pass, a
  line with a foreign id or more riders than stages.
- `parse_competitor_line()` returns `"chips"` (empty when the field is absent);
  `build_competitor_line(..., chips="")` writes `format_chips(chips)` after the refs, so
  every built line has 12 separators. `participant_to_open_line()` passes nothing and so writes an
  empty field.
- `merge_open_lines()` is unchanged: it never rebuilds an existing line, and `set_refs()` keeps
  field 11.
- `_refresh_duplicate_indicator()` reads the protocol list once, checks bibs and references as
  before, then names the line in the chip indicator: "CHIP IDS NEED A FIX!" for
  the first row of `chip_rows()`, else "ONE CHIP ON TWO BIBS!" for the second.
- The form gets "Chips:" under "Site entry:"; its `returnPressed` inserts `, ` at the cursor unless
  the text before it is empty or ends with a separator. `_parse_and_fill_form()` fills it;
  `_on_save_to_file()` stops on `foreign_chip_tokens()`, then on `cleaned_chip_text()` (showing the
  ids for a second Save), passes the field to `build_competitor_line()` and clears it after
  saving; `_on_add_into_team()` adds the member's chips as the next rider (`merge_chip_text()`).
- "Open competitors list" names the loaded lines with a foreign chip id.

## Complexity Tracking

Empty: no constitution violation.
