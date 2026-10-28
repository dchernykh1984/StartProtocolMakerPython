# Contract: field 11 of the start protocol line

For ChronometerPython, ChronometerAndroid and any later reader of the start protocol.

- Field 11 (zero-based, `#`-separated) holds the line's chip ids: riders separated by semicolons,
  in stage order, and the ids of one rider by commas, each one or more of `A-Z0-9`. A rider without
  chips is nothing between two semicolons (`A1;;C1`), keeping the riders after it in place; riders
  without chips at the end are not written. The field is empty when the line has no chips -- also
  for a team whose riders have none -- and absent from lines written before this feature (11 or
  fewer separators).
- The bib is field 0. `NOT_PAID` in field 0 (open list) or an empty field 0 is not a bib.
- Binding: on a line whose field 4 (stages) is N > 1 and whose bib is a number, the k-th rider
  (from 0) binds to bib + k, the way FinishProtocolGenerator and the site number stage riders, and
  riders past the N-th bind nothing. On any other line every chip binds to the bib.
- A reader normalises what it compares the same way: split on semicolons and commas, then upper
  case, ASCII letters and digits only.
- A chip on the lines of two different bibs is an error of the start protocol; a reader reports it
  rather than choosing. On two lines of one bib it simply belongs to that bib.
- Lines arrive through the start protocol file (UTF-8) or the site's
  `GET /api/v1/start-list/?competition_token=...` (`devices[].items`, verbatim strings).

Examples -- a rider with two chips, and a three-stage relay whose riders 21, 22 and 23 carry A1 and
A2, B1, and C1:

```text
15#Ivanov Ivan#M40#3#1#1985#Team#Almaty##0 00:00:00.000#r1234#E28011700000020A,E2801170000002AB#
21#Kim A / Lee B / Park C#Relay#1#3#1990 / 1991 / 1992#Team###0 00:00:00.000#r21,r17,r9#A1,A2;B1;C1#
```
