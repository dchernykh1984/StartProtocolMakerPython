# Contract: field 11 of the start protocol line

For ChronometerPython, ChronometerAndroid and any later reader of the start protocol.

- Field 11 (zero-based, `#`-separated) holds the line's chip ids, comma-separated, each one or
  more of `A-Z0-9`. It is empty when the line has no chips, and absent from lines written before
  this feature (11 or fewer separators).
- The bib is field 0. `NOT_PAID` in field 0 (open list) or an empty field 0 is not a bib.
- A reader normalises what it compares the same way: split field 11 on commas and semicolons, then
  upper case, ASCII letters and digits only.
- A chip on two lines is an error of the start protocol; a reader reports it rather than choosing.
- Lines arrive through the start protocol file (UTF-8) or the site's
  `GET /api/v1/start-list/?competition_token=...` (`devices[].items`, verbatim strings).

Example:

```text
15#Ivanov Ivan#M40#3#1#1985#Team#Almaty##0 00:00:00.000#r1234#E28011700000020A,E2801170000002AB#
```
