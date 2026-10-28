# Start protocol, backup and site exchange

Written from the code (`app/models.py`, `app/main_window.py`, `app/http_io.py`) on 2026-10-25.
Where the code does not say why, this file does not guess.

## Two lists

- **Open list** (left): the pre-registration database, loaded from the site or typed by hand. Its
  lines usually carry no bib -- bibs are handed out at the start.
- **Protocol list** (right): the start protocol itself. It is what the start protocol file, the
  backup's second section and the site upload contain.

A line reaches the protocol list in two ways:

1. **Copied verbatim** from the open list ("open to protocol", "all to protocol").
2. **Built from the form**: a line opened from either list fills the form; "Save to file" appends a
   new line made by `build_competitor_line()` from the form fields only.

## The line

`#`-separated and `#`-terminated, read by index (`get_field`):

| Index | Field | Notes |
| --- | --- | --- |
| 0 | number | The bib. `NOT_PAID` in the open list marks an unpaid entry on a paid event |
| 1 | name | `Last First`; a relay from the site has its members joined by `<BR>`; "Add into team" joins with ` / ` |
| 2 | group | Category name |
| 3 | laps | Empty when the category has no lap count |
| 4 | stage | Number of stages, `1` by default; with N > 1 FinishProtocolGenerator expects bibs `number` .. `number + N - 1`, one per stage |
| 5 | year_of_birth | For a relay from the site, members' years joined by `<BR>` |
| 6 | team | |
| 7 | city | |
| 8 | comment | Free text; from the site it is `additional_info` with `#` and line breaks replaced by spaces. "Check mail" compares its first word |
| 9 | time_shift | Start delay, `D HH:MM:SS.mmm`, `0 00:00:00.000` by default |
| 10 | refs | Site registrations of the line, `r<id>` comma-separated (cycling-site #349); written always, even empty |
| 11 | chips | Timing chip ids, upper case, ASCII letters and digits: commas between the ids of a rider, semicolons between the riders of a team in stage order (ChronometerPython #49); written always, even empty, so a line has 12 separators |

A line written before field 10 existed has 10 separators: its field is *absent*, which the site
tells apart from an empty one (a referee's unlink). A line written before field 11 existed has 11
separators and no chips. A group without a lap count still writes the empty laps field, so every
later field stays in place. Readers that exist:

- FinishProtocolGeneratorPython (`StartProtocolElement.from_line`) reads fields 0-9 by index and
  ignores anything after them, fields 10 and 11 included.
- WindowsChronometerPython and ChronometerAndroid read field 0 and, for chip timing, field 11
  (their `specs/001-event-sources/`).
- The site stores uploaded lines as opaque strings (up to 2000 characters each) and returns them
  to FinishProtocolGenerator.

## Numbers, delays, duplicates

- **Get number** picks the lowest free bib in the group's range (`bib_from-bib_to` from the site,
  or typed). Bibs used in the protocol list are taken; so are those in the open list unless
  "Use all numbers" is ticked.
- **AutoShift** sets the delay to `(number - first number) * delay per number`, never below zero.
  A group range may carry its own `range#first#delay` override.
- **Duplicates**: every save checks the protocol list for a repeated bib (field 0), a repeated site
  registration (field 10) and a chip on the lines of two different bibs (field 11); "Check names"
  and "Check mail" check fields 1 and 8 on demand. A repeat is reported; the first repeat whose
  stage fields are equal is selected in the list.
- **Merge from site** matches a line by its site reference; two registrations of one person stay
  two lines. The `(last name, first name, year)` key only links an old unreferenced line when it is
  the single match, otherwise the line is added and reported as ambiguous. A reference on two
  protocol lines lights the duplicate warning like a repeated bib. **Replace from site** clears the open list first. Both sync groups and their bib
  ranges, keeping a local AutoShift override.

## Files

- **Backup** `data/spm_backup.txt`, rewritten on every save, plus a timestamped copy in
  `temp/spm<unix time>.txt`. Sections in order: open list, protocol list, groups, number ranges,
  RegExp From, RegExp To, FTP, HTTP (site URL and token), then optional tags `StartProtocolFile`,
  `UseAllNumbers`, `AutoShift`, `FirstNumber`, `DelayPerNumber`, `DeviceId`, `ClientRevision`,
  `AutoSend`. Tags are read back in this order, so a new one goes last. Loading tries UTF-8,
  then cp1251, then Latin-1.
- **Start protocol file**: the protocol list, one line per competitor, UTF-8; it can be pushed to
  an FTP server as well.

## Site exchange

- `GET /api/v1/participants/?competition_token=...&include_unpaid=true` returns registrations and
  categories; `participant_to_open_line()` keeps each registration's `id` as `r<id>` in field 10.
- The form's "Site entry" field shows and edits it; saving a rider clears it for the next one, and
  "Join Team" adds the joined rider's reference and keeps the team's already issued bib,
  including with AutoShift enabled.
  Text field separators (`#` and line breaks) become spaces before serialization,
  including category names, so supplied text cannot shift the registration reference.
- `POST /api/v1/start-list/` sends the protocol list as `items` with `device_id` and an increasing
  `client_revision`; the site keeps one snapshot per device and answers 409 to a stale one.
- With **Auto** ticked, edits are sent 2 seconds after the last one; a failure is shown under the
  button and retried every 15 seconds. The backup is written before every send.

## Timing chips

- The form's "Chips" field shows and edits field 11. Commas and semicolons separate ids; spaces and
  punctuation inside an id are dropped, and ids are kept upper case without repeats. When cleaning
  dropped something inside an id, the first Save shows the ids as they will be saved and the second
  saves them. Enter in the field adds a separator at the cursor, for desk readers that end each id
  with Enter.
- An id with a character outside ASCII -- a Cyrillic look-alike typed with the Russian layout --
  stops the save: a message names it and every form field keeps what was typed.
- Saving a rider clears the field for the next one; "Add into team" adds the member's chips as the
  next rider, after a semicolon, and a member without chips as `-`. On a line with N > 1 stages and
  a numeric bib, the k-th rider's chips belong to bib + k, as FinishProtocolGenerator and the site
  number stage riders.
- "Open competitors list" loads lines as they are and names those whose chip field has a character
  outside ASCII, to be fixed through the form. In the protocol list such a line, or a relay with
  more riders than stages, lights "CHIP IDS NEED A FIX!" and is selected.
- Copies keep the field as they keep every field: open to protocol, the backup, the start protocol
  file, FTP and the start list upload. A line from the site arrives with an empty field, and a merge
  never changes the chips of a line it already has.

## Features

- [001-registration-references](../001-registration-references/spec.md): field 10.
- [002-chip-ids](../002-chip-ids/spec.md): field 11.
