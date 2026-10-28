# Data model: chip ids

## Start protocol line

`number#name#group#laps#stage#year_of_birth#team#city#comment#time_shift#refs#chips#`

| Index | Field | Rule |
| --- | --- | --- |
| 0-10 | unchanged | see `specs/app/start-protocol.md` |
| 11 | chips | empty, or chip ids: `,` between the ids of a rider, `;` between the riders of a team (nothing between two `;` for a rider without chips) |

- A line built by this program (form, site participant) has 12 separators, field 11 included.
- A line with 11 or fewer separators has no chip field; it reads as having no chips.
- Fields after 11, written by a later version, are kept wherever the line is copied verbatim.

## Chip id

- One or more of `A-Z` and `0-9` after normalisation.
- Normalisation of typed text: split on `,` and `;`; upper-case; drop every character that is not
  an ASCII letter or digit, spaces included; drop empty tokens and repeats, keeping the first
  occurrence in place. When a character other than a letter's case was dropped inside an id, the
  form shows the result before saving it.
- A token with a character outside ASCII is not normalised: the form refuses to save it.

## Relations

- A chip belongs to the bib of the line that carries it, except on a relay with N > 1 stages and a
  numeric bib, where the k-th rider's chips belong to bib + k.
- A chip bound to two different bibs is a duplicate the indicator reports.
